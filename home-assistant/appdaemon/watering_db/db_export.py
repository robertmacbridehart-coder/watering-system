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
architecture.md Section 13.5). The year defaults to the current UTC year and can
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

        conn = None
        counts = {}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 5000;")
            for table, ts_col in self.TABLES.items():
                counts[table] = self._export_table(conn, table, ts_col, year, start, end)
            self._write_audit_row(conn, year, counts)
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
        cur = conn.execute(
            f"SELECT * FROM {table} "
            f"WHERE {ts_col} >= ? AND {ts_col} < ? "
            f"ORDER BY {ts_col}",
            (start, end),
        )
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        path = os.path.join(self.export_dir, f"{table}_{year}.csv")
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)
        return len(rows)

    def _write_audit_row(self, conn, year, counts):
        """Record the export outcome as an `info` system_events row."""
        summary = ", ".join(f"{t}={n}" for t, n in counts.items())
        conn.execute(
            "INSERT INTO system_events "
            "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "seasonal_export",
                "info",
                f"Exported year {year}: {summary} -> {self.export_dir}",
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
