# Entity ID Reference

**Last Updated:** 2025-10-14  
**Purpose:** Canonical mapping of ESPHome entities to Home Assistant entity IDs

---

## Watering System Entity ID Pattern

ESPHome entities are prefixed with the device name and derived from the `name:` field (not `id:`):

```
{platform}.{device_name}_{slugified_name}
```

Example:
```yaml
# ESPHome config:
esphome:
  name: watering-system

switch:
  - platform: template
    id: relay_pump_main              # Internal ESPHome ID
    name: "Relay 1 - Main Pump"      # Generates entity_id
    
# Home Assistant entity:
switch.watering_system_relay_1_main_pump
```

---

## Watering System Switches (Relays)

| ESPHome ID | ESPHome Name | Home Assistant Entity ID | Function |
|------------|--------------|-------------------------|----------|
| `relay_pump_main` | "Relay 1 - Main Pump" | `switch.watering_system_relay_1_main_pump` | Main irrigation pump |
| `relay_zone_1` | "Relay 2 - Zone 1" | `switch.watering_system_relay_2_zone_1` | Zone 1 valve |
| `relay_zone_2` | "Relay 3 - Zone 2" | `switch.watering_system_relay_3_zone_2` | Zone 2 valve |
| `relay_zone_3` | "Relay 4 - Zone 3" | `switch.watering_system_relay_4_zone_3` | Zone 3 valve |
| `relay_zone_4` | "Relay 5 - Zone 4" | `switch.watering_system_relay_5_zone_4` | Zone 4 valve |
| `relay_fert_bypass_valve` | "Relay 6 - Fert Bypass" | `switch.watering_system_relay_6_fert_bypass` | Fertilizer bypass valve |
| `relay_fert_line_valve` | "Relay 7 - Fert Line" | `switch.watering_system_relay_7_fert_line` | Fertilizer injection line valve |
| `relay_8` | "Relay 8" | `switch.watering_system_relay_8` | Unused/reserved |
| `relay_pressure_relief` | "Relay 9 - Pressure Relief" | `switch.watering_system_relay_9_pressure_relief` | Pressure relief valve |
| `relay_24v_cabinet` | "Relay 10 - 24V Cabinet" | `switch.watering_system_relay_10_24v_cabinet` | 24V cabinet enable |
| `relay_11` | "Relay 11" | `switch.watering_system_relay_11` | Future expansion |
| `relay_12` | "Relay 12" | `switch.watering_system_relay_12` | Future expansion |
| `relay_13` | "Relay 13" | `switch.watering_system_relay_13` | Future expansion |
| `relay_14` | "Relay 14" | `switch.watering_system_relay_14` | Future expansion |
| `relay_15` | "Relay 15" | `switch.watering_system_relay_15` | Future expansion |
| `relay_16` | "Relay 16" | `switch.watering_system_relay_16` | Future expansion |

---

## Watering System Binary Sensors (Float Switches)

| ESPHome ID | ESPHome Name | Home Assistant Entity ID | Function |
|------------|--------------|-------------------------|----------|
| `low_water_level` | "Low Water Level" | `binary_sensor.watering_system_low_water_level` | Tank low alarm (GPIO33) |
| `low_low_water_level` | "Low Low Water Level" | `binary_sensor.watering_system_low_low_water_level` | Tank empty alarm (GPIO32) |

---

## Watering System Sensors (Victron BLE)

| ESPHome ID | ESPHome Name | Home Assistant Entity ID | Function |
|------------|--------------|-------------------------|----------|
| `mppt_battery_voltage` | "MPPT Battery Voltage" | `sensor.watering_system_mppt_battery_voltage` | Battery voltage (V) |
| `mppt_battery_current` | "MPPT Battery Current" | `sensor.watering_system_mppt_battery_current` | Battery current (A) |
| `mppt_load_current` | "MPPT Load Current" | `sensor.watering_system_mppt_load_current` | Load current (A) |
| `mppt_pv_power` | "MPPT PV Power" | `sensor.watering_system_mppt_pv_power` | Solar power (W) |
| `mppt_yield_today` | "MPPT Yield Today" | `sensor.watering_system_mppt_yield_today` | Daily solar yield (Wh) |
| `mppt_charger_state` | "MPPT Charger State" | `sensor.watering_system_mppt_charger_state` | Charger state text |
| `mppt_error_reason` | "MPPT Error Reason" | `sensor.watering_system_mppt_error_reason` | Error description |
| `mppt_error_state` | "MPPT Error State" | `binary_sensor.watering_system_mppt_error_state` | Error flag |
| `mppt_fault_state` | "MPPT Fault State" | `binary_sensor.watering_system_mppt_fault_state` | Fault flag |

---

## Watering System Common Usage Examples

### Emergency Stop All Relays
```yaml
service: switch.turn_off
target:
  entity_id:
    - switch.watering_system_relay_1_main_pump
    - switch.watering_system_relay_2_zone_1
    - switch.watering_system_relay_3_zone_2
    - switch.watering_system_relay_4_zone_3
    - switch.watering_system_relay_5_zone_4
    - switch.watering_system_relay_6_fert_bypass
    - switch.watering_system_relay_7_fert_line
```

### Check Tank Level
```yaml
condition: state
entity_id: binary_sensor.watering_system_low_water_level
state: 'off'  # OFF = water level OK (switch not triggered)
```

### Open Zone Valve
```yaml
service: switch.turn_on
target:
  entity_id: switch.watering_system_relay_2_zone_1
```

---

## Verification Commands

### List All Watering System Entities
```bash
# Via HA CLI
ha entities list | grep watering_system

# Via curl (requires long-lived token)
```

### Developer Tools Template
```yaml
{% set entities = states | selectattr('entity_id', 'search', 'watering_system') | list %}
{{ entities | map(attribute='entity_id') | list | sort }}
```

---

## Notes

- **Device Name:** `watering-system` (hyphen in ESPHome) becomes `watering_system` (underscore in HA entity IDs)
- **Slugification:** Spaces and special characters converted to underscores, all lowercase
- **Friendly Names:** Can be changed in HA UI without affecting entity IDs
- **Entity ID Changes:** Require ESPHome recompile if you change the `name:` field

---

## When Adding New Entities

1. **Choose descriptive names** in ESPHome YAML (this becomes the entity ID)
2. **Follow existing pattern:** "Relay X - Description" for switches
3. **Update this document** after flashing new firmware
4. **Verify in HA** before writing automations: Developer Tools → States → Search "watering"

---

## Home Assistant Configuration Helpers (Phase 2)

### Watering System Configuration Helpers

**File:** `home-assistant/packages/watering_config_helpers.yaml`  
**Entity Count:** 12 helpers (system-level configuration)

| Entity ID | Entity Type | Purpose |
|-----------|-------------|---------|
| `input_select.watering_system_state` | input_select | Master state machine (11 states) |
| `input_select.zone_sequencing_mode` | input_select | Parallel or sequential zone operation |
| `input_number.watering_cycle_days` | input_number | Watering frequency (1-14 days) |
| `input_number.max_single_zone_runtime_min` | input_number | Safety limit per zone (1-180 min) |
| `input_number.pressure_relief_duration_sec` | input_number | Relief valve duration (5-300 sec) |
| `input_datetime.morning_window_start` | input_datetime | Morning window start time |
| `input_datetime.morning_window_end` | input_datetime | Morning window end time |
| `input_datetime.evening_window_start` | input_datetime | Evening window start time |
| `input_datetime.evening_window_end` | input_datetime | Evening window end time |
| `input_boolean.enable_morning_window` | input_boolean | Enable/disable morning watering |
| `input_boolean.enable_evening_window` | input_boolean | Enable/disable evening watering |
| `input_boolean.manual_override_active` | input_boolean | Pause state machine for manual control |

---

### Watering Zone Configuration Helpers

**File:** `home-assistant/packages/watering_zone_helpers.yaml`  
**Entity Count:** 96 helpers (per-zone configuration)

#### Friendly Name Helpers (4 entities)

| Entity ID | Entity Type | Default Value | Purpose |
|-----------|-------------|---------------|---------|
| `input_text.zone_1_friendly_name` | input_text | "Raspberries" | Zone 1 display name |
| `input_text.zone_2_friendly_name` | input_text | "Blueberries" | Zone 2 display name |
| `input_text.zone_3_friendly_name` | input_text | "Zone 3" | Zone 3 display name |
| `input_text.zone_4_friendly_name` | input_text | "Zone 4" | Zone 4 display name |

#### Season and Program Selectors (8 entities)

| Entity ID | Entity Type | Options | Purpose |
|-----------|-------------|---------|---------|
| `input_select.zone_{1-4}_season` | input_select | spring, summer, fall, winter | Current season per zone |
| `input_select.zone_{1-4}_program` | input_select | off, light, normal, heavy | Watering program per zone |

#### Base Runtime (4 entities)

| Entity ID | Entity Type | Range | Purpose |
|-----------|-------------|-------|---------|
| `input_number.zone_{1-4}_base_runtime_min` | input_number | 1-120 min | Base watering time per zone |

#### Seasonal Thresholds (80 entities: 20 per zone)

**Pattern:** `input_number.zone_{1-4}_{season}_{threshold}`

For each zone (1-4) and season (spring/summer/fall/winter):

| Threshold Suffix | Purpose | Range | Unit |
|------------------|---------|-------|------|
| `rain_off_mm` | Heavy rain threshold (skip watering) | 0-100 | mm |
| `rain_light_mm` | Light rain threshold (reduce watering) | 0-50 | mm |
| `rain_min_mm` | Minimum rain for heavy program | 0-20 | mm |
| `temp_heavy_c` | High temp threshold (heavy watering) | 15-40 | °C |
| `temp_normal_c` | Moderate temp threshold (normal watering) | 10-35 | °C |

**Total:** 5 thresholds × 4 seasons × 4 zones = 80 entities

---

### Fertigation Configuration Helpers

**File:** `home-assistant/packages/watering_fert_helpers.yaml`  
**Entity Count:** 63 entities (36 input helpers + 27 template sensors)

#### Schedule (5 entities)

| Entity ID | Entity Type | Range/Type | Purpose |
|-----------|-------------|------------|---------|
| `input_number.fert_cycle_days` | input_number | 1-30 days | Fertilization frequency |
| `input_datetime.last_fert_zone_{1-4}` | input_datetime | Date only | Last fertilization date per zone |

#### Per-Zone Dosing (13 entities)

| Entity ID | Entity Type | Range | Purpose |
|-----------|-------------|-------|---------|
| `input_number.fert_zone_{1-4}_pump{1-3}_dose_ml` | input_number | 0-500 mL | Total dose per zone/pump (12 entities) |
| `input_number.fert_flush_duration_min` | input_number | 1-15 min | Post-fertilization flush time |

#### Pump Calibration Storage (18 entities: 6 per pump)

**Pattern:** `input_number.fert_pump{1-3}_cal_{parameter}`

For each pump (1-3):

| Parameter Suffix | Entity Type | Range | Purpose |
|-----------------|-------------|-------|---------|
| `slope` | input_number | 0-1 mL/min per % | Calibration curve slope (a) |
| `intercept` | input_number | -5 to 5 mL/min | Calibration curve intercept (b) |
| `r2` | input_number | 0-1 | Goodness of fit (R²) |
| `pressure` | input_number | 0-3 bar | Test pressure during calibration |
| `last_cal` | input_datetime | Date only | Calibration date |
| `cal_notes` | input_text | 200 char max | Calibration observations |

#### Template Sensors - Calculated Values (27 entities)

**Flow Rate Calculations (12 entities):**

| Entity ID | Unit | Purpose |
|-----------|------|---------|
| `sensor.fert_zone_{1-4}_pump{1-3}_rate_ml_per_min` | mL/min | Required flow rate (dose ÷ runtime) |

**Pump Commands (12 entities):**

| Entity ID | Unit | Purpose |
|-----------|------|---------|
| `sensor.fert_zone_{1-4}_pump{1-3}_command` | % | Command value for pump (calculated from calibration curve) |

**Calibration Status (3 entities):**

| Entity ID | Values | Purpose |
|-----------|--------|---------|
| `sensor.fert_pump{1-3}_calibration_status` | VALID, WARNING, EXPIRED, POOR | Calibration health indicator |

**Attributes on calibration status sensors:**
- `equation`: Full calibration equation (q = a×cmd + b)
- `r_squared`: R² value
- `calibration_date`: Date of last calibration
- `pressure_bar`: Test pressure used
- `notes`: Calibration notes text

---

## Phase 2 Entity Summary

**Total Entities Created:** 171
- System-level helpers: 12
- Zone helpers: 96
- Fertigation helpers: 36 (input) + 27 (template sensors)

**Entity Domains:**
- `input_select`: 10 (2 system + 8 zone)
- `input_number`: 119 (3 system + 84 zone + 29 fert + 3 fert cal pressure)
- `input_datetime`: 11 (4 system + 7 fert)
- `input_boolean`: 3 (system-level)
- `input_text`: 7 (4 zone + 3 fert)
- `sensor`: 27 (template sensors for fertigation calculations)

**Naming Conventions:**
- System helpers: `{domain}.{function}`
- Zone helpers: `{domain}.zone_{id}_{parameter}`
- Fertigation helpers: `{domain}.fert_{context}_{detail}`
- Dynamic friendly names: Use Jinja templates referencing `input_text.zone_{id}_friendly_name`

---

## Common Usage Examples

### Check Current System State
```yaml
{{ states('input_select.watering_system_state') }}
```

### Get Zone Program
```yaml
{{ states('input_select.zone_1_program') }}
```

### Calculate Actual Zone Runtime
```yaml
{% set base = states('input_number.zone_1_base_runtime_min') | float %}
{% set program = states('input_select.zone_1_program') %}
{% set multipliers = {'off': 0.0, 'light': 0.5, 'normal': 1.0, 'heavy': 1.5} %}
{{ base * multipliers.get(program, 1.0) }}
```

### Check Pump Calibration Status
```yaml
{{ states('sensor.fert_pump1_calibration_status') }}
```

### Get Calculated Pump Command
```yaml
{{ states('sensor.fert_zone_1_pump1_command') }} %
```

---

## Verification Commands

### List All Configuration Helpers
```yaml
# Developer Tools → Template
{{ states | selectattr('entity_id', 'search', 'watering|fert|zone') | 
   map(attribute='entity_id') | list | sort }}
```

### Count Entities by File
```yaml
# System helpers
{{ states | selectattr('entity_id', 'search', '^(input_select.watering_system_state|input_select.zone_sequencing|input_number.watering_cycle|input_number.max_single|input_number.pressure_relief|input_datetime.(morning|evening)_window|input_boolean.enable_(morning|evening)|input_boolean.manual_override)') | list | count }}

# Zone helpers
{{ states | selectattr('entity_id', 'search', '^(input_text.zone_|input_select.zone_|input_number.zone_)') | list | count }}

# Fert helpers (input only)
{{ states | selectattr('entity_id', 'search', '^(input_number.fert_|input_datetime.fert_|input_text.fert_)') | list | count }}

# Fert sensors (template)
{{ states.sensor | selectattr('entity_id', 'search', '^sensor.fert_') | list | count }}
```

---

## Notes

- **Dynamic Naming:** Zone helpers use Jinja templates in `name:` attributes to reference friendly names
- **Initial Values:** All fertigation doses default to 0 (disabled until user configures)
- **Calibration Data:** All pump calibration coefficients default to 0 (awaiting first calibration)
- **Template Sensors:** Calculated values update automatically when dependencies change
- **Dependencies:** Fertigation template sensors depend on zone helpers (base_runtime, program)
- **Error Handling:** Template sensors include guards for division by zero and unknown states

---
