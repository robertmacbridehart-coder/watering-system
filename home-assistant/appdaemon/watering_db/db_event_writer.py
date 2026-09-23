"""db_event_writer.py -- AppDaemon app: persist system events to watering_ops.

Listens for the HA bus event `watering_system_event` (fired by the HA logging
helper `script.log_system_event`) and INSERTs one row into the `system_events`
table. This is the persistent, queryable record that replaces the transient
`input_text.cycle_event_log` for safety / error / info events.

This app implements Event 5 of the event-payload contract
(docs/architecture.md Section 13.3.1). `system_events` rows are NOT tied to a
cycle and need no correlation, so they are written immediately on receipt --
unlike the cycle / zone-run / dose events, which depend on the Phase 4 state
machine minting cycle_uuid / zrun_uuid.

The operational DB is fire-and-forget reporting and is not on the watering /
safety path (architecture.md Section 13.1): this handler never raises. A bad
payload is logged, recorded as a rejection row, and skipped; a DB error is
logged and swallowed. Nothing here can stall irrigation.

apps.yaml configuration (see the sibling apps.yaml):
  db_path        -- absolute path to the SQLite file
  trigger_event  -- HA event name this app listens for
                    (default `watering_system_event`)
"""

import sqlite3
from datetime import datetime, timezone

import appdaemon.plugins.hass.hassapi as hass


class DbEventWriter(hass.Hass):
    """Persist `watering_system_event` payloads into system_events."""

    VALID_SEVERITY = ("info", "warning", "error", "critical")

    # Optional string columns carried in the payload, populated when present.
    OPTIONAL_FIELDS = ("entity_id", "value_before", "value_after", "notes")

    def initialize(self):
        self.db_path = self.args.get("db_path", "/homeassistant/watering_ops.db")
        self.trigger_event = self.args.get(
            "trigger_event", "watering_system_event"
        )
        self.listen_event(self.on_event, self.trigger_event)
        self.log(
            f"DbEventWriter ready; listening for '{self.trigger_event}'",
            level="INFO",
        )

    def on_event(self, event_name, data, kwargs):
        """Validate one event payload and INSERT it into system_events."""
        data = data or {}

        timestamp = self._clean(data.get("timestamp"))
        event_type = self._clean(data.get("event_type"))
        severity = self._clean(data.get("severity"))

        # Required-field / vocabulary validation (Section 13.3.1). On any
        # violation: log, record a rejection row, and skip -- never raise.
        problems = []
        if not timestamp:
            problems.append("missing 'timestamp'")
        if not event_type:
            problems.append("missing 'event_type'")
        if not severity:
            problems.append("missing 'severity'")
        elif severity not in self.VALID_SEVERITY:
            problems.append(
                f"invalid 'severity' {severity!r} "
                f"(expected one of {self.VALID_SEVERITY})"
            )
        if problems:
            self.error(
                f"Rejected {self.trigger_event}: {'; '.join(problems)}; "
                f"payload={data!r}"
            )
            self._record_rejection(data, problems)
            return

        row = {
            "timestamp": timestamp,
            "event_type": event_type,
            "severity": severity,
        }
        for field in self.OPTIONAL_FIELDS:
            row[field] = self._clean(data.get(field))

        if self._insert(row):
            detail = f" ({row['entity_id']})" if row["entity_id"] else ""
            self.log(
                f"system_events <- {severity}/{event_type} @ {timestamp}{detail}",
                level="DEBUG",
            )

    def _insert(self, row):
        """INSERT one validated row. Returns True on success, False on DB error.

        system_events has no foreign keys, so PRAGMA foreign_keys is not needed
        here; busy_timeout guards against a transient lock (WAL is already set on
        the file by db_schema_init).
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute(
                "INSERT INTO system_events "
                "(timestamp, event_type, severity, entity_id, "
                " value_before, value_after, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row["timestamp"],
                    row["event_type"],
                    row["severity"],
                    row["entity_id"],
                    row["value_before"],
                    row["value_after"],
                    row["notes"],
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            self.error(f"system_events INSERT failed: {exc}; row={row!r}")
            return False
        finally:
            if conn is not None:
                conn.close()

    def _record_rejection(self, data, problems):
        """Best-effort: record a `warning` audit row about a rejected payload.

        Uses a server-side UTC timestamp because the payload's own timestamp may
        be the field that was missing or malformed.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute(
                "INSERT INTO system_events "
                "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "event_rejected",
                    "warning",
                    f"Rejected {self.trigger_event}: {'; '.join(problems)}; "
                    f"payload={data!r}",
                ),
            )
            conn.commit()
        except sqlite3.Error:
            self.error("Could not record event_rejected row to system_events")
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def _clean(value):
        """Normalise a payload value to a stripped str, or None for empties.

        HA template output for an absent field commonly arrives as '',
        'unknown', or 'unavailable'; treat those as SQL NULL so optional columns
        stay clean.
        """
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() in ("unknown", "unavailable"):
            return None
        return text
