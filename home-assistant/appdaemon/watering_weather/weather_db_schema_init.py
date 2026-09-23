"""weather_db_schema_init.py -- AppDaemon bootstrap for the watering_weather DB.

Applies the schema in weather_schema.sql idempotently on AppDaemon start-up.
Every statement in that file is `CREATE ... IF NOT EXISTS`, so re-running on
every start is safe and cheap. This is the ONLY step required to create the
weather-observations database -- there is no manual SQL execution on HAOS.

Sibling of the watering_ops bootstrap (../watering_db/db_schema_init.py); kept a
SEPARATE app + module (distinct class/module/app-key names) so the two never
collide in AppDaemon's global module namespace. The weather DB is a separate
SQLite file with a different lifecycle (continuous twice-daily series) and
retention (long-term, no pruning) -- see ADR-018.

Canonical design:
  docs/programming-notes.md (ADR-018)   -- the weather DB rationale
  docs/impl_roadmap.md Section 3.6
  docs/weather_schema.sql               -- the schema this app applies

apps.yaml configuration (see the sibling apps.yaml):
  db_path      -- absolute path to the SQLite file (must be reachable by the
                  AppDaemon container and inside the HA backup set)
  schema_path  -- absolute path to the deployed copy of docs/weather_schema.sql
                  (refreshed from the canonical docs/ copy by pull_public_repo.sh)
"""

import os
import sqlite3

import appdaemon.plugins.hass.hassapi as hass


class WeatherDbSchemaInit(hass.Hass):
    """Create / verify the watering_weather schema on start-up."""

    EXPECTED_TABLES = (
        "weather_snapshots",
        "zone_decisions",
    )

    def initialize(self):
        db_path = self.args.get("db_path", "/homeassistant/watering_weather.db")
        schema_path = self.args.get(
            "schema_path",
            os.path.join(os.path.dirname(__file__), "weather_schema.sql"),
        )

        if not os.path.exists(schema_path):
            self.error(
                f"Schema file not found at {schema_path}; "
                f"watering_weather database NOT initialised"
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
                    f"watering_weather schema incomplete after init at {db_path}; "
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
            f"watering_weather schema verified/created at {db_path} "
            f"({len(self.EXPECTED_TABLES)} tables present)",
            level="INFO",
        )
