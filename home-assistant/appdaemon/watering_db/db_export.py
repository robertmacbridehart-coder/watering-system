"""db_export.py -- AppDaemon app: seasonal CSV export of the watering_ops DB.

On receiving the trigger event (default `watering_seasonal_export`, fired by the
HA winterization automation), this app writes each of the four tables to a dated,
year-filtered CSV file under the export directory. It is read-only against the
operational data: it SELECTs rows and never modifies them. The only write it
makes is a single `system_events` audit row recording the export outcome -- the
durable record, since the notification system is disabled while the system is
winterized and a notification would be suppressed.

Year-filtered: `<table>_<YYYY>.csv` contains only rows whose UTC timestamp falls
in that calendar year, so the yearly files partition the data cleanly (see
architecture.md Section 13.5).

Weather DB (ADR-018, §3.6 S5): the same trigger also exports the two tables of
the SEPARATE weather database (`watering_weather.db`) -- `weather_snapshots`
(year-filtered on observed_at) and `zone_decisions` (the rows of those
snapshots). That database is opened READ-ONLY (SQLite URI mode=ro): export only,
never delete (long-term retention). It is secondary: a missing or unreadable
weather DB skips those two files and marks the audit row `warning`, but never
fails the operational export. The year defaults to the current UTC year and can
be overridden via the event payload (`event_data.year`) for testing or backfill.
Empty result sets still produce a header-only CSV, so the archive set is always
complete.

Canonical design:
  docs/architecture.md Section 13.5 (Archive Strategy) and Section 13.3.1
  docs/programming-notes.md (ADR-011)

apps.yaml configuration (see the sibling apps.yaml):
  db_path        -- absolute path to the SQLite file
  export_dir     -- directory for the CSV files (created if absent; keep it
                    inside /homeassistant so the files are in HA backups)
  trigger_event  -- HA event name this app listens for
  weather_db_path -- absolute path to watering_weather.db (optional; default
                     /homeassistant/watering_weather.db)
"""

import csv
import os
import sqlite3
from datetime import datetime, timezone

import appdaemon.plugins.hass.hassapi as hass


class DbSeasonalExport(hass.Hass):
    """Export the watering_ops tables to dated, year-filtered CSV files."""

    # table -> the UTC timestamp column used for year filtering. Timestamps are
    # stored as TEXT 'YYYY-MM-DD HH:MM:SS' (UTC), which sorts and range-compares
    # correctly as text, so string bounds give a correct calendar-year filter.
    TABLES = {
        "watering_cycles": "start_time",
        "zone_runs": "start_time",
        "fertigation_doses": "timestamp",
        "system_events": "timestamp",
    }

    def initialize(self):
        self.db_path = self.args.get("db_path", "/homeassistant/watering_ops.db")
        self.export_dir = self.args.get(
            "export_dir", "/homeassistant/watering_exports"
        )
        self.trigger_event = self.args.get(
            "trigger_event", "watering_seasonal_export"
        )
        self.weather_db_path = self.args.get(
            "weather_db_path", "/homeassistant/watering_weather.db"
        )
        self.listen_event(self.run_export, self.trigger_event)
        self.log(
            f"DbSeasonalExport ready; listening for '{self.trigger_event}'",
            level="INFO",
        )

    def run_export(self, event_name, data, kwargs):
        """Export all four tables for one calendar year to CSV."""
        data = data or {}
        raw_year = data.get("year")
        try:
            year = int(raw_year) if raw_year else datetime.now(timezone.utc).year
        except (TypeError, ValueError):
            self.error(
                f"Ignoring seasonal export: invalid 'year' in event payload: "
                f"{raw_year!r}"
            )
            return

        start = f"{year}-01-01 00:00:00"
        end = f"{year + 1}-01-01 00:00:00"

        if not os.path.exists(self.db_path):
            self.error(
                f"Seasonal export aborted: database not found at {self.db_path}"
            )
            return

        try:
            os.makedirs(self.export_dir, exist_ok=True)
        except OSError as exc:
            self.error(
                f"Seasonal export aborted: cannot create {self.export_dir}: {exc}"
            )
            return

        # Weather DB first (its own read-only connection) so its outcome lands
        # in the single audit row below. Never raises.
        weather_counts, weather_problem = self._export_weather(year)

        conn = None
        counts = {}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 5000;")
            for table, ts_col in self.TABLES.items():
                counts[table] = self._export_table(conn, table, ts_col, year, start, end)
            counts.update(weather_counts)
            self._write_audit_row(conn, year, counts, weather_problem)
            conn.commit()
        except (sqlite3.Error, OSError) as exc:
            self.error(f"Seasonal export failed for year {year}: {exc}")
            self._try_record_failure(conn, year, exc)
            return
        finally:
            if conn is not None:
                conn.close()

        summary = ", ".join(f"{t}={n}" for t, n in counts.items())
        self.log(
            f"Seasonal export complete for {year}: {summary} -> {self.export_dir}",
            level="INFO",
        )

    def _export_table(self, conn, table, ts_col, year, start, end):
        """Write one table's rows for the year to <table>_<year>.csv.

        Returns the number of data rows written (header excluded).
        """
        # table / ts_col come from the fixed TABLES map, not user input, so the
        # f-string interpolation here cannot carry untrusted SQL.
        return self._write_csv(
            conn,
            f"SELECT * FROM {table} "
            f"WHERE {ts_col} >= ? AND {ts_col} < ? "
            f"ORDER BY {ts_col}",
            (start, end),
            f"{table}_{year}.csv",
        )

    def _export_weather(self, year):
        """Export weather_snapshots + zone_decisions for the year (read-only).

        Returns (counts, problem): counts maps table -> rows written; problem is
        None on success or a short reason string when the weather export was
        skipped or failed. Never raises -- the operational export must not
        depend on the weather DB.
        """
        if not os.path.exists(self.weather_db_path):
            msg = f"weather DB not found at {self.weather_db_path}; weather tables skipped"
            self.log(f"Seasonal export: {msg}", level="WARNING")
            return {}, msg

        # observed_at is ISO-8601 TEXT ('YYYY-MM-DDTHH:MM:SS...+00:00'); a
        # 'YYYY-01-01' .. 'YYYY+1-01-01' string range selects the calendar year.
        start, end = f"{year}-01-01", f"{year + 1}-01-01"
        conn = None
        try:
            conn = sqlite3.connect(f"file:{self.weather_db_path}?mode=ro", uri=True)
            conn.execute("PRAGMA busy_timeout = 5000;")
            counts = {
                "weather_snapshots": self._write_csv(
                    conn,
                    "SELECT * FROM weather_snapshots "
                    "WHERE observed_at >= ? AND observed_at < ? "
                    "ORDER BY observed_at",
                    (start, end),
                    f"weather_snapshots_{year}.csv",
                ),
                "zone_decisions": self._write_csv(
                    conn,
                    "SELECT d.* FROM zone_decisions d "
                    "JOIN weather_snapshots s ON s.snapshot_id = d.snapshot_id "
                    "WHERE s.observed_at >= ? AND s.observed_at < ? "
                    "ORDER BY d.decision_id",
                    (start, end),
                    f"zone_decisions_{year}.csv",
                ),
            }
            return counts, None
        except (sqlite3.Error, OSError) as exc:
            msg = f"weather export FAILED: {exc}"
            self.error(f"Seasonal export: {msg}")
            return {}, msg
        finally:
            if conn is not None:
                conn.close()

    def _write_csv(self, conn, sql, params, filename):
        """Run a fixed SELECT and write header + rows to export_dir/filename."""
        cur = conn.execute(sql, params)
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        path = os.path.join(self.export_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)
        return len(rows)

    def _write_audit_row(self, conn, year, counts, weather_problem=None):
        """Record the export outcome as a system_events row.

        `info` normally; `warning` when the weather tables were skipped/failed
        (the operational export itself still succeeded).
        """
        summary = ", ".join(f"{t}={n}" for t, n in counts.items())
        notes = f"Exported year {year}: {summary} -> {self.export_dir}"
        if weather_problem:
            notes += f" ({weather_problem})"
        conn.execute(
            "INSERT INTO system_events "
            "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "seasonal_export",
                "warning" if weather_problem else "info",
                notes,
            ),
        )

    def _try_record_failure(self, conn, year, exc):
        """Best-effort: record a `critical` system_events row about the failure."""
        if conn is None:
            return
        try:
            conn.execute(
                "INSERT INTO system_events "
                "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "seasonal_export",
                    "critical",
                    f"Seasonal export FAILED for year {year}: {exc}",
                ),
            )
            conn.commit()
        except sqlite3.Error:
            self.error("Could not record seasonal_export failure to system_events")
