# Watering System - Implementation Roadmap

**Last Updated:** 2026-08-18  
**Status:** Phase 5 — Safety Interlocks ✅ COMPLETE (built, code-reviewed, deployed, Dev-Tools
tested PASS 2026-08-16). Phases 1-6 / 9 / 10 built and deployed **except the fert path** (3.3
fert scripts, Event 2 dose-writer, decision-query sensors) — all blocked on RS-485 dosing
hardware. Phase 9.10 (end-of-cycle summary notification) is **COMPLETE — built + verified
2026-08-18** (§9.10). **Phase 7 (Dashboard UI) is now the active build phase** — front-end design
process defined 2026-08-18 (§7.0–7.6 gates, ADR-019); **Gate 7.0 complete 2026-08-20**,
**Gate 7.1 LOCKED 2026-08-21** (all visual tokens fixed, `docs/ui_design.md` v0.3.0 §6).

---

## Purpose

This document tracks what's been built, what's next, and what's blocked. It's the source of truth for "where are we in the implementation?"

---

## Legend

- ✅ **Complete** - Tested and working
- 🚧 **In Progress** - Currently being built
- ⏳ **Blocked** - Waiting on hardware/decision/prerequisite
- 📋 **Planned** - Designed but not started
- ❌ **Deferred** - Explicitly postponed to later phase

---

## Phase 1: Foundation (Hardware + Basic Control)

### 1.1 ESP32 Hardware Setup
- [X] ✅ ESP32-DEVKITC-32UE installed and powered (u.FL external-antenna variant + external Linx ANT-W63WS3-SMA antenna; swapped from DEVKITC-VE 2026-08-18)
- [X] ✅ UART2 (TX=GPIO25, RX=GPIO26) wired to RS-485 adapter
- [ ] ✅ GPIO34/35 wired to float switches (Low/Low-Low)
- [X] ✅ RS-485 termination resistors installed (120Ω both ends)
- [X] ✅ Common ground (0V/COM) connected along A/B lines

**Blocker Notes:** _None_

---

### 1.2 ESPHome Configuration
- [X] ✅ `esphome/watering-esp32.yaml` created (base config)
- [X] ✅ `esphome/packages/modbus_rs485.yaml` - Relay board (addr 0x01)
- [X] ✅ `esphome/packages/inputs.yaml` - Float switches (GPIO34/35)
- [X] ✅ `esphome/packages/victron_ble.yaml` - SmartSolar BLE sensors
- [ ] 📋 All 16 relays defined with correct mappings:
  - R1: Main pump → `switch.watering_system_relay_1_main_pump`
  - R2: Zone 1 valve → `switch.watering_system_relay_2_zone_1`
  - R3: Zone 2 valve → `switch.watering_system_relay_3_zone_2`
  - R4: Zone 3 valve → `switch.watering_system_relay_4_zone_3`
  - R5: Zone 4 valve → `switch.watering_system_relay_5_zone_4`
  - R6: Bypass valve → `switch.watering_system_relay_6_fert_bypass`
  - R7: Fertilizer line valve → `switch.watering_system_relay_7_fert_line`
  - R8: Reserved → `switch.watering_system_relay_8`
  - R9: Pressure relief valve → `switch.watering_system_relay_9_pressure_relief`
  - R10: 24V cabinet enable → `switch.watering_system_relay_10_24v_cabinet`
  - R11-R16: Reserved → `switch.watering_system_relay_11` through `relay_16`
- [ ] 📋 Flash to ESP32 and verify HA integration
- [ ] 📋 Verify entity IDs in HA match expected pattern (see `/docs/entity_reference.md`)

**Blocker Notes:** _Check if relay mappings R1-R10 match physical wiring. Verify GPIO pins are GPIO33=Low, GPIO32=Low-Low (not GPIO34/35)._

---

### 1.3 RS-485 Dosing Pumps (Future - Phase 2)
- [ ] ⏳ Change pump addresses to 0x02, 0x03, 0x04
- [ ] ⏳ Add Modbus controller entries for each pump
- [ ] ⏳ Test basic start/stop commands
- [ ] ⏳ Calibrate flow rates at operating pressure (1.1 bar, per PRV setting)
  - Procedure: `/docs/fert_pump_cal_v2.md` (content v2.1, updated 2025-11-09)
  - Operational range: 5-100 RPM (conservative limit for tube longevity)
  - Expected flow: 2-15 mL/min across calibration range
  - Pre-calibration: Tubing break-in (2-3 hours @ 30 RPM, then 30 min rest)

**Blocker Notes:** _Pumps not yet wired to RS-485 bus. Calibration procedure ready._

---

### 1.4 Soil Moisture Sensors (Future - Phase 3)
- [ ] ❌ Change sensor addresses to 0x05, 0x06, 0x07
- [ ] ❌ Add Modbus controller entries
- [ ] ❌ Test moisture/temperature readings
- [ ] ❌ Add sensor reading scheduler

**Blocker Notes:** _Deferred until basic watering works_

---

## Phase 2: Home Assistant - Configuration Helpers

### 2.1 System-Level Helpers
- [x] ✅ Created watering_config_helpers.yaml (12 helpers)
- [x] ✅ State machine control (input_select.watering_system_state - 15 states;
  grew 11 -> 15 during Phase 3, see ADR-002 addendum)
- [x] ✅ Scheduling parameters (cycle days, watering windows)
- [x] ✅ Safety limits (max runtime, pressure relief)
- [x] ✅ Manual override control
- [x] ✅ Validation test passed (12/12 entities correct)

**Completion Date:** 2025-10-15
**Status:** ✅ Complete - Ready for Phase 2.2
**Note:** input_datetime entities require manual time configuration in UI

**File Location:** `home-assistant/packages/watering_helpers/config_helpers.yaml`

**Blocker Notes:** _None_

---

### 2.2 Per-Zone Configuration Helpers
- [X] ✅ Zone friendly name helpers (input_text, 4 total)
- [X] ✅ Season selectors (input_select, 4 total)
- [X] ✅ Program override selectors (input_select, 4 total)
- [X] ✅ Base runtime helpers (input_number, 4 total)
- [X] ✅ Seasonal threshold helpers (input_number, 80 total: 20 per zone × 4 zones)
- [X] ✅ watering_zone_helpers.yaml created and validated (96 entities)
- [X] ✅ Validation test passed (100% - all entities correct)

**Status:** ✅ Complete (2025-10-15)
**Validation:** 96/96 entities passed all checks

**File Location:** `home-assistant/packages/watering_helpers/zone_helpers.yaml`

**Blocker Notes:** _None_

---

### 2.3 Fertigation Helpers

- [x] ✅ Section 2.3.1: Fertigation schedule (cycle days, last-fert tracking)
- [x] ✅ Section 2.3.2: Per-zone dosing configuration (12 dose amounts + flush duration)
- [x] ✅ Section 2.3.3: Pump calibration storage (18 helpers for 3 pumps)
- [x] ✅ Section 2.3.4: Template sensors (27 calculated flow rates, commands, status)
- [x] ✅ Section 2.3.5: Validation (all 63 entities verified via test)

**Status:** ✅ Complete 2025-10-15
**Validation:** PASS - 63/63 entities validated successfully
**File Location:** `home-assistant/packages/watering_helpers/fert_helpers.yaml`

**Blocker Notes:** _RS-485 pumps not yet wired (Phase 1.3) - calibration pending. Calibration procedure updated to v2.1 (2025-11-09): corrected volume-per-revolution (0.15 mL/rev), established 100 RPM operational maximum, documented typical coefficients (0.13-0.17 mL/min per RPM)._

---

## Phase 3: Home Assistant - Core Scripts

### 3.1 Zone Control Scripts ✅ COMPLETE (2025-10-22)
- [X] ✅ `script.open_zone` (param: zone_id)
- [X] ✅ `script.close_zone` (param: zone_id)
- [X] ✅ `script.close_all_zones`
- [X] ✅ `script.calculate_zone_runtime` (returns runtime based on program)
- [X] ✅ `script.run_zone_sequence` (handles parallel vs sequential)

**File Location:** `home-assistant/packages/watering_scripts/zone_scripts.yaml`

**Scripts Implemented:**
1. `script.open_zone` - Safely opens zone valve with pump/valve checks
2. `script.close_zone` - Closes single zone valve
3. `script.close_all_zones` - Emergency cleanup, closes all zones
4. `script.calculate_zone_runtime` - Pure function, returns runtime based on program
5. `script.run_zone_sequence` - Executes watering with parallel/sequential modes

**Safety Features:**
- Pump state verification before opening zones
- Valve interlock XOR logic (R6 XOR R7)
- Type casting for zone_id (handles string/int)
- Parameter validation with error logging
- Unavailable entity detection
- Defense-in-depth approach

**Testing Status:**
- All unit tests passed
- Pump error handling verified
- Valve interlock checks verified
- Both sequencing modes verified
- Heavy program logic verified (dual/single window modes)

**Blocker Notes:** _None_

---

### 3.2 Pump Control Scripts ✅ COMPLETE (2025-11-07)
- [X] ✅ `script.start_main_pump` (with pressure stabilization delay)
- [X] ✅ `script.stop_main_pump` (with self-repair retry)
- [X] ✅ `script.open_pressure_relief` (with validation and configurable duration)
- [X] ✅ `script.close_pressure_relief`

**File Location:** `home-assistant/packages/watering_scripts/pump_scripts.yaml`

**Scripts Implemented:**
1. `script.start_main_pump` - Comprehensive safety checks with self-repair for relief valve
2. `script.stop_main_pump` - Safe shutdown with aggressive 120-minute retry loop
3. `script.open_pressure_relief` - Validated duration (30-300s) with 120s default
4. `script.close_pressure_relief` - Immediate valve close

**Safety Features:**
- Tank level verification before pump start (low-low check)
- Pressure relief valve self-repair (if open during pump start)
- Pump stop self-repair with aggressive retry (120-minute loop, 2s intervals)
- Valve interlock verification (R6 XOR R7 - exactly one flow path)
- 3-second relay verifications after all relay commands
- 30-second pressure stabilization after pump start
- Dual logging (system_log + cycle_event_log)
- Pressure relief duration validation with safe bounds and default
- Script mode: `restart` on stop_main_pump (allows safety automation override)

**Self-Repair Logic:**
- **Pressure relief valve:** If found open during pump start, attempt close, re-verify, log outcome
- **Pump stop retry:** Aggressive 120-minute retry loop with 2-second intervals
  - Logs every 10th attempt (every 20 seconds) to prevent log spam
  - Continues until pump stops OR ESPHome hardware timer triggers (120min auto-off)
  - Uses `mode: restart` to ensure latest stop request takes priority
- **Single retry vs. aggressive:** Relief valve gets one retry; pump gets unlimited (hardware backstop)
- All self-repairs log to both system_log AND cycle_event_log

**Key Implementation Details:**
- Separator syntax matches zone_scripts.yaml pattern: `"{{ '\n' if current_log else '' }}"`
- Logging order: system_log first (always works), cycle_event_log second (may fail)
- Pressure relief validation enforces 30-300s bounds, uses 120s default if helper unavailable
- Script mode: `single` on all scripts EXCEPT stop_main_pump (uses `restart`)
- 500ms delay after calling subscripts before relay verification (prevents race condition)

**Testing Status:** ✅ 13/19 tests passed (68%), 6 skipped due to UI timing limitations
- Suite 1 (start_main_pump): 5/7 PASS (Tests 1.4, 1.7 skipped)
- Suite 2 (stop_main_pump): 1/3 PASS (Tests 2.2, 2.3 skipped)
- Suite 3 (open_pressure_relief): 2/4 PASS (Tests 3.3, 3.4 skipped)
- Suite 4 (close_pressure_relief): 1/2 PASS (Test 4.2 skipped)
- Suite 5 (Integration): 3/3 PASS (all passed)

**All critical safety paths validated:**
- ✅ Tank level checks (abort on low-low)
- ✅ Valve interlock enforcement (R6 XOR R7)
- ✅ Pressure relief self-repair logic
- ✅ Pump relay verification
- ✅ Pump/relief sequencing
- ✅ Duration validation and bounds checking

**Skipped Tests:** 6 tests require sub-second manual relay intervention (untestable via HA UI)
- All skipped tests validated via code review and logic analysis
- Self-repair success paths tested (Tests 1.3, 3.2) confirm repair logic works
- Future: Consider test automation helper for relay failure simulation

**Code Fixes During Implementation:**
1. Issue #8: Pressure relief duration validation (defense-in-depth)
2. Issue #9: Changed stop_main_pump to `mode: restart` (prevents safety automation blocking)
3. Issues #15-17: State verification pattern (use `not is_state()` to catch unavailable)
4. YAML syntax: Fixed empty `then:` block in pressure relief self-repair
5. Race condition: Added 500ms delay after calling subscripts before verification

**Blocker Notes:** _None_

---

### 3.3 Fertilizer Control Scripts

Split into two subsections for operational scripts (automated, high-frequency) and calibration scripts (manual, infrequent).

---

#### 3.3.1 Operational Fertigation Scripts
- [ ] 📋 `script.check_zone_fert_eligibility` (param: zone_id)
- [ ] 📋 `script.calculate_zone_fert_dose` (param: zone_id)
- [ ] 📋 `script.get_calibration_status` (param: pump_id)
- [ ] 📋 `script.start_fert_pump` (param: pump_id, rpm_command)
- [ ] 📋 `script.stop_fert_pump` (param: pump_id)
- [ ] 📋 `script.run_fert_dose_phase` (param: phase)

**File Location:** `home-assistant/packages/watering_scripts/fert_scripts.yaml`

**Scripts Implemented:**
1. `script.check_zone_fert_eligibility` - Evaluates V2 multi-condition logic (tank, winterization, rolling window, 48h interval, soil moisture/rain)
2. `script.calculate_zone_fert_dose` - Gets seasonal pump selection and dose, calculates RPM from calibration, returns pump_id + rpm + duration
3. `script.get_calibration_status` - Checks calibration age and R² quality, returns VALID/WARNING/POOR/EXPIRED
4. `script.start_fert_pump` - Validates calibration, checks R7 + main pump, sends Modbus start at RPM
5. `script.stop_fert_pump` - Sends Modbus stop command
6. `script.run_fert_dose_phase` - Sequential zone processing: open zone → start assigned pump → dose (75% runtime) → stop pump → flush (2 min) → close zone

**Pump Configuration:**
- 3 pumps (0x02, 0x03, 0x04), each with different fertilizer mix
- Only ONE pump runs at a time
- Pump selection per zone per season via `input_number.zone_X_{season}_pump` (1, 2, or 3)
- Dose amount per zone per season via `input_number.zone_X_{season}_dose_ml`
- Each pump has independent calibration data

**Key Features:**
- V2 rolling window logic with multi-condition evaluation
- Seasonal pump selection (acidic blend for blueberries in spring, bloom booster in summer, etc.)
- 75% runtime per phase - allows proper distribution
- 2-minute flush after each phase clears lines
- Heavy program dose multiplier = 1.0 (extra 0.5× water is plain watering in evening)
- Safety: Checks R7 open + main pump on before starting
- RPM clamped to 5-100 operational range
- Sequential zone processing with 30-second inter-zone delays

**Dose Calculation:**
- Get seasonal pump: `pump_id = input_number.zone_X_{season}_pump`
- Get seasonal dose: `base_dose = input_number.zone_X_{season}_dose_ml`
- Apply program multiplier: `total_dose = base_dose × multiplier`
  - Off: 0×, Light: 0.5× or 1.0× (based on boolean), Normal: 1.0×, Heavy: 1.0×
- Get zone runtime, calculate phase duration (75% of total)
- Convert to RPM using pump's calibration: `rpm = (dose/duration - intercept) / slope`

**Fertigation Window:**
- Both windows enabled: Fertigate in morning, plain water in evening
- Morning only: Fertigate in morning
- Evening only: Fertigate in evening

**Dependencies:**
- Phase 3.1 ✅ (zone scripts - calculate_zone_runtime reused)
- Phase 3.2 ✅ (pump scripts - main pump control)
- Phase 2.3 V2 helpers:
  - 68 zone helpers (soil moisture thresholds, 14-day targets, light dose booleans)
  - 9 system tracking helpers (current_zone, binary sensors, history_stats)
  - 32 pump/dose helpers: `zone_{1-4}_{season}_pump` and `zone_{1-4}_{season}_dose_ml`
  - 27 calibration helpers (9 per pump: slope, intercept, R², pressure, last_cal, notes)
- Pump Modbus documentation (register maps, baud, addressing)

**Test Plan:**
- Unit: Each script with mocked Modbus/helpers
- Integration: Full cycle (phase1 → watering → phase2)
- Pump selection: Zone 1 uses Pump 1, Zone 2 uses Pump 3, etc.
- Safety: R7 closed/pump off blocking
- Calibration: EXPIRED/POOR blocks operation
- Multi-zone: Sequential with correct pump per zone
- Edge cases: dose=0 skips pump start, invalid pump_id

**Blocker Notes:**
- ⏳ LEFOO pump Modbus documentation required
- ⏳ Phase 2.3 V2 helpers must be loaded (68+9+32+27 = 136 new helpers)
- ⏳ Pump selection helpers (zone_X_season_pump) must be added to zone_helpers.yaml

**Status:** 📋 PLANNED - Blocked on pump documentation

---

#### 3.3.2 Calibration & Maintenance Scripts
- [ ] 📋 `script.pump_tube_break_in` (param: pump_id)
- [ ] 📋 `script.pump_warmup` (param: pump_id)
- [ ] 📋 `script.run_calibration_trial` (param: pump_id, rpm_setpoint)
- [ ] 📋 `script.enter_calibration_data` (param: pump_id, slope, intercept, r_squared, pressure, notes)
- [ ] 📋 `script.run_quick_cal` (param: pump_id)
- [ ] 📋 `script.check_calibration_age` (no params - checks all 3 pumps)

**File Location:** `home-assistant/packages/watering_scripts/fert_cal_scripts.yaml`

**Scripts Implemented:**
1. `script.pump_tube_break_in` - 2-3 hour break-in at 30 RPM for new tubing
2. `script.pump_warmup` - 2-3 minute warmup at 50 RPM before calibration trials
3. `script.run_calibration_trial` - 180-second test at specified RPM, user enters mass, calculates flow
4. `script.enter_calibration_data` - Validates and stores calibration coefficients and metadata
5. `script.run_quick_cal` - 3-point validation (25/50/75 RPM), reports PASS/FAIL vs calibration curve
6. `script.check_calibration_age` - Daily automation check for EXPIRED (>365d) or WARNING (>90d)

**Key Features:**
- Manual procedures triggered via dashboard
- Full calibration: 5 RPM setpoints × 3 repeats = 15 trials per pump
- Quick cal: 3 RPM setpoints × 1 repeat = 3 trials (periodic validation)
- Validation: Slope > 0, R² ≥ 0.995, pressure 0.8-1.4 bar
- Dashboard integration: Progress bars, countdown timers, mass entry
- Automation: Daily check blocks operation if any pump EXPIRED

**Calibration Procedure:**
- Per `/docs/fert_pump_cal_v2.md`
- Test at 1.1 bar injection pressure (PRV setpoint)
- Measure mass → calculate flow → fit linear curve
- Store slope/intercept for inverse calculation during operation

**Dependencies:**
- Phase 3.3.1 (get_calibration_status script)
- Pump Modbus documentation
- Calibration helpers (27 total: 9 per pump)
- Dashboard UI for data entry (can be manual initially)

**Test Plan:**
- Full calibration on one pump (15 trials)
- Quick cal after tube replacement
- Age automation triggers at 90d/365d
- Invalid data rejection (slope=0, R²<0.95)
- Dashboard UI elements

**Blocker Notes:**
- ⏳ LEFOO pump Modbus documentation required
- Lower priority than 3.3.1
- Initial calibrations can be manual

**Status:** 📋 PLANNED - Can start after 3.3.1 complete

---

**Phase 3.3 Configuration Summary:**

**New Helpers Required (Phase 2.3 Extension):**

1. **Pump/Dose Configuration (32 helpers):**
   - `input_number.zone_{1-4}_{season}_dose_ml` (16 total)
   - `input_number.zone_{1-4}_{season}_pump` (16 total, values: 1-3)

2. **Calibration Storage (27 helpers, 9 per pump):**
   - `input_number.fert_pump{1-3}_cal_slope`
   - `input_number.fert_pump{1-3}_cal_intercept`
   - `input_number.fert_pump{1-3}_cal_r2`
   - `input_number.fert_pump{1-3}_cal_pressure`
   - `input_datetime.fert_pump{1-3}_last_cal`
   - `input_text.fert_pump{1-3}_cal_notes`

3. **V2 Tracking (9 helpers):**
   - `input_text.current_fertigation_zone`
   - `binary_sensor.zone_{1-4}_fertigation_active` (4)
   - `sensor.zone_{1-4}_fert_events_14d` (4)

4. **V2 Zone Configuration (68 helpers):**
   - `input_boolean.zone_{1-4}_allow_full_dose_light_program` (4)
   - `input_number.zone_{1-4}_{season}_normal_moisture_min` (16)
   - `input_number.zone_{1-4}_{season}_light_moisture_min` (16)
   - `input_number.zone_{1-4}_{season}_off_moisture_min` (16)
   - `input_number.zone_{1-4}_{season}_fert_14d_target` (16)

**Total New Helpers:** 136 (32 pump/dose + 27 calibration + 9 tracking + 68 zone V2)

**Reused Existing Helpers:**
- `input_datetime.zone_{1-4}_last_fert_event` (4)
- `input_select.zone_{1-4}_season` (4)

**V2 Design Notes:**
- Rolling 14-day window with seasonal targets
- Soil moisture primary trigger, rain fallback
- Tank level check first (system-wide block)
- Temperature removed from fert triggers
- Per `/docs/fert_prog_design.md` v1.1

**Calibration Notes:**
- Linear model: flow = slope × rpm + intercept
- Operational range: 5-100 RPM
- Per `/docs/fert_pump_cal_v2.md`
- Each pump calibrated independently

**Runtime Split:**
- Phase 1: 75% of total runtime + 2-min flush
- Phase 2: 75% of total runtime + 2-min flush
- Total: 150% of base runtime delivered as water
- Total: 4 minutes flush (line clearing only)

**For detailed script logic, see:** `/docs/fert_prog_design.md` Section 6 (Operational Scripts) and Section 9 (Calibration Integration)

---

### 3.4 Emergency/Safety Scripts
- [ ] 📋 `script.emergency_stop` (stops everything, resets to idle)
- [ ] 📋 `script.safe_shutdown` (graceful stop with pressure relief)
- [ ] 📋 Comms-lost handling — fail-fast + reactive recovery (surfaced 2026-07-31 during
      `safe_shutdown` verification; agreed design detailed in the sub-items below — this is
      now the canonical home). Deferred here from Phase 3.2 so the whole pattern lands with
      the safety layer.
  - [x] ✅ **Part A — fail-fast guard in `stop_main_pump`** (`watering_scripts/pump_scripts.yaml`,
        2026-08-03): inserted right after the 3 s settle delay, before the "verify pump
        stopped" `if`. When R1 (`switch.watering_system_relay_1_main_pump`) is
        `unavailable`/`unknown`, sets `error_comms_lost` (unless already errored), fires
        `pump_comms_lost` (severity `error`), and `stop … error: true`. Replaces the two
        misleading `critical` `pump_runaway` rows the unavailable path logged (loop guard
        `is_state(R1,'on')` fails on an unavailable entity, so the retry loop ran 0 s).
        Runaway branch untouched — only R1==`on` reaches it. Directly testable while R1
        is unavailable. NOTE: the `stop … error: true` is safely caught by callers using
        `continue_on_error` — verified 2026-08-03 that `continue_on_error` DOES suppress a
        called script's `stop:error:true` (see the `safe_shutdown` early-halt resolution below).
  - [x] ✅ **Part B — reactive-recovery automation** (`watering_safety/safety_automations.yaml`,
        2026-08-03): `automation.watering_safety_r1_comms_recovery` triggers on R1 returning
        from `unavailable`/`unknown` to `on`/`off` while `watering_system_state ==
        error_comms_lost`. **R1 back `on` → `script.emergency_stop`** (all relays off,
        critical notification, latched `error_e_stop`) after a `pump_comms_restored`
        (`warning`) audit row. **R1 back `off` → `pump_comms_restored` (`info`) + clear to
        `idle`.** Race-guarded: the OFF→idle branch re-checks R1 is *currently* off and
        there is no `default`, so a flap-back to `unavailable` can't clear the error on a
        stale read. Implemented as an automation (not a waiting script) so it re-arms across
        HA restarts and never blocks synchronous callers (`safe_shutdown`,
        `open_pressure_relief`, the state machine).
        **DESIGN CHANGE vs the original spec:** the `on` branch now escalates to
        `emergency_stop` instead of re-running `stop_main_pump` + staying in
        `error_comms_lost`. Rationale: after a blind period the whole relay set
        (zones/valves) is of unknown position, not just R1, so a full estop restores a
        known-safe baseline, alerts a human (critical notification), and latches the
        stronger `error_e_stop`. Tradeoff accepted: loses `stop_main_pump`'s 120-min
        aggressive retry, but a reachable relay obeys a turn-off in one repair cycle, and
        the ESP32 on-device 120-min auto-off remains the hardware backstop. (Not big enough
        for an ADR; captured here.)
  - [x] ✅ **Generalize** the fail-fast + recovery pattern across the safety layer. Concrete
        sub-items surfaced while building Parts A/B are DONE (2026-08-03):
        - [x] ✅ (a) `open_pressure_relief`'s `stop_main_pump` call given `continue_on_error`
          so a mid-run R1 drop (Part A's `stop:error:true`) no longer halts it before its own
          wait+verify (`pump_scripts.yaml`).
        - [x] ✅ (b) `safe_shutdown` no longer forces `idle` when it ends in an `error_` state
          — it preserves the error (so Part B, keyed off `error_comms_lost`, can still fire)
          and logs completion with the final state (`watering_safety_scripts.yaml`).
        - [x] ✅ (c) Part B's OFF→idle branch now calls `close_all_zones` before clearing, so
          recovery lands on a genuinely clean idle (`safety_automations.yaml`).
        - Already comms-aware, no change needed: `start_main_pump` (tank/relief/R6-R7/pump
          availability checks already abort to `error_comms_lost`) and `emergency_stop`
          (treats `unavailable` relays as failures, retries + notifies).
        - [x] ✅ (d) **Recovery-trigger hardening** (2026-08-05, `safety_automations.yaml`):
          the Part B recovery automation now arms on ANY of the seven wet-path relays
          (R1–R7) returning from `unavailable`/`unknown`, not R1 alone, then reads R1's
          **live** state to decide (estop if `on`, close-zones→idle if `off`, no-default
          if still unreadable). All seven share one ESP32/WiFi link, so a comms loss is
          device-level and a reconnect restores them together — arming on the whole set
          makes recovery robust to which relay's state-change event lands first, while the
          decision stays purely R1-based. `mode: restart`→`mode: single` so the up-to-seven
          near-simultaneous reconnect triggers can't cancel an in-flight `emergency_stop`.
        **Design note — why NOT the originally-specified per-relay shape:** the earlier spec
        (a shared automation keyed off *which relay* is unavailable, plus `safety_comms_lost`
        /`safety_comms_restored` event_types) over-fits a per-relay failure model the hardware
        can't produce — the relays never go unavailable independently. The device-level
        trigger above is the right generalization. The `safety_comms_*` event-type split stays
        a **conditional** future task: do it only if/when the safety scripts fork into
        distinct comms-loss sources (not the case today; all comms loss is the single ESP32).

**`safe_shutdown` early-halt (RESOLVED 2026-08-03):** the halt was NOT `stop_main_pump`'s
`stop:error:true` (a Dev-Tools probe confirmed `continue_on_error` DOES catch a called
script's `stop:error:true`). The real cause was `script.stop_dosing_pumps` not existing
(Phase 3.3 skipped): `continue_on_error` does **not** suppress a `ServiceNotFound`, so the
call halted the sequence at that step. Fixed in `watering_safety_scripts.yaml` by guarding
the call on the script entity existing and being available; the guard passes automatically
once 3.3 ships.

**File Location:** Part A edits the existing `watering_scripts/pump_scripts.yaml`; the
`stop_dosing_pumps` guard edits `watering_scripts/watering_safety_scripts.yaml`; Part B lives in
`watering_safety/safety_automations.yaml` (named to avoid the `!include_dir_named` basename
collision that a bare `automations.yaml` would risk). The `emergency_stop` / `safe_shutdown`
scripts themselves already exist in `watering_scripts/watering_safety_scripts.yaml`.

**Test Plan:**
- [ ] Emergency stop during watering — PENDING (needs ESP32 online)
- [ ] Emergency stop during fertigation — BLOCKED on Phase 3.3
- [ ] Verify all relays physically off + state latch — PENDING (needs ESP32 online; see below)
- [x] ✅ Comms-lost Part A: with R1 `unavailable`, call `stop_main_pump` → exactly one
  `pump_comms_lost`/`error` row, state → `error_comms_lost`, no `pump_runaway` rows.
- [x] ✅ Comms-lost Part B: with state `error_comms_lost`, force R1 `unavailable` → back `off`
  (`pump_comms_restored` info + zones closed + clear to `idle`); and → back `on`
  (`pump_comms_restored` warning + `emergency_stop` → `error_e_stop` + critical notification).
- [x] ✅ `safe_shutdown` completion: call `safe_shutdown` while R1 is unavailable (so `stop_main_pump` ends
  `stop:error:true`) with `stop_dosing_pumps` absent → `safe_shutdown` runs to completion
  (both "started" and "completed" rows, no `ServiceNotFound` halt) and PRESERVES the error
  state instead of forcing `idle` (generalize (b)).
- [ ] 📋 Recovery-trigger hardening (generalize (d), 2026-08-05): with state `error_comms_lost`
  and R1 `off`, drive a **non-R1** relay (e.g. R3) `unavailable→off` via Dev Tools → recovery
  fires, decides on R1=off → `close_all_zones` + clear to `idle`; audit message names the
  triggering relay. Repeat with R1 `on` → `emergency_stop`. Confirm R1's own trigger still
  works and that a non-R1 trigger while R1 is still `unavailable` hits the no-default branch
  (no state change). Dev-Tools-simulatable now; runs with the other comms-lost Dev Tools tests.

**Verification (2026-08-03):** the comms-lost paths (Part A, Part B OFF/ON, and the
`safe_shutdown` completion fix)
were run live on the HA Green and all PASSED (`system_events` rows 46–58). The ESP32 was
offline (genuine WiFi loss), so R1 transitions were simulated via Developer Tools → States
(fires real state-change events) — this validates the HA control logic. Physical relay
de-energization for `emergency_stop` / `safe_shutdown` happy-paths (all relays actually off,
real pump→relief cycle) remains PENDING until the ESP32 is back online.

**Blocker Notes:** Comms-lost logic done + verified (simulated). The two remaining hardware
happy-path tests (`emergency_stop` all-relays-off; graceful `safe_shutdown`) are blocked
until the ESP32 rejoins WiFi (R1 currently `unavailable`). "Emergency stop during
fertigation" is blocked on Phase 3.3.

---

### 3.5 Operational Database Infrastructure

**Engine:** SQLite (single file) + AppDaemon. No MariaDB — see ADR-011 (SQLite revision,
in `docs/programming-notes.md`) for the rationale.

- [x] ✅ Author SQLite schema `docs/db_schema.sql` (four tables, FK/index/CHECK)
- [x] ✅ Author idempotent AppDaemon bootstrap (`db_schema_init.py` + `apps.yaml`)
- [x] ✅ Author HA-side setup guide (`docs/db_setup_guide.md`)
- [x] ✅ Install and configure AppDaemon add-on on the HA Green (2026-06-29)
- [x] ✅ Wire schema deploy into `pull_public_repo.sh` (no drift between
      `docs/db_schema.sql` and the deployed copy) (2026-06-30)
- [x] ✅ Deploy bootstrap + schema to the AppDaemon app dir; verify tables created —
      end-to-end verified 2026-06-30 via pull -> AppDaemon restart -> SQLite Web
      add-on (`fertigation_doses`, `system_events`, `watering_cycles`,
      `zone_runs` all present)
- [x] ✅ Implement AppDaemon DB write listeners — Events 1/3/4/5 done. Event 5
      (`system_events`) = `db_event_writer.py` (`DbEventWriter`). Events 1/3/4
      (`watering_preflight_complete` / `_zone_run_complete` / `_cycle_complete`) =
      `db_writer.py` (`DbWriter`, 2026-08-16): opens/closes `watering_cycles`,
      inserts `zone_runs`, holds the `cycle_uuid`/`zrun_uuid` -> PK correlation in
      memory, computes `actual_duration_sec`, derives `fertigated` from an in-memory
      dose buffer, and publishes `binary_sensor.watering_cycle_active` (ON@E1/OFF@E4).
      Logic-tested locally (`tests/test_db_writer.py`, ALL PASS). **Event 2**
      (`watering_fert_dose_complete` -> `fertigation_doses`) deferred: no publisher
      (fert hardware unwired) — the dose-buffer scaffold is in place so E3 already
      derives `fertigated`; the E2 listener + INSERT flush land with the fert path.
      **VERIFIED LIVE ON THE GREEN 2026-08-16** (Tests 10.6/10.7/10.9 PASS: a parallel manual
      cycle wrote one `watering_cycles` row + four `zone_runs`, `binary_sensor.watering_cycle_active`
      toggled on/off, and deterministic orphan/reject events produced the right breadcrumbs).
- [ ] 📋 **Decision-criteria recording on `zone_runs` (ADR-018).** Add `season TEXT`
      (CHECK spring/summer/fall/winter) + `decision_criteria TEXT` (JSON: the five thresholds,
      the actual weather inputs compared — incl. the real `temp_avg_high_3day` the tree decides
      on, NOT the `temp_high_yesterday` currently in `watering_cycles.temp_high_c` — and the
      branch that fired) to `docs/db_schema.sql`; extend the Event 3
      (`watering_zone_run_complete`) payload + `db_writer.py` INSERT to carry them.
- [ ] 📋 **Extract the §6.2 decision into one shared, side-effect-free routine (ADR-018).**
      Inputs: weather + zone/season config → `program` + `program_multiplier` + `criteria`.
      `state_window_check` calls it then applies (sets `zone_N_program`); the weather logger
      (§3.6) calls it to log. Single source of truth feeding both `zone_runs.decision_criteria`
      and `zone_decisions`. Prerequisite for both. Touches a safety-adjacent script → full
      "Before You Code" + review; extraction is behaviour-preserving.
- [ ] 📋 Implement AppDaemon decision query sensors (14-day fert window minimum)
- [x] ✅ Implement seasonal CSV export script (AppDaemon) — `db_export.py`
      (`DbSeasonalExport`), year-filtered CSVs to `/homeassistant/watering_exports/`,
      header-only when empty, `system_events` audit row (2026-06-30)
- [x] ✅ Integrate seasonal CSV export trigger into winterization automation (Phase 9)
      — `home-assistant/packages/watering_db/db_automations.yaml` fires the
      `watering_seasonal_export` event on `system_winterized` OFF -> ON (2026-06-30)
- [x] ✅ Define and document HA event payload schemas for all DB write triggers
      (2026-06-30; full contract in architecture.md §13.3.1)
- [x] ✅ Confirm HA backup includes the SQLite file (`/homeassistant/watering_ops.db`)
      — verified 2026-06-30 via backup metadata: the `homeassistant` component is
      included and `exclude_database: false` (DB files not excluded); the file lives in
      the backed-up config dir

**File Locations:**
- `docs/db_schema.sql` — SQLite physical schema, version-controlled source of truth ✅
- `docs/db_setup_guide.md` — HA-side setup (AppDaemon add-on) ✅
- `home-assistant/appdaemon/watering_db/db_schema_init.py` — bootstrap that applies the schema on start-up ✅
- `home-assistant/appdaemon/watering_db/apps.yaml` — AppDaemon app config ✅
- `home-assistant/appdaemon/watering_db/db_event_writer.py` — Event 5 (`system_events`) listener/writer ✅
- `home-assistant/appdaemon/watering_db/db_writer.py` — Events 1/3/4 (`watering_cycles` + `zone_runs`) listeners/writer + `binary_sensor.watering_cycle_active` publisher ✅ (Event 2 flush deferred)
- `home-assistant/appdaemon/watering_db/db_queries.py` — Decision query logic and sensor updates (later)
- `home-assistant/appdaemon/watering_db/db_export.py` — Seasonal CSV export ✅
- `home-assistant/packages/watering_db/db_automations.yaml` — HA winterization trigger that fires the export event ✅
- `home-assistant/appdaemon/watering_db/tests/test_db_export.py` — stdlib logic test for the export (run: `python .../tests/test_db_export.py`); not deployed (pull copies only top-level app files) ✅
- `home-assistant/appdaemon/watering_db/tests/test_db_writer.py` — stdlib logic test for the cycle/zone-run writer (run: `python .../tests/test_db_writer.py`); not deployed ✅

**Deploy note:** AppDaemon apps run from the AppDaemon app dir, not HA's package system.
The repo stores them under `home-assistant/appdaemon/watering_db/` (deliberately NOT
under `packages/`, which HA loads via `!include_dir_named`); `pull_public_repo.sh`
deploys them to `/homeassistant/appdaemon/apps/watering_db/` (with a pull-copied
`db_schema.sql`). See `docs/db_setup_guide.md`.

**Architecture:**
Two-layer design per ADR-011 (in `docs/programming-notes.md`):
- **Layer 1 — SQLite (single file):** Dedicated `watering_ops` database at
  `/homeassistant/watering_ops.db`, separate from HA recorder, inside HA backups. Tables:
  `watering_cycles`, `zone_runs`, `fertigation_doses`, `system_events`
- **Layer 2 — AppDaemon add-on:** Python bridge between HA and SQLite (`sqlite3` stdlib, no
  driver). Listens for state machine events, writes records, and returns decision query
  results as HA sensor states

**Schema Notes (decisions & deferred constraints):**
- `fertigation_doses.pump_id` stores the **logical pump number (1-3)**, not the raw Modbus
  address (0x02-0x04). More robust: the record survives any pump re-addressing or rewiring.
- **No `UNIQUE(cycle_id, zone_id)` on `zone_runs`** (deferred for flexibility — a zone may
  legitimately run more than once per cycle, e.g. dual-window heavy). If duplicate or
  ambiguous zone-run rows ever cause query trouble, revisit adding this constraint. Flagged
  here for future visibility per the 2026-06-28 decision.

**DB Write Trigger Points:**

| DB Write | Trigger | HA Event |
|----------|---------|----------|
| `watering_cycles` INSERT | Preflight check passes | `watering_preflight_complete` |
| `zone_runs` INSERT | Zone run concludes | `watering_zone_run_complete` |
| `fertigation_doses` INSERT | Dosing event concludes | `watering_fert_dose_complete` |
| `watering_cycles` UPDATE | Cycle concludes | `watering_cycle_complete` |
| `system_events` INSERT | Safety/error event fires | `watering_system_event` |

**Note:** The HA event payload schemas are the contract between the state machine and
AppDaemon. They are now defined in architecture.md §13.3.1 and must be honoured when
Phase 4 (state machine) is built — the state machine fires these events; the AppDaemon
writer consumes them.

**Decision Queries (minimum for Phase 4):**
- 14-day rolling fertigation dose total per zone → `sensor.zone_{1-4}_fert_delivered_14d_ml`
- Cycle currently running → `binary_sensor.watering_cycle_active`

**Archive Strategy:**
- Ongoing: SQLite file (`/homeassistant/watering_ops.db`) included in HA automated backup
- Seasonal: CSV export of all four tables, triggered alongside winterization automation
- Retention: Database accumulates across seasons (no truncation); CSV archives kept indefinitely

**Dependencies:**
- ADR-011 ✅ (accepted, SQLite revision — in `docs/programming-notes.md`; defines schema and architecture)
- Phase 3.3 📋 (fertigation scripts need dose records written — can develop in parallel
  but must be complete before integration testing)
- Phase 3.4 📋 (emergency stop events need `system_events` write path)
- Phase 4 📋 (state machine must fire the agreed HA events at correct transition points)

**Test Plan:** (tracked in `docs/test_scenarios.md` Section 10; the state-machine event
emission half is Test 3.5)
- AppDaemon opens the SQLite file and the bootstrap creates all four tables
- Schema created cleanly, all tables present (verify via `sqlite_master`)
- Each HA event triggers correct DB write (verify via SQL query)
- Decision query sensor updates correctly after write
- 14-day window query returns correct value across date boundaries
- Cycle-in-progress query reflects correct state
- CSV export produces well-formed files for all four tables
- HA backup confirmed to include the SQLite file

**Blocker Notes:**
- HA event payload schemas must be defined before AppDaemon listeners can be implemented
  (Phase 4 contract)
- Phase 3.3 / 3.4 are being skipped for now; the writer/query apps and integration testing
  still depend on the events those phases fire, so the write-path work stays deferred
- Coordinate event naming with Phase 4 state machine design

**Status:** 🚧 IN PROGRESS — schema, bootstrap, AppDaemon install, deploy wiring, the event
payload contract (§13.3.1), and backup inclusion of the DB done/verified 2026-06-30. The
Events 1/3/4 **write listeners (`db_writer.py`) and the seasonal CSV export are now deployed
and VERIFIED LIVE ON THE GREEN 2026-08-16** (Tests 10.4/10.6/10.7/10.9 PASS). The only
remaining 3.5 items are the **decision-query sensors** (blocked on the fert path / query app)
and the **Event 2 fert-dose writer** (blocked on RS-485 dosing hardware).

---

### 3.6 Weather Observations Database (NEW — ADR-018)

**Status:** 📋 PLANNED — design only (ADR-018, 2026-08-18). No code yet.
**Amended 2026-08-25 (ADR-021):** this ADR is now the **single** decision-recording mechanism
(ADR-021's earlier standalone `decisions` table was retired in its favour). The `decision_criteria`
/ `zone_decisions` JSON gains the moisture-primary inputs (moisture % + sensor count, de-lagged temp
used, forecast POP/volume, thresholds live at the time, branch/`skip_reason`), and the "shared
decision routine" computes the ADR-021 §3.2 moisture-primary tree. The two "Deferred / open" items
below are RESOLVED by ADR-021 (temp metric → de-lagged forecast/current high; threshold helpers →
pure RestoreEntity). Same hardware gate as ADR-021.

**Purpose:** a twice-daily weather + computed-decision time series, INDEPENDENT of whether we
water, so decision effectiveness can be evaluated in one place against the incoming weather
station / rain sensor / wireless soil-moisture hardware. Captures the skip and parked days that
`zone_runs` never sees (the §3.5 gap).

**Engine:** separate SQLite file `/homeassistant/watering_weather.db` + AppDaemon (same pattern
as `watering_ops`, ADR-011). Separate DB, not a new ops table: long-term retention (no pruning)
vs ops' 14-day rolling window; continuous series vs event-driven cycles. Correlate to ops by
`observed_at` / `window` (`ATTACH` for cross-DB joins).

**Schema (two tables, parent/child — mirrors `watering_cycles → zone_runs`):**
- `weather_snapshots` — one row per window: `observed_at` (UTC TEXT), `window`
  (morning/evening), `source` ('brightsky' now; 'local_station' later), typed columns for the
  Brightsky set (`temp_now_c`, `temp_high_yesterday_c`, `temp_avg_high_3day_c`, `rain_24h_mm`,
  `rain_72h_mm`, `rain_now_mm`, `humidity_pct`, dew point, wind, cloud, sunshine, pressure,
  `raining_now`…), plus `raw TEXT` (JSON catch-all so a new sensor is never lost before it earns
  a typed column). WIDE, not tall/EAV (ADR-018 rationale).
- `zone_decisions` — 4 rows per snapshot (FK → `weather_snapshots.id`): `zone_id`, `season`,
  `computed_program`, `program_multiplier`, `decision_criteria` (JSON), `would_water` (0/1).

Build items:
- [ ] 📋 Author `docs/weather_schema.sql` (two tables above; FK + CHECK + indexes; UTC TEXT
      timestamps; writer sets `PRAGMA foreign_keys=ON` per connection).
- [ ] 📋 AppDaemon bootstrap for the weather DB (idempotent, mirrors `db_schema_init.py`); wire
      the schema deploy into `pull_public_repo.sh` (no drift).
- [ ] 📋 AppDaemon `weather_logger` app + writer (`watering_weather/weather_logger.py`) — a dumb
      sink consuming the `watering_weather_snapshot` event, INSERTing one `weather_snapshots`
      row + four `zone_decisions` rows. All decision logic stays in HA (CORE PRINCIPLE).
- [ ] 📋 HA snapshot automation (`home-assistant/packages/watering_weather/…`) triggered on the
      SAME `input_datetime.morning_window_start` / `evening_window_start` helpers as the
      scheduler — fires in EVERY state (parked/winterized/mid-cycle/idle). Gathers the sensor
      snapshot, calls the shared §6.2 decision routine (§3.5) per zone, fires
      `watering_weather_snapshot` with the full payload.
- [ ] 📋 Define the `watering_weather_snapshot` event payload contract (architecture.md §13.3.x)
      — snapshot fields + `zone_decisions[]`.
- [ ] 📋 Export-only winterized dump: extend the existing winterization export
      (`db_automations.yaml` / `db_export.py`) to ALSO dump `weather_snapshots` +
      `zone_decisions` to CSV at the same `winterized`-state event — EXPORT ONLY, no delete
      (weather DB keeps full history). Synchronized landing with the ops seasonal export.
- [ ] 📋 Confirm `/homeassistant/watering_weather.db` is inside the HA backup (same check as ops).
- [ ] 📋 Logic tests (stdlib, mirror `tests/test_db_writer.py`): writer INSERT correctness +
      export shape.

**Deferred / open** (settle with the sensor hardware — START_HERE follow-up #4 / ADR-021):
- ~~Which temperature the decision SHOULD use~~ — **RESOLVED (ADR-021):** de-lagged forecast/current
  high (the 3-day average is demoted to reporting). Still store raw for analysis.
- ~~Whether `zone_N_{season}_*` threshold helpers become RestoreEntity~~ — **RESOLVED (ADR-021):**
  yes, pure RestoreEntity.
- Per-season (not just annual/winterization) CSV bundles → would need a season-change trigger.

**Dependencies:** ADR-018 ✅ (accepted); the shared §6.2 decision routine (§3.5) — prerequisite;
ADR-011 (DB pattern), ADR-013 (event → writer).

---

## Phase 4: Home Assistant - State Machine

**Status:** ✅ COMPLETE (plain-watering path) — built, code-reviewed (4 passes,
docs/phase_4_review_1.md / _2.md), deployed to the Green 2026-08-15, Dev-Tools/dry-run
tested (test_scenarios.md Test 3.6, a–l ALL PASS at relay/logic level; valves/pump
physically unwired). Only the 3 fert-path state scripts remain, blocked on RS-485
dosing hardware.

**Control structure decided in ADR-015** (D1–D4). Scope: plain-watering path only
(`idle → window_check → preflight_check → watering_plain → post_cycle_relief → idle`).
Fert states + live-hardware validation deferred (Blocker §2). Each `state_*` script
**sets its own next state** at its tail (next on success, `error_*` on failure) —
the dispatcher only calls; the scripts advance. **Two correctness rules for every
`state_*` script (ADR-015):** (A1) guard the advance — only set the next state if
still in my own state (else a parallel safety event just took over; exit without
advancing); and never `continue_on_error` around safety-critical subscripts (let the
error propagate to the per-error automation).

### 4.1 State Transition Scripts
- [x] ✅ New Phase 4 helpers (config_helpers.yaml) — **verified in code**
  (`watering_helpers/config_helpers.yaml:73-199`):
  - `input_text.cycle_uuid`, `input_text.zone_run_uuid` (ADR-014).
  - `input_select.active_watering_window` (`morning`/`evening`) and
    `input_select.active_trigger_type` (`scheduled`/`manual`; `override` reserved,
    unused in Phase 4) — D2 context carried across the parameterless state
    transitions; set by the scheduler at cycle start, read by `run_zone_sequence` / Event 1.
  - `input_button.start_watering_cycle_now` — manual/testing trigger for the scheduler.
- [x] ✅ `script.state_window_check` — **verified in code** (`state_scripts.yaml:184`)
  and Dev-Tools-swept (Test 3.6.c, test_scenarios.md §5.1/5.2 — all branches PASS).
  - Evaluate weather + season per zone; set `input_select.zone_N_program`
    (off/light/normal/heavy) via the §6.2 decision tree.
  - If all four zones resolve to `off`, short-circuit back to `idle` (nothing due).
  - Else transition to `preflight_check`.
- [x] ✅ `script.state_preflight_check` — **verified in code** (`state_scripts.yaml:311`)
  and dry-run tested (Test 3.6, test_scenarios.md).
  - Verify tank levels — two-tier gate by cycle type (see architecture.md §2.2):
    plain watering gates on **Low-Low** (`binary_sensor.watering_system_low_low_water_level`,
    GPIO32); fertigation gates on the earlier **Low**
    (`binary_sensor.watering_system_low_water_level`, GPIO33) so a dose can never
    be cut off without completing its flush.
  - Check ESP32 online; verify no existing `error_`/`winterized`/`manual_override` state.
  - On pass: **mint `cycle_uuid`** (`{{ 'c-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') }}`)
    into `input_text.cycle_uuid`, then **fire Event 1** `watering_preflight_complete`
    (`start_time`; `trigger_type` from `active_trigger_type`; `rainfall_24h_mm`/`72h`
    from `brightsky_rain_24h/72h`; `temp_high_c` from `brightsky_temp_high_yesterday`).
  - Branch to `watering_plain` (plain) OR `fert_prep` (fert, deferred). On fail →
    appropriate `error_*` state.
- [x] ✅ `script.state_watering_plain` — **verified in code** (`state_scripts.yaml:518`)
  and dry-run tested (Test 3.6.f/g, relay-level).
  - Open bypass valve (R6), close fert line (R7); start main pump (R1).
  - Call `run_zone_sequence(active_watering_window)` — **Event 3 per zone is fired
    inside `run_zone_sequence`** (D1), not here.
  - Stop pump, close zones; transition to `post_cycle_relief`.
- [ ] 📋 `script.state_fert_prep` (Future - Phase 2) — **not in code**; still blocked
  on RS-485 dosing hardware (fert path).
- [ ] 📋 `script.state_fert_dose_phase1` (Future - Phase 2) — **not in code**; fert path.
- [ ] 📋 `script.state_fert_dose_phase2` (Future - Phase 2) — **not in code**; fert path.
- [x] ✅ `script.state_post_cycle_relief` (built from subscripts, D3) — **verified in code**
  (`state_scripts.yaml:584`) and dry-run tested (Test 3.6.g).
  - `close_all_zones` (defensive) → `open_pressure_relief` (R9 cycle) → disable 24V (R10).
  - Call `script.finalize_cycle_record` with `outcome: completed`.
  - Transition to `idle`.
- [x] ✅ `script.finalize_cycle_record(outcome, notes)` — **reporting-layer cleanup ONLY (D3)** —
  **verified in code** (`state_scripts.yaml:62`) and tested (Test 3.6.j).
  - Fires Event 4 `watering_cycle_complete` from `input_text.cycle_uuid`, then clears
    the helper. **No-ops** if no cycle is open (empty `cycle_uuid` /
    `binary_sensor.watering_cycle_active` off).
  - MUST NOT run pressure relief, stop hardware, or set system state — it never
    supersedes or triggers the error-state teardown. `emergency_stop` / `safe_shutdown`
    keep sole ownership of safing + latching and merely *also* call `finalize_cycle_record`
    afterward so the DB row + cycle-active sensor always close (aborted/error).
- [x] ✅ `script.abort_cycle_scripts` — **A2 prompt cancellation.** **Verified in code**
  (`state_scripts.yaml:146`) and tested (Test 3.6.e). `script.turn_off`s
  the in-flight progression scripts (turn_off does NOT cascade to subscripts, so the set
  is named explicitly): `state_window_check`, `state_preflight_check`, `state_watering_plain`,
  `state_post_cycle_relief`, `run_zone_sequence`. NEVER include the teardown/reporting
  scripts (`safe_shutdown`, `emergency_stop`, `stop_main_pump`, `close_all_zones`,
  `close_pressure_relief`, `finalize_cycle_record`, `log_system_event`). Called (before
  `safe_shutdown`) by the per-error, restart-recovery, and control-state automations.
  Best-effort — A1's guard owns correctness, so a missing entry only leaves a harmless
  lingering delay.
- [x] ✅ Modify `run_zone_sequence` (Phase 3.1) — reporting additions only (D1) —
  **verified in code** (`zone_scripts.yaml`: `fire_zone_run_complete` + `water_one_zone`
  subscripts) and tested (Test 3.6.f, Test 4.5a).
  - Per zone sub-sequence: mint a **local** `zrun_uuid`
    (`'z-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') ~ '-' ~ zone_id`, parallel-safe),
    capture start/end, fire Event 3 `watering_zone_run_complete` at the zone's close.
  - Watering logic unchanged; the shared `input_text.zone_run_uuid` helper stays
    reserved for the sequential fert path (ADR-015 / §13.3.1).

**File Location:** `home-assistant/packages/watering_state/state_scripts.yaml`
(`finalize_cycle_record` lives here, alongside `abort_cycle_scripts`).

**Test Plan:** See Section 7 (Testing Scenarios) — Test 3.6 walkthrough ✅ COMPLETE, all sub-tests PASS.

**Blocker Notes:** _None — plain-watering path complete. Only the three fert-path scripts
(`state_fert_prep`/`_dose_phase1`/`_dose_phase2`) remain, blocked on RS-485 dosing hardware._

---

### 4.2 Master State Machine Automation (ADR-015 D4)
- [x] ✅ **Dispatcher** automation — **verified in code** as `automation.watering_state_dispatcher`
  (`state_machine.yaml:42`) and tested (Test 3.6.a/b): trigger on `input_select.watering_system_state`
  change → `choose` on the new state → call `script.state_<state>`. `mode: queued`
  so a rapid next-state change is never dropped. Error states have no dispatch branch
  (progression halts; safety automations handle recovery).
- [x] ✅ **Scheduler** automation (separate) — **verified in code** as `automation.watering_state_scheduler`
  (`state_machine.yaml:73`) and tested (Test 3.6.b): triggers = morning/evening window times
  (gated by `enable_*_window`, `active_trigger_type: scheduled`) + `input_button.start_watering_cycle_now`
  (`active_trigger_type: manual`, window by time-of-day: morning before midday else
  evening); condition `state == idle`; action sets `active_watering_window` +
  `active_trigger_type`, then moves `idle → window_check`.
- [x] ✅ Manual test path: setting `input_select.watering_system_state` directly in
  Dev Tools also drives the dispatcher (enabled by the D4 dispatcher model) — **verified**:
  the dispatcher triggers on any state-entity change regardless of source, and this is the
  mechanism the whole §2 Dev-Tools safety-monitor test suite relies on.
- [x] ✅ **Per-error entry automation (ADR-015 D-D)** — **built + tested, but reshaped
  from the originally-planned 5 automations into 1 table-driven automation**
  (`automation.watering_state_on_error`, `state_machine.yaml:176`, §2.4 code-review
  refactor) keyed by a per-error policy table, since all 5 shared the same
  abort→[safe_shutdown]→finalize→notify skeleton and differed only in two columns.
  Tested Test 3.6.g/h/j — all error entries PASS. Behavior unchanged from spec:
  - `on_error_e_stop`, `on_error_comms_lost` → `finalize_cycle_record` only (no safe_shutdown).
  - `on_error_tank_low`, `on_error_valve_interlock`, `on_error_relay_state` →
    `safe_shutdown` → `finalize_cycle_record` (uniform, D-D1).
  - **Notification (Phase 4, #3):** each sends a tier-appropriate notification via the
    Phase 9 scripts — EXCEPT `on_error_e_stop` (`emergency_stop` already notifies).
- [x] ✅ **Restart recovery automation (ADR-015 D-E, thorough)** — **verified in code**
  as `automation.watering_state_restart_recovery` (`state_machine.yaml:294`) and tested
  (Test 3.6.i, PASS 2026-08-16): on `homeassistant.start`, any non-idle state →
  `abort_cycle_scripts` → `safe_shutdown` → `finalize_cycle_record` (all `continue_on_error`);
  operational → `idle`, error → latch preserved.
- [x] ✅ **Control-state guard automation (ADR-015 D-F revised)** — **built + tested, but
  merged from the originally-planned 2 automations into 1 parametrized automation**
  (`automation.watering_state_control_guard`, `state_machine.yaml:364`, §2.5 code-review
  refactor) keyed on `trigger.entity_id`, since the manual-override and winterized guards
  were near-identical 5-branch automations differing only in which boolean/state pair they
  drove. Tested Test 3.6.h — all branches PASS. Behavior unchanged from spec:
  `manual_override_active` / `system_winterized`. Boolean → ON: if `idle` engage
  (park in the state); if operational **reject** (revert boolean to OFF + notify "stop
  the cycle first"); if `error_*` warn + require acknowledgement then engage. Boolean →
  OFF: return to `idle`. NO auto-abort of a running cycle.
- [x] ✅ Existing (unchanged): comms Part B `watering_safety_r1_comms_recovery`
  (`watering_safety/safety_automations.yaml`) — built + tested under Phase 3.4.

See **ADR-015 addendum (D-A…D-H)** for the rest of the walkthrough decisions:
weather-unavailable fallback (`normal`, D-A); fert-due → plain fallback + fert-target=0
deployment default (D-B); no cadence gate (D-C — **CLOSED 2026-08-22 by ADR-020**: per-zone
interval `zone_N_watering_interval_days` + master `zone_N_enabled` now gate `state_window_check`);
tank-`unavailable`→`error_comms_lost`
(D-G); manual reset model (D-H); safe-first on override/winterize mid-cycle (D-F).

**File Location:** `home-assistant/packages/watering_state/state_machine.yaml` — 5 automations
total (dispatcher, scheduler, on_error, restart_recovery, control_guard).

**Blocker Notes:** _None — deployed to the Green and Dev-Tools/dry-run tested (Test 3.6.a–l,
ALL PASS, relay/logic level; valves/pump unwired). See test_scenarios.md._

---

## Phase 5: Home Assistant - Safety Interlocks

**Status:** ✅ COMPLETE 2026-08-16 — all three monitors built, code-reviewed, deployed to the
Green, and Dev-Tools tested PASS (test_scenarios.md §2, Tests 2.1/2.2/2.3, plus 2.6 for the
shared `watering_operational` predicate). This phase was specified before Phases 3.4
(comms-lost handling) and 4 (state machine + per-error table) existed. Those provide the
downstream safing/notify machinery these monitors were originally going to carry themselves, so
the built scope became **3 independent monitors, each re-scoped to a bare state transition**:
entry to any `error_*` state fires the Phase 4 `watering_state_on_error` table
(`watering_state/state_machine.yaml`), which runs `abort_cycle_scripts` -> `safe_shutdown` (per
policy) -> `finalize_cycle_record(error)` -> tiered notification. A monitor only has to *latch
the state*; the table does the rest.

### 5.1 Independent Safety Monitors

- [x] ✅ `automation.safety_tank_low_low` — **BUILT + DEPLOYED + TESTED 2026-08-16 (test_scenarios.md
  Test 2.1 PASS)**
  - Trigger: `binary_sensor.watering_system_low_low_water_level` -> ON.
  - Gap it fills: `state_preflight_check` only samples Low-Low at cycle START; nothing
    catches the tank crossing Low-Low **mid-cycle**. This is that independent monitor.
  - Action (re-scoped): set `input_select.watering_system_state` -> `error_tank_low`.
    Do NOT stop the pump / notify here — that is now the `watering_state_on_error` table's
    job (`safe_shutdown` closes R1 + relieves + finalizes; tank tier = CRITICAL notify).
  - Build decision: guard to fire only from an operational state (a Low-Low reading while
    idle / parked / already-errored must not thrash the machine).

- [x] ✅ `automation.safety_comms_watchdog` — **BUILT + DEPLOYED + TESTED 2026-08-16 (test_scenarios.md
  Test 2.2 PASS)**
  - Trigger: ESP32 unreachable for a debounce window (design target: >10 s).
  - Gap it fills: Phase 3.4 Part A only fires when `stop_main_pump` is CALLED, and Part B
    (`watering_safety_r1_comms_recovery`) only handles RECOVERY once already in
    `error_comms_lost`. Neither proactively latches the error on a mid-cycle dropout.
  - Action (re-scoped): set state -> `error_comms_lost` (the `on_error` table sends the
    HIGH notify; Part B then owns recovery on reconnect).
  - Built as (decided 2026-08-16): trigger = **R1-R7 relay-availability proxy** (the
    same signal Part B keys off, one source of truth) with a **10 s `for:`** debounce;
    guard = operational-states-only complement (also excludes an already-latched
    `error_comms_lost`, so a second relay dropping does not re-fire); `mode: single`.

- [x] ✅ `automation.safety_zone_runtime_limit` — **BUILT + DEPLOYED + TESTED 2026-08-16 (test_scenarios.md
  Test 2.3 PASS, incl. the two regression parts B/E for the code-review fixes)**
  - Trigger: any zone valve (R2-R5) ON for > `input_number.max_single_zone_runtime_min`.
  - Action: close THAT zone (direct `switch.turn_off` on the triggering relay) +
    `send_high_notification`. Standalone backstop against a stuck valve / runaway sequence.
  - Built as (decided 2026-08-16): **notify-and-close only** (cycle not aborted); guard =
    every state EXCEPT `manual_override` (protects idle/winterized too, but stands down
    during hands-on override); `mode: parallel` (max 4). `for:` = **`min(helper, 120)` +1 min
    grace** (`int(120)` fallback), mirroring the same `min(helper, 120)` ceiling
    `run_zone_sequence` enforces (helper AND the absolute 120-min cap), so a normal
    full-runtime close never false-trips and a helper set >120 still trips at 121, not
    helper+1; only a true overrun (> capped runtime + grace) does.
  - Note: distinct from the runtime CAP already in `calculate_zone_runtime`
    (`zone_scripts.yaml`), which bounds the *planned* runtime; this watches *actual*
    valve-on duration.
  - **Code-review fixes (2026-08-16):** (1) closes the valve via a direct `switch.turn_off`
    on the triggering relay instead of `script.close_zone` — the script is `mode:single`
    and this backstop is `mode:parallel`, so two simultaneous overruns would have dropped
    the second `close_zone` and left a valve open. (2) The notify now quotes the ENFORCED
    cap `min(helper,120)`, not the raw helper. (3) Reciprocal "KEEP IN SYNC" comments pin
    the duplicated 120-min cap to `run_zone_sequence`. Separately, `binary_sensor.watering_operational`
    now excludes `unknown`/`unavailable` (fail-safe OFF) so the tank monitor can't latch on
    a startup-window garbage state.

- [x] ✅ `automation.safety_manual_override_handler` — **DONE (superseded by Phase 4).**
  Implemented — and extended — as `automation.watering_state_control_guard`
  (`watering_state/state_machine.yaml`, ADR-015 D-F): engage-from-idle parks in
  `manual_override`; engage-while-running REJECTS (reverts the boolean + "stop the cycle
  first" notify); engage-from-error engages + warns + audit-logs; exit -> idle. The same
  parametrized guard also covers `system_winterized`. The original spec's "pause state
  machine" = park in the `manual_override` state, which the dispatcher treats as terminal.
  No separate Phase 5 automation needed.

**File Location:** `home-assistant/packages/watering_safety/safety_automations.yaml`
(NOT `automations.yaml` — a bare `automations.yaml` basename collides under
`!include_dir_named`, per START_HERE Top Gotchas; the Phase 3.4 Part B automation already
lives in `safety_automations.yaml`, so the three new monitors join it there).

**Downstream note (Phase 9.9):** the safety -> notification integration in §9.9 is now
ALREADY satisfied for the error path — the `watering_state_on_error` table calls
`send_critical`/`send_high_notification` per tier and `emergency_stop` self-notifies.
Revisit §9.9 as "verify coverage," not "build from scratch."

**Test Plan:** See Phase 8.2 (Safety Interlock Testing) and `docs/test_scenarios.md`
Section 2 (the zone-runtime test already drops `max_single_zone_runtime_min` to 5 min).

**Entity References:** All entity IDs must use the full `watering_system_` prefix. See
`/docs/entity_reference.md` for the complete mapping. Key IDs (per monitor):
`binary_sensor.watering_system_low_low_water_level` (tank),
`switch.watering_system_relay_{1-7}_*` (comms availability proxy),
`switch.watering_system_relay_{2-5}_zone_{1-4}` (zone runtime). Note:
`sensor.watering_system_wifi_signal` is diagnostic only and is NOT a trigger input —
`comms_watchdog` keys off the relay-availability proxy, so don't wire the comms test to it.

**Build status (2026-08-16):** the three monitors are **written** in `safety_automations.yaml`
(YAML parse-validated locally, 4 automations total incl. the 3.4 Part B recovery). Next:
push → deploy to the Green → Dev-Tools test each (tank/comms/zone). NOTE: all three guards
stand down in `manual_override`, so DON'T test under the brake — drive each monitor in the
state its guard requires (operational for tank/comms; any non-override state for zone), with
valves/pump still unwired as the safety, then re-park. Then flip these to ✅ and add
test_scenarios.md §2 cases.

**Blocker Notes:** _None — all prerequisites (state machine, per-error table, notification
scripts, tank/relay/wifi entities) are built and deployed._

---

## Phase 6: Weather Integration

### 6.1 Brightsky/DWD Integration
- [x] ✅ Brightsky REST sensors configured — **verified in code** (`dwd_brightsky.yaml`)
- [x] ✅ `sensor.brightsky_rain_24h` (precipitation last 24h) — `unique_id: brightsky_rain_24h_total`
- [x] ✅ `sensor.brightsky_rain_72h` (precipitation last 72h) — `unique_id: brightsky_rain_72h_total`
- [x] ✅ Current weather conditions (temperature, humidity, pressure, etc.) — `brightsky_temperature_now`,
  `brightsky_humidity_now`, `brightsky_pressure_now`, `brightsky_dew_point_now`, `brightsky_cloud_cover_now`
- [x] ✅ Wind sensors (speed, gust, direction) — `brightsky_wind_speed_60_now`,
  `brightsky_wind_gust_60_now`, `brightsky_wind_direction_now` (+ `brightsky_wind_speed_knots`)
- [x] ✅ Binary sensors (raining_now, sunny_now) — `brightsky_raining_now_bool`, `brightsky_sunny_now_bool`
- [x] ✅ `sensor.brightsky_temp_high_yesterday` (max temp from previous day) — built 2026-08-05
- [x] ✅ `sensor.brightsky_temp_avg_high_3day` (average of daily highs for the 3
  preceding complete days: yesterday, -2, -3; today excluded) — built 2026-08-05

**File Location:** `home-assistant/packages/weather/dwd_brightsky.yaml` ✅ **EXISTS**

**Additional sensors available (not required for watering logic):**
- Dew point, cloud cover, sunshine minutes
- Wind speed in knots (converted from m/s)
- Weather URL generator template

**Blocker Notes:** _None - implementation complete._ **Note (2026-08-16):** the two long-poll REST
sensors (`temp_avg_high_3day`, `temp_high_yesterday`; `scan_interval` 1800 s) come up `unavailable`
after an HA restart until their first scheduled poll; a manual `update_entity` populates them
immediately (observed 32.7 °C). Low-priority: warm them on `homeassistant.start` (a START_HERE
Open follow-up).

---

### 6.2 Weather-Based Program Logic
> **REWORK — ADR-021 ACCEPTED 2026-08-25 (architecture §3.2, v1.9.0); implementation HELD for the
> moisture hardware.** The tree below is being replaced by a **moisture-primary** one (soil moisture
> drives intensity; weather/forecast modulate; de-lagged temp; capped/floored forecast-rain
> downgrade; weather-only fallback). Decision recording folds into ADR-018 (see §3.6). Test 4.24
> (test_scenarios) covers the new tree. The current tree stays deployed as ADR-021's fallback until
> then.
- [x] ✅ Integrate weather sensors into `script.state_window_check` — built (Phase 4, `state_scripts.yaml`)
- [x] ✅ Decision tree per zone (built + **validated live 2026-08-16**, Test 3.6.c / test_scenarios §5):
  - rain_72h > rain_off_mm → program = off
  - rain_24h > rain_light_mm → program = light
  - temp_avg_high_3day > temp_heavy_c AND rain_72h < rain_min_mm → program = heavy
  - temp_avg_high_3day > temp_normal_c → program = normal
  - else → program = light

**Status (2026-08-16):** ✅ **Built + validated.** The tree lives in `script.state_window_check`
(`watering_state/state_scripts.yaml`) and was swept on the Green with spring thresholds
(roff 20 / rlight 10 / rmin 5 / theavy 28 / tnormal 22): off / light / heavy / normal + all-off→idle
all PASS, the else-light branch (temp 18 < tnormal) swept 2026-08-16 (test_scenarios §5.2 Test C),
plus the D-A fallback (a Brightsky sensor `unavailable` → all zones `normal` + warning). All branches
of the tree are now exercised.

**Blocker Notes:** _Resolved — state machine (Phase 4) deployed and Test 3.6.c passed; temperature
sensors from 6.1 available since 2026-08-05._

---

## Phase 7: Dashboard UI

> **Standard implementation path (set 2026-08-18, ADR-019).** Phase 7 is executed through the
> seven-gate process below (**7.0–7.6**). Each gate has an **exit checklist** that must be
> satisfied — with user sign-off — before the next gate begins, plus a short note on *how* it
> will be accomplished. The original placeholder card list (created at project start) is
> **retained** as **§7.7 Feature / Content Inventory** — a good catalogue of what the finished
> UI must contain, now folded into the gates as content targets rather than as the process.
>
> **Design direction:** glassmorphism (blurred gradient background, light/airy translucent
> cards); **desktop** HA UI first, with mobile/iPad and a minimal Apple Watch surface as later
> tiers. **Storage:** repo YAML-mode dashboards (canonical, review-before-push), provisional per
> ADR-019. **Tooling set up 2026-08-18:** `frontend-design` + `ha-dashboard-design` skills;
> `hass-mcp` live HA access (**READ-ONLY** — no state/service/helper/config/code change without
> express per-action consent); in-app browser + HTML-Artifact mockups as the feedback loop.
> **Current position: Gate 7.0 COMPLETE (2026-08-20). Gate 7.1 LOCKED (2026-08-21) —
> all visual tokens fixed; both prior open items (pill text color, E-stop red strength)
> resolved.** Deliverable: `docs/ui_design.md` v0.3.0 §6; locked design canvas
> (`claude.ai/code/artifact/387b2a69-637f-4f75-8d58-7b33918b9365`). Next: Gate 7.2+.

### 7.0 Requirements & Inventory — ✅ COMPLETE (2026-08-20, user sign-off)
- [x] ✅ UI surfaces enumerated and prioritized (desktop first; mobile/iPad/Watch flagged as later tiers)
- [x] ✅ Per surface: the entities/helpers it **displays** vs. the ones it must let the user **edit** ("see vs. do" split)
- [x] ✅ Entity/helper IDs verified **live** (hass-mcp, read-only) against `entity_reference.md` — no ID drift (canonical `watering_system_*`, no `back_garden_` prefix)
- [x] ✅ Context / Constraints / Success Criteria written for the UI as a whole

**Deliverable:** `docs/ui_design.md` v0.1.0 (surfaces §2, see/do split §3, live inventory §4,
Manual Override logic §5, follow-ups §6). Live inventory found the ESP32 offline (expected — MPPT
enclosure rebuild) and several at-a-glance values with no HA entity yet (next/last watering, fert
history — in `watering_ops`, need template/DB-query sensors; `ui_design.md` §6 follow-up #2).

**How:** inventory the live system with read-only hass-mcp (`system_overview`, `list_entities`,
`get_entities_by_area`, `domain_summary_tool`), reconcile against `entity_reference.md`, and
capture the requirements here / in `docs/ui_design.md`.

---

### 7.1 Design Language → Tokens — ✅ LOCKED (2026-08-21, user sign-off)
- [x] ✅ Moodboards received from user and analyzed — plus **two ChatGPT design specs** adopted as source of truth (`ui_design.md` §6)
- [x] ✅ Tokens locked in `docs/ui_design.md` §6: glass recipe, palette, typography (**Hanken Grotesk**), radius, state colors, four-state status-pill table (brighter per-state text), rounded Emergency-Stop capsule, tile grid, Water-Usage meter gradient, icon set
- [x] ✅ Legibility rule stated (solid high-contrast over glass; big values carry a contrast shadow)
- [x] ✅ User sign-off on the token spec (2026-08-21). Organic-blob background deferred to its own session (`ui_design.md` §7).

**How:** run the `frontend-design` skill to commit to a distinctive direction (avoid templated
defaults / Inter); adapt the `ha-dashboard-design` glassmorphism recipe + a mature glass theme as
a base; record everything as versioned tokens in `docs/ui_design.md`.

---

### 7.2 Information Architecture
- [ ] 📋 Dashboard(s) + views defined; card inventory per view; navigation model
- [ ] 📋 Each card mapped to its entities and its interaction type (read / edit / action)
- [ ] 📋 Wireframe-level layout (structure only, no styling) reviewed and approved

**How:** map the §7.7 content inventory onto views as a wireframe (ASCII or a plain Artifact);
confirm entity coverage via read-only hass-mcp; get approval before any styling.

---

### 7.3 High-Fidelity Static Mockup
- [ ] 📋 One or two hero views built as a rendered **HTML Artifact** in the locked glass style
- [ ] 📋 Mockup conforms to the tokens; readability verified in light and dark
- [ ] 📋 **User approves the look before any HA YAML is written**

**How:** build the mockup as an Artifact (`artifact-design` skill) and iterate cheaply *outside*
HA — the primary design loop; it doubles as the spec ported in 7.4.

---

### 7.4 Build in Home Assistant (repo YAML)
- [ ] 📋 Curated HACS deps installed on the Green (card-mod + set), each documented as a dependency
- [ ] 📋 Existing storage dashboard **backed up** before the YAML-mode switch (conversion can wipe it)
- [ ] 📋 Dashboard authored as YAML-mode file(s) under `home-assistant/dashboards/`; theme added
- [ ] 📋 Reload-without-restart behavior **verified live**; SSH/Samba fast-sync path confirmed
- [ ] 📋 Rendered result reconciled against the 7.3 mockup via browser screenshots
- [ ] 📋 "Before You Code" checklist run; changes reversible; committed with approval

**How:** port the approved mockup to Lovelace YAML; fast-loop = author in repo → direct-sync to
the Green (bypassing the slow guarded repo-pull) → hard browser refresh → screenshot → reconcile
→ batch-commit. Read-only MCP only unless a specific change is expressly approved.

---

### 7.5 Responsive Tiers
- [ ] 📋 Desktop locked
- [ ] 📋 Tablet/phone adaptation, incl. the blur→flat performance fallback for older iPad / wall tablets
- [ ] 📋 Minimal Apple Watch surface scoped (HA actions/complications — a separate paradigm, not Lovelace)

**How:** verify at breakpoints in the browser; add a mobile theme variant; treat the Watch tier
as a small, separate task after the desktop/tablet tiers are solid.

---

### 7.6 Interaction & Hardening
- [ ] 📋 Helper editing works inline (Mushroom number/select, sliders, time/date pickers)
- [ ] 📋 Error / empty / `unavailable` states designed and handled (conditional / alert cards)
- [ ] 📋 Accessibility (contrast, keyboard focus, reduced-motion) + performance pass
- [ ] 📋 Final review; `entity_reference.md` + `test_scenarios.md` updated for the UI

**How:** exercise every control; add fault-state cards; run an a11y/perf audit; then update the
entity + test docs (UI test cases, verified IDs).

---

### 7.7 Feature / Content Inventory (original placeholder — retained as content targets)

> Created at project start as the first-pass card list. **Superseded as the *process* by gates
> 7.0–7.6**, but kept as a checklist of *what the finished UI must contain*. Items here get
> absorbed into the relevant gate.

**Main Control**
- [ ] 📋 Current system state (large, colored badge)
- [ ] 📋 Next scheduled watering (countdown timer)
- [ ] 📋 Emergency stop button (prominent, red)
- [ ] 📋 Manual override toggle

**Zone Status (per zone)**
- [ ] 📋 Current program (off/light/normal/heavy)
- [ ] 📋 Last watering timestamp
- [ ] 📋 Next fertigation due date
- [ ] 📋 Manual valve control (when in override mode)

**System Configuration**
- [ ] 📋 Zone sequencing mode dropdown
- [ ] 📋 Watering cycle period slider
- [ ] 📋 Window time pickers (morning/evening)
- [ ] 📋 Season selector

**Safety Status**
- [ ] 📋 Tank level indicators (Low, Low-Low) with colors
- [ ] 📋 ESP32 online status
- [ ] 📋 Last Modbus transaction timestamp
- [ ] 📋 Active alarms list

**Statistics / History**
- [ ] 📋 Pump runtime tracking (relay state duration)
- [ ] 📋 Watering cycle history (dates/durations per zone)
- [ ] 📋 Water usage estimate (flow rates × runtime)
- [ ] 📋 Energy consumption (from Victron)

**File Location (target):** `home-assistant/dashboards/` (YAML-mode; supersedes the earlier `ui-lovelace.yaml` note)

---

## Phase 8: Testing & Validation

### 8.1 State Machine Testing
- [ ] 📋 Execute tests from docs/test_scenarios.md sections 3.1-3.4 — **checked against
  test_scenarios.md: 3.1/3.2/3.3/3.4 are individually still 📋 READY TO RUN (not yet
  executed as discrete tests).** However, `Test 3.6` (Phase 4 full walkthrough) already
  exercises equivalent ground at the relay/logic level and is ✅ COMPLETE, ALL PASS
  (3.6.a–l, 2026-08-16) — cycle start, preflight abort, restart persistence (D-E), and
  the control guard (D-F) are all covered there. Running 3.1-3.4 as discrete tests is
  likely redundant with 3.6; leaving unchecked since they haven't been run as specified.
**Test Results:** _See test_scenarios.md for detailed pass/fail status_

---

### 8.2 Safety Interlock Testing
- [x] ✅ Test: Trigger Low-Low switch during watering (verify immediate stop) — **PASS**
  (test_scenarios.md Test 2.1, 2026-08-16)
- [x] ✅ Test: Disconnect ESP32 during watering (verify comms watchdog) — **PASS**
  (test_scenarios.md Test 2.2, 2026-08-16)
- [x] ✅ Test: Leave zone valve on beyond max runtime (verify auto-close) — **PASS**
  (test_scenarios.md Test 2.3, 2026-08-16)
- [ ] 📋 Test: Emergency stop from each state — **control logic PASS** (Test 2.5, R1
  simulated), but the physical hardware happy-path (relays actually de-energizing during
  a live operation) is ⏸️ BLOCKED per Test 2.4 until the ESP32 is back online — a
  commissioning dependency, not open dev work.

**Test Results:** See detailed test procedures in `docs/test_scenarios.md` Section 2 (Safety Interlock Tests)

**Note:** All test scenarios use corrected entity IDs with `watering_system_` prefix (updated 2025-01-14). Before testing, verify entity IDs in HA Developer Tools → States.

---

### 8.3 Zone Sequencing Testing
- [x] ✅ Test: Parallel mode - all zones with same runtime (should start/stop together) —
  **PASSED** (test_scenarios.md Test 4.4, 2025-10-22)
- [x] ✅ Test: Sequential mode - 4 zones (should run one at a time) — **PASSED**
  (test_scenarios.md Test 4.5, 2025-10-22)
- [x] ✅ Test: Mixed programs - some zones off, others light/normal/heavy — **PASSED**
  (test_scenarios.md Test 4.4 Test B: zone 1 skipped, zones 2/3/4 staggered close by
  program — light@1min, normal+heavy@2min)

**Test Results:** _Document in `docs/test_scenarios.md` (Test Status Legend: ✅/❌/🚧/⏸️/⏭️)_

---

### 8.4 Weather-Based Program Testing
- [x] ✅ Test: Heavy rain in last 72h → zones = off — **PASS** (test_scenarios.md Test 5.1,
  via Test 3.6.c weather-tree sweep, 2026-08-16)
- [x] ✅ Test: Light rain in last 24h → zones = light — **PASS** (test_scenarios.md Test 5.1,
  same sweep — the `rain_24h > rain_light_mm` branch)
- [x] ✅ Test: High temps + no rain → zones = heavy — **PASS** (test_scenarios.md Test 5.2,
  heavy branch swept 2026-08-16)
- [ ] 📋 Test: Manual program override (bypass weather logic) — **checked the code: no
  bypass exists.** `script.state_window_check` (`state_scripts.yaml:255-259`)
  unconditionally overwrites `input_select.zone_N_program` from the weather decision tree
  on every cycle; there is no "manual mode" gate that would let an operator-set value
  survive the next `window_check`. This looks like a stale test-plan item from before the
  Phase 4 decision-tree design was finalized (ADR-015) rather than an unbuilt feature —
  worth a decision on whether a real override toggle is wanted, or the test item should be
  dropped.

**Test Results:** _Document in `docs/test_scenarios.md` (Test Status Legend: ✅/❌/🚧/⏸️/⏭️)_

---

## Known Issues / Technical Debt

### Current Issues
_None yet - will populate as bugs are discovered_

### Deferred Improvements
1. Flow rate monitoring (Phase 4) - requires additional hardware
2. Energy optimization (Phase 4) - waits for battery SOC thresholds
3. Advanced fertigation (Phase 2) - split dosing, zone-specific ratios

---

# Implementation Roadmap Changes - Notification System

**Location 1:** Add new Phase 9 after "Phase 8: Testing & Validation"

---

## Phase 9: Notification System

### 9.1 Service Configuration
- [x] ✅ CallMeBot WhatsApp registration complete
  - Recipient Phone: stored in secrets.yaml as `!secret whatsapp_phone` (your German mobile)
  - API Key: stored in secrets.yaml as `!secret whatsapp_api_key`
  - Registration via +34 694 242 562 (not used in API calls)
- [x] ✅ Gmail SMTP/IMAP setup complete
  - Username: stored in secrets.yaml as `!secret gmail_username`
  - App password: stored in secrets.yaml as `!secret gmail_app_password`
  - Auto-forward to primary email configured
- [x] ✅ Add credentials to secrets.yaml (4 secrets total)
- [x] ✅ Test WhatsApp notification via curl/browser
- [x] ✅ Test Gmail SMTP via HA Developer Tools
- [x] ✅ Test Gmail IMAP inbox monitoring

**File Location:** `home-assistant/secrets.yaml` (credentials only, never committed)

**Blocker Notes:** _None - all services tested and operational_

**Completion Date:** 2025-10-13

---

### 9.2 Notification Helpers
- [x] ✅ `input_boolean.system_winterized` (winterization control)
- [x] ✅ `input_boolean.notification_system_error` (health status)
- [x] ✅ `input_boolean.monthly_test_whatsapp_confirmed` (test tracking)
- [x] ✅ `input_boolean.dewinter_test_whatsapp_confirmed` (test tracking)
- [x] ✅ `input_boolean.dewinter_test_email_confirmed` (test tracking)
- [x] ✅ Template sensors:
  - `sensor.last_email_test_time`
  - `sensor.last_monthly_test_time`
  - `sensor.last_notification_error`

**File Location:** `home-assistant/packages/notification/helpers.yaml` ✅ **EXISTS**

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

---

### 9.3 REST Commands
- [x] ✅ `rest_command.send_whatsapp_notification` (CallMeBot integration)
- [x] ✅ `notify.gmail_smtp` (email sending via Gmail)
- [x] ✅ IMAP email integration (inbox monitoring for daily test)

**File Location:** `home-assistant/packages/notification/config.yaml` ✅ **EXISTS**

**Test Plan:**
- Test WhatsApp: Send "Test message" and verify receipt ✅ PASSED
- Test Email: Send test email and verify receipt + forwarding ✅ PASSED
- Test IMAP: Send email and verify HA detects arrival ✅ PASSED

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

---

### 9.4 Notification Scripts
- [x] ✅ `script.send_critical_notification` (WhatsApp + Email)
- [x] ✅ `script.send_high_notification` (WhatsApp + Email)
- [x] ✅ `script.send_standard_notification` (WhatsApp only)
- [x] ✅ `script.send_watering_summary` (compiles cycle data, calls standard notification)
  — **built 2026-08-18 with §9.10** (this line was ticked in error before the
  cycle path existed; the other three tier scripts were the actual 2025-10-13 work)

**File Location:** `home-assistant/packages/notification/scripts.yaml` ✅ **EXISTS**

**Test Plan:**
- Manually trigger each script type via Developer Tools ✅ PASSED
- Verify message formatting and delivery ✅ PASSED
- Test error handling (simulate API failure) ✅ PASSED

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

---

### 9.5 Daily Email Test Automation
- [x] ✅ `automation.daily_email_test_send` (19:00 daily, sends self-test email)
- [x] ✅ `automation.daily_email_test_monitor` (monitors inbox, 5-minute timeout)
- [x] ✅ `automation.daily_email_test_failure` (sets notification_system_error, sends WhatsApp alert)
- [x] ✅ Integration with preflight_check (blocks watering if error = ON)

**File Location:** `home-assistant/packages/notification/tests.yaml` ✅ **EXISTS**

**Test Plan:**
- Manually trigger daily test ✅ PASSED
- Verify email sent and detected by IMAP ✅ PASSED
- Simulate failure (disconnect internet) and verify error state set ✅ PASSED
- Verify preflight_check blocks watering when error = ON ✅ PASSED

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

**Testing Notes:** Time-based delays (5-minute timeout) verified via code review and functional testing.

---

### 9.6 Monthly WhatsApp Test Automation
- [x] ✅ `automation.monthly_whatsapp_test` (1st at 19:00, sends test message)
- [x] ✅ `automation.monthly_whatsapp_test_reminder` (12h before deadline, if unconfirmed)
- [x] ✅ `automation.monthly_whatsapp_test_failure` (24h after test, if unconfirmed → CRITICAL email)
- [x] ✅ `automation.monthly_test_reset` (resets confirmation boolean after successful test)

**File Location:** `home-assistant/packages/notification/tests.yaml` ✅ **EXISTS**

**Test Plan:**
- Manually trigger monthly test ✅ PASSED
- Confirm via dashboard button ✅ PASSED
- Simulate failure (don't click button) and verify email alert after 24h ✅ PASSED (logic verified)
- Test reminder automation at 12h mark ✅ PASSED (logic verified)

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

**Testing Notes:** Time-based delays (12h reminder, 24h timeout) verified via code review. Actual time periods not tested due to time requirements.

---

### 9.7 De-winterization Test Automation
- [x] ✅ `automation.dewinterization_test_trigger` (triggers when system_winterized → OFF)
- [x] ✅ `automation.dewinterization_test_monitor` (checks confirmations after 24h)
- [x] ✅ `automation.dewinterization_test_failure` (sends CRITICAL if any channel unconfirmed)
- [x] ✅ `automation.dewinterization_test_success` (marks system ready, resets confirmation booleans)

**File Location:** `home-assistant/packages/notification/tests.yaml` ✅ **EXISTS**

**Test Plan:**
- Set system_winterized = ON, then OFF ✅ PASSED
- Verify both test messages sent ✅ PASSED
- Confirm both via dashboard buttons ✅ PASSED
- Simulate failure (confirm only one channel) and verify blocking behavior ✅ PASSED

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

**Testing Notes:** Time-based delays (24h timeout) verified via code review. Actual time period not tested due to time requirements.

---

### 9.8 Winterization Integration
- [x] ✅ Update all notification automations with condition: `system_winterized = OFF`
- [x] ✅ Update daily/monthly test automations to skip when winterized
- [x] ✅ Update watering automations with condition: `system_winterized = OFF`

**File Location:** Multiple files (notification/tests.yaml, notification/scripts.yaml)

**Test Plan:**
- Set system_winterized = ON ✅ PASSED
- Trigger various events (tank low, cycle complete) ✅ PASSED
- Verify no notifications sent ✅ PASSED
- Verify tests skip execution ✅ PASSED
- Set system_winterized = OFF ✅ PASSED
- Verify de-winterization test triggers ✅ PASSED

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

**Testing Notes:** Manual trigger testing requires `skip_condition: false` parameter to properly evaluate conditions.

---

### 9.9 Safety Integration
- [ ] ⏸️ Update `automation.safety_tank_low_low` to call `script.send_critical_notification`
- [ ] ⏸️ Update `automation.safety_comms_watchdog` to call `script.send_critical_notification`
- [ ] ⏸️ Update `automation.safety_zone_runtime_limit` to call `script.send_high_notification`
- [ ] ⏸️ Update `script.emergency_stop` to call `script.send_critical_notification`
- [ ] ⏸️ Add notification to preflight_check failure (HIGH tier)

**File Location:** `home-assistant/packages/watering_safety.yaml` (modifications to existing automations)

**Test Plan:**
- Trigger each safety automation ⏸️ BLOCKED
- Verify correct notification tier sent ⏸️ BLOCKED
- Verify message content and formatting ⏸️ BLOCKED

**Blocker Notes:** _Requires safety automations to be implemented (Phase 5)_

**Completion Date:** _TBD - blocked on Phase 5_

---

### 9.10 Watering Summary Integration
- [x] ✅ Built `script.send_watering_summary` (was never actually created despite the
  §9.4 tick) + added the call near the end of `script.state_post_cycle_relief`
  (`watering_state/state_scripts.yaml`, after `finalize_cycle_record`, before the
  `idle` transition; `continue_on_error` so a notify hiccup can't strand the machine)
- [x] ✅ Template logic to compile cycle data — **from HA state, not a DB query.**
  post_cycle_relief is reached only on a clean completed cycle (≥1 zone; any error
  latches an `error_*` state that never reaches here), so HA state is authoritative:
  zones+programs from `input_select.zone_N_program` (≠`off`) named via
  `input_text.zone_N_friendly_name`; window/trigger from the `active_*` helpers.
  **Fertilizer + errors are intentionally omitted** (fert path unwired → no doses;
  errors can't occur on this path). Runtime is captured in `state_post_cycle_relief`
  from `binary_sensor.watering_cycle_active.last_changed` (ON since Event 1 = cycle
  start) **before** `finalize_cycle_record` fires Event 4 (which flips that sensor OFF).
- [x] ✅ Format summary message for WhatsApp — compact one-liner via the STANDARD
  tier (`send_standard_notification`, WhatsApp-only + winter-gated), e.g.
  `✅ Morning watering complete — Raspberries (normal), Blueberries (light) · 45 min`

**File Location:** `home-assistant/packages/notification/scripts.yaml` (new script)
+ `home-assistant/packages/watering_state/state_scripts.yaml` (call site)

**Design note (DB vs HA state):** 9.10 predates the operational DB, so a DB query was
considered. Rejected for the compact summary: the DB's `watering_cycles.start_time` is
written at the *same* Event 1 that flips `cycle_active` ON, so it offers no runtime
accuracy gain, and there is no HA→SQLite query path configured (no `sql` integration) —
adding one purely for a timestamp already available in HA state was not worth it. The
richer DB-sourced path (per-zone `actual_duration_sec` / `fertigated` from `zone_runs`,
composed in AppDaemon off the Event 4 it already consumes) remains a future upgrade if
authoritative per-zone durations or a fert dose summary are ever wanted.

**Test Plan:**
- Standalone: trigger `script.send_watering_summary` in Dev Tools (with/without
  `runtime_min`, various zone programs incl. all-normal and a single zone) — verify
  the multi-line body + graceful runtime omission ✅ **PASS 2026-08-18** (Dev-Tools
  send with `runtime_min: 45`, 4 zones — multi-line body rendered correctly on the
  phone: headline, one `• zone (program)` per line, `Runtime: 45 min`)
- Full cycle: run a dry-run cycle to `post_cycle_relief` and verify one summary lands
  after finalize, content accurate (zones, programs, window, runtime) ✅ **PASS
  2026-08-18** (manual-button cycle, parallel, zones shortened to 1 min — exactly ONE
  summary auto-fired; `Evening watering complete (manual)`; `Runtime: 2 min` matched
  wall-clock; this also confirmed `binary_sensor.watering_cycle_active` was recreated
  by `db_writer` at Event 1 so the runtime capture worked end-to-end; state returned
  to `idle`)
- Winter gate: `system_winterized` ON suppresses the summary (standard tier) — covered
  by the shared `send_standard_notification` winter gate (Test 9.6.1 PASS); not
  separately re-run this session.

**Blocker Notes:** _Code complete 2026-08-18; **live + dry-run VERIFIED 2026-08-18**
(relay-level, valves/pump unwired). §9.10 COMPLETE._

**Completion Date:** _Code 2026-08-18; verification TBD_

---

### 9.11 Dashboard UI
- [ ] 📋 Notification Status Card (system health, last test results, winterization status)
- [ ] 📋 Test Confirmation Card (monthly/de-winterization confirmation buttons with countdown)
- [ ] 📋 Manual Test Triggers (for debugging)
- [ ] 📋 Notification History (recent notifications log)

**File Location:** `home-assistant/ui-lovelace.yaml` or dashboard config

**Blocker Notes:** _Can be built in parallel - dashboard configuration separate from automation logic_

**Completion Date:** _TBD - planned for Phase 7 (Dashboard UI)_

---

## Phase 10: Notification System Testing

### 10.1 Service Integration Tests
- [x] ✅ Test: Send WhatsApp notification via REST command
- [x] ✅ Test: Send Email via SMTP
- [x] ✅ Test: IMAP detects incoming email within 5 min
- [x] ✅ Test: Simulate API failure (invalid credentials) and verify error handling

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.1 for details.

---

### 10.2 Daily Email Test
- [x] ✅ Test: Daily test sends email at 19:00
- [x] ✅ Test: IMAP detects self-sent email successfully
- [x] ✅ Test: Simulate email failure (disconnect internet)
  - Expected: `notification_system_error = ON` ✅ PASSED
  - Expected: WhatsApp alert sent ✅ PASSED
- [x] ✅ Test: Preflight check blocks watering when error = ON

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.2 for details.

**Testing Notes:** Time-based delays verified via code review and functional testing.

---

### 10.3 Monthly WhatsApp Test
- [x] ✅ Test: Monthly test sends WhatsApp on 1st at 19:00
- [x] ✅ Test: User confirms via button → test passes
- [x] ✅ Test: User doesn't confirm → CRITICAL email after 24h (logic verified)
- [x] ✅ Test: Reminder sent at 12h mark if unconfirmed (logic verified)
- [x] ✅ Test: Test skips when system_winterized = ON

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.3 for details.

**Testing Notes:** Time-based delays (12h, 24h) verified via code review. Actual time periods not tested due to time requirements.

---

### 10.4 De-winterization Test
- [x] ✅ Test: Set system_winterized = ON → OFF
  - Expected: Both channels send test immediately ✅ PASSED
- [x] ✅ Test: Confirm both channels → system ready
- [x] ✅ Test: Confirm only one → system remains blocked
- [x] ✅ Test: No confirmation → CRITICAL alert after 24h (logic verified)

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.4 for details.

**Testing Notes:** Time-based delays (24h timeout) verified via code review. Actual time period not tested due to time requirements.

---

### 10.5 Winterization Behavior
- [x] ✅ Test: Set system_winterized = ON
  - Trigger tank low alarm → no notification sent ✅ PASSED
  - Trigger cycle completion → no notification sent ✅ PASSED
  - Daily test skips execution ✅ PASSED
  - Monthly test skips execution ✅ PASSED
- [x] ✅ Test: Set system_winterized = OFF
  - De-winterization test triggers immediately ✅ PASSED
  - Normal notifications resume after test confirmed ✅ PASSED

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.6 for details.

**Testing Notes:** Manual trigger testing requires `skip_condition: false` parameter to properly evaluate conditions.

---

### 10.6 Notification Tier Validation
- [x] ✅ Test: CRITICAL tier sends via WhatsApp + Email
- [x] ✅ Test: HIGH tier sends via WhatsApp + Email
- [x] ✅ Test: STANDARD tier sends via WhatsApp only
- [x] ✅ Test: Message formatting correct for each tier

**Test Results:** All tests PASSED (2025-10-13). See test_scenarios.md Section 9.5 for details.

---

### 10.7 Integration Testing
- [ ] ⏸️ Test: Safety automations trigger correct notifications
- [ ] ⏸️ Test: Watering summary sent after cycle completion
- [ ] ⏸️ Test: Preflight check blocks watering when notification error active

**Test Results:** BLOCKED - requires watering system automations (Phases 4-5)

**Blocker Notes:** Integration tests require state machine, safety automations, and preflight_check script to be implemented.

---

## Phase 9 & 10 Summary

**Phase 9 (Notification System):**
- **Status:** ✅ 89% Complete (8/9 sections complete, 2 sections blocked)
- **Completion Date:** 2025-10-13
- **Files Created:**
  - `notification_helpers.yaml` (5 booleans, 3 template sensors, 3 datetimes, 2 text inputs)
  - `notification_config.yaml` (REST command, SMTP config, IMAP notes)
  - `notification_scripts.yaml` (3 tiered notification scripts)
  - `notification_tests.yaml` (11 test automations)
- **Blocked Items:**
  - 9.9 Safety Integration (requires Phase 5 safety automations)
  - 9.10 Watering Summary Integration (requires Phase 4 state machine)
  - 9.11 Dashboard UI (planned for Phase 7)

**Phase 10 (Notification Testing):**
- **Status:** ✅ 86% Complete (24/27 tests passed, 3 tests blocked)
- **Test Date:** 2025-10-13
- **Key Findings:**
  - Manual trigger testing requires `skip_condition: false` parameter
  - Dual-channel approach provides robust redundancy
  - Daily self-test successfully detects email failures within 5 minutes
  - Time-based delays (12h, 24h) verified via code review only

**Next Steps:**
- Complete Phases 2-5 (watering system core functionality)
- Return to Phase 9 sections 9.9-9.10 after state machine complete
- Run integration tests (10.7) after safety automations complete

---

## Change Log Addition

**Add to end of Change Log in impl_roadmap.md:**



---

## Known Issues / Technical Debt

### Current Issues
**1. Entity ID Documentation Error (Resolved 2025-01-14)**
- **Issue:** Documentation was using ESPHome `id:` field values instead of actual HA entity IDs derived from `name:` field
- **Impact:** Automation examples would fail with "entity not found" errors
- **Resolution:** All affected docs updated (architecture.md, test_scenarios.md, programming-notes.md, impl_roadmap.md)
- **Reference:** See `/docs/entity_reference.md` for canonical entity ID mapping
- **Pattern:** All ESPHome entities prefixed with `watering_system_`
- **Example:** `switch.relay_pump_main` → `switch.watering_system_relay_1_main_pump`

### Deferred Improvements
1. Flow rate monitoring (Phase 4) - requires additional hardware
2. Energy optimization (Phase 4) - waits for battery SOC thresholds
3. Advanced fertigation (Phase 2) - split dosing, zone-specific ratios
4. SMS notifications (deferred) - Sipgate requires business registration; Twilio costs €0.75/month; WhatsApp + Email dual-channel deemed sufficient for safety-critical alerts

---

## Change Log

- **2025-10-04:** Initial roadmap created based on architecture.md v1.0
- **2025-10-09:** 
  - Added Phase 9: Notification System (WhatsApp + Email dual-channel)
  - Added Phase 10: Notification System Testing (6 test categories)
  - Service registration complete: CallMeBot WhatsApp, Gmail SMTP/IMAP
  - File structure: 4 new package files for notification system
  - Integration points: Safety automations, state machine, preflight checks
  - Winterization support: All notifications disabled when system powered down
  - Testing strategy: Daily email test, monthly WhatsApp test, de-winterization test
- **2025-10-13:**
  - Phase 9 (Notification System):
    - Sections 9.1-9.8 complete
    - Section 9.9 blocked (requires Phase 5 safety automations)
    - Section 9.10 blocked (requires Phase 4 state machine)
    - Section 9.11 planned for Phase 7 (Dashboard UI)
  - Phase 10 (Notification Testing):
    - 24 tests passed across 6 test categories
    - 3 integration tests blocked (requires Phases 4-5)
  - Files created: 4 new package files (notification_helpers.yaml, notification_config.yaml, notification_scripts.yaml, notification_tests.yaml).   status: ✅ Complete 
  - Key discovery: Manual automation triggers require `skip_condition: false` to properly evaluate conditions
  - Testing methodology: Time-based delays (12h, 24h) verified via code review only due to time requirements
- **2025-10-14:**
  - **Entity ID Documentation Corrections** (Critical Issue Resolved)
    - **Root Cause:** Documentation used ESPHome `id:` field values instead of actual HA entity IDs (derived from `name:` field)
    - **Discovery:** Identified during AI collaboration bootcamp Week 1
    - **Impact:** Safety-critical automations and test procedures contained non-existent entity IDs
    - **Files Updated:**
      - Created `/docs/entity_reference.md` - Canonical entity ID mapping (27 entities documented)
      - `architecture.md`: Sections 5.1A, 5.2, 5.3, 7.1, 7.2 (all safety automations and flow diagrams)
      - `test_scenarios.md`: Tests 1.3, 1.4, 2.1, 2.2, 2.3 + added reference table
      - `programming-notes.md`: Added Known Gotcha, updated "Before You Code" checklist
      - `impl_roadmap.md`: Section 1.2 relay mapping, Section 5.1 entity references, Known Issues
    - **Pattern Change:** All ESPHome entities must include `watering_system_` prefix
    - **Examples:**
      - `switch.relay_pump_main` → `switch.watering_system_relay_1_main_pump`
      - `binary_sensor.low_water_level` → `binary_sensor.watering_system_low_water_level`
      - `switch.raspberries_02` → `switch.watering_system_relay_2_zone_1`
    - **Prevention:** Added entity ID verification to "Before You Code" checklist
    - **Documentation:** All relay references now show both number (R1-R16) and full entity ID
- **2025-10-15**
  - Phase 2 (Helpers)
    - Phase 2.1-2.3 completed and verified
    - Added entity_reference.md to documentation files
- **2025-10-16:**
  - **Package Reorganization**: Implemented feature-based subfolder structure
    - **New structure**: 8 YAML files reorganized into subfolders by function
      - `notification/` - Dual-channel notification system (4 files)
      - `weather/` - External weather integration (1 file)
      - `watering_helpers/` - Configuration helpers (3 files)
    - **Planned structure**: Future files organized by functional area
      - `watering_scripts/` - All operational scripts (zone, pump, fert controls)
      - `watering_state/` - State machine and state transition logic
      - `watering_safety/` - Safety monitors and emergency procedures
      - `watering_sensors/` - Soil sensor management (Phase 3)
      - `watering_ui/` - Dashboard configuration (Phase 7)
    - **File structure table**: Complete rewrite with subfolder organization
    - **Phase 3-5 updates**: All file locations updated to new paths
    - **Verification**: GitHub Actions sanitization → public repo → HA pull script
    - **Entity IDs**: No changes (file moves only, all 218+ entities unchanged)
    - **Migration**: Completed successfully, all entities verified operational
    - **Note**: repo_pull.yaml intentionally excluded (not tracked in GitHub)
- **2025-10-22:**
  - **Phase 3.1** is completed inclusive testing.
- **2025-11-07:**
  - **Phase 3.2 Complete:** Pump Control Scripts - Design, Implementation, Review, and Testing
    - **Design Phase (2025-10-22):**
      - Defined 4 pump control scripts with comprehensive safety architecture
      - Established three-layer defense system: Safety automations (Phase 5), Script checks (Phase 3), State machine (Phase 4)
      - Designed self-healing patterns for pressure relief valve and pump stop
      - Defined 3-second relay verification standard (R10 2s + coil 1s)
      - Created dual logging strategy (system_log + cycle_event_log)
    - **Implementation Phase (2025-10-27):**
      - Implemented all 4 scripts: start_main_pump, stop_main_pump, open_pressure_relief, close_pressure_relief
      - Added Issue #8 fix: Pressure relief duration validation (30-300s bounds, 120s default)
      - Validated separator syntax consistency across all pump scripts
      - Implemented self-repair logic for both pressure relief and pump stop
    - **Adversarial Review Phase (2025-10-28):**
      - Conducted 8-pass code review (assume broken until proven otherwise)
      - Fixed Issue #9 (CRITICAL): Changed stop_main_pump to `mode: restart` (prevents safety automation blocking)
      - Fixed Issues #15-17: State verification pattern (use `not is_state()` for failure detection)
      - Fixed Issue #13: Removed redundant first retry logging (attempt_number > 0 check)
      - Verified all patterns against Home Assistant official documentation
    - **Testing Phase (2025-11-02 to 2025-11-07):**
      - Executed 19 test scenarios across 5 test suites
      - Results: 13/19 PASS (68%), 6 skipped due to UI timing limitations
      - Fixed YAML syntax error: Empty `then:` block in pressure relief self-repair
      - Fixed race condition: Added 500ms delay after subscript calls before verification
      - All critical safety paths validated (tank checks, valve interlocks, self-repair)
  - **Critical Lessons Documented:**
    - Pressure relief duration validation: Defense-in-depth for safety-critical parameters
    - Script mode for safety: Use `mode: restart` on scripts callable by safety automations
    - State verification pattern: Use `not is_state(entity, 'desired')` to catch unavailable states
    - YAML gotcha: Empty `then:` blocks cause silent failures
    - Race condition: 500ms delay needed after calling relay control subscripts
  - **ADR-010 Added:** Self-Healing Logic Patterns (consolidated across pressure relief + pump stop)
  - **Test Infrastructure:** Tank sensors (low/low-low) now controllable via R15/R16 for testing
- **2025-11-09:**
  - **Fertigation Pump Calibration Procedure Updated (v2.0 → v2.1):**
    - **Corrected volume-per-revolution:** 0.3 → 0.15 mL/rev
      - Calculation basis: 1mm ID tube, 3 rollers, ~58.6mm arc between rollers
      - Volume per rev: 3 × 0.785mm² × 58.6mm ≈ 138mm³ ≈ 0.15 mL/rev
    - **Revised calibration setpoints:**
      - Old: 2,4,8,12,16 mL/min @ 7,13,27,40,53 RPM
      - New: 2,4,6,10,15 mL/min @ 13,27,40,67,100 RPM
      - Rationale: Better distribution across operating range, avoids extrapolation beyond 100 RPM
    - **Established 100 RPM operational maximum:**
      - Tube longevity: ~2000 hours @ 100 RPM vs <500 hours @ 200 RPM
      - Flow accuracy: Better repeatability at moderate speeds
      - Safety margin: Well below driver capability (3000 RPM) but within practical peristaltic limits
    - **Added tubing break-in procedure:**
      - Pre-calibration requirement: 2-3 hours @ 30 RPM (water only)
      - Rest period: 30 minutes before calibration
      - Rationale: Silicone tubing stretches 5-10% during first hours of use
    - **Documented typical calibration coefficients:**
      - Slope: 0.13-0.17 mL/min per RPM (expected range)
      - Intercept: 0-0.5 mL/min (expected range)
      - R² requirement: ≥0.995 for acceptance
    - **Clarified command units:** RPM (rev/min) via Modbus register 0x0033, NOT percentage
    - **File updated:** `docs/fert_pump_cal_v2.md` (content revised to v2.1; replaces prior v2.0 content dated 2025-10-01)
    - **Related updates:**
      - `docs/fert_prog_design.md` Section 9: Calibration integration with dose calculation logic
      - `docs/impl_roadmap.md` Phase 1.3, 2.3, 3.3: Updated calibration references
      - `docs/programming-notes.md`: Change log entry added
  - **Rationale:** Original 0.3 mL/rev estimate based on incomplete tube geometry. Corrected calculation using actual tube cross-sectional area and pump head radius ensures accurate dose delivery. Conservative 100 RPM limit balances sufficient flow capacity (15 mL/min maximum) against tube wear and measurement accuracy. Expected calibration curve: ~0.15 mL per revolution × RPM matches theoretical calculation.
- **2025-11-11**
  - Alter 3.3 to account for new fert plan
- **2026-04-08:**
  - **ADR-011: Operational Database Architecture** — created and accepted
    - Two-layer architecture: MariaDB add-on (`watering_ops` database) +
      AppDaemon add-on as Python bridge
    - Schema: four tables (`watering_cycles`, `zone_runs`, `fertigation_doses`,
      `system_events`) — see `docs/ADR-011-operational-database.md`
  - **Phase 3.5: Operational Database Infrastructure** — added to roadmap
    - Positioned between Phase 3.4 (safety scripts) and Phase 4 (state machine)
    - HA event payload schemas must be defined before Phase 4 begins (contract
      between state machine and AppDaemon)
    - New file: `docs/db_schema.sql` — SQL schema under version control
    - New subfolder: `home-assistant/packages/watering_appdaemon/` (3 AppDaemon scripts)
    - Decision query sensors added as Phase 4 dependency:
      `sensor.zone_{1-4}_fert_delivered_14d_ml`, `binary_sensor.watering_cycle_active`
    - Seasonal CSV export to integrate with winterization automation (Phase 9)
- **2026-06-28:**
  - **Roadmap hygiene:**
    - Header **Last Updated** refreshed 2025-11-11 → 2026-06-28; **Status**
      refined to "Phase 3 — 3.3 Fertigation Scripts (active)".
    - Filename references reconciled to actual repo files:
      - `test-scenarios.md` → `test_scenarios.md` (File Ownership table)
      - `fert_pump_cal_v2.1.md` → `fert_pump_cal_v2.md` (Phase 1.3 procedure
        ref + 2025-11-09 change-log line). The calibration *content* is v2.1;
        the *file* is `fert_pump_cal_v2.md` — the ".1" was only ever a content
        version, never the filename.
  - **Not changed (noted for later):** the empty "Change Log Addition" scaffolding
    section left as-is.
- **2026-06-28 (Phase 3.5 — SQLite revision):**
  - Reworked Phase 3.5 from the MariaDB design to **SQLite + AppDaemon** per the ADR-011
    SQLite revision (`docs/programming-notes.md`). Updated the task list, File Locations,
    Architecture, Archive Strategy, Dependencies, Test Plan, Blocker Notes, and Status.
  - Marked schema (`docs/db_schema.sql`), bootstrap
    (`home-assistant/packages/watering_appdaemon/db_schema_init.py` + `apps.yaml`), and
    setup guide (`docs/db_setup_guide.md`) as authored; install/deploy on the HA Green pending.
  - Removed MariaDB references (add-on install, connection test, "MariaDB data" backup).
  - **Schema decisions:** `pump_id` set to logical pump number (1-3); `UNIQUE(cycle_id,
    zone_id)` on `zone_runs` deliberately deferred for flexibility (see §3.5 Schema Notes).
- **2026-06-30 (Phase 3.5 — schema deploy wiring + path fix):**
  - **Wired the schema copy into the pull workflow** (resolves the "schema cannot
    drift" follow-up). `pull_public_repo.sh` now deploys the AppDaemon `watering_db`
    app to `/homeassistant/appdaemon/apps/watering_db/`, copying `apps.yaml` +
    `db_schema_init.py` from the repo and `db_schema.sql` from the canonical
    `docs/db_schema.sql` on every pull. AppDaemon re-applies the (additive) schema on
    its next restart/reload.
  - **Moved the AppDaemon app out of `packages/`** (resolves the repo-path-vs-deploy-path
    follow-up). `home-assistant/packages/watering_appdaemon/` →
    `home-assistant/appdaemon/watering_db/`. Reason: `configuration.yaml` loads
    `packages/` via `!include_dir_named`, which would parse `apps.yaml` as an HA package
    and fail config validation. Files were still untracked, so no live system was affected.
  - **Publish whitelist:** added `home-assistant/appdaemon` and `docs/db_schema.sql` to
    `.github/sanitize.py` so both reach the public repo the pull script reads.
  - **Docs:** updated `apps.yaml` header, `db_setup_guide.md` Step 3 (now describes the
    automated deploy + restart-to-apply note), File Ownership rows, and START_HERE §4/§6.
  - **Resolved the `docs/test-results.md` follow-up:** that file was never created; the
    two Phase 8.3/8.4 "Test Results" pointers now redirect to `docs/test_scenarios.md`
    (which already has a populated Test Status Legend) instead of a planned doc.
  - **Verified the deploy wiring end-to-end on the HA Green:** ran `pull_public_repo.sh`,
    confirmed `apps.yaml` + `db_schema_init.py` + `db_schema.sql` landed at
    `/homeassistant/appdaemon/apps/watering_db/`, restarted AppDaemon, and confirmed via
    the SQLite Web add-on (`database: /homeassistant/watering_ops.db`) that all four
    tables exist (`fertigation_doses`, `system_events`, `watering_cycles`, `zone_runs`,
    plus the expected `sqlite_sequence` housekeeping table from the `AUTOINCREMENT`
    primary keys). Phase 3.5 infrastructure checklist items closed; remaining 3.5 work
    (write listeners, decision queries, CSV export) stays blocked on Phase 3.3/3.4/4 per
    Blocker Notes.
  - **Defined the HA event payload contract** (§3.5 checklist item, the Phase 4
    prerequisite). Full per-event field schemas for all five DB-write triggers are now in
    architecture.md §13.3.1 (bumped v1.5.1 -> v1.5.2). Key decisions: payload-carried UTC
    timestamps; `cycle_uuid`/`zrun_uuid` correlation held in an AppDaemon in-memory map (no
    schema columns added); dose events buffered until the parent `zone_runs` row exists;
    `fertigated` derived by AppDaemon. UUID generation mechanism deferred to Phase 4.
  - **Implemented the seasonal CSV export** (two §3.5 checklist items: the AppDaemon
    script + the winterization trigger). New `home-assistant/appdaemon/watering_db/db_export.py`
    (`DbSeasonalExport`) listens for `watering_seasonal_export` and writes year-filtered CSVs
    of all four tables to `/homeassistant/watering_exports/` (header-only when a year is
    empty), plus a `system_events` audit row; read-only and never raises. New HA package
    `home-assistant/packages/watering_db/db_automations.yaml` fires that event on
    `system_winterized` OFF -> ON (the OFF -> ON trigger did not previously exist; only the
    de-winterization OFF case did). Registered the app in the AppDaemon `apps.yaml`, and
    generalised the `pull_public_repo.sh` AppDaemon block to copy the whole app folder so new
    apps deploy without further pull-script edits. architecture.md §13.5 updated to match
    (still v1.5.2). Export logic tested locally against a temp DB built from `db_schema.sql`
    (`home-assistant/appdaemon/watering_db/tests/test_db_export.py` — year filtering,
    header-only-when-empty, audit row all pass); live AppDaemon/event-bus run still pending.
  - **Confirmed the DB is in HA backups** (§3.5 checklist item). Verified from backup
    metadata (`backup.json`): the `homeassistant` component is included and
    `exclude_database: false`, so `/homeassistant/watering_ops.db` (in the config dir) is
    captured. Automatic backups are encrypted (`protected: true`), which is why a direct
    `tar` peek fails; the metadata flag is authoritative. Off-box replication (NAS/cloud)
    remains a separate, open nice-to-have (tracked in programming-notes).
- **2026-08-03 (Phase 3.4 — comms-lost handling BUILT + `safe_shutdown` early-halt fixed):**
  - **Part A** implemented in `watering_scripts/pump_scripts.yaml` (`stop_main_pump`): comms-lost
    fail-fast guard after the settle delay — R1 `unavailable`/`unknown` → `error_comms_lost` +
    one `pump_comms_lost`/`error` row + `stop:error:true`, replacing the two misleading
    `critical`/`pump_runaway` rows.
  - **Part B** implemented as a NEW package `watering_safety/safety_automations.yaml`
    (`automation.watering_safety_r1_comms_recovery`). R1 back `on` → `emergency_stop`
    (design change from the original "re-run `stop_main_pump`, stay `error_comms_lost`"; whole
    relay set is suspect after a blind period, so full estop + critical notification +
    latched `error_e_stop`). R1 back `off` → `pump_comms_restored` info + clear to `idle`.
    Race-guarded (no `default`; OFF branch re-checks current state). Not big enough for an ADR;
    rationale captured in §3.4.
  - **`safe_shutdown` early-halt RESOLVED.** A Dev-Tools probe proved `continue_on_error` DOES catch a called
    script's `stop:error:true`, so `stop_main_pump` was never the halt point; the cause was
    `script.stop_dosing_pumps` not existing (3.3 skipped) → `ServiceNotFound`, which
    `continue_on_error` does not suppress. Fixed in `watering_safety_scripts.yaml` by guarding
    that call on the script entity existing and being available.
  - Verified the ESP32 on-device 120-min auto-off (`relay_1_on_sequence`,
    `esphome/packages/modbus_rs485.yaml`) is the comms-independent hardware backstop that makes
    the fail-fast safe. `entity_reference.md` updated: `pump_comms_lost`/`pump_comms_restored`
    now **emitted** (dropped the "not yet emitted" note). `event_type` is free `TEXT` (only
    `severity` is CHECK-constrained), so the new types persist without a schema change.
  - Still open (Phase 3.4 "generalize"): `open_pressure_relief` calls `stop_main_pump` without
    `continue_on_error` (narrow mid-run R1-drop window); `safe_shutdown` lands on `idle` even
    after a mid-sequence `error_`; Part B OFF→idle doesn't confirm zones closed.
    _(The three concrete items above were then implemented the same day — see the generalize
    sub-items in §3.4.)_
  - **Live-verified on the Green (2026-08-03):** Part A, Part B (OFF + ON), and the
    `safe_shutdown` completion fix all PASSED (`system_events` rows 46–58). R1 transitions were
    simulated via Developer Tools → States because the ESP32 is offline (real WiFi loss); this
    validates the HA control logic. Hardware happy-path (relays physically de-energizing on
    `emergency_stop` / graceful `safe_shutdown`) stays PENDING until the ESP32 is back online.
    Phase 3.4 remains IN PROGRESS (that hardware validation + the deferred shared-recovery
    automation are the only open items).
- **2026-08-03 (Phase 3.4 — comms-lost handling documented, not yet built):**
  - Captured the agreed comms-lost **fail-fast + reactive-recovery** design as Phase 3.4
    deliverables in §3.4 (Part A guard in `stop_main_pump`, Part B recovery automation in
    `watering_safety/automations.yaml`, plus the generalization to the other safety
    scripts). Promoted from a loose START_HERE working note into this specced deliverable:
    §3.4 here is the canonical home; implementation deferred to land with the rest of the 3.4
    safety layer.
    Added matching Test Plan bullets. No HA config changed this session.
  - Reserved two new pump event_types in `entity_reference.md` — `pump_comms_lost`,
    `pump_comms_restored` — marked **planned (Phase 3.4)**, not yet emitted.
- **2026-08-05 (Phase 3.4 — "generalize" closed via recovery-trigger hardening):**
  - Closed the last open Phase 3.4 "generalize" design item (follow-up 5). The Part B
    recovery automation (`packages/watering_safety/safety_automations.yaml`) now arms on ANY
    of the seven wet-path relays (R1–R7) returning from `unavailable`/`unknown`, then reads
    R1's **live** state to decide (estop if `on`; `close_all_zones`→`idle` if `off`;
    no-default if still unreadable). Rationale: all seven share one ESP32/WiFi link, so comms
    loss is device-level and a reconnect restores them together — arming on the whole set
    makes recovery independent of which relay's state-change event lands first, while the
    decision stays purely R1-based. `mode: restart`→`mode: single` so the up-to-seven
    near-simultaneous reconnect triggers can't cancel an in-flight `emergency_stop`. Audit
    messages now name the triggering relay (`{{ trigger.to_state.name }}`).
  - Recorded a design note in §3.4: the originally-specified per-relay shape (keyed off
    *which* relay is unavailable + `safety_comms_lost`/`safety_comms_restored` event_types)
    over-fits a failure mode the hardware can't produce (relays never go unavailable
    independently); the `safety_comms_*` split is now a **conditional** future task, only if
    the safety scripts ever fork into distinct comms-loss sources. Added a Dev-Tools test
    bullet for the broadened trigger (non-R1 relay drives recovery). YAML validated; live
    Dev-Tools run pending (bundle with the other comms-lost sims). No hardware needed.
- **2026-08-05 (Phase 4 prep — state-machine doc reconciliation):**
  - Cross-checked the state machine against the runtime entity
    `input_select.watering_system_state` (config_helpers.yaml = canonical **15 states**)
    before starting Phase 4. Design docs had lagged at 11/12.
  - Fixed §Phase 2 checklist "11 states" → 15 (with an ADR-002-addendum pointer), and the
    §4.1 `state_preflight_check` tank line (the non-existent "GPIO35 = Low switch" → the
    **two-tier gate**: plain watering = Low-Low/GPIO32, fertigation = Low/GPIO33, so a
    dose is never aborted without its flush).
  - Companion edits: architecture.md §2.1/§2.2 (state list + missing transitions +
    two-tier preflight + `winterization_mode`→`system_winterized`), v1.5.2→v1.5.5;
    ADR-002 addendum + fert_prog_design.md entity-name fix. No code changes.
- **2026-08-05 (Phase 4 design — control structure decided, ADR-015):**
  - Locked D1–D4 for the plain-watering state machine and rewrote §4.1/§4.2 to the
    decided shape: dispatcher + self-advancing scripts + separate scheduler (D4);
    `active_watering_window`/`active_trigger_type` context helpers (D2); Event 3 fired
    inside `run_zone_sequence` with parallel-safe local per-zone `zrun_uuid` (D1);
    reporting-only `finalize_cycle_record` for Event 4, never on the safety path (D3).
  - `run_zone_sequence` (Phase 3.1) is slated for reporting-only additions (per-zone
    uuid + Event 3). architecture.md §13.3.1 clarified for the parallel plain-watering
    `zrun_uuid`; ADR-014 amended. Still design-only — no YAML written.
  - **Later same day (state walkthrough, D-A…D-H):** captured the edge-case decisions
    in the ADR-015 addendum and listed the resulting automations in §4.2 — five
    per-error entry automations (D-D) + a thorough HA-restart recovery (D-E), alongside
    the existing comms Part B. Enshrined the "cycle row always closes" invariant and
    the rule that operational `state_*` scripts don't `continue_on_error` around
    safety-critical subscripts. Design-only.
  - **Final capture pass same day:** added A1 (guard the state-advance) + A2
    (`abort_cycle_scripts`) to §4.1/§4.2; revised D-F to the guard model (two
    control-state guard automations, no auto-abort); added the manual-trigger button,
    Event 1 `temp_high_c` = `temp_high_yesterday`, and error notifications in the
    per-error automations. Superseded architecture.md §5.3 snippets (v1.5.6). Phase 4
    design is now decision-complete; still no YAML written.
- **2026-08-09 (Phase 4 BUILT — Steps 1-5, plain-watering path):**
  - **Step 1 — helpers** (`watering_helpers/config_helpers.yaml`): added
    `input_text.cycle_uuid` / `zone_run_uuid`, `input_select.active_watering_window` /
    `active_trigger_type`, `input_button.start_watering_cycle_now` (12->17 helpers).
  - **Step 2 — shared scripts** (new `watering_state/state_scripts.yaml`):
    `finalize_cycle_record` (D3: Event 4 + clear uuid, no-op when no open cycle,
    never touches hardware/state) and `abort_cycle_scripts` (A2: turn_off the named
    `state_*` progression set only).
  - **Step 3 — `run_zone_sequence`** (`watering_scripts/zone_scripts.yaml`):
    reporting-only additions (145 insertions, 0 logic deletions) — local per-zone
    `zrun_uuid` `z-<us>-<zone_id>` + Event 3 `watering_zone_run_complete` at each zone
    close, in both parallel and sequential branches.
  - **Step 4 — state scripts** (`state_scripts.yaml`): `state_window_check` (§6.2 tree
    + D-A weather fallback + all-off->idle), `state_preflight_check` (Low-Low/D-G/control
    gates, mint `cycle_uuid`, Event 1, D-B plain-always), `state_watering_plain`
    (R6/R7 interlock -> pump -> `run_zone_sequence` -> stop; **12 s** valve-travel delays),
    `state_post_cycle_relief` (relief -> R10 off -> `finalize('completed')` -> idle). Every
    script obeys A1 (guard-the-advance) + no `continue_on_error` around safety subscripts.
  - **Step 5 — automations** (new `watering_state/state_machine.yaml`): dispatcher
    (queued), scheduler, 5 per-error entries (abort -> [safe_shutdown for
    tank/valve/relay] -> finalize('error') -> notify; e_stop/comms = finalize-only,
    e_stop no notify), restart recovery (D-E), 2 D-F control guards. Plus retargeted the
    seasonal export to the `winterized` **state** (`watering_db/db_automations.yaml`,
    D-F watch-item) so a rejected winterization can't fire a spurious export.
  - **Build-time decisions (all revisable; recorded in ADR-015 change-log):**
    finalize/abort co-located in state_scripts.yaml; `error_*`->override/winterize =
    engage-with-warning; notify tiers critical(tank/valve/relay)/high(comms)/none(e_stop);
    valve physical-travel delay **12 s** (datasheet 6-10 s) where a step depends on valve
    position. Test plan added as test_scenarios.md **Test 3.6**.
  - **Status:** committed to main, NOT pushed — pending adversarial code review, then
    deploy + Test 3.6. Fert states, live-hardware validation, and the AppDaemon
    write-listeners for Events 1/3/4 remain deferred.
- **2026-08-16 (Phase 3.5 — Events 1/3/4 write-listeners BUILT):**
  - New AppDaemon app `home-assistant/appdaemon/watering_db/db_writer.py` (`DbWriter`),
    registered in `apps.yaml`, listening for `watering_preflight_complete` (E1),
    `watering_zone_run_complete` (E3), `watering_cycle_complete` (E4). E1 INSERTs an
    open `watering_cycles` row (`end_time`/`outcome` NULL); E3 resolves `cycle_id` from
    the in-memory `cycle_uuid` map, computes `actual_duration_sec` (end−start), derives
    `fertigated` from the dose buffer, INSERTs `zone_runs`; E4 UPDATEs the cycle's
    `end_time`/`outcome`/`notes` and drops the cycle's in-memory correlation. Publishes
    `binary_sensor.watering_cycle_active` via `set_state` (ON@E1/OFF@E4 — the publisher
    that unblocks the sensor's promotion to live). Fire-and-forget: every handler
    validates (controlled-vocab + required fields), never raises; bad payloads and
    unresolved `cycle_uuid`/`zrun_uuid` (e.g. AppDaemon restart mid-cycle) get a
    `system_events` breadcrumb (`event_rejected` / `event_unresolved`) and are skipped.
    Every connection sets `PRAGMA foreign_keys = ON`.
  - **Event 2 deferred** (`watering_fert_dose_complete` -> `fertigation_doses`): no
    publisher (fert hardware unwired). The in-memory dose-buffer scaffold is present so
    E3's `fertigated` derivation is already contract-correct (empty buffer -> 0); the E2
    listener + INSERT flush are added together when the fert path is wired.
  - Logic test `tests/test_db_writer.py` (stdlib, not deployed) — happy path,
    duration/FK/`fertigated` derivation, cycle-active ON/OFF, correlation cleanup,
    orphan-drop, and reject paths: **ALL PASS** locally (Python 3.13).
  - Deploys automatically via `pull_public_repo.sh` (copies every top-level app file);
    no pull-script edit. **Live DB-write verification on the Green pending** the next
    deploy + AppDaemon restart. NOT yet committed/pushed at time of writing.
- **2026-08-16 (Phase 3.5 — write path VERIFIED LIVE + export live run):**
  - `db_writer.py` committed (`aec7a7c`), deployed, and **verified live on the HA Green**. A
    parallel manual cycle (zone runtimes temporarily 1 min) wrote one `watering_cycles` row
    (opened at preflight, closed `completed` at post-cycle relief) + four `zone_runs` FK'd to it
    with computed `actual_duration_sec`, and `binary_sensor.watering_cycle_active` toggled
    `unknown→on→off` — **Test 10.6 PASS**. Deterministic Dev-Tools events confirmed graceful
    degradation: unknown `cycle_uuid` → `event_unresolved` (no orphan row), bad payloads → `event_rejected`
    on both Event 3 and Event 4 — **Tests 10.7 + 10.9 PASS**.
  - **Seasonal CSV export exercised live with real data** (follow-up #2): `watering_seasonal_export
    {year:2026}` produced `cycles=1/zone_runs=4/doses=0/events=171` and four correct CSVs — **Test
    10.4 PASS**. Corrected a stale note: `db_export` had actually been deployed since ≤2026-08-15
    (prior header-only exports), so the "not yet deployed" caveat was wrong.
  - Promoted `binary_sensor.watering_cycle_active` Planned → **live** in `entity_reference.md`
    (publisher = `db_writer`, verified). START_HERE follow-ups #1/#2/#3 closed + renumbered.
  - Remaining Phase 3.5: decision-query sensors (query app) + Event 2 fert-dose writer (RS-485 hardware).
- **2026-08-16 (Phase 6.2 — weather-based program logic VALIDATED LIVE):**
  - The per-zone weather decision tree in `script.state_window_check`
    (`watering_state/state_scripts.yaml`) was swept on the Green (Test 3.6.c / test_scenarios §5)
    with spring thresholds (roff 20 / rlight 10 / rmin 5 / theavy 28 / tnormal 22): **off / light /
    heavy / normal + all-off→idle all PASS**, plus the D-A fallback (Brightsky sensor `unavailable`
    → all zones `normal` + warning). Method: Brightsky sensors overridden in Dev Tools; state set →
    `window_check` under a `manual_override` brake so runnable programs abort at preflight → idle (no
    cycle launched). **Phase 6.2 marked Built + validated — all tree branches exercised** (the
    temp-below-normal else-light branch swept 2026-08-16, temp 18 → light; test_scenarios §5.2 Test C).
    Also noted a low-priority reliability item: the two long-poll REST
    temp sensors come up `unavailable` after an HA restart until their first poll (START_HERE
    follow-up #6). Docs only (test_scenarios.md §5, impl_roadmap §6.1/§6.2).
- **2026-08-16 (Phase 5 — Safety Interlocks reconciled against built Phases 3.4/4):**
  - Rewrote §5.1 to reflect that the phase was specified before the comms-lost handling
    (3.4) and the state machine + per-error table (4) existed.
    `safety_manual_override_handler` marked ✅ DONE — superseded by
    `automation.watering_state_control_guard` (`watering_state/state_machine.yaml`,
    ADR-015 D-F), a strict superset (also covers `system_winterized`).
  - The three remaining monitors (`safety_tank_low_low`, `safety_comms_watchdog`,
    `safety_zone_runtime_limit`) stay 📋 but are **re-scoped to a bare state transition**:
    entry to each `error_*` state now triggers the Phase 4 `watering_state_on_error` table
    (abort -> safe_shutdown -> finalize -> tiered notify), so the monitors no longer carry
    safing/notify themselves. Recorded the specific gap each fills (mid-cycle Low-Low,
    mid-cycle ESP32 dropout, actual valve-on duration) and the open build decisions.
  - Corrected the File Location `automations.yaml` -> `safety_automations.yaml` (bare
    basename collides under `!include_dir_named`); the new monitors join the existing 3.4
    Part B automation there. Noted §9.9 safety -> notify integration is already satisfied
    for the error path. Header refreshed (Last Updated -> 2026-08-16; Status -> Phase 5
    active). **Doc only — no YAML changed.**
- **2026-08-16 (Phase 5 — three safety monitors BUILT):**
  - Added `watering_safety_tank_low_low`, `watering_safety_comms_watchdog`, and
    `watering_safety_zone_runtime_limit` to `watering_safety/safety_automations.yaml`
    (now 4 automations incl. the 3.4 Part B recovery; YAML parse-validated locally).
  - **tank_low_low:** Low-Low -> ON while operational (complement guard) -> set
    `error_tank_low`; the Phase 4 `watering_state_on_error` table does safe_shutdown +
    finalize + CRITICAL notify. Fills the mid-cycle gap preflight cannot (it samples
    Low-Low only at cycle start).
  - **comms_watchdog:** any R1-R7 relay `unavailable`/`unknown` for 10 s while operational
    -> set `error_comms_lost` (on_error HIGH notify; Part B recovers on reconnect). Uses
    the relay-availability proxy Part B already keys off (one source of truth), not the
    WiFi sensor. `mode: single` collapses the near-simultaneous multi-relay triggers.
  - **zone_runtime_limit:** zone valve R2-R5 ON longer than
    **`min(max_single_zone_runtime_min, 120)` +1 min grace** (templated `for:`,
    `int(120)` fallback) -> `close_zone` that zone + HIGH notify; cycle not aborted.
    Guard = every state except `manual_override`. The `for:` mirrors the same
    `min(helper, 120)` ceiling `run_zone_sequence` enforces, so the grace keeps a normal
    full-runtime close (which holds for exactly the capped runtime) from racing the backstop
    into a false alarm, and a helper set >120 still trips at 121 min rather than helper+1.
    Distinct from the planned-runtime cap in `calculate_zone_runtime`.
  - All three only LATCH a state (or, for zone, close one valve + notify) — the Phase 4
    error machinery owns the teardown. **Not yet pushed/deployed/tested** — next is deploy
    to the Green + a Dev-Tools sweep (each monitor driven in the state its guard requires — the
    three stand down in `manual_override`, so the usual brake can't be used here), then ✅ + §2 tests.
- **2026-08-16 (Phase 5.1 — Dev-Tools sweep COMPLETE, all PASS; Phase 5 ✅ DONE):** ran
  test_scenarios.md §2 Tests 2.6 (operational predicate truth table + fail-safe on
  `unknown`/`unavailable`), 2.1 (tank low-low latches `error_tank_low` while operational, stands
  down idle/`manual_override`), 2.2 (comms watchdog latches `error_comms_lost` after the 10 s
  `for:` while operational, stands down idle, restart-safety guard confirmed), and 2.3 (zone
  runtime backstop — single-zone force-close, the two-simultaneous-zone regression for the
  `mode:parallel`/`close_zone` fix, a normal close clear of the +1 min grace, stand-down in
  `manual_override`, and the enforced-cap-in-notify regression) on the Green. All boxes PASS,
  no follow-up defects. §5.1 flipped to ✅ COMPLETE; Phase 5 done. System re-parked in
  `manual_override` (SOP) after the sweep.

- **2026-08-18 (Checkbox reconciliation — Phases 4, 6.1, 8):** the roadmap's own checkboxes
  had drifted behind the narrative status blocks (Phase 4/6.1/8 items were still shown
  unchecked despite being built/tested). Went through each unchecked box, confirmed against
  either the test record (test_scenarios.md) or the deployed code directly, and ticked what's
  actually done:
  - **Phase 4** (§4.1/§4.2): all state-transition scripts, helpers, and automations checked
    off, verified present in `state_scripts.yaml` / `state_machine.yaml` / `zone_scripts.yaml`
    and covered by Test 3.6 (ALL PASS). Left unchecked: the 3 fert-path state scripts
    (`state_fert_prep`/`_dose_phase1`/`_dose_phase2`) — confirmed absent from code, blocked on
    RS-485 hardware. Noted where the code review consolidated the originally-planned 5
    per-error automations into 1 table-driven `watering_state_on_error`, and the 2 D-F guards
    into 1 parametrized `watering_state_control_guard` — behavior unchanged, just reshaped.
  - **Phase 6.1**: all 8 Brightsky sensor checkboxes verified present in `dwd_brightsky.yaml`
    and checked off.
  - **Phase 8**: checked off items backed by an actual test PASS (8.2's tank/comms/runtime
    tests -> Tests 2.1/2.2/2.3; 8.3's parallel/sequential/mixed-program tests -> Tests
    4.4/4.5; 8.4's rain-off/rain-light/temp-heavy tests -> Tests 5.1/5.2). Left unchecked:
    8.1 (test_scenarios.md 3.1-3.4 are still individually un-run, even though the broader
    Test 3.6 walkthrough already PASSED equivalent ground); 8.2's hardware e-stop happy-path
    (blocked on ESP32 being physically online — commissioning); 8.4's "manual program
    override" test — checked the code (`state_scripts.yaml:255-259`) and found no override
    bypass exists (`state_window_check` unconditionally overwrites `zone_N_program` from the
    weather tree every cycle), so this reads as a stale pre-ADR-015 test-plan item rather
    than an unbuilt feature; flagged for a decision rather than silently dropped.
- **2026-08-18 (Phase 9.10 — end-of-cycle Watering Summary BUILT):** wired the missing
  end-of-cycle notification (START_HERE follow-up #5). **Finding:**
  `script.send_watering_summary` was marked ✅ in §9.4 but had never actually been
  created — only the three tier scripts existed. Built it in
  `notification/scripts.yaml`: compiles a compact one-liner from HA state (zones+programs
  from `zone_N_program`/`zone_N_friendly_name`, window/trigger from the `active_*` helpers)
  and hands off to `send_standard_notification` (WhatsApp-only + winter-gated). Fertilizer
  and errors are intentionally omitted (fert path unwired; the error path never reaches
  post_cycle_relief). Wired the call into `state_post_cycle_relief`
  (`watering_state/state_scripts.yaml`) after `finalize_cycle_record`, before the `idle`
  transition, `continue_on_error` so a notify failure can't strand the machine. Runtime is
  captured at the **top** of post_cycle_relief from
  `binary_sensor.watering_cycle_active.last_changed` (ON since Event 1 = cycle start),
  **before** finalize fires Event 4 and AppDaemon flips that sensor OFF — the race the
  ordering guards against. **DB query considered and rejected** for the compact summary: the
  DB's `start_time` is written at the same Event 1, so it gives no runtime accuracy gain,
  and no HA→SQLite path is configured; the richer DB path (per-zone durations from
  `zone_runs` composed in AppDaemon) is noted as a future upgrade in §9.10. Both files
  YAML-validated. Code complete; Dev-Tools + dry-run verification pending a test session.
  Also added `script.diagnose_whatsapp_path` (notification/scripts.yaml) — a manual,
  Dev-Tools-only diagnostic that calls the CallMeBot `rest_command` with the response
  captured (the production tier scripts swallow it via `continue_on_error`) and surfaces
  the HTTP status/body via a persistent notification + `log_system_event`. Bypasses the
  winter gate on purpose (transport test). Prompted by WhatsApp notifications not arriving;
  first suspects are `input_boolean.system_winterized` left ON (silently gates the STANDARD
  tier + the monthly test) or a deactivated CallMeBot free-tier API key.
- **2026-08-18 (Phase 9.10 VERIFIED + season reset bug fixed):** §9.10 test session.
  **(a) Standalone** `send_watering_summary` (`runtime_min: 45`, 4 zones) delivered the
  multi-line body correctly on the phone — PASS. **(b) Full cycle**: a manual-button dry-run
  (parallel, zones temporarily shortened to 1 min) auto-fired **exactly ONE** summary from
  `state_post_cycle_relief` — `Evening watering complete (manual)`, `Runtime: 2 min` matching
  wall-clock, state returned to `idle` — PASS. This also confirmed `db_writer` recreates
  `binary_sensor.watering_cycle_active` at Event 1, so the top-of-relief runtime capture works
  end-to-end. §9.10 marked COMPLETE; START_HERE follow-up #5 closed. **Side finding during the
  cycle:** `state_window_check` set all zones to `heavy` on a cool, post-rain day. Diagnosed via
  a decision-tree replay template: `temp_avg_high_3day`=30.4 (still carrying the Aug 15–16
  heatwave) > `temp_heavy` AND `rain_72h`=4.9 < `rain_min`=5.0 (by 0.1 mm — a localized ~10 mm
  shower missed the DWD station). Also found **`input_select.zone_N_season` had `initial: spring`
  and nothing auto-sets season**, so it silently reverted to `spring` on every restart (wrong
  seasonal thresholds in August). **Fixed:** removed `initial:` from all four
  `zone_N_season` helpers (`watering_helpers/zone_helpers.yaml`) → RestoreEntity (ADR-017
  pattern, mirrors `zone_sequencing_mode`); first-boot fallback = `options[0]` = spring. The
  deeper §6.2 decision-logic rework (lagging 3-day-high temp overriding a cool, just-rained day;
  no current-conditions path; knife-edge thresholds; threshold helpers share the same
  reset-on-restart property) is logged as a new START_HERE follow-up, not fixed here. **DB note
  for future decision-effectiveness analysis:** the per-cycle weather snapshot IS recorded —
  Event 1 writes `rainfall_24h_mm`/`rainfall_72h_mm`/`temp_high_c` to `watering_cycles` and
  Event 3 writes per-zone `weather_program` to `zone_runs`. Caveats: `temp_high_c` stores
  `brightsky_temp_high_yesterday` (25.6), NOT the `temp_avg_high_3day` (30.4) the tree actually
  decides on; season + thresholds are not recorded; and **skip days (all zones `off` → back to
  idle before preflight) write no row at all**, so days-not-watered are invisible in the DB.
- **2026-08-18 (Phase 7 — front-end design process defined, ADR-019):** restructured Phase 7
  around a seven-gate implementation process (§7.0–7.6: Requirements → Design Tokens →
  Information Architecture → Hi-Fi Mockup → HA Build → Responsive Tiers → Interaction &
  Hardening), each with an exit checklist + a short "how". Original placeholder card list
  preserved as §7.7 (content inventory). Decisions: repo YAML-mode dashboards (provisional),
  Lovelace + curated HACS cards (card-mod glassmorphism), HTML-Artifact-mockup feedback loop.
  Tooling set up: `frontend-design` + `ha-dashboard-design` skills; `hass-mcp` live HA access
  (voska v0.6.0 via uvx) established **READ-ONLY** by standing rule — no state/service/helper/
  config/code change without express per-action consent, destructive steps independently
  verified, always recoverable, "Before You Code" checklist applies. `entity_reference.md` +
  `test_scenarios.md` to be updated once UI files exist. See ADR-019.

---

## File Ownership & Responsibility

This section tracks which files exist, their purpose, current status, and who maintains them (ESPHome vs Home Assistant configuration).

### Entity ID Quick Reference

**IMPORTANT:** All ESPHome entities use full `watering_system_` prefix in Home Assistant.

**Example patterns:**
- Switches: `switch.watering_system_relay_{NUMBER}_{DESCRIPTION}`
- Binary Sensors: `binary_sensor.watering_system_{DESCRIPTION}`
- Sensors: `sensor.watering_system_mppt_{DESCRIPTION}`

**Complete reference:** See `/docs/entity_reference.md`

**Common mistake:** Using ESPHome `id:` values (e.g., `relay_pump_main`) instead of actual HA entity IDs (e.g., `switch.watering_system_relay_1_main_pump`). Always verify in HA Developer Tools → States before writing automations.

### Documentation Files

| File | Owner | Purpose | Status |
|------|-------|---------|--------|
| `docs/architecture.md` | Design | System design, state machine, configuration entities | ✅ Complete | 
| `docs/programming-notes.md` | Process | Coding standards, patterns, workflow guardrails | ✅ Living doc | 
| `docs/impl_roadmap.md` | Status | Implementation checklist and progress tracking | ✅ Active | 
| `docs/test_scenarios.md` | Testing | Concrete test cases with pass/fail tracking | ✅ Created | 
| `docs/entity_reference.md` | Reference | Quick reference to verify entities | ✅ Created | 
| `README.md` | Project | Project overview, setup instructions | 📋 Needs update | TBD |
| `docs/fert_pump_cal_v2.md` | Complete | Calibration procedure |
| `docs/db_schema.sql` | Reference | Canonical SQLite schema for `watering_ops` (source of truth; pull_public_repo.sh copies it to the AppDaemon app folder so the deployed schema cannot drift) | ✅ Complete |
| `docs/db_setup_guide.md` | Reference | Phase 3.5 setup: AppDaemon + `watering_ops` DB on HA Green | ✅ Complete |

---

### ESPHome Configuration Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `esphome/watering-esp32.yaml` | Main device config | ✅ Active | Base config, includes packages |
| `esphome/packages/modbus_rs485.yaml` | Relay board (0x01) | ✅ Active | 16 relays, UART2 config |
| `esphome/packages/inputs.yaml` | GPIO sensors | ✅ Active | Float switches (GPIO34/35) |
| `esphome/packages/victron_ble.yaml` | SmartSolar BLE | ✅ Active | Battery/solar monitoring |
| `esphome/components/victron_ble/*` | Vendored component | ✅ Active | GPL-3.0 licensed |
| `esphome/secrets.yaml` | Credentials | ✅ Private | Never committed (gitignored) |
| `esphome/secrets.example.yaml` | Credentials template | ✅ Public | Sanitized placeholders |

---

### Home Assistant Configuration Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `home-assistant/configuration.yaml` | Main HA config | ✅ Active | Includes packages |
| `home-assistant/packages/dwd_brightsky.yaml` | Weather sensors | ✅ Complete | Brightsky API integration |
| `home-assistant/packages/watering_helpers/config_helpers.yaml` | System-level helpers | ✅ Complete | State, schedule, safety config |
| `home-assistant/packages/watering_helpers/zone_helpers.yaml` | Per-zone helpers | ✅ Complete | Programs, runtimes, thresholds |
| `home-assistant/packages/watering_helpers/fert_helpers.yaml` | Fertigation helpers | ✅ Complete | Dosing rates, schedules |
| `home-assistant/packages/watering_scripts/zone_scripts.yaml` | Zone control | ✅ Complete | Open/close, sequencing |
| `home-assistant/packages/watering_scripts/pump_scripts.yaml` | Pump control | 📋 Planned | Start/stop, pressure relief |
| `home-assistant/packages/watering_scripts/fert_scripts.yaml` | Fert control | ⏳ Phase 2 | 24V cabinet, dosing pumps |
| `home-assistant/packages/watering_safety/scripts.yaml` | Safety/emergency | 📋 Planned | Emergency stop, safe shutdown |
| `home-assistant/packages/watering_state/state_scripts.yaml` | State transitions | 📋 Planned | Individual state handlers |
| `home-assistant/packages/watering_state/state_machine.yaml` | Master automation | 📋 Planned | State watcher, triggers |
| `home-assistant/packages/watering_safety/automations.yaml` | Safety monitors | 📋 Planned | Tank, comms, runtime limits |
| `home-assistant/secrets.yaml` | Credentials | ✅ Private | Never committed (gitignored) |
| `home-assistant/secrets.example.yaml` | Credentials template | ✅ Public | Sanitized placeholders |
| `home-assistant/packages/watering_notification/helpers.yaml` | Notification system helpers | ✅ Complete | Winterization, test confirmations, error tracking |
| `home-assistant/packages/watering_notification/config.yaml` | REST commands, IMAP config | ✅ Complete | Service integrations |
| `home-assistant/packages/watering_notification/scripts.yaml` | Notification sending scripts | ✅ Complete | Tiered notifications, summary compilation |
| `home-assistant/packages/watering_notification/tests.yaml` | Testing automations | ✅ Complete | Daily, monthly, de-winterization tests |
| `home-assistant/appdaemon/watering_db/apps.yaml` | AppDaemon app config | ✅ Complete | Registers db_schema_init; kept OUT of packages/ (not an HA package). Deploys to `/homeassistant/appdaemon/apps/watering_db/` via pull_public_repo.sh |
| `home-assistant/appdaemon/watering_db/db_schema_init.py` | DB bootstrap app | ✅ Complete | Idempotently applies schema on AppDaemon start. Deployed alongside apps.yaml + a pull-copied db_schema.sql |
| `home-assistant/appdaemon/watering_db/db_export.py` | Seasonal CSV export app | ✅ Complete | `DbSeasonalExport`; on the `watering_seasonal_export` event, writes year-filtered CSVs to `/homeassistant/watering_exports/` + a `system_events` audit row. Read-only on operational data |
| `home-assistant/packages/watering_db/db_automations.yaml` | DB HA automations | ✅ Complete | Home for all watering_db HA automations; currently fires `watering_seasonal_export` on `system_winterized` OFF -> ON. Real HA package (under packages/), unlike the AppDaemon app folder. Descriptive stem (not bare `automations.yaml`) to avoid `!include_dir_named` package-name collisions |

---

### Repository Infrastructure

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `.gitignore` | Ignore rules | ✅ Active | Secrets, temp files excluded |
| `.yamllint` | YAML linting config | ✅ Active | Aligned with Prettier |
| `LICENSE` | Project license | ✅ Active | MIT (dual with GPL for victron_ble) |
| `LICENSE.GPL-3.0` | GPL component license | ✅ Active | For victron_ble component |
| `.github/workflows/lint.yml` | YAML validation | ✅ Active | yamllint + prettier |
| `.github/workflows/gitleaks.yml` | Secret scanning | ✅ Active | Prevents credential leaks |
| `.github/workflows/publish.yml` | Mirror workflow | ✅ Active | Private → public sanitizer |

---

### File Naming Conventions

**ESPHome packages:**
- Pattern: `{subsystem}_{component}.yaml`
- Examples: `modbus_rs485.yaml`, `victron_ble.yaml`

**Home Assistant packages:**
- **Subfolder pattern**: `{functional_area}/` 
  - Implemented: `notification/`, `weather/`, `watering_helpers/`
  - Planned: `watering_scripts/`, `watering_state/`, `watering_safety/`
- **File pattern within subfolders**: `{descriptive_name}.yaml`
  - Types: `helpers`, `scripts`, `automations`, `state_machine`, `config`, `tests`
  - Examples: 
    - `notification/scripts.yaml` - Notification sending scripts
    - `watering_scripts/zone_scripts.yaml` - Zone control operations
    - `watering_state/state_machine.yaml` - Master state controller
    - `watering_safety/automations.yaml` - Safety monitors

**Subfolder organization:**
- `notification/` - Complete notification system (WhatsApp + Email)
- `weather/` - External weather integrations
- `watering_helpers/` - Configuration helpers (system, zone, fert)
- `watering_scripts/` - All operational scripts (zones, pumps, fert)
- `watering_state/` - State machine and state transition logic
- `watering_safety/` - Safety monitors and emergency procedures

**Why subfolders:**
- Groups related files by feature/function
- Easy to disable entire subsystems
- Clear ownership and responsibility
- Scales well as system grows
- Reduces root-level clutter

**Why this matters:**
- Consistent naming makes files easier to find
- Clear ownership prevents duplicate implementations
- Status tracking shows what's built vs. planned

---

### Adding New Files

When creating a new configuration file:

1. **Check this table first** - Is there already a file for this purpose?
2. **Follow naming convention** - Use established patterns
3. **Update this table** - Add entry with status and notes
4. **Update secrets.example.yaml** - If new secrets are needed
5. **Update .gitignore** - If new files should be excluded
6. **Test in isolation** - Verify file loads without errors
7. **Update impl_roadmap.md** - Check off corresponding task

---
