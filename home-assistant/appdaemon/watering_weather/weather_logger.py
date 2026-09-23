"""weather_logger.py -- AppDaemon app: persist weather snapshots + zone decisions.

Listens for the HA bus event `watering_weather_snapshot` (fired twice-daily by the
always-on snapshot automation, regardless of system state -- parked in
manual_override, winterized, mid-cycle, or idle) and writes ONE `weather_snapshots`
row plus its N `zone_decisions` children into the SEPARATE weather-observations
database (watering_weather.db). This is Event 6 of the event-payload contract
(docs/architecture.md Section 13.3.1); the schema is docs/weather_schema.sql.

Self-contained event: the payload carries the full snapshot AND the per-zone
decisions, so -- unlike the ops cycle/zone-run events -- there is NO cross-event
correlation to hold. Parent + children are written in a SINGLE transaction, so a
snapshot is all-or-nothing (a bad child rolls the parent back; no orphan snapshot).

All decision logic stays in HA (CORE PRINCIPLE): the shared routine
`script.compute_zone_programs` computes the decisions; this app is a DUMB SINK. It
is fire-and-forget reporting and is not on the watering / safety path
(architecture.md Section 13.1), so this handler NEVER raises: a bad payload is
logged and skipped, a DB error is logged and swallowed. Nothing here can stall
irrigation. Unlike the ops writer, the weather DB has no `system_events` table, so
rejections are logged to the AppDaemon log only (not persisted as a breadcrumb row).

apps.yaml configuration (see the sibling apps.yaml):
  db_path        -- absolute path to the SQLite file
                    (default `/homeassistant/watering_weather.db`)
  trigger_event  -- HA event name this app listens for
                    (default `watering_weather_snapshot`)
"""

import json
import sqlite3

import appdaemon.plugins.hass.hassapi as hass


class WeatherLogger(hass.Hass):
    """Persist `watering_weather_snapshot` payloads into the weather DB."""

    VALID_WINDOWS = ("morning", "evening")
    VALID_SOURCES = ("brightsky", "local_station", "mixed")
    VALID_SEASONS = ("spring", "summer", "fall", "winter")
    VALID_PROGRAMS = ("off", "light", "normal", "heavy", "booster")
    VALID_RAIN_SOURCES = ("wh40", "dwd", "none")

    # weather_snapshots columns carried straight through as REAL (float|null).
    SNAPSHOT_FLOATS = (
        "temp_c",
        "temp_high_forecast_c",
        "temp_high_yesterday_c",
        "temp_avg_high_3day_c",
        "rain_24h_mm",
        "rain_72h_mm",
        "forecast_pop_today",
        "forecast_rain_today_mm",
        "humidity_pct",
        "pressure_hpa",
        "cloud_cover_pct",
        "wind_speed_ms",
    )

    def initialize(self):
        self.db_path = self.args.get(
            "db_path", "/homeassistant/watering_weather.db"
        )
        self.trigger_event = self.args.get(
            "trigger_event", "watering_weather_snapshot"
        )
        self.listen_event(self.on_event, self.trigger_event)
        self.log(
            f"WeatherLogger ready; listening for '{self.trigger_event}'",
            level="INFO",
        )

    def on_event(self, event_name, data, kwargs):
        """Validate one snapshot payload and write it + its zone_decisions."""
        data = data or {}

        # ---- snapshot-level validation -------------------------------------
        observed_at = self._clean(data.get("observed_at"))
        window_name = self._clean(data.get("window_name"))

        problems = []
        if not observed_at:
            problems.append("missing 'observed_at'")
        if not window_name:
            problems.append("missing 'window_name'")
        elif window_name not in self.VALID_WINDOWS:
            problems.append(
                f"invalid 'window_name' {window_name!r} "
                f"(expected one of {self.VALID_WINDOWS})"
            )

        source = self._clean(data.get("source")) or "brightsky"
        if source not in self.VALID_SOURCES:
            problems.append(
                f"invalid 'source' {source!r} (expected one of {self.VALID_SOURCES})"
            )

        rain_source = self._clean(data.get("rain_source"))
        if rain_source is not None and rain_source not in self.VALID_RAIN_SOURCES:
            problems.append(
                f"invalid 'rain_source' {rain_source!r} "
                f"(expected one of {self.VALID_RAIN_SOURCES})"
            )

        decisions_in = data.get("zone_decisions")
        if not isinstance(decisions_in, (list, tuple)) or not decisions_in:
            problems.append(
                "missing/empty 'zone_decisions' (expected a non-empty list)"
            )

        # ---- per-zone validation + coercion --------------------------------
        decision_rows = []
        if not problems:
            for idx, dec in enumerate(decisions_in):
                if not isinstance(dec, dict):
                    problems.append(f"zone_decisions[{idx}] is not a mapping")
                    break
                zid = self._to_int(dec.get("zone_id"))
                season = self._clean(dec.get("season"))
                program = self._clean(dec.get("computed_program"))
                criteria = self._json(dec.get("decision_criteria"))

                if zid is None or not (1 <= zid <= 4):
                    problems.append(f"zone_decisions[{idx}]: bad zone_id {dec.get('zone_id')!r}")
                if season not in self.VALID_SEASONS:
                    problems.append(f"zone_decisions[{idx}]: bad season {season!r}")
                if program not in self.VALID_PROGRAMS:
                    problems.append(f"zone_decisions[{idx}]: bad computed_program {program!r}")
                if criteria is None:
                    problems.append(f"zone_decisions[{idx}]: missing decision_criteria")
                if problems:
                    break

                # would_water: use payload if valid, else derive (program != 'off').
                would = self._to_bool(dec.get("would_water"))
                if would is None:
                    would = 0 if program == "off" else 1

                decision_rows.append(
                    {
                        "zone_id": zid,
                        "season": season,
                        "computed_program": program,
                        "program_multiplier": self._to_float(dec.get("program_multiplier")),
                        "would_water": would,
                        "moisture_pct": self._to_float(dec.get("moisture_pct")),
                        "moisture_sensor_count": self._to_int(dec.get("moisture_sensor_count")) or 0,
                        "decision_criteria": criteria,
                    }
                )

        if problems:
            self.error(
                f"Rejected {self.trigger_event}: {'; '.join(problems)}; "
                f"payload={data!r}"
            )
            return

        # ---- build the snapshot row ----------------------------------------
        snapshot = {
            "observed_at": observed_at,
            "window_name": window_name,
            "source": source,
            "weather_available": self._to_bool(data.get("weather_available"), default=1),
            "raining_now": self._to_bool(data.get("raining_now")),
            "rain_source": rain_source,
            "raw": self._json(data.get("raw")),
        }
        for field in self.SNAPSHOT_FLOATS:
            snapshot[field] = self._to_float(data.get(field))

        if self._insert(snapshot, decision_rows):
            self.log(
                f"weather_snapshots <- {window_name} @ {observed_at} "
                f"(+{len(decision_rows)} zone_decisions)",
                level="DEBUG",
            )

    def _insert(self, snapshot, decision_rows):
        """Write the snapshot + all decisions in ONE transaction.

        FK is enforced (PRAGMA foreign_keys = ON) so a bad child aborts the whole
        write; the parent is rolled back with it -- no orphan snapshot. Returns
        True on success, False on any DB error (logged, never raised).
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA foreign_keys = ON;")
            with conn:  # commits on success, rolls back on exception
                cur = conn.execute(
                    "INSERT INTO weather_snapshots "
                    "(observed_at, window_name, source, weather_available, "
                    " temp_c, temp_high_forecast_c, temp_high_yesterday_c, "
                    " temp_avg_high_3day_c, rain_24h_mm, rain_72h_mm, raining_now, "
                    " rain_source, forecast_pop_today, forecast_rain_today_mm, "
                    " humidity_pct, pressure_hpa, cloud_cover_pct, wind_speed_ms, raw) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        snapshot["observed_at"],
                        snapshot["window_name"],
                        snapshot["source"],
                        snapshot["weather_available"],
                        snapshot["temp_c"],
                        snapshot["temp_high_forecast_c"],
                        snapshot["temp_high_yesterday_c"],
                        snapshot["temp_avg_high_3day_c"],
                        snapshot["rain_24h_mm"],
                        snapshot["rain_72h_mm"],
                        snapshot["raining_now"],
                        snapshot["rain_source"],
                        snapshot["forecast_pop_today"],
                        snapshot["forecast_rain_today_mm"],
                        snapshot["humidity_pct"],
                        snapshot["pressure_hpa"],
                        snapshot["cloud_cover_pct"],
                        snapshot["wind_speed_ms"],
                        snapshot["raw"],
                    ),
                )
                snapshot_id = cur.lastrowid
                conn.executemany(
                    "INSERT INTO zone_decisions "
                    "(snapshot_id, zone_id, season, computed_program, "
                    " program_multiplier, would_water, moisture_pct, "
                    " moisture_sensor_count, decision_criteria) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            snapshot_id,
                            d["zone_id"],
                            d["season"],
                            d["computed_program"],
                            d["program_multiplier"],
                            d["would_water"],
                            d["moisture_pct"],
                            d["moisture_sensor_count"],
                            d["decision_criteria"],
                        )
                        for d in decision_rows
                    ],
                )
            return True
        except sqlite3.Error as exc:
            self.error(
                f"weather_snapshots/zone_decisions INSERT failed: {exc}; "
                f"snapshot={snapshot!r}"
            )
            return False
        finally:
            if conn is not None:
                conn.close()

    # ---- coercion helpers --------------------------------------------------
    @staticmethod
    def _clean(value):
        """Stripped str, or None for empties / HA 'unknown'|'unavailable'."""
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() in ("unknown", "unavailable"):
            return None
        return text

    @classmethod
    def _to_float(cls, value):
        text = cls._clean(value)
        if text is None:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _to_int(cls, value):
        text = cls._clean(value)
        if text is None:
            return None
        try:
            return int(float(text))  # tolerate "2", "2.0"
        except (TypeError, ValueError):
            return None

    @classmethod
    def _to_bool(cls, value, default=None):
        """Return 0/1 from truthy/falsey payloads; `default` when absent/unparsable."""
        text = cls._clean(value)
        if text is None:
            return default
        low = text.lower()
        if low in ("1", "true", "on", "yes"):
            return 1
        if low in ("0", "false", "off", "no"):
            return 0
        return default

    @classmethod
    def _json(cls, value):
        """Serialise a dict/list to a JSON string; pass a non-empty string through.

        Returns None only for a genuinely absent value, so a required
        decision_criteria that arrives empty is caught by validation.
        """
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, separators=(",", ":"), sort_keys=True)
            except (TypeError, ValueError):
                return None
        text = str(value).strip()
        return text or None
