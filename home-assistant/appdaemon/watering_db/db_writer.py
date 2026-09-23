"""db_writer.py -- AppDaemon app: persist cycle & zone-run events to watering_ops.

Consumes Events 1/3/4/7 of the event-payload contract (docs/architecture.md
Section 13.3.1) fired by the Phase 4 state machine:

  Event 7  watering_decision_applied    -> buffer the applied decision
  Event 1  watering_preflight_complete  -> INSERT watering_cycles (open row);
                                           attach the buffered decision
  Event 3  watering_zone_run_complete   -> INSERT zone_runs (+ season and the
                                           zone's decision_criteria)
  Event 4  watering_cycle_complete      -> UPDATE watering_cycles (close row)

Decision buffer (ADR-018, §3.6 S5): state_window_check fires Event 7 with the
applied per-zone decision just before it hands over to preflight -- BEFORE
cycle_uuid exists (preflight mints it). This app holds it as the single pending
decision, attaches it to the cycle at the next Event 1 if it is recent
(DECISION_MAX_AGE_SEC), and writes each zone's criteria onto its zone_runs row
at Event 3. Same in-memory, never-persisted pattern as the dose buffer: an
AppDaemon restart mid-cycle loses it and those rows get NULL decision_criteria
(the run row itself is always written).

SQLite primary keys are assigned at INSERT, so the state machine cannot know
them when it fires an event; it mints opaque correlation ids (cycle_uuid /
zrun_uuid) and stamps them on every related event. This app keeps an in-memory
map (cycle_uuid -> cycle_id, zrun_uuid -> zrun_id) for the life of a cycle and
uses it to populate foreign keys. The map is deliberately NOT persisted
(Section 13.3.1): if AppDaemon restarts mid-cycle it loses the map, a later
event then arrives with an unknown correlation id, and the writer logs it,
records a system_events breadcrumb, and skips.

The operational DB is fire-and-forget reporting and is not on the watering /
safety path (Section 13.1): no handler here raises. A bad payload is validated
out (logged + system_events reject row + skipped) and a DB error is logged and
swallowed. Nothing here can stall irrigation.

Event 5 (watering_system_event -> system_events) is handled separately by the
sibling db_event_writer.py. Event 2 (watering_fert_dose_complete) has no
publisher yet (fertigation hardware unwired); the dose-buffer scaffold below is
in place so Event 3 already derives `fertigated` correctly (empty buffer -> 0).
The Event-2 listener and the fertigation_doses INSERT flush land together when
the fert path is wired.

apps.yaml configuration (see the sibling apps.yaml):
  db_path             -- absolute path to the SQLite file
  event_preflight     -- HA event for Event 1 (default watering_preflight_complete)
  event_zone_run      -- HA event for Event 3 (default watering_zone_run_complete)
  event_cycle         -- HA event for Event 4 (default watering_cycle_complete)
  event_decision      -- HA event for Event 7 (default watering_decision_applied)
  cycle_active_sensor -- binary_sensor reflecting cycle-in-progress
                         (default binary_sensor.watering_cycle_active)
"""

import json
import sqlite3
from datetime import datetime, timezone

import appdaemon.plugins.hass.hassapi as hass


class DbWriter(hass.Hass):
    """Persist cycle / zone-run events (Events 1/3/4) into watering_ops."""

    TRIGGER_TYPES = ("scheduled", "manual", "override")
    WEATHER_PROGRAMS = ("off", "light", "normal", "heavy")
    OUTCOMES = ("completed", "aborted", "error")
    SEASONS = ("spring", "summer", "fall", "winter")

    # window_check -> preflight is sub-second; anything older than this is a
    # decision whose cycle never started (e.g. a parked Dev-Tools run) and must
    # not be attached to a later, unrelated cycle.
    DECISION_MAX_AGE_SEC = 600

    TS_FORMAT = "%Y-%m-%d %H:%M:%S"

    def initialize(self):
        self.db_path = self.args.get("db_path", "/homeassistant/watering_ops.db")
        self.event_preflight = self.args.get(
            "event_preflight", "watering_preflight_complete"
        )
        self.event_zone_run = self.args.get(
            "event_zone_run", "watering_zone_run_complete"
        )
        self.event_cycle = self.args.get("event_cycle", "watering_cycle_complete")
        self.cycle_active_sensor = self.args.get(
            "cycle_active_sensor", "binary_sensor.watering_cycle_active"
        )
        self.event_decision = self.args.get(
            "event_decision", "watering_decision_applied"
        )

        # In-memory correlation state (Section 13.3.1). Reset on restart by
        # design; never persisted. Bounded: entries are dropped at Event 4.
        self.cycle_ids = {}    # cycle_uuid -> cycle_id
        self.zrun_ids = {}     # zrun_uuid  -> zrun_id
        self.dose_buffer = {}  # zrun_uuid  -> [dose payloads]  (Event 2, later)
        self.cycle_zruns = {}  # cycle_uuid -> set(zrun_uuid)   (for cleanup)
        self.pending_decision = None  # Event 7 awaiting its Event 1
        self.cycle_decisions = {}     # cycle_uuid -> {zone_id: criteria}

        self.listen_event(self.on_decision, self.event_decision)
        self.listen_event(self.on_preflight, self.event_preflight)
        self.listen_event(self.on_zone_run, self.event_zone_run)
        self.listen_event(self.on_cycle_complete, self.event_cycle)
        self.log(
            "DbWriter ready; listening for "
            f"'{self.event_decision}', '{self.event_preflight}', "
            f"'{self.event_zone_run}', '{self.event_cycle}'",
            level="INFO",
        )

    # ----------------------------------------------------------------- Event 7
    def on_decision(self, event_name, data, kwargs):
        """Event 7: buffer the applied decision until its cycle opens.

        Payload: window + zone_decisions (the compute_zone_programs list; each
        item carries zone_id + decision_criteria). A newer Event 7 replaces an
        older pending one. Malformed items are skipped, never raised.
        """
        data = data or {}
        items = data.get("zone_decisions")
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except ValueError:
                items = None
        if not isinstance(items, list):
            self.log(
                f"Ignored {event_name}: zone_decisions is not a list "
                f"({type(items).__name__})",
                level="WARNING",
            )
            return

        zones = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            zone_id = self._int(item.get("zone_id"))
            criteria = item.get("decision_criteria")
            if zone_id in (1, 2, 3, 4) and criteria is not None:
                zones[zone_id] = criteria

        self.pending_decision = {"received_at": self._now(), "zones": zones}
        self.log(
            f"Decision buffered for the next cycle "
            f"(window={self._clean(data.get('window'))}, zones={sorted(zones)})",
            level="INFO",
        )

    def _take_pending_decision(self):
        """Pop the pending decision if it is recent enough, else drop it."""
        pending, self.pending_decision = self.pending_decision, None
        if pending is None:
            return None
        age = (self._now() - pending["received_at"]).total_seconds()
        if age > self.DECISION_MAX_AGE_SEC:
            self.log(
                f"Discarded a stale buffered decision ({int(age)} s old); this "
                "cycle's zone_runs get NULL decision_criteria",
                level="WARNING",
            )
            return None
        return pending["zones"]

    # ----------------------------------------------------------------- Event 1
    def on_preflight(self, event_name, data, kwargs):
        """Event 1: open a watering_cycles row; record cycle_uuid -> cycle_id."""
        data = data or {}
        cycle_uuid = self._clean(data.get("cycle_uuid"))
        start_time = self._clean(data.get("start_time"))
        trigger_type = self._clean(data.get("trigger_type"))

        problems = []
        if not cycle_uuid:
            problems.append("missing 'cycle_uuid'")
        if not start_time:
            problems.append("missing 'start_time'")
        if not trigger_type:
            problems.append("missing 'trigger_type'")
        elif trigger_type not in self.TRIGGER_TYPES:
            problems.append(
                f"invalid 'trigger_type' {trigger_type!r} "
                f"(expected one of {self.TRIGGER_TYPES})"
            )
        if problems:
            self._reject(self.event_preflight, problems, data)
            return

        cycle_id = self._insert_cycle(
            (
                start_time,
                trigger_type,
                self._num(data.get("rainfall_24h_mm")),
                self._num(data.get("rainfall_72h_mm")),
                self._num(data.get("temp_high_c")),
            )
        )
        if cycle_id is None:
            return  # DB error already logged

        if cycle_uuid in self.cycle_ids:
            self.log(
                f"cycle_uuid {cycle_uuid!r} already mapped "
                f"(-> {self.cycle_ids[cycle_uuid]}); overwriting with {cycle_id}",
                level="WARNING",
            )
        self.cycle_ids[cycle_uuid] = cycle_id
        self.cycle_zruns.setdefault(cycle_uuid, set())
        decision = self._take_pending_decision()
        if decision is not None:
            self.cycle_decisions[cycle_uuid] = decision
        self._set_cycle_active(True, cycle_uuid)
        self.log(
            f"watering_cycles <- cycle_id={cycle_id} "
            f"({trigger_type} @ {start_time}) uuid={cycle_uuid}",
            level="INFO",
        )

    # ----------------------------------------------------------------- Event 3
    def on_zone_run(self, event_name, data, kwargs):
        """Event 3: INSERT a zone_runs row, then flush any buffered doses."""
        data = data or {}
        cycle_uuid = self._clean(data.get("cycle_uuid"))
        zrun_uuid = self._clean(data.get("zrun_uuid"))
        zone_id = self._int(data.get("zone_id"))
        weather_program = self._clean(data.get("weather_program"))
        start_time = self._clean(data.get("start_time"))
        aborted = self._int(data.get("aborted"))

        problems = []
        if not cycle_uuid:
            problems.append("missing 'cycle_uuid'")
        if not zrun_uuid:
            problems.append("missing 'zrun_uuid'")
        if zone_id not in (1, 2, 3, 4):
            problems.append(
                f"invalid 'zone_id' {data.get('zone_id')!r} (expected 1-4)"
            )
        if not weather_program:
            problems.append("missing 'weather_program'")
        elif weather_program not in self.WEATHER_PROGRAMS:
            problems.append(
                f"invalid 'weather_program' {weather_program!r} "
                f"(expected one of {self.WEATHER_PROGRAMS})"
            )
        if not start_time:
            problems.append("missing 'start_time'")
        if aborted not in (0, 1):
            problems.append(
                f"invalid 'aborted' {data.get('aborted')!r} (expected 0 or 1)"
            )
        if problems:
            self._reject(self.event_zone_run, problems, data)
            return

        cycle_id = self.cycle_ids.get(cycle_uuid)
        if cycle_id is None:
            self._orphan(
                self.event_zone_run,
                f"unknown cycle_uuid {cycle_uuid!r} (no open cycle; "
                "AppDaemon may have restarted mid-cycle)",
                data,
            )
            return

        end_time = self._clean(data.get("end_time"))
        actual_duration = self._duration_sec(start_time, end_time)
        # `fertigated` is DERIVED from the dose buffer, never read from the
        # payload (Section 13.3.1). No Event-2 publisher yet -> always 0.
        fertigated = 1 if self.dose_buffer.get(zrun_uuid) else 0
        # Decision recording (S5): never a reason to reject the run row -- an
        # unknown season or a missing decision is stored as NULL.
        season = self._clean(data.get("season"))
        if season is not None and season not in self.SEASONS:
            self.log(
                f"zone_runs season {season!r} not in {self.SEASONS}; storing NULL",
                level="WARNING",
            )
            season = None
        criteria = self._json_text(
            self.cycle_decisions.get(cycle_uuid, {}).get(zone_id)
        )

        zrun_id = self._insert_zone_run(
            (
                cycle_id,
                zone_id,
                weather_program,
                start_time,
                end_time,
                self._int(data.get("planned_duration_sec")),
                actual_duration,
                self._num(data.get("program_multiplier")),
                fertigated,
                aborted,
                self._clean(data.get("abort_reason")),
                season,
                criteria,
            )
        )
        if zrun_id is None:
            return

        self.zrun_ids[zrun_uuid] = zrun_id
        self.cycle_zruns.setdefault(cycle_uuid, set()).add(zrun_uuid)
        self._flush_doses(zrun_uuid, zrun_id)
        self.log(
            f"zone_runs <- zrun_id={zrun_id} cycle_id={cycle_id} "
            f"zone={zone_id} program={weather_program} "
            f"dur={actual_duration}s fert={fertigated} aborted={aborted} "
            f"season={season} criteria={'yes' if criteria else 'NULL'}",
            level="INFO",
        )

    # ----------------------------------------------------------------- Event 4
    def on_cycle_complete(self, event_name, data, kwargs):
        """Event 4: close the watering_cycles row and drop the cycle's state."""
        data = data or {}
        cycle_uuid = self._clean(data.get("cycle_uuid"))
        end_time = self._clean(data.get("end_time"))
        outcome = self._clean(data.get("outcome"))

        problems = []
        if not cycle_uuid:
            problems.append("missing 'cycle_uuid'")
        if not end_time:
            problems.append("missing 'end_time'")
        if not outcome:
            problems.append("missing 'outcome'")
        elif outcome not in self.OUTCOMES:
            problems.append(
                f"invalid 'outcome' {outcome!r} "
                f"(expected one of {self.OUTCOMES})"
            )
        if problems:
            self._reject(self.event_cycle, problems, data)
            return

        # A cycle has definitively ended: clear the cycle-active sensor
        # regardless of whether we still hold its correlation (a restart could
        # have dropped the map). Safe to turn off on any valid Event 4.
        self._set_cycle_active(False, cycle_uuid)

        cycle_id = self.cycle_ids.get(cycle_uuid)
        if cycle_id is None:
            self._orphan(
                self.event_cycle,
                f"unknown cycle_uuid {cycle_uuid!r} (no open cycle to close; "
                "AppDaemon may have restarted mid-cycle)",
                data,
            )
            return

        if self._update_cycle(
            cycle_id, end_time, outcome, self._clean(data.get("notes"))
        ):
            self.log(
                f"watering_cycles -> cycle_id={cycle_id} closed "
                f"({outcome} @ {end_time})",
                level="INFO",
            )
        self._forget_cycle(cycle_uuid)

    def _forget_cycle(self, cycle_uuid):
        """Drop this cycle's in-memory correlation and any lingering buffers."""
        self.cycle_ids.pop(cycle_uuid, None)
        self.cycle_decisions.pop(cycle_uuid, None)
        for zrun_uuid in self.cycle_zruns.pop(cycle_uuid, ()):
            self.zrun_ids.pop(zrun_uuid, None)
            self.dose_buffer.pop(zrun_uuid, None)

    def _flush_doses(self, zrun_uuid, zrun_id):
        """Flush buffered Event-2 doses for this zone run (Section 13.3.1).

        Event 2 (watering_fert_dose_complete) has no publisher yet, so the
        buffer is always empty and this clears nothing. When the fertigation
        path is wired, the Event-2 listener will append doses here and this
        method will INSERT each into fertigation_doses with `zrun_id`, then
        clear the buffer entry.
        """
        doses = self.dose_buffer.pop(zrun_uuid, None)
        if doses:
            # Reached only if a future Event-2 listener populated the buffer
            # before the INSERT flush was built. Do not silently drop them.
            self.log(
                f"{len(doses)} buffered dose(s) for zrun_uuid={zrun_uuid} "
                f"(zrun_id={zrun_id}) not written: fertigation_doses INSERT not "
                "built yet (lands with the Event-2 listener)",
                level="WARNING",
            )

    # ---------------------------------------------------------------- DB writes
    def _connect(self):
        """Open a connection with FK enforcement + a busy timeout (per-conn)."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _insert_cycle(self, params):
        """INSERT one watering_cycles row. Returns cycle_id or None on error."""
        conn = None
        try:
            conn = self._connect()
            cur = conn.execute(
                "INSERT INTO watering_cycles "
                "(start_time, trigger_type, rainfall_24h_mm, rainfall_72h_mm, "
                " temp_high_c) VALUES (?, ?, ?, ?, ?)",
                params,
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            self.error(f"watering_cycles INSERT failed: {exc}; params={params!r}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def _insert_zone_run(self, params):
        """INSERT one zone_runs row. Returns zrun_id or None on error."""
        conn = None
        try:
            conn = self._connect()
            cur = conn.execute(
                "INSERT INTO zone_runs "
                "(cycle_id, zone_id, weather_program, start_time, end_time, "
                " planned_duration_sec, actual_duration_sec, program_multiplier, "
                " fertigated, aborted, abort_reason, season, decision_criteria) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                params,
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            self.error(f"zone_runs INSERT failed: {exc}; params={params!r}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def _update_cycle(self, cycle_id, end_time, outcome, notes):
        """Close a watering_cycles row. Returns True on a matched UPDATE."""
        conn = None
        try:
            conn = self._connect()
            cur = conn.execute(
                "UPDATE watering_cycles "
                "SET end_time = ?, outcome = ?, notes = ? WHERE cycle_id = ?",
                (end_time, outcome, notes, cycle_id),
            )
            conn.commit()
            if cur.rowcount == 0:
                self.error(
                    "watering_cycles UPDATE matched no row for "
                    f"cycle_id={cycle_id}"
                )
                return False
            return True
        except sqlite3.Error as exc:
            self.error(
                f"watering_cycles UPDATE failed: {exc}; cycle_id={cycle_id}"
            )
            return False
        finally:
            if conn is not None:
                conn.close()

    # ------------------------------------------------------- audit breadcrumbs
    def _reject(self, event_name, problems, data):
        """Log a validation failure and record a system_events warning row."""
        msg = f"Rejected {event_name}: {'; '.join(problems)}; payload={data!r}"
        self.error(msg)
        self._system_event("event_rejected", "warning", msg)

    def _orphan(self, event_name, reason, data):
        """Log an unresolved-correlation drop and record a breadcrumb row."""
        msg = f"Dropped {event_name}: {reason}; payload={data!r}"
        self.log(msg, level="WARNING")
        self._system_event("event_unresolved", "warning", msg)

    def _system_event(self, event_type, severity, notes):
        """Best-effort audit row into system_events. Never raises.

        Uses a server-side UTC timestamp: the offending payload's own timestamp
        may be the field that was missing or malformed.
        """
        conn = None
        try:
            conn = self._connect()
            conn.execute(
                "INSERT INTO system_events "
                "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).strftime(self.TS_FORMAT),
                    event_type,
                    severity,
                    notes,
                ),
            )
            conn.commit()
        except sqlite3.Error:
            self.error(f"Could not record {event_type} row to system_events")
        finally:
            if conn is not None:
                conn.close()

    # ------------------------------------------------------------ HA sensor out
    def _set_cycle_active(self, active, cycle_uuid):
        """Reflect cycle-in-progress on the cycle-active binary_sensor.

        This is the publisher for binary_sensor.watering_cycle_active (§13.4).
        A set_state entity is virtual: it does NOT survive an AppDaemon restart.
        That is acceptable -- it is fire-and-forget reporting, not a safety
        input (Section 13.1). Never raises.
        """
        attributes = {
            "friendly_name": "Watering Cycle Active",
            "device_class": "running",
        }
        if active:
            attributes["cycle_uuid"] = cycle_uuid
        try:
            self.set_state(
                self.cycle_active_sensor,
                state=("on" if active else "off"),
                attributes=attributes,
            )
        except Exception as exc:  # AppDaemon set_state must not propagate here
            self.error(
                f"Could not set {self.cycle_active_sensor} "
                f"{'on' if active else 'off'}: {exc}"
            )

    # ---------------------------------------------------------------- coercion
    @staticmethod
    def _now():
        """UTC now (a method so tests can age a buffered decision)."""
        return datetime.now(timezone.utc)

    @staticmethod
    def _json_text(value):
        """Serialise decision criteria for a TEXT column; None stays NULL.

        A dict/list becomes compact, key-sorted JSON; a string is kept as-is.
        Anything unserialisable becomes NULL rather than failing the row.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value or None
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean(value):
        """Normalise a payload value to a stripped str, or None for empties.

        HA template output for an absent field commonly arrives as '',
        'unknown', or 'unavailable'; treat those as SQL NULL.
        """
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() in ("unknown", "unavailable"):
            return None
        return text

    @classmethod
    def _num(cls, value):
        """Coerce an optional numeric payload field to float, or None."""
        text = cls._clean(value)
        if text is None:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _int(cls, value):
        """Coerce an optional integer payload field to int, or None.

        Tolerates float-looking strings ('1.0') so a template that renders a
        number still parses.
        """
        text = cls._clean(value)
        if text is None:
            return None
        try:
            return int(float(text))
        except (TypeError, ValueError):
            return None

    def _duration_sec(self, start_time, end_time):
        """actual_duration_sec = end - start, in whole seconds; None if either
        timestamp is absent or unparseable."""
        if not start_time or not end_time:
            return None
        try:
            start = datetime.strptime(start_time, self.TS_FORMAT)
            end = datetime.strptime(end_time, self.TS_FORMAT)
        except (TypeError, ValueError) as exc:
            self.log(
                "Could not compute actual_duration_sec from "
                f"start={start_time!r} end={end_time!r}: {exc}",
                level="WARNING",
            )
            return None
        return int(round((end - start).total_seconds()))
