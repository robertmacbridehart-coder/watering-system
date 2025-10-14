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
