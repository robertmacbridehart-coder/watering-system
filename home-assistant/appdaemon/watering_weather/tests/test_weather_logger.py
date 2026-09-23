"""Logic test for weather_logger.WeatherLogger (stdlib only; no pytest needed).

Run from anywhere:

    python home-assistant/appdaemon/watering_weather/tests/test_weather_logger.py

It builds a temporary SQLite database from the canonical docs/weather_schema.sql,
stubs the AppDaemon `hass.Hass` base class (swallowing log/error to stdout), and
drives the real Event 6 handler to assert:

  * happy path: one weather_snapshots row + four zone_decisions children with the
    correct FK; empty/'unavailable' fields become SQL NULL; a dict decision_criteria
    / raw payload is serialised to a JSON string; a bool raining_now -> 0/1;
  * would_water is DERIVED (program != 'off') when the payload omits it;
  * a bad window_name is rejected (no rows written);
  * a missing/empty zone_decisions list is rejected (no rows);
  * ATOMICITY: a child that passes app-level validation but violates a schema CHECK
    (moisture_sensor_count = -1) rolls the whole snapshot back -- no orphan parent.

Exits non-zero on any failure.

NOT an AppDaemon app and NOT deployed: pull_public_repo.sh copies only the
top-level files in the app folder, so this tests/ subdirectory never reaches the
AppDaemon app dir. All setup is inside main() so importing this file has no side
effects (the sys.modules stubbing must never run inside a live AppDaemon).
"""

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)  # .../appdaemon/watering_weather
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCHEMA = os.path.join(REPO, "docs", "weather_schema.sql")
APP_PY = os.path.join(APP_DIR, "weather_logger.py")


def _load_app():
    """Stub the AppDaemon hassapi module, then import weather_logger by path."""
    hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")

    class _Hass:
        def __init__(self):
            self.args = {}

        def log(self, msg, level="INFO"):
            print(f"[log/{level}] {msg}")

        def error(self, msg, level="ERROR"):
            print(f"[error/{level}] {msg}")

        def listen_event(self, *a, **k):
            pass

    hassapi.Hass = _Hass
    sys.modules["appdaemon"] = types.ModuleType("appdaemon")
    sys.modules["appdaemon.plugins"] = types.ModuleType("appdaemon.plugins")
    sys.modules["appdaemon.plugins.hass"] = types.ModuleType("appdaemon.plugins.hass")
    sys.modules["appdaemon.plugins.hass.hassapi"] = hassapi

    spec = importlib.util.spec_from_file_location("weather_logger", APP_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_db(path):
    with open(SCHEMA, "r", encoding="utf-8") as fh:
        sql = fh.read()
    conn = sqlite3.connect(path)
    conn.executescript(sql)
    conn.commit()
    conn.close()


def _new_app(mod, db_path):
    app = mod.WeatherLogger()
    app.args = {"db_path": db_path}
    app.initialize()
    return app


def _query(db_path, sql, params=()):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def _count(db_path, table):
    return _query(db_path, f"SELECT COUNT(*) FROM {table}")[0][0]


def main():
    mod = _load_app()
    tmp = tempfile.mkdtemp(prefix="wxlogger_")
    db_path = os.path.join(tmp, "watering_weather.db")
    _build_db(db_path)

    failures = []

    def check(cond, label):
        print(("PASS" if cond else "FAIL"), "-", label)
        if not cond:
            failures.append(label)

    app = _new_app(mod, db_path)

    # ---- Happy path -------------------------------------------------------
    app.on_event(
        "watering_weather_snapshot",
        {
            "observed_at": "2026-08-30 06:00:00",
            "window_name": "morning",
            "weather_available": "1",
            "temp_c": "18.2",
            "temp_high_forecast_c": "26.8",
            "temp_avg_high_3day_c": "",          # -> NULL
            "rain_24h_mm": "0.1",
            "rain_72h_mm": "8.2",
            "raining_now": "false",              # -> 0
            "rain_source": "dwd",
            "forecast_pop_today": "40",
            "forecast_rain_today_mm": "0",
            "humidity_pct": "unavailable",       # -> NULL
            "raw": {"soil_moisture_1": 51, "soil_ec_1": 320},   # dict -> JSON
            "zone_decisions": [
                {"zone_id": 1, "season": "summer", "computed_program": "off",
                 "would_water": 0, "moisture_pct": 56.0, "moisture_sensor_count": 3,
                 "decision_criteria": {"branch": "wet_skip"}},
                {"zone_id": 2, "season": "summer", "computed_program": "heavy",
                 "program_multiplier": 1.0, "moisture_pct": "22",
                 "moisture_sensor_count": "1",           # would_water OMITTED -> derived 1
                 "decision_criteria": {"branch": "dry"}},
                {"zone_id": 3, "season": "summer", "computed_program": "off",
                 "would_water": 0, "moisture_sensor_count": 0,
                 "decision_criteria": "{\"fallback\":1}"},   # criteria already a string
                {"zone_id": 4, "season": "summer", "computed_program": "booster",
                 "program_multiplier": 0.5, "would_water": 1, "moisture_pct": 50.0,
                 "moisture_sensor_count": 0,
                 "decision_criteria": {"branch": "booster"}},
            ],
        },
        {},
    )

    snaps = _query(
        db_path,
        "SELECT snapshot_id, observed_at, window_name, source, weather_available, "
        "temp_avg_high_3day_c, raining_now, rain_source, humidity_pct, raw "
        "FROM weather_snapshots",
    )
    check(len(snaps) == 1, f"one weather_snapshots row (got {len(snaps)})")
    sid = snaps[0][0] if snaps else None
    if snaps:
        s = snaps[0]
        check(s[2] == "morning", "window_name stored")
        check(s[3] == "brightsky", "source defaults to brightsky")
        check(s[4] == 1, "weather_available coerced 1")
        check(s[5] is None, "temp_avg_high_3day_c NULL from empty string")
        check(s[6] == 0, "raining_now 'false' -> 0")
        check(s[7] == "dwd", "rain_source stored")
        check(s[8] is None, "humidity_pct NULL from 'unavailable'")
        check(s[9] and json.loads(s[9]).get("soil_moisture_1") == 51,
              "raw dict serialised to JSON string")

    decs = _query(
        db_path,
        "SELECT zone_id, computed_program, program_multiplier, would_water, "
        "moisture_pct, moisture_sensor_count, decision_criteria, snapshot_id "
        "FROM zone_decisions ORDER BY zone_id",
    )
    check(len(decs) == 4, f"four zone_decisions rows (got {len(decs)})")
    if len(decs) == 4:
        check(all(d[7] == sid for d in decs), "all decisions FK the snapshot")
        z2 = decs[1]
        check(z2[3] == 1, "zone 2 would_water DERIVED 1 (omitted, program=heavy)")
        check(abs(z2[4] - 22.0) < 1e-9, "zone 2 moisture_pct coerced from '22'")
        check(z2[5] == 1, "zone 2 moisture_sensor_count coerced from '1'")
        z1 = decs[0]
        check(z1[3] == 0, "zone 1 would_water 0")
        check(json.loads(z1[6]).get("branch") == "wet_skip",
              "zone 1 decision_criteria dict -> JSON")
        z3 = decs[2]
        check(json.loads(z3[6]).get("fallback") == 1,
              "zone 3 decision_criteria string passed through as JSON")
        z4 = decs[3]
        check(z4[1] == "booster" and abs(z4[2] - 0.5) < 1e-9,
              "zone 4 booster + multiplier 0.5")

    # ---- Reject: bad window_name -----------------------------------------
    before = _count(db_path, "weather_snapshots")
    app.on_event("watering_weather_snapshot",
                 {"observed_at": "2026-08-30 18:00:00", "window_name": "afternoon",
                  "zone_decisions": [{"zone_id": 1, "season": "summer",
                                      "computed_program": "off", "would_water": 0,
                                      "decision_criteria": {}}]},
                 {})
    check(_count(db_path, "weather_snapshots") == before,
          "bad window_name inserts no snapshot")

    # ---- Reject: missing zone_decisions ----------------------------------
    before = _count(db_path, "weather_snapshots")
    app.on_event("watering_weather_snapshot",
                 {"observed_at": "2026-08-30 18:00:00", "window_name": "evening"},
                 {})
    check(_count(db_path, "weather_snapshots") == before,
          "missing zone_decisions inserts no snapshot")

    # ---- Atomicity: schema-CHECK failure on a child rolls back the parent -
    snaps_before = _count(db_path, "weather_snapshots")
    decs_before = _count(db_path, "zone_decisions")
    app.on_event(
        "watering_weather_snapshot",
        {
            "observed_at": "2026-08-30 18:00:00", "window_name": "evening",
            "zone_decisions": [
                {"zone_id": 1, "season": "summer", "computed_program": "off",
                 "would_water": 0, "moisture_sensor_count": 0,
                 "decision_criteria": {"ok": 1}},
                # passes app validation but violates CHECK (moisture_sensor_count >= 0)
                {"zone_id": 2, "season": "summer", "computed_program": "normal",
                 "would_water": 1, "moisture_sensor_count": -1,
                 "decision_criteria": {"bad": 1}},
            ],
        },
        {},
    )
    check(_count(db_path, "weather_snapshots") == snaps_before,
          "atomic rollback: no orphan snapshot on child CHECK failure")
    check(_count(db_path, "zone_decisions") == decs_before,
          "atomic rollback: no partial zone_decisions")

    print("\nRESULT:",
          "ALL PASS" if not failures else f"{len(failures)} FAILURE(S): {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
