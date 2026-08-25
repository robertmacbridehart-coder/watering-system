"""db_schema_init.py -- AppDaemon bootstrap for the watering_ops SQLite database.

Applies the schema in db_schema.sql idempotently on AppDaemon start-up. Every
statement in that file is `CREATE ... IF NOT EXISTS`, so re-running on every
start is safe and cheap. This is the ONLY step required to create the
operational database -- there is no manual SQL execution on HAOS.

This is the first and (for now) only AppDaemon app for the watering database.
The db_writer / db_queries / db_export apps come later (Phase 3.5 continuation,
after the state-machine HA events exist).

Canonical design:
  docs/architecture.md Section 13
  docs/programming-notes.md (ADR-011)
  docs/db_schema.sql  (the schema this app applies)

apps.yaml configuration (see the sibling apps.yaml):
  db_path      -- absolute path to the SQLite file (must be reachable by the
                  AppDaemon container and inside the HA backup set)
  schema_path  -- absolute path to the deployed copy of db_schema.sql
"""

import os
import sqlite3

import appdaemon.plugins.hass.hassapi as hass


class DbSchemaInit(hass.Hass):
    """Create / verify the watering_ops schema on start-up."""

    EXPECTED_TABLES = (
        "watering_cycles",
        "zone_runs",
        "fertigation_doses",
        "system_events",
    )

    def initialize(self):
        db_path = self.args.get("db_path", "/homeassistant/watering_ops.db")
        schema_path = self.args.get(
            "schema_path",
            os.path.join(os.path.dirname(__file__), "db_schema.sql"),
        )

        if not os.path.exists(schema_path):
            self.error(
                f"Schema file not found at {schema_path}; "
                f"watering_ops database NOT initialised"
            )
            return

        try:
            with open(schema_path, "r", encoding="utf-8") as handle:
                schema_sql = handle.read()
        except OSError as exc:
            self.error(f"Could not read schema file {schema_path}: {exc}")
            return

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            # journal_mode is a persistent property of the file; setting it once
            # is sufficient. foreign_keys and busy_timeout are per-connection
            # (every future writer/query connection must set them too).
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript(schema_sql)
            conn.commit()

            # Verify execution rather than trusting that no exception == success.
            present = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table';"
                ).fetchall()
            }
            missing = set(self.EXPECTED_TABLES) - present
            if missing:
                self.error(
                    f"watering_ops schema incomplete after init at {db_path}; "
                    f"missing tables: {sorted(missing)}"
                )
                return
        except sqlite3.Error as exc:
            self.error(f"Schema initialisation failed for {db_path}: {exc}")
            return
        finally:
            if conn is not None:
                conn.close()

        self.log(
            f"watering_ops schema verified/created at {db_path} "
            f"({len(self.EXPECTED_TABLES)} tables present)",
            level="INFO",
        )
