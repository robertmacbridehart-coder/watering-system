"""Logic test for db_writer.DbWriter (stdlib only; no pytest needed).

Run from anywhere:

    python home-assistant/appdaemon/watering_db/tests/test_db_writer.py

It builds a temporary SQLite database from the canonical docs/db_schema.sql,
stubs the AppDaemon `hass.Hass` base class (capturing set_state calls and log
output), and drives the real Event 1/3/4 handlers to assert:

  * happy path: cycle opens, zone_run inserts with a computed
    actual_duration_sec + FK to the cycle, cycle closes;
  * binary_sensor.watering_cycle_active goes on at Event 1, off at Event 4;
  * `fertigated` is DERIVED from the dose buffer (1 when seeded, else 0);
  * in-memory correlation is dropped once the cycle closes;
  * unresolved correlation (unknown cycle_uuid) writes no row but records a
    system_events breadcrumb;
  * a malformed payload is rejected (no row) with a system_events reject row;
  * S5 decision recording: Event 7 is buffered, attached at Event 1 and written
    as zone_runs.season + decision_criteria at Event 3; a stale, missing or
    partial decision -> NULL criteria, an invalid season -> NULL, and the run
    row is always still written.

Exits non-zero on any failure.

NOT an AppDaemon app and NOT deployed: pull_public_repo.sh copies only the
top-level files in the app folder, so this tests/ subdirectory never reaches the
AppDaemon app dir. All setup is inside main() so merely importing this file has
no side effects (the sys.modules stubbing must never run inside a live AppDaemon).
"""

import importlib.util
import os
import sqlite3
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)  # .../appdaemon/watering_db
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCHEMA = os.path.join(REPO, "docs", "db_schema.sql")
APP_PY = os.path.join(APP_DIR, "db_writer.py")


def _load_app():
    """Stub the AppDaemon hassapi module, then import db_writer by path.

    The stub Hass records set_state calls in self.states so assertions can read
    the published binary_sensor, and swallows log/error to stdout.
    """
    hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")

    class _Hass:
        def __init__(self):
            self.args = {}
            self.states = {}

        def log(self, msg, level="INFO"):
            print(f"[log/{level}] {msg}")

        def error(self, msg, level="ERROR"):
            print(f"[error/{level}] {msg}")

        def listen_event(self, *a, **k):
            pass

        def set_state(self, entity_id, state=None, attributes=None):
            self.states[entity_id] = {
                "state": state,
                "attributes": attributes or {},
            }

    hassapi.Hass = _Hass
    sys.modules["appdaemon"] = types.ModuleType("appdaemon")
    sys.modules["appdaemon.plugins"] = types.ModuleType("appdaemon.plugins")
    sys.modules["appdaemon.plugins.hass"] = types.ModuleType(
        "appdaemon.plugins.hass"
    )
    sys.modules["appdaemon.plugins.hass.hassapi"] = hassapi

    spec = importlib.util.spec_from_file_location("db_writer", APP_PY)
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


def _new_app(db_writer, db_path):
    app = db_writer.DbWriter()
    app.args = {"db_path": db_path}
    app.initialize()
    return app


def _query(db_path, sql, params=()):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def main():
    db_writer = _load_app()

    tmp = tempfile.mkdtemp(prefix="dbwriter_")
    db_path = os.path.join(tmp, "watering_ops.db")
    _build_db(db_path)

    failures = []

    def check(cond, label):
        print(("PASS" if cond else "FAIL"), "-", label)
        if not cond:
            failures.append(label)

    # ---- Happy path: Event 1 -> Event 3 -> Event 4 --------------------------
    app = _new_app(db_writer, db_path)
    cuuid = "c-20260816060000000000"

    app.on_preflight(
        "watering_preflight_complete",
        {
            "cycle_uuid": cuuid,
            "start_time": "2026-08-16 06:00:00",
            "trigger_type": "scheduled",
            "rainfall_24h_mm": "1.5",
            "rainfall_72h_mm": "",          # -> NULL
            "temp_high_c": "unavailable",   # -> NULL
        },
        {},
    )

    cycles = _query(
        db_path,
        "SELECT cycle_id, start_time, trigger_type, rainfall_24h_mm, "
        "rainfall_72h_mm, temp_high_c, end_time, outcome FROM watering_cycles",
    )
    check(len(cycles) == 1, f"one watering_cycles row (got {len(cycles)})")
    if cycles:
        c = cycles[0]
        cid = c[0]
        check(c[1] == "2026-08-16 06:00:00", "cycle start_time stored")
        check(c[2] == "scheduled", "cycle trigger_type stored")
        check(c[3] == 1.5, f"rainfall_24h_mm=1.5 (got {c[3]!r})")
        check(c[4] is None, "rainfall_72h_mm NULL from empty string")
        check(c[5] is None, "temp_high_c NULL from 'unavailable'")
        check(c[6] is None and c[7] is None, "end_time/outcome NULL pre-close")
    else:
        cid = None

    active = app.states.get("binary_sensor.watering_cycle_active")
    check(
        active is not None and active["state"] == "on",
        "cycle_active sensor ON after Event 1",
    )
    check(
        bool(active) and active["attributes"].get("cycle_uuid") == cuuid,
        "cycle_active carries cycle_uuid attribute",
    )

    zuuid = cuuid + "-z2"
    app.on_zone_run(
        "watering_zone_run_complete",
        {
            "cycle_uuid": cuuid,
            "zrun_uuid": zuuid,
            "zone_id": "2",
            "weather_program": "normal",
            "start_time": "2026-08-16 06:05:00",
            "end_time": "2026-08-16 06:20:00",  # 900 s
            "planned_duration_sec": "840",
            "aborted": "0",
        },
        {},
    )

    zruns = _query(
        db_path,
        "SELECT zrun_id, cycle_id, zone_id, weather_program, start_time, "
        "end_time, planned_duration_sec, actual_duration_sec, fertigated, "
        "aborted FROM zone_runs",
    )
    check(len(zruns) == 1, f"one zone_runs row (got {len(zruns)})")
    if zruns:
        z = zruns[0]
        check(z[1] == cid, "zone_run FK cycle_id matches the open cycle")
        check(z[2] == 2, "zone_run zone_id=2")
        check(z[3] == "normal", "zone_run weather_program stored")
        check(z[6] == 840, "planned_duration_sec stored")
        check(z[7] == 900, f"actual_duration_sec computed 900 (got {z[7]!r})")
        check(z[8] == 0, "fertigated derived 0 (empty dose buffer)")
        check(z[9] == 0, "aborted 0")

    app.on_cycle_complete(
        "watering_cycle_complete",
        {
            "cycle_uuid": cuuid,
            "end_time": "2026-08-16 06:25:00",
            "outcome": "completed",
            "notes": "all zones nominal",
        },
        {},
    )

    closed = _query(
        db_path,
        "SELECT end_time, outcome, notes FROM watering_cycles WHERE cycle_id = ?",
        (cid,),
    )
    check(
        closed and closed[0] == ("2026-08-16 06:25:00", "completed",
                                 "all zones nominal"),
        f"cycle closed with end/outcome/notes (got {closed})",
    )
    active = app.states.get("binary_sensor.watering_cycle_active")
    check(
        active is not None and active["state"] == "off",
        "cycle_active sensor OFF after Event 4",
    )
    check(
        not app.cycle_ids and not app.zrun_ids and not app.cycle_zruns,
        "in-memory correlation dropped after cycle close",
    )

    # ---- fertigated derivation: seed the dose buffer -> 1 -------------------
    app2 = _new_app(db_writer, db_path)
    cuuid2 = "c-20260816070000000000"
    app2.on_preflight(
        "watering_preflight_complete",
        {
            "cycle_uuid": cuuid2,
            "start_time": "2026-08-16 07:00:00",
            "trigger_type": "manual",
        },
        {},
    )
    zuuid2 = cuuid2 + "-z1"
    app2.dose_buffer[zuuid2] = [{"placeholder": "dose"}]  # simulate an Event 2
    app2.on_zone_run(
        "watering_zone_run_complete",
        {
            "cycle_uuid": cuuid2,
            "zrun_uuid": zuuid2,
            "zone_id": "1",
            "weather_program": "heavy",
            "start_time": "2026-08-16 07:05:00",
            "end_time": "2026-08-16 07:10:00",
            "aborted": "0",
        },
        {},
    )
    fert = _query(
        db_path,
        "SELECT fertigated FROM zone_runs WHERE weather_program = 'heavy'",
    )
    check(fert and fert[0][0] == 1, "fertigated derived 1 when buffer non-empty")
    check(zuuid2 not in app2.dose_buffer, "dose buffer cleared after flush")

    # ---- unresolved correlation: unknown cycle_uuid -------------------------
    app3 = _new_app(db_writer, db_path)
    zr_before = _query(db_path, "SELECT COUNT(*) FROM zone_runs")[0][0]
    app3.on_zone_run(
        "watering_zone_run_complete",
        {
            "cycle_uuid": "c-does-not-exist",
            "zrun_uuid": "z-orphan",
            "zone_id": "3",
            "weather_program": "light",
            "start_time": "2026-08-16 08:00:00",
            "aborted": "0",
        },
        {},
    )
    zr_after = _query(db_path, "SELECT COUNT(*) FROM zone_runs")[0][0]
    check(zr_after == zr_before, "orphan Event 3 inserts no zone_run")
    orphan = _query(
        db_path,
        "SELECT COUNT(*) FROM system_events WHERE event_type = 'event_unresolved'",
    )[0][0]
    check(orphan == 1, f"one event_unresolved breadcrumb (got {orphan})")

    # ---- rejection: malformed Event 1 (bad trigger_type) --------------------
    app4 = _new_app(db_writer, db_path)
    cyc_before = _query(db_path, "SELECT COUNT(*) FROM watering_cycles")[0][0]
    app4.on_preflight(
        "watering_preflight_complete",
        {
            "cycle_uuid": "c-bad",
            "start_time": "2026-08-16 09:00:00",
            "trigger_type": "bogus",  # not in the controlled vocabulary
        },
        {},
    )
    cyc_after = _query(db_path, "SELECT COUNT(*) FROM watering_cycles")[0][0]
    check(cyc_after == cyc_before, "rejected Event 1 inserts no cycle")
    rej = _query(
        db_path,
        "SELECT COUNT(*) FROM system_events WHERE event_type = 'event_rejected'",
    )[0][0]
    check(rej == 1, f"one event_rejected breadcrumb (got {rej})")

    # ---- S5 decision recording: Event 7 -> Event 1 -> Event 3 ----------------
    import datetime as _dt
    import json as _json

    def run_cycle(app, cuuid, zone, season, start):
        app.on_preflight(
            "watering_preflight_complete",
            {"cycle_uuid": cuuid, "start_time": start, "trigger_type": "scheduled"},
            {},
        )
        app.on_zone_run(
            "watering_zone_run_complete",
            {
                "cycle_uuid": cuuid,
                "zrun_uuid": f"{cuuid}-z{zone}",
                "zone_id": str(zone),
                "weather_program": "normal",
                "start_time": start,
                "end_time": start,
                "aborted": "0",
                "season": season,
            },
            {},
        )
        return _query(
            db_path,
            "SELECT season, decision_criteria FROM zone_runs "
            "WHERE zrun_id = (SELECT MAX(zrun_id) FROM zone_runs)",
        )[0]

    crit1 = {"branch": "warm", "skip_reason": None, "enabled": True, "due": True}
    decision = {
        "window": "morning",
        "zone_decisions": [
            {"zone_id": 1, "season": "fall", "computed_program": "normal",
             "decision_criteria": crit1},
            {"zone_id": 2, "season": "fall", "computed_program": "off",
             "decision_criteria": {"branch": "warm", "skip_reason": "moisture_wet"}},
            {"zone_id": 3},                      # no criteria -> skipped
            "not-a-dict",                        # malformed -> skipped
        ],
    }
    app5 = _new_app(db_writer, db_path)
    app5.on_decision("watering_decision_applied", decision, {})
    check(app5.pending_decision is not None
          and sorted(app5.pending_decision["zones"]) == [1, 2],
          "Event 7 buffers zones with criteria (malformed items skipped)")
    season, criteria = run_cycle(app5, "c-s5-1", 1, "fall", "2026-09-24 04:00:00")
    check(season == "fall", f"zone_runs.season stored (got {season!r})")
    check(criteria is not None and _json.loads(criteria) == crit1,
          f"zone_runs.decision_criteria = the zone's criteria JSON (got {criteria!r})")
    check(app5.pending_decision is None, "pending decision consumed at Event 1")
    check("c-s5-1" in app5.cycle_decisions, "decision attached to the cycle")
    app5.on_cycle_complete(
        "watering_cycle_complete",
        {"cycle_uuid": "c-s5-1", "end_time": "2026-09-24 04:10:00",
         "outcome": "completed"},
        {},
    )
    check("c-s5-1" not in app5.cycle_decisions, "cycle decision dropped at Event 4")

    # stale decision (older than DECISION_MAX_AGE_SEC) is NOT attached
    app6 = _new_app(db_writer, db_path)
    app6.on_decision("watering_decision_applied", decision, {})
    app6.pending_decision["received_at"] -= _dt.timedelta(
        seconds=app6.DECISION_MAX_AGE_SEC + 1)
    season, criteria = run_cycle(app6, "c-s5-2", 1, "fall", "2026-09-24 05:00:00")
    check(criteria is None and season == "fall",
          "stale decision discarded -> criteria NULL, season still stored")
    check(app6.pending_decision is None, "stale decision cleared")

    # no Event 7 at all (e.g. AppDaemon restarted after window_check)
    app7 = _new_app(db_writer, db_path)
    season, criteria = run_cycle(app7, "c-s5-3", 2, "summer", "2026-09-24 06:00:00")
    check(criteria is None and season == "summer",
          "no buffered decision -> criteria NULL, row still written")

    # invalid season -> NULL, row still written (never rejected)
    app8 = _new_app(db_writer, db_path)
    zr_before = _query(db_path, "SELECT COUNT(*) FROM zone_runs")[0][0]
    season, criteria = run_cycle(app8, "c-s5-4", 3, "monsoon", "2026-09-24 07:00:00")
    zr_after = _query(db_path, "SELECT COUNT(*) FROM zone_runs")[0][0]
    check(season is None and zr_after == zr_before + 1,
          "invalid season -> NULL, zone_run still inserted")

    # zone without criteria in the decision -> NULL for that zone only
    app9 = _new_app(db_writer, db_path)
    app9.on_decision("watering_decision_applied", decision, {})
    season, criteria = run_cycle(app9, "c-s5-5", 3, "fall", "2026-09-24 08:00:00")
    check(criteria is None, "zone missing from the decision -> criteria NULL")

    # zone_decisions not a list -> ignored, nothing buffered
    app10 = _new_app(db_writer, db_path)
    app10.on_decision("watering_decision_applied", {"zone_decisions": 42}, {})
    check(app10.pending_decision is None, "non-list zone_decisions ignored")
    app10.on_decision("watering_decision_applied",
                      {"zone_decisions": _json.dumps(decision["zone_decisions"][:2])}, {})
    check(app10.pending_decision is not None
          and sorted(app10.pending_decision["zones"]) == [1, 2],
          "JSON-string zone_decisions accepted")

    print(
        "\nRESULT:",
        "ALL PASS" if not failures else f"{len(failures)} FAILURE(S): {failures}",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
