"""db_schema_init.py -- AppDaemon bootstrap for the watering_ops SQLite database.

Applies the schema in db_schema.sql idempotently on AppDaemon start-up. Every
statement in that file is `CREATE ... IF NOT EXISTS`, so re-running on every
start is safe and cheap. This is the ONLY step required to create the
operational database -- there is no manual SQL execution on HAOS.

Column migrations: `CREATE TABLE IF NOT EXISTS` never alters an existing table,
so a column added to db_schema.sql later would never reach an already-created
database. COLUMN_MIGRATIONS lists such columns; after the schema script runs,
any that are missing are added with ALTER TABLE ADD COLUMN (idempotent: a
present column is skipped). Only nullable columns belong here -- ADD COLUMN
cannot add a NOT NULL column without a default, nor change a CHECK (those need
a table rebuild, see the 2026-07-31 db_schema.sql change-log entry).

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

    # (table, column, column definition). KEEP IDENTICAL to db_schema.sql.
    COLUMN_MIGRATIONS = (
        # ADR-018 decision recording on zone_runs (§3.6 S5, 2026-09-23).
        (
            "zone_runs",
            "season",
            "TEXT CHECK (season IS NULL OR "
            "season IN ('spring', 'summer', 'fall', 'winter'))",
        ),
        ("zone_runs", "decision_criteria", "TEXT"),
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
            added = self._migrate_columns(conn)

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
            f"({len(self.EXPECTED_TABLES)} tables present; columns added: "
            f"{', '.join(added) if added else 'none'})",
            level="INFO",
        )

    def _migrate_columns(self, conn):
        """Add any COLUMN_MIGRATIONS column missing from its table.

        Returns the list of 'table.column' names added (empty when the database
        is already current). Raises sqlite3.Error to the caller, which logs it
        and reports the init as failed.
        """
        added = []
        for table, column, definition in self.COLUMN_MIGRATIONS:
            # table/column come from the fixed tuple above, not user input.
            present = {
                row[1] for row in conn.execute(f"PRAGMA table_info({table});")
            }
            if column in present:
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
            added.append(f"{table}.{column}")
        if added:
            conn.commit()
        return added
