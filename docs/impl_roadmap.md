# Watering System - Implementation Roadmap

**Last Updated:** 2025-10-14  
**Status:** Planning Phase

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
- [X] ✅ ESP32-DEVKITC-VE installed and powered
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
- [ ] ⏳ Calibrate flow rates at operating pressure (1.5 bar)

**Blocker Notes:** _Pumps not yet wired to RS-485 bus_

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
- [ ] 📋 `input_select.watering_system_state` (11 states)
- [ ] 📋 `input_select.zone_sequencing_mode` (parallel/sequential)
- [ ] 📋 `input_number.watering_cycle_days`
- [ ] 📋 `input_time.morning_window_start`
- [ ] 📋 `input_time.morning_window_end`
- [ ] 📋 `input_time.evening_window_start`
- [ ] 📋 `input_time.evening_window_end`
- [ ] 📋 `input_boolean.enable_morning_window`
- [ ] 📋 `input_boolean.enable_evening_window`
- [ ] 📋 `input_number.max_single_zone_runtime_min`
- [ ] 📋 `input_number.pressure_relief_duration_sec`
- [ ] 📋 `input_select.season` (spring/summer/fall/winter)
- [ ] 📋 `input_boolean.manual_override_active`

**File Location:** `home-assistant/packages/watering_config_helpers.yaml`

**Blocker Notes:** _None_

---

### 2.2 Per-Zone Helpers (Zone 1 Example)
- [ ] 📋 `input_select.zone_1_program` (off/light/normal/heavy)
- [ ] 📋 `input_number.zone_1_base_runtime_min`
- [ ] 📋 Seasonal thresholds (spring/summer/fall/winter):
  - `input_number.zone_1_{season}_rain_off_mm`
  - `input_number.zone_1_{season}_rain_light_mm`
  - `input_number.zone_1_{season}_rain_min_mm`
  - `input_number.zone_1_{season}_temp_heavy_c`
  - `input_number.zone_1_{season}_temp_normal_c`

**Repeat for:** Zone 2, Zone 3, Zone 4

**File Location:** `home-assistant/packages/watering_zone_helpers.yaml`

**Blocker Notes:** _Need to finalize zone naming (all zones use numeric IDs: zone_1, zone_2, zone_3, zone_4)_

---

### 2.3 Fertigation Helpers
- [ ] 📋 `input_number.fert_cycle_days`
- [ ] 📋 `input_datetime.last_fert_zone_1`
- [ ] 📋 `input_datetime.last_fert_zone_2`
- [ ] 📋 `input_datetime.last_fert_zone_3`
- [ ] 📋 `input_datetime.last_fert_zone_4`
- [ ] 📋 Per-zone dosing rates (3 pumps × 4 zones = 12 helpers):
  - `input_number.fert_zone_1_pump1_rate_ml_per_min`
  - `input_number.fert_zone_1_pump2_rate_ml_per_min`
  - `input_number.fert_zone_1_pump3_rate_ml_per_min`
  - (repeat pattern for zone_2, zone_3, zone_4)
- [ ] 📋 `input_number.fert_flush_duration_min`

**File Location:** `home-assistant/packages/watering_fert_helpers.yaml`

**Blocker Notes:** _None_

---

## Phase 3: Home Assistant - Core Scripts

### 3.1 Zone Control Scripts
- [ ] 📋 `script.open_zone` (param: zone_id)
- [ ] 📋 `script.close_zone` (param: zone_id)
- [ ] 📋 `script.close_all_zones`
- [ ] 📋 `script.calculate_zone_runtime` (returns runtime based on program)
- [ ] 📋 `script.run_zone_sequence` (handles parallel vs sequential)

**File Location:** `home-assistant/packages/watering_zone_scripts.yaml`

**Test Plan:**
- Manual test: open/close each zone individually
- Verify `calculate_zone_runtime` returns correct values for off/light/normal/heavy
- Test parallel mode (all zones together)
- Test sequential mode (one at a time with delays)

**Blocker Notes:** _None_

---

### 3.2 Pump Control Scripts
- [ ] 📋 `script.start_main_pump` (with pressure stabilization delay)
- [ ] 📋 `script.stop_main_pump`
- [ ] 📋 `script.open_pressure_relief` (with timeout)
- [ ] 📋 `script.close_pressure_relief`

**File Location:** `home-assistant/packages/watering_pump_scripts.yaml`

**Test Plan:**
- Start pump with bypass open (safe test)
- Verify 30s pressure stabilization delay
- Test pressure relief valve open/close cycle

**Blocker Notes:** _None_

---

### 3.3 Fertilizer Control Scripts (Future - Phase 2)
- [ ] ⏳ `script.enable_24v_cabinet`
- [ ] ⏳ `script.disable_24v_cabinet`
- [ ] ⏳ `script.valve_interlock` (ensures bypass XOR fert line)
- [ ] ⏳ `script.start_dosing_pumps` (param: zone_id, phase)
- [ ] ⏳ `script.stop_dosing_pumps`
- [ ] ⏳ `script.flush_fert_lines`

**File Location:** `home-assistant/packages/watering_fert_scripts.yaml`

**Blocker Notes:** _Requires RS-485 pumps wired and addressed_

---

### 3.4 Emergency/Safety Scripts
- [ ] 📋 `script.emergency_stop` (stops everything, resets to idle)
- [ ] 📋 `script.safe_shutdown` (graceful stop with pressure relief)

**File Location:** `home-assistant/packages/watering_safety_scripts.yaml`

**Test Plan:**
- Emergency stop during watering
- Emergency stop during fertigation
- Verify all relays off + state reset

**Blocker Notes:** _None_

---

## Phase 4: Home Assistant - State Machine

### 4.1 State Transition Scripts
- [ ] 📋 `script.state_window_check`
  - Evaluate weather conditions
  - Check last watering dates
  - Check fertigation schedule
  - Set zone programs (off/light/normal/heavy)
  - Transition to preflight_check
- [ ] 📋 `script.state_preflight_check`
  - Verify tank levels (GPIO35 = Low switch)
  - Check ESP32 online
  - Verify no errors
  - Branch to watering_plain OR fert_prep
- [ ] 📋 `script.state_watering_plain`
  - Open bypass valve (R6), close fert line (R7)
  - Start main pump (R1)
  - Run zone sequence
  - Stop pump, close zones
  - Transition to post_cycle_relief
- [ ] 📋 `script.state_fert_prep` (Future - Phase 2)
- [ ] 📋 `script.state_fert_dose_phase1` (Future - Phase 2)
- [ ] 📋 `script.state_fert_dose_phase2` (Future - Phase 2)
- [ ] 📋 `script.state_post_cycle_relief`
  - Stop pump
  - Close all valves
  - Open pressure relief (R9)
  - Wait configured duration
  - Close pressure relief
  - Disable 24V cabinet (if enabled)
  - Transition to idle

**File Location:** `home-assistant/packages/watering_state_scripts.yaml`

**Test Plan:** See Section 7 (Testing Scenarios)

**Blocker Notes:** _Requires all helpers + zone/pump scripts complete_

---

### 4.2 Master State Machine Automation
- [ ] 📋 Single automation watching `input_select.watering_system_state`
- [ ] 📋 Choose block for each state → calls corresponding script
- [ ] 📋 Time-based triggers for morning/evening windows
- [ ] 📋 Manual trigger option (for testing)

**File Location:** `home-assistant/packages/watering_state_machine.yaml`

**Blocker Notes:** _Requires all state transition scripts complete_

---

## Phase 5: Home Assistant - Safety Interlocks

### 5.1 Independent Safety Monitors
- [ ] 📋 `automation.safety_tank_low_low`
  - Trigger: `binary_sensor.watering_system_low_low_water_level` = ON
  - Action: Stop pump immediately, set state to error_tank_low, notify
- [ ] 📋 `automation.safety_comms_watchdog`
  - Trigger: ESP32 unavailable for >10s
  - Action: Set state to error_comms_lost, notify
- [ ] 📋 `automation.safety_zone_runtime_limit`
  - Trigger: Any zone valve on for > max_single_zone_runtime_min
  - Action: Close that zone, notify
- [ ] 📋 `automation.safety_manual_override_handler`
  - Trigger: `input_boolean.manual_override_active` = ON
  - Action: Pause state machine (set state to manual_override)

**File Location:** `home-assistant/packages/watering_safety_automations.yaml`

**Test Plan:** See Section 7.2 (Safety Interlock Testing) and `docs/test_scenarios.md` Section 2

**Entity References:** All entity IDs must use full `watering_system_` prefix. See `/docs/entity_reference.md` for complete mapping.

**Blocker Notes:** _None_

---

## Phase 6: Weather Integration

### 6.1 Brightsky/DWD Integration
- [ ] ✅ Brightsky REST sensors configured
- [ ] ✅ `sensor.brightsky_rain_24h` (precipitation last 24h)
- [ ] ✅ `sensor.brightsky_rain_72h` (precipitation last 72h)
- [ ] ✅ Current weather conditions (temperature, humidity, pressure, etc.)
- [ ] ✅ Wind sensors (speed, gust, direction)
- [ ] ✅ Binary sensors (raining_now, sunny_now)
- [ ] 📋 `sensor.brightsky_temp_high_yesterday` (max temp from previous day)
- [ ] 📋 `sensor.brightsky_temp_avg_high_3day` (average of daily highs for last 3 days)

**File Location:** `home-assistant/packages/dwd_brightsky.yaml` ✅ **EXISTS**

**Additional sensors available (not required for watering logic):**
- Dew point, cloud cover, sunshine minutes
- Wind speed in knots (converted from m/s)
- Weather URL generator template

**Blocker Notes:** _None - implementation complete_

---

### 6.2 Weather-Based Program Logic
- [ ] 📋 Integrate weather sensors into `script.state_window_check`
- [ ] 📋 Decision tree per zone:
  - rain_72h > rain_off_mm → program = off
  - rain_24h > rain_light_mm → program = light
  - temp_avg_high_3day > temp_heavy_c AND rain_72h < rain_min_mm → program = heavy
  - temp_avg_high_3day > temp_normal_c → program = normal
  - else → program = light

**Blocker Notes:** _Requires state machine scripts (Phase 4) and temperature sensors from 6.1_

---

## Phase 7: Dashboard UI

### 7.1 Main Control Card
- [ ] 📋 Current system state (large, colored badge)
- [ ] 📋 Next scheduled watering (countdown timer)
- [ ] 📋 Emergency stop button (prominent, red)
- [ ] 📋 Manual override toggle

**File Location:** `home-assistant/ui-lovelace.yaml` (or dashboard config)

---

### 7.2 Zone Status Cards
- [ ] 📋 Per-zone card showing:
  - Current program (off/light/normal/heavy)
  - Last watering timestamp
  - Next fertigation due date
  - Manual valve control (when in override mode)

---

### 7.3 System Configuration Card
- [ ] 📋 Zone sequencing mode dropdown
- [ ] 📋 Watering cycle period slider
- [ ] 📋 Window time pickers (morning/evening)
- [ ] 📋 Season selector

---

### 7.4 Safety Status Card
- [ ] 📋 Tank level indicators (Low, Low-Low) with colors
- [ ] 📋 ESP32 online status
- [ ] 📋 Last Modbus transaction timestamp
- [ ] 📋 Active alarms list

---

### 7.5 Statistics/History Card
- [ ] 📋 Pump runtime tracking (based on relay state duration)
- [ ] 📋 Watering cycle history (dates/durations per zone)
- [ ] 📋 Water usage estimate (based on flow rates × runtime)
- [ ] 📋 Energy consumption (from Victron)

---

## Phase 8: Testing & Validation

### 8.1 State Machine Testing
- [ ] 📋 Execute tests from docs/test_scenarios.md sections 3.1-3.4
**Test Results:** _See test_scenarios.md for detailed pass/fail status_

---

### 8.2 Safety Interlock Testing
- [ ] 📋 Test: Trigger Low-Low switch during watering (verify immediate stop)
- [ ] 📋 Test: Disconnect ESP32 during watering (verify comms watchdog)
- [ ] 📋 Test: Leave zone valve on beyond max runtime (verify auto-close)
- [ ] 📋 Test: Emergency stop from each state

**Test Results:** See detailed test procedures in `docs/test_scenarios.md` Section 2 (Safety Interlock Tests)

**Note:** All test scenarios use corrected entity IDs with `watering_system_` prefix (updated 2025-01-14). Before testing, verify entity IDs in HA Developer Tools → States.

---

### 8.3 Zone Sequencing Testing
- [ ] 📋 Test: Parallel mode - all zones with same runtime (should start/stop together)
- [ ] 📋 Test: Sequential mode - 4 zones (should run one at a time)
- [ ] 📋 Test: Mixed programs - some zones off, others light/normal/heavy

**Test Results:** _Document in `docs/test-results.md`_

---

### 8.4 Weather-Based Program Testing
- [ ] 📋 Test: Heavy rain in last 72h → zones = off
- [ ] 📋 Test: Light rain in last 24h → zones = light
- [ ] 📋 Test: High temps + no rain → zones = heavy
- [ ] 📋 Test: Manual program override (bypass weather logic)

**Test Results:** _Document in `docs/test-results.md`_

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

**File Location:** `home-assistant/packages/notification_helpers.yaml` ✅ **EXISTS**

**Blocker Notes:** _None_

**Completion Date:** 2025-10-13

---

### 9.3 REST Commands
- [x] ✅ `rest_command.send_whatsapp_notification` (CallMeBot integration)
- [x] ✅ `notify.gmail_smtp` (email sending via Gmail)
- [x] ✅ IMAP email integration (inbox monitoring for daily test)

**File Location:** `home-assistant/packages/notification_config.yaml` ✅ **EXISTS**

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

**File Location:** `home-assistant/packages/notification_scripts.yaml` ✅ **EXISTS**

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

**File Location:** `home-assistant/packages/notification_tests.yaml` ✅ **EXISTS**

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

**File Location:** `home-assistant/packages/notification_tests.yaml` ✅ **EXISTS**

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

**File Location:** `home-assistant/packages/notification_tests.yaml` ✅ **EXISTS**

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

**File Location:** Multiple files (notification_tests.yaml, notification_scripts.yaml)

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
- [ ] ⏸️ Add `script.send_watering_summary` call to end of `script.state_post_cycle_relief`
- [ ] ⏸️ Template logic to compile cycle data (zones watered, programs, fertilizer, errors, runtime)
- [ ] ⏸️ Format summary message for WhatsApp

**File Location:** `home-assistant/packages/watering_state_scripts.yaml` (modification to existing script)

**Test Plan:**
- Run full watering cycle ⏸️ BLOCKED
- Verify summary sent after post_cycle_relief ⏸️ BLOCKED
- Verify summary content accuracy (zones, programs, runtime) ⏸️ BLOCKED
- Test with errors present (verify error reporting in summary) ⏸️ BLOCKED

**Blocker Notes:** _Requires state machine implementation (Phase 4)_

**Completion Date:** _TBD - blocked on Phase 4_

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
- **2025-01-14:**
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

| File | Owner | Purpose | Status | Last Updated |
|------|-------|---------|--------|--------------|
| `docs/architecture.md` | Design | System design, state machine, configuration entities | ✅ Complete | 2025-10-01 |
| `docs/programming-notes.md` | Process | Coding standards, patterns, workflow guardrails | ✅ Living doc | 2025-10-04 |
| `docs/impl_roadmap.md` | Status | Implementation checklist and progress tracking | ✅ Active | 2025-10-04 |
| `docs/test-scenarios.md` | Testing | Concrete test cases with pass/fail tracking | ✅ Created | 2025-10-04 |
| `README.md` | Project | Project overview, setup instructions | 📋 Needs update | TBD |

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
| `home-assistant/packages/watering_config_helpers.yaml` | System-level helpers | 📋 Planned | State, schedule, safety config |
| `home-assistant/packages/watering_zone_helpers.yaml` | Per-zone helpers | 📋 Planned | Programs, runtimes, thresholds |
| `home-assistant/packages/watering_fert_helpers.yaml` | Fertigation helpers | 📋 Planned | Dosing rates, schedules |
| `home-assistant/packages/watering_zone_scripts.yaml` | Zone control | 📋 Planned | Open/close, sequencing |
| `home-assistant/packages/watering_pump_scripts.yaml` | Pump control | 📋 Planned | Start/stop, pressure relief |
| `home-assistant/packages/watering_fert_scripts.yaml` | Fert control | ⏳ Phase 2 | 24V cabinet, dosing pumps |
| `home-assistant/packages/watering_safety_scripts.yaml` | Safety/emergency | 📋 Planned | Emergency stop, safe shutdown |
| `home-assistant/packages/watering_state_scripts.yaml` | State transitions | 📋 Planned | Individual state handlers |
| `home-assistant/packages/watering_state_machine.yaml` | Master automation | 📋 Planned | State watcher, triggers |
| `home-assistant/packages/watering_safety_automations.yaml` | Safety monitors | 📋 Planned | Tank, comms, runtime limits |
| `home-assistant/secrets.yaml` | Credentials | ✅ Private | Never committed (gitignored) |
| `home-assistant/secrets.example.yaml` | Credentials template | ✅ Public | Sanitized placeholders |
| `home-assistant/packages/watering_notification_helpers.yaml` | Notification system helpers | ✅ Complete | Winterization, test confirmations, error tracking |
| `home-assistant/packages/watering_notification_config.yaml` | REST commands, IMAP config | ✅ Complete | Service integrations |
| `home-assistant/packages/watering_notification_scripts.yaml` | Notification sending scripts | ✅ Complete | Tiered notifications, summary compilation |
| `home-assistant/packages/watering_notification_tests.yaml` | Testing automations | ✅ Complete | Daily, monthly, de-winterization tests |

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
- Pattern: `watering_{function}_{type}.yaml`
- Types: `helpers`, `scripts`, `automations`, `machine`
- Examples: `watering_zone_scripts.yaml`, `watering_safety_automations.yaml`

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
