-- =============================================================================
-- watering_ops -- Operational Database Schema (SQLite)
-- =============================================================================
-- Canonical design: docs/architecture.md Section 13 and
--                   docs/programming-notes.md (ADR-011)
--
-- This file is the version-controlled SOURCE OF TRUTH for the physical schema.
-- It is applied idempotently by the AppDaemon bootstrap app (db_schema_init.py)
-- on start-up; every statement is safe to run repeatedly (CREATE ... IF NOT
-- EXISTS). There is no manual SQL execution step on HAOS.
--
-- Engine notes (SQLite):
--   * Foreign keys are OFF by default, per-connection. The application MUST
--     issue `PRAGMA foreign_keys = ON;` on EVERY connection for the FK
--     constraints below to be enforced. The PRAGMA in this file only affects
--     the single connection that runs this script.
--   * Timestamps are stored as TEXT in SQLite datetime format
--     'YYYY-MM-DD HH:MM:SS', in UTC. Store UTC; convert to local
--     (Europe/Berlin) only for display. This keeps the 14-day rolling-window
--     queries correct across the CET/CEST changeover. This format compares and
--     sorts correctly as text and works directly with SQLite date functions,
--     e.g. datetime('now', '-14 days').
--   * SQLite has no native BOOLEAN/DECIMAL/DATETIME types:
--       BOOLEAN  -> INTEGER (0/1, CHECK-constrained)
--       DECIMAL  -> REAL
--       DATETIME -> TEXT ('YYYY-MM-DD HH:MM:SS', UTC)
--       VARCHAR  -> TEXT
--   * Controlled vocabularies (trigger_type, outcome, weather_program,
--     severity, phase) are enforced with CHECK constraints.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- watering_cycles -- one row per cycle. Two-phase write:
--   INSERT at preflight    (start_time, trigger_type, weather snapshot)
--   UPDATE at completion   (end_time, outcome, notes)
-- end_time / outcome / notes are therefore NULL between the two writes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watering_cycles (
    cycle_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time       TEXT    NOT NULL,                 -- UTC; written at preflight
    trigger_type     TEXT    NOT NULL
                       CHECK (trigger_type IN ('scheduled', 'manual', 'override')),
    rainfall_24h_mm  REAL,                             -- weather snapshot at preflight
    rainfall_72h_mm  REAL,                             -- weather snapshot at preflight
    temp_high_c      REAL,                             -- weather snapshot at preflight
    end_time         TEXT,                             -- UTC; written at completion
    outcome          TEXT
                       CHECK (outcome IS NULL OR
                              outcome IN ('completed', 'aborted', 'error')),
    notes            TEXT                              -- written at completion
);

CREATE INDEX IF NOT EXISTS idx_cycles_start_time ON watering_cycles (start_time);
CREATE INDEX IF NOT EXISTS idx_cycles_outcome    ON watering_cycles (outcome);

-- -----------------------------------------------------------------------------
-- zone_runs -- one row per zone per cycle. Written at zone-run conclusion.
-- weather_program lives here (per-zone evaluation), not on the cycle.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zone_runs (
    zrun_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id              INTEGER NOT NULL,
    zone_id               INTEGER NOT NULL CHECK (zone_id BETWEEN 1 AND 4),
    weather_program       TEXT    NOT NULL
                            CHECK (weather_program IN
                                   ('off', 'light', 'normal', 'heavy')),
    start_time            TEXT    NOT NULL,            -- UTC, valve open
    end_time              TEXT,                        -- UTC, valve close
    planned_duration_sec  INTEGER,                     -- from script.calculate_zone_runtime
    actual_duration_sec   INTEGER,                     -- computed by AppDaemon on write
    program_multiplier    REAL,                        -- e.g. 1.0, 1.5, 0.5
    fertigated            INTEGER NOT NULL DEFAULT 0
                            CHECK (fertigated IN (0, 1)),
    aborted               INTEGER NOT NULL DEFAULT 0
                            CHECK (aborted IN (0, 1)),
    abort_reason          TEXT,                        -- populated when aborted = 1
    FOREIGN KEY (cycle_id) REFERENCES watering_cycles (cycle_id)
);

CREATE INDEX IF NOT EXISTS idx_zone_runs_cycle      ON zone_runs (cycle_id);
CREATE INDEX IF NOT EXISTS idx_zone_runs_zone_start ON zone_runs (zone_id, start_time);

-- -----------------------------------------------------------------------------
-- fertigation_doses -- one row per dose event. Written at dosing conclusion.
-- zone_id is denormalised (copied from the parent zone_run) so the 14-day
-- rolling-window decision query never needs a join.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fertigation_doses (
    dose_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    zrun_id          INTEGER NOT NULL,
    zone_id          INTEGER NOT NULL CHECK (zone_id BETWEEN 1 AND 4),
    timestamp        TEXT    NOT NULL,                 -- UTC, dose delivered
    nutrient_product TEXT,                             -- product name / identifier
    target_dose_ml   REAL,                             -- planned dose
    actual_dose_ml   REAL,                             -- delivered dose
    pump_id          INTEGER                           -- logical pump number 1-3 (maps to Modbus addr 0x02-0x04)
                       CHECK (pump_id IS NULL OR pump_id BETWEEN 1 AND 3),
    phase            INTEGER
                       CHECK (phase IS NULL OR phase IN (1, 2)),
    FOREIGN KEY (zrun_id) REFERENCES zone_runs (zrun_id)
);

-- Primary index for the 14-day "fert delivered per zone" decision query.
CREATE INDEX IF NOT EXISTS idx_doses_zone_ts ON fertigation_doses (zone_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_doses_zrun    ON fertigation_doses (zrun_id);

-- -----------------------------------------------------------------------------
-- system_events -- append-only. Written immediately after a safety/error event.
-- Not linked to a cycle (events can fire outside a cycle).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,                        -- UTC
    event_type   TEXT NOT NULL,                        -- e.g. 'safety_interlock', 'manual_override'
    severity     TEXT NOT NULL
                   CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    entity_id    TEXT,                                 -- HA entity involved, if applicable
    value_before TEXT,
    value_after  TEXT,
    notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_ts       ON system_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type     ON system_events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON system_events (severity);

-- =============================================================================
-- Change log
-- 2026-06-28  Initial schema (SQLite dialect) created per ADR-011 (SQLite
--             revision). Four tables, FK + CHECK constraints, indexes for the
--             14-day rolling-window and FK lookups. Supersedes the never-built
--             MariaDB formulation.
-- 2026-07-31  system_events.severity CHECK extended to add 'error' (now:
--             info / warning / error / critical), matching HA's log levels
--             (minus debug) so a persisted severity maps 1:1 to the system_log
--             level with no lossy remap. NOTE: existing databases need a
--             one-time table rebuild -- SQLite cannot ALTER a CHECK, and the
--             bootstrap's CREATE TABLE IF NOT EXISTS skips the change on an
--             already-created DB. See architecture.md 13.2/13.3.1 and the
--             ADR-011 addendum in programming-notes.md.
-- =============================================================================
