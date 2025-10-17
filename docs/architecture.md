# Watering System Architecture v1.2.4

**Date:** 2025-10-16 
**Status:** Phase 3  
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
- **Sensors:** Float switches (GPIO33=Low, GPIO32=Low-Low), future soil sensors (0x05-0x07)
- **Power:** 12V LiFePO4 + solar, 24V cabinet for RS-485 (Relay 10 controlled)

---

## 2. State Machine Design

### 2.1 Master State Entity
```yaml
input_select.watering_system_state:
  options:
    - idle
    - window_check          # Evaluating what needs to run
    - preflight_check       # Safety checks before starting
    - watering_plain        # Plain watering (no fertilizer)
    - fert_prep             # Preparing for fertigation
    - fert_dose_phase1      # First dose + partial watering
    - fert_dose_phase2      # Second dose + remaining water (or flush)
    - post_cycle_relief     # Pressure relief valve sequence
    - error_tank_low        # Tank level alarm
    - error_comms_lost      # Modbus communication failure
    - manual_override       # User has taken manual control
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
  - Tank levels OK (GPIO33 Low switch = HIGH)
  - 24V cabinet available (if using RS-485 devices)
  - No existing watering in progress
- Branch:
  - If fertigation due → FERT_PREP
  - Otherwise → WATERING_PLAIN

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
- Trigger: Modbus communication timeout (no response from 0x01 for 10s)
- Action:
  - Attempt pump stop command
  - Set error state
  - Send notification
- Recovery: Manual reset after comms restored

---

## 3. Per-Zone Program States

### 3.1 Zone Program Entities
```yaml
input_select.zone_1_program:
  options: [off, light, normal, heavy]

input_select.zone_2_program:
  options: [off, light, normal, heavy]

input_select.zone_3_program:
  options: [off, light, normal, heavy]

input_select.zone_4_program:
  options: [off, light, normal, heavy]
```

### 3.2 Program Selection Logic (per zone)

Evaluated during **WINDOW_CHECK** state:

```python
# Pseudocode for zone program determination
def select_zone_program(zone_id):
    rain_24h = sensor.brightsky_rain_24h
    rain_72h = sensor.brightsky_rain_72h
    temp_avg_3day = (calculate from brightsky history)
    season = input_select.season  # spring/summer/fall/winter
    
    # Load zone-specific thresholds (configurable per season)
    thresholds = get_zone_thresholds(zone_id, season)
    
    # Decision tree
    if rain_72h > thresholds.rain_off_mm:
        return "off"
    elif rain_24h > thresholds.rain_light_mm:
        return "light"
    elif temp_avg_3day > thresholds.temp_heavy_c and rain_72h < thresholds.rain_min_mm:
        return "heavy"
    elif temp_avg_3day > thresholds.temp_normal_c:
        return "normal"
    else:
        return "light"
```

### 3.3 Runtime Calculation (per zone)

```python
# Zone runtime = base_time × program_multiplier
# Zone ID is numeric: zone_1, zone_2, zone_3, zone_4
base_runtime = input_number.zone_{id}_base_runtime_min  # User configured

multipliers = {
    "off": 0.0,
    "light": 0.5,
    "normal": 1.0,
    "heavy": 1.5
}

actual_runtime = base_runtime × multipliers[program]
```

---

## 4. Configuration Entities (Input Helpers)

### 4.1 System Configuration
```yaml
# Zone Sequencing
input_select.zone_sequencing_mode:
  options: [parallel, sequential]
  initial: parallel

# Watering Schedule
input_number.watering_cycle_days:
  min: 1
  max: 14
  step: 1
  initial: 3
  unit: days

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
```yaml
script:
  emergency_stop:
    alias: "Emergency Stop - All Systems"
    icon: mdi:stop-circle
    sequence:
      - service: switch.turn_off
        target:
          entity_id:
            - switch.watering_system_relay_1_main_pump
            - switch.watering_system_relay_2_zone_1
            - switch.watering_system_relay_3_zone_2
            - switch.watering_system_relay_4_zone_3
            - switch.watering_system_relay_5_zone_4
            - switch.watering_system_relay_6_fert_bypass
            - switch.watering_system_relay_7_fert_line
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'idle'
      - service: notify.mobile_app
        data:
          message: "Emergency stop activated. System reset to idle."
```

### Manual Override Mode
```yaml
input_boolean.manual_override_active:
  name: "Manual Override Mode"
  icon: mdi:hand-back-right

# When enabled, state machine pauses
automation:
  - alias: "Manual Override - Pause State Machine"
    trigger:
      - platform: state
        entity_id: input_boolean.manual_override_active
        to: 'on'
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'manual_override'
```

### 5.3 User-Level Controls

**Emergency Stop Script**
```yaml
script:
  emergency_stop:
    alias: "Emergency Stop - All Systems"
    icon: mdi:stop-circle
    sequence:
      - service: switch.turn_off
        target:
          entity_id:
            - switch.watering_system_relay_1_main_pump
            - switch.watering_system_relay_2_zone_1
            - switch.watering_system_relay_3_zone_2
            - switch.watering_system_relay_4_zone_3
            - switch.watering_system_relay_5_zone_4
            - switch.watering_system_relay_6_fert_bypass
            - switch.watering_system_relay_7_fert_line
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'idle'
      - service: notify.mobile_app
      #TODO: Update to current notification architecture
        data:
          message: "Emergency stop activated. System reset to idle."
```

**Manual Override Mode**
```yaml
input_boolean.manual_override_active:
  name: "Manual Override Mode"
  icon: mdi:hand-back-right

# When enabled, state machine pauses
automation:
  - alias: "Manual Override - Pause State Machine"
    trigger:
      - platform: state
        entity_id: input_boolean.manual_override_active
        to: 'on'
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.watering_system_state
        data:
          option: 'manual_override'
```

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
│   │   │   └── fert_helpers.yaml     # Dosing rates, calibration
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
  - Check last watering date
  - Check fertigation schedule
  - Evaluate weather conditions per zone
  - Set zone programs (off/light/normal/heavy)
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
  ↓
  STATE: FERT_DOSE_PHASE1 → FERT_DOSE_PHASE2
  ↓
  Script: fert_dose_phase2
    - [If normal/heavy] Start dosing, run 50%
    - [If light] Skip to flush
    - Open bypass (switch.watering_system_relay_6_fert_bypass)
    - Flush 5min
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
- DFRobot SEN0600 RS-485 sensors (addresses 0x05-0x07)
- Requires 24V cabinet enable before reading
- Add condition: "Skip if soil moisture > threshold"
- Override weather-based program selection
- Per-zone moisture targets
- Integrate with zone_X program selection logic

### 9.2 Flow Rate Monitoring (Phase 4)
- Detect zone valve failures (no flow when expected)
- Leak detection (flow when no zones open)
- Proportional dosing (fertilizer rate tied to actual flow)

### 9.3 Energy Optimization (Phase 4)
- Delay watering if battery SOC < threshold
- Prefer watering during solar generation hours
- Track energy consumption per cycle

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

## Change Log

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
  - Planned files organized into: watering_core/, watering_zone/, watering_pump/, watering_fert/, watering_safety/
  - All file path references in Sections 6.1-6.6 updated to new locations
