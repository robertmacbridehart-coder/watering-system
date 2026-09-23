-- =============================================================================
-- watering_weather -- Weather Observations Database Schema (SQLite)
-- =============================================================================
-- Canonical design: docs/programming-notes.md (ADR-018) + (ADR-021 inputs);
--                   docs/impl_roadmap.md Section 3.6; docs/architecture.md §13.
--
-- This file is the version-controlled SOURCE OF TRUTH for the physical schema of
-- the SEPARATE weather-observations database (watering_weather.db), distinct from
-- the operational database (watering_ops.db, docs/db_schema.sql). Two databases,
-- not one table: different lifecycle (a continuous twice-daily time series vs
-- event-driven cycles) and different retention (LONG-TERM, NEVER pruned -- the
-- ops DB keeps only a 14-day rolling window). Correlate the two by observed_at /
-- window_name (ATTACH for cross-DB joins).
--
-- Applied idempotently by the AppDaemon bootstrap (weather DB clone of
-- db_schema_init.py) on start-up; every statement is CREATE ... IF NOT EXISTS,
-- safe to run repeatedly. No manual SQL execution step on HAOS.
--
-- Engine notes (SQLite) -- identical conventions to db_schema.sql:
--   * Foreign keys are OFF by default, per-connection. Every connection MUST
--     issue `PRAGMA foreign_keys = ON;`. The PRAGMA here affects only the single
--     connection that runs this script.
--   * Timestamps are TEXT 'YYYY-MM-DD HH:MM:SS' in UTC. Store UTC; convert to
--     local (Europe/Berlin) only for display -- keeps date-window queries correct
--     across the CET/CEST changeover, sorts/compares as text, and works with
--     SQLite date functions.
--   * SQLite has no native BOOLEAN/DECIMAL/DATETIME:
--       BOOLEAN  -> INTEGER (0/1, CHECK-constrained)
--       DECIMAL  -> REAL
--       DATETIME -> TEXT ('YYYY-MM-DD HH:MM:SS', UTC)
--       VARCHAR  -> TEXT
--   * Controlled vocabularies enforced with CHECK constraints.
--   * WIDE, not tall/EAV (ADR-018 rationale): typed columns for the decision-
--     relevant metrics + a `raw` JSON catch-all so a new sensor is never lost
--     before it earns a typed column (the local-station integration is the
--     natural migration point). A future homogeneous soil-moisture ARRAY is where
--     a tall table would earn its place -- it can be its own table then.
--   * The column named `window` in ADR-018 shorthand is `window_name` here:
--     WINDOW is a reserved keyword in SQLite (window functions), so a bare
--     `window` column needs quoting in every query. window_name avoids that.
--
-- DEFERRED (ADR-018 amendment 2026-08-26, resolve at build-out, NOT here): a
-- once-daily calendar-day capture (rain_total_mm / temp_high_c for the completed
-- prior day) for the dashboard Weather-card 7-day history. The twice-daily
-- snapshots below sample the ROLLING rain_24h, which is not a clean per-day
-- total. Add a daily-granularity mechanism (or a REST/history sensor) then;
-- it depends only on BrightSky, so it can be pulled forward independently.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- weather_snapshots -- one row per window (morning/evening), written by the
-- ALWAYS-ON snapshot automation regardless of system state (parked in
-- manual_override, winterized, mid-cycle, or idle). Capturing the skip/parked
-- days -- the days we correctly did NOT water -- is the whole point (ADR-018).
-- The soil-moisture/rain sensors are independent of the ESP32/relays, so this
-- records normally while the unit is parked pre-go-live.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_snapshots (
    snapshot_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at          TEXT    NOT NULL,               -- UTC, at window fire
    window_name          TEXT    NOT NULL
                           CHECK (window_name IN ('morning', 'evening')),
    source               TEXT    NOT NULL DEFAULT 'brightsky'
                           CHECK (source IN ('brightsky', 'local_station', 'mixed')),
    weather_available    INTEGER NOT NULL DEFAULT 1      -- D-A: were the weather inputs readable
                           CHECK (weather_available IN (0, 1)),

    -- temperature (raw + all candidate "highs" -- defer which is THE high; the
    -- ops DB historically stored the wrong metric, ADR-018 root cause)
    temp_c               REAL,                           -- current, brightsky_temperature
    temp_high_forecast_c REAL,                           -- brightsky_forecast_temp_high (the de-lagged high ADR-021 uses)
    temp_high_yesterday_c REAL,                          -- brightsky_temp_high_yesterday
    temp_avg_high_3day_c REAL,                           -- brightsky_temp_avg_high_3day (the LAGGING metric, ADR-004)

    -- rain (the SELECTED values the decision saw, via the WH40/DWD abstraction)
    rain_24h_mm          REAL,                           -- sensor.rain_24h
    rain_72h_mm          REAL,                           -- sensor.rain_72h
    raining_now          INTEGER                         -- binary_sensor.rain_active
                           CHECK (raining_now IS NULL OR raining_now IN (0, 1)),
    rain_source          TEXT                            -- which source fed rain_24h
                           CHECK (rain_source IS NULL OR
                                  rain_source IN ('wh40', 'dwd', 'none')),

    -- forecast (dedicated hourly-BrightSky aggregates the ADR-021 downgrade uses)
    forecast_pop_today       REAL,                       -- % max hourly POP, now -> midnight
    forecast_rain_today_mm   REAL,                       -- sum hourly precip, now -> midnight

    -- other atmospherics (cheap; decision-adjacent context)
    humidity_pct         REAL,
    pressure_hpa         REAL,
    cloud_cover_pct      REAL,
    wind_speed_ms        REAL,

    -- catch-all: full raw payload as JSON (per-channel soil moisture/temp/EC/
    -- battery, sensor liveness, any not-yet-typed metric). Never lose a reading.
    raw                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_snapshots_observed ON weather_snapshots (observed_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_window   ON weather_snapshots (window_name, observed_at);

-- -----------------------------------------------------------------------------
-- zone_decisions -- N=4 per snapshot (one per zone). The SHADOW decision the
-- single shared routine (script.compute_zone_programs) computes for this window,
-- recorded whether or not we water. Same routine feeds zone_runs.decision_criteria
-- on real runs (ops DB); this table is the always-on record.
--
-- computed_program is the FINAL program after the cadence/booster gates (so it
-- can be 'booster' or 'off'), not just the weather/moisture base intensity; the
-- intermediate base + the reason live in decision_criteria.
--
-- decision_criteria is a JSON audit blob (change-tolerant across the moisture
-- rework -- new keys carry through with no migration). Expected keys:
--   base_program            -- moisture/weather base intensity before cadence
--   branch / skip_reason    -- which rule fired
--   moisture_pct, moisture_sensor_count  -- also first-class columns below
--   thresholds              -- {off_moisture_min, light_moisture_min,
--                              normal_moisture_min, rain_off/light/min,
--                              temp_heavy/normal} LIVE at decision time
--   rain_24h, rain_72h, raining_now, rain_source
--   temp_high_used          -- the de-lagged forecast/current high (not the 3day avg)
--   forecast_pop_today, forecast_rain_today
--   weather_modifier        -- +/- step applied (recent rain / hot / cool)
--   forecast_downgrade      -- steps dropped by the capped/floored forecast rule
--   hysteresis              -- band state, if it changed the outcome
--   cadence                 -- {enabled, interval_days, days_since, due,
--                              booster_pending, booster_slot}
--   weather_only_fallback   -- 1 when no fresh sensor -> weather-only path
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zone_decisions (
    decision_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id          INTEGER NOT NULL,
    zone_id              INTEGER NOT NULL CHECK (zone_id BETWEEN 1 AND 4),
    season               TEXT    NOT NULL
                           CHECK (season IN ('spring', 'summer', 'fall', 'winter')),
    computed_program     TEXT    NOT NULL
                           CHECK (computed_program IN
                                  ('off', 'light', 'normal', 'heavy', 'booster')),
    program_multiplier   REAL,                           -- e.g. 1.0, 1.5, 0.5
    would_water          INTEGER NOT NULL                -- convenience: program != 'off'
                           CHECK (would_water IN (0, 1)),
    moisture_pct         REAL,                           -- zone aggregate; NULL -> weather-only fallback
    moisture_sensor_count INTEGER NOT NULL DEFAULT 0     -- fresh contributing sensors (0 = fallback)
                           CHECK (moisture_sensor_count >= 0),
    decision_criteria    TEXT    NOT NULL,               -- JSON (see keys above)
    FOREIGN KEY (snapshot_id) REFERENCES weather_snapshots (snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_decisions_snapshot ON zone_decisions (snapshot_id);
CREATE INDEX IF NOT EXISTS idx_decisions_zone     ON zone_decisions (zone_id, decision_id);

-- =============================================================================
-- Change log
-- 2026-08-30  Initial schema (SQLite dialect) per ADR-018 (Weather Observations
--             DB) + ADR-021 moisture-primary inputs. Two tables (weather_snapshots
--             1 -> zone_decisions N=4), wide + `raw` JSON catch-all, long-term
--             retention (no pruning). Mirrors db_schema.sql conventions. Applied
--             by the weather DB bootstrap (db_schema_init.py clone, next step).
--             Daily-granularity capture (ADR-018 2026-08-26 amendment) DEFERRED.
-- =============================================================================
