# Entity ID Reference

**Last Updated:** 2026-08-25  
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

## Watering System Diagnostic Sensors

| ESPHome ID | ESPHome Name | Home Assistant Entity ID | Function |
|------------|--------------|-------------------------|----------|
| `wifi_signal_db` | "WiFi Signal" | `sensor.watering_system_wifi_signal` | WiFi RSSI in dBm (`device_class: signal_strength`, `entity_category: diagnostic`, 60 s update). Marginal link measured at ~-72 dBm. |
| (template) | "WS Build Info" | `text_sensor.watering_system_ws_build_info` | Firmware build date/time (`__DATE__ __TIME__`). |

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

**File:** `home-assistant/packages/watering_helpers/config_helpers.yaml`  
**Entity Count:** 12 helpers (system-level configuration)
> `input_number.watering_cycle_days` was **retired 2026-08-22** (Phase 7, ADR-020) —
> superseded by per-zone `input_number.zone_N_watering_interval_days` (see Per-Zone
> Configuration Helpers below). It was never consumed in code.

| Entity ID | Entity Type | Purpose |
|-----------|-------------|---------|
| `input_select.watering_system_state` | input_select | Master state machine (15 options: idle, window_check, preflight_check, watering_plain, fert_prep, fert_dose_phase1, fert_dose_phase2, post_cycle_relief, manual_override, winterized, error_e_stop, error_tank_low, error_comms_lost, error_valve_interlock, error_relay_state) |
| `input_select.zone_sequencing_mode` | input_select | Parallel or sequential zone operation |
| `input_number.max_single_zone_runtime_min` | input_number | Safety limit per zone (1-180 min) |
| `input_number.pressure_relief_duration_sec` | input_number | Relief valve duration (5-300 sec) |
| `input_datetime.morning_window_start` | input_datetime | Morning window start time |
| `input_datetime.morning_window_end` | input_datetime | Morning window end time |
| `input_datetime.evening_window_start` | input_datetime | Evening window start time |
| `input_datetime.evening_window_end` | input_datetime | Evening window end time |
| `input_boolean.enable_morning_window` | input_boolean | Enable/disable morning watering |
| `input_boolean.enable_evening_window` | input_boolean | Enable/disable evening watering |
| `input_boolean.manual_override_active` | input_boolean | Pause state machine for manual control |

> `input_text.cycle_event_log` was **retired 2026-07-31** — event logging moved to the
> `watering_ops` `system_events` table via `script.log_system_event` (ADR-013). Query the
> DB (SQLite Web) instead of an HA entity.

---

### Phase 4 State-Machine Helpers

**File:** `home-assistant/packages/watering_helpers/config_helpers.yaml`
**Added:** 2026-08-09 (ADR-014 / ADR-015). Consumed by the Phase 4 state machine
(`watering_state/state_machine.yaml`, `watering_state/state_scripts.yaml`).

| Entity ID | Entity Type | Options / Format | Purpose |
|-----------|-------------|------------------|---------|
| `input_select.active_watering_window` | input_select | `morning`, `evening` (init `morning`) | Window the active cycle is running (set by the scheduler before `window_check`). |
| `input_select.active_trigger_type` | input_select | `scheduled`, `manual`, `override` | How the active cycle started. `override` reserved for a future forced run; unused in Phase 4. Stamped on Event 1. |
| `input_text.cycle_uuid` | input_text (max 50) | `c-<UTC %Y%m%d%H%M%S%f>` | Cycle correlation id (ADR-014). Empty = no open cycle (the no-op signal for `finalize_cycle_record`). |
| `input_text.zone_run_uuid` | input_text (max 50) | `z-…` | Reserved for the fertigation path (Event 2 ↔ Event 3 dose correlation). Unused in Phase 4 — the plain path mints a local parallel-safe `zrun_uuid` inside `run_zone_sequence`. |
| `input_button.start_watering_cycle_now` | input_button | — | Manual / on-demand cycle start; the scheduler triggers on it (sets `active_trigger_type = manual`, window by time of day). |
| `binary_sensor.watering_operational` | template binary_sensor | `on` / `off` | Derived (2026-08-16): `on` iff `watering_system_state` is an operational (cycle-in-flight) state — NOT idle, NOT a control state (`manual_override` / `winterized`), NOT a latched `error_*`. Single source of truth for that complement; consumed by the three Phase 5.1 safety monitors and the state-machine control guard. (Restart-recovery keeps its own inline template to avoid a startup setup-ordering dependency.) |

---

### Weather Sensors (DWD Brightsky)

**File:** `home-assistant/packages/weather/dwd_brightsky.yaml`
Used by `state_window_check` (program-selection tree, architecture.md §3.2) and
`state_preflight_check` (Event 1 payload).

| Entity ID | Entity Type | Purpose |
|-----------|-------------|---------|
| `sensor.brightsky_rain_24h` | sensor (mm) | Rainfall, last 24h — `off`/`light` program gating. |
| `sensor.brightsky_rain_72h` | sensor (mm) | Rainfall, last 72h — `off`/`heavy` program gating. |
| `sensor.brightsky_temp_avg_high_3day` | sensor (°C) | 3-day average high temp. **Demoted by ADR-021** (lagging) — the reworked §3.2 tree uses forecast/current high instead; retained for DB/reporting. |
| `sensor.brightsky_temp_high_yesterday` | sensor (°C) | Yesterday's high temp — stamped on Event 1 (`temp_high_c`). |
| `sensor.brightsky_forecast_rain` | sensor (mm) | Forecast rain total for the upcoming "forecast day" (rolls at 04:00 local; no-data → 0). Feeds the deferred "Next Program" card + weather card. |
| `sensor.brightsky_forecast_temp_high` | sensor (°C) | Forecast high for the upcoming forecast day (no-data → `unknown`). Same rollover. |

---

### Dashboard-Derived Sensors (Phase 7 / Gate 7.2)

**File:** `home-assistant/packages/watering_ui/derived_sensors.yaml` (added 2026-08-22)
Read-only surfacing of data with no first-class HA entity. No hardware/state writes.
**Deployed & verified live on the Green 2026-08-22.** SQL `db_url` uses HA Core's
`/config/watering_ops.db` (NOT AppDaemon's `/homeassistant` path — see programming-notes
"Dashboard-Derived Sensors (Gate 7.2)").

| Entity ID | Entity Type | Purpose |
|-----------|-------------|---------|
| `sensor.zone_{1-4}_watering` | `sql:` (secondary `watering_ops.db`) | State = latest successful **MAIN** `zone_runs.start_time` (device_class timestamp, UTC-aware) — used by `state_window_check` as the per-zone interval anchor. Attr `history` = JSON array of the last 4 successful main runs, most-recent first (`t`=start_time, `p`=weather_program, `d`=actual_duration_sec, `f`=fertigated). Filter: `aborted=0 AND end_time IS NOT NULL AND NOT (weather_program='heavy' AND COALESCE(program_multiplier,1.0)=0.5)` — the last clause excludes the heavy mid-interval booster so it doesn't reset the cadence clock (ADR-020). Empty zone → state `unknown`, `history` `[]`. |
| `sensor.zone_{1-4}_last_booster` | `sql:` (secondary `watering_ops.db`) | State = latest successful **BOOSTER** `zone_runs.start_time` (device_class timestamp, UTC-aware), else `unknown`. The exact INVERSE of the `_watering` filter: `aborted=0 AND end_time IS NOT NULL AND weather_program='heavy' AND COALESCE(program_multiplier,1.0)=0.5`. `state_window_check` compares it against `sensor.zone_N_watering` to make the booster retry once per interval (pending iff unknown OR older than the last main dose). Added 2026-08-23 (ADR-020 review Fix #4b). |
| `sensor.zone_{1-4}_fert_next_due` | template (timestamp) | `last_fert_zone_{n}` + `fert_cycle_days`. Unavailable until a real last-fert date is set (unset restores to 1970 → hidden). |

> Rescoped 2026-08-25 (ADR-021 accepted): the per-zone preview is now a **"Current Status"**
> tile — the live §3.2 tree evaluated on *current* inputs, framed as status, not a forecast (a
> true forecast would need to predict future soil moisture; deferred to post-season). See the
> PLANNED block below and ui_design §7 #1.

---

### ADR-021 Entities — PLANNED (NOT YET LIVE; implementation held for moisture hardware)

**Status:** design of record only (ADR-021, architecture §3.2/§9.1). **None of these exist on the
Green yet** — do NOT reference as live IDs until the moisture hardware is installed and the code
is deployed. IDs below are the intended names, subject to change at implementation.

| Entity ID (planned) | Entity Type | Purpose |
|---------------------|-------------|---------|
| `sensor.zone_{1-4}_soil_moisture` | template (%) | Per-zone aggregate soil moisture = **average** of all sensors mapped to the zone (WH52 + SEN0600). Primary §3.2 input. Zones 3 & 4 both read the shared "Vegetables" pool. `unknown` when no sensor mapped → §3.2 weather-only fallback. |
| `input_select.moisture_wireless_{1-4}_zone` | input_select | Runtime zone tag for each movable WH52. Options: Raspberries / Blueberries / Vegetables / Unassigned. *(Tag mechanism itself deferred until the sensors are set up — ADR-021.)* |
| `sensor.brightsky_forecast_pop_today` | sensor (%) | Whole-day (→ midnight) max hourly precipitation probability, from the shared BrightSky forecast fetch. Forecast-rain downgrade gate (> 80 %). |
| `sensor.brightsky_forecast_rain_today` | sensor (mm) | Whole-day (→ midnight) summed forecast precipitation, same fetch. Downgrade gate (≥ 5 mm). Distinct from `brightsky_forecast_rain` (04:00-rollover card sensor). |
| `sensor.zone_{1-4}_current_status` | template | The "Current Status" preview (rescoped item above): live §3.2 program the zone would get if the window were now. Dashboard only. |

> **Decision recording** (not entities): handled by **ADR-018** (weather-observations DB —
> `watering_weather.db` `zone_decisions` + `zone_runs.decision_criteria` JSON), extended by
> ADR-021 with the moisture-primary inputs. No separate `decisions` table. Schemas/writers added
> at implementation (impl_roadmap §3.5/§3.6).

---

### Watering Zone Configuration Helpers

**File:** `home-assistant/packages/watering_helpers/zone_helpers.yaml`  
**Entity Count:** 172 helpers (per-zone configuration)

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
| `input_select.zone_{1-4}_program` | input_select | off, light, normal, heavy, **booster** | Watering program per zone. `booster` is SYSTEM-set only (heavy mid-interval 0.5× top-up placed by `state_window_check`; recorded to the DB as heavy+multiplier 0.5 — ADR-020). |

#### Base Runtime + Cadence (12 entities)

| Entity ID | Entity Type | Range | Purpose |
|-----------|-------------|-------|---------|
| `input_number.zone_{1-4}_base_runtime_min` | input_number | 1-120 min | Base watering time per zone |
| `input_number.zone_{1-4}_watering_interval_days` | input_number | 1-14 days | Per-zone cadence ("water on day N"). RestoreEntity. Consumed by `state_window_check` (anchor = last main dose from `sensor.zone_N_watering`). Replaces retired `watering_cycle_days`. Phase 7 / ADR-020. |
| `input_boolean.zone_{1-4}_enabled` | input_boolean | on/off | Per-zone master enable (hard on/off). OFF forces program `off` every window (durable, unlike `zone_N_program`). RestoreEntity; first-boot OFF (fail-safe). Phase 7 / ADR-020. |

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

#### Seasonal Soil Moisture Thresholds (48 entities: 12 per zone)

**Pattern:** `input_number.zone_{1-4}_{season}_{threshold}`

For each zone (1-4) and season (spring/summer/fall/winter):

| Threshold Suffix | Purpose | Range | Unit |
|------------------|---------|-------|------|
| `off_moisture_min` | Soil saturation — skip watering entirely | 0-100 | % |
| `light_moisture_min` | Adequate moisture — light program | 0-100 | % |
| `normal_moisture_min` | Moderate moisture — normal program | 0-100 | % |

Logic (waterfall): `>= off_moisture_min` → off; `>= light_moisture_min` → light; `>= normal_moisture_min` → normal; else → heavy. Sensors (DFRobot SEN0600) deferred to Phase 3; rain-only fallback used until then.

**Total:** 3 thresholds × 4 seasons × 4 zones = 48 entities

#### Light Program Dose Behaviour (4 entities)

| Entity ID | Entity Type | Default | Purpose |
|-----------|-------------|---------|--------|
| `input_boolean.zone_{1-4}_allow_full_dose_light_program` | input_boolean | off | Full dose (ON) or proportional dose (OFF) during light watering program. Default OFF (conservative). Only enable for salt-tolerant crops; keep OFF for blueberries/ericaceous plants. |

#### Fertigation 14-Day Frequency Targets (16 entities)

**Pattern:** `input_number.zone_{1-4}_{season}_fert_14d_target`

| Entity ID | Range | Purpose |
|-----------|-------|---------|
| `input_number.zone_{1-4}_{season}_fert_14d_target` | 0-14 events | Target fertigation events per rolling 14-day window, per zone and season |

Logic: fertigation eligible when `events_last_14_days < target` (combined with soil moisture and weather conditions).

**Total:** 4 seasons × 4 zones = 16 entities

---

### Fertigation Configuration Helpers

**File:** `home-assistant/packages/watering_helpers/fert_helpers.yaml`  
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

**Total Entities Created:** 244
- System-level helpers: 12 (`input_text.cycle_event_log` retired 2026-07-31, see ADR-013)
- Zone helpers: 172 (includes 48 moisture thresholds + 16 fert 14d targets + 4 dose booleans + 4 watering-interval + 4 zone-enable, the last two added Phase 7 / ADR-020)
- Fertigation helpers: 36 (input) + 27 (template sensors)

**Entity Domains:**
- `input_select`: 10 (2 system + 8 zone)
- `input_number`: 183 (3 system + 148 zone + 29 fert + 3 fert cal pressure)
- `input_datetime`: 11 (4 system + 7 fert)
- `input_boolean`: 7 (3 system-level + 4 zone dose behaviour)
- `input_text`: 8 (1 system + 4 zone + 3 fert)
- `sensor`: 27 (template sensors for fertigation calculations)

> **Note:** `input_boolean.system_winterized` and all notification helpers live in
> `home-assistant/packages/notification/helpers.yaml`, not the watering helpers files.

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

## Operational Database (`watering_ops`)

The operational database is **not** a set of Home Assistant entities. It is a separate
SQLite file at `/homeassistant/watering_ops.db`, written by AppDaemon. Its tables and
columns — `watering_cycles`, `zone_runs`, `fertigation_doses`, `system_events` — are the
source of truth for cycle / zone-run / dose / event history and are defined in
**`docs/db_schema.sql`** (canonical). Design lives in architecture.md §13; the HA-event
payload contract in §13.3.1; HA-side setup in `docs/db_setup_guide.md`.

Do **not** look for cycle/dose/event records as HA entities — query the database directly
(e.g. via the SQLite Web add-on) or use the decision-query sensors below. For column names,
types, and constraints, see `docs/db_schema.sql`.

The AppDaemon decision-query app (Phase 3.5, not yet built) will publish the fert-window
sensor below back into HA once it exists:

| Planned HA Entity | Source | Purpose |
|-------------------|--------|---------|
| `sensor.zone_{1-4}_fert_delivered_14d_ml` | `fertigation_doses` 14-day rolling query | Phase 3.3 fert eligibility |

**Live AppDaemon-published entity:**

| HA Entity | Source | Publisher | Purpose |
|-----------|--------|-----------|---------|
| `binary_sensor.watering_cycle_active` | Event 1 → ON, Event 4 → OFF (an open `watering_cycles` row) | `db_writer.py` (`DbWriter._set_cycle_active`) | Is a cycle running? — state machine / safety |

> **Virtual entity caveat:** `watering_cycle_active` is published via AppDaemon `set_state`, so it
> materialises only on the first cycle after an AppDaemon start and reads `unknown` until then; it
> does **not** survive an AppDaemon restart (fire-and-forget reporting, not a safety input — §13.1).
> Verified live on the Green **2026-08-16** (Test 10.6): `unknown → on` with a `cycle_uuid` attribute
> at Event 1 (`watering_preflight_complete`), `→ off` at Event 4 (`watering_cycle_complete`).

---

## System Event Logging (`system_events`)

Watering scripts do **not** write `system_log` or SQLite directly for notable events; they
call one reusable HA script, and an AppDaemon app persists the result to the `system_events`
table (ADR-013; architecture.md §13.3.1 Event 5). This replaced the retired
`input_text.cycle_event_log`.

**Flow:** `script.log_system_event` → fires the `watering_system_event` bus event →
AppDaemon `DbEventWriter` INSERTs one `system_events` row. (`log_system_event` also always
writes `system_log`, so a DB problem never loses the diagnostic line and never stalls the
watering/safety path.)

**`script.log_system_event`** — `home-assistant/packages/watering_scripts/logging_scripts.yaml`

| Field | Required | Purpose |
|-------|----------|---------|
| `severity` | yes | `info` / `warning` / `error` / `critical` |
| `event_type` | yes | coarse `<domain>_<event>` class (table below) |
| `message` | yes | human-readable detail → `system_log` and the `notes` column |
| `entity_id` | no | HA entity involved |
| `value_before` / `value_after` | no | state around the event |
| `logger` | no | `system_log` logger name (default `watering_system.events`) |

**Bus event (not an entity):** `watering_system_event`, fired by `script.log_system_event`
and consumed by the AppDaemon `DbEventWriter` app
(`home-assistant/appdaemon/watering_db/db_event_writer.py`, registered in that folder's
`apps.yaml`). Payload contract: architecture.md §13.3.1 Event 5. The writer validates and
never raises — a bad payload is logged, recorded as an `event_rejected` row, and skipped.

**Severity ladder** (matches HA `system_log` levels minus `debug`; DB `CHECK`-constrained):

| severity | meaning |
|----------|---------|
| `info` | normal event (pump stopped, self-repair succeeded) |
| `warning` | recoverable / degraded (self-repair attempt, config fallback, duration clamp) |
| `error` | operation aborted / failed but contained (interlock, tank low, relay verify) |
| `critical` | catastrophic, needs physical intervention (pump runaway) |

**`event_type` vocabulary** (coarse class; specifics live in `notes` / `entity_id`):

| Domain | event_type values | Source |
|--------|-------------------|--------|
| Pump | `pump_start_abort`, `pump_stop`, `pump_runaway`, `pump_relay_fault`, `pump_self_repair`, `pump_relief`, `pump_relief_abort`, `pump_comms_lost`, `pump_comms_restored` | `pump_scripts.yaml` (recovery: `watering_safety/safety_automations.yaml`) |
| Zone | `zone_open_abort`, `zone_sequence_abort`, `zone_config_fallback` | `zone_scripts.yaml` |
| Safety | `safety_estop`, `safety_relay_fault`, `safety_shutdown`, `safety_state_fault` | `watering_safety_scripts.yaml` |
| Maintenance | `seasonal_export` (`db_export`), `event_rejected` (`DbEventWriter`), plus repo-pull audit rows | AppDaemon apps |

Note: `pump_comms_lost` / `pump_comms_restored` — **emitted as of 2026-08-03** (Phase 3.4
comms-lost handling shipped). `pump_comms_lost` (`error`) is fired by the fail-fast guard in
`stop_main_pump` (`pump_scripts.yaml`). `pump_comms_restored` is fired by the reactive-recovery
automation `watering_safety_r1_comms_recovery` (`watering_safety/safety_automations.yaml`):
`warning` when R1 returns `on` (then `emergency_stop`), `info` when R1 returns `off` (then clear
to `idle`).

These rows are **not** HA entities — query the DB (SQLite Web), e.g.
`SELECT * FROM system_events ORDER BY event_id DESC LIMIT 20;`.

---

## Repo Pull / Maintenance Entities

Entities for the AppDaemon-driven repository pull (ADR-012). App:
`home-assistant/appdaemon/repo_pull/`; HA glue:
`home-assistant/packages/repo_pull.yaml`.

| Entity ID | Type | Source | Purpose |
|-----------|------|--------|---------|
| `input_button.repo_pull` | input_button | `packages/repo_pull.yaml` | Dashboard button; a press fires the `watering_repo_pull` event consumed by the AppDaemon app (interlock → partial backup → pull → validate → restart) |
| `sensor.repo_pull` | command_line | reads `/config/version.json` | Current tag (state); attributes `repo`, `branch`, `tag`, `sha`, `pulled_at`. Written by `pull_public_repo.sh` |
| `sensor.repo_pull_short_sha` | template | `sensor.repo_pull` `sha` attribute | First 7 chars of the commit SHA |
| `sensor.repo_pull_time` | template (trigger) | `sensor.repo_pull` `pulled_at` attribute | Timestamp of the last pull (`device_class: timestamp`) |

**Bus event (not an entity):** `watering_repo_pull`, fired by the automation
`repo_pull_on_button_press` in `packages/repo_pull.yaml` and consumed by the
AppDaemon `repo_pull` app.

**Package-file gotcha:** with `packages: !include_dir_named packages`, the package
key is the file BASENAME and must be globally unique across the whole `packages/`
tree. Keep all repo-pull HA config in the flat `packages/repo_pull.yaml`; do NOT
add a `packages/repo_pull/` subdir file of the same basename — the duplicate key
silently drops one file's entities (this once knocked out the version sensors).

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-08-22 | Claude | **Gate 7.2 derived sensors added + DEPLOYED & VERIFIED LIVE.** New section "Dashboard-Derived Sensors": `sensor.zone_{1-4}_watering` (SQL, `watering_ops.db` — last/last-4 waterings) + `sensor.zone_{1-4}_fert_next_due` (template) in `packages/watering_ui/derived_sensors.yaml`. Added `sensor.brightsky_forecast_rain` / `sensor.brightsky_forecast_temp_high` (one shared BrightSky forecast `rest:` resource) to the Weather Sensors table. All ten verified live on the Green 2026-08-22. Two silent-failure fixes en route (programming-notes "Dashboard-Derived Sensors (Gate 7.2)"): SQL `db_url` → Core `/config` path; merged the two forecast REST sensors into one `rest:` fetch (startup race). Per-zone "Next Program" forecast templates deferred. |
| 2026-08-16 | Claude | Promoted `binary_sensor.watering_cycle_active` from Planned → **live**: its publisher (`db_writer.py` / `DbWriter`, Events 1/3/4) is deployed and **verified live on the Green** (Test 10.6 — `unknown → on → off` across a cycle). Split the planned table (fert 14-day sensor stays planned under the decision-query app) and added the virtual-entity caveat (set_state; resets on AppDaemon restart). |
| 2026-08-12 | Claude | Added "Watering System Diagnostic Sensors" section: `sensor.watering_system_wifi_signal` (new `wifi_signal` platform sensor in `esphome/watering-system.yaml`, dBm RSSI, diagnostic, 60 s) and back-filled the existing `text_sensor.watering_system_ws_build_info`. Ships on the next ESP32 OTA flash. |
| 2026-08-03 | Claude | Phase 3.4 comms-lost handling **shipped**: `pump_comms_lost` / `pump_comms_restored` now **emitted** (dropped the ᴾ "planned / not yet emitted" markers + rewrote the note). `pump_comms_lost` fired by the fail-fast guard in `stop_main_pump`; `pump_comms_restored` by the new recovery automation `watering_safety_r1_comms_recovery` in `watering_safety/safety_automations.yaml` (recovery source path corrected from `automations.yaml`). |
| 2026-08-03 | Claude | Reserved two planned pump `event_type`s in the vocabulary table — `pump_comms_lost`, `pump_comms_restored` (superscript ᴾ + note) — for the Phase 3.4 comms-lost fail-fast + reactive-recovery work (roadmap §3.4). Marked **not yet emitted**; no code changed. |
| 2026-07-31 | Claude | Added "System Event Logging (`system_events`)" section documenting `script.log_system_event`, the `watering_system_event` bus event, the `DbEventWriter` app, and the severity + `event_type` vocabularies (ADR-013). Retired `input_text.cycle_event_log` (system-level helper count 13→12): event logging moved to the `watering_ops` `system_events` table via that path; removed the definition from `config_helpers.yaml`, so the entity no longer exists — query the DB (SQLite Web) instead. |
| 2026-07-01 | Claude | Added "Repo Pull / Maintenance Entities" section: `input_button.repo_pull`, the version sensors (`sensor.repo_pull` / `sensor.repo_pull_short_sha` / `sensor.repo_pull_time`), and the `watering_repo_pull` bus event, for the AppDaemon repo-pull button (ADR-012). Documented the `!include_dir_named` basename-uniqueness gotcha that briefly knocked out the version sensors. |
| 2026-06-30 | Claude | Added "Operational Database (`watering_ops`)" section pointing to `docs/db_schema.sql` as the source of truth for the DB tables (which are not HA entities), with references to architecture.md §13/§13.3.1 and the planned decision-query sensors (`sensor.zone_{1-4}_fert_delivered_14d_ml`, `binary_sensor.watering_cycle_active`). |
| 2026-06-28 | Claude | Cross-checked all helper YAML files against entity_reference. Corrected file paths for config_helpers, zone_helpers, fert_helpers, notification/helpers, notification/scripts (flat-file names → subdirectory paths). Config helpers: count 12→13, added `input_text.cycle_event_log`, expanded `watering_system_state` to list all 15 options. Zone helpers: count 96→164, renamed "Seasonal Thresholds" to "Seasonal Weather Thresholds", added Seasonal Soil Moisture Thresholds (48 entities), Light Program Dose Behaviour (4 `input_boolean`), Fertigation 14-Day Frequency Targets (16 entities). Phase 2 summary updated (171→244 total, all domain counts corrected, notification helpers location note added). |
