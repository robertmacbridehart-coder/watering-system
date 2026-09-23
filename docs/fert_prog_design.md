# Fertigation Program V2 Design Summary

**Document Version:** 1.3  
**Date:** 2026-08-06 (added §5.5 Concentrate Loadout & Per-Zone Seasonal Plan)  
**Status:** Design Complete - Ready for Implementation  
**Implementation Phase:** Phase 3.3 (Fertigation Control Scripts)

---

## Executive Summary

This document defines the complete V2 fertigation program design, replacing the original fixed-interval approach with a weather-responsive rolling window system. The design provides per-zone flexibility for different crop requirements while maintaining robust safety controls and graceful degradation when sensors are unavailable.

**Key Changes from V1:**
- Fixed interval (every N days) → Rolling 14-day window with seasonal targets
- System-wide settings → Per-zone configuration for all parameters
- Single trigger logic → Multi-condition evaluation with hard blocks and prevailing criteria
- Fixed dose → Flexible dose behavior for light programs (salt-sensitive vs tolerant crops)
- Temperature-based triggers → Soil moisture primary, rain fallback, temperature removed

---

## 1. Design Philosophy

### 1.1 Core Principles

**Weather-Responsive Fertigation:**
- Fertilizer application adapts to actual weather conditions, not fixed schedules
- Prevents over-fertilization during rainy periods (leaching risk)
- Ensures adequate fertilization during dry periods (uptake optimization)

**Per-Zone Flexibility:**
- Each zone has independent configuration for all parameters
- Supports mixed cropping (blueberries, raspberries, vegetables in different zones)
- Different salt tolerance, moisture requirements, fertilization rates

**Safety-First Design:**
- System-wide hard blocks prevent unsafe fertigation
- Tank level check BEFORE starting any fertigation
- Post-phase flushing ensures line clearing even if cycle interrupted
- Graceful degradation: works without soil sensors (rain-only mode)

**Agronomic Foundation:**
- Initial values optimized for ericaceous crops (blueberries/lingonberries)
- Conservative defaults (salt-sensitive behavior)
- User must explicitly enable aggressive options (full dose in light program)

---

## 2. System Architecture

### 2.1 Decision Flow

```
window_check state (existing):
  ↓
  [NEW] Check tank level (system-wide hard block)
  ↓ BLOCK ALL if low_water_level == ON
  ↓ CONTINUE if OK
  ↓
  Check winterization (existing system-wide block)
  ↓ BLOCK ALL if system_winterized == ON
  ↓ CONTINUE if inactive
  ↓
  FOR EACH ZONE:
    ↓
    Check rolling window target
    → events_last_14d < seasonal_target?
    ↓ NO → BLOCK (target met)
    ↓ YES → CONTINUE
    ↓
    Check 48-hour interval
    → hours_since_last_fert >= 48?
    ↓ NO → BLOCK (too soon)
    ↓ YES → CONTINUE
    ↓
    Check prevailing criteria
    → IF soil_sensor_available:
        Check moisture range (normal_min to off_min)
      ELSE:
        Check rain fallback (< rain_off_mm)
    ↓ FAIL → BLOCK (conditions unfavorable)
    ↓ PASS → ALLOW
    ↓
  Determine which zones fertigate
  ↓
  Execute fertigation (sequential mode)
```

### 2.2 State Machine Integration

**Existing States (No Changes):**
- `window_check` - Enhanced with V2 logic
- `fert_prep` - Unchanged
- `fert_dose_phase1` - Unchanged
- `fert_dose_phase2` - Unchanged

**New Requirements:**
- `window_check` must evaluate V2 multi-condition logic
- Per-zone eligibility determination (which zones fertigate)
- Sequential zone execution (one zone completes before next starts)

**State Tracking:**
- New helper: `input_text.current_fertigation_zone` (tracks active zone 0-4)
- Binary sensors: `binary_sensor.zone_X_fertigation_active` (ON during dose phases)
- History stats: `sensor.zone_X_fert_events_14d` (rolling window count)

---

## 3. Configuration Helpers

### 3.1 New Helpers Summary

**Total New Entities:** 77
- **68 helpers in zone_helpers.yaml** (per-zone configuration)
- **9 helpers/sensors** (system tracking and history)

**Reused Existing Helpers:** 8
- 4× `input_datetime.zone_X_last_fert_event` (48h interval tracking)
- 4× `input_select.zone_X_season` (threshold selection)

### 3.2 Zone Helpers (68 Total)

**File:** `home-assistant/packages/watering_helpers/zone_helpers.yaml`

#### 3.2.1 Light Program Dose Control (4 helpers)

**Purpose:** Control fertilizer dose behavior during light watering programs

```yaml
input_boolean:
  zone_1_allow_full_dose_light_program:
    name: "{{states('input_text.zone_1_friendly_name')}} - Allow Full Dose in Light Program"
    icon: mdi:beaker-alert
    initial: false  # Conservative default

  # Repeat for zones 2, 3, 4
```

**Logic:**
- `false` (default): 50% fertilizer in 50% water (proportional, same concentration)
- `true` (user-enabled): 100% fertilizer in 50% water (full dose, 2x concentration)

**Safety:** Default to conservative proportional dosing. Only enable for salt-tolerant crops.

**Crop Guidance:**
- Salt-sensitive (keep OFF): Blueberries, azaleas, rhododendrons, lingonberries
- Salt-tolerant (can enable): Raspberries, blackberries, most vegetables

#### 3.2.2 Soil Moisture Thresholds (48 helpers)

**Purpose:** Define soil saturation thresholds for program selection and fertigation eligibility

**Pattern:** 3 thresholds × 4 seasons × 4 zones = 48 helpers

```yaml
input_number:
  zone_X_SEASON_normal_moisture_min:
    min: 0
    max: 100
    step: 5
    unit_of_measurement: "%"
    mode: slider

  zone_X_SEASON_light_moisture_min:
    # Same structure

  zone_X_SEASON_off_moisture_min:
    # Same structure
```

**Program Selection Logic:**
```
IF moisture >= off_moisture_min:     program = "off" (saturated)
ELIF moisture >= light_moisture_min: program = "light" (adequate)
ELIF moisture >= normal_moisture_min: program = "normal" (moderate)
ELSE:                                 program = "heavy" (dry)
```

**Fertigation Eligibility Range:**
```
ALLOWED if: normal_moisture_min <= moisture < off_moisture_min
BLOCKED if: moisture < normal_min (too dry) OR moisture >= off_min (too wet)
```

**Initial Values (Berry-Optimized):**

| Season | Normal Min | Light Min | Off Min | Fert Range | Rationale |
|--------|------------|-----------|---------|------------|-----------|
| Spring | 40% | 55% | 75% | 40-75% | Active growth, wider tolerance |
| Summer | 45% | 60% | 70% | 45-70% | Peak stress, tighter range |
| Fall | 40% | 55% | 75% | 40-75% | Growth slowing, similar to spring |
| Winter | 35% | 50% | 80% | 35-80% | Dormant, widest tolerance |

**Agronomic Basis:**
- Blueberries/lingonberries: ericaceous, 50-70% field capacity optimal
- Avoid waterlogging (>70-80%): root rot, fertilizer leaching
- Avoid drought (<40-45%): nutrient uptake impaired, stress
- Summer tightest: fruit development most critical

#### 3.2.3 Fertigation 14-Day Targets (16 helpers)

**Purpose:** Define target number of fertigation events per 14-day rolling window

**Pattern:** 4 seasons × 4 zones = 16 helpers

```yaml
input_number:
  zone_X_SEASON_fert_14d_target:
    min: 0
    max: 14
    step: 1
    unit_of_measurement: "events"
    mode: box
```

**Initial Values (All Zones):**

| Season | Target Events | Frequency | Rationale |
|--------|---------------|-----------|-----------|
| Spring | 5 | ~2.5×/week | Active root growth |
| Summer | 7 | ~3.5×/week | Peak nutrient demand |
| Fall | 3 | ~1.5×/week | Growth slowing |
| Winter | 0 | None | Dormant period |

**Logic:**
```
IF events_last_14_days < seasonal_target:
  Fertigation eligible (subject to other conditions)
ELSE:
  Fertigation blocked (target met)
```

### 3.3 System Helpers (9 entities)

**File:** `home-assistant/packages/watering_helpers/fert_helpers.yaml` (add to existing file)

#### 3.3.1 Current Zone Tracking (1 helper)

```yaml
input_text:
  current_fertigation_zone:
    name: "Current Fertigation Zone"
    icon: mdi:sprinkler-variant
    max: 4
    initial: "0"  # "0" = no zone, "1"-"4" = zone number
```

**Usage:**
- Set by fertigation script when entering `fert_dose_phase1`
- Reset to "0" when exiting `fert_dose_phase2`
- Used by binary sensors to determine which zone is active
- **Critical:** Must reset on error states (TBD in Phase 3.3)

#### 3.3.2 Zone Fertigation Active Sensors (4 template sensors)

```yaml
binary_sensor:
  - platform: template
    sensors:
      zone_1_fertigation_active:
        friendly_name: "Zone 1 Fertigation Active"
        value_template: >
          {{ states('input_select.watering_system_state') in ['fert_dose_phase1', 'fert_dose_phase2']
             and states('input_text.current_fertigation_zone') == '1' }}
        icon: mdi:sprinkler-variant

      # Repeat for zones 2, 3, 4
```

**Purpose:**
- Indicates when specific zone is actively receiving fertilizer
- Used by history_stats for event counting
- ON during dosing phases only (NOT during fert_prep or window_check)

#### 3.3.3 Rolling Window Event Counters (4 history_stats sensors)

```yaml
sensor:
  - platform: history_stats
    name: "Zone 1 Fert Events Last 14 Days"
    unique_id: zone_1_fert_events_14d
    entity_id: binary_sensor.zone_1_fertigation_active
    state: "on"
    type: count
    duration:
      days: 14

  # Repeat for zones 2, 3, 4
```

**Purpose:**
- Counts fertigation events in true rolling 14-day window
- Automatic calculation (no manual timestamp management)
- Persists across HA restarts (requires recorder/database)

**Behavior:**
- Each OFF→ON transition = 1 event
- Split-dose cycles (phase1→phase2) = 1 event (sensor stays ON)
- Updates continuously, no daily reset needed

**Dependencies:**
- Requires Home Assistant recorder (SQLite or external DB)
- 5-30 second initialization delay after HA restart (normal behavior)

---

## 4. Trigger Conditions

### 4.1 Hard Blocks (System-Wide & Per-Zone)

**System-Wide Blocks (Block ALL zones):**

1. **Tank Level Low** ⭐ NEW - FIRST CHECK
   - Entity: `binary_sensor.watering_system_low_water_level`
   - Condition: Must be OFF (tank adequate)
   - Rationale: Prevents starting fertigation if tank near empty
   - Safety: Ensures sufficient water for complete cycle + flush

2. **Winterization Active**
   - Entity: `input_boolean.system_winterized`
   - Condition: Must be OFF
   - Rationale: System powered down for winter

**Per-Zone Blocks:**

3. **Rolling Window Target Met**
   - Entity: `sensor.zone_X_fert_events_14d`
   - Condition: Must be < `input_number.zone_X_SEASON_fert_14d_target`
   - Rationale: Prevents over-fertilization, ensures even distribution

4. **Interval Too Short**
   - Entity: `input_datetime.zone_X_last_fert_event`
   - Condition: Must be ≥48 hours ago
   - Calculation: `(now() - last_fert).total_seconds() / 3600 >= 48`
   - Rationale: Minimum recovery time, prevents salt accumulation

### 4.2 Prevailing Criteria (Per-Zone)

**Priority Order:** Soil moisture (if available) → Rain (fallback)

#### 4.2.1 Soil Moisture Check (Primary)

**Availability Check:**
```yaml
states('sensor.zone_X_soil_moisture') not in ['unknown', 'unavailable']
```

**Eligibility Logic:**
```yaml
current_season = states('input_select.zone_X_season')
normal_min = states(f'input_number.zone_X_{current_season}_normal_moisture_min')
off_min = states(f'input_number.zone_X_{current_season}_off_moisture_min')
moisture = states('sensor.zone_X_soil_moisture') | float

IF moisture >= off_min:
  BLOCK (too wet - saturation risk, leaching risk)
ELIF moisture < normal_min:
  BLOCK (too dry - need plain water first, uptake impaired)
ELSE:
  ALLOW (optimal range for fertigation)
```

**Range Examples:**
- Spring: 40-75% (35% range)
- Summer: 45-70% (25% range) - tightest
- Fall: 40-75% (35% range)
- Winter: 35-80% (45% range) - widest

#### 4.2.2 Rain Fallback (Secondary)

**When Used:** Soil sensor unavailable or reading invalid

**Eligibility Logic:**
```yaml
current_season = states('input_select.zone_X_season')
rain_off = states(f'input_number.zone_X_{current_season}_rain_off_mm')
rain_24h = states('sensor.brightsky_rain_24h') | float

IF rain_24h >= rain_off:
  BLOCK (too much recent rain - soil likely saturated)
ELSE:
  ALLOW (rain conditions favorable)
```

**Existing Thresholds (Reused):**
- Defined in existing zone_helpers.yaml
- Example: Zone 1 spring `rain_off_mm = 20mm`
- Example: Zone 2 spring `rain_off_mm = 15mm` (more sensitive)

### 4.3 Temperature Removal

**Decision:** Temperature check REMOVED from fertigation triggers

**Rationale:**
- Soil moisture already captures heat stress effects
- Rain already captures cool/wet period effects
- Temperature still affects watering program (light/normal/heavy)
- Simplifies trigger logic without sacrificing safety

---

## 5. Dose Calculation Logic

### 5.1 Base Dose by Program

**Standard Behavior (per zone):**

| Program | Water Runtime | Base Fertilizer Dose | Notes |
|---------|---------------|----------------------|-------|
| Off | 0% | 0% | No watering, no fertilizer |
| Light | 50% | See 5.2 | Depends on zone boolean |
| Normal | 100% | 100% | Standard dose |
| Heavy | 150% (single window) or 100%+50% (dual window) | 100% | Extra water, NOT extra fertilizer |

### 5.2 Light Program Special Handling

**Per-Zone Boolean:** `input_boolean.zone_X_allow_full_dose_light_program`

**Logic:**
```yaml
IF zone_program == "light":
  IF zone_X_allow_full_dose_light_program == ON:
    dose_multiplier = 1.0  # Full dose (100% fert in 50% water = 2x concentration)
  ELSE:
    dose_multiplier = 0.5  # Proportional (50% fert in 50% water = same concentration)
```

**Safety:**
- Default: `false` (proportional dosing, conservative)
- User must explicitly enable full dose for each zone
- Dashboard warning when enabled: "⚠️ 2x concentration - salt-tolerant crops only"

**Crop Guidance:**

| Crop Type | Setting | Rationale |
|-----------|---------|-----------|
| Blueberries | OFF (0.5x) | Salt-sensitive, ericaceous, avoid concentration |
| Lingonberries | OFF (0.5x) | Salt-sensitive, ericaceous |
| Azaleas/Rhododendrons | OFF (0.5x) | Salt-sensitive, ericaceous |
| Raspberries | Can enable (1.0x) | More salt-tolerant |
| Blackberries | Can enable (1.0x) | More salt-tolerant |
| Most vegetables | Can enable (1.0x) | Generally salt-tolerant |

### 5.3 Split-Dose vs Single-Dose

**Determined by Zone Program:**

Dosing phase 1: 50% of plain watering runtime + 2-min flush
Dosing phase 2: 50% of plain watering runtime + 2-min flush

Fertilizer split:
- Phase 1: 50% of total dose
- Phase 2: 50% of total dose

Example (Normal program, base = 20 min):
- Plain watering would be: 20 min
- Phase 1 dosing: 10 min (50% of 20 min)
- Phase 1 flush: 2 min
- Phase 2 dosing: 10 min (50% of 20 min)
- Phase 2 flush: 2 min
- Total: 20 min dosing + 4 min flush = 24 min

**Normal/Heavy Programs (Split-Dose):**
```
Phase 1: 50% of calculated dose
Phase 2: 50% of calculated dose
Total: 100% (or 150% for heavy)
```

**Light Program (Single-Dose):**
```
Phase 1: Calculated dose (50% or 100% depending on boolean)
Phase 2: Plain water only (no fertilizer)
Total: 50% or 100%
```

**Rationale:**
- Split-dose (normal/heavy): Better nutrient distribution, reduced concentration peaks
- Single-dose (light): Adequate soil moisture already present, minimize fertilizer

### 5.4 Actual Pump Commands

**Calculation Flow:**
```
1. Determine program (off/light/normal/heavy)
2. Get base runtime: input_number.zone_X_base_runtime_min
3. Apply program multiplier: runtime = base × program_multiplier
4. Get fertilizer dose per pump: input_number.zone_X_fert_pumpN_dose_ml
5. Apply dose multiplier: dose = base_dose × dose_multiplier
6. Calculate pump command using calibration curve: cmd = (dose/runtime - b) / a
7. Send Modbus command to RS-485 pumps (0x02-0x04)
```

**Existing Infrastructure:**
- Pump calibration: `input_number.fert_pump{n}_cal_*` helpers
- Calibration curves: q = a×cmd + b (linear regression, R² ≥ 0.995)
- Per-zone dosing: `input_number.zone_X_fert_pump{n}_dose_ml`

**Pump Selection (per zone, per season):**
- Helper: input_number.zone_{1-4}_{season}_pump
- Values: 1, 2, or 3 (selects which of the 3 RS-485 pumps to use)
- Each zone uses only ONE pump per cycle
- Selection can change by season (e.g., spring uses pump 1, summer uses pump 2)

### 5.5 Concentrate Loadout & Per-Zone Seasonal Plan

> **PLANNED / provisional (2026-08-06).** Fills in §5.4's `zone_{1-4}_{season}_pump`
> selection — *what each pump holds* and *which zone/season draws which grade*.
> Doses/EC are starting points to refine at calibration and first seasons. All three
> grades are chloride-free, sulfate-based, with chelated micros. Physical bed/emitter
> layouts live in `physical_layout.md`.

**Pump loadout** (three pumps, mixed at season start and left in place — no weekly re-mix):

| Pump | Concentrate | Role |
|------|-------------|------|
| 1 | **Hakaphos Grün 20-5-10 (+2 MgO)** | Growth / N-forward |
| 2 | **Hakaphos Blau 15-10-15 (+2 MgO)** | Balanced main-season |
| 3 | **Hakaphos Rot 8-12-24 (+4 MgO)** | Fruiting / K peak |

- **Calcium is handled outside fertigation** — a yearly granular **gypsum** (CaSO₄)
  application to beds that need it (esp. Zone 4). **Not Patentkali** (K/Mg/S — would
  double Rot's potassium and recreate the K→Mg/Ca antagonism seen in the 2026 canes).
  **No calcium on Zone 2** (calcifuge). Keeping Ca out of the pumps also removes any
  Ca/phosphate–sulfate precipitation on the shared upstream manifold, so the three
  grades are mutually compatible.
- **Seasonal arc (all fruiting-perennial zones):** Grün (spring) → Blau (early/main
  summer) → Rot (fruiting + fall hardening). Zones differ in **dose/EC and handoff
  timing**, not in which bottle.
- **EU 2019/1148:** Grün (20 N) can trip the explosives-precursor purchase rule; it is
  currently available to consumers at the chosen retailer. Contingency if later
  restricted: swap in a lower-N growth grade (or lean Blau harder) and adjust the dose
  table — no rig change.

**Per-zone seasonal selection:**

**Zone 1 — Cane fruit + espalier**

| Season | Grade | Rationale |
|--------|-------|-----------|
| Spring | Grün | N push for cane/leaf growth (no fruit yet) |
| Summer | Blau | fruiting begins; balanced N (primocane growth) + rising K |
| Fall → first frost | Rot | late fruit (fall rasp, blackberry) + cane hardening; N tapered |

- Standard dose; `allow_full_dose_light_program` **OFF** (strawberries salt-sensitive).
  No high-N (Grün) after midsummer — soft growth hurts winter hardiness. Hold in
  fall/Rot until first frost. Mg/K via grades (Rot +4 MgO) + EPSO Top foliar if short;
  Ca not currently limiting (gypsum optional).

**Zone 2 — Moorbeet (blueberries + lingonberries)**

| Season | Grade | Rationale |
|--------|-------|-----------|
| Spring | Grün | N + mild acidification — ideal ericaceous |
| Early summer | Blau | gentle N→K transition at fruit set |
| Fruiting + fall | Rot | high K for fruit + hardening / bud set |

- Conservative: **EC < 1.0**, ~0.87 g/L; `allow_full_dose_light_program` **OFF**. **No
  calcium** (calcifuge). Cease by mid-October. Minor watch: Rot's higher P vs
  mycorrhizal P-scavenging (negligible at this EC). Supersedes the moorbeet plan §7.1
  Grün→Naranja→Rot arc (Naranja replaced by Blau + Rot).

**Zone 3 — Vegetable patch, leafy (lettuce)**

| Season | Grade | Rationale |
|--------|-------|-----------|
| Growing season | Grün → Blau lean | leafy crops want steady N most of the season |

- Salt-tolerant: `allow_full_dose_light_program` may be **ON**. Little/no Rot. Layout
  transient → revisit yearly.

**Zone 4 — Vegetable patch, fruiting/root (tomato, pepper, cucumber, onion)**

| Season | Grade | Rationale |
|--------|-------|-----------|
| Early | Grün / Blau | N for establishment / vegetative growth |
| Fruit set → harvest | Rot | K for fruiting |

- Salt-tolerant: full dose OK. **Calcium critical** (blossom-end rot on tomato/pepper):
  spring **gypsum** + even watering (the automated schedule matters as much as soil Ca).
  Onions: moderate feeders. Layout transient → revisit yearly.

---

## 6. Post-Phase Flushing

### 6.1 Flush Requirements

**Specification:**
- Duration: 2 minutes fresh water
- Frequency: After EACH dosing phase
- Flow path: Same as fertigation (R7 fert line valve open)

**Timing Breakdown:**
- Dosing period: 50% of plain watering runtime (pump ON)
- Flush period: 2 minutes (pump OFF, main pump continues)
- Total phase time: dosing_duration + 2 min flush

**Important:** The 2-minute flush is ADDITIONAL time beyond the dosing period, not included in it.

**Total Flush Time Per Cycle:**
- Split-dose (normal/heavy): 4 minutes (2 min after phase1 + 2 min after phase2)
- Single-dose (light): 4 minutes (2 min after phase1 + 2 min after phase2)

**Note:** Light program still executes both phases (phase2 is plain water only), so still gets full flush time.

### 6.2 Rationale

**Safety Benefit:**
- Prevents fertilizer crystallization in lines
- Clears residue from pump tubing and injection point
- If error occurs between phases, lines already flushed from phase1

**Agronomic Benefit:**
- Ensures fertilizer reaches soil (not stuck in lines)
- Distributes fertilizer through root zone
- Reduces concentration at injection point

### 6.3 Implementation

**State Machine Flow:**
```
fert_dose_phase1:
  - Open R7 (fert line valve)
  - Close R6 (bypass valve)
  - Start pumps (fertilizer dosing)
  - Run for calculated time
  - Stop pumps
  - [NEW] 2-minute fresh water flush (pumps OFF, main pump ON, R7 still open)
  - Close R7, open R6
  - Transition to fert_dose_phase2 OR watering

fert_dose_phase2:
  - (Repeat above sequence)
  - After flush completes → transition to watering
```

**Key Point:** Main pump stays on during flush, RS-485 peristaltic pumps stop, fresh water pushes fertilizer through.

---

## 7. Sequential Fertigation Mode

### 7.1 Execution Order

**Requirement:** Zones fertigate one at a time (sequential only, no parallel option)

**Flow:**
```
window_check determines which zones need fertigation:
  Example: Zone 1, Zone 4 are eligible for fertigation, Zone 2 plain watering
  ↓
fert_prep:
  - Open bypass valve (R6)
  - Close fert line valve (R7)
  - Start main pump
  - Wait for pressure stabilization
  ↓
fert_dose_phase1 For each eligible zone (in order):
  ↓
  Zone 1:
    - Open zone 1 valve (R2)
    - Execute fert_dose_phase1 (dose + flush)
    - Close zone 1 valve
    - 30-second inter-zone delay
  ↓
  Zone 3:
    - Open zone 3 valve (R4)
    - Execute fert_dose_phase1 (dose + flush)
    - Close zone 3 valve
    - 30-second inter-zone delay
  ↓
  Zone 4:
    - Open zone 4 valve (R5)
    - Execute fert_dose_phase1 (dose + flush)
    - Close zone 4 valve
  ↓
Transition to watering_plain (Zone 2)
  ↓
  Zone 1:
    - Open zone 1 valve (R2)
    - Execute fert_dose_phase2 (dose + flush)
    - Close zone 1 valve
    - 30-second inter-zone delay
  ↓
  Zone 3:
    - Open zone 3 valve (R4)
    - Execute fert_dose_phase2 (dose + flush)
    - Close zone 3 valve
    - 30-second inter-zone delay
  ↓
  Zone 4:
    - Open zone 4 valve (R5)
    - Execute fert_dose_phase2 (dose + flush)
    - Close zone 4 valve
```

### 7.2 Inter-Zone Delays

**Specification:**
- 30 seconds between zones (same as plain watering)
- Allows pressure stabilization
- Prevents water hammer from rapid valve switching

**During Delay:**
- Previous zone valve closed
- Next zone valve still closed
- Main pump stays on
- Bypass valve open (R6), fert line valve closed (R7)

### 7.3 Pump Operation

**Main Pump (R1):**
- Stays ON continuously throughout entire fertigation sequence
- No stop/start between zones
- Reduces wear, maintains stable pressure

**Peristaltic Pumps (0x02-0x04):**
- Start/stop for each phase of each zone
- Commands sent via Modbus
- Independent control per zone based on dose calculations

---

## 8. Error Handling & Recovery

### 8.1 Scope

**Status:** TBD during Phase 3.3 implementation

**Documentation Requirement:**
- Identify error scenarios
- Define recovery procedures
- Ensure `current_fertigation_zone` reset
- Prevent orphaned binary sensor states

### 8.2 Known Scenarios (To Be Addressed)

1. **Manual Emergency Stop During Fertigation**
   - Expected: User presses emergency stop button
   - Required: Reset zone tracking, close valves, stop pumps

2. **Low-Low Tank Alarm Mid-Cycle**
   - Expected: Tank level drops below Low-Low threshold during dosing
   - Required: Immediate pump stop, state→error_tank_low, attempt flush if possible

3. **ESP32 Disconnect During Fertigation**
   - Expected: Network loss, ESP32 unavailable
   - Required: State→error_relay_state, halt fertigation, attempt graceful recovery

4. **Power Loss Mid-Cycle**
   - Expected: Power outage during fertigation
   - Required: On restart, detect incomplete cycle, reset tracking helpers

5. **State Machine Forced to Error State**
   - Expected: Automation forces state change due to unexpected condition
   - Required: Clean up tracking helpers, reset zone indicator

### 8.3 Critical Reset

**Requirement:** On ANY error state transition, ensure:
```yaml
input_text.current_fertigation_zone = "0"
binary_sensor.zone_X_fertigation_active → OFF (all zones)
# (Automatic once current_fertigation_zone = "0")
```

**Prevents:**
- Stuck event counters (history_stats would continue incrementing)
- Dashboard showing active fertigation when none occurring
- Incorrect interval calculations (thinks zone is still fertigating)

---

## Section 9: Pump Calibration Integration

**Purpose:** Define how pump calibration data integrates with V2 fertigation dose calculations

**Reference Document:** `/docs/fert_pump_cal_v2.md` - Complete step-by-step calibration procedure

---

### 9.1 Calibration Overview

#### Purpose

Peristaltic pump flow rates vary based on:
- Tubing elasticity and wear
- Operating pressure (backpressure from check valve + system pressure)
- Pump motor characteristics
- Solution viscosity and temperature

**Calibration establishes:** The relationship between motor speed command (rev/min) and actual delivered flow rate (mL/min) at operating conditions.

**CRITICAL:** The IRS42 stepper driver uses register 0x0033 (Maximum Speed) with values in **rev/min** (motor revolutions per minute), NOT percentage. Valid range: 1-3000 rev/min.

**Operating Conditions:**
- **Pressure:** 1.1 bar (via PRV on injection branch)
- **Solution:** Stock fertilizer at typical concentration (100 g/L)
- **Temperature:** Ambient (recorded from weather sensor)
- **System Load:** Test fixture matching typical zone emitter count

**Practical Speed Limits:**
- **Safe range:** 5-100 RPM (recommended for normal operation)
- **Operational maximum:** 100 RPM (conservative limit for tube longevity)
- **Not recommended:** >100 RPM (accelerated tube wear, reduced accuracy)
- **Driver limit:** 3000 RPM (hardware maximum, never practical for peristaltic pumps)

**For LEFOO LFP101ST with 1×3mm silicone tube:**
- Nameplate: 1-16 mL/min
- Estimated: ~0.15 mL/rev (3-roller design, based on 1mm ID tube cross-section)
- Practical range: ~7-100 RPM (targeting 1-15 mL/min)
- Maximum capacity at 100 RPM: ~15 mL/min
- Calibration setpoints: 13, 27, 40, 67, 100 RPM (targeting 2, 4, 6, 10, 15 mL/min)

#### Calibration Data Storage

**Home Assistant Helpers (per pump):**

```yaml
# Calibration Coefficients (linear model: q = a × cmd + b)
input_number:
  fert_pump1_cal_slope:         # 'a' - mL/min per % command
  fert_pump1_cal_intercept:     # 'b' - mL/min at 0% command
  fert_pump1_cal_r2:            # R² goodness of fit (0.995 minimum)
  
# Calibration Metadata
input_datetime:
  fert_pump1_last_cal:          # Date of last calibration
  
input_number:
  fert_pump1_cal_pressure:      # Test pressure in bar (1.1 typical)
  fert_pump1_cal_sg:            # Specific gravity of test solution
  
input_text:
  fert_pump1_cal_notes:         # Observations, tubing age, etc. (200 char max)
```

**Repeat for pumps 2 and 3.**

#### Calibration Status Sensors

**Template Sensor (per pump):**

```yaml
sensor:
  - platform: template
    sensors:
      fert_pump1_calibration_status:
        friendly_name: "Pump 1 Calibration Status"
        value_template: >
          {% set last_cal = states('input_datetime.fert_pump1_last_cal') %}
          {% set r2 = states('input_number.fert_pump1_cal_r2') | float(0) %}
          {% set days_old = (now() - as_datetime(last_cal)).days if last_cal != 'unknown' else 9999 %}
          
          {% if last_cal == 'unknown' or days_old > 365 %}
            EXPIRED
          {% elif r2 < 0.995 %}
            POOR
          {% elif days_old > 90 %}
            WARNING
          {% else %}
            VALID
          {% endif %}
        icon_template: >
          {% set status = states('sensor.fert_pump1_calibration_status') %}
          {% if status == 'VALID' %}
            mdi:check-circle
          {% elif status == 'WARNING' %}
            mdi:alert-circle
          {% elif status == 'POOR' %}
            mdi:close-circle
          {% else %}
            mdi:help-circle
          {% endif %}
        attribute_templates:
          equation: >
            {% set a = states('input_number.fert_pump1_cal_slope') | float(0) %}
            {% set b = states('input_number.fert_pump1_cal_intercept') | float(0) %}
            q = {{ "%.4f"|format(a) }} × cmd + {{ "%.4f"|format(b) }}
          r_squared: "{{ states('input_number.fert_pump1_cal_r2') }}"
          calibration_date: "{{ states('input_datetime.fert_pump1_last_cal') }}"
          pressure_bar: "{{ states('input_number.fert_pump1_cal_pressure') }}"
          notes: "{{ states('input_text.fert_pump1_cal_notes') }}"
```

**Status Values:**
- **VALID:** R² ≥ 0.995, calibration ≤ 90 days old
- **WARNING:** Calibration 91-365 days old (needs recalibration soon)
- **POOR:** R² < 0.995 (calibration fit poor, recalibrate immediately)
- **EXPIRED:** Calibration > 365 days old or never calibrated

---

### 9.2 Dose Calculation Flow (V2)

#### Step 1: Determine Target Dose

**Input Parameters (per zone, per pump):**
- `input_number.fert_zone_X_pumpN_dose_ml` - Base dose in mL (e.g., 60 mL)
- `input_select.zone_X_program` - Current program (off/light/normal/heavy)
- `input_boolean.zone_X_allow_full_dose_light_program` - Light program behavior

**V2 Dose Multipliers:**

| Program | Multiplier | Condition |
|---------|------------|-----------|
| Off | 0.0× | No fertigation |
| Light (proportional) | 0.5× | boolean OFF (default) |
| Light (full dose) | 1.0× | boolean ON (user-enabled) |
| Normal | 1.0× | Standard dose |
| Heavy | 1.5× | High water need → high nutrient need |

**Calculation:**

```yaml
# Example for Zone 1, Pump 1
{% set base_dose = states('input_number.fert_zone_1_pump1_dose_ml') | float(0) %}
{% set program = states('input_select.zone_1_program') %}
{% set allow_full = is_state('input_boolean.zone_1_allow_full_dose_light_program', 'on') %}

{% set multiplier = {
  'off': 0.0,
  'light': 1.0 if allow_full else 0.5,
  'normal': 1.0,
  'heavy': 1.5
} %}

{% set target_dose = base_dose * multiplier.get(program, 1.0) %}
```

**Example:**
- Base dose: 60 mL
- Program: Light
- Boolean: OFF (proportional)
- **Target dose: 60 × 0.5 = 30 mL**

#### Step 2: Calculate Required Flow Rate

{% set target_dose = 30 %}  # mL
{% set base_runtime = states('input_number.zone_1_base_runtime_min') | float(10) %}
{% set program = states('input_select.zone_1_program') %}

# Apply program multiplier to runtime (for WATERING, not dose)
{% set runtime_multipliers = {'off': 0.0, 'light': 0.5, 'normal': 1.0, 'heavy': 1.5} %}
# BUT: Heavy is 1.5 only in single-window mode, 1.0 in dual-window mode
{% set morning_enabled = is_state('input_boolean.enable_morning_window', 'on') %}
{% set evening_enabled = is_state('input_boolean.enable_evening_window', 'on') %}
{% set dual_window = morning_enabled and evening_enabled %}

{% if program == 'heavy' %}
  {% set runtime_multiplier = 1.0 if dual_window else 1.5 %}
{% else %}
  {% set runtime_multiplier = runtime_multipliers[program] %}
{% endif %}

{% set plain_watering_runtime = base_runtime * runtime_multiplier %}

# Dosing duration is 50% of plain watering runtime
{% set dosing_duration = plain_watering_runtime * 0.5 %}

# Calculate required flow rate
{% set required_flow = target_dose / dosing_duration %}
```

**Example:**
- Target dose: 30 mL (for entire cycle, 15 mL per phase)
- Base runtime: 10 minutes
- Program: Normal (1.0× multiplier)
- Plain watering runtime: 10 × 1.0 = 10 minutes
- Dosing duration per phase: 10 × 0.5 = 5 minutes
- **Phase 1 required flow: 15 mL / 5 min = 3 mL/min**
- **Phase 2 required flow: 15 mL / 5 min = 3 mL/min**

#### Step 3: Convert Flow to Command Value

**Inputs:**
- Required flow (mL/min) - from Step 2
- Calibration coefficients (slope, intercept) - from helpers

**Inverse Calibration Equation:**

Given calibration model: `q = a × cmd + b`

Solve for command: `cmd = (q - b) / a`

Where:
- `q` = required flow (mL/min)
- `cmd` = motor speed (rev/min)
- `a` = slope (mL/min per rev/min)
- `b` = intercept (mL/min at 0 rev/min)

**Implementation:**

```yaml
{% set required_flow = 6.0 %}  # mL/min
{% set a = states('input_number.fert_pump1_cal_slope') | float(0.3) %}
{% set b = states('input_number.fert_pump1_cal_intercept') | float(0.1) %}

# Calculate motor speed in rev/min
{% set motor_speed_rpm = (required_flow - b) / a %}

# Clamp to pump limits (1-3000 rev/min for IRS42 driver)
{% set motor_speed_rpm = [1, [motor_speed_rpm, 3000] | min] | max %}
```

**Example:**
- Required flow: 6.0 mL/min
- Slope (a): 0.3 mL/min per rev/min
- Intercept (b): 0.1 mL/min
- Motor speed: (6.0 - 0.1) / 0.3 = 19.7 rev/min
- **Modbus Command to register 0x0033: 20 rev/min** (rounded to integer)

#### Step 4: Validation & Safety Checks

**Pre-Execution Validation:**

```yaml
# Check 1: Calibration status
{% set cal_status = states('sensor.fert_pump1_calibration_status') %}
{% if cal_status not in ['VALID', 'WARNING'] %}
  # BLOCK: Calibration invalid or expired
  # Log error, set error_calibration state
{% endif %}

# Check 2: Command within operational limits
{% if motor_speed_rpm < 5 or motor_speed_rpm > 100 %}
  # BLOCK: Outside safe peristaltic pump range (5-100 RPM)
  # Below 5 RPM: Flow too low for accurate control
  # Above 100 RPM: Excessive tube wear, reduced accuracy
  # Adjust dose or extend runtime
{% endif %}

# Check 3: Command within driver hardware limits (backstop)
{% if motor_speed_rpm < 1 or motor_speed_rpm > 3000 %}
  # BLOCK: Command outside IRS42 driver range (1-3000 RPM)
  # This should never occur if Check 2 passes
{% endif %}

# Check 4: Flow rate achievable within safe range
{% set max_rpm = 100 %}  # Operational maximum
{% set max_safe_flow = (max_rpm * a) + b %}
{% if required_flow > max_safe_flow %}
  # BLOCK: Required flow exceeds pump capability
  # At {{ max_rpm }} RPM max: {{ max_safe_flow | round(1) }} mL/min
  # Reduce dose or extend runtime
{% endif %}

# Check 5: Dose vs. runtime sanity
{% if target_dose / actual_runtime > 15 %}
  # WARN: Very high flow rate (>15 mL/min is above typical operating range)
  # Verify dose and runtime settings
{% endif %}
```

**Speed Limit Rationale:**
- **5-100 RPM:** Safe operational range for tube longevity and accuracy
- **100 RPM hard limit:** Conservative maximum for 1×3mm silicone tube
- **Tube life at 100 RPM:** ~2000 hours (approximately 3-4 months of daily use)
- **Driver limit (3000 RPM):** Hardware maximum, serves as backstop only

#### Step 5: Send Modbus Command

**Script Execution:**

```yaml
script:
  start_dosing_pumps:
    sequence:
      # Write motor speed to register 0x0033 (Maximum Speed)
      - service: modbus.write_register
        data:
          hub: modbus_rs485
          slave: 2  # Pump 1 address (0x02)
          address: 0x0033  # Maximum Speed register
          value: "{{ motor_speed_rpm | int }}"
      
      # Trigger start command (register 0x0037)
      - service: modbus.write_register
        data:
          hub: modbus_rs485
          slave: 2
          address: 0x0037  # Start Command register
          value: 1  # Speed mode start
      
      # Repeat for pumps 2 and 3 if enabled (addresses 0x03, 0x04)
```

**Modbus Frame Examples:**
- Set 20 rev/min: `02 06 00 33 00 14 [CRC]` (hex 0x0014 = decimal 20)
- Start pump: `02 06 00 37 00 01 [CRC]`
- Stop pump: `02 06 00 38 00 01 [CRC]`

**Runtime Monitoring:**

During dose phase:
- Monitor actual delivered volume (if flow meter available)
- Compare to expected: `expected_volume = required_flow × elapsed_time`
- If deviation > 10%, flag for investigation

---

### 9.3 Error Detection & Recovery

#### Calibration Quality Issues

**Symptom:** R² < 0.995 after calibration

**Possible Causes:**
1. Air bubbles in suction or discharge line
2. Pressure instability during test (PRV malfunction)
3. Scale reading drift or vibration
4. Worn tubing (non-uniform elasticity)

**Resolution:**
1. Re-prime pump thoroughly
2. Verify PRV stable at 1.1 bar
3. Check scale calibration and stability
4. Replace tubing if age > 6 months or visible wear
5. Re-run full calibration

#### Operational Dose Errors

**Symptom:** Delivered dose consistently deviates from expected

**Detection Methods:**
1. **Flow meter validation** (if installed): Compare measured vs. calculated flow
2. **Tank consumption tracking**: Compare total fertilizer used vs. sum of commanded doses
3. **Plant response**: Nutrient deficiency or toxicity symptoms

**Resolution:**
1. Verify calibration status (VALID?)
2. Check operating pressure matches calibration pressure (1.1 bar)
3. Inspect tubing for wear, cracks, or slippage
4. Recalibrate if >90 days since last calibration
5. If persistent, suspect pump motor issue or Modbus communication problem

#### Calibration Expiration Handling

**Behavior:**
- **VALID (< 90 days):** Normal operation
- **WARNING (91-365 days):** Operation allowed, notify user to recalibrate soon
- **POOR (R² < 0.995):** Operation BLOCKED, immediate recalibration required
- **EXPIRED (> 365 days):** Operation BLOCKED, recalibration required

**Notification:**
- Email notification when status transitions to WARNING (HIGH priority)
- WhatsApp + Email when status transitions to POOR or EXPIRED (CRITICAL priority)

---

### 9.4 Recalibration Triggers

#### Mandatory Recalibration

Perform full calibration (15 trials, 5 setpoints × 3 repeats) when:

1. **Tubing Replacement**
   - New tubing has different elasticity
   - Must calibrate before returning to service

2. **Pump Head Serviced**
   - Roller adjustment or bearing maintenance
   - Affects mechanical advantage and slip

3. **Pressure Setting Changed**
   - PRV adjusted to different setpoint
   - Backpressure affects flow rate significantly

4. **Calibration Status = POOR or EXPIRED**
   - R² < 0.995 or > 365 days since last calibration
   - Safety interlock prevents operation

5. **Detected Dose Error > 10%**
   - Measured delivery consistently deviates from expected
   - Indicates calibration drift

#### Recommended Recalibration

Perform verification test (3 setpoints × 1 repeat = 3 trials) when:

1. **Quarterly Maintenance** (every 90 days)
   - Proactive check for calibration drift
   - If deviation < 7%, continue with existing calibration
   - If deviation ≥ 7%, perform full recalibration

2. **Stock Solution Concentration Change**
   - Viscosity/density affects flow
   - If ΔSG > 3%, recalibrate

3. **Seasonal Temperature Change > 15°C**
   - Tubing elasticity temperature-dependent
   - Winter → summer transition

4. **After Extended Non-Use (> 30 days)**
   - Tubing may have relaxed or deformed
   - Verify calibration before resuming operation

---

### 9.5 Calibration Workflow Integration

#### Pre-Calibration Checklist

**System State:**
- [ ] Winterization mode OFF
- [ ] Tank level above Low switch
- [ ] Main pump functional
- [ ] Test fixture installed (drip line + emitters matching typical zone)

**Equipment Ready:**
- [ ] Scale: 0.01 g resolution, tared and stable
- [ ] Graduated cylinder: 50-100 mL
- [ ] Volumetric flask: 100 mL (for SG measurement)
- [ ] Stock solution: Sufficient volume (>200 mL)
- [ ] Pressure gauge: Readable at injection point

**Software Preparation:**
- [ ] Home Assistant script created for automated timing (180s per trial)
- [ ] Data recording method ready (CSV template or input_number helpers)
- [ ] Modbus commands tested (start/stop pump at known speeds)

#### Calibration Day Procedure

**Refer to:** `/docs/fert_pump_cal_v2.md` for complete step-by-step procedure

**Summary:**
1. System setup (hydraulics, pressure, priming)
2. Measurement preparation (SG, temperature, scale)
3. Execute 15 trials (5 setpoints × 3 repeats)
   - **Revised setpoints for 100 RPM max:**
     - Setpoint 1: ~13 RPM → 2 mL/min
     - Setpoint 2: ~27 RPM → 4 mL/min
     - Setpoint 3: ~40 RPM → 6 mL/min
     - Setpoint 4: ~67 RPM → 10 mL/min
     - Setpoint 5: ~100 RPM → 15 mL/min
   - Speeds refined during calibration based on actual measurements
4. Data analysis (per-trial flow, per-setpoint statistics, curve fitting)
5. Verification (R² ≥ 0.995, residuals < ±5%)
6. Store coefficients in Home Assistant helpers
   - Slope: mL/min per RPM (typical: 0.13-0.17)
   - Intercept: mL/min at 0 RPM (typical: 0-0.5)
7. Generate calibration report

**Estimated Duration:** 2-3 hours per pump (including setup and analysis)

**Note:** Initial speed estimates assume ~0.15 mL per revolution for 3-roller peristaltic pump with 1×3mm silicone tubing. Actual values determined during calibration. Maximum operating speed limited to 100 RPM for tube longevity.

#### Post-Calibration Verification

**Immediate Checks:**
1. Verify coefficients stored correctly in helpers
2. Check calibration status sensor shows "VALID"
3. Test dose calculation with known values (dry run, no water)
4. Verify Modbus commands generate expected values

**7-Day Break-In Test:**
- Run 1 full fertigation cycle
- Measure actual delivered volume (if possible)
- Compare to expected: Should be within ±7%
- If deviation > 7%, consider re-run calibration (tubing may need break-in)

---

### 9.6 Calibration Data in V2 Eligibility Logic

#### No Direct Impact on Eligibility

Calibration status **does NOT affect** fertigation eligibility decisions in `window_check`:
- Eligibility based on: tank level, winterization, rolling window targets, soil moisture, rain
- Calibration quality affects dose accuracy, not whether to fertigate

#### Indirect Impact via Safety Interlock

**Pre-Execution Block:**

In `fert_prep` state or `script.start_dosing_pumps`:

```yaml
# Check calibration status before starting pumps
{% set pump1_status = states('sensor.fert_pump1_calibration_status') %}
{% set pump2_status = states('sensor.fert_pump2_calibration_status') %}
{% set pump3_status = states('sensor.fert_pump3_calibration_status') %}

{% if pump1_status in ['POOR', 'EXPIRED'] or 
      pump2_status in ['POOR', 'EXPIRED'] or 
      pump3_status in ['POOR', 'EXPIRED'] %}
  # BLOCK fertigation
  # Set state to error_calibration
  # Send CRITICAL notification
  # Log: "Fertigation blocked - pump calibration invalid"
{% endif %}
```

**WARNING Status Handling:**

If any pump shows "WARNING" (91-365 days old):
- Allow operation to proceed
- Send HIGH priority notification: "Pump N calibration due soon (X days old)"
- Log warning in cycle_event_log
- User has time to schedule recalibration

---

### 9.7 Dashboard Integration

#### Calibration Status Card

**Recommended Display:**

```yaml
type: entities
title: Pump Calibration Status
entities:
  - entity: sensor.fert_pump1_calibration_status
    name: Pump 1
  - entity: sensor.fert_pump2_calibration_status
    name: Pump 2
  - entity: sensor.fert_pump3_calibration_status
    name: Pump 3
  - type: divider
  - entity: input_datetime.fert_pump1_last_cal
    name: Pump 1 Last Cal
  - entity: input_datetime.fert_pump2_last_cal
    name: Pump 2 Last Cal
  - entity: input_datetime.fert_pump3_last_cal
    name: Pump 3 Last Cal
```

**Status Icon Colors:**
- VALID: Green checkmark
- WARNING: Yellow warning triangle
- POOR: Red X
- EXPIRED: Gray question mark

#### Calibration Details Card

**For each pump (expandable):**

```yaml
type: markdown
title: Pump 1 Calibration Details
content: >
  **Equation:** {{ state_attr('sensor.fert_pump1_calibration_status', 'equation') }}
  
  **R² Value:** {{ state_attr('sensor.fert_pump1_calibration_status', 'r_squared') }}
  
  **Calibration Date:** {{ state_attr('sensor.fert_pump1_calibration_status', 'calibration_date') }}
  
  **Test Pressure:** {{ state_attr('sensor.fert_pump1_calibration_status', 'pressure_bar') }} bar
  
  **Notes:** {{ state_attr('sensor.fert_pump1_calibration_status', 'notes') }}
```

---

### 9.8 Testing Calibration Integration

#### Unit Tests

1. **Dose Calculation Accuracy**
   - Input: Known dose, runtime, program
   - Expected: Correct flow rate and command value
   - Verify: Math matches hand calculation

2. **Light Program Boolean Behavior**
   - Test: Proportional (boolean OFF) vs. Full dose (boolean ON)
   - Verify: 0.5× vs. 1.0× multiplier applied correctly

3. **Calibration Status Sensor Logic**
   - Test: Various ages and R² values
   - Verify: Correct status (VALID/WARNING/POOR/EXPIRED)

4. **Command Clamping**
   - Test: Very low dose (expect cmd < 5%) and very high dose (expect cmd > 95%)
   - Verify: Commands clamped to safe range or error triggered

#### Integration Tests

1. **End-to-End Dose Delivery**
   - Setup: Calibrated pump, known zone configuration
   - Execute: Full fertigation cycle (all phases)
   - Measure: Actual delivered volume
   - Verify: Within ±7% of expected

2. **Calibration Expiration Blocking**
   - Setup: Manually set last_cal to > 365 days ago
   - Execute: Attempt fertigation
   - Verify: Blocked at fert_prep, error_calibration state, CRITICAL notification

3. **WARNING Status Notification**
   - Setup: Set last_cal to 95 days ago
   - Execute: Fertigation cycle
   - Verify: Cycle completes, HIGH notification sent, warning logged

#### Safety Tests

1. **Invalid Calibration Data**
   - Test: Set slope to 0 (division by zero risk)
   - Verify: Error handled gracefully, fertigation blocked

2. **Uncalibrated Pump**
   - Test: Fresh install, no calibration performed
   - Verify: Status = EXPIRED, operation blocked

3. **Pressure Mismatch**
   - Setup: Calibrate at 1.1 bar, operate at 0.8 bar (PRV failure)
   - Verify: Dose error > 10% detected, notification sent

---

### 9.9 Documentation References

#### Primary Documents

1. **Calibration Procedure:** `/docs/fert_pump_cal_v2.md`
   - Step-by-step procedure for calibration day
   - Equipment list, test matrix, acceptance criteria
   - Data analysis methods and curve fitting

2. **V2 Fertigation Design:** `/docs/fert_prog_design.md` (this document)
   - Section 9 (this section): Calibration integration
   - Section 4: Dose calculation logic
   - Section 11.2: Implementation checklist (Step 4 includes calibration verification)

3. **Architecture Document:** `/docs/architecture.md`
   - Section 4.3: Fertigation configuration helpers (calibration storage)
   - Section 5.5: Fertilizer control scripts (dose calculation)

4. **Implementation Roadmap:** `/docs/impl_roadmap.md`
   - Phase 2.3: Fertigation helpers (includes calibration storage entities)
   - Phase 3.3: Fertigation scripts (includes calibration-aware dose calculation)

#### ADRs (Architecture Decision Records)

- **ADR-011** (planned): V2 Fertigation Program Design Decisions
  - Should include: Calibration integration approach
  - Rationale: Why linear model, why operating pressure matters, recalibration triggers

---

### 9.10 Summary

**Key Integration Points:**

1. **Calibration Data Storage:** 9 helpers per pump (coefficients, metadata, notes)
2. **Status Monitoring:** Template sensor tracks calibration health (VALID/WARNING/POOR/EXPIRED)
3. **Dose Calculation:** Uses inverse calibration equation to convert flow → command
4. **Safety Interlocks:** Blocks operation if calibration POOR or EXPIRED
5. **Notifications:** Warns at 90 days, blocks at 365 days or poor R²
6. **Recalibration Triggers:** Defined mandatory and recommended scenarios

**Benefits of Calibration Integration:**

- **Accuracy:** Accounts for real-world pump behavior (not just nameplate specs)
- **Safety:** Prevents operation with invalid/expired calibration data
- **Traceability:** Full calibration history stored and accessible
- **Proactive Maintenance:** Early warnings before calibration expires
- **Agronomic Reliability:** Consistent nutrient delivery → healthy plants

**Next Steps:**
- Implement calibration storage helpers (Phase 2.3 V2)
- Create calibration status template sensors
- Integrate calibration checks into fertigation scripts (Phase 3.3)
- Test calibration blocking and warning notifications
- Perform initial pump calibrations per fert_pump_cal_v2.md

---

## 10. Dashboard & User Interface

### 10.1 New UI Elements Needed

**Per-Zone Configuration Section:**
```
Zone Name (dynamic friendly name)
├─ Current Season (dropdown: spring/summer/fall/winter)
├─ Soil Moisture Thresholds
│  ├─ Normal Min (slider: 0-100%)
│  ├─ Light Min (slider: 0-100%)
│  └─ Off Min (slider: 0-100%)
├─ Fertigation Settings
│  ├─ 14-Day Target (number: 0-14 events)
│  └─ Allow Full Dose in Light Program (toggle with warning)
└─ Last Fertigation Event (datetime display)
```

**System Status Section:**
```
Fertigation Status
├─ Currently Fertigating: [Zone Name or "None"]
├─ Per-Zone Event Counters
│  ├─ Zone 1: X / Y events (progress bar)
│  ├─ Zone 2: X / Y events (progress bar)
│  ├─ Zone 3: X / Y events (progress bar)
│  └─ Zone 4: X / Y events (progress bar)
└─ System Blocks Active
   ├─ Tank Level: OK / LOW (warning badge)
   └─ Winterization: Active / Inactive
```

**Zone Status Cards (Enhanced):**
```
[Zone Name]
├─ Current Program: off/light/normal/heavy
├─ Soil Moisture: XX% (or "sensor unavailable")
├─ Rain (24h): XX mm
├─ Fertigation Status:
│  ├─ Last Event: [datetime]
│  ├─ Hours Since: XX.X hours
│  ├─ Events (14d): X / Y (target)
│  └─ Next Eligible: [calculated datetime or "blocked"]
└─ Blocks Active (if any):
   ├─ Target Met
   ├─ Interval Too Short
   ├─ Soil Too Wet / Too Dry
   └─ Rain Too Heavy
```

### 10.2 Warning Indicators

**Full Dose in Light Program:**
- Icon: ⚠️ or mdi:alert-circle
- Color: Orange/amber
- Tooltip: "High concentration mode - only for salt-tolerant crops"

**Tank Level Low:**
- Icon: mdi:water-alert
- Color: Red
- Text: "Fertigation blocked - refill tank"

**Sensor Unavailable:**
- Icon: mdi:help-circle
- Color: Gray
- Text: "Using rain fallback (soil sensor unavailable)"

---

## 11. Testing Strategy

### 11.1 Unit Testing (Per Component)

**Helper Validation:**
- [ ] All 68 zone helpers load without errors
- [ ] All 9 system helpers/sensors load without errors
- [ ] Yamllint passes with zero warnings
- [ ] Entity IDs follow naming conventions

**Threshold Logic:**
- [ ] Verify threshold order: heavy < normal < light < off
- [ ] Test seasonal threshold selection (spring/summer/fall/winter)
- [ ] Validate fertigation range calculations (normal_min to off_min)

**Binary Sensors:**
- [ ] Zone active sensors respond to state changes
- [ ] Only activate during fert_dose_phase1 and fert_dose_phase2
- [ ] Deactivate properly when current_fertigation_zone resets

**History Stats:**
- [ ] Event counting increments correctly (1 per cycle)
- [ ] Rolling window updates continuously
- [ ] Persists through HA restart (after recorder init)

### 11.2 Integration Testing (Full Cycle)

**Fertigation Eligibility:**
- [ ] Tank level low blocks all zones
- [ ] Winterization blocks all zones
- [ ] Rolling window target met blocks specific zone
- [ ] 48-hour interval blocks specific zone
- [ ] Soil moisture out of range blocks specific zone
- [ ] Rain too heavy blocks specific zone (when sensor unavailable)

**Sequential Execution:**
- [ ] Multiple zones fertigate in sequence (not parallel)
- [ ] Inter-zone delays function correctly (30 seconds)
- [ ] Zone tracking updates properly (current_fertigation_zone)
- [ ] Event counters increment once per zone

**Dose Calculations:**
- [ ] Light program proportional dose (boolean OFF): 50% fertilizer
- [ ] Light program full dose (boolean ON): 100% fertilizer
- [ ] Normal program: 100% fertilizer
- [ ] Heavy program: 150% fertilizer

**Post-Phase Flushing:**
- [ ] Add 2-minute flush after dosing completes in phase 1
- [ ] Add 2-minute flush after dosing completes in phase 2
- [ ] Test flush execution (verify pumps OFF, main pump ON)
- [ ] Measure total cycle time (should be dosing_time + 4 min flush, NOT just dosing_time × 2)

### 11.3 Safety Testing

**Tank Level Pre-Check:**
- [ ] Enable low water level sensor
- [ ] Verify fertigation blocked for ALL zones
- [ ] Verify plain watering still allowed
- [ ] Verify notification sent

**Error Recovery:**
- [ ] Manual emergency stop resets zone tracking
- [ ] Low-low alarm during fertigation stops cycle
- [ ] ESP32 disconnect handles gracefully
- [ ] Power loss recovery (restart scenario)

**Sensor Fallback:**
- [ ] Disable soil moisture sensor
- [ ] Verify rain fallback activates
- [ ] Verify fertigation still functions correctly
- [ ] Dashboard shows "sensor unavailable" warning

### 11.4 Agronomic Validation

**Long-Term Monitoring:**
- [ ] Track actual fertigation frequency per zone
- [ ] Compare to seasonal targets (should average close)
- [ ] Monitor soil EC (electrical conductivity) for salt buildup
- [ ] Observe plant health indicators (growth rate, color, yield)

**Seasonal Adjustment:**
- [ ] User adjusts season selector (spring→summer)
- [ ] Verify threshold changes take effect
- [ ] Verify target frequency changes take effect
- [ ] Test transition behavior (events don't reset)

---

## 12. Implementation Checklist

### 12.1 Phase 3.3 Prerequisites

**Before starting Phase 3.3:**
- [ ] Phase 3.1 complete (Zone Control Scripts - ✅ DONE)
- [ ] Phase 3.2 complete (Pump Control Scripts - ✅ DONE)
- [ ] All 68 zone helpers added and validated
- [ ] All 9 system helpers/sensors added and validated
- [ ] Yamllint compliance verified
- [ ] Entity reference documentation updated

### 12.2 Implementation Order

**Step 1: Helper Implementation**
1. [ ] Add zone_helpers_additions_v2.yaml to zone_helpers.yaml
2. [ ] Create new file: fert_tracking.yaml (9 system entities)
3. [ ] Reload Home Assistant configuration
4. [ ] Verify all 77 new entities in Developer Tools → States
5. [ ] Set Zone 2 season to "spring" (test seasonal selection)

**Step 2: Template Sensors**
1. [ ] Implement 4× binary_sensor.zone_X_fertigation_active
2. [ ] Implement 4× sensor.zone_X_fert_events_14d (history_stats)
3. [ ] Test binary sensor activation (manual zone tracking)
4. [ ] Wait 24 hours, verify history_stats functioning

**Step 3: Eligibility Logic**
1. [ ] Implement tank level pre-check in window_check
2. [ ] Implement per-zone hard block checks
3. [ ] Implement soil moisture prevailing criteria
4. [ ] Implement rain fallback logic
5. [ ] Test each condition in isolation
6. [ ] Test combined condition logic

**Step 4: Dose Calculation**
1. [ ] Implement dosing duration calculation: 50% of plain watering runtime
2. [ ] Implement flush as separate 2-minute period (not included in dosing time)
3. [ ] Test all program modes (off/light/normal/heavy)
4. [ ] Verify heavy program: dose=1.0×, water varies by window mode

**Step 5: Sequential Execution**
1. [ ] Implement zone sequencing in fertigation script
2. [ ] Implement inter-zone delays
3. [ ] Implement zone tracking (current_fertigation_zone)
4. [ ] Test multi-zone fertigation (2+ zones)

**Step 6: Post-Phase Flushing**
1. [ ] Add 2-minute flush after fert_dose_phase1
2. [ ] Add 2-minute flush after fert_dose_phase2
3. [ ] Test flush execution (verify pumps off, main pump on)
4. [ ] Measure total cycle time (should be ~4 min longer)

**Step 7: Error Handling**
1. [ ] Identify all error scenarios (see Section 8.2)
2. [ ] Implement zone tracking reset on error states
3. [ ] Test each error scenario
4. [ ] Verify graceful recovery

**Step 8: Testing & Validation**
1. [ ] Execute full unit test suite (Section 10.1)
2. [ ] Execute full integration test suite (Section 10.2)
3. [ ] Execute safety test suite (Section 10.3)
4. [ ] Document any deviations or issues

### 12.3 Documentation Updates Required

**After implementation:**
- [ ] Update architecture.md Section 3 (State Machine) with V2 logic
- [ ] Update architecture.md Section 4 (Configuration) with new helpers
- [ ] Update architecture.md Section 5 (Scripts) with new fertigation logic
- [ ] Update impl_roadmap.md Phase 3.3 status
- [ ] Update test_scenarios.md with V2 test cases
- [ ] Update programming-notes.md with lessons learned
- [ ] Create ADR-011 (or next): "V2 Fertigation Program Design Decisions"

---

## 13. Migration from V1

### 13.1 Configuration Changes

**No Breaking Changes:**
- All existing helpers remain functional
- V1 logic can coexist during transition
- Gradual zone-by-zone migration possible

**New Configuration Required:**
- Add 68 zone helpers (one-time setup)
- Add 9 system helpers (one-time setup)
- Set initial season selectors for each zone
- Adjust soil moisture thresholds per crop (optional)

**User Action Required:**
- Review light program dose booleans (default OFF is safe)
- Adjust 14-day targets if needed (defaults are conservative)
- Monitor first few cycles, adjust thresholds based on observations

### 13.2 Transition Strategy

**Recommended Approach:**
1. Implement all V2 helpers and logic
2. Set all zones to winter (target = 0, disables V2 fertigation)
3. Test V2 logic in isolation on test bench
4. Enable one zone at a time (Zone 2 first - blueberries)
5. Monitor for 14 days, verify behavior matches expectations
6. Enable remaining zones sequentially
7. Remove or disable V1 logic once V2 validated

**Rollback Plan:**
- V1 logic remains in automations (disabled)
- Can re-enable V1 by setting all zone targets to 0
- No data loss (V1 last_fert_event helpers still maintained)

---

## 14. Known Limitations & Future Enhancements

### 14.1 Current Limitations

**Soil Moisture Sensors:**
- Phase 3 deferred (DFRobot SEN0600 RS-485 not yet installed)
- V2 works without sensors (rain fallback)
- Cannot use optimal moisture-based triggering until sensors installed

**Single Rain Sensor:**
- brightsky_rain_24h is system-wide (not per-zone)
- Assumes uniform rainfall across property
- Microclimate variations not captured

**Manual Season Selection:**
- User must update season selectors manually
- No automatic transition based on calendar dates
- Risk of forgetting to update (uses wrong thresholds)

**14-Day Window Only:**
- Cannot easily analyze longer trends (monthly, seasonal)
- history_stats limited to fixed duration
- Consider adding 30-day and 90-day counters for reporting

### 14.2 Future Enhancements

**Phase 3 (Soil Sensor Integration):**
- Install DFRobot SEN0600 sensors (3 zones max on RS-485 bus)
- Implement per-zone soil moisture readings
- Switch from rain fallback to moisture-primary mode
- Add moisture trending graphs to dashboard

**Phase 4 (Flow Rate Monitoring):**
- Add flow meter to main line
- Verify actual water delivery matches calculated runtime
- Detect zone valve failures (no flow when expected)
- Proportional dosing based on actual flow (more precise)

**Automation Enhancements:**
- Auto-suggest season changes based on calendar dates
- Notification when 14-day target at risk of not being met
- Weekly fertigation summary reports (actual vs target)
- Alert if soil EC rising (salt accumulation detection)

**Advanced Features:**
- Per-zone rain sensors (if microclimates significant)
- Integration with weather forecast (skip if rain predicted)
- Machine learning: optimize thresholds based on plant response
- Mobile app integration for remote monitoring

---

## 15. Conclusion

This V2 fertigation program design provides a robust, flexible, and safety-focused system for weather-responsive fertilizer application. The design prioritizes:

**Agronomic Soundness:**
- Evidence-based initial values for berry crops
- Seasonal adjustments matching plant growth stages
- Conservative defaults requiring explicit user enablement for aggressive options

**System Flexibility:**
- Per-zone configuration for all parameters
- Support for mixed cropping with different requirements
- Graceful degradation when sensors unavailable

**Safety & Reliability:**
- Multi-layer hard blocks prevent unsafe operation
- Tank level check before starting prevents mid-cycle failures
- Post-phase flushing ensures line clearing even if interrupted

**User-Friendly Operation:**
- Intuitive dashboard with clear status indicators
- Warning badges for non-default configurations
- Comprehensive testing strategy ensures reliable operation

**Future-Proof Architecture:**
- Designed for soil sensor integration (Phase 3)
- Extensible for flow monitoring (Phase 4)
- Foundation for advanced automation and ML optimization

The design is ready for Phase 3.3 implementation. All helper definitions are complete, logic flows documented, and testing strategies defined.

---

## Appendices

### Appendix A: Entity Reference Quick List

**Zone Helpers (68):**
```
input_boolean.zone_{1-4}_allow_full_dose_light_program (4)
input_number.zone_{1-4}_{season}_normal_moisture_min (16)
input_number.zone_{1-4}_{season}_light_moisture_min (16)
input_number.zone_{1-4}_{season}_off_moisture_min (16)
input_number.zone_{1-4}_{season}_fert_14d_target (16)
```

**System Helpers (9):**
```
input_text.current_fertigation_zone (1)
binary_sensor.zone_{1-4}_fertigation_active (4)
sensor.zone_{1-4}_fert_events_14d (4)
```

**Reused Existing (8):**
```
input_datetime.zone_{1-4}_last_fert_event (4)
input_select.zone_{1-4}_season (4)
```

### Appendix B: File Locations

**Home Assistant:**
```
packages/watering_helpers/zone_helpers.yaml (68 additions)
packages/watering_helpers/fert_helpers.yaml (add 9 tracking entities to existing ~90 entities)
packages/watering_scripts/fert_scripts.yaml (Phase 3.3 implementation)
packages/watering_state/state_machine.yaml (window_check updates)
```

**Documentation:**
```
docs/architecture.md (Sections 3, 4, 5 updates)
docs/impl_roadmap.md (Phase 3.3 tracking)
docs/test_scenarios.md (V2 test cases)
docs/programming-notes.md (lessons learned)
docs/architecture-decisions/ADR-011-v2-fertigation-design.md (new)
```

### Appendix C: Glossary

**Terms:**
- **Rolling Window:** Dynamic 14-day period that continuously updates (not calendar-based)
- **Hard Block:** Condition that absolutely prevents fertigation (no override)
- **Prevailing Criteria:** Conditions evaluated in priority order (soil moisture > rain)
- **Dose Multiplier:** Factor applied to base dose (0x, 0.5x, 1.0x, 1.5x)
- **Sequential Mode:** Zones fertigate one at a time (vs parallel = simultaneous)
- **Salt-Sensitive:** Crops susceptible to fertilizer burn at high concentrations
- **Field Capacity:** Maximum water soil can hold against gravity (100% = saturated)
- **Ericaceous:** Acid-loving plants (blueberries, azaleas, rhododendrons)

---

**Change Log**
- **2025-11-09**
  -Add Section 9, Calibration
* **2025-11-10**:
  - **Fertigation Timing and Dose Logic Corrections (Critical):**
    - **Dosing duration:** Corrected from "75% of base runtime" to "50% of plain watering runtime per phase"
      - Normal program (base=20min): Phase 1 = 10min dose + 2min flush, Phase 2 = 10min dose + 2min flush
      - Heavy single-window (base=20min): Phase 1 = 15min dose + 2min flush, Phase 2 = 15min dose + 2min flush
    - **2-minute flush:** Clarified as SEPARATE from dosing time (not included in dosing duration)
      - Total phase time = dosing_duration + 2 min flush
      - Flush runs with fertilizer pumps OFF, main pump ON
    - **Heavy program fertilizer dose:** Corrected to 1.0× (NOT 1.5×)
      - Water delivery: 1.5× (single window) or 1.0× morning + 0.5× evening (dual window)
      - Fertilizer dose: Always 1.0× to prevent salt buildup
      - Rationale: Heavy programs address water stress, not nutrient deficiency
    - **Pump selection:** Clarified as `input_number.zone_{1-4}_{season}_pump` (seasonal helper)
      - Each zone uses only ONE pump per cycle (not all 3 pumps)
      - Pump selection can change by season
    - **script.calculate_zone_fert_dose outputs:** Returns RPM and Time (dosing duration only, flush separate)
    - **Heavy program runtime logic:**
      - Single window: plain_watering_runtime = base × 1.5, dosing = 0.5 × plain_runtime = 0.75 × base per phase
      - Dual window: plain_watering_runtime = base × 1.0, dosing = 0.5 × plain_runtime = 0.5 × base per phase
  - **Files Updated:**
    - `docs/architecture.md` Section 5.6 - Complete rewrite with corrected logic
  - **Files Requiring Update:**
    - `docs/fert_prog_design.md` - Sections 5.1, 5.3, 5.4, 6, 7.1, 9.2, 11.2, 12.2, all examples
  - **Rationale:**
    - Original 75% figure was based on misunderstanding of split-dose timing
    - Heavy program should increase water for drought stress, not fertilizer (prevents salt accumulation)
    - Separating flush time improves clarity and safety (ensures lines always flushed)
    - Seasonal pump selection enables crop-specific fertilizer blends per growing stage
