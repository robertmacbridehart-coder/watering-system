# Watering System Architecture v1.9.0

**Date:** 2026-08-25
**Status:** Phase 7  
**Purpose:** Canonical architecture document for Home Assistant watering automation

---

## 1. System Overview

### 1.1 Core Philosophy
- **Logic Location:** All automation logic in Home Assistant
- **ESP32 Role:** Sensor/command relay only (no decision-making)
- **Safety:** Multi-layer interlocks (ESPHome hardware + HA automation + manual switches)
- **Flexibility:** All parameters configurable via UI (no YAML editing for adjustments)

### 1.2 Hardware Summary
- **Control:** ESP32 + 16-relay Modbus board (0x01)
- **Pumps:** 3× RS-485 stepper dosing pumps (0x02-0x04)
- **Sensors:** Float switches (GPIO33=Low, GPIO32=Low-Low); soil sensors — two documented options (wired RS-485 SEN0600 at 0x05-0x07, or wireless Ecowitt WH52 hybrid; see §9.1)
- **Weather (planned):** Ecowitt GW1200 gateway (868 MHz) + WS90 7-in-1 array + WH40 tipping-bucket rain gauge → local HA integration (see §9.4)
- **Power:** 12V LiFePO4 + solar, 24V cabinet for RS-485 (Relay 10 controlled)

---

## 2. State Machine Design

### 2.1 Master State Entity
```yaml
input_select.watering_system_state:
  # 15 options. Canonical definition lives in
  # home-assistant/packages/watering_helpers/config_helpers.yaml (the runtime
  # entity); this list must mirror it (see ADR-002 addendum, 2026-08-05).
  options:
    # --- Operational states ---
    - idle                  # Ready; nothing running
    - window_check          # Evaluating what needs to run; sets per-zone programs
    - preflight_check       # Safety checks before starting; branches plain vs fert
    - watering_plain        # Plain watering (no fertilizer)
    - fert_prep             # Preparing for fertigation
    - fert_dose_phase1      # First dose + partial watering
    - fert_dose_phase2      # Second dose + remaining water (or flush)
    - post_cycle_relief     # Pressure relief valve sequence
    # --- Control states ---
    - manual_override       # User has taken manual control
    - winterized            # Seasonal shutdown; cycles suppressed
    # --- Error states (latched; each halts the system for review/recovery) ---
    - error_e_stop          # Emergency stop latched (script.emergency_stop)
    - error_tank_low        # Low-low tank level detected, system halted
    - error_comms_lost      # Modbus/ESP32 communication failure
    - error_valve_interlock # Invalid valve configuration (R6/R7 issue), system halted
    - error_relay_state     # Relay verification failed, system halted
```

### 2.2 State Transition Logic

**IDLE → WINDOW_CHECK**
- Trigger: Time-based (morning/evening window opens)
- Condition: System not in error state
- Action: Evaluate what tasks are due (plain watering vs fertigation)

**WINDOW_CHECK → PREFLIGHT_CHECK**
- Trigger: Tasks identified (zones need watering)
- Action: 
  - Determine per-zone programs (off/light/normal/heavy)
  - Check fertigation schedule
  - Set target zone sequence

**PREFLIGHT_CHECK → WATERING_PLAIN or FERT_PREP**
- Conditions checked:
  - **Tank level — two-tier gate by cycle type:**
    - Plain watering gates on **Low-Low** (`binary_sensor.watering_system_low_low_water_level`,
      GPIO32) = OFF. Plain watering can be cut at any point with no side effects,
      so it only needs enough water to keep the pump wet.
    - Fertigation gates on the earlier **Low** warning
      (`binary_sensor.watering_system_low_water_level`, GPIO33) = OFF. A fert
      cycle must never be aborted mid-dose without completing its clean-water
      flush (nutrient left in the lines corrodes/clogs), so it demands the larger
      headroom of the Low switch to ensure the full dose **plus flush** can run.
    - Matches the implemented gate in `script.start_main_pump` (Low-Low) and the
      fert eligibility check below.
  - 24V cabinet available (if using RS-485 devices)
  - No existing watering in progress
- Branch:
  - If fertigation due AND Low switch OFF → FERT_PREP
  - Otherwise (Low-Low OFF) → WATERING_PLAIN

**WATERING_PLAIN → POST_CYCLE_RELIEF**
- Sequence:
  - Open bypass valve (R6), close fert line (R7)
  - Run zone sequence (parallel or sequential per config)
  - Close all zone valves
- Next: POST_CYCLE_RELIEF

**FERT_PREP → FERT_DOSE_PHASE1**
- Sequence:
  - Enable 24V cabinet (R10)
  - Wait 5s for stabilization
  - Close bypass valve (R6), open fert line (R7)
  - Verify valve positions
- Next: FERT_DOSE_PHASE1

**FERT_DOSE_PHASE1 → FERT_DOSE_PHASE2**
- Sequence (Normal/Heavy programs):
  - Open target zone valve (single zone only)
  - Start main pump (R1)
  - Wait for pressure stabilization (30s)
  - Start dosing pumps (RS-485 Modbus commands)
  - Run for 50% of target zone duration
  - Stop dosing pumps
  - Continue watering remaining 50%
- Sequence (Light program):
  - Same start, but 100% dose during first phase
- Next: FERT_DOSE_PHASE2

**FERT_DOSE_PHASE2 → POST_CYCLE_RELIEF**
- Sequence (Normal/Heavy):
  - Start dosing pumps again (second 50% dose)
  - Run for remaining 50% of target duration
  - Stop dosing pumps, stop main pump
  - Open bypass valve (R6), close fert line (R7)
  - Flush injection lines (5min clean water)
- Sequence (Light):
  - Open bypass valve, flush lines (5min)
- Next: POST_CYCLE_RELIEF

**POST_CYCLE_RELIEF → IDLE**
- Sequence:
  - Stop main pump (R1)
  - Close all zone valves
  - Open pressure relief valve (R9)
  - Wait configurable duration (default 120s)
  - Close pressure relief valve (R9)
  - Disable 24V cabinet (R10) if not needed for sensors
- Next: IDLE

**ANY STATE → ERROR_TANK_LOW**
- Trigger: GPIO32 (Low-Low switch) goes LOW
- Action:
  - Immediately stop main pump (R1)
  - Close all valves
  - Set error state
  - Send notification
- Recovery: Manual reset required after tank refilled

**ANY STATE → ERROR_COMMS_LOST**
- Trigger: Modbus communication timeout / ESP32 relays read `unavailable`.
- Action:
  - Attempt pump stop command (fail-fast if R1 unreadable — Phase 3.4 Part A)
  - Set error state
  - Send notification
- Recovery: Reactive automation `watering_safety_r1_comms_recovery` (Phase 3.4
  Part B, safety_automations.yaml) — on any R1–R7 reconnect it reads R1's live
  state: R1 back ON → escalate to `emergency_stop` (→ `error_e_stop`); R1 back
  OFF → close zones and clear to `idle`.

**ANY STATE → ERROR_E_STOP**
- Trigger: `script.emergency_stop` (manual button, safety automation, or comms
  recovery escalation).
- Action:
  - Turn OFF all 16 relays in parallel, verify, one repair cycle on failures
  - Send critical notification
  - **Latch** `error_e_stop` (deliberately NOT auto-cleared)
- Recovery: Manual — operator must clear the latch after resolving the fault.

**ANY STATE → ERROR_VALVE_INTERLOCK**
- Trigger: R6 XOR R7 flow-path interlock violated (both open, both closed, or a
  valve reads unavailable) as detected by the zone/pump scripts.
- Action: Set error state; the calling script aborts (`stop: error: true`).
- Recovery: Manual reset after the valve configuration is corrected.

**ANY STATE → ERROR_RELAY_STATE**
- Trigger: A relay fails post-command verification (pump did not energize /
  de-energize; relief valve did not open/close) after the settle delay + retry.
- Action: Set error state; emergency cleanup where applicable; abort.
- Recovery: Manual reset after the relay/board fault is resolved.

**IDLE ⇄ WINTERIZED**
- Enter: seasonal winterization procedure parks the system in `winterized`;
  cycles are suppressed while here. (The `input_boolean.system_winterized`
  control additionally gates cycle start; the state makes the shutdown explicit
  in the UI/logs.)
- Exit: de-winterization returns the system to `idle`.

#### Fertigation Eligibility (Evaluated in window_check)

**System-Wide Hard Blocks (Block ALL zones):**

1. **Tank Level Low (FIRST CHECK - NEW)**
   - Entity: `binary_sensor.watering_system_low_water_level`
   - Condition: Must be OFF (tank adequate)
   - Rationale: Ensures sufficient water for complete cycle + 4min flush

2. **Winterization Active**
   - Entity: `input_boolean.system_winterized`
   - Condition: Must be OFF

**Per-Zone Hard Blocks:**

3. **Rolling Window Target Met**
   - Check: `sensor.zone_X_fert_events_14d < input_number.zone_X_{season}_fert_14d_target`

4. **Interval Too Short**
   - Check: `(now() - input_datetime.zone_X_last_fert_event).hours >= 48`

**Prevailing Criteria (Per-Zone):**

- **Primary:** Soil moisture check (if sensor available)
  - Range: `normal_moisture_min <= moisture < off_moisture_min`
- **Fallback:** Rain check (if no sensor)
  - Check: `rain_24h < zone_X_{season}_rain_off_mm`

**Temperature:** Removed from fertigation triggers (still used for watering program selection)

---

## 3. Per-Zone Program States

### 3.1 Zone Program Entities
```yaml
input_select.zone_1_program:
  options: [off, light, normal, heavy, booster]

input_select.zone_2_program:
  options: [off, light, normal, heavy, booster]

input_select.zone_3_program:
  options: [off, light, normal, heavy, booster]

input_select.zone_4_program:
  options: [off, light, normal, heavy, booster]
```

`booster` (Phase 7) is a SYSTEM-set value only — `state_window_check` sets it to
place the heavy mid-interval top-up (0.5× base runtime) at the interval midpoint.
It is not an operator selection. At the DB write boundary it is recorded as
`weather_program='heavy'` with `program_multiplier=0.5` (see §3.3, §13.3.1), so
the `zone_runs` CHECK vocabulary stays `off/light/normal/heavy`.

**Master enable / cadence (Phase 7):** each zone also has
`input_boolean.zone_N_enabled` (hard on/off; OFF removes the zone from every
cycle) and `input_number.zone_N_watering_interval_days` (per-zone cadence, "water
on day N"). Both are consumed by `state_window_check` (§3.2). See §4.2.

### 3.2 Program Selection Logic (per zone)

Evaluated during **WINDOW_CHECK** state. An intensity (`wp`) is computed; two Phase 7
cadence layers then wrap it — the **enable gate** and the **interval/booster gate** — to
produce the final program. Intensity is *what* to water; cadence is *when*. (Closes
ADR-015 D-C, the deferred cadence gate, now that `sensor.zone_N_watering` supplies the
last-main-dose anchor.)

> **STATUS — intensity computation reworked by ADR-021 (ACCEPTED 2026-08-25), implementation
> HELD.** ADR-021 replaces the weather-only decision tree with a **moisture-primary** one (soil
> moisture drives the base intensity; weather/forecast only modulate). It is the design of
> record below, but **implementation waits for the soil-moisture hardware** (4× Ecowitt WH52 +
> 3× DFRobot SEN0600; see §9.1). Until then the **deployed** code runs the interim
> **weather-only tree**, which ADR-021 keeps as the **moisture-unavailable FALLBACK** (with the
> de-lagged temperature fix). The **cadence/booster layer (ADR-020) is UNCHANGED** — ADR-021
> only changes how `wp` is computed. Full rationale, sensor→zone mapping, pulse-poll, and
> thresholds live in ADR-021; decision recording is handled by ADR-018 (its `zone_decisions` /
> `decision_criteria` JSON, extended with the moisture inputs).

```python
# Pseudocode for zone program determination (state_window_check)
def select_zone_program(zone_id, active_window):
    # ---- intensity -> wp (ADR-021 moisture-primary; IMPLEMENTATION PENDING) ----
    # Ladder order (dry->wet needs less water): heavy > normal > light > off.
    thresholds = get_zone_thresholds(zone_id, season)   # moisture off/light/normal_min; rain; temp
    moisture   = sensor.zone_{id}_soil_moisture         # avg of sensors mapped to the zone (%)
    temp_high  = forecast_or_current_high               # DE-LAGGED: NOT temp_avg_high_3day

    if moisture is unavailable:                         # no sensor mapped / all unavailable
        wp = weather_only_tree(zone_id, season)         # FALLBACK (see below); fail-safe, not fail-heavy
    elif moisture >= thresholds.off_moisture_min:  wp = "off"   # wet-skip: soil already wet
    elif rain_now > 0:                             wp = "off"   # wet-skip: actively raining
    else:
        # moisture ladder -> base intensity
        if   moisture >= thresholds.light_moisture_min:  base = "light"
        elif moisture >= thresholds.normal_moisture_min: base = "normal"
        else:                                            base = "heavy"
        # weather modifiers: +/- ONE step (never escalate a moist zone straight to heavy)
        if rain_24h > thresholds.rain_light_mm:          base = step_down(base)      # recent rain
        if temp_high >= thresholds.temp_heavy_c:         base = step_up(base)        # hot -> up to heavy
        if temp_high <  thresholds.temp_normal_c:        base = step_down(base)      # cool -> down
        # forecast-rain downgrade: <=2 steps, FLOORED so a hot/dry zone still waters
        #   (heavy->light, normal->off). Gated on whole-day (->midnight) POP + volume.
        if forecast_pop_today > 80 and forecast_rain_today >= 5.0:
            base = downgrade(base, max_steps=2, heavy_floor="light")
        wp = base

    # weather_only_tree(zone, season)  == the FALLBACK and the interim deployed logic:
    #   if not weather_available:                              return "normal"   # D-A
    #   if rain_72h > rain_off_mm:                             return "off"
    #   if rain_24h > rain_light_mm:                           return "light"
    #   if temp_high >= temp_heavy_c and rain_72h < rain_min:  return "heavy"    # temp_high de-lagged
    #   if temp_high >  temp_normal_c:                         return "normal"
    #   return "light"

    # ---- cadence inputs ----
    enabled   = input_boolean.zone_{id}_enabled == "on"
    N         = input_number.zone_{id}_watering_interval_days      # "water on day N"
    last_main = sensor.zone_{id}_watering        # last MAIN dose (excludes booster)
    days_since = (now - last_main) in days       # never watered => treat as overdue
    due       = days_since >= N

    # heavy mid-interval BOOSTER (0.5x): fires on the target (evening) window from
    # N/2 onward, RETRYING each target window until it lands exactly once per
    # interval. Always the evening window (fallback morning if evening disabled);
    # no odd/even branch and no 'afternoon' window — day granularity absorbs the
    # parity. "Pending" = no booster recorded since the last main dose.
    mid             = N / 2
    target          = "evening" if evening_enabled else "morning"
    last_booster    = sensor.zone_{id}_last_booster   # last (heavy, 0.5x) run
    booster_pending = last_booster is None or last_booster < last_main
    in_band         = last_main is not None and mid <= days_since < N
    single_window   = morning_enabled ^ evening_enabled
    booster_slot = in_band and active_window == target and booster_pending \
                   and not (single_window and N == 1)   # N==1 single-window edge

    # ---- layer the gates (order matters) ----
    if not enabled:                      return "off"   # hard operator disable
    if wp == "off":                      return "off"   # rain gate; anchor NOT
                                                        # advanced -> stays overdue,
                                                        # retries until it waters
    if due:                              return wp      # MAIN dose
    if booster_slot and wp == "heavy":   return "booster"
    return "off"                                        # not due yet
```

**Notes (ADR-021 intensity).** Moisture is **primary**: the 2026-08-18 all-heavy failure
(cool, overcast, just rained) is resolved **by construction** — wet soil reads ≥ `off_min` →
`off`. **Recent** rain (`rain_24h`) only steps down (it does *not* hard-skip: DWD's recent-rain
is the signal that *missed* the local storm), while **current** rain hard-skips. The
temperature signal is **de-lagged** (forecast/current high, not the 3-day average — partially
supersedes ADR-004). The forecast-rain downgrade is capped at 2 steps and floored so a hot/dry
`heavy` zone still waters (never stranded on the hope of a shower). When no moisture sensor is
mapped to a zone, the **weather-only fallback** runs — fail-safe, never fail-`heavy`. Skip and
run decisions (with the full input vector + thresholds live at the time) are recorded via
**ADR-018**'s weather-observations DB (`zone_decisions` / `decision_criteria`, extended with the
moisture inputs) for season-scale tuning. *All of the above is HELD pending the
moisture hardware; the cadence notes below are LIVE (ADR-020).*

**Notes (ADR-020 cadence — LIVE).** A rained-off due day does not consume the interval (`last_main`
unchanged), so the zone retries every window until it actually waters. The
booster is decided by **re-evaluating** the weather at each target window from
the midpoint on — it fires only if the zone is still `heavy` there, and if it is
missed (override engaged, or evening temporarily disabled) it **retries** on a
later target window until it lands exactly once per interval (tracked via
`sensor.zone_N_last_booster` vs `last_main` — ADR-020 Fix #4b). **The main (full
1.0×) dose always has priority:** `due` is layered before `booster_slot` and the
booster band is capped at `days_since < N`, so once a zone is due the main fires
and any still-pending booster is abandoned — the retry can never override,
replace, or delay the full dose (the anchor excludes boosters, so retries never
push the main out). The `N==1` + single-window case (booster slot collides with
the main slot) schedules no booster; §3.3 delivers a single 1.5× dose instead.

### 3.3 Runtime Calculation (per zone)

Zone runtime is a **window-independent** function of the program (Phase 7). The
old same-day heavy split (morning `1.0×` + evening `0.5×`) was **retired** in
favour of a mid-interval booster: heavy's extra `0.5×` now falls at the interval
midpoint (§3.2), not on the same day. `calculate_zone_runtime` no longer varies
by window (the `window` argument is retained only for call-site compatibility).

#### Multipliers

```python
base_runtime = input_number.zone_{id}_base_runtime_min  # User configured

multipliers = {
    "off":     0.0,
    "light":   0.5,
    "normal":  1.0,
    "heavy":   1.0,   # MAIN dose; the extra 0.5x rides a separate 'booster' run
    "booster": 0.5,   # the heavy mid-interval top-up
}
```

**Heavy total across an interval** = `1.0×` (main, on day N) + `0.5×` (booster,
at N/2) = `1.5× base_runtime`, spread across the interval instead of one day.

#### N==1 single-window exception

When only one window is enabled **and** the zone's interval is daily (`N == 1`),
the booster slot collides with the main slot, so there is nowhere to place a
separate booster. In that one case `heavy` delivers the full `1.5× base_runtime`
as a single dose, and `state_window_check` schedules no booster.

#### Implementation

```python
def calculate_zone_runtime(zone_id, window):   # window unused (see above)
    base_runtime  = input_number.zone_{zone_id}_base_runtime_min
    program       = input_select.zone_{zone_id}_program
    interval_days = input_number.zone_{zone_id}_watering_interval_days
    single_window = input_boolean.enable_morning_window ^ input_boolean.enable_evening_window

    if program == "off":     return 0.0
    if program == "light":   return base_runtime * 0.5
    if program == "normal":  return base_runtime * 1.0
    if program == "booster": return base_runtime * 0.5
    if program == "heavy":
        if single_window and interval_days == 1:
            return base_runtime * 1.5   # N==1 single-window: full dose, no booster
        return base_runtime * 1.0       # MAIN; booster delivered separately
    return 0.0
```

#### Runtime Limits

- **Maximum per zone:** Configurable via `input_number.max_single_zone_runtime_min` (default: 120 min)
- **ESPHome backstop:** All relays have 120-minute auto-off timer
- **Calculation cap:** Runtime calculations capped at 120 minutes to prevent data corruption

---

## 4. Configuration Entities (Input Helpers)

### 4.1 System Configuration
```yaml
# Zone Sequencing
input_select.zone_sequencing_mode:
  options: [parallel, sequential]
  initial: parallel

# Watering Schedule
# NOTE (Phase 7): the system-wide input_number.watering_cycle_days was RETIRED
# in favour of a per-zone cadence — input_number.zone_N_watering_interval_days
# (see §3.2, §4.2). Frequency is now decided per zone, not globally.

input_datetime.morning_window_start:
  has_date: false
  has_time: true
  initial: "06:00:00"

input_datetime.morning_window_end:
  has_date: false
  has_time: true
  initial: "08:00:00"

input_datetime.evening_window_start:
  has_date: false
  has_time: true
  initial: "18:00:00"

input_datetime.evening_window_end:
  has_date: false
  has_time: true
  initial: "20:00:00"

input_boolean.enable_morning_window:
  initial: true

input_boolean.enable_evening_window:
  initial: true

# Safety Limits
input_number.max_single_zone_runtime_min:
  min: 1
  max: 180
  step: 1
  initial: 120
  unit: minutes

input_number.pressure_relief_duration_sec:
  min: 30
  max: 300
  step: 10
  initial: 120
  unit: seconds
```

### 4.2 Per-Zone Configuration
```yaml
# Example for Zone 1 (repeat pattern for zone_2, zone_3, zone_4)
input_number.zone_1_base_runtime_min:
  min: 1
  max: 120
  step: 1
  initial: 30
  unit: minutes

# Seasonal thresholds (spring example, repeat for summer/fall/winter)
input_number.zone_1_spring_rain_off_mm:
  min: 0
  max: 100
  step: 1
  initial: 20
  unit: mm

input_number.zone_1_spring_rain_light_mm:
  min: 0
  max: 50
  step: 1
  initial: 10
  unit: mm

input_number.zone_1_spring_rain_min_mm:
  min: 0
  max: 20
  step: 1
  initial: 5
  unit: mm

input_number.zone_1_spring_temp_heavy_c:
  min: 15
  max: 40
  step: 1
  initial: 28
  unit: °C

input_number.zone_1_spring_temp_normal_c:
  min: 10
  max: 35
  step: 1
  initial: 22
  unit: °C
```
**Note:** Generic zone numbering (zone_1, zone_2, zone_3, zone_4) allows flexibility if crops change. 
User can customize display names in Home Assistant UI without breaking automations.

**ADR-021 additions (design of record; implementation HELD):**
- **Per-zone/season moisture thresholds** already exist: `input_number.zone_N_{season}_{off,light,normal}_moisture_min` (%). These become the primary §3.2 ladder inputs.
- **All threshold helpers** (`zone_N_{season}_*`, weather **and** moisture) → **pure RestoreEntity** (drop `initial:`) so operator tuning survives restart (ADR-017 pattern; closes follow-up #4(e)).
- **New wireless-sensor zone tags:** `input_select.moisture_wireless_N_zone` (one per movable WH52), friendly options Raspberries/Blueberries/Vegetables/Unassigned. Consumed by the per-zone `sensor.zone_N_soil_moisture` averaging (§9.1). *(Tag mechanism deferred until the sensors are set up — ADR-021.)*

### 4.2.6 Fertigation Zone Configuration

#### Light Program Dose Control

Controls fertilizer dose during light watering programs (50% runtime).
```yaml
input_boolean:
  zone_1_allow_full_dose_light_program:
    name: "{{states('input_text.zone_1_friendly_name')}} - Allow Full Dose in Light Program"
    icon: mdi:beaker-alert
    initial: false  # Conservative default
  # Repeat for zones 2, 3, 4
```

**Logic:**
- `false` (default): 50% fert in 50% water (proportional, same concentration)
- `true` (user-enabled): 100% fert in 50% water (full dose, 2x concentration)

**Warning:** Only enable for salt-tolerant crops (raspberries, vegetables). Keep OFF for blueberries/azaleas.

#### Soil Moisture Thresholds

**Pattern:** 3 thresholds × 4 seasons × 4 zones
```yaml
input_number:
  zone_X_SEASON_normal_moisture_min:  # Initial: 35-45% depending on season
  zone_X_SEASON_light_moisture_min:   # Initial: 50-60%
  zone_X_SEASON_off_moisture_min:     # Initial: 70-80%
```

**Initial Values (Berry-Optimized):**

| Season | Normal | Light | Off | Fert Range |
|--------|--------|-------|-----|------------|
| Spring | 40% | 55% | 75% | 40-75% |
| Summer | 45% | 60% | 70% | 45-70% (tightest) |
| Fall | 40% | 55% | 75% | 40-75% |
| Winter | 35% | 50% | 80% | 35-80% (widest) |

#### Fertigation 14-Day Targets (16 helpers)

**Pattern:** 4 seasons × 4 zones
```yaml
input_number:
  zone_X_SEASON_fert_14d_target:  # 0-14 events per rolling window
```

**Initial Values:**
- Spring: 5 events (~2.5×/week)
- Summer: 7 events (~3.5×/week)
- Fall: 3 events (~1.5×/week)
- Winter: 0 events (dormant)

### 4.3 Fertigation Configuration
```yaml
# Schedule
input_number.fert_cycle_days:
  min: 1
  max: 30
  step: 1
  initial: 7
  unit: days

input_datetime.last_fert_zone_1:
  has_date: true
  has_time: false

input_datetime.last_fert_zone_2:
  has_date: true
  has_time: false

input_datetime.last_fert_zone_3:
  has_date: true
  has_time: false

input_datetime.last_fert_zone_4:
  has_date: true
  has_time: false

# Dosing amounts per zone, per pump (in mL total dose)
# Backend calculates mL/min based on calibration curve and zone runtime

input_number.fert_zone_1_pump1_dose_ml:
  min: 0
  max: 500
  step: 1
  initial: 60
  unit: ml

input_number.fert_zone_1_pump2_dose_ml:
  min: 0
  max: 500
  step: 1
  initial: 0  # Disabled by default
  unit: ml

input_number.fert_zone_1_pump3_dose_ml:
  min: 0
  max: 500
  step: 1
  initial: 0  # Disabled by default
  unit: ml

# [Repeat for zones 2, 3, 4]

# Calculated/Display sensors (template sensors)
sensor:
  - platform: template
    sensors:
      fert_zone_1_pump1_rate_ml_per_min:
        friendly_name: "Zone 1 Pump 1 Calculated Rate"
        unit_of_measurement: "ml/min"
        value_template: >
          {% set dose = states('input_number.fert_zone_1_pump1_dose_ml') | float %}
          {% set runtime = states('input_number.zone_1_base_runtime_min') | float %}
          {% set program = states('input_select.zone_1_program') %}
          {% set multipliers = {'off': 0.0, 'light': 0.5, 'normal': 1.0, 'heavy': 1.5} %}
          {% set actual_runtime = runtime * multipliers.get(program, 1.0) %}
          {% if actual_runtime > 0 %}
            {{ (dose / actual_runtime) | round(2) }}
          {% else %}
            0
          {% endif %}
      
      fert_zone_1_pump1_command:
        friendly_name: "Zone 1 Pump 1 Command Value"
        unit_of_measurement: "%"
        value_template: >
          {% set required_flow = states('sensor.fert_zone_1_pump1_rate_ml_per_min') | float %}
          {% set slope = states('input_number.fert_pump1_cal_slope') | float %}
          {% set intercept = states('input_number.fert_pump1_cal_intercept') | float %}
          {% if slope > 0 %}
            {{ ((required_flow - intercept) / slope) | round(1) }}
          {% else %}
            0
          {% endif %}

      # [Repeat for all zone/pump combinations]

# Flush duration
input_number.fert_flush_duration_min:
  min: 1
  max: 15
  step: 1
  initial: 5
  unit: minutes
```

### 4.4 Fertilizer Pump Calibration

**Full Procedure:** `/docs/fert_pump_cal_v2.md`

**Purpose:** Establish flow vs. command relationship for each RS-485 peristaltic pump to enable accurate dose delivery.

**Calibration Storage (per pump):**
```yaml
# Calibration coefficients (linear model: q = a×cmd + b)
input_number.fert_pump1_cal_slope:
  min: 0
  max: 1
  step: 0.0001
  mode: box
  unit_of_measurement: "mL/min per %"

input_number.fert_pump1_cal_intercept:
  min: -5
  max: 5
  step: 0.01
  mode: box
  unit_of_measurement: "mL/min"

input_number.fert_pump1_cal_r2:
  min: 0
  max: 1
  step: 0.0001
  mode: box

input_datetime.fert_pump1_last_cal:
  has_date: true
  has_time: false

input_number.fert_pump1_cal_pressure:
  min: 0
  max: 3
  step: 0.1
  unit_of_measurement: "bar"

input_text.fert_pump1_cal_notes:
  max: 200

# [Repeat for pump2 and pump3]
```

**Runtime Dose Calculation**
```Python
# Given:
target_dose_ml = input_number.fert_zone_1_pump1_dose_ml
zone_runtime_min = calculated based on program (light/normal/heavy)

# Calculate required flow rate:
required_flow_ml_per_min = target_dose_ml / zone_runtime_min

# Convert to pump command using calibration curve:
# q = a×cmd + b  →  cmd = (q - b) / a
slope = input_number.fert_pump1_cal_slope
intercept = input_number.fert_pump1_cal_intercept

pump_command = (required_flow_ml_per_min - intercept) / slope

# Send to pump via Modbus
```

**Calibration Template Sensors**
```yaml
sensor:
  - platform: template
    sensors:
      fert_pump1_calibration_status:
        friendly_name: "Pump 1 Calibration Status"
        value_template: >
          {% set r2 = states('input_number.fert_pump1_cal_r2') | float %}
          {% set date = states('input_datetime.fert_pump1_last_cal') %}
          {% set days_old = (now() - as_datetime(date)).days if date != 'unknown' else 999 %}
          {% if r2 < 0.995 %}
            POOR (R²={{ r2 }})
          {% elif days_old > 90 %}
            EXPIRED ({{ days_old }} days old)
          {% elif days_old > 60 %}
            WARNING ({{ days_old }} days old)
          {% else %}
            VALID ({{ days_old }} days old)
          {% endif %}
        attribute_templates:
          equation: "q = {{ states('input_number.fert_pump1_cal_slope') }}×cmd + {{ states('input_number.fert_pump1_cal_intercept') }}"
          r_squared: "{{ states('input_number.fert_pump1_cal_r2') }}"
          calibration_date: "{{ states('input_datetime.fert_pump1_last_cal') }}"
          pressure_bar: "{{ states('input_number.fert_pump1_cal_pressure') }}"
          notes: "{{ states('input_text.fert_pump1_cal_notes') }}"

      # [Repeat for pump2 and pump3]
```
### 4.5 Sensor Reading Configuration
```yaml
input_number.soil_sensor_read_interval_hours:
  min: 0.5
  max: 24
  step: 0.5
  initial: 2
  unit: hours

input_number.soil_sensor_stabilization_sec:
  min: 1
  max: 30
  step: 1
  initial: 5
  unit: seconds
```

### 4.6 Season Selection
```yaml
input_select.season:
  options: [spring, summer, fall, winter]
  initial: spring
```

### 4.7 Cycle Event Log

```yaml
input_text:
  cycle_event_log:
    name: "Cycle Event Log"
    max: 255
    initial: ""
```

**Purpose:** Track non-critical events (warnings, self-repairs) during watering cycles for end-of-cycle email summary.

**Format:** Timestamped entries (DD/MM HH:MM:SS) separated by newlines.

**Lifecycle:**
- **Cleared:** At preflight_check (start of each cycle)
- **Populated:** During cycle by scripts (Phases 3.1, 3.2, 3.3)
- **Sent:** At post_cycle_relief via email notification

**Limitations:**
- 255 character hard limit (Home Assistant restriction)
- Capacity: ~4-5 error messages before truncation
- **Known Issue:** Implementation missing newline separators between entries
- **Status:** Requires redesign before Phase 9 (notification integration)

**Usage Example:**
```yaml
- variables:
    timestamp: "{{ now().strftime('%d/%m %H:%M:%S') }}"
    new_entry: "{{ timestamp }} - Valve configuration corrected"
    current_log: "{{ states('input_text.cycle_event_log') }}"
- service: input_text.set_value
  target:
    entity_id: input_text.cycle_event_log
  data:
    value: "{{ current_log }}{{ new_entry }}\n"
```

#### Fertigation Tracking

**Current Fertigation Zone:**
```yaml
input_text:
  current_fertigation_zone:
    name: "Current Fertigation Zone"
    max: 4
    initial: "0"  # "0"=none, "1"-"4"=zone number
```

**Zone Fertigation Active Sensors:**
```yaml
binary_sensor:
  zone_X_fertigation_active:  # Template sensor, 4 total
    # ON during fert_dose_phase1 and fert_dose_phase2 when current_zone matches
```

**Rolling Window Event Counters:**
```yaml
sensor:
  zone_X_fert_events_14d:  # history_stats sensor, 4 total
    # Counts events in rolling 14-day window
    # Requires Home Assistant recorder
```

---

## 5. Safety Interlocks

### 5.1 Hardware-Level (ESPHome)
**Already Implemented:**
- Relay auto-off timers (120min max)
- `ALWAYS_OFF` restore mode (relays off on boot)
- 24V enable scripts prevent Modbus traffic without power

**To Verify:**
- GPIO32/33 are `INPUT_PULLUP` with debounce
- Relay 1 (pump) has hardware timeout in template switch

### Section 5.1A ESPHome Relay Control Architecture
**Hardware-Level Safety (Already Implemented):**

All relay template switches have 120min auto-off timers
Auto-off timers properly cancelled when manually turned off
24V cabinet manual control stops auto-off timer (no conflicts)
All raw Modbus coils marked internal: true
All raw Modbus coils use ALWAYS_OFF restore mode

**Template Switch Naming**
ESPHome Internal IDs (for use within ESPHome YAML):

relay_pump_main - Main irrigation pump
relay_zone_1 through relay_zone_4 - Zone valves
relay_fert_bypass_valve - Fertilizer bypass
relay_fert_line_valve - Fertilizer injection line
relay_pressure_relief - Pressure relief valve
relay_24v_cabinet - 24V cabinet enable
relay_8, relay_11 through relay_16 - Reserved

**Home Assistant Entity IDs (for use in automations/scripts):**

switch.watering_system_relay_1_main_pump - Main irrigation pump
switch.watering_system_relay_2_zone_1 through switch.watering_system_relay_5_zone_4 - Zone valves
switch.watering_system_relay_6_fert_bypass - Fertilizer bypass
switch.watering_system_relay_7_fert_line - Fertilizer injection line
switch.watering_system_relay_9_pressure_relief - Pressure relief valve
switch.watering_system_relay_10_24v_cabinet - 24V cabinet enable
switch.watering_system_relay_8, switch.watering_system_relay_11 through switch.watering_system_relay_16 - Reserved

**ESPHome Names (displayed in Home Assistant UI):**

"Relay 1 - Main Pump"
"Relay 2 - Zone 1" through "Relay 5 - Zone 4"
"Relay 6 - Fert Bypass"
"Relay 7 - Fert Line"
"Relay 9 - Pressure Relief"
"Relay 10 - 24V Cabinet"
"Relay 8", "Relay 11" through "Relay 16"

**Icons:**

mdi:pump - Main pump
mdi:sprinkler-variant - Zone valves
mdi:valve - Control valves (bypass, fert line, pressure relief)
mdi:power - 24V cabinet enable

**Architecture:**

Raw coils (relay_X_raw) are internal Modbus switches
Safe scripts (turn_on/off_relay_X_safe) handle 24V power sequencing
ON sequence scripts (relay_X_on_sequence) provide 120min auto-off timers
Template switches (relay_X) are user-facing with proper timer management

## Section 5.2: Automation-Level (Home Assistant) (CORRECTED)

**Independent Safety Monitors** (separate automations, always running):

### Tank Level Safety
```yaml
automation:
  - alias: "Safety - Tank Level Emergency Stop"
    trigger:
      - platform: state
        entity_id: binary_sensor.watering_system_low_low_water_level
        to: 'on'
        # Note: Sensor has 5s delayed_on filter, so this triggers after sustained low level
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.watering_system_relay_1_main_pump
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'error_tank_low'
      - service: notify.mobile_app
        data:
          title: "WATERING SYSTEM ALARM"
          message: "Tank Low-Low level reached. System stopped."
```

**Note:** Float switches use multi-stage filtering:
- `delayed_on_off: 100ms` - Debounces contact bounce
- `delayed_on: 5s` - Prevents splash false alarms
- `delayed_off: 30s` - Prevents sloshing from clearing alarm prematurely

### Modbus Communication Watchdog
```yaml
automation:
  - alias: "Safety - Modbus Communication Watchdog"
    trigger:
      - platform: state
        entity_id: binary_sensor.watering_system_status  # ESP32 online status
        to: 'unavailable'
        for:
          seconds: 10
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'error_comms_lost'
      - service: notify.mobile_app
        data:
          title: "WATERING SYSTEM ALARM"
          message: "Lost communication with ESP32. Check hardware."
```

### Zone Runtime Limit
```yaml
automation:
  - alias: "Safety - Zone Runtime Exceeded"
    trigger:
      - platform: state
        entity_id: 
          - switch.watering_system_relay_2_zone_1
          - switch.watering_system_relay_3_zone_2
          - switch.watering_system_relay_4_zone_3
          - switch.watering_system_relay_5_zone_4
        to: 'on'
        for:
          minutes: "{{ states('input_number.max_single_zone_runtime_min') | int }}"
    action:
      - service: switch.turn_off
        target:
          entity_id: "{{ trigger.entity_id }}"
      - service: notify.mobile_app
        data:
          title: "WATERING SYSTEM WARNING"
          message: "Zone {{ trigger.to_state.name }} exceeded max runtime and was stopped."
```

---

## Section 5.3: User-Level Controls

### Emergency Stop Script

> **Superseded — see the implemented `emergency_stop`** in
> `home-assistant/packages/watering_scripts/watering_safety_scripts.yaml`. The early
> sketch here (turn off R1–R7, set `idle`, `notify.mobile_app`) does NOT match the
> built behaviour: the real script turns off **all 16 relays** with verification + one
> repair cycle, sends a **critical notification**, and **latches `error_e_stop`** (never
> auto-returns to `idle`) so the system can't silently restart. `error_e_stop` is then
> finalized for the DB by the `on_error_e_stop` automation (ADR-015 D-D).

### Manual Override Mode

> **Superseded — see ADR-015 D-F (revised).** `input_boolean.manual_override_active`
> is the control; the `manual_override` state mirrors it. Engagement is a **guard, not
> an auto-abort**: from `idle` it parks in `manual_override`; from any operational
> state it is **rejected** (boolean reverted + "stop the cycle first" notification);
> from an `error_*` state it warns + requires acknowledgement, then engages. Turning
> the boolean OFF returns to `idle`. The system never silently aborts a running cycle
> to satisfy an override — the user must stop it first (`emergency_stop` today; a
> safe-stop UX button later). `input_boolean.system_winterized` / the `winterized`
> state follow the same guard pattern.

### 5.4 Zone Control Scripts

**Location:** `home-assistant/packages/watering_scripts/zone_scripts.yaml`

#### script.open_zone
Opens a single zone valve after safety checks.

**Parameters:**
- `zone_id` (required, 1-4): Which zone to open

**Safety Checks:**
1. Pump running (R1 = on)
2. Valid flow path: (R6 on AND R7 off) OR (R6 off AND R7 on)

**Error States:**
- `error_relay_state` - Pump off or unavailable
- `error_valve_interlock` - Invalid R6/R7 configuration

#### script.close_zone
Closes a single zone valve.

**Parameters:**
- `zone_id` (required, 1-4): Which zone to close

#### script.close_all_zones
Closes all four zone valves in parallel.

#### script.calculate_zone_runtime
Calculates appropriate runtime for a zone based on program and window.

**Parameters:**
- `zone_id` (required, 1-4): Which zone
- `window` (required, 'morning' or 'evening'): Which watering window

**Returns:** Runtime in minutes (float)

**Uses:** Home Assistant `response_variable` feature

#### script.run_zone_sequence
Executes watering for all active zones in configured sequence.

**Parameters:**
- `window` (required, 'morning' or 'evening'): Which watering window

**Modes:**
- **Parallel:** All zones open simultaneously, each closes at its own runtime
- **Sequential:** Zones run one at a time with 30-second inter-zone delays

**Zone Selection:** Only zones with runtime > 0 are watered (program = 'off' skipped)

### 5.5 Pump Control Scripts

**Location:** `home-assistant/packages/watering_scripts/pump_scripts.yaml`

#### script.start_main_pump
Starts main pump with comprehensive safety checks, self-healing, and pressure stabilization.

**Safety Checks (Pre-startup):**
1. **Tank level:** Low-low switch must be OFF
   - Checks: `binary_sensor.watering_system_low_low_water_level`
   - Error: Sets `error_tank_low` if tank empty
2. **Pressure relief:** R9 must be closed
   - Checks: `switch.watering_system_relay_9_pressure_relief`
   - Self-healing: Attempts to close if found open (see below)
3. **Valve interlock:** R6 XOR R7 (exactly one flow path valve open)
   - Checks: `switch.watering_system_relay_6_fert_bypass` and `switch.watering_system_relay_7_fert_line`
   - Error: Sets `error_valve_interlock` if both ON or both OFF
   - **Pump-start check only (ADR-016):** both-OFF is invalid *here* because a cycle
     is committing to water, but both-OFF is the intended **RESTING** state — valves
     rest closed (valve discipline). `state_watering_plain` opens R6 before this check
     runs; `post_cycle_relief` / `safe_shutdown` close both valves on the way out.
4. **Error state protection:** Aborts if system already in error state

**Self-Healing:** If pressure relief valve found open:
1. Logs warning to cycle_event_log
2. Calls `script.close_pressure_relief`
3. Waits 500ms for state propagation (prevents race condition)
4. Re-assesses valve state
5. If still open → Sets `error_valve_interlock` and aborts
6. If closed → Logs success and continues

**Startup Sequence:**
1. Enable 24V cabinet (R10) if not already on
2. Command pump relay (R1) ON
3. Wait 3 seconds for relay verification (R10 2s stabilization + coil 1s response)
4. Verify pump relay energized
5. Wait 30 seconds for pressure stabilization (interruptible if pump fails)

**Error Handling:**
- Relay verification failure → Sets `error_relay_state`
- Tank low-low → Sets `error_tank_low`
- Invalid valve configuration → Sets `error_valve_interlock`
- All errors logged to both system_log and cycle_event_log

**Script Mode:** `single` (sequential execution, no interruption)

---

#### script.stop_main_pump
Stops main pump with relay verification and aggressive self-repair retry loop.

**Shutdown Sequence:**
1. Command pump relay (R1) OFF
2. Wait 3 seconds for relay de-energization
3. Verify pump relay de-energized

**Self-Healing (Aggressive Retry):**
If pump relay doesn't de-energize:
1. Log warning to cycle_event_log
2. Enter retry loop:
   - Re-send stop command every 2 seconds
   - Re-verify relay state after each attempt
   - Log every 10th attempt (every 20 seconds) to prevent log spam
   - Continue for up to 120 minutes
3. Exit loop when pump stops OR hardware timer triggers

**Hardware Backstop:** ESPHome auto-off timer at 120 minutes provides ultimate safety

**Error Handling:**
- If pump still running after self-repair → Sets `error_relay_state`
- Logs all retry attempts to system_log and cycle_event_log

**Script Mode:** `restart` (latest stop request kills previous attempt and starts fresh)
- **Critical:** Ensures safety automations can always override in-progress stop attempts

---

#### script.open_pressure_relief
Opens pressure relief valve for configured duration with validation, then closes.

**Pre-Operation Check:**
1. Verify pump is OFF
   - If pump running: Calls `script.stop_main_pump` first
   - Waits for stop completion (3s verification)
   - Aborts if pump won't stop

**Duration Validation:**
- Source: `input_number.pressure_relief_duration_sec`
- Bounds: 30-300 seconds (enforced)
- Default: 120 seconds (if helper unavailable or invalid)
- Logs warning if validation triggers

**Operation Sequence:**
1. Command pressure relief valve (R9) ON
2. Wait 3 seconds for relay verification
3. Verify valve opened (abort if fails)
4. Wait configured duration (validated, 30-300s)
5. Command relief valve OFF
6. Wait 3 seconds for relay verification
7. Verify valve closed (abort if fails)

**Error Handling:**
- Pump won't stop → Sets `error_relay_state`
- Relief valve verification failure (open or close) → Sets `error_relay_state`
- Invalid duration → Uses safe default (120s), logs warning

**Script Mode:** `single`

---

#### script.close_pressure_relief
Immediately closes pressure relief valve with verification.

**Operation:**
1. Command pressure relief valve (R9) OFF
2. Wait 3 seconds for relay de-energization
3. Verify valve closed

**Error Handling:**
- Relay verification failure → Sets `error_relay_state`

**Idempotency:** Safe to call when valve already closed (no state change)

**Script Mode:** `single`

---

**Timing Standards:**
- **3-second relay verification:** All relay operations (R10 2s stabilization + coil 1s response)
- **30-second pressure stabilization:** After pump start (interruptible)
- **500ms propagation delay:** After calling relay control subscripts

**Dual Logging:**
- `system_log.write`: Permanent debugging record (warnings/errors)
- `cycle_event_log`: Per-cycle user summary (warnings/errors with timestamps)
- Format: "DD/MM HH:MM:SS - {event description}"

**Self-Healing Philosophy:**
- **Single-attempt:** Pressure relief valve (low-risk repair)
- **Aggressive retry:** Pump stop (high-risk failure, requires persistent correction)
- All repairs logged before and after verification
- Hardware timer provides ultimate safety backstop for runaway pump

## 5.6 Fertilizer Control Scripts

**File Locations:**
- `home-assistant/packages/watering_scripts/fert_scripts.yaml` - Operational fertigation scripts
- `home-assistant/packages/watering_scripts/fert_cal_scripts.yaml` - Calibration procedures

**Integration:** Works with V2 fertigation program design (rolling 14-day windows, multi-condition eligibility)

---

### 5.6.1 Operational Fertigation Scripts

**File:** `home-assistant/packages/watering_scripts/fert_scripts.yaml`

#### script.check_zone_fert_eligibility

**Purpose:** Multi-condition evaluation to determine if a zone is eligible for fertigation

**Inputs:**
- `zone_id` (1-4)

**Checks Performed (in order):**
1. **Tank level** - `binary_sensor.watering_system_low_water_level` must be OFF (system-wide block)
2. **Winterization** - `input_boolean.system_winterized` must be OFF (system-wide block)
3. **Rolling window target** - `sensor.zone_X_fert_events_14d < input_number.zone_X_{season}_fert_14d_target`
4. **48-hour interval** - Hours since `input_datetime.zone_X_last_fert_event ≥ 48`
5. **Soil moisture or rain fallback** - Within favorable range for fertigation

**Returns (via response_variable):**
- `eligible`: boolean (true/false)
- `block_reason`: string (e.g., "tank_low", "target_met", "too_soon", "moisture_high")

**Called From:** `window_check` state to determine which zones fertigate vs plain water

---

#### script.calculate_zone_fert_dose

**Purpose:** Calculate pump RPM and dosing duration for a zone's fertigation phase

**Inputs:**
- `zone_id` (1-4)
- `phase` (1 or 2)

**Calculation Logic:**

1. **Get pump selection from seasonal helper:**
   ```yaml
   {% set season = states('input_select.zone_' ~ zone_id ~ '_season') %}
   {% set pump_id = states('input_number.zone_' ~ zone_id ~ '_' ~ season ~ '_pump') | int %}
   ```

2. **Get base dose and program:**
   ```yaml
   {% set base_dose = states('input_number.zone_' ~ zone_id ~ '_' ~ season ~ '_dose_ml') | float %}
   {% set program = states('input_select.zone_' ~ zone_id ~ '_program') %}
   ```

3. **Calculate fertilizer dose for this phase:**
   ```yaml
   # Dose multipliers by program
   {% set dose_multipliers = {
     'off': 0.0,
     'light': 1.0 if is_state('input_boolean.zone_' ~ zone_id ~ '_allow_full_dose_light_program', 'on') else 0.5,
     'normal': 1.0,
     'heavy': 1.0
   } %}
   {% set total_dose = base_dose * dose_multipliers[program] %}
   {% set phase_dose = total_dose * 0.5 %}  # Split 50/50 between phases
   ```

4. **Calculate plain watering runtime (what non-fert watering would be):**
   ```yaml
   {% set base_runtime = states('input_number.zone_' ~ zone_id ~ '_base_runtime_min') | float %}
   {% set morning_enabled = is_state('input_boolean.enable_morning_window', 'on') %}
   {% set evening_enabled = is_state('input_boolean.enable_evening_window', 'on') %}
   {% set dual_window = morning_enabled and evening_enabled %}
   
   # Runtime multipliers depend on program and window mode
   {% if program == 'heavy' %}
     {% set runtime_multiplier = 1.0 if dual_window else 1.5 %}
   {% else %}
     {% set runtime_multipliers = {'off': 0.0, 'light': 0.5, 'normal': 1.0} %}
     {% set runtime_multiplier = runtime_multipliers[program] %}
   {% endif %}
   
   {% set plain_watering_runtime = base_runtime * runtime_multiplier %}
   ```

5. **Calculate dosing duration (50% of plain watering time):**
   ```yaml
   {% set dosing_duration = plain_watering_runtime * 0.5 %}
   ```

6. **Calculate required flow rate:**
   ```yaml
   {% set required_flow = phase_dose / dosing_duration %}  # mL/min
   ```

7. **Convert to RPM using pump calibration curve:**
   ```yaml
   {% set slope = states('input_number.fert_pump' ~ pump_id ~ '_cal_slope') | float %}
   {% set intercept = states('input_number.fert_pump' ~ pump_id ~ '_cal_intercept') | float %}
   {% set rpm_command = (required_flow - intercept) / slope %}
   {% set rpm_clamped = [5, [rpm_command, 100] | min] | max %}  # Clamp to 5-100 RPM
   ```

**Returns (via response_variable):**
- `rpm_command`: Pump speed (RPM, clamped to 5-100 range)
- `dosing_duration_min`: Phase dosing time in minutes (excludes flush)

**Notes:**
- **Dosing duration = 50% of plain watering runtime** per phase
- **Flush is separate:** After dosing completes, 2-minute flush runs (pumps OFF, main pump ON)
- **Total phase time:** dosing_duration + 2 min flush
- **Heavy program water delivery:**
  - Single window: plain_runtime = base × 1.5, so dosing = base × 0.75 per phase
  - Dual window: plain_runtime = base × 1.0, so dosing = base × 0.5 per phase (extra water in evening)
- **Heavy program fertilizer:** Always 1.0× dose (extra water does NOT increase fertilizer)

**Example Calculations:**

*Heavy program, single window (morning only), base runtime = 20 min:*
- Plain watering would be: 20 × 1.5 = 30 min
- Phase 1 dosing: 30 × 0.5 = 15 min
- Phase 1 flush: 2 min
- Phase 2 dosing: 30 × 0.5 = 15 min  
- Phase 2 flush: 2 min
- **Total: 30 min dosing + 4 min flush = 34 min**

*Heavy program, dual window, base runtime = 20 min:*
- Plain watering (morning): 20 × 1.0 = 20 min
- Phase 1 dosing: 20 × 0.5 = 10 min
- Phase 1 flush: 2 min
- Phase 2 dosing: 20 × 0.5 = 10 min
- Phase 2 flush: 2 min
- **Morning total: 20 min dosing + 4 min flush = 24 min**
- Evening plain watering: 20 × 0.5 = 10 min (no fertilizer)
- **Total water across both windows: 30 min** (same as single window)

---

#### script.get_calibration_status

**Purpose:** Check calibration validity for a specific pump

**Inputs:**
- `pump_id` (1-3)

**Validation Checks:**
1. **Age:** Days since `input_datetime.fert_pumpN_last_cal`
   - ≤90 days: VALID
   - 91-365 days: WARNING
   - >365 days or never calibrated: EXPIRED
2. **Quality:** `input_number.fert_pumpN_cal_r2`
   - ≥0.995: VALID
   - <0.995: POOR

**Returns (via response_variable):**
- `status`: VALID | WARNING | POOR | EXPIRED
- `message`: Human-readable description

**Blocking Behavior:**
- POOR or EXPIRED → Blocks fertigation, triggers error state
- WARNING → Allows operation, sends HIGH-priority notification

---

#### script.start_fert_pump

**Purpose:** Start a peristaltic pump at calculated RPM with full safety checks

**Inputs:**
- `pump_id` (1-3)
- `rpm_command` (5-100 RPM)

**Safety Checks (BEFORE starting):**
1. **Calibration status:** Calls `script.get_calibration_status`, blocks if not VALID or WARNING
2. **Fert line valve (R7):** Verifies `switch.watering_system_relay_7_fert_line` is ON
3. **Main pump (R1):** Verifies `switch.watering_system_relay_1_main_pump` is ON
4. **RPM validation:** Clamps command to 5-100 RPM range

**Modbus Operations:**
1. Write RPM to register 0x0033 (Start Speed)
2. Send start command to register 0x0037

**Error Handling:**
- If any check fails → Log error, set `error_fert_system` state, send CRITICAL notification
- Modbus timeout → Retry once, then error state

---

#### script.stop_fert_pump

**Purpose:** Stop a peristaltic pump via Modbus

**Inputs:**
- `pump_id` (1-3)

**Operations:**
1. Send stop command to register 0x0038
2. Verify pump stopped (optional read-back)

**Error Handling:**
- Modbus timeout → Retry once
- If retry fails → Log warning (pump may still stop mechanically)

---

#### script.run_fert_dose_phase

**Purpose:** Orchestrate sequential fertigation for all eligible zones in a single phase

**Inputs:**
- `phase` (1 or 2)
- `eligible_zones` (list of zone IDs from `window_check`)

**Sequential Execution:**
```
FOR EACH zone_id IN eligible_zones:
  1. Set input_text.current_fertigation_zone = zone_id
  2. Check R7 (fert line valve) is OPEN and main pump (R1) is ON
  3. Open zone valve (R2-R5)
  4. Call script.calculate_zone_fert_dose (returns rpm_command, dosing_duration_min)
  5. Call script.start_fert_pump (starts pump at RPM)
  6. Wait for dosing_duration_min (50% of plain watering runtime)
  7. Call script.stop_fert_pump
  8. Continue watering for 2-minute flush (fresh water, fertilizer pumps OFF, main pump ON)
  9. Close zone valve
  10. Set input_text.current_fertigation_zone = 0
  11. Update input_datetime.zone_X_last_fert_event (only after phase 2 complete)
  12. 30-second inter-zone delay (if more zones remain)
NEXT zone_id
```

**Timing Breakdown:**
- **Dosing period:** 50% of plain watering runtime (pumps ON)
- **Flush period:** 2 minutes (pumps OFF, main pump continues)
- **Total phase time per zone:** dosing_duration + 2 min

**Inter-Zone Behavior:**
- 30-second delay between zones for pressure stabilization
- Main pump (R1) stays ON throughout entire sequence
- Fert line valve (R7) stays OPEN throughout
- Only selected pump runs (from `input_number.zone_X_{season}_pump`)

**Post-Phase Flushing:**
- 2 minutes fresh water after dosing completes
- Fertilizer pump OFF, main pump ON, R7 still open
- Ensures fertilizer reaches soil, clears injection lines
- Flush runs even if dosing encounters error (safety measure)

**Zone Tracking:**
- `input_text.current_fertigation_zone` = "0" when idle, "1"-"4" during active dosing
- Drives `binary_sensor.zone_X_fertigation_active` (used by history_stats for event counting)
- Binary sensor ON during dosing + flush (entire phase), OFF between zones

---

### 5.6.2 Calibration Scripts

**File:** `home-assistant/packages/watering_scripts/fert_cal_scripts.yaml`

**Purpose:** Support initial setup, maintenance, and recalibration of RS-485 peristaltic pumps

**Full Procedure:** See `/docs/fert_pump_cal_v2.md` for complete calibration protocol

---

#### script.tube_break_in

**Purpose:** Pre-calibration conditioning of new silicone tubing (stretches 5-10% in first hours)

**Inputs:**
- `pump_id` (1-3)
- `duration_sec` (default: 7200 = 2 hours)

**Procedure:**
1. Enable 24V cabinet (R10)
2. Initialize pump (Modbus registers 0x0030-0x0032, 0x0039)
3. Set speed to 30 RPM (register 0x0033)
4. Start pump (register 0x0037)
5. Wait for `duration_sec`
6. Stop pump (register 0x0038)
7. Send notification: "Break-in complete for pump {pump_id}"

**Usage:**
- Run once on NEW tubing installation
- Run at 30 RPM (conservative speed)
- Allow 30-minute rest period before calibration

**Testing:**
- Use `duration_sec: 60` for dry-run testing
- Full production run: 7200 seconds (2 hours)

---

#### script.perform_fert_pump_calibration

**Purpose:** User-paced gravimetric calibration at 5 setpoints × 3 repeats

**Inputs:**
- `pump_id` (1-3)
- `setpoint_number` (1-5, or "all" for full sequence)
- `trial_number` (1-3)

**Test Setpoints:**
| Setpoint | Target Flow | Estimated RPM | Trial Duration |
|----------|-------------|---------------|----------------|
| 1 | 2 mL/min | 13 RPM | 180 seconds |
| 2 | 4 mL/min | 27 RPM | 180 seconds |
| 3 | 6 mL/min | 40 RPM | 180 seconds |
| 4 | 10 mL/min | 67 RPM | 180 seconds |
| 5 | 15 mL/min | 100 RPM | 180 seconds |

**Procedure Per Trial:**
1. Display instructions via persistent notification: "Place collection cup, press Continue when ready"
2. Wait for user acknowledgment (via input_boolean or manual script trigger)
3. Start pump at setpoint RPM
4. Run for 180 seconds
5. Stop pump
6. Prompt user: "Remove cup, weigh contents, record mass in spreadsheet, press Continue"
7. Log trial data to `input_text.fert_pumpN_cal_notes`

**Full Calibration Mode (`setpoint_number: "all"`):**
- Runs all 5 setpoints × 3 trials = 15 measurements
- User-paced (waits for acknowledgment between trials)
- Estimated time: 60-90 minutes (including user actions)

**Output:**
- User records mass data in spreadsheet
- Calculates linear fit: q = slope × cmd + intercept
- Stores results in `input_number.fert_pumpN_cal_*` helpers
- Updates `input_datetime.fert_pumpN_last_cal`

**Acceptance Criteria:**
- R² ≥ 0.995 (VALID calibration)
- R² < 0.995 (POOR calibration, repeat required)

**Recalibration Triggers:**
- After tubing replacement (mandatory)
- Every 90 days (recommended, WARNING status)
- If dosing error >10% detected
- If PRV pressure adjusted

---

## Integration Notes

**Fertigation Window Behavior:**

**Dual-Window Mode (Both Morning + Evening Enabled):**
- **Morning Window:** Fertigation occurs here (if eligible)
  - FERT_PREP → FERT_DOSE_PHASE1 → FERT_DOSE_PHASE2
  - Phase 1: Dosing (50% of plain runtime) + 2-min flush
  - Phase 2: Dosing (50% of plain runtime) + 2-min flush
  - Total water per zone: 100% + 4 min flush
  - Fertilizer delivered: 100% of calculated dose (50% + 50%)
- **Evening Window:** Plain watering only (if heavy program)
  - WATERING_PLAIN with 0.5× multiplier
  - No fertilizer delivered
  - Provides extra 50% water for heavy programs

**Single-Window Mode (Morning OR Evening Only):**
- Fertigation occurs in whichever window is enabled
- Phase 1: Dosing (75% of base runtime) + 2-min flush
- Phase 2: Dosing (75% of base runtime) + 2-min flush
- Total water: 150% of base runtime + 4 min flush
- Fertilizer: 100% of calculated dose (50% + 50%)

**Timing Examples:**

*Example 1: Normal program, base runtime = 20 min*
- Plain watering would be: 20 min
- Phase 1 dosing: 20 × 0.5 = 10 min
- Phase 1 flush: 2 min
- Phase 2 dosing: 20 × 0.5 = 10 min
- Phase 2 flush: 2 min
- **Total: 20 min dosing + 4 min flush = 24 min**

*Example 2: Heavy program, single window (morning only), base = 20 min*
- Plain watering would be: 20 × 1.5 = 30 min
- Phase 1 dosing: 30 × 0.5 = 15 min
- Phase 1 flush: 2 min
- Phase 2 dosing: 30 × 0.5 = 15 min
- Phase 2 flush: 2 min
- **Total: 30 min dosing + 4 min flush = 34 min**
- Fertilizer dose: 1.0× (normal dose, NOT increased)

*Example 3: Heavy program, dual window (morning + evening), base = 20 min*
- **Morning (fertigation):**
  - Plain watering component: 20 × 1.0 = 20 min
  - Phase 1 dosing: 20 × 0.5 = 10 min
  - Phase 1 flush: 2 min
  - Phase 2 dosing: 20 × 0.5 = 10 min
  - Phase 2 flush: 2 min
  - **Morning total: 20 min dosing + 4 min flush = 24 min**
- **Evening (plain watering only):**
  - Plain watering: 20 × 0.5 = 10 min (no fertilizer)
- **Grand total water: 30 min** (same as single window, split between windows)
- Fertilizer dose: 1.0× (normal dose, NOT increased)

**Dose Multipliers by Program:**
- Off: 0.0× (no fertigation)
- Light: 0.5× (proportional) or 1.0× (full dose, if boolean enabled)
- Normal: 1.0×
- Heavy: 1.0× (fertilizer stays at normal dose)

**Water Multipliers by Program:**
- Off: 0.0×
- Light: 0.5×
- Normal: 1.0×
- Heavy: 1.5× (single window) or 1.0× morning + 0.5× evening (dual window)

**Critical Design Principle:**
- Fertilizer dose is determined by crop nutrient needs, NOT water requirements
- Heavy programs increase WATER delivery to compensate for heat/drought
- Heavy programs keep fertilizer at NORMAL dose (1.0×) to avoid salt buildup
- If crops need more fertilizer, user adjusts `input_number.zone_X_{season}_dose_ml` directly

---

## Section 6: Automation Structure

### 6.1 Master State Machine
**File:** `home-assistant/packages/watering_state/state_machine.yaml`

Single automation that watches `input_select.watering_system_state` and executes scripts based on state transitions.

### 6.2 State Transition Scripts
**File:** `home-assistant/packages/watering_state/state_scripts.yaml`

Individual scripts for each state's actions:
- `script.window_check`
- `script.preflight_check`
- `script.watering_plain_sequence`
- `script.fert_prep_sequence`
- `script.fert_dose_phase1`
- `script.fert_dose_phase2`
- `script.post_cycle_relief`

### 6.3 Zone Control Scripts
**File:** `home-assistant/packages/watering_scripts/zone_scripts.yaml`

Reusable scripts for zone operations:
- `script.open_zone` (parameters: zone_id)
- `script.close_zone` (parameters: zone_id)
- `script.run_zone_sequence` (handles parallel vs sequential)
- `script.calculate_zone_runtime` (returns runtime based on program)

### 6.4 Fertilizer Control Scripts
**File:** `home-assistant/packages/watering_scripts/fert_scripts.yaml`

RS-485 Modbus control for dosing pumps:
- `script.enable_24v_cabinet`
- `script.disable_24v_cabinet`
- `script.start_dosing_pumps` (parameters: zone_id, phase)
  - Uses calibration curve to convert dose → flow → command
  - Sends Modbus command to appropriate pump addresses (0x02-0x04)
- `script.stop_dosing_pumps`
- `script.valve_interlock` (ensures bypass XOR fert line open)
- `script.fertilizer_pump_calibration` (runs full calibration procedure)

**Calibration Integration:**
The `start_dosing_pumps` script retrieves:
1. Target dose from `input_number.fert_zone_{zone_id}_pump{n}_dose_ml`
2. Zone runtime (adjusted for program: light/normal/heavy)
3. Required flow rate = dose / runtime
4. Calibration coefficients from `input_number.fert_pump{n}_cal_*`
5. Command value = (flow - intercept) / slope
6. Send command via Modbus to pump address

**Additional Pump Control Scripts:**

**File:** `home-assistant/packages/watering_scripts/pump_scripts.yaml`

Main pump control operations:
- `script.start_main_pump` (with pressure stabilization delay)
- `script.stop_main_pump`
- `script.open_pressure_relief` (with timeout)
- `script.close_pressure_relief`

### 6.5 Independent Safety Automations
**File:** `home-assistant/packages/watering_safety/automations.yaml`

Always-running monitors:
- `automation.tank_level_safety`
- `automation.modbus_watchdog`
- `automation.zone_runtime_safety`
- `automation.manual_override_handler`

**File:** `home-assistant/packages/watering_safety/scripts.yaml`

Safety-related scripts:
- `script.emergency_stop` (stops everything, resets to idle)
- `script.safe_shutdown` (graceful stop with pressure relief)

### 6.6 Sensor Reading Scheduler (Future - Phase 3)
**File:** `home-assistant/packages/watering_sensors/scheduler.yaml`

Periodic soil sensor reading:
- `automation.soil_sensor_reading_schedule`
- `automation.pre_watering_sensor_read`
- `script.read_soil_sensors` (24V enable → read → disable)
---

watering-system/                      # Public repo (sanitized)
├── docs/
│   ├── architecture.md               # System design document
│   ├── programming-notes.md          # Coding standards & tribal knowledge
│   ├── impl_roadmap.md               # Implementation status tracking
│   ├── test_scenarios.md             # Test cases & validation
│   ├── db_schema.sql                 # Operational database schema (watering_ops)
│   └── entity_reference.md           # Entity ID quick reference
│
├── esphome/
│   ├── watering-system.yaml          # Main ESP32 device config
│   ├── packages/
│   │   ├── modbus_rs485.yaml         # UART + 16-relay board
│   │   ├── inputs.yaml               # Float switches (GPIO32/33)
│   │   └── victron_ble.yaml          # SmartSolar BLE sensors
│   ├── components/
│   │   └── victron_ble/              # Vendored component (GPL-3.0)
│   └── secrets.example.yaml          # Template with placeholders
│
├── home-assistant/
│   ├── configuration.yaml            # Main HA config
│   ├── packages/
│   │   ├── notification/
│   │   │   ├── helpers.yaml          # Notification controls
│   │   │   ├── config.yaml           # REST commands, IMAP config
│   │   │   ├── scripts.yaml          # Tiered notification sending
│   │   │   └── tests.yaml            # Daily/monthly/de-winterization tests
│   │   ├── weather/
│   │   │   └── dwd_brightsky.yaml    # BrightSky API integration
│   │   ├── watering_helpers/
│   │   │   ├── system_helpers.yaml   # State, schedule, safety config
│   │   │   ├── zone_helpers.yaml     # Zone programs, thresholds
│   │   │   ├── fert_helpers.yaml     # Dosing rates, calibration
│   │   ├── watering_scripts/
│   │   │   ├── zone_scripts.yaml     # Zone operations
│   │   │   ├── pump_scripts.yaml     # Main pump control
│   │   │   └── fert_scripts.yaml     # Fertilizer dosing pumps
│   │   ├── watering_state/
│   │   │   ├── state_machine.yaml    # Master state controller
│   │   │   └── state_scripts.yaml    # State transition scripts
│   │   ├── watering_safety/
│   │   │   ├── automations.yaml      # Safety monitors
│   │   │   └── scripts.yaml          # Emergency procedures
│   │   ├── watering_sensors/
│   │   │   └── scheduler.yaml        # Soil sensor reading (Phase 3)
│   │   └── watering_ui/
│   │       └── dashboard.yaml        # Dashboard config (Phase 7)
│   ├── appdaemon/watering_db/        # AppDaemon app (NOT under packages/)
│   │   ├── apps.yaml                 # AppDaemon app config (db_schema_init)
│   │   ├── db_schema_init.py         # Schema bootstrap (Phase 3.5) ✅
│   │   ├── db_writer.py              # AppDaemon event listeners and DB writes (later)
│   │   ├── db_queries.py             # Decision query logic and sensor updates (later)
│   │   └── db_export.py              # Seasonal CSV export (later)
│   └── secrets.example.yaml          # Template with placeholders
│
├── README.md                         # Project overview & attribution
├── LICENSE                           # Dual-license notice (MIT + GPL-3.0)
├── .gitignore                        # Excludes secrets, logs, db files
├── .yamllint                         # YAML linter config
└── .github/
    └── workflows/
        ├── lint.yml                  # yamllint + gitleaks on push/PR
        └── publish.yml               # Mirror workflow (private → public)

---

## 7. Data Flow

## Section 7.1: Morning Window Example

```
06:00 - Time Trigger
  ↓
STATE: IDLE → WINDOW_CHECK
  ↓
Script: window_check
  - Evaluate weather conditions per zone (intensity: off/light/normal/heavy)
  - Apply cadence gate (Phase 7): per-zone enable + interval (days since last
    main dose from sensor.zone_N_watering) + heavy mid-interval booster
  - Set zone programs (off/light/normal/heavy/booster)
  ↓
STATE: WINDOW_CHECK → PREFLIGHT_CHECK
  ↓
Script: preflight_check
  - Verify tank levels (binary_sensor.watering_system_low_water_level)
  - Check ESP32 online
  - Build task list
  ↓
STATE: PREFLIGHT_CHECK → WATERING_PLAIN or FERT_PREP
  ↓
[If plain watering]
  Script: watering_plain_sequence
    - Open bypass valve (switch.watering_system_relay_6_fert_bypass)
    - Start main pump (switch.watering_system_relay_1_main_pump)
    - Run zones (parallel or sequential)
    - Stop pump, close zones
  ↓
  STATE: WATERING_PLAIN → POST_CYCLE_RELIEF
  
[If fertigation due]
  Script: fert_prep_sequence
    - Enable 24V (switch.watering_system_relay_10_24v_cabinet)
    - Close bypass (switch.watering_system_relay_6_fert_bypass)
    - Open fert line (switch.watering_system_relay_7_fert_line)
  ↓
  STATE: FERT_PREP → FERT_DOSE_PHASE1
  ↓
  Script: fert_dose_phase1
    - Open target zone valve (switch.watering_system_relay_2_zone_1 through relay_5_zone_4)
    - Start pump (switch.watering_system_relay_1_main_pump)
    - Wait for pressure stabilization (30s)
    - Start dosing pumps (Modbus)
    - Run for 50% duration (or 100% if light)
    - Stop dosing
    - Flush 2min (fert line R7 still open, dosing pumps off)   # per fert_prog_design.md §6.3
  ↓
  STATE: FERT_DOSE_PHASE1 → FERT_DOSE_PHASE2
  ↓
  Script: fert_dose_phase2
    - [If normal/heavy] Start dosing, run 50%, stop dosing
    - [If light] Plain water only (no dosing this phase)
    - Flush 2min (fert line R7 still open, dosing pumps off)   # per fert_prog_design.md §6.3
    - Close fert line (switch.watering_system_relay_7_fert_line),
      open bypass (switch.watering_system_relay_6_fert_bypass)
  ↓
  STATE: FERT_DOSE_PHASE2 → POST_CYCLE_RELIEF

Post-Cycle (both paths converge):
  Script: post_cycle_relief
    - Stop pump (switch.watering_system_relay_1_main_pump)
    - Close all zones:
        • switch.watering_system_relay_2_zone_1
        • switch.watering_system_relay_3_zone_2
        • switch.watering_system_relay_4_zone_3
        • switch.watering_system_relay_5_zone_4
    - Open pressure relief valve (switch.watering_system_relay_9_pressure_relief)
    - Wait 120s
    - Close pressure relief
    - Disable 24V (switch.watering_system_relay_10_24v_cabinet)
  ↓
  STATE: POST_CYCLE_RELIEF → IDLE
```

---

## Section 7.2: Safety Monitor (Parallel, Always Active)

```
[Running independently of state machine]

Monitor: binary_sensor.watering_system_low_low_water_level
  ↓
  [If goes 'on']
    - Immediately turn off pump (switch.watering_system_relay_1_main_pump)
    - Force state → ERROR_TANK_LOW
    - Send notification
    - Block further state transitions until manual reset
```

---

## Entity ID Reference for State Machine Flow

**For quick reference while reading flow diagrams:**

| Abbreviation | Full Entity ID |
|--------------|----------------|
| R1 (Pump) | `switch.watering_system_relay_1_main_pump` |
| R2 (Zone 1) | `switch.watering_system_relay_2_zone_1` |
| R3 (Zone 2) | `switch.watering_system_relay_3_zone_2` |
| R4 (Zone 3) | `switch.watering_system_relay_4_zone_3` |
| R5 (Zone 4) | `switch.watering_system_relay_5_zone_4` |
| R6 (Bypass) | `switch.watering_system_relay_6_fert_bypass` |
| R7 (Fert Line) | `switch.watering_system_relay_7_fert_line` |
| R9 (Pressure Relief) | `switch.watering_system_relay_9_pressure_relief` |
| R10 (24V Cabinet) | `switch.watering_system_relay_10_24v_cabinet` |
| Low Level | `binary_sensor.watering_system_low_water_level` |
| Low-Low Level | `binary_sensor.watering_system_low_low_water_level` |

**Note:** These abbreviations (R1, R2, etc.) are for documentation clarity only. Always use full entity IDs in actual YAML configurations.

## 8. Dashboard Structure

### 8.1 Main Control Card
- Current system state (large, colored)
- Next scheduled watering (date/time)
- Emergency stop button
- Manual override toggle

### 8.2 Zone Status Cards (one per zone)
- Current program (off/light/normal/heavy)
- Last watering date/time
- Next fertigation due date
- Manual zone control (when in override mode)

### 8.3 System Configuration Card
- Zone sequencing mode (parallel/sequential)
- Watering cycle period (days)
- Morning/evening window times
- Season selector

### 8.4 Per-Zone Configuration Card
- Zone friendly name editor
- Phase friendly name editors (5 phases)
- Current phase selector (dropdown with friendly names)
- Base runtime
- Phase-specific thresholds (collapsible sections per phase)
- Fertigation dosing amounts (ml per dose)
- Calculated dosing rates (ml/min - read-only display)
- Calculated pump commands (% - read-only display, shows what will be sent to pumps)

### 8.5 Safety Status Card
- Tank level indicators (Low, Low-Low)
- ESP32 communication status
- Last successful Modbus transaction
- Active alarms/warnings

### 8.6 Fertilizer Pump Calibration Card
- Per-pump calibration status badges (VALID/WARNING/EXPIRED/POOR)
- Last calibration date per pump
- Calibration equation display (q = a×cmd + b)
- R² value display
- "Run Calibration" button (launches `script.fertilizer_pump_calibration`)
- Calibration curve graph:
  - Scatter plot: calibration points
  - Line plot: fitted curve
  - Shaded region: typical operating range (0.5-4 mL/min)
  - X-axis: Command (%)
  - Y-axis: Flow (mL/min)
 
### 8.7 ESPHome Device Dashboard
**Relay Controls:**

All 16 relays visible as individual switches
Real-time state from Modbus board
Icons differentiate pump/zones/valves/power

**Tank Level Monitoring:**

Low Water Level (GPIO33) - mdi:water-alert
Low-Low Water Level (GPIO32) - mdi:water-alert-outline
5-second alarm delay prevents splash false positives

**Solar System Monitoring:**

Battery voltage, current
PV power, yield today
Load current
Fault/error states
Charger state text

---

## 9. Future Extensions

### 9.1 Soil Moisture Sensor Integration (Phase 3)

> **DECIDED by ADR-021 (ACCEPTED 2026-08-25):** adopt the **hybrid** — **4× wireless Ecowitt
> WH52** (Option B) **+ 3× wired DFRobot SEN0600** (Option A). Soil moisture is now the
> **PRIMARY** program-selection input (§3.2), not an override. Sensor→zone mapping: hard-wired
> SEN0600 are fixed to zones; the movable WH52 carry a runtime zone tag
> (`input_select.moisture_wireless_N_zone`, friendly options Raspberries/Blueberries/Vegetables);
> `sensor.zone_N_soil_moisture` = the **average** of all sensors mapped to the zone (zones 3 & 4
> share the veg bed → both read the "Vegetables"/zone-3 pool, distinct thresholds). WH52 moisture
> is **native 0–100 %** (no calibration). SEN0600 sit on the isolated pump RS-485 bus →
> **pulse-poll** (energize R10, stabilize, read, de-energize). Implementation is **HELD** until
> the hardware is installed & calibrated. Full detail in ADR-021.

**Integration goals (sensor-agnostic):**
- **Primary signal:** soil moisture drives the base intensity (ADR-021), weather only modulates
- Wet-skip: soil at/above `off_moisture_min` → `off`
- Per-zone / per-season moisture targets (`zone_N_{season}_{off,light,normal}_moisture_min`)
- Weather-only fallback when a zone has no mapped/available sensor

**Option A — Wired RS-485 (plan of record):**
- DFRobot SEN0600 RS-485 sensors (addresses 0x05-0x07), on the existing Modbus bus
- Requires 24V cabinet enable before reading
- SEN0600 measures moisture + temperature only (no EC). SEN0601 adds EC
  (0-20,000 µS/cm, ±3%); SEN0604 adds pH. IP68, 316 stainless needle — can be
  buried at root-zone depth (vertically, or horizontally in a pit wall), which
  matters under drip for deeper-rooted zones.

**Option B — Wireless Ecowitt WH52 hybrid (documented alternative, undecided):**
- Ecowitt WH52 3-in-1 (moisture ±5%, soil temp ±1°C, EC — coarse/trend-grade),
  wireless 868 MHz to the GW1200 weather gateway (§9.4); up to 16 soil sensors.
- Moves soil sensing OFF the RS-485 bus → frees 0x05-0x07 and the 24V-enable read
  gating; data arrives via the Ecowitt HA integration, not Modbus reads.
- No cable to lay. Capacitive % is relative (per-soil calibration, drift, inter-unit
  variance) and the EC is a coarse index, so it is trend-grade, not research-grade.
- **Depth caveat:** the WH52 is surface-inserted (sensing zone ~ top 10-15 cm; the
  body/RF must stay near the surface). Well-matched to shallow-rooted beds
  (strawberries, blueberries/lingonberries, herbs); under-represents deeper-rooted
  beds (raspberries, kiwi, tomatoes) under drip. The WH51L (moisture-only, probe on
  a 1 m/5 m wire) reaches depth but drops EC/temp.
- **Hybrid intent:** WH52 wireless across the shallow-rooted zones; a wired DFRobot
  probe (SEN0601 for EC, or SEN0600) where depth or precise EC changes a decision
  (e.g. the strawberry co-zone for salinity; raspberry/kiwi for true root-zone moisture).
- **RESOLVED (ADR-021):** adopted as a **hybrid** — WH52 wireless *plus* the SEN0600 wired
  (not either/or); see the §9.1 banner above.

### 9.2 Flow Rate Monitoring (Phase 4)
- Detect zone valve failures (no flow when expected)
- Leak detection (flow when no zones open)
- Proportional dosing (fertilizer rate tied to actual flow)

### 9.3 Energy Optimization (Phase 4)
- Delay watering if battery SOC < threshold
- Prefer watering during solar generation hours
- Track energy consumption per cycle

### 9.4 Local Weather Station (selected — hardware pending)

**Purpose:** A local, on-site source for temperature, rainfall, and humidity to
replace/supplement the DWD/BrightSky API pull (`weather/dwd_brightsky.yaml`) with
more stable, garden-accurate data, and to log solar-radiation/UV for future
evapotranspiration-based tuning.

**Chosen hardware (Ecowitt, 868 MHz EU band):**
- **Gateway:** GW1200 (WiFi, local HA integration; IoT-capable variant chosen for
  future headroom, though the system's own valve/relay control stays in HA).
- **Array:** WS90 7-in-1 (solar + supercap; temp, humidity, piezo rain, ultrasonic
  wind, solar radiation, UV). Wind is unused; ultrasonic = no moving parts.
- **Rain:** WH40 tipping-bucket gauge as the trusted rainfall source — Ecowitt rate
  the piezo rain below a dedicated tipping bucket, so irrigation decisions read the
  WH40. In HA the WH40 (traditional rain) and WS90 (piezo rain) appear as separate
  streams; point `rain_24h`/`rain_72h` logic at the WH40.

**Siting / RF:** Gateway in the cellar on WiFi (beside the extender), with the whole
unit at — or its antenna routed to — a cellar window facing the garden. 868 MHz range
is ample for garden distances; verify per-sensor RSSI after install and nudge if
marginal.

**Integration (deferred, no code yet):** Add an Ecowitt integration under the
`weather/` package alongside `dwd_brightsky.yaml`; repoint the rain (and optionally
temperature) sensors used by §3.2 program selection from BrightSky to the WS90/WH40
entities. Warrants an ADR when implemented.

---

## 10. Testing Strategy

### 10.1 State Machine Testing
1. Test each state transition individually
2. Verify state persistence across HA restarts
3. Test error state recovery paths
4. Test manual override at each state

### 10.2 Safety Interlock Testing
1. Trigger Low-Low float switch during watering
2. Disconnect ESP32 during fertigation
3. Exceed zone runtime limits
4. Test emergency stop from each state

### 10.3 Zone Sequencing Testing
1. Parallel mode: all zones start/stop together
2. Sequential mode: zones run one at a time
3. Mixed programs: some zones skip, others run

### 10.4 Fertigation Testing
1. Split-dose sequence (normal/heavy programs)
2. Single-dose + flush (light program)
3. Valve interlock (bypass XOR fert line)
4. RS-485 pump communication

---

## 11. Maintenance Procedures

### 11.1 Seasonal Threshold Updates
- Review/adjust per-zone thresholds at season change
- Update via UI (no YAML editing)
- Test program selection with historical weather data

### 11.2 Fertigation Calibration
- **Full procedure:** `/docs/fert_pump_cal_v2.md`
- **Calibrate pumps at operating pressure** (1.1 bar via PRV)
- **Test protocol:** 5 setpoints × 3 repeats, 180s per trial
- **Method:** Gravimetric (0.01g scale), user-paced measurement
- **Output:** Linear calibration curve (q = a×cmd + b) with R² ≥ 0.995
- **Storage:** Coefficients in `input_number.fert_pump{n}_cal_*` helpers
- **Runtime:** System calculates required command from dose + runtime using stored curve
- **Recalibration schedule:**
  - After tubing replacement
  - Quarterly (90 days)
  - If dosing error >10% detected
  - If PRV pressure adjusted
- **Record keeping:** Calibration date, pressure, SG, coefficients logged in programming notes

### 11.3 System Health Checks
- Weekly: Review automation logs for errors
- Monthly: Test safety interlocks
- Seasonal: Clean disc filter, inspect valves

---

## 12. Notification System

### 12.1 Overview

The notification system provides multi-channel alerts for system events, safety alarms, and operational status. All notifications respect the winterization state and include comprehensive testing to prevent silent failures.

**Core Principles:**
- Multi-channel redundancy (WhatsApp + Email)
- Tiered notification strategy based on event severity
- Daily and monthly automated testing
- Winterization-aware (all notifications disabled when system powered down)
- Cannot fail silently (test failures trigger escalated alerts)

---

### 12.2 Notification Channels

**WhatsApp (CallMeBot):**
- API-based message delivery
- Instant delivery to smartphone
- Used for time-sensitive alerts and daily summaries
- Free, unlimited messages
- One-way only (no replies)

**Email (Gmail SMTP):**
- Dedicated Gmail account: bob.m.hart.ha@gmail.com
- Auto-forwards to primary email
- Used for critical alerts and daily self-test
- IMAP monitoring for delivery verification
- Supports daily health checks

---

### 12.3 Notification Tiers

#### CRITICAL Tier (WhatsApp + Email)
**Events:**
- Tank Low-Low emergency stop
- ESP32 communication lost
- Manual emergency stop triggered
- Daily email test failure (triggers notification_system_error)
- Monthly WhatsApp test failure (24h delayed)
- De-winterization test failure

**Message Format:**
```
🚨 CRITICAL: [Event]
Time: [HH:MM]
Action Required: [Specific instruction]
```

**Characteristics:**
- Sent via both channels simultaneously
- No retry logic (sent once per event)
- Requires immediate user attention

---

#### HIGH Tier (WhatsApp + Email)
**Events:**
- Tank Low warning (not yet Low-Low)
- Zone runtime exceeded safety cutoff
- Fertigation cycle blocked/failed to start
- Preflight check failures

**Message Format:**
```
⚠️ WARNING: [Event]
Time: [HH:MM]
System Status: [Current state]
```

**Characteristics:**
- Dual-channel for reliability
- Indicates degraded state requiring attention

---

#### STANDARD Tier (WhatsApp only)
**Events:**
- Morning window summary (after post_cycle_relief)
- Evening window summary (after post_cycle_relief)

**Message Format:**
```
✅ Watering Summary - [Morning/Evening Window]
Zones Watered: [1, 2, 4 (programs: normal, light, heavy)]
Fertilizer: [Zone 3 - Pump 1: 60ml]
Errors: [None / List any warnings]
Runtime: [Total: 45min]
```

**Characteristics:**
- Informational only
- Single channel sufficient
- Compiled during post_cycle_relief state

---

### 12.4 Winterization Behavior

**Entity:** `input_boolean.system_winterized`

**When Winterized (ON):**
- All watering automations disabled
- All notification automations disabled
- Daily email test skipped
- Monthly WhatsApp test skipped
- De-winterization test armed

**When De-winterized (switched OFF):**
- Immediate test of WhatsApp + Email channels
- User must confirm receipt within 24h
- Failed confirmation blocks automatic watering
- System marked "ready" only after successful test

---

### 12.5 Silent Failure Prevention

**Multi-layered Detection:**

**Layer 1: Send Failure Detection**
- REST API error codes logged immediately
- Failed channel attempt → notification sent via other channel
- Logged to `sensor.last_notification_error`

**Layer 2: Daily Email Self-Test (19:00)**
- HA sends email to itself
- IMAP monitors inbox for arrival within 5 minutes
- Failure → Sets `input_boolean.notification_system_error = ON`
- Triggers CRITICAL notification via WhatsApp
- Checked in preflight_check state (blocks watering if ON)

**Layer 3: Monthly WhatsApp Test (1st at 19:00)**
- Sends test message via WhatsApp
- User clicks `input_boolean.monthly_test_whatsapp_confirmed` within 24h
- Failure → CRITICAL notification via Email (24h delayed)

**Layer 4: De-winterization Test**
- Triggered when `input_boolean.system_winterized` → OFF
- Sends test via WhatsApp + Email
- User confirms both channels within 24h
- Failed confirmation blocks automatic watering until resolved

---

### 12.6 Configuration Entities

```yaml
# Winterization Control
input_boolean.system_winterized:
  name: "System Winterized"
  icon: mdi:snowflake

# Notification System Health
input_boolean.notification_system_error:
  name: "Notification System Error"
  icon: mdi:alert-circle
  initial: off

# Monthly Test Confirmations
input_boolean.monthly_test_whatsapp_confirmed:
  name: "Monthly WhatsApp Test Confirmed"
  icon: mdi:check-circle
  initial: off

# De-winterization Test Confirmations
input_boolean.dewinter_test_whatsapp_confirmed:
  name: "De-winterization WhatsApp Test Confirmed"
  icon: mdi:check-circle
  initial: off

input_boolean.dewinter_test_email_confirmed:
  name: "De-winterization Email Test Confirmed"
  icon: mdi:check-circle
  initial: off

# Test Tracking
sensor.last_email_test_time:
  # Template sensor - timestamp of last daily test

sensor.last_monthly_test_time:
  # Template sensor - timestamp of last monthly test

sensor.last_notification_error:
  # Template sensor - last error message and timestamp
```

---

### 12.7 Integration with State Machine

**Preflight Check Enhancement:**

```yaml
# Additional check in preflight_check state:
- condition: state
  entity_id: input_boolean.notification_system_error
  state: 'off'
# If ON → transition to error state, require manual resolution
```

**Post-Cycle Relief Enhancement:**

```yaml
# Add to post_cycle_relief state (before transition to idle):
- service: script.send_watering_summary
  # Compiles cycle data and sends STANDARD tier notification
```

---

### 12.8 API Configuration

**WhatsApp (CallMeBot):**
- Phone: +34 694 242 562
- API Key: 4691969
- Endpoint: `https://api.callmebot.com/whatsapp.php`

**Email (Gmail SMTP):**
- Server: smtp.gmail.com:587
- Username: bob.m.hart.ha@gmail.com
- App Password: hokefkhgjcrdqcqd (stored in secrets.yaml)
- TLS: Required

**Email (IMAP - for daily test monitoring):**
- Server: imap.gmail.com:993
- Username: bob.m.hart.ha@gmail.com
- App Password: (same as SMTP)
- SSL: Required

---

### 12.9 Dashboard Elements

**Notification Status Card:**
- Notification system health indicator (OK / ERROR)
- Last daily email test result + timestamp
- Last monthly WhatsApp test result + timestamp
- Winterization status badge
- Manual test triggers (for debugging)

**Test Confirmation Card:**
- Monthly test confirmation button (appears after test sent)
- De-winterization test confirmation buttons (2)
- Countdown timer showing time remaining for confirmation

---

### 12.10 Maintenance Schedule

**Daily:** Email self-test at 19:00 (automated)

**Monthly:** WhatsApp test on 1st at 19:00 (automated, requires user confirmation)

**Seasonal:** De-winterization test when switching from winter to spring mode

**As Needed:** Manual notification test via dashboard (for debugging or after configuration changes)

---

### 12.11 Implementation Status

**Status:** ✅ Operational (2025-10-13)
- All core notification functionality tested and working
- Daily self-test running automatically at 19:00
- Monthly test scheduled for 1st of each month at 19:00
- 24/27 test scenarios passed (89% test coverage)

**Pending Integration:**
- Safety automation integration (requires Phase 5)
- Watering summary generation (requires Phase 4 state machine)

**Files:** 
- `notification_helpers.yaml` - 5 booleans, 3 template sensors, 3 datetimes, 2 text inputs
- `notification_config.yaml` - REST commands, SMTP/IMAP config
- `notification_scripts.yaml` - Tiered notification scripts
- `notification_tests.yaml` - 11 test automations

---

## Section 13: Operational Database Architecture

### 13.1 Overview

The system uses a two-layer architecture for persistent operational storage,
per ADR-011 (in `docs/programming-notes.md`):

- **Layer 1 — SQLite (single database file):** Dedicated `watering_ops`
  database in one SQLite file at `/homeassistant/watering_ops.db`, completely
  separate from HA's recorder database. Living in the HA config directory means
  it is captured by HA's normal backup and is reachable from the AppDaemon
  container. Schema defined in `docs/db_schema.sql`.
- **Layer 2 — AppDaemon add-on:** Python bridge between HA and SQLite. Listens
  for state machine events, writes records, and returns decision query results
  as HA sensor states. Uses the `sqlite3` standard library (no driver add-on).

AppDaemon failure does not affect watering operations — DB writes are
fire-and-forget from the state machine perspective.

---

### 13.2 Schema

Four tables. Full SQL in `docs/db_schema.sql`.

> The column **Type** values below are logical (illustrative). The physical
> SQLite mapping (BOOLEAN -> INTEGER, DECIMAL -> REAL, DATETIME -> TEXT in UTC,
> VARCHAR -> TEXT), foreign keys, indexes, and CHECK constraints are defined in
> `docs/db_schema.sql`.

**`watering_cycles`** — One row per cycle. Written in two phases.

| Column | Type | Description |
|--------|------|-------------|
| `cycle_id` | INT AUTO_INCREMENT PK | Unique cycle identifier |
| `start_time` | DATETIME | Written at preflight |
| `trigger_type` | VARCHAR(20) | `scheduled` / `manual` / `override` |
| `rainfall_24h_mm` | DECIMAL(5,1) | Weather snapshot at preflight |
| `rainfall_72h_mm` | DECIMAL(5,1) | Weather snapshot at preflight |
| `temp_high_c` | DECIMAL(4,1) | Weather snapshot at preflight |
| `end_time` | DATETIME | Updated on completion |
| `outcome` | VARCHAR(20) | `completed` / `aborted` / `error` |
| `notes` | VARCHAR(500) | Updated on completion |

**`zone_runs`** — One row per zone per cycle. Written at zone run conclusion.

| Column | Type | Description |
|--------|------|-------------|
| `zrun_id` | INT AUTO_INCREMENT PK | Unique zone run identifier |
| `cycle_id` | INT FK | Parent cycle |
| `zone_id` | TINYINT | Zone number 1–4 |
| `weather_program` | VARCHAR(10) | `off` / `light` / `normal` / `heavy` |
| `start_time` | DATETIME | Zone valve open time |
| `end_time` | DATETIME | Zone valve close time |
| `planned_duration_sec` | INT | From `script.calculate_zone_runtime` |
| `actual_duration_sec` | INT | Calculated by AppDaemon on write |
| `program_multiplier` | DECIMAL(3,2) | e.g. 1.0, 1.5, 0.5 |
| `fertigated` | BOOLEAN | True if fertigation doses exist for this run |
| `aborted` | BOOLEAN | True if zone did not complete planned duration |
| `abort_reason` | VARCHAR(200) | Populated if aborted = true |

**`fertigation_doses`** — One row per dose event. Written at dosing conclusion.

| Column | Type | Description |
|--------|------|-------------|
| `dose_id` | INT AUTO_INCREMENT PK | Unique dose identifier |
| `zrun_id` | INT FK | Parent zone run |
| `zone_id` | TINYINT | Denormalized for query convenience |
| `timestamp` | DATETIME | When dose was delivered |
| `nutrient_product` | VARCHAR(100) | Product name/identifier |
| `target_dose_ml` | DECIMAL(6,2) | Planned dose |
| `actual_dose_ml` | DECIMAL(6,2) | Actual dose delivered |
| `pump_id` | INTEGER | Logical pump number 1–3 (maps to Modbus 0x02–0x04) |
| `phase` | TINYINT | Dose phase: 1 or 2 |

**`system_events`** — Append-only. Written immediately after event.

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | INT AUTO_INCREMENT PK | Unique event identifier |
| `timestamp` | DATETIME | When event occurred |
| `event_type` | VARCHAR(50) | e.g. `safety_interlock`, `manual_override` |
| `severity` | VARCHAR(20) | `info` / `warning` / `error` / `critical` |
| `entity_id` | VARCHAR(100) | HA entity involved, if applicable |
| `value_before` | VARCHAR(200) | State/value before event |
| `value_after` | VARCHAR(200) | State/value after event |
| `notes` | VARCHAR(500) | Human-readable detail |

---

### 13.3 Write Trigger Points

AppDaemon listens for HA events fired by the state machine:

| DB Write | Trigger Point | HA Event |
|----------|---------------|----------|
| `watering_cycles` INSERT | Preflight check passes | `watering_preflight_complete` |
| `zone_runs` INSERT | Zone run concludes | `watering_zone_run_complete` |
| `fertigation_doses` INSERT | Dosing event concludes | `watering_fert_dose_complete` |
| `watering_cycles` UPDATE | Cycle concludes | `watering_cycle_complete` |
| `system_events` INSERT | Safety/error event fires | `watering_system_event` |

**Note:** The HA event payload schemas are the contract between the state machine
and AppDaemon. They are defined in §13.3.1 and must be stable before Phase 4
implementation builds the state machine against them.

---

### 13.3.1 Event Payload Schemas

These define the contract between the state machine (Phase 4, which fires the
events) and the AppDaemon writer (which validates and persists them).

**Shared conventions**

- Each event is a Home Assistant event with an `event_type` (the names in §13.3)
  and an `event_data` mapping (the fields tabulated per event below).
- **Timestamps** are UTC strings in the SQLite datetime format
  `'YYYY-MM-DD HH:MM:SS'` (see the §13.2 engine notes). They are carried in the
  payload and never stamped by AppDaemon on receipt: several events report a
  moment that already passed (a cycle's start, a zone valve's open/close), so the
  firing component is the only authority on when the event actually occurred.
- **Correlation identifiers.** SQLite primary keys (`cycle_id`, `zrun_id`) are
  assigned by the database at INSERT, so the state machine cannot know them when
  it fires an event. Instead it mints two opaque identifiers and stamps them on
  every related event:
  - `cycle_uuid` — one per watering cycle, present on every event belonging to
    that cycle.
  - `zrun_uuid` — one per zone run, present on the zone-run event and on every
    fertigation-dose event for that run.
  AppDaemon keeps an in-memory map (`cycle_uuid -> cycle_id`,
  `zrun_uuid -> zrun_id`) for the life of a cycle and uses it to populate foreign
  keys. The identifiers need only be unique and stable for the duration of a
  cycle. The state machine mints them as a microsecond UTC timestamp with a
  scope prefix (`c-`/`z-`), stored in `input_text.cycle_uuid` /
  `input_text.zone_run_uuid` — see "Minting `cycle_uuid`/`zrun_uuid`" below and
  ADR-014.
- **Ordering.** A `watering_fert_dose_complete` event is fired before its zone
  run's `watering_zone_run_complete`, because the dose happens mid-run. AppDaemon
  therefore buffers dose events in memory keyed by `zrun_uuid` and writes them
  only once the parent `zone_runs` row exists (see Event 3).
- **Validation.** Before any write, AppDaemon checks that required fields are
  present and that controlled-vocabulary fields (`trigger_type`, `outcome`,
  `weather_program`, `severity`) hold legal values (per the CHECK constraints in
  `docs/db_schema.sql`). On a violation it logs an error, records a
  `system_events` row describing the rejected payload, and skips the write — it
  does not raise. Every DB connection sets `PRAGMA foreign_keys = ON`
  (per-connection; see §13.2 and the Known Gotchas).

**Event 1 — `watering_preflight_complete`** → INSERT `watering_cycles`

| Field | Type | Required | Maps to |
|-------|------|----------|---------|
| `cycle_uuid` | str | yes | (correlation, not stored) |
| `start_time` | str (UTC) | yes | `start_time` |
| `trigger_type` | str | yes | `trigger_type` (`scheduled`/`manual`/`override`) |
| `rainfall_24h_mm` | float\|null | no | `rainfall_24h_mm` |
| `rainfall_72h_mm` | float\|null | no | `rainfall_72h_mm` |
| `temp_high_c` | float\|null | no | `temp_high_c` |

AppDaemon: INSERT the row; record `cycle_uuid -> cycle_id` (the new `lastrowid`);
set `binary_sensor.watering_cycle_active` on. `end_time`, `outcome`, and `notes`
stay NULL until Event 4.

**Event 2 — `watering_fert_dose_complete`** → buffered, written during Event 3

| Field | Type | Required | Maps to |
|-------|------|----------|---------|
| `zrun_uuid` | str | yes | (correlation, resolves `zrun_id`) |
| `zone_id` | int 1–4 | yes | `zone_id` (denormalized) |
| `timestamp` | str (UTC) | yes | `timestamp` |
| `nutrient_product` | str\|null | no | `nutrient_product` |
| `target_dose_ml` | float\|null | no | `target_dose_ml` |
| `actual_dose_ml` | float\|null | no | `actual_dose_ml` |
| `pump_id` | int 1–3\|null | no | `pump_id` |
| `phase` | 1\|2\|null | no | `phase` |

AppDaemon: append the payload to an in-memory buffer keyed by `zrun_uuid`. No
write yet — the parent `zone_runs` row does not exist until Event 3.

**Event 3 — `watering_zone_run_complete`** → INSERT `zone_runs`, then flush doses

| Field | Type | Required | Maps to |
|-------|------|----------|---------|
| `cycle_uuid` | str | yes | resolves `cycle_id` (FK) |
| `zrun_uuid` | str | yes | (correlation for buffered doses) |
| `zone_id` | int 1–4 | yes | `zone_id` |
| `weather_program` | str | yes | `weather_program` (`off`/`light`/`normal`/`heavy`) — a heavy mid-interval `booster` is mapped to `heavy` here (Phase 7 / ADR-020), so the CHECK vocabulary is unchanged |
| `start_time` | str (UTC) | yes | `start_time` |
| `end_time` | str (UTC)\|null | no | `end_time` |
| `planned_duration_sec` | int\|null | no | `planned_duration_sec` |
| `program_multiplier` | float\|null | no | `program_multiplier` — **threaded from `calculate_zone_runtime`** (the single source) via `run_zone_sequence`→`water_one_zone`→`fire_zone_run_complete`, not re-derived from a static map (ADR-020 review §3). Values: `off` 0.0 / `light` 0.5 / `normal` 1.0 / `heavy` 1.0 (main) / `booster` 0.5, plus the **N==1 single-window heavy = 1.5** edge, which a static map could not reproduce. A booster row is `weather_program='heavy'` + `0.5`; `sensor.zone_N_watering` excludes that pair so the cadence anchor tracks main doses only (was previously always NULL) |
| `aborted` | 0\|1 | yes | `aborted` |
| `abort_reason` | str\|null | no | `abort_reason` |

AppDaemon: resolve `cycle_id` from `cycle_uuid`; compute `actual_duration_sec` as
`end_time − start_time` in seconds (NULL if `end_time` is NULL); set `fertigated`
to 1 if the dose buffer for `zrun_uuid` is non-empty, else 0 — AppDaemon derives
this rather than reading it from the payload, matching the §13.2 definition "true
if fertigation doses exist for this run"; INSERT the `zone_runs` row and record
`zrun_uuid -> zrun_id`; then INSERT every buffered dose for `zrun_uuid` with that
`zrun_id` and clear the buffer.

**Event 4 — `watering_cycle_complete`** → UPDATE `watering_cycles`

| Field | Type | Required | Maps to |
|-------|------|----------|---------|
| `cycle_uuid` | str | yes | resolves `cycle_id` |
| `end_time` | str (UTC) | yes | `end_time` |
| `outcome` | str | yes | `outcome` (`completed`/`aborted`/`error`) |
| `notes` | str\|null | no | `notes` |

AppDaemon: resolve `cycle_id`; UPDATE the row's `end_time`, `outcome`, `notes`;
set `binary_sensor.watering_cycle_active` off; drop this cycle's map entry and any
remaining buffer entries for it.

**Event 5 — `watering_system_event`** → INSERT `system_events`

| Field | Type | Required | Maps to |
|-------|------|----------|---------|
| `timestamp` | str (UTC) | yes | `timestamp` |
| `event_type` | str | yes | `event_type` |
| `severity` | str | yes | `severity` (`info`/`warning`/`error`/`critical`) |
| `entity_id` | str\|null | no | `entity_id` |
| `value_before` | str\|null | no | `value_before` |
| `value_after` | str\|null | no | `value_after` |
| `notes` | str\|null | no | `notes` |

AppDaemon: INSERT immediately. These events are not tied to a cycle and need no
correlation.

**Unresolved correlation.** If an event arrives whose `cycle_uuid`/`zrun_uuid` is
not in the map — for example AppDaemon restarted mid-cycle and lost its in-memory
state — AppDaemon logs a warning, records a `system_events` row noting the dropped
record, and continues. The operational DB is fire-and-forget reporting and is not
part of the watering or safety path (§13.1), so a gap here never affects
irrigation. Surviving an AppDaemon restart would require persisting the
identifiers as columns in the schema; that is deliberately not done, because the
added schema surface is not justified for non-safety reporting data.

**Minting `cycle_uuid`/`zrun_uuid` (decided — ADR-014).** The state machine mints
each identifier as a microsecond-precision UTC timestamp captured at the start of
its scope, with a scope prefix so a cycle id and a zone-run id can never collide
even in the same microsecond:

```
cycle_uuid   {{ 'c-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') }}   e.g. c-20260805043012123456
zrun_uuid    {{ 'z-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') }}   e.g. z-20260805043118654321
```

Each value is written to a reusable `input_text` helper at its minting point and
read unchanged by every later event in that scope:

- `input_text.cycle_uuid` — set by `state_preflight_check` just before Event 1;
  read by Events 3 and 4.
- `input_text.zone_run_uuid` — **fertigation path only.** Fert runs are
  single-zone and strictly sequential, so the shared helper is set at each fert
  zone-run start and read by that run's Event 2 doses and its Event 3.

**Plain watering `zrun_uuid` (parallel-safe — ADR-015).** Plain watering supports
a `parallel` zone-sequencing mode, so its zone runs are **not** strictly sequential
and cannot share one helper (a second zone would overwrite it before the first
zone's Event 3 fires). Instead, `run_zone_sequence` mints each zone's `zrun_uuid`
as a **local, run-scoped variable** and appends the zone id so two `parallel:`
branches minting in the same microsecond stay distinct:
`zrun_uuid = 'z-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') ~ '-' ~ zone_id`. The value
is carried in that zone's Event 3 payload directly (plain watering has no Event 2
that needs to cross-reference it, so no shared helper is required). AppDaemon
treats it as an opaque string, so the suffixed form is contract-compatible.

The `cycle_uuid` helper is overwritten each cycle, which is safe because cycles
never overlap (§13.1). Uniqueness is required only within a single live cycle's
in-memory map, so a microsecond timestamp under that invariant is provably distinct
— it needs no native UUID support and no live HA-version check (HA Jinja has no UUID
filter; `utcnow().strftime` is already used in `logging_scripts.yaml`). The value is
opaque to AppDaemon and must not be parsed back into a time. See ADR-014 (scheme)
and ADR-015 (the plain-watering parallel-run resolution).

---

### 13.4 Decision Query Sensors

AppDaemon updates these HA sensors in response to decision queries from the
state machine:

| Sensor | Query | Used By |
|--------|-------|---------|
| `sensor.zone_{1-4}_fert_delivered_14d_ml` | Total fert dose per zone last 14 days | Phase 3.3 eligibility check |
| `binary_sensor.watering_cycle_active` | Is a cycle currently running? | State machine / safety |

Additional sensors to be defined as query patterns emerge.

---

### 13.5 Archive Strategy

- **Ongoing backup:** SQLite database file (`/homeassistant/watering_ops.db`) included in HA automated backup
- **Seasonal export:** the AppDaemon `db_export` app (`DbSeasonalExport`) exports
  all four tables as dated CSV files. It is triggered by the HA event
  `watering_seasonal_export`, which the winterization automation
  (`home-assistant/packages/watering_db/db_automations.yaml`) fires when
  `input_boolean.system_winterized` transitions OFF -> ON.
- **Export location:** `/homeassistant/watering_exports/` (inside the HA config
  tree, so the CSVs are captured by HA backups). Configurable via `export_dir` in
  the AppDaemon `apps.yaml`.
- **File naming:** `watering_cycles_YYYY.csv`, `zone_runs_YYYY.csv`,
  `fertigation_doses_YYYY.csv`, `system_events_YYYY.csv`
- **Year-filtered:** each file holds only the rows whose UTC timestamp falls in
  that calendar year (filtered on each table's time column: `start_time` for
  `watering_cycles`/`zone_runs`, `timestamp` for `fertigation_doses`/`system_events`),
  so the yearly files partition the data. The year defaults to the current UTC
  year and can be overridden via the event payload (`event_data.year`) for testing
  or backfill. An empty result still produces a header-only CSV, so the archive set
  is always complete.
- **Audit:** each export writes one `system_events` row recording the outcome
  (`event_type = 'seasonal_export'`, `info` with per-table row counts, or
  `critical` on failure). The export is otherwise read-only and never raises, so a
  failure cannot disrupt watering.
- **Retention:** Database accumulates across seasons; CSV archives kept indefinitely

**Reference:** ADR-011 (in `docs/programming-notes.md`)

---

## Change Log

### Version 1.9.0
**2026-08-25**
**ADR-021 accepted — moisture-primary §3.2 program selection (design of record; implementation HELD)**
- **§3.2 (intensity `wp` reworked):** replaced the weather-only decision tree with a
  **moisture-primary** one — soil moisture drives the base intensity (wet-skip at
  `off_moisture_min`; ladder light/normal/heavy), weather modulates ±1 step, a capped 2-step
  forecast-rain downgrade (whole-day-to-midnight POP > 80 % ∧ ≥ 5 mm, floored heavy→light).
  Temperature signal **de-lagged** (forecast/current high, not the 3-day average — partially
  supersedes ADR-004). Weather-only **fallback** when a zone has no mapped/available moisture
  sensor. The **ADR-020 cadence/booster layer is UNCHANGED**. Added a STATUS banner: the
  deployed code still runs the interim weather-only tree (now the fallback) until the moisture
  hardware lands.
- **§9.1 (soil sensors DECIDED):** the WH52 + SEN0600 **hybrid** is now the plan of record
  (was "undecided"); recorded the sensor→zone mapping, WH52 native 0–100 %, SEN0600 pulse-poll.
- **Decision recording folded into ADR-018** (not a new table): ADR-018's already-accepted
  weather-observations DB (`zone_decisions` / `zone_runs.decision_criteria` JSON, always-on
  capture of run/skip/parked windows) absorbs the moisture-primary inputs; ADR-018 amended,
  and its two deferred items (temp metric, threshold RestoreEntity) resolved by ADR-021.
- **Reference:** ADR-021 (programming-notes.md); ui_design §7 #1 rescoped to a "Current Status"
  tile. Header v1.8.1 → v1.9.0. **Implementation + deploy HELD until moisture hardware is
  installed & calibrated.**

### Version 1.8.1
**2026-08-23**
**ADR-020 cadence-rework code-review fixes (downstream consumers)**
- **§3.2 (booster retry, Fix #4b):** The heavy booster now **retries** on each target
  (evening) window from the midpoint until it lands exactly once per interval, instead of
  the former single-shot `[mid, mid+1)` band. "Pending" is tracked by the new
  `sensor.zone_N_last_booster` (last `(heavy, 0.5×)` run) vs `sensor.zone_N_watering`
  (last main dose): a booster fires while `mid <= days_since < N` and no booster has been
  recorded since the last main dose. A missed evening (override/disabled window) is picked
  up on a later one.
- **§13.3.1 (multiplier threading, Fix #3):** `program_multiplier` is now **threaded from
  `calculate_zone_runtime`** (the single source) through `run_zone_sequence` →
  `water_one_zone` → `fire_zone_run_complete`, replacing a static per-site map. This is
  the only way the recorded multiplier matches the actual runtime for the **N==1
  single-window heavy = 1.5×** edge. `calculate_zone_runtime` now returns `multiplier`
  alongside `program`/`runtime_minutes`.
- **Notification (Fix #2):** the end-of-cycle watering summary now includes `booster` runs
  (labeled "booster (0.5×)"), so a booster-only evening no longer reports "complete, no
  zones."
- **Fert helpers (Fix #1):** the 12 flow-rate template maps aligned to the authoritative
  multipliers (`heavy` 1.0, added `booster` 0.5) with a KEEP-IN-SYNC comment; the N==1
  heavy edge + booster fert dosing are TODO-deferred to the fert phase (hardware-blocked).
- **Fix #6:** corrected the `state_window_check` booster comment (always evening; no
  odd/even parity branch; no "afternoon" window).
- **Reference:** ADR-020 review (programming-notes.md). Header v1.8.0 → v1.8.1.

### Version 1.8.0
**2026-08-22**
**Per-zone watering cadence + master enable; heavy split → mid-interval booster (Phase 7)**
- **§3.1:** Added `booster` to each `zone_N_program` (SYSTEM-set only). Documented the
  per-zone `input_boolean.zone_N_enabled` (hard on/off) and
  `input_number.zone_N_watering_interval_days` (cadence).
- **§3.2:** The weather decision tree (intensity → `wp`) is now wrapped by two Phase 7
  cadence layers — the **enable gate** and the **interval/booster gate** — producing the
  final program. This **closes ADR-015 D-C** (deferred cadence gate) now that
  `sensor.zone_N_watering` supplies the last-main-dose anchor. A rained-off due day does
  not consume the interval; the booster re-evaluates weather at the midpoint window.
- **§3.3:** **Retired the same-day heavy split.** Runtime is now window-independent:
  `heavy = 1.0×` (MAIN) + a separate `booster = 0.5×` at the interval midpoint (N/2).
  Kept the `N==1` single-window exception (full `1.5×` single dose, no booster).
- **§4.1:** Retired the system-wide `input_number.watering_cycle_days` (per-zone interval
  replaces it).
- **§7.1:** Data-flow "Check last watering date" step is now implemented (the cadence gate).
- **DB boundary:** the booster is recorded as `weather_program='heavy'` +
  `program_multiplier=0.5` (see §13.3.1) — `zone_runs` CHECK vocabulary and the AppDaemon
  writer are unchanged. `sensor.zone_N_watering` excludes `(heavy, 0.5)` so the anchor
  tracks main doses only.
- **Reference:** ADR-020 (programming-notes.md). Header v1.7.0 → v1.8.0.

* **2025-10-01**: 
  - Added Section 4.4: Fertilizer Pump Calibration
    - Calibration coefficient storage (~30 new helpers: 9 per pump × 3 pumps)
    - Runtime dose calculation algorithm (dose → flow → command via calibration curve)
    - Calibration status template sensors (VALID/WARNING/EXPIRED/POOR)
  - Updated Section 4.3: Fertigation Configuration
    - Added calculated pump command sensors (display what will be sent to pumps)
  - Updated Section 6.4: Fertilizer Control Scripts
    - Added calibration integration to start_dosing_pumps script
  - Updated Section 8.4: Per-Zone Configuration Card
    - Added calculated pump command displays
  - Added Section 8.6: Fertilizer Pump Calibration Card (dashboard spec)
  - Updated Section 11.2: Fertigation Calibration
    - Complete rewrite with reference to /docs/fert_pump_cal_v2.md
  - Total helper count: ~210 (was ~180)
- **2025-10-04:** Section 6.5: Added explicit filename `watering_safety.yaml` to header for consistency with other sections
### Version 1.1 
**2025-10-05**
- 1.2 Hardware Summary: Clarified GPIO pin assignments (GPIO33=Low, GPIO32=Low-Low)
- 3.1 Zone Program Entities: Changed from crop-specific names (raspberries/blueberries) to generic (zone_1, zone_2, zone_3, zone_4)
- 3.3 Runtime Calculation: Updated zone ID references to numeric format
- 4.2 Per-Zone Configuration: Updated all helper entity names from crop-specific to zone_X pattern
- 4.3 Fertigation Configuration: Updated fertigation datetime/rate entities to zone_X pattern
- 5.2 Automation-Level Safety: Added filter behavior notes for float switches
- 5.1A ESPHome Relay Control Architecture (NEW): Complete documentation of relay control design including:
  - Hardware-level safety features
  - Template switch naming convention (relay_pump_main, relay_zone_1-4, relay_fert_bypass_valve, etc.)
  - Script architecture (raw coils → safe scripts → ON sequences → template switches)
  - 24V cabinet power management and auto-off behavior
- 7.1 Morning Window Example: Updated entity names to new relay_* convention (relay_pump_main, relay_zone_1, etc.)
- 8.6 ESPHome Device Dashboard (NEW): Added section documenting relay controls, tank monitoring, and solar system monitoring
- 9.1 Future Extensions: Updated soil sensor integration details with RS-485 addressing
### Version 1.2
- **2025-10-09**
- Added Section 12: Notification System
  - Multi-channel strategy (WhatsApp + Email)
  - Tiered notification approach (Critical/High/Standard)
  - Daily email self-test with failure detection
  - Monthly WhatsApp test with user confirmation
  - De-winterization testing protocol
  - Winterization-aware notification blocking
  - Integration with state machine preflight checks
  - API configuration for CallMeBot and Gmail
  - ~8 new configuration entities (booleans + sensors)
- Updated Section 7.1: Added post_cycle_relief notification trigger for watering summaries
- Updated preflight_check logic: Now checks notification_system_error boolean  
### Version 1.2.1
- **2025-10-13**
- Section 12: Notification System implementation complete
  - 24/27 tests passed (service integration, daily/monthly tests, de-winterization, tiers, winterization)
  - 3 integration tests blocked (requires watering system Phases 4-5)
  - Created 4 package files (notification_helpers, notification_config, notification_scripts, notification_tests)
  - Daily email self-test operational, monthly WhatsApp test scheduled
### Version 1.2.2
- **2025-10-14**
- Section 5: Corrected ESP32 entity names to {domain}.{device_name}_{id}
- Section 7: Corrected ESP32 entity names to {domain}.{device_name}_{id}
### Version 1.2.3
- **2025-10-15**
- Section 4.1: Changed input_time. to input_datetime
### Version 1.2.4
**2025-10-16**
- **Package Reorganization**: Updated all file paths to reflect feature-based subfolder structure
  - Implemented files moved to: notification/, weather/, watering_helpers/
### Version 1.3.1
- Section 2.1: Add three error states to state machine
- Section 3.3: Update runtime calculation
- Section 4.7: Add input_text.cycle_event_log
- Section 5.4: Add zone control scripts
  - Planned files organized into: watering_core/, watering_zone/, watering_pump/, watering_fert/, watering_safety/
  - All file path references in Sections 6.1-6.6 updated to new locations
### Version 1.3.2
**2025-11-07**
- Section 5.5: Add pump scripts
### Version 1.4.0
**2025-11-08**
**V2 Fertigation Program Design - Major Update**
- **Configuration Entities (68 new zone helpers):**
  - 4× Light program dose control booleans (Section 4.2.6)
  - 48× Soil moisture thresholds (3 per season × 4 seasons × 4 zones)
  - 16× Fertigation 14-day targets (4 seasons × 4 zones)
- **System Tracking (9 new entities - Section 4.7):**
  - 1× Current fertigation zone tracker (input_text)
  - 4× Zone fertigation active sensors (binary_sensor)
  - 4× Rolling window event counters (history_stats)
- **State Machine:** Enhanced Section 2.2 with V2 eligibility logic
- **Scripts:** Updated Section 5.6 (renamed from 5.5) with V2 requirements
- **Safety:** Added tank level pre-check as first system-wide block (Section 7.1)
- **Design:** Rolling 14-day window replaces fixed intervals
- **Triggers:** Multi-condition hierarchy (hard blocks + prevailing criteria)
- **Sensors:** Soil moisture primary, rain fallback, temperature removed from fert triggers
- **Total helpers:** ~232 (was ~164)
**2025-11-11**
- Add 5.6 Fert Scripts
### Version 1.5.0
**2026-04-08**
- **Section 6:** Added `watering_appdaemon/` subfolder to HA package structure (Phase 3.5)
- **Section 6:** Added `docs/db_schema.sql` to repository docs listing
- **Section 13 (new):** Operational Database Architecture
  - Section 13.1: Overview (MariaDB + AppDaemon two-layer architecture)
  - Section 13.2: Full schema for all four tables
  - Section 13.3: Write trigger points and HA event names
  - Section 13.4: Decision query sensors
  - Section 13.5: Archive strategy
- **Reference:** ADR-011

### Version 1.5.1
**2026-06-28**
**Operational Database -- engine changed to SQLite (supersedes MariaDB)**
- **Section 13.1:** Layer 1 changed from the MariaDB add-on to a single SQLite
  database file (`/homeassistant/watering_ops.db`), separate from the recorder.
  Layer 2 (AppDaemon bridge) unchanged. Removed MariaDB references.
- **Section 13.2:** Noted that the table lists logical types; the SQLite
  physical mapping and all constraints live in `docs/db_schema.sql`.
- **Section 13.5:** Backup line updated to reference the SQLite database file.
- **Rationale:** tiny single-writer workload; SQLite removes the MariaDB
  add-on, DB/user-via-add-on-config, driver, and charset setup with no loss of
  capability. Full reasoning in ADR-011 (SQLite revision).
- **Created:** `docs/db_schema.sql` (SQLite schema) and `docs/db_setup_guide.md`
  (HA-side setup). ADR-011 itself was updated in place in `docs/programming-notes.md`
  (no standalone ADR file).
- **Schema refinement:** `fertigation_doses.pump_id` stores the logical pump number
  (1–3), not the raw Modbus address (0x02–0x04) — more robust to re-addressing/rewiring.
  No `UNIQUE(cycle_id, zone_id)` on `zone_runs` (a zone may run more than once per cycle);
  noted in impl_roadmap.md §3.5 for future visibility.
- **Follow-on:** impl_roadmap.md Phase 3.5 has been updated to the SQLite design to match.

### Version 1.5.2
**2026-06-30**
**Operational Database -- event payload contract defined**
- **Section 13.3.1 (new):** Event Payload Schemas — the full state-machine ->
  AppDaemon contract for all five DB-write events (`watering_preflight_complete`,
  `watering_fert_dose_complete`, `watering_zone_run_complete`,
  `watering_cycle_complete`, `watering_system_event`). Per-event field tables
  (type / required / target column), plus shared conventions: payload-carried UTC
  timestamps, `cycle_uuid`/`zrun_uuid` correlation resolved via an in-memory map,
  dose events buffered until the parent `zone_runs` row exists, AppDaemon-side
  validation of CHECK vocabularies, and the unresolved-correlation behaviour after
  an AppDaemon restart.
- **Section 13.3:** "Note" updated to point at §13.3.1 (contract now defined, not
  merely pending).
- **Section 13.5:** Archive Strategy expanded to the implemented design — the
  `db_export` AppDaemon app triggered by the `watering_seasonal_export` event (fired
  by the winterization automation), year-filtered CSVs under
  `/homeassistant/watering_exports/`, header-only files when a year is empty, and a
  `system_events` audit row per export.
- **Decisions captured in the contract:** timestamps are authoritative from the
  firing component (not stamped on receipt); `fertigated` is derived by AppDaemon
  from the dose buffer, not sent in the payload; correlation identifiers are
  in-memory only (no schema columns) since the DB is non-safety, fire-and-forget
  reporting. UUID generation mechanism left as a Phase 4 detail (HA Jinja has no
  native UUID filter — confirm approach when Phase 4 is built).

### Version 1.7.0
**2026-08-15**
**Weather station selected; soil sensing gains a wireless hybrid option**
- **Section 9.4 (new):** Local Weather Station (selected, hardware pending) —
  Ecowitt GW1200 gateway + WS90 7-in-1 array + WH40 tipping-bucket rain, 868 MHz,
  cellar-window sited on WiFi. Trusted rainfall = WH40 (piezo rain de-prioritised);
  solar-radiation/UV logged for future ET tuning. Integration deferred (add under
  `weather/` beside `dwd_brightsky.yaml`; repoint §3.2 rain/temp sensors) — ADR to
  follow at implementation.
- **Section 9.1:** Restructured into sensor-agnostic integration goals + two
  documented options. Option A = wired RS-485 (DFRobot SEN0600 plan of record; noted
  SEN0601 adds EC, SEN0604 adds pH, and the buriable-at-depth advantage). Option B
  (new) = wireless Ecowitt WH52 3-in-1 hybrid (moisture/temp/EC on the GW1200, off
  the Modbus bus), with its accuracy limits (relative capacitive %, coarse EC) and
  the surface-depth caveat vs deep-rooted beds; hybrid intent = WH52 for shallow
  zones, a wired DFRobot probe where depth/precise EC matters. Undecided; adopting it
  would supersede the SEN0600 plan and warrant an ADR.
- **Section 1.2:** Added the planned Ecowitt weather subsystem; annotated the soil
  sensor line with the two options.
- **Header:** v1.6.1 → v1.7.0; date refreshed to 2026-08-15.
- No code changes — hardware selection/documentation only.

### Version 1.6.1
**2026-08-06**
**Fert-event flush reconciled to fert_prog_design.md (drift removal)**
- **Section 2.2 (fert flow):** Corrected the dose-phase flush to match the canonical
  `fert_prog_design.md` §6.1/§6.3 — flush **2 min** (was 5 min) with the **fert line
  R7 open** (was bypass R6, which would not clear the injection path), and flush after
  **each** dose phase (phase 1 previously had none). R7→R6 toggle happens only after
  the phase-2 flush.
- **Context:** Companion to the moorbeet plan §6.5 reconciliation — the 90–120 min
  "pulse pause" was removed as unjustified at 2.3 L/h drip rates; split-dose +
  per-phase 2-min flush is now the single canonical fert-event shape.
- No code changes (fert path deferred — RS-485 unwired).

### Version 1.6.0
**2026-08-05**
**Minor bump — entering Phase 4 (state machine); design decision-complete**
- Marks the transition into Phase 4 implementation (program tag `v0.2.0`). The full
  Phase 4 plain-watering control design is settled in ADR-015 (D1–D4) + its addenda
  (D-A…D-H, A1/A2, revised D-F guard model); no state-machine YAML written yet.
- **Section 5.3:** Replaced the two outdated code sketches with pointers to current
  behaviour — the implemented `emergency_stop` (all 16 relays + verify/repair, critical
  notification, latched `error_e_stop`; see watering_safety_scripts.yaml) and the revised
  ADR-015 D-F manual-override **guard** model (reject mid-cycle / ack-from-error /
  engage-from-idle; no auto-abort). Same for `winterized`.
- **Reference:** ADR-015 (+ its D-A…D-H and A1/A2 addenda), programming-notes.md.

### Version 1.5.5
**2026-08-05**
**State machine reconciled to the implemented 15 states (Phase 4 prep)**
- **Section 2.1:** Master state option list corrected to the real **15** states
  (`config_helpers.yaml` is canonical). Removed the duplicated `error_tank_low`;
  added the missing `winterized` and `error_e_stop`; grouped and commented the
  set (operational / control / error). The list had lagged at 12 unique.
- **Section 2.2:** Added transition logic that existed in code but not in this
  doc — `ANY → error_e_stop` (via `script.emergency_stop`, latched),
  `ANY → error_valve_interlock`, `ANY → error_relay_state`, and `idle ⇄ winterized`.
  Expanded the `error_comms_lost` recovery note to reference the Phase 3.4 Part A
  fail-fast + Part B reactive-recovery automation.
- **Section 2.2 (preflight):** Replaced the single tank check with the **two-tier
  gate** — plain watering gates on **Low-Low** (GPIO32), fertigation on the
  earlier **Low** (GPIO33) so a dose is never cut off without its flush. Matches
  the implemented `start_main_pump` gate.
- **Fertigation eligibility + Section (fert preflight):** Fixed the winterization
  entity name `input_boolean.winterization_mode` → `input_boolean.system_winterized`
  (also corrected in `fert_prog_design.md`).
- **Header:** version stamp corrected v1.5.2 → v1.5.5 (had lagged the change log).
- **Reference:** ADR-002 addendum (programming-notes.md). No code changes — the
  runtime entity was already correct; the design docs were brought up to it.

### Version 1.5.4
**2026-08-05**
**Operational Database -- correlation-ID minting decided (Phase 4 prep)**
- **Section 13.3.1:** The "Open for Phase 4" note on how the state machine mints
  `cycle_uuid`/`zrun_uuid` is resolved. Decision: microsecond UTC timestamp
  (`utcnow().strftime('%Y%m%d%H%M%S%f')`) with a `c-`/`z-` scope prefix, stored in
  reusable helpers `input_text.cycle_uuid` / `input_text.zone_run_uuid` and read
  unchanged by every related event. Chosen over an execution-`context.id` ULID
  because it depends only on `utcnow().strftime` (already used in
  `logging_scripts.yaml`) and needs no live HA-version verification. The
  "Correlation identifiers" shared-conventions bullet updated to match; the field
  names `cycle_uuid`/`zrun_uuid` are unchanged (they name the role, not the format).
- **Reference:** ADR-014 (programming-notes.md). Closes START_HERE follow-up #1.

### Version 1.5.3
**2026-07-31**
**Operational Database -- `system_events.severity` gains `error`**
- **Section 13.2 / 13.3.1:** `system_events.severity` controlled vocabulary
  extended from `info` / `warning` / `critical` to
  **`info` / `warning` / `error` / `critical`**, matching HA's `system_log`
  levels (minus `debug`). This lets a fired event's DB severity map 1:1 to its
  `system_log` level with no lossy remap, and restores the `error`-vs-`critical`
  distinction (routine contained aborts = `error`; catastrophic, needs physical
  intervention = `critical`, e.g. pump runaway). `debug` deliberately excluded —
  transient diagnostics belong in `system_log`, not the persistent record.
- **Context:** part of the Phase 3.1/3.2 retrofit that routes script logging
  through `script.log_system_event` -> the `watering_system_event` bus event ->
  the AppDaemon `DbEventWriter` app, persisting safety/error/info events to
  `system_events` (replacing the transient `input_text.cycle_event_log`).
- **Migration:** existing `watering_ops.db` needs a one-time `system_events`
  table rebuild (SQLite cannot `ALTER` a CHECK; the bootstrap's
  `CREATE TABLE IF NOT EXISTS` skips it on an existing DB). See `db_schema.sql`
  change log and the ADR-011 addendum in `programming-notes.md`.
