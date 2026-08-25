"""Logic test for db_export.DbSeasonalExport (stdlib only; no pytest needed).

Run from anywhere:

    python home-assistant/appdaemon/watering_db/tests/test_db_export.py

It builds a temporary SQLite database from the canonical docs/db_schema.sql,
inserts rows across two calendar years, stubs the AppDaemon `hass.Hass` base
class (only self.args/log/error are used by run_export), drives the real export,
and asserts the CSV output, year-filtering, header-only-when-empty behaviour, and
the system_events audit row. Exits non-zero on any failure.

NOT an AppDaemon app and NOT deployed: pull_public_repo.sh copies only the
top-level files in the app folder, so this tests/ subdirectory never reaches the
AppDaemon app dir. All setup is inside main() so merely importing this file has
no side effects (the sys.modules stubbing must never run inside a live AppDaemon).
"""

import csv
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
APP_PY = os.path.join(APP_DIR, "db_export.py")


def _load_app():
    """Stub the AppDaemon hassapi module, then import db_export by path."""
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

    spec = importlib.util.spec_from_file_location("db_export", APP_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_db(path):
    with open(SCHEMA, "r", encoding="utf-8") as fh:
        sql = fh.read()
    conn = sqlite3.connect(path)
    conn.executescript(sql)
    # one cycle in 2026 (kept) and one in 2025 (excluded from the 2026 export)
    conn.execute(
        "INSERT INTO watering_cycles (cycle_id, start_time, trigger_type) "
        "VALUES (1, '2026-05-01 06:00:00', 'scheduled')"
    )
    conn.execute(
        "INSERT INTO watering_cycles (cycle_id, start_time, trigger_type) "
        "VALUES (2, '2025-08-01 06:00:00', 'scheduled')"
    )
    conn.execute(
        "INSERT INTO zone_runs (zrun_id, cycle_id, zone_id, weather_program, start_time) "
        "VALUES (1, 1, 2, 'normal', '2026-05-01 06:05:00')"
    )
    conn.execute(
        "INSERT INTO fertigation_doses (dose_id, zrun_id, zone_id, timestamp) "
        "VALUES (1, 1, 2, '2026-05-01 06:06:00')"
    )
    # system_events left empty for 2026 to exercise header-only output
    conn.commit()
    conn.close()


def main():
    db_export = _load_app()

    tmp = tempfile.mkdtemp(prefix="dbexp_")
    db_path = os.path.join(tmp, "watering_ops.db")
    export_dir = os.path.join(tmp, "exports")
    _build_db(db_path)

    app = db_export.DbSeasonalExport()
    app.args = {"db_path": db_path, "export_dir": export_dir}
    app.db_path = db_path
    app.export_dir = export_dir
    app.trigger_event = "watering_seasonal_export"

    app.run_export("watering_seasonal_export", {"year": 2026}, {})

    failures = []

    def check(cond, label):
        print(("PASS" if cond else "FAIL"), "-", label)
        if not cond:
            failures.append(label)

    files = {
        "watering_cycles": os.path.join(export_dir, "watering_cycles_2026.csv"),
        "zone_runs": os.path.join(export_dir, "zone_runs_2026.csv"),
        "fertigation_doses": os.path.join(export_dir, "fertigation_doses_2026.csv"),
        "system_events": os.path.join(export_dir, "system_events_2026.csv"),
    }
    for name, path in files.items():
        check(os.path.exists(path), f"{name} CSV created")

    with open(files["watering_cycles"], newline="", encoding="utf-8") as fh:
        cycle_rows = list(csv.reader(fh))
    check(cycle_rows[0][0] == "cycle_id", "watering_cycles header present")
    check(len(cycle_rows) == 2, f"watering_cycles has 1 data row (got {len(cycle_rows) - 1})")
    check(any("2026-05-01 06:00:00" in row for row in cycle_rows[1:]), "2026 cycle present")
    check(
        not any("2025-08-01" in cell for row in cycle_rows[1:] for cell in row),
        "2025 cycle excluded",
    )

    with open(files["system_events"], newline="", encoding="utf-8") as fh:
        event_rows = list(csv.reader(fh))
    check(event_rows[0][0] == "event_id", "system_events header present")
    check(
        len(event_rows) == 1,
        f"system_events header-only (got {len(event_rows) - 1} data rows)",
    )

    conn = sqlite3.connect(db_path)
    audit = conn.execute(
        "SELECT severity, notes FROM system_events WHERE event_type = 'seasonal_export'"
    ).fetchall()
    conn.close()
    check(len(audit) == 1, f"one seasonal_export audit row (got {len(audit)})")
    if audit:
        check(audit[0][0] == "info", f"audit severity=info (got {audit[0][0]})")
        print("  audit notes:", audit[0][1])

    print("\nRESULT:", "ALL PASS" if not failures else f"{len(failures)} FAILURE(S): {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
