"""Logic test for db_schema_init.DbSchemaInit (stdlib only; no pytest needed).

Run from anywhere:

    python home-assistant/appdaemon/watering_db/tests/test_db_schema_init.py

Drives the real bootstrap against temporary SQLite files built from the canonical
docs/db_schema.sql and asserts the column migration (COLUMN_MIGRATIONS):

  * fresh database: every table + the S5 zone_runs columns exist, nothing to add;
  * pre-S5 database (zone_runs WITHOUT season / decision_criteria, holding a row):
    the columns are added, the existing row survives with NULLs, and the season
    CHECK is enforced on new writes;
  * re-running is idempotent (nothing added the second time);
  * COLUMN_MIGRATIONS and db_schema.sql agree (a fresh DB needs no migration).

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
APP_PY = os.path.join(APP_DIR, "db_schema_init.py")

# zone_runs exactly as it was created before §3.6 S5 (2026-09-23).
PRE_S5_ZONE_RUNS = """
CREATE TABLE zone_runs (
    zrun_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id              INTEGER NOT NULL,
    zone_id               INTEGER NOT NULL CHECK (zone_id BETWEEN 1 AND 4),
    weather_program       TEXT    NOT NULL
                            CHECK (weather_program IN
                                   ('off', 'light', 'normal', 'heavy')),
    start_time            TEXT    NOT NULL,
    end_time              TEXT,
    planned_duration_sec  INTEGER,
    actual_duration_sec   INTEGER,
    program_multiplier    REAL,
    fertigated            INTEGER NOT NULL DEFAULT 0
                            CHECK (fertigated IN (0, 1)),
    aborted               INTEGER NOT NULL DEFAULT 0
                            CHECK (aborted IN (0, 1)),
    abort_reason          TEXT,
    FOREIGN KEY (cycle_id) REFERENCES watering_cycles (cycle_id)
);
"""


def _load_app():
    """Stub the AppDaemon hassapi module, then import db_schema_init by path."""
    hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")

    class _Hass:
        def __init__(self):
            self.args = {}
            self.logs = []
            self.errors = []

        def log(self, msg, level="INFO"):
            self.logs.append(msg)
            print(f"[log/{level}] {msg}")

        def error(self, msg, level="ERROR"):
            self.errors.append(msg)
            print(f"[error/{level}] {msg}")

    hassapi.Hass = _Hass
    sys.modules["appdaemon"] = types.ModuleType("appdaemon")
    sys.modules["appdaemon.plugins"] = types.ModuleType("appdaemon.plugins")
    sys.modules["appdaemon.plugins.hass"] = types.ModuleType("appdaemon.plugins.hass")
    sys.modules["appdaemon.plugins.hass.hassapi"] = hassapi

    spec = importlib.util.spec_from_file_location("db_schema_init", APP_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_init(module, db_path):
    app = module.DbSchemaInit()
    app.args = {"db_path": db_path, "schema_path": SCHEMA}
    app.initialize()
    return app


def _columns(db_path, table):
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table});")]
    conn.close()
    return cols


def main():
    module = _load_app()
    tmp = tempfile.mkdtemp(prefix="dbinit_")
    failures = []

    def check(cond, label):
        print(("PASS" if cond else "FAIL"), "-", label)
        if not cond:
            failures.append(label)

    # ---- fresh database ------------------------------------------------------
    fresh = os.path.join(tmp, "fresh.db")
    app = _run_init(module, fresh)
    cols = _columns(fresh, "zone_runs")
    check(not app.errors, "fresh DB: no errors")
    check("season" in cols and "decision_criteria" in cols,
          "fresh DB: zone_runs has season + decision_criteria")
    check(any("columns added: none" in m for m in app.logs),
          "fresh DB: schema file already current (nothing to migrate)")

    # ---- pre-S5 database holding a row ---------------------------------------
    old = os.path.join(tmp, "old.db")
    conn = sqlite3.connect(old)
    # The pre-S5 zone_runs first; the current schema script then creates the other
    # tables and (CREATE TABLE IF NOT EXISTS) leaves the old zone_runs untouched --
    # exactly the live Green's state before this migration.
    conn.executescript(PRE_S5_ZONE_RUNS)
    with open(SCHEMA, "r", encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.execute(
        "INSERT INTO watering_cycles (cycle_id, start_time, trigger_type) "
        "VALUES (1, '2026-08-16 06:00:00', 'scheduled')"
    )
    conn.execute(
        "INSERT INTO zone_runs (zrun_id, cycle_id, zone_id, weather_program, start_time) "
        "VALUES (1, 1, 2, 'normal', '2026-08-16 06:05:00')"
    )
    conn.commit()
    conn.close()
    check("season" not in _columns(old, "zone_runs"), "pre-S5 DB: season absent before init")

    app = _run_init(module, old)
    cols = _columns(old, "zone_runs")
    check(not app.errors, "pre-S5 DB: no errors")
    check("season" in cols and "decision_criteria" in cols,
          "pre-S5 DB: season + decision_criteria added")
    check(any("zone_runs.season" in m and "zone_runs.decision_criteria" in m
              for m in app.logs), "pre-S5 DB: log names the added columns")

    conn = sqlite3.connect(old)
    legacy = conn.execute(
        "SELECT zrun_id, weather_program, season, decision_criteria FROM zone_runs"
    ).fetchall()
    check(legacy == [(1, "normal", None, None)], f"legacy row preserved with NULLs (got {legacy})")
    conn.execute(
        "INSERT INTO zone_runs (cycle_id, zone_id, weather_program, start_time, "
        "season, decision_criteria) VALUES (1, 1, 'light', '2026-09-24 04:00:00', "
        "'fall', '{\"branch\":\"cool\"}')"
    )
    conn.commit()
    try:
        conn.execute(
            "INSERT INTO zone_runs (cycle_id, zone_id, weather_program, start_time, "
            "season) VALUES (1, 1, 'light', '2026-09-24 05:00:00', 'monsoon')"
        )
        conn.commit()
        check(False, "season CHECK rejects an invalid value")
    except sqlite3.IntegrityError:
        check(True, "season CHECK rejects an invalid value")
    conn.close()

    # ---- idempotent re-run ---------------------------------------------------
    app = _run_init(module, old)
    check(not app.errors and any("columns added: none" in m for m in app.logs),
          "re-run: nothing added, no errors")
    check(_columns(old, "zone_runs").count("season") == 1, "re-run: no duplicate column")

    print("\nRESULT:", "ALL PASS" if not failures else f"{len(failures)} FAILURE(S): {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
