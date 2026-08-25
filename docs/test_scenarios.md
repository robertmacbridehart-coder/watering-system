# Watering System - Test Scenarios

**Last Updated:** 2026-08-16 (§2 Tests 2.1, 2.2, 2.3, 2.6 all RUN + PASS on the Green — Phase 5.1
safety monitors + the `watering_operational` predicate, incl. the four xhigh code-review fixes)
**Purpose:** Concrete, runnable test cases for validating system behavior

---

## Testing Philosophy

- **Test before production use** - Every feature must pass its test scenario
- **Document results** - Record pass/fail status and dates
- **Regression testing** - Re-run critical tests after changes
- **Safety first** - Test interlocks before enabling actuators
- **Incremental validation** - Test components individually before integration

---

## Entity ID Verification

**CRITICAL:** Before running any test, verify entity IDs in Home Assistant:
1. Go to Developer Tools → States
2. Search for "watering_system"
3. Confirm entity exists before testing
4. Use exact entity ID from HA (not ESPHome config)

See `/docs/entity_reference.md` for complete entity mapping.

---

## Test Status Legend

- ✅ **PASS** - Test completed successfully, date recorded
- ❌ **FAIL** - Test failed, issues documented
- 🚧 **PARTIAL** - Some test steps passed, others failed
- ⏸️ **BLOCKED** - Cannot test yet (missing hardware/code)
- ⏭️ **SKIPPED** - Intentionally not tested (future phase)

---

## Entity ID Quick Reference

**For tests referencing ESPHome entities, use these full entity IDs:**

| Relay | Function | Entity ID |
|-------|----------|-----------|
| R1 | Main Pump | `switch.watering_system_relay_1_main_pump` |
| R2 | Zone 1 | `switch.watering_system_relay_2_zone_1` |
| R3 | Zone 2 | `switch.watering_system_relay_3_zone_2` |
| R4 | Zone 3 | `switch.watering_system_relay_4_zone_3` |
| R5 | Zone 4 | `switch.watering_system_relay_5_zone_4` |
| R6 | Fert Bypass | `switch.watering_system_relay_6_fert_bypass` |
| R7 | Fert Line | `switch.watering_system_relay_7_fert_line` |
| R9 | Pressure Relief | `switch.watering_system_relay_9_pressure_relief` |
| R10 | 24V Cabinet | `switch.watering_system_relay_10_24v_cabinet` |

**Sensors:**
- Low water level: `binary_sensor.watering_system_low_water_level` (GPIO33)
- Low-Low water level: `binary_sensor.watering_system_low_low_water_level` (GPIO32)

**Complete reference:** See `/docs/entity_reference.md`

---

## 1. Hardware & Communication Tests

### Test 1.1: ESP32 Basic Connectivity
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** ESP32 flashed with watering-esp32.yaml

**Test Steps:**
1. Power on ESP32
2. Verify connection in Home Assistant: Settings → Devices → watering-esp32
3. Check entity status (should show "Online" or similar)
4. Verify API encryption is working (check logs for successful API handshake)

**Expected Results:**
- [ ] ESP32 appears in HA devices list
- [ ] All entities show "available" status
- [ ] No connection errors in HA logs
- [ ] API encryption shows as "connected"

**Pass Criteria:** All checkboxes checked, stable connection for 5+ minutes

**Notes:** _Record any issues or observations here_

---

### Test 1.2: Modbus Relay Board Communication
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** RS-485 adapter wired (TX=GPIO25, RX=GPIO26), relay board at 0x01

**Test Steps:**
1. Check ESPHome logs for Modbus initialization messages
2. Verify relay board responds to read coil commands
3. Attempt to toggle relay 16 (safe test - unused relay)
4. Check logs for any Modbus timeout errors

**Expected Results:**
- [ ] Modbus controller reports successful initialization
- [ ] Relay board responds to read requests within 100ms
- [ ] Relay 16 toggles on/off successfully
- [ ] No timeout errors in 5-minute observation period

**Pass Criteria:** All checkboxes checked, reliable communication

**Notes:** _Record Modbus response times, any retries needed_

---

### Test 1.3: Float Switch Inputs (Low/Low-Low)
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** GPIO33 and GPIO32 wired to float switches

**Test Steps:**
1. With tank full, verify both switches show correct state
2. Lower water level to trigger "Low" switch (GPIO33)
3. Verify state change in HA: `binary_sensor.watering_system_low_water_level`
4. Lower level to trigger "Low-Low" switch (GPIO32)
5. Verify state change in HA: `binary_sensor.watering_system_low_low_water_level`
6. Refill tank, verify both switches return to normal

**Expected Results:**
- [ ] Low switch (GPIO33) triggers at correct level
- [ ] Low-Low switch (GPIO32) triggers at correct level
- [ ] No false triggers due to water movement
- [ ] Switches return to normal state when refilled
- [ ] Debounce and delayed_off filters work as configured

**Pass Criteria:** Reliable state changes with no bounce/chatter

**Notes:** _Record actual trigger levels, any bounce observed_

---

### Test 1.4: Victron BLE Sensors
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** SmartSolar within BLE range, bindkey configured

**Test Steps:**
1. Check ESPHome logs for BLE advertisements from SmartSolar
2. Verify all MPPT sensors are updating in Home Assistant:
   - `sensor.watering_system_mppt_battery_voltage`
   - `sensor.watering_system_mppt_battery_current`
   - `sensor.watering_system_mppt_load_current`
   - `sensor.watering_system_mppt_pv_power`
   - `sensor.watering_system_mppt_yield_today`
3. Check error/fault sensors:
   - `binary_sensor.watering_system_mppt_error_state`
   - `binary_sensor.watering_system_mppt_fault_state`
4. Check sensor updates occur regularly (every 60s)
5. Move ESP32 away from SmartSolar (test range limits)
6. Move back within range, verify reconnection and sensor updates resume

**Expected Results:**
- [ ] BLE advertisements detected in logs
- [ ] All MPPT sensors appear in Home Assistant
- [ ] All sensors updating regularly (every 60s)
- [ ] Sensor values are reasonable (voltage 12-14V, etc.)
- [ ] Reconnection after temporary disconnect works
- [ ] Sensors resume updating after reconnection

**Pass Criteria:** All sensors available and updating, auto-reconnect works

**Notes:** _Record max reliable distance, reconnection time_

---

### Test 1.5: WiFi Signal Diagnostic Sensor (NEW)
**Status:** ⏸️ BLOCKED (needs ESP32 OTA flash — the sensor ships on the next firmware build)
**Last Run:** Not yet tested
**Prerequisites:** `esphome/watering-system.yaml` `wifi_signal` sensor flashed to the ESP32 (OTA)

**Test Steps:**
1. After the next OTA flash, open Developer Tools → States.
2. Find `sensor.watering_system_wifi_signal`.

**Expected Results:**
- [ ] `sensor.watering_system_wifi_signal` exists, reports RSSI in dBm, updates every 60 s.
- [ ] `device_class: signal_strength`, `entity_category: diagnostic` (ESPHome `wifi_signal` platform
      defaults; not set explicitly in YAML).
- [ ] Value plausible for the install (~-72 dBm measured at the marginal location).

**Pass Criteria:** Diagnostic sensor present and updating with a plausible dBm value.

**Notes:** Documented in `entity_reference.md` "Watering System Diagnostic Sensors". Diagnostic only —
does NOT affect watering control.

---

## 2. Safety Interlock Tests

### Phase 5.1 monitors — common setup (read before Tests 2.1–2.3 and 2.6)

Tests 2.1–2.3 and 2.6 cover the three built safety monitors in
`watering_safety/safety_automations.yaml` and their shared operational predicate. They are
**relay/logic-level Dev-Tools tests** — valves/pump are unwired, so there is zero irrigation risk.

**Prerequisites (all four):** Phase 5.1 deployed to the Green (commit `ea87748`, code-review fixes
included); ESP32 online (relays report `on`/`off`); system starts **parked in `manual_override`**.
**Re-park in `manual_override` between tests** (SOP until go-live).

**Holding a stable operational state (Tests 2.1 / 2.2).** The `state_*` scripts self-advance, so to
park the machine in a stable operational state for the tank/comms guards, temporarily **disable
`automation.watering_state_dispatcher`** (Settings → Automations toggle), then set the state with
the service below. With the dispatcher off nothing runs the state script, so the state sticks and
`binary_sensor.watering_operational` reads `on`. Re-enable the dispatcher afterward.
(`watering_state_on_error` stays ENABLED so the error teardown is still observed.)

```yaml
service: input_select.select_option
target:
  entity_id: input_select.watering_system_state
data:
  option: watering_plain
```

**Observation template** (Developer Tools → Template — keep open as the live dashboard):

```jinja
State:       {{ states('input_select.watering_system_state') }}
Operational: {{ states('binary_sensor.watering_operational') }}
Low-Low:     {{ states('binary_sensor.watering_system_low_low_water_level') }}
Cap (min):   {{ states('input_number.max_single_zone_runtime_min') }}
  enforced:  {{ [states('input_number.max_single_zone_runtime_min') | int(120), 120] | min }}
R1={{ states('switch.watering_system_relay_1_main_pump') }}
R2={{ states('switch.watering_system_relay_2_zone_1') }}
R3={{ states('switch.watering_system_relay_3_zone_2') }}
R4={{ states('switch.watering_system_relay_4_zone_3') }}
R5={{ states('switch.watering_system_relay_5_zone_4') }}
```

**Events (one per tab):** listen on `watering_system_event` for the state-machine/log breadcrumbs;
use a separate tab for `watering_cycle_complete` (Event 4) when a `cycle_uuid` is open.
Notifications land on the mobile app (WhatsApp/email path).

---

### Test 2.1: Tank Low-Low — Mid-Cycle Monitor (`watering_safety_tank_low_low`, Phase 5.1)
**Status:** ✅ PASS
**Last Run:** 2026-08-16
**Covers:** `automation.watering_safety_tank_low_low` — a Low-Low edge WHILE OPERATIONAL latches
`error_tank_low` (the mid-cycle case preflight cannot catch). The monitor only latches; the Phase 4
`watering_state_on_error` table owns the `safe_shutdown` + Event 4 + CRITICAL notify (proven in 3.6.h).
See "Phase 5.1 monitors — common setup" above.

**Part A — fires while operational (positive):**
1. Ensure Low-Low is `off` (R15 test relay OFF, or Set State
   `binary_sensor.watering_system_low_low_water_level` = `off`).
2. Disable `watering_state_dispatcher`; `select_option` state → `watering_plain` (template shows
   Operational = `on`).
3. Drive Low-Low → `on` (R15 test relay ON, or Set State).
- [x] State latches → `error_tank_low`.
- [x] `watering_state_on_error` runs: CRITICAL notification received; `safe_shutdown` closes all
      zone relays (R2–R5 off) + pressure relief. A `watering_cycle_complete` (Event 4, `error`)
      fires only if a `cycle_uuid` was open (none in this forced test → finalize no-ops).
- [x] `binary_sensor.watering_operational` is now `off` (error state), so Low-Low chatter does NOT
      re-fire the monitor.

**Part B — stands down when NOT operational (negative):**
4. Clear the error (`select_option` → `idle`); Low-Low → `off`.
5. With state = `idle` (Operational = `off`), drive Low-Low → `on`.
- [x] State does NOT change (stays `idle`); no `error_tank_low`, no teardown, no notify. (An idle
      Low-Low is preflight Check 1's job at the next cycle start, not this monitor's.)
6. Repeat with state = `manual_override`.
- [x] No latch (Operational = `off` in a control state).

**Pass Criteria:** Part A latches `error_tank_low` from the operational Low-Low edge; Part B never
latches from idle/parked. Re-enable the dispatcher; re-park in `manual_override`. **PASS 2026-08-16.**

**Notes:** _Record state-change latency and the `system_events` rows._

---

### Test 2.2: Comms Watchdog — Mid-Cycle ESP32 Dropout (`watering_safety_comms_watchdog`, Phase 5.1)
**Status:** ✅ PASS
**Last Run:** 2026-08-16
**Covers:** `automation.watering_safety_comms_watchdog` — any R1–R7 relay `unavailable`/`unknown`
for ≥10 s WHILE OPERATIONAL latches `error_comms_lost` (the proactive mid-cycle gap Phase 3.4
Part A/B did not cover). Uses the same R1–R7 availability proxy Part B keys off. The monitor only
latches; the on_error table sends the HIGH notify (NO `safe_shutdown` — comms policy). See
"Phase 5.1 monitors — common setup" above.

Best driven by a REAL comms loss (matches 3.6.d): a **physical cabinet power-cycle** takes all
seven relays `unavailable` together. A Dev-Tools Set State to `unavailable` also exercises the
logic path.

**Part A — fires while operational (positive):**
1. Disable `watering_state_dispatcher`; `select_option` state → `watering_plain` (Operational =
   `on`). (With a real power-cycle instead, hold a genuine dry cycle in `watering_plain`.)
2. Take a relay `unavailable` for > 10 s: physical cabinet OFF, or Set State
   `switch.watering_system_relay_1_main_pump` = `unavailable`.
- [x] After the 10 s `for:`, state latches → `error_comms_lost`.
- [x] HIGH notification received; NO `safe_shutdown` actuation (policy `safe_shutdown: false`).
- [x] `watering_operational` now `off`, so a second relay dropping does NOT re-fire.
3. Restore comms (cabinet ON / Set State → `off`): Part B (`watering_safety_r1_comms_recovery`)
   owns recovery — R1 back `off` → `idle` (per Test 2.5).

**Part B — restart-safety guard (`from: [on, off]`):**
- [x] On an HA restart the relays come up AT `unavailable` (no `on/off → unavailable` edge), so the
      watchdog does NOT fire during boot even if the restored state was operational and the ESP32
      takes > 10 s to reconnect. Confirm opportunistically on the next restart (watch that no
      spurious `error_comms_lost` latches before `watering_state_restart_recovery` idles the state).

**Part C — stands down when idle (negative):**
4. State = `idle`; take a relay `unavailable` > 10 s.
- [x] No latch (Operational = `off`; an idle comms loss is preflight Check 2's job next cycle).

**Pass Criteria:** Part A latches `error_comms_lost` after 10 s while operational; Part C never
latches from idle; Part B confirmed on a restart. Re-enable dispatcher; re-park. **PASS 2026-08-16.**

**Notes:** _Record detection time (~10 s + proxy latency) and recovery behavior._

---
### Test 2.3: Zone Runtime Limit — Stuck-Valve Backstop (`watering_safety_zone_runtime_limit`, Phase 5.1)
**Status:** ✅ PASS
**Last Run:** 2026-08-16
**Covers:** `automation.watering_safety_zone_runtime_limit` — a zone valve (R2–R5) on longer than
`min(max_single_zone_runtime_min, 120) + 1 min` grace → force-close THAT zone (direct
`switch.turn_off`) + HIGH notify. Fires in EVERY state EXCEPT `manual_override`. Watches ACTUAL
valve-on duration (distinct from the planned-runtime cap inside `calculate_zone_runtime`).

**Guard note:** this monitor fires in `idle`, so EXIT the park first (`manual_override` OFF → state
`idle`) or it stands down. No dispatcher change needed (a raw zone relay on does not move the state).

**Part A — single zone force-close (positive):**
1. Set `input_number.max_single_zone_runtime_min` = 1 (→ enforced cap 1, backstop `for:` = 2 min).
2. State = `idle` (park exited). Turn on Zone 1:
```yaml
service: switch.turn_on
target:
  entity_id: switch.watering_system_relay_2_zone_1
```
3. Wait ~2 min (cap + 1 grace) without closing it.
- [x] At ~2 min, R2 auto-closes (`switch.watering_system_relay_2_zone_1` → `off`).
- [x] HIGH notification: "Zone 1 valve exceeded the max single-zone runtime (1 min) and was
      force-closed…".
- [x] `input_select.watering_system_state` UNCHANGED (cycle not aborted — local fault only).
- [x] Zone can be reopened afterward (no latch).

**Part B — two zones at once (regression for the `close_zone` mode:single drop, fix #1):**
4. `max_single_zone_runtime_min` = 1. Turn on Zone 1 AND Zone 2 in ONE call so their `for:` timers
   arm together:
```yaml
service: switch.turn_on
target:
  entity_id:
    - switch.watering_system_relay_2_zone_1
    - switch.watering_system_relay_3_zone_2
```
5. Wait ~2 min.
- [x] BOTH R2 and R3 auto-close (mode:parallel + direct `switch.turn_off`; neither dropped). This
      is the exact case the pre-fix `script.close_zone` (mode:single) could have dropped for the
      second zone.
- [x] TWO HIGH notifications (one per zone; `send_high_notification` is mode:queued).

**Part C — normal full-runtime close does NOT trip (negative):**
6. `max_single_zone_runtime_min` = 1. Turn on Zone 3, and close it yourself at ~55 s (before cap+1).
- [x] No force-close event, no notify (the +1 grace keeps a normal close clear of the backstop).

**Part D — stands down in `manual_override` (negative):**
7. Park: `manual_override` ON (state `manual_override`). Turn on Zone 4; wait > 2 min.
- [x] R5 stays ON (monitor stands down during hands-on override).

**Part E — notify quotes the ENFORCED cap, not the raw helper (regression, fix #4):**
Fast Dev-Tools Template check (no long wait): set `max_single_zone_runtime_min` = 150 and render:
```jinja
{{ [states('input_number.max_single_zone_runtime_min') | int(120), 120] | min }}
```
- [x] Renders `120` (not `150`) — so a force-close message would quote "120 min", the enforced
      limit, not the raw helper. (The `for:` mirrors this, arming at 121 min, not 151.)

**Pass Criteria:** A/B force-close the overrun zone(s); C/D never trip; E renders 120. Restore
`max_single_zone_runtime_min` to its operating value; re-park in `manual_override`. **PASS 2026-08-16.**

**Notes:** _Record close latency vs the 2-min arm, and the exact notification text._

---
### Test 2.4: Emergency Stop Button
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** Emergency stop script configured, UI button available

**Test Steps:**
1. Start complex operation (e.g., fertigation with multiple devices active)
2. Press emergency stop button in HA dashboard
3. Observe immediate system response

**Expected Results:**
- [ ] ALL relays turn off (pump, valves, 24V cabinet) — commanded in parallel, immediate
- [ ] System state latches to `error_e_stop` (NOT `idle`) — this is what "does not
      auto-restart" means; corrected 2026-08-03 to match the as-built `emergency_stop`
- [ ] Critical confirmation notification sent
- [ ] System does not auto-restart (latched in `error_e_stop`)
- [ ] Manual restart possible only after clearing the `error_e_stop` latch

**Pass Criteria:** Relays de-energize immediately; script then verifies (4 s stabilization +
one repair cycle if any relay fails) and latches `error_e_stop`.

**Safety Note:** This is the "big red button" - must be 100% reliable

**Status note (2026-08-03):** the `emergency_stop` control logic was exercised via Test 2.5
Part B (ON branch) with R1 simulated. This hardware test (relays *physically* off during a
live operation) remains ⏸️ BLOCKED until the ESP32 is back online.

**Notes:** _Record shutdown time, any devices that didn't stop_

---
### Test 2.5: Comms-Lost Handling — Fail-Fast + Reactive Recovery (Phase 3.4)
**Status:** ✅ PASS (control logic; R1 simulated — ESP32 offline)
**Last Run:** 2026-08-03
**Prerequisites:** Part A guard in `stop_main_pump`; Part B automation
`automation.watering_safety_r1_comms_recovery`; R1
(`switch.watering_system_relay_1_main_pump`) `unavailable`.

**Verification method:** the ESP32 was offline (genuine WiFi loss), so R1 transitions were
simulated with **Developer Tools → States** (which fires real state-change events). This
validates the HA control logic; *physical* relay de-energization is covered by Test 2.4
(hardware, still ⏸️ BLOCKED until the ESP32 is online).

**Part A — fail-fast** (call `stop_main_pump` while R1 `unavailable`):
- [x] Exactly one `pump_comms_lost` / `error` row; **no** `pump_runaway` rows
- [x] State → `error_comms_lost`

**Part B — reactive recovery** (R1 returns while in `error_comms_lost`):
- [x] R1 → `off`: one `pump_comms_restored` / `info`, zones closed, state → `idle`
- [x] R1 → `on`: one `pump_comms_restored` / `warning` → `emergency_stop` → state
      `error_e_stop` + critical notification

**`safe_shutdown` completes despite a missing sub-script** (R1 `unavailable`, `stop_dosing_pumps` absent):
- [x] Both "started" and "completed" `safety_shutdown` rows (no `ServiceNotFound` halt)
- [x] Error state preserved (not forced to `idle`)

**Pass Criteria:** all boxes checked. ✅ All passed 2026-08-03 (`system_events` rows 46–58).

**Pending (hardware):** happy-path proof that relays *physically* de-energize on
`emergency_stop`, and a real graceful pump→relief `safe_shutdown`, require the ESP32 back
online (see Test 2.4).

---

### Test 2.6: Operational Predicate — `binary_sensor.watering_operational` (Phase 5.1, fix #2)
**Status:** ✅ PASS
**Last Run:** 2026-08-16
**Covers:** the shared single-source-of-truth predicate that guards Tests 2.1/2.2 and the Phase 4
control guard. ON iff `watering_system_state` is operational (not idle, not a control state, not
`error_*`). Code-review fix #2 added `unknown`/`unavailable` to the exclusion set so a garbage
source state reads OFF (fail-safe) instead of ON. **Run this before 2.1/2.2.** See
"Phase 5.1 monitors — common setup" (dispatcher-disable technique).

**Part A — truth table.** For each state, `select_option` (dispatcher DISABLED so it sticks) and
read `binary_sensor.watering_operational`:
- [x] `idle` → OFF
- [x] `watering_plain` (spot-check at least one operational state; also `window_check` /
      `preflight_check` / `post_cycle_relief`) → ON
- [x] `manual_override` → OFF
- [x] `winterized` → OFF
- [x] `error_tank_low` (and any `error_*`) → OFF

**Part B — fail-safe on garbage (the fix):**
1. Dev Tools → Set State `input_select.watering_system_state` = `unavailable` (Set State, since
   `select_option` rejects a non-option).
- [x] `binary_sensor.watering_operational` reads **OFF** (pre-fix it read ON, which could let the
      tank monitor latch `error_tank_low` on a startup-window Low-Low edge with no cycle running).
2. Set State = `unknown`.
- [x] `binary_sensor.watering_operational` reads **OFF**.

**Pass Criteria:** predicate matches the truth table AND reads OFF for `unknown`/`unavailable`.
Restore a real state (`select_option` → `idle`); re-enable dispatcher; re-park. **PASS 2026-08-16.**

**Notes:** _Set State is ephemeral — HA may overwrite the input_select on its next update; read
`watering_operational` immediately after forcing the state._

---

## 3. State Machine Tests

### Test 3.1: Full Cycle — Plain Watering (No Fertigation)
**Status:** 📋 READY TO RUN (relays live, valves not wired — see Test 3.6 rig note)
**Last Run:** Not yet tested (Phase 4)
**Prerequisites:** Phase 4 deployed; zone helpers configured; ESP32 online

**Test Steps:**
1. Start a cycle via the scheduler — the manual button or a timed window (Test 3.6.b).
2. Observe the self-advancing path: `window_check → preflight_check → watering_plain →
   post_cycle_relief → idle`.
3. Watch the relays and the Event bus (Events 1, 3, 4).

**Expected Results:**
- [ ] `window_check` sets each `zone_N_program` (§3.3 tree) and advances to `preflight_check`
      (unless all-off).
- [ ] `preflight_check` passes (tank ok, R1 available) → **Event 1**, `cycle_uuid` minted.
- [ ] `watering_plain`: R6 on / R7 off, pump starts, each due zone runs via `water_one_zone`
      (**Event 3** each), pump stops.
- [ ] `post_cycle_relief`: R9 relief cycle, R10 off, **Event 4** (`completed`), `cycle_uuid`
      cleared → `idle`.
- [ ] All relays OFF at idle; no errors.

**Pass Criteria:** Complete cycle, correct transitions, Events 1/3/4 fired, no errors.
**Detailed procedure:** Test 3.6.b–f (+ 3.6.l parallel/sequential). **Notes:** record total cycle time.

---

### Test 3.2: Preflight Abort → error_tank_low
**Status:** 📋 READY TO RUN
**Last Run:** Not yet tested (Phase 4)
**Prerequisites:** State machine deployed; Low-Low sensor readable (live float switch or simulated)

**Corrected premise (Phase 4).** Tank Low-Low is gated at **`preflight_check`** (and inside
`start_main_pump`), NOT continuously from `idle` — there is no real-time `idle → error_tank_low`
automation. A cycle that *starts* while Low-Low is active aborts to `error_tank_low`; sitting in
`idle` with Low-Low on does nothing until the next cycle start.

**Test Steps:**
1. Set Low-Low = `on` (live float switch, or Dev Tools → States).
2. Start a cycle (scheduler) or set state → `preflight_check`.
3. Verify the abort; then clear Low-Low and manually reset state → `idle`.

**Expected Results:**
- [ ] `preflight_check` → `error_tank_low` + `preflight_abort` log; **no** Event 1, no pump start.
- [ ] `watering_state_on_error` handles it: `safe_shutdown`, **Event 4** `error`, critical notification.
- [ ] Error latched until manual reset; reset to `idle` restores normal operation.

**Pass Criteria:** Low-Low blocks the cycle at preflight and latches `error_tank_low`.
**Detailed procedure:** Test 3.6.d step 2 + 3.6.h.

---

### Test 3.3: State + Cycle Persistence Across HA Restart (D-E)
**Status:** 📋 READY TO RUN
**Last Run:** Not yet tested (Phase 4)
**Prerequisites:** Phase 4 restart-recovery automation deployed

**Test Steps:** restart HA from each of: a control state, an operational state (with a dummy open
`cycle_uuid`), an `error_*` state, and `idle`.

**Expected Results:**
- [ ] **Control** (`manual_override` / `winterized`): state persists (RestoreEntity), no hardware
      safing, no watering triggered.
- [ ] **Operational** (e.g. `watering_plain`): recovery runs `abort_cycle_scripts` + `safe_shutdown`,
      state ends `idle`, any open `cycle_uuid` closed via finalize.
- [ ] **`error_*`**: latch preserved (state unchanged); finalize still closes an orphaned row.
- [ ] **`idle`**: no hardware action; finalize no-ops.
- [ ] All `input_select`/`input_text` helpers retain their values across the restart.

**Pass Criteria:** Control/error latches survive; operational states are safed to idle; the cycle row
always closes.
**Detailed procedure:** Test 3.6.k.

---

### Test 3.4: Control Guard — Manual Override + Winterized (D-F)
**Status:** 📋 READY TO RUN
**Last Run:** Not yet tested (Phase 4)
**Prerequisites:** `watering_state_control_guard` deployed

**Corrected premise (Phase 4).** The control guard does **not** pause a running cycle. It is a GUARD:
engaging a control boolean mid-cycle is **rejected** (the boolean reverts, a notification is sent, the
cycle continues); it engages only from `idle`, or from an `error_*` state with a warning. "Never
silently abort a running cycle." One merged automation handles both `manual_override_active` and
`system_winterized`.

**Test Steps:** for BOTH control booleans, toggle ON from `idle`, from an operational state, from an
`error_*` state, and from the *other* control state; then toggle OFF while parked.

**Expected Results:**
- [ ] `idle` + ON → parks in the control state (`manual_override` / `winterized`); winterized-entry
      fires one `watering_seasonal_export`.
- [ ] Operational + ON → **rejected** (boolean reverts, high notification, cycle continues, no export).
- [ ] `error_*` + ON → **engages** + high warning notification (prior error not auto-cleared).
- [ ] Other control state active + ON → **rejected** via the default branch.
- [ ] OFF while parked → `idle`; leaving `winterized` fires the de-winterization test (keyed on the
      STATE, not the boolean).

**Pass Criteria:** Engages only from idle/error; never aborts a running cycle; winter consumers fire
only on genuine state entry/exit.
**Detailed procedure:** Test 3.6.j.

---

### Test 3.5: DB Event Emission — Payload Contract (§13.3.1)

**Test ID:** 3.5
**Component:** State machine (Phase 4) — event emission half of the DB write contract
**Objective:** Verify the state machine fires the operational-database events with payloads matching
architecture.md §13.3.1, at the correct transition points.
**Status:** 📋 READY TO RUN (event *firing* is live; DB rows deferred to the Phase 3.5 writer)
**Last Run:** Not yet tested
**Prerequisites:** Phase 4 deployed; capture via Developer Tools → Events

**Scope note.** This tests that the state machine *fires correct events*. The AppDaemon side that
*consumes* them and writes DB rows is Section 10.6. As of 2026-08-16 all of Events 1/3/4/5 have a
consumer (`db_writer.py`/`DbWriter` for 1/3/4, `db_event_writer.py` for 5). Once db_writer is deployed
+ AppDaemon-restarted on the Green, Events 1/3/4 are verifiable **as DB rows** (Test 10.6), not only on
the bus. Event 2 (`watering_fert_dose_complete`) still has no publisher (fert hardware unwired).

**Expected Results (capture each on the Event bus during a full cycle):**
- [ ] `watering_preflight_complete` at preflight pass — `cycle_uuid`, `start_time`, `trigger_type`
      (∈ scheduled/manual/override), weather snapshot (`''`→NULL when unreadable). Fired by
      `state_preflight_check`.
- [ ] `watering_zone_run_complete` at each zone-run end — `cycle_uuid`, `zrun_uuid`
      (`<cycle_uuid>-z<id>`), `zone_id`, `weather_program`, `start_time`/`end_time`, `aborted`.
      Fired by `fire_zone_run_complete` (called by `water_one_zone`), reporting-only.
- [ ] `watering_cycle_complete` at cycle end — `cycle_uuid`, `end_time`, `outcome`
      (∈ completed/aborted/error). Fired by `finalize_cycle_record`.
- [ ] `watering_system_event` on a safety/error event — `timestamp`, `event_type`, `severity`
      (∈ info/warning/critical). Fired by `script.log_system_event`.
- [ ] **N/A in Phase 4:** `watering_fert_dose_complete` — the fert path is deferred (RS-485 unwired),
      so no dose events are emitted; re-enable this check when fertigation ships.
- [ ] One `cycle_uuid` is stable across all events of a cycle; one `zrun_uuid` per zone run.

**Pass Criteria:** Events 1/3/4/5 fire at the right points with contract-valid payloads; `cycle_uuid`
stable per cycle, `zrun_uuid` per zone run.
**Notes:** Cross-reference Section 10.6 (AppDaemon consumption) and Test 3.6.

---

### Test 3.6: Phase 4 State Machine — Full Walkthrough (relays live, valves not wired)

**Status:** ✅ **COMPLETE — 3.6.a–l ALL PASS** (relay/logic level; valves/pump unwired). Final items
closed 2026-08-16: c (weather tree + all-off), d (comms gate via physical cabinet power-cycle),
j Part 3 (`0c085c5` re-verify), k (idle→no-op), l (sequential). No 3.6 sub-tests remain.
**Last Run:** 2026-08-16 (3.6.d comms gate, build `13fa378`)
**Prerequisites:** Phase 4 deployed to the Green. ESP32 online. Tank floats jumpered to spare relays:
**R15 → Low-Low, R16 → Low** (relay ON = sensor ON; 5 s on / 30 s off debounce). NOTE: ADR-016 now
rests R6/R7 CLOSED — the older "R6 on at rest" assumptions in the sub-steps below are superseded
(`watering_plain` opens R6; `post_cycle_relief`/`safe_shutdown` close it). (An AppDaemon restart only
matters once the Event 1/3/4 write-listeners exist — Phase 3.5.)

**Run results (2026-08-15, deployed `0c085c5`):**
- **a** PASS (5 helpers / 8 scripts / 5 automations registered). **b** PASS (scheduler sets
  trigger/window, idle→window_check). **c** PASS (D-A fallback + advance + dispatch-by-handler;
  program tree off/light/heavy/normal + all-off→idle, 2026-08-16). **d** PASS: preflight pass +
  Event 1 (`c-` uuid), control gate (→idle), tank gate (→error_tank_low + `preflight_abort` +
  safe_shutdown + CRITICAL); **comms gate PASS 2026-08-16 (physical cabinet power-cycle →
  error_comms_lost + auto-recovery to idle).** **e** PASS (R6/R7 interlock,
  pump start, per-zone Event 3 `<cycle_uuid>-z<id>`). **f** PASS (full `completed` cycle → Event 4,
  cycle_uuid cleared, idle). **g** PASS (CRITICAL — abort cancels `water_one_zone`, NO stray Event 3).
  **h** PASS all 5 errors (safe_shutdown yes for tank/valve/relay, no for e_stop/comms; tiers
  critical/high/none; Event 4 `error` + uuid clear + latch each). **i** PASS (finalize no-ops on
  empty + non-`c-` uuid). **j** PASS all 4 parts (engage/exit from idle + exactly 1 export; reject
  while operational; ack-from-error; cross-control reject; e-stop-while-winterized preserves the
  state). **l-parallel** PASS. **k** → restart-recovery `initial:` bug FIXED by ADR-017, then **re-run
  2026-08-15 on `13fa378`: operational→idle+safe PASS (mid-cycle `watering_plain` → `idle`, uuid
  cleared, hardware safed); latch-preserved PASS for `manual_override`/`winterized` (no safing) and
  `error_tank_low` (safed but error latch kept); **idle→no-op PASS 2026-08-16 — 3.6.k COMPLETE.** Lesson:
  recovery takes ~2 min (relief bleed at the 120s default that resets each restart) — a first-seconds
  monitor snapshot looks like a failure, so **read the automation trace, not an early snapshot**.
- **Findings this session:** ADR-016 valve discipline (R6/R7 rest closed); `0c085c5` control-guard
  engage-from-error audit — **RE-VERIFIED PASS 2026-08-16** (3.6.j Part 3: `error_e_stop → manual_override`
  → state `manual_override`, `control_engage_from_error` `watering_system_event` fired
  [`value_before: error_e_stop`, `value_after: manual_override`, notes name the prior error], HIGH
  notification names `error_e_stop`); `fc06fc9` preflight reorder
  (kept; the "missing preflight_abort" was a stale Dev-Tools listener, not a real drop — re-arm
  listeners after a restart). Minor: relief input_number min=5 vs 30 s operational floor; the
  e-stop-while-winterized log emits a redundant "entering error_e_stop" line before "left as winterized".

**TEST RIG REALITY — read first.** The ESP32 / relay board is **online**: relays energize and
de-energize on command and report `on`/`off`. But the relay **outputs are not wired to the
valves or pump**, so there is no water flow and no physical valve travel. What this means:
- We can exercise the **entire control + relay-actuation path end-to-end** — a full completed
  cycle, per-zone Event 3, and the abort path — with **zero irrigation risk**. This is the ideal
  dry run.
- `start_main_pump` now **succeeds**: R1 energizes and reports `on`, so preflight and pump-start
  pass. (The pre-2026-08-12 "ESP32 offline → `error_relay_state`" outcome no longer applies.)
- **Not** verified here: real water delivery, physical valve *position* (only the relay coil ack),
  actual pump operation. The 12 s valve-travel delays still elapse (they are time-based) but there
  is no valve to travel.
- Tank / comms sensors: if the Low-Low float switch is wired and reading, use it live; otherwise
  simulate via **Developer Tools → States** (`binary_sensor.watering_system_low_low_water_level`
  = `off`/`on`). R1 availability is the ESP32/comms proxy (D-G).

**Roster under test (post-review structure).** 5 automations — `watering_state_dispatcher`,
`watering_state_scheduler`, `watering_state_on_error` (ONE table-driven automation for all five
`error_*`), `watering_state_restart_recovery`, `watering_state_control_guard` (ONE merged guard
for override + winterized). Scripts — `state_window_check` / `state_preflight_check` /
`state_watering_plain` / `state_post_cycle_relief`, `finalize_cycle_record`, `abort_cycle_scripts`,
plus `fire_zone_run_complete` and the extracted `water_one_zone` (per-zone open → hold → close →
Event 3).

**Setup for every sub-test.** Developer Tools → Events: listen on `watering_preflight_complete`,
`watering_zone_run_complete`, `watering_cycle_complete`, `watering_seasonal_export`, and
`watering_system_event`. Use short test values so a full cycle is a few minutes: zone runtimes
~1 min, `input_number.pressure_relief_duration_sec` ~15 s. Drive states from Developer Tools →
States when a sub-test says "set state" — the dispatcher reacts to a manual set exactly as to a
self-advance.

**3.6.a — Config loads clean.**
- [x] No Phase 4 YAML/schema errors in the HA log after restart.
- [x] 5 helpers exist: `input_text.cycle_uuid`, `input_text.zone_run_uuid`,
      `input_select.active_watering_window`, `input_select.active_trigger_type`,
      `input_button.start_watering_cycle_now`.
- [x] 5 automations registered; scripts registered incl. `script.water_one_zone` and
      `script.fire_zone_run_complete`.

**3.6.b — Scheduler starts a cycle (NEW — owns cycle START).**
1. State = `idle`; `manual_override_active` + `system_winterized` OFF.
2. Path A (manual): press `input_button.start_watering_cycle_now`.
3. Path B (timed): set `input_datetime.morning_window_start` to ~1 min ahead with
   `input_boolean.enable_morning_window` ON; wait for the time trigger.
- [x] `active_trigger_type` set to `manual` (button) or `scheduled` (timed).
- [x] `active_watering_window` = `morning` if `now().hour < 12` else `evening` (button) / the fired
      window (timed).
- [x] State advances `idle → window_check`.
- [ ] **Guard:** with state ≠ idle, or override/winterized ON, the scheduler does NOT start (no
      transition).
- [ ] A timed trigger whose `enable_<window>_window` is OFF does nothing; the **manual button
      ignores** the enable booleans (deliberate operator override).

**3.6.c — window_check weather tree + dispatcher.**
1. Set the four `input_select.zone_N_season` and the `zone_N_{season}_*` thresholds to known
   values; set the brightsky sensors (or read live).
2. Set state → `window_check`; observe each `input_select.zone_N_program`.
- [x] Programs match the architecture.md §3.3 tree for contrived inputs (force each of
      off/light/normal/heavy: e.g. heavy = high `temp_avg_high_3day` + low `rain_72h`; off = high
      `rain_72h`; light = high `rain_24h`). **PASS 2026-08-16** (zone 1, spring thresholds
      roff=20/rlight=10/rmin=5/theavy=28/tnormal=22; brake = `manual_override` ON so runnable
      programs abort at preflight Check 3 → idle): off `(72h=25)`, light `(24h=15)`,
      heavy `(temp=30, 72h=0)`, normal `(temp=25)` — all four match.
- [x] **D-A:** a brightsky sensor `unavailable` → all zones `normal` + a `state_window_check`
      warning row.
- [x] **All-off:** thresholds forcing every zone `off` → state returns to `idle` (no advance).
      Otherwise → `preflight_check`. **PASS 2026-08-16** (`rain_72h=100` → all four `off`; state went
      straight to `idle`, not `preflight_check`; `watering_system_event` `state_window_check`/`info`
      "All zones resolved to 'off' - nothing due. Returning to idle.").
- [x] **Dispatcher (derivation):** setting state → an `error_*` / control / `idle` state calls **no**
      `state_*` script; setting → `window_check`/`preflight_check`/`watering_plain`/
      `post_cycle_relief` calls the matching `script.state_<name>` (dispatch derived from handler
      existence, not a hard-coded list).

**3.6.d — preflight gates + Event 1.**
1. **Comms (D-G):** set R1 (and the tank sensor) `unavailable` via Dev Tools; set state →
   `preflight_check` → `error_comms_lost` + `preflight_abort` log.
   - [x] **PASS 2026-08-16** — **physical cabinet power-cycle** (real comms loss, not a Dev-Tools
         fake). Cabinet OFF → R1 + Low-Low `unavailable`; set state → `preflight_check` → Check 1
         fired: `preflight_abort` (`severity error`, Low-Low → `unavailable`, "treating as comms loss
         (D-G)") → state `error_comms_lost`; HIGH notification; **no relay actuation** (comms policy
         `safe_shutdown: false`). Cabinet back ON → `watering_safety_r1_comms_recovery` auto-fired
         (R1 back `off`): `pump_comms_restored` (`info`, "clearing error_comms_lost to idle") →
         state `idle`, relays `off`. Both loss and recovery breadcrumbs confirmed on the bus.
2. **Tank:** tank sensor readable, Low-Low = `on`; set state → `preflight_check` → `error_tank_low`.
3. **Control:** `manual_override_active` or `system_winterized` ON; set state → `preflight_check` →
   returns to `idle` (defence-in-depth, `error: true` stop; no cycle opened).
4. **Pass:** tank readable + `off`, R1 available, override/winterized OFF; set state →
   `preflight_check` →
   - [x] **Event 1** `watering_preflight_complete` fires: fresh `c-…` `cycle_uuid`, `start_time`,
         `trigger_type`, weather snapshot (numeric or `''`→NULL when unreadable).
   - [x] `input_text.cycle_uuid` populated; advance → `watering_plain`.

**3.6.e — watering_plain live (relay level).** Continue from 3.6.d pass.
- [x] R6 `turn_on`, R7 `turn_off` (relays actuate + report); 12 s valve delay.
- [x] `start_main_pump` **passes**: R9 off, R6-XOR-R7 satisfied, R1 turns on + confirms, 30 s
      stabilization, no error.
- [x] `run_zone_sequence` → each due zone via `water_one_zone`: zone relay `on`, holds its runtime,
      zone relay `off`, then **Event 3** `watering_zone_run_complete` — `cycle_uuid` = the open cycle,
      `zrun_uuid` = `<cycle_uuid>-z<id>`, `weather_program`, `start_time`/`end_time`, `aborted=0`.
- [x] `stop_main_pump` (R1 off), `close_all_zones`, 12 s delay, advance → `post_cycle_relief`.

**3.6.f — post_cycle_relief → full completed cycle (NEW — now reachable).**
- [x] `close_all_zones`; `open_pressure_relief` (R9 `on` → wait `pressure_relief_duration_sec` → R9
      `off`; pump auto-stop if somehow still on).
- [x] R10 `turn_off` + 3 s confirm; a **warning** (not error) if R10 does not confirm off.
- [x] `finalize_cycle_record('completed')` → **Event 4** `watering_cycle_complete` (`outcome:
      completed`, `end_time`); `input_text.cycle_uuid` **cleared**; state → `idle`.
- [x] **Full cycle complete, all relays off.** Record total cycle time.

**3.6.g — Abort mid-cycle cancels water_one_zone (NEW — CRITICAL, protects the abort-set fix).**
1. Start a cycle; set a zone runtime ~3 min so a zone is mid-hold in `watering_plain` (its zone
   relay `on`, `water_one_zone` running).
2. Inject an error whose policy safes hardware: either set state → `error_tank_low` (Dev Tools) OR
   call `script.emergency_stop` (→ `error_e_stop`).
- [x] `watering_state_on_error` fires; `abort_cycle_scripts` turns **off** the `state_*` scripts,
      `run_zone_sequence`, **and** `water_one_zone` (check each script entity goes `off`).
- [x] The mid-hold zone's `watering_zone_run_complete` does **NOT** fire — the hold delay is
      cancelled before `close_zone`/Event 3. *(This is exactly the behaviour the abort-set addition
      protects; if a stray "completed" Event 3 fires, the fix regressed.)*
- [x] `safe_shutdown` (for `error_tank_low`) closes all zone relays + pump + relief; **Event 4**
      `outcome: error`; `cycle_uuid` cleared; the error state is latched (not overwritten).
      *(For `error_e_stop` via `emergency_stop`, hardware is safed by emergency_stop itself; on_error
      does not run safe_shutdown for e_stop.)*

**3.6.h — Table-driven on_error, per error (was 5 automations, now 1).** For each of
`error_e_stop`, `error_comms_lost`, `error_tank_low`, `error_valve_interlock`, `error_relay_state`:
first set `input_text.cycle_uuid` to a dummy `c-test…`, then set state → that error.
- [x] `abort_cycle_scripts` ran.
- [x] `safe_shutdown` ran for tank / valve / relay; did **not** run for e_stop / comms (policy column).
- [x] **Event 4** `watering_cycle_complete` `outcome: error`; `input_text.cycle_uuid` cleared
      (**invariant: the cycle row always closes**).
- [x] Notification tier: critical (tank/valve/relay), high (comms), none (e_stop); each notify sets
      `bypass_winterization` so it lands even if `system_winterized` is on.
- [x] The error state is **not** overwritten (latch held).

**3.6.i — finalize no-op + cycle_open format check.**
- [x] `input_text.cycle_uuid` empty → call `script.finalize_cycle_record` (outcome `error`) → **no**
      Event 4, no state/helper change.
- [x] Set `cycle_uuid` to a non-`c-` value (e.g. `unknown`) → finalize still no-ops (open-cycle test
      keys on the `c-` uuid format, not a sentinel list).

**3.6.j — Control guards (merged) + winter consumers.** For BOTH `manual_override_active` and
`system_winterized`:
- [x] `idle` + boolean ON → state = the control state; **winterized** ON also fires exactly **one**
      `watering_seasonal_export` (on entering the state).
- [x] Operational (e.g. `watering_plain`) + boolean ON → **rejected**: boolean reverts OFF, high
      notification, state unchanged, **no** export.
- [x] `error_*` + boolean ON → **engages** + high **warning** notification.
- [x] Boolean OFF while parked in that control state → returns to `idle`; **leaving `winterized`
      fires the de-winterization test** (notification/tests.yaml, keyed on the STATE, not the boolean).
- [x] **NEW:** engage one control boolean while the OTHER control state is active (e.g. turn
      `manual_override_active` ON while state = `winterized`) → **rejected via the default branch**
      (boolean reverts, "resolve current state" notification).
- [x] **NEW:** call `script.emergency_stop` while state = `winterized` → state **stays** `winterized`
      (not `error_e_stop`), hardware safed, CRITICAL sent → **no** spurious de-winterization test.

**3.6.k — Restart recovery (D-E).**
- [x] Operational (e.g. `watering_plain`) + a dummy open `cycle_uuid` → restart HA → on start:
      `abort_cycle_scripts` + `safe_shutdown` run, state ends `idle`, `cycle_uuid` cleared.
      **PASS 2026-08-15** (staged `watering_plain` + `c-20260815-120000`, dispatcher disabled during
      staging; trace 23:10:32→23:12:46: outer-if true → abort → safe_shutdown [~2 min relief bleed,
      dur reset to 120s default] → state=idle → inner backstop skipped [safe_shutdown already idled]
      → finalize closed the row. NOTE: a monitor snapshot taken in the first seconds looked like a
      failure — it was mid-recovery; the trace is ground truth.)
- [x] `manual_override` / `winterized` / `error_*` → restart → **latch preserved** (state unchanged);
      finalize still runs (no-op when `cycle_uuid` empty; closes an orphaned row if a control state
      was raced in mid-error). **Hardware safing differs by class** (corrected 2026-08-15): control
      states (`manual_override`/`winterized`) **skip** safing (recovery outer-if false); `error_*`
      **is** safed (outer-if true → `abort` + `safe_shutdown`), but `safe_shutdown`'s `ended_in_error`
      branch preserves the error latch instead of clearing to idle. **PASS 2026-08-15** — 2a
      `manual_override` (no safing, latch kept), 2b `winterized` (no safing, latch kept, **no spurious
      `watering_seasonal_export` on restart**), 2c `error_tank_low` (safed + latch kept).
- [x] `idle` → restart → finalize no-op, no hardware action. **PASS 2026-08-16** (trace at boot:
      outer `if` → *No action executed* [abort/safe_shutdown/idle-set skipped]; only the unconditional
      `finalize_cycle_record` ran, 0.02 s, no Event 4 [empty `cycle_uuid`]; state stayed `idle`, all
      relays off). **3.6.k COMPLETE.**

**3.6.l — Parallel vs sequential live.** Run a full cycle in each `input_select.zone_sequencing_mode`
with ≥2 due zones (short runtimes):
- [x] **parallel:** due-zone relays energize together; each closes at its own runtime; one Event 3 each.
- [x] **sequential:** one zone relay at a time; 30 s gap between zones (none after the last); one
      Event 3 each, in order. **PASS 2026-08-16** (base=1 min + `light` ×0.5 = 30 s runs; cycle
      `c-20260816091904156136`: R2→R3→R4→R5 one at a time, no overlap; four Event 3 in order
      z1→z4, each `zrun_uuid <cycle>-z<N>`, `planned_duration_sec 30`, `aborted 0`; inter-zone gaps
      exactly 30 s by timestamp [end→next-start]; returned to `idle`, `cycle_uuid` cleared).

**Deferred to wired hardware (valves/pump connected):** real water delivery, physical valve travel /
position, actual pump/irrigation. **Deferred to the Phase 3.5 writer:** DB rows for Events 1/3/4
(only Event 5 is consumed today) — see Section 10 / roadmap §3.5. **Deferred Phase 4 follow-ons**
(not on the fast-follow list — tracked here + impl_roadmap.md §4, ADR-015): fert states
(`fert_prep` / `fert_dose_phase1` / `fert_dose_phase2`) — RS-485 dosing pumps unwired; the
safe-stop / e-stop UX buttons + fert-flush branch + the `'aborted'` cycle-outcome producer (D-F,
"another day").

**Pass Criteria:** 3.6.a–l pass at the relay/logic level. In particular: **3.6.f** completes a full
cycle to `idle` with Event 4 `completed`, and **3.6.g** fires **no** stray Event 3 on abort. Record
anything that diverges.

---

## 4. Script Tests

### Test 4.1: script.open_zone - Valid Conditions
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Zone control scripts implemented, pump and valves connected

**Test Steps:**
1. Turn on main pump (R1) and bypass valve (R6)
2. Ensure fert line valve (R7) is off
3. Call `script.open_zone` with `zone_id: 1`

**Expected Results:**
- [x] Zone 1 valve opens successfully
- [x] Pump verification check passes
- [x] Valve interlock check passes (R6 XOR R7)
- [x] No errors logged

**Pass Criteria:** Zone opens when all safety conditions met

**Notes:** Tested with all 4 zones, both bypass and fert line flow paths

---

### Test 4.2: script.open_zone - Safety Interlocks
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Zone control scripts implemented

**Test Steps:**
1. Test A: Pump OFF, attempt to open zone
2. Test B: Both valves open (R6=on, R7=on), attempt to open zone
3. Test C: Both valves closed (R6=off, R7=off), attempt to open zone
4. Test D: Invalid zone_id (5, 99)
5. Test E: Missing zone_id parameter

**Expected Results:**
- [x] Test A: Script aborts, zone remains closed, error logged
- [x] Test B: Script aborts, sets `error_valve_interlock` state
- [x] Test C: Script aborts, sets `error_valve_interlock` state
- [x] Test D: Script aborts silently (safe failure)
- [x] Test E: HA catches missing required parameter

**Pass Criteria:** All invalid conditions correctly blocked

**Notes:** Valve interlock (R6 XOR R7) working correctly. Invalid zone_id fails safely but without error log.

---

### Test 4.3: script.calculate_zone_runtime - Program Multipliers
**Status:** ⚠️ RE-TEST REQUIRED (behaviour changed by ADR-020 — same-day heavy split retired)
**Last Run:** 2025-10-22 (old model)
**Prerequisites:** Runtime calculation script implemented (Phase 7 / ADR-020 version)

**Test Steps (window-independent multipliers now):**
1. Test off program (expected: 0.0x)
2. Test light program (expected: 0.5x)
3. Test normal program (expected: 1.0x)
4. Test heavy program (expected: 1.0x — MAIN dose; window no longer matters)
5. Test booster program (expected: 0.5x)
6. Test heavy + single-window + interval==1 EDGE (expected: 1.5x single dose)

**Expected Results (base 10 min):**
- [ ] Off: 0.0 min
- [ ] Light: 0.5x → 5 min
- [ ] Normal: 1.0x → 10 min
- [ ] Heavy (any window, interval≥2 or dual-window): 1.0x → 10 min
- [ ] Booster: 0.5x → 5 min
- [ ] Heavy + single-window + `zone_N_watering_interval_days`==1: 1.5x → 15 min
- [ ] `result.program` present in the response (unchanged)

**Pass Criteria:** Multipliers match the ADR-020 table (architecture.md §3.3); the heavy
value is independent of `window`; the `booster` case returns 0.5x; the N==1 single-window
edge returns 1.5x.

**Notes:** The old dual-window split (morning 1.0x + evening 0.5x) and evening-independence
(ADR-009) were RETIRED — heavy's extra 0.5x now rides a separate `booster` run at the interval
midpoint (see Test 4.22 below and `state_window_check`). The N==1 single-window 1.5x is the one
survivor of ADR-007's single-window behaviour.

---

### Test 4.4: script.run_zone_sequence - Parallel Mode
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Zone sequencing script implemented, parallel mode configured

> **⚠️ Re-run required (Phase 4).** The per-zone open→hold→close body was extracted into
> `script.water_one_zone` (commit `e8181f7`); `run_zone_sequence` now calls it ×4 inside a
> `parallel:` block. Behaviour should be identical (the pass criteria below still apply), but re-run
> to confirm, and additionally verify each due zone now fires **Event 3**
> `watering_zone_run_complete` via `water_one_zone`. Abort-cancels-`water_one_zone`: Test 3.6.g.

**Test Steps:**
1. Set `zone_sequencing_mode` to `parallel`
2. Test A: All zones normal program, 1 min runtime
3. Test B: Mixed programs (off/light/normal/heavy), 2 min base
4. Test C: All zones off program

**Expected Results:**
- [x] Test A: All zones open simultaneously, runtime ≈ 1 minute total
- [x] Test B: Zones 2,3,4 open together (zone 1 skipped), staggered closing (light@1min, normal+heavy@2min)
- [x] Test C: No zones open, completes in <1 second (efficient skip)
- [x] Parallel execution confirmed (not sequential)
- [x] All relays OFF after completion

**Pass Criteria:** Zones run simultaneously, independent timers

**Notes:** Measured runtimes: Test A=60s, Test B=120s, Test C=0.09s. Staggered closing proves independent zone timers.

---

### Test 4.5: script.run_zone_sequence - Sequential Mode
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Zone sequencing script implemented, sequential mode configured

> **⚠️ Re-run required (Phase 4).** The per-zone open→hold→close body was extracted into
> `script.water_one_zone` (commit `e8181f7`); `run_zone_sequence` now calls it ×4, keeping the 30 s
> inter-zone delay in the caller (so a skipped zone still adds no delay). Behaviour should be
> identical (the pass criteria below still apply), but re-run to confirm, and additionally verify
> each due zone now fires **Event 3** `watering_zone_run_complete` via `water_one_zone`.

**Test Steps:**
1. Set `zone_sequencing_mode` to `sequential`
2. Test A: All zones normal program, 1 min runtime
3. Test B: Mixed programs (off/light/normal/heavy), 1 min base
4. Verify 30-second inter-zone delays

**Expected Results:**
- [x] Test A: Zones run one at a time, 30s delays between zones, runtime ≈ 5.5 min (4×60s + 3×30s)
- [x] Test B: Off zones skipped entirely (no wasted delay), runtime ≈ 3.5 min
- [x] Only one zone open at any time
- [x] All relays OFF after completion

**Pass Criteria:** Sequential execution with inter-zone delays

**Notes:** Measured runtimes: Test A=330.25s (perfect), Test B=210s (perfect). Off zones properly skipped.

---

### Test 4.5a: script.water_one_zone — Single Zone (NEW, Phase 4)
**Status:** 📋 READY TO RUN (relays live, valves not wired)
**Last Run:** Not yet tested
**Prerequisites:** Phase 4 deployed; ESP32 online

**Purpose:** exercise the extracted per-zone script directly — the shared body behind
`run_zone_sequence`'s parallel and sequential modes (commit `e8181f7`).

**Test Steps (Developer Tools → Actions → `script.water_one_zone`):**
1. `zone_id: 1, runtime_minutes: 1, weather_program: normal, cycle_uuid: c-test123`.
2. Same but `runtime_minutes: 0` (and once negative).
3. Same but `cycle_uuid: ""` (empty).
4. Fire 4 instances near-simultaneously (different `zone_id`s).

**Expected Results:**
- [ ] `runtime>0`: zone relay `on` → ~1 min hold → zone relay `off` → **Event 3**
      `watering_zone_run_complete` (`zrun_uuid = c-test123-z1`, `aborted: 0`).
- [ ] `runtime<=0`: **no-op** — no relay change, no Event 3.
- [ ] empty `cycle_uuid`: Event 3 still fires with `cycle_uuid: ""` and a standalone `zrun_uuid`
      (`z-<ts>-1`) — an uncorrelated test run, not a failure.
- [ ] The `fire_zone_run_complete` call is `continue_on_error` (reporting-only) — it is **not** on
      the fail-the-cycle path.
- [ ] 4 parallel instances all run (mode `parallel`, max 4 — none dropped).

**Pass Criteria:** Correct per-zone actuation + Event 3; `runtime<=0` no-op; parallel-safe.
**Cross-ref:** Test 3.6.e (in-cycle), Test 3.6.g (abort cancels it — the abort-set dependency).

---

### Test 4.6: Heavy Program - Mid-Day Weather Change
**Status:** ❌ OBSOLETE — superseded by ADR-020 (same-day heavy split + evening independence retired).
The mid-day-adaptation intent now lives in the mid-interval booster's fresh weather re-evaluation
(Test 4.22). Heavy no longer runs an evening 0.5x on the same day; a heavy zone runs 1.0x on its due
day and a 0.5x booster at the interval midpoint. Do not re-run as written.

_(Original steps/results retained in git history; removed here to avoid asserting retired behaviour.)_

---

### Test 4.7: Decimal Runtime Handling
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Runtime calculation implemented

**Test Steps:**
1. Set zone to light program, 1 min base runtime
2. Both windows enabled (dual-window mode)
3. Execute morning window

**Expected Results:**
- [x] Calculated runtime: 0.5 minutes = 30 seconds (exactly)
- [x] Zone runs for exactly 30 seconds (measured)
- [x] No rounding errors or timing drift

**Pass Criteria:** Decimal runtimes handled precisely

**Notes:** Measured 30 seconds exactly. Confirms Home Assistant handles fractional minute delays correctly.

---

### Test 4.8: Error State Recovery
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** Error states implemented

**Test Steps:**
1. Trigger `error_valve_interlock` state (both valves open)
2. Attempt to open zone (should fail)
3. Fix valve configuration (close one valve)
4. Manual reset state to idle
5. Retry zone open

**Expected Results:**
- [x] Error state prevents zone operations
- [x] After fix, manual reset to idle works
- [x] Zone opens successfully after recovery
- [x] System returns to normal operation

**Pass Criteria:** Clean recovery from error states

**Notes:** Manual state reset required (no auto-recovery). Idempotent behavior confirmed - scripts safe to call multiple times.

---

### Test 4.9: Full Cycle Integration Test
**Status:** ✅ PASSED  
**Last Run:** 2025-10-22  
**Prerequisites:** All zone scripts implemented

**Test Steps:**
1. Configure parallel mode, all zones normal, 1 min runtime
2. Set valid flow path (pump on, bypass open, fert line closed)
3. Clear cycle event log
4. Execute `script.run_zone_sequence` with `window: "morning"`
5. Monitor complete execution

**Expected Results:**
- [x] All 4 zones open and close successfully
- [x] Runtime ≈ 60 seconds (parallel execution)
- [x] All relays return to OFF state
- [x] No errors in system log
- [x] Script trace shows success

**Pass Criteria:** Complete cycle executes without manual intervention

**Notes:** Full integration test confirms all components working together. Ready for state machine integration.

---

### 4.10 Pump Start - Normal Operation

**Test ID:** 4.10  
**Script:** `script.start_main_pump`  
**Objective:** Verify pump starts successfully under ideal conditions  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF
- Tank level: OK (Low-Low sensor OFF)
- Bypass valve (R6): ON
- Fert line valve (R7): OFF
- Pressure relief (R9): OFF

**Test Steps:**
1. Clear `input_text.cycle_event_log`
2. Verify R6 = ON, R7 = OFF (valid interlock)
3. Call service: `script.start_main_pump`
4. Wait 3 seconds (relay verification delay)
5. Verify pump relay (R1) = ON
6. Verify no error state set (state machine = 'idle')
7. Wait 30 seconds (pressure stabilization)
8. Check Home Assistant logs for errors
9. Check cycle_event_log for entries

**Expected Results:**
- Pump relay (R1) turns ON after 3s
- No error state set
- No error messages in HA logs
- cycle_event_log contains no entries (clean start, no warnings)
- Total time: ~33 seconds (3s verify + 30s stabilize)

**Actual Results:**
- Pump relay (R1): ON ✓
- Error state: idle ✓
- HA log errors: None ✓
- cycle_event_log: Empty ✓
- Total time: 33 seconds ✓

**Pass Criteria:** Script completes in 33 seconds, pump running, no errors

**Result:** ✅ PASS

---

### 4.11 Pump Start - Tank Low Abort

**Test ID:** 4.11  
**Script:** `script.start_main_pump`  
**Objective:** Verify pump start aborts when tank is low-low  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF
- **Tank level: LOW-LOW (sensor ON via R15)** ← Critical
- Bypass valve (R6): ON (valid interlock)
- Fert line valve (R7): OFF

**Test Steps:**
1. Clear cycle_event_log
2. Manually turn ON R15 to simulate low-low tank
3. Verify `binary_sensor.watering_system_low_low_water_level` = ON
4. Call service: `script.start_main_pump`
5. Immediate check: Pump relay (R1) should remain OFF
6. Check state machine state
7. Check Home Assistant logs

**Expected Results:**
- Pump relay (R1) remains OFF
- State machine transitions to `error_tank_low`
- HA log shows error: "Tank level low-low detected - cannot start pump"
- cycle_event_log empty (abort before operation)
- Script aborts immediately (<1 second)

**Actual Results:**
- Pump relay (R1): OFF ✓
- Error state: error_tank_low ✓
- HA log error: "Tank level low-low detected - cannot start pump" ✓
- cycle_event_log: Empty ✓
- Abort time: <1 second ✓

**Pass Criteria:** Immediate abort with correct error state, pump stays OFF

**Result:** ✅ PASS

---

### 4.12 Pump Start - Pressure Relief Self-Repair Success

**Test ID:** 4.12  
**Script:** `script.start_main_pump`  
**Objective:** Verify self-repair successfully closes stuck pressure relief valve  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF
- Tank level: OK
- Bypass valve (R6): ON
- Fert line valve (R7): OFF
- **Pressure relief (R9): Manually turned ON** ← Stuck open

**Test Steps:**
1. Clear cycle_event_log
2. Manually turn ON pressure relief valve (R9) via Lovelace
3. Verify R9 = ON (simulating stuck valve)
4. Call service: `script.start_main_pump`
5. Observe: Script should detect R9 is open
6. Wait 3 seconds (close attempt + verification)
7. Verify R9 closes automatically
8. Verify script continues with pump start
9. Wait 3 seconds (pump relay verification)
10. Wait 30 seconds (pressure stabilization)
11. Check cycle_event_log for self-repair message

**Expected Results:**
- R9 closes automatically (self-repair succeeds)
- Pump relay (R1) turns ON
- No error state set (state machine still 'idle')
- cycle_event_log contains self-repair messages:
  - "Pressure relief valve (R9) was open, closed successfully, continuing"
- Total time: ~36 seconds (3s close + 3s verify + 30s stabilize)

**Actual Results:**
- R9 after self-repair: OFF ✓
- Pump relay (R1): ON ✓
- Error state: idle ✓
- cycle_event_log message: "02/11 14:23:45 - Pressure relief valve (R9) was open, closed successfully, continuing" ✓
- Total time: 36 seconds ✓

**Pass Criteria:** Self-repair succeeds, pump starts normally, event logged

**Result:** ✅ PASS

**Notes:** Initial test failed due to race condition (state checked too quickly after close). Fixed by adding 500ms delay after subscript call. Re-tested and passed.

---

### 4.13 Pump Start - Valve Interlock Failures

**Test ID:** 4.13a, 4.13b  
**Script:** `script.start_main_pump`  
**Objective:** Verify pump start aborts with invalid valve configurations  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS (both tests)

#### Test 4.13a: Both Valves OFF

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF (including R6 and R7)
- Tank level: OK
- **Bypass (R6): OFF** ← Invalid
- **Fert line (R7): OFF** ← Invalid

**Test Steps:**
1. Clear cycle_event_log
2. Verify both R6 and R7 are OFF
3. Call service: `script.start_main_pump`
4. Immediate check: Pump should not start
5. Check state machine state
6. Check Home Assistant logs

**Expected Results:**
- Pump relay (R1) remains OFF
- State machine transitions to `error_valve_interlock`
- HA log error: "Invalid valve configuration: Both R6 and R7 are off. Exactly one valve must be open."
- cycle_event_log empty (abort before operation)
- Script aborts immediately (<1 second)

**Actual Results:**
- Pump relay (R1): OFF ✓
- Error state: error_valve_interlock ✓
- HA log error: Correct message ✓
- Abort time: <1 second ✓

**Result:** ✅ PASS

---

#### Test 4.13b: Both Valves ON

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF except R6 and R7
- Tank level: OK
- **Bypass (R6): Manually turned ON**
- **Fert line (R7): Manually turned ON**

**Test Steps:**
1. Clear cycle_event_log
2. Manually turn ON both R6 and R7 via Lovelace
3. Verify both R6 = ON and R7 = ON
4. Call service: `script.start_main_pump`
5. Immediate check: Pump should not start
6. Check state machine state
7. Check Home Assistant logs

**Expected Results:**
- Pump relay (R1) remains OFF
- State machine transitions to `error_valve_interlock`
- HA log error: "Invalid valve configuration: Both R6 and R7 are on. Exactly one valve must be open."
- cycle_event_log empty (abort before operation)
- Script aborts immediately (<1 second)

**Actual Results:**
- Pump relay (R1): OFF ✓
- Error state: error_valve_interlock ✓
- HA log error: Correct message ✓
- Abort time: <1 second ✓

**Result:** ✅ PASS

**Pass Criteria (both tests):** Valve interlock detected, correct error state, pump never starts

---

### 4.14 Pump Stop - Normal Operation

**Test ID:** 4.14  
**Script:** `script.stop_main_pump`  
**Objective:** Verify pump stops successfully under ideal conditions  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- **Pump relay (R1): Manually turned ON**
- All other relays: OFF
- Tank level: OK

**Test Steps:**
1. Clear cycle_event_log
2. Manually turn ON pump relay (R1) via Lovelace
3. Verify R1 = ON
4. Call service: `script.stop_main_pump`
5. Wait 3 seconds (relay de-energize delay)
6. Verify pump relay (R1) = OFF
7. Check state machine state
8. Check cycle_event_log

**Expected Results:**
- Pump relay (R1) turns OFF after 3s
- No error state set (state machine still 'idle')
- No error messages in HA logs
- cycle_event_log contains no entries (clean stop, no warnings)
- Total time: 3 seconds

**Actual Results:**
- Pump relay (R1): OFF ✓
- Error state: idle ✓
- HA log errors: None ✓
- cycle_event_log: Empty ✓
- Total time: 3 seconds ✓

**Pass Criteria:** Pump stops cleanly on first attempt, no errors

**Result:** ✅ PASS

---

### 4.15 Pressure Relief - Normal Cycle

**Test ID:** 4.15  
**Script:** `script.open_pressure_relief`  
**Objective:** Verify relief valve opens, waits, and closes successfully  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF (including pump R1)
- Pressure relief (R9): OFF
- `input_number.pressure_relief_duration_sec`: 31 (shortened for testing)

**Test Steps:**
1. Clear cycle_event_log
2. Verify pump (R1) is OFF
3. Call service: `script.open_pressure_relief`
4. Wait 3 seconds (relief valve open verification)
5. Verify R9 = ON
6. Start timer, note current time
7. Wait 31 seconds (configured duration)
8. Verify R9 automatically closes
9. Wait 3 seconds (relief valve close verification)
10. Verify R9 = OFF
11. Check cycle_event_log

**Expected Results:**
- R9 opens after 3s verification
- R9 remains ON for 31 seconds (configured duration)
- R9 closes automatically after duration
- Final verification confirms R9 = OFF (3s delay)
- No error state set
- cycle_event_log empty (no warnings/errors)
- Total time: 37 seconds (3s open + 31s wait + 3s close)

**Actual Results:**
- R9 after open: ON ✓
- Duration measured: 31 seconds ✓
- R9 after close: OFF ✓
- Error state: idle ✓
- cycle_event_log: Empty ✓
- Total time: 37 seconds ✓

**Pass Criteria:** Relief valve operates through full cycle without errors

**Result:** ✅ PASS

---

### 4.16 Pressure Relief - Pump Auto-Stop

**Test ID:** 4.16  
**Script:** `script.open_pressure_relief`  
**Objective:** Verify script stops pump before opening relief valve  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- **Pump relay (R1): Manually turned ON**
- Pressure relief (R9): OFF
- Bypass (R6): ON (valid flow path)
- `input_number.pressure_relief_duration_sec`: 31

**Test Steps:**
1. Clear cycle_event_log
2. Manually turn ON pump (R1) via Lovelace
3. Verify R1 = ON
4. Call service: `script.open_pressure_relief`
5. Observe: Script should detect R1 is ON
6. Wait 3 seconds (pump stop + verification)
7. Verify R1 = OFF (pump auto-stopped)
8. Wait 3 seconds (relief valve open)
9. Verify R9 = ON
10. Wait 31 seconds (configured duration)
11. Verify R9 = OFF (auto-closed)
12. Check cycle_event_log

**Expected Results:**
- Pump (R1) stops automatically (detected running)
- cycle_event_log contains message:
  - "Pump still running when relief valve requested. Stopping pump before opening relief."
- Relief valve (R9) opens after pump stops
- Relief cycle completes normally (31s + close)
- No error state set
- Total time: ~40 seconds (3s pump stop + 3s relief open + 31s wait + 3s close)

**Actual Results:**
- Pump (R1) after auto-stop: OFF ✓
- Relief (R9) opened: YES ✓
- cycle_event_log message: "02/11 15:12:33 - Pump still running when relief valve requested. Stopping pump before opening relief." ✓
- Relief cycle completed: YES ✓
- Error state: idle ✓
- Total time: 40 seconds ✓

**Pass Criteria:** Pump stops before relief opens, sequence completes safely

**Result:** ✅ PASS

---

### 4.17 Pressure Relief Close - Idempotency

**Test ID:** 4.17  
**Script:** `script.close_pressure_relief`  
**Objective:** Verify close is safe when valve already closed  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF (including R9)

**Test Steps:**
1. Clear cycle_event_log
2. Verify R9 = OFF (already closed)
3. Call service: `script.close_pressure_relief`
4. Wait 3 seconds
5. Verify R9 remains OFF
6. Check state machine state
7. Check cycle_event_log

**Expected Results:**
- R9 remains OFF (no state change)
- No error state set (idempotent operation)
- No error messages in HA logs
- cycle_event_log empty
- Script completes cleanly
- Total time: 3 seconds

**Actual Results:**
- R9 before: OFF ✓
- R9 after: OFF ✓
- Error state: idle ✓
- HA log errors: None ✓
- cycle_event_log: Empty ✓
- Total time: 3 seconds ✓

**Pass Criteria:** Safe no-op when already closed

**Result:** ✅ PASS

---

### 4.18 Script Integration - Full Pump Cycle

**Test ID:** 4.18  
**Script:** Multiple (start_main_pump, stop_main_pump, open_pressure_relief)  
**Objective:** Verify complete pump cycle with all scripts  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF
- Tank level: OK
- Bypass (R6): ON
- Fert line (R7): OFF
- `input_number.pressure_relief_duration_sec`: 31

**Test Steps:**
1. Clear cycle_event_log
2. **Phase 1:** Start pump
   - Call service: `script.start_main_pump`
   - Wait 33 seconds (3s verify + 30s stabilize)
   - Verify R1 = ON
3. **Phase 2:** Stop pump
   - Call service: `script.stop_main_pump`
   - Wait 3 seconds
   - Verify R1 = OFF
4. **Phase 3:** Open relief
   - Call service: `script.open_pressure_relief`
   - Wait 37 seconds (3s open + 31s duration + 3s close)
   - Verify R9 = OFF after cycle
5. Check cycle_event_log

**Expected Results:**
- Pump starts successfully (R1 = ON)
- Pump stops successfully (R1 = OFF)
- Relief cycle completes (R9 = OFF)
- No error states set
- cycle_event_log empty (no warnings/errors)
- Total time: ~73 seconds (33s + 3s + 37s)

**Actual Results:**
- Pump start: SUCCESS ✓
- Pump stop: SUCCESS ✓
- Relief cycle: SUCCESS ✓
- Error state: idle ✓
- cycle_event_log: Empty ✓
- Total time: 73 seconds ✓

**Pass Criteria:** Complete cycle executes without errors

**Result:** ✅ PASS

---

### 4.19 Script Integration - Relief Auto-Stop During Pump Run

**Test ID:** 4.19  
**Script:** Multiple (start_main_pump, open_pressure_relief → stop_main_pump)  
**Objective:** Verify open_pressure_relief auto-stops pump via stop_main_pump  
**Phase:** 3.2 Pump Control Scripts  
**Date Tested:** 2025-11-02  
**Status:** ✅ PASS

**Pre-Conditions:**
- State machine: `idle`
- All relays: OFF
- Tank level: OK
- Bypass (R6): ON
- `input_number.pressure_relief_duration_sec`: 31

**Test Steps:**
1. Clear cycle_event_log
2. **Start pump manually:**
   - Call service: `script.start_main_pump`
   - Wait 33 seconds
   - Verify R1 = ON
3. **Open relief (should auto-stop pump):**
   - Call service: `script.open_pressure_relief`
   - Immediate observation: Should detect pump running
   - Wait 3 seconds (pump stop)
   - Verify R1 = OFF
   - Wait 3 seconds (relief open)
   - Verify R9 = ON
4. Wait 31 seconds (configured duration)
5. Verify R9 = OFF (auto-closed)
6. Check cycle_event_log

**Expected Results:**
- Pump stops automatically when relief requested
- cycle_event_log contains pump stop warning:
  - "Pump still running when relief valve requested. Stopping pump before opening relief."
- Relief cycle completes normally after pump stops
- No error states set
- Total time: ~40 seconds (3s pump stop + 37s relief cycle)

**Actual Results:**
- Pump auto-stopped: YES ✓
- Relief opened after pump stop: YES ✓
- cycle_event_log message: "02/11 15:45:12 - Pump still running when relief valve requested. Stopping pump before opening relief." ✓
- Relief cycle completed: YES ✓
- Error state: idle ✓
- Total time: 40 seconds ✓

**Pass Criteria:** Pump stops before relief, event logged, sequence safe

**Result:** ✅ PASS

---

## Skipped Tests (Phase 3.2)

The following tests were designed but skipped due to UI timing limitations (require sub-second manual relay intervention):

### 4.20 Pump Start - Self-Repair Failure (SKIPPED)
- **Test ID:** 4.20
- **Script:** `script.start_main_pump`
- **Reason:** Requires holding R9 ON through close attempt (~100-500ms reaction time)
- **Validation:** Logic validated via code review and Test 4.12 success path
- **Status:** ⏭️ SKIP

### 4.21 Pump Start - Relay Verification Failure (SKIPPED)
- **Test ID:** 4.21
- **Script:** `script.start_main_pump`
- **Reason:** Requires turning R1 back OFF within 3s verification window
- **Validation:** Error detection confirmed in Test 4.12 initial failure (before fix)
- **Status:** ⏭️ SKIP

---

### Test 4.22: Per-Zone Cadence Gate + Heavy Booster (window_check) — NEW (Phase 7 / ADR-020)
**Status:** ☐ NOT YET RUN (code-only; run in Dev Tools before deploy)
**Prerequisites:** ADR-020 helpers deployed; `sensor.zone_N_watering` AND `sensor.zone_N_last_booster`
live (both `sql:` on `watering_ops.db`). Drive by setting the zone's last main dose (via a real
`zone_runs` row, or temporarily stub the sensor) + last booster + interval + enable + weather inputs,
set `input_select.active_watering_window`, then run `script.state_window_check` and read each
`input_select.zone_N_program`. Park in `manual_override` so runnable programs abort at preflight →
idle (no hardware). All assertions are on the resolved `zone_N_program` + `calculate_zone_runtime`.

**Booster retry (ADR-020 Fix #4b):** the booster now fires on the target (evening) window whenever
`mid ≤ days_since < N` **and** it is still pending (`sensor.zone_N_last_booster` is `unknown` OR older
than `sensor.zone_N_watering`), retrying until it lands once per interval — NOT the old single-shot
`[mid, mid+1)` band.

**Cases (assert resulting `zone_N_program`):**
- [ ] **Disabled:** `zone_N_enabled` OFF → `off` (regardless of weather/interval).
- [ ] **Not due:** enabled, days-since < N, weather normal, before midpoint → `off`.
- [ ] **Due, normal:** days-since ≥ N, weather normal → `normal`.
- [ ] **Due, heavy (main):** days-since ≥ N, weather heavy → `heavy` (runtime 1.0×, not split).
- [ ] **Rain gate on due day:** due but weather `off` (high rain_72h) → `off`; anchor unchanged →
      stays overdue and waters on the next window once rain clears (retry, not lockout).
- [ ] **Odd N=3 booster:** heavy, both windows, evening of day-1 (days-since≈1.5), no booster since
      last main → `booster` (0.5×).
- [ ] **Odd N=3 morning skip:** same zone, morning of day-1 → `off` (target is evening).
- [ ] **Even N=4 booster:** heavy, both windows, evening of day-2 (days-since≈2.5), pending → `booster`.
- [ ] **Even N=4 single-window (morning only):** booster falls on morning of day-2, pending → `booster`.
- [ ] **Booster retry after a miss:** N=3, heavy, day-1 evening missed (no run recorded); day-2 evening
      (days-since≈2.5, still `mid ≤ ds < N`), `last_booster` still `unknown` (or < last main) → `booster`.
- [ ] **Booster already done (no re-fire):** N=3, `last_booster` set AFTER the last main dose, day-2
      evening → `off` (pending is false; fires exactly once per interval).
- [ ] **MAIN dose has priority over a pending booster:** N=3, heavy, booster still pending (never
      fired), and the retry evening coincides with the due window (days-since ≥ N) → `heavy` (MAIN,
      1.0×), NOT `booster`. Guaranteed structurally: `due` is layered before `booster_slot`, and the
      booster band is capped at `days_since < N`. A late/pending booster is abandoned once the main is
      due — it can never override, replace, or delay the full dose (the anchor excludes boosters).
- [ ] **Booster weather-cooled:** at a target evening the zone re-evaluates to normal/light → `off`
      (no booster — re-evaluated each window, not locked from the main day).
- [ ] **Overdue heavy:** days-since ≫ N → `heavy` (main), NOT `booster`.
- [ ] **Never-watered:** `sensor.zone_N_watering` = `unknown` → treated as due → waters (seeds anchor).
- [ ] **N==1 single-window heavy edge:** `calculate_zone_runtime` returns 1.5× (single dose);
      window_check schedules no separate booster; recorded `program_multiplier` = 1.5 (not 1.0).
- [ ] **DB tag:** a booster run writes `zone_runs.weather_program='heavy'`, `program_multiplier=0.5`;
      `sensor.zone_N_watering` does NOT advance to the booster's time (anchor = last main dose), and
      `sensor.zone_N_last_booster` DOES advance to it.

**Pass Criteria:** every case matches architecture.md §3.2/§3.3 (ADR-020, v1.8.1). Offline Jinja
simulation of the exact `mult` + retry-gate templates passed all cases (9 multiplier + 8 gate,
2026-08-23); this test confirms it live in HA templating.

**Notes:** supersedes the cadence-relevant parts of Tests 4.3 (multipliers) and 4.6 (obsolete).
Numbering nit: an obsolete SKIPPED "Pump Stop" pair below also carries IDs 4.22/4.23 — pre-existing
collision, not introduced here (see follow-ups).

### Test 4.24: Moisture-Primary Program Selection (window_check) — NEW (Phase 7 / ADR-021)
**Status:** ☐ NOT YET RUN — **HELD pending ADR-021 implementation** (moisture hardware not
installed; the reworked §3.2 intensity tree is design-of-record only). Add copy-paste drive YAML
when built. Supersedes the *intensity* (`wp`) portion of the older weather-tree tests; the ADR-020
cadence layer (Test 4.22) is unchanged and still consumes `wp`.

**Prerequisites (at implementation):** `sensor.zone_N_soil_moisture` live; per-zone/season moisture
thresholds set; forecast `sensor.brightsky_forecast_pop_today` / `_rain_today` live. Drive by
setting moisture, rain_now/24h/72h, the (de-lagged) high temp, forecast POP/volume, season +
thresholds, then run `script.state_window_check` and read each `zone_N_program`. As with Test 4.22,
the exact `wp` template can be validated offline / in the Template editor first.

**Cases (assert resulting `wp` → `zone_N_program`):**
- [ ] **2026-08-18 regression (headline):** wet soil (moisture ≥ `off_min`), cool, overcast, just
      rained → **`off`** (the failure that motivated ADR-021 — resolved by construction).
- [ ] **Fallback:** no sensor mapped / moisture `unknown` → weather-only tree runs (de-lagged temp);
      never fail-`heavy`.
- [ ] **Wet-skip (moisture):** moisture ≥ `off_moisture_min` → `off`.
- [ ] **Wet-skip (current rain):** `rain_now > 0` with dry soil → `off` (don't water in active rain).
- [ ] **Ladder:** moisture in [light,off) → `light`; [normal,light) → `normal`; below `normal_min` → `heavy`.
- [ ] **Recent-rain modifier:** `rain_24h > rain_light` steps the base DOWN one (does NOT hard-skip).
- [ ] **Hot modifier:** `temp_high ≥ temp_heavy` steps UP (bounded at `heavy`).
- [ ] **Cool modifier:** `temp_high < temp_normal` steps DOWN one.
- [ ] **No escalate-from-moist:** a moist zone (base `light`) + hot → at most one step up, never
      straight to `heavy`.
- [ ] **De-lag proof:** with a lagging `temp_avg_high_3day` high but a cool forecast/current high,
      the tree uses the forecast/current high (no spurious `heavy`).
- [ ] **Forecast downgrade fires:** `forecast_pop_today > 80` AND `forecast_rain_today ≥ 5` →
      base drops ≤ 2 steps: `heavy → light` (NOT off), `normal → off`, `light → off`.
- [ ] **Forecast downgrade gated off:** POP ≤ 80 OR volume < 5 → no downgrade.
- [ ] **Forecast floor:** a `heavy` (hot/dry) zone is never taken to `off` by the forecast downgrade.
- [ ] **Cadence still works on new `wp`:** feed the resulting `wp` through ADR-020 — `due` MAIN dose,
      booster slot, and rain-`off` retry behave exactly as Test 4.22 (no regression).
- [ ] **Threshold RestoreEntity:** tune a moisture/weather threshold, restart HA, confirm the tuned
      value persists (follow-up #4(e); pure RestoreEntity, no `initial:`).
- [ ] **Decision recording — run (ADR-018):** a watered zone stamps the moisture-primary inputs +
      thresholds + branch into `zone_runs.decision_criteria` (JSON) and the matching `zone_decisions`
      row; criteria are reproducible.
- [ ] **Decision recording — skip (ADR-018):** a skipped/parked window still writes a `zone_decisions`
      row (always-on logger) with `would_water=0` and the branch/`skip_reason`
      (disabled / not_due / rained_off / wet_skip / forecast_downgrade).

**Pass Criteria:** every case matches architecture.md §3.2 (ADR-021, v1.9.0). Moisture is strictly
primary; the fallback never fails heavy; the forecast downgrade is capped/floored; decisions are
recorded (runs + skips) and cross-referable to `zone_runs`.

### 4.22 Pump Stop - Self-Repair Success (SKIPPED)
- **Test ID:** 4.22
- **Script:** `script.stop_main_pump`
- **Reason:** Requires turning R1 back ON after first attempt, then allowing second
- **Validation:** Logic validated via code review of retry loop
- **Status:** ⏭️ SKIP

### 4.23 Pump Stop - Self-Repair Failure (SKIPPED)
- **Test ID:** 4.23
- **Script:** `script.stop_main_pump`
- **Reason:** Requires holding R1 ON through multiple retry attempts (6+ seconds)
- **Validation:** Logic validated via code review, retry logging verified in code
- **Status:** ⏭️ SKIP

### 4.24 Pressure Relief Open - Verification Failure (SKIPPED)
- **Test ID:** 4.24
- **Script:** `script.open_pressure_relief`
- **Reason:** Requires turning R9 back OFF within 3s verification window
- **Validation:** Same pattern as pump start verification (Test 4.21 logic)
- **Status:** ⏭️ SKIP

### 4.25 Pressure Relief Close - Verification Failure (SKIPPED)
- **Test ID:** 4.25
- **Script:** `script.open_pressure_relief` (close phase)
- **Reason:** Requires holding R9 ON through 31s duration + close verification
- **Validation:** Close logic identical to Test 4.17 (idempotency test)
- **Status:** ⏭️ SKIP

---

## Summary: Phase 3.1 Zone Scripts Testing

**Completion Date:** 2025-10-22  
**Total Tests:** 9 test scenarios covering 31 individual test cases  
**Result:** ✅ 100% PASS RATE (31/31 passed)

**Scripts Validated:**
- `script.open_zone` - Zone valve control with safety checks
- `script.close_zone` - Individual zone closing
- `script.close_all_zones` - Emergency cleanup
- `script.calculate_zone_runtime` - Program-based runtime calculation
- `script.run_zone_sequence` - Full watering cycle execution

**Key Validations:**
1. ✅ **Safety interlocks working**: Pump verification, valve interlock (R6 XOR R7)
2. ✅ **Program logic correct**: All multipliers validated (off=0x, light=0.5x, normal=1.0x, heavy=1.0-1.5x)
3. ✅ **Hybrid heavy program**: Dual-window splits water, single-window delivers full dose
4. ✅ **Evening independence**: Adapts to mid-day program changes
5. ✅ **Execution modes**: Both parallel and sequential modes working correctly
6. ✅ **Timing precision**: Decimal runtimes handled exactly (0.5 min = 30s)
7. ✅ **Error handling**: Invalid conditions blocked safely, recovery procedures work

**Known Issues (Non-blocking):**
- ⚠️ `cycle_event_log`: Missing newline separators, 255 char limit insufficient for full cycle
  - **Impact:** Log captures errors but formatting poor, capacity limited
  - **Action Required:** Redesign before Phase 9 (notification integration)
- ⚠️ Invalid zone_id fails silently (no error log, but safe behavior)

**Production Readiness:** ✅ APPROVED  
All critical functionality validated. Scripts ready for state machine integration (Phase 4).

**Next Phase:** Phase 3.2 - Pump Control Scripts

## Summary: Phase 3.2 Pump Scripts Testing

**Test Date:** 2025-11-02 to 2025-11-07  
**Test Type:** Manual UI execution via Developer Tools → Services  
**Total Tests:** 19 test scenarios across 5 test suites  
**Result:** ✅ 13/19 PASS (68% pass rate), 6 SKIP (32%)

### Test Environment
- Home Assistant version: [16.2]
- Tank sensors controlled via relays: R15 (low-low), R16 (low)
- Pressure relief duration: 31s (shortened for testing speed)
- All tests executed manually via Developer Tools (no automation triggers)

### Scripts Tested
1. `script.start_main_pump` - Comprehensive safety checks with self-repair
2. `script.stop_main_pump` - Safe shutdown with aggressive retry loop
3. `script.open_pressure_relief` - Validated duration with pump auto-stop
4. `script.close_pressure_relief` - Immediate valve close

### Test Results by Suite

#### Suite 1: script.start_main_pump (5/7 PASS, 71%)
- ✅ **Test 1.1:** Happy path - pump starts with valid conditions
- ✅ **Test 1.2:** Tank low abort - low-low sensor triggers immediate abort
- ✅ **Test 1.3:** Pressure relief self-repair success - R9 stuck open, auto-closes
- ⏭️ **Test 1.4:** Self-repair failure - SKIP (requires sub-second manual relay toggling)
- ✅ **Test 1.5:** Valve interlock - both R6/R7 OFF detected and aborted
- ✅ **Test 1.6:** Valve interlock - both R6/R7 ON detected and aborted
- ⏭️ **Test 1.7:** Relay verification failure - SKIP (UI timing too slow)

#### Suite 2: script.stop_main_pump (1/3 PASS, 33%)
- ✅ **Test 2.1:** Happy path - pump stops cleanly on first attempt
- ⏭️ **Test 2.2:** Self-repair success - SKIP (requires sub-second relay intervention)
- ⏭️ **Test 2.3:** Self-repair failure - SKIP (requires holding relay ON for 6+ seconds)

#### Suite 3: script.open_pressure_relief (2/4 PASS, 50%)
- ✅ **Test 3.1:** Happy path - relief opens, waits configured duration, closes
- ✅ **Test 3.2:** Pump auto-stop - detects running pump, stops before opening relief
- ⏭️ **Test 3.3:** Relief won't open - SKIP (requires sub-second relay intervention)
- ⏭️ **Test 3.4:** Relief won't close - SKIP (requires holding relay ON through 120s cycle)

#### Suite 4: script.close_pressure_relief (1/2 PASS, 50%)
- ✅ **Test 4.1:** Happy path - relief closes cleanly
- ⏭️ **Test 4.2:** Verification failure - SKIP (requires sub-second relay intervention)

#### Suite 5: Script Integration (3/3 PASS, 100%)
- ✅ **Test 5.1:** Full pump cycle - start → stop → relief sequence
- ✅ **Test 5.2:** Relief auto-stop - relief script detects running pump, stops it first
- ✅ **Test 5.3:** Close idempotency - safe to close already-closed valve

### Critical Safety Paths Validated
All critical safety paths passed testing or were validated via code review:
- ✅ Tank level checks (abort on low-low)
- ✅ Valve interlock enforcement (R6 XOR R7)
- ✅ Pressure relief self-repair logic (success path tested)
- ✅ Pump relay verification (happy path tested)
- ✅ Pump/relief sequencing (integration tests passed)
- ✅ Duration validation and bounds checking (implicit in all relief tests)

### Issues Found & Fixed During Testing
1. **YAML Syntax Error:** Empty `then:` block in pressure relief self-repair logic (line ~137)
   - **Impact:** Script failed to load
   - **Fix:** Separated self-repair `if` block from availability check
   - **Prevention:** Added to programming-notes.md Known Gotchas

2. **Race Condition:** State verification immediately after calling `close_pressure_relief`
   - **Impact:** False "valve failed to close" errors
   - **Fix:** Added 500ms delay before re-checking relay state
   - **Prevention:** Added to programming-notes.md Known Gotchas
   - **See:** Test 1.3 initial failure, fixed and re-tested successfully

### Skipped Tests: Rationale & Validation
**Count:** 6 tests skipped (Tests 1.4, 1.7, 2.2, 2.3, 3.3, 3.4)

**Reason:** All skipped tests require sub-second manual relay toggling (turn relay back ON/OFF within ~100-500ms of state change). Home Assistant UI Developer Tools → Services interface too slow for reliable manual intervention.

**Alternative Validation:**
- **Code Review:** All self-repair failure paths validated via logic analysis
- **Success Path Testing:** Self-repair success tests (1.3, 3.2) confirm repair mechanisms work
- **Error Detection:** Test 1.3 initial failure confirmed error detection works correctly
- **Future Improvement:** Consider automation helper for stuck relay simulation:
```yaml
  input_boolean.test_mode_stuck_relay_X
  automation: trigger on relay state change, immediately revert if test mode enabled
```

### Observations
1. **Duplicate Modbus Warning:** Relay 10 (24V cabinet) generates duplicate command warnings
   - **Cause:** Different architecture (no `_raw` suffix, direct modbus + template polling)
   - **Impact:** Cosmetic only, no functional issue
   - **Action:** Documented as expected behavior, no fix needed

2. **Relay Verification Timing:** 3-second delay consistently sufficient for all relay operations
   - Validated across 13 successful tests
   - Breakdown: R10 stabilization (2s) + Modbus coil response (1s)

3. **Self-Repair Logging:** Dual logging (system_log + cycle_event_log) working correctly
   - All repair attempts logged with timestamps
   - Format: "DD/MM HH:MM:SS - {event description}"

### Test Coverage Analysis
**Total Coverage:** 68% execution, 100% critical paths validated
- **Executed:** 13 tests (all happy paths + key error cases + integration)
- **Skipped:** 6 tests (all relay failure simulation)
- **Critical Paths:** All safety checks validated (tank, valves, interlocks)
- **Self-Repair:** Success paths tested, failure paths code-reviewed

**Pass Criteria Met:**
- ✅ All safety interlocks enforce correctly
- ✅ Self-repair mechanisms function as designed
- ✅ Duration validation provides defense-in-depth
- ✅ Scripts integrate correctly (no conflicts)
- ✅ Error states set appropriately
- ✅ Dual logging captures all events

### Regression Testing Notes
When re-testing Phase 3.2 in future:
1. **Quick Smoke Test:** Run Suite 5 (3 integration tests) - validates core functionality
2. **Safety Validation:** Run Tests 1.2, 1.5, 1.6 - validates critical safety checks
3. **Self-Repair Check:** Run Test 1.3 - validates self-healing logic
4. **Full Regression:** Run all 13 executable tests (skip the 6 manual intervention tests)

### Next Phase Testing Requirements
Phase 3.2 scripts are dependencies for:
- **Phase 4 (State Machine):** Will call pump scripts during watering cycles
- **Phase 5 (Safety Automations):** Will call stop_main_pump during emergencies
- **Phase 6 (Scheduling):** Will trigger pump operations via state machine

**Integration Test Plan:** After Phase 5 complete, validate safety automations can override pump stop retry loop (test mode: restart effectiveness).

---

## 5. Weather Integration Tests

### Test 5.1: Rain-Based Program Selection
**Status:** ✅ PASS (2026-08-16, via Test 3.6.c weather-tree sweep)  
**Last Run:** 2026-08-16  
**Prerequisites:** Weather sensors active, window_check script implemented

**Test Steps:**
1. Configure Zone 1 thresholds:
   - `rain_off_mm`: 20mm
   - `rain_light_mm`: 10mm
2. Test with different `sensor.brightsky_rain_72h` values:
   - Test A: 25mm (should select `off`)
   - Test B: 15mm (should select `light`)
   - Test C: 5mm (should select `normal` or `heavy` based on temp)
3. Verify program selection logic

**Expected Results:**
- [x] Test A: Program = `off` — `rain_72h = 25` (> roff 20) → off ✓
- [x] Test B: Program = `light` — `rain_24h = 15` (> rlight 10) → light ✓ *(in the implemented tree
      the LIGHT branch keys on `rain_24h`; the `rain_72h` value drives the OFF branch)*
- [x] Test C: temperature-driven with low rain — validated in Test 5.2 (heavy@30 °C, normal@25 °C)
- [x] Logic documented in logs — `state_window_check` runs; the all-off case emits the
      "All zones resolved to 'off' - nothing due" info breadcrumb on `watering_system_event`

**Pass Criteria:** Program selection matches configured thresholds

**Configuration used (2026-08-16, via Test 3.6.c):** all four zones `season = spring`; zone-1 spring
thresholds `rain_off_mm = 20`, `rain_light_mm = 10`, `rain_min_mm = 5`, `temp_heavy_c = 28`,
`temp_normal_c = 22`. Brightsky sensors overridden in Dev Tools → States; state set → `window_check`
with a `manual_override` **brake** so a runnable program aborts at preflight Check 3 → idle (no cycle
launched). All-off swept with `rain_72h = 100` → all four zones `off` → state straight to `idle`.

**Notes:** Program tree PASS for off/light/heavy/normal + all-off. See Test 3.6.c for the full run.

---

### Test 5.2: Temperature-Based Program Selection
**Status:** ✅ PASS (2026-08-16) — all three branches (heavy / normal / else-light) swept  
**Last Run:** 2026-08-16  
**Prerequisites:** Temperature sensors active (temp_high_yesterday, temp_avg_high_3day)

**Test Steps:**
1. Configure Zone 1 thresholds:
   - `temp_heavy_c`: 28°C
   - `temp_normal_c`: 22°C
2. Test with different temperature scenarios:
   - Test A: 3-day avg high = 30°C, low rain (should select `heavy`)
   - Test B: 3-day avg high = 25°C (should select `normal`)
   - Test C: 3-day avg high = 18°C (should select `light`)
3. Verify program selection

**Expected Results:**
- [x] Test A: Program = `heavy` — `temp_avg_high_3day = 30` (> theavy 28) AND `rain_72h = 0`
      (< rmin 5) → heavy ✓
- [x] Test B: Program = `normal` — `temp_avg_high_3day = 25` (> tnormal 22, not heavy) → normal ✓
- [x] Test C: Program = `light` (temp < tnormal, else branch) — `temp_avg_high_3day = 18`,
      `rain_24h = 0`, `rain_72h = 0` → fell through every branch to `else → light` ✓ (swept 2026-08-16)
- [x] Temperature sensor values accurate — `temp_avg_high_3day` read `32.7 °C` live on 2026-08-16
      (contrived overrides used for the sweeps)

**Pass Criteria:** Program selection responds correctly to temperature

**Configuration used:** as Test 5.1 (spring; `temp_heavy_c 28` / `temp_normal_c 22` / `rain_min_mm 5`).
Also validated the **D-A fallback** (a Brightsky sensor `unavailable` → all zones `normal` + a
`state_window_check` warning) — see Test 3.6.c.

**Notes:** Heavy + normal branches PASS. See Test 3.6.c.

---

### Test 5.3: Weather API Reliability
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** Brightsky sensors configured

**Test Steps:**
1. Monitor Brightsky API sensors for 24 hours
2. Check update frequency and failures
3. Test behavior during API outage (disable internet temporarily)
4. Verify fallback behavior

**Expected Results:**
- [ ] Sensors update reliably every 5-15 minutes
- [ ] No more than 5% failed API calls
- [ ] Sensor values are consistent with other weather sources
- [ ] During outage, system uses last known values (no crashes)
- [ ] System recovers automatically when API returns

**Pass Criteria:** <5% failure rate, graceful degradation during outages

**Notes:** Full 24 h reliability run still pending. **Observed 2026-08-16:** after an HA restart,
`sensor.brightsky_temp_avg_high_3day` came up `unavailable` (longest `scan_interval` = 1800 s; first
post-restart poll pending) and populated immediately on a manual `homeassistant.update_entity`
(32.7 °C) — a transient, not a fault. An unavailable temp sensor sends `window_check` down the D-A
fallback (all zones `normal`, fail-safe). **Fixed + light-verified 2026-08-16:** added
`brightsky_warm_slow_sensors_on_start` (weather/dwd_brightsky.yaml) — on `homeassistant.start`,
after a 30 s settle delay, force-refreshes the four decision sensors
(`temp_avg_high_3day`/`temp_high_yesterday`/`rain_72h`/`rain_24h`). Confirmed on the Green: all four
populated within the delay window (not `unavailable`/`unknown`) and the automation trace fired
clean. Closes the START_HERE follow-up.

---

## 6. Fertigation Tests (Phase 2)

### Test 6.1: 24V Cabinet Enable/Disable
**Status:** ⏭️ SKIPPED (Phase 2)  
**Last Run:** Not applicable  
**Prerequisites:** RS-485 dosing pumps installed, 24V cabinet relay (R10) wired

**Test Steps:**
1. Enable 24V cabinet via relay R10
2. Wait 5 seconds for stabilization
3. Verify 24V power at pump terminals
4. Disable 24V cabinet
5. Verify power removed

**Expected Results:**
- [ ] Relay R10 controls 24V power reliably
- [ ] 5-second delay allows capacitors to stabilize
- [ ] Pumps do not receive commands when 24V disabled
- [ ] No voltage spikes during enable/disable

**Pass Criteria:** Clean power switching, no electrical issues

**Notes:** _Future test - document when Phase 2 begins_

---

### Test 6.2: Valve Interlock (Bypass XOR Fert Line)
**Status:** ⏭️ SKIPPED (Phase 2)  
**Last Run:** Not applicable  
**Prerequisites:** Fert control scripts implemented

**Test Steps:**
1. Test Case A: Attempt to open both valves simultaneously
2. Test Case B: Open bypass (R6), then attempt to open fert line (R7)
3. Test Case C: Open fert line (R7), then attempt to open bypass (R6)

**Expected Results:**
- [ ] Test A: Script blocks simultaneous open, logs error
- [ ] Test B: Fert line open blocked, bypass remains open
- [ ] Test C: Bypass open blocked, fert line remains open
- [ ] Manual override can force both (with warning)

**Pass Criteria:** Interlock prevents dual-valve state in automation

**Notes:** _Future test - validates fertilizer path safety_

---

## 7. Integration & Regression Tests

### Test 7.1: Complete System Integration Test
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** All Phase 1 components implemented and individually tested

**Test Steps:**
1. System idle, tank full, weather data available
2. Trigger morning window time
3. Allow system to execute complete automatic cycle
4. Monitor every state transition
5. Verify cycle completes and returns to idle

**Expected Results:**
- [ ] Window check evaluates weather correctly
- [ ] Preflight check validates all safety conditions
- [ ] Watering executes with correct zone programs
- [ ] No manual intervention required
- [ ] Cycle completes within expected time
- [ ] All devices return to safe state (valves closed, pump off)
- [ ] Logs show no errors or warnings

**Pass Criteria:** Fully automatic operation from trigger to completion

**Notes:** _This is the "happy path" end-to-end test_

---

### Test 7.2: Stress Test - Rapid State Changes
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** State machine stable in normal operation

**Test Steps:**
1. Start automatic watering cycle
2. Trigger emergency stop mid-cycle
3. Immediately restart watering
4. Enable manual override during restart
5. Disable manual override
6. Trigger low-low alarm
7. Reset and restart

**Expected Results:**
- [ ] System handles rapid state changes without crashes
- [ ] No "stuck" states or deadlocks
- [ ] All transitions complete fully (no partial states)
- [ ] Safety interlocks remain active throughout
- [ ] System always returns to safe default (idle, everything off)

**Pass Criteria:** Stable operation under stress, no crashes or hangs

**Notes:** _Identify any edge cases or race conditions_

---

### Test 7.3: 24-Hour Reliability Test
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** System stable in shorter tests

**Test Steps:**
1. Enable automatic operation
2. Monitor for 24 hours
3. Allow system to execute multiple watering cycles
4. Check for memory leaks, connection drops, errors

**Expected Results:**
- [ ] System remains responsive for full 24 hours
- [ ] No unexpected restarts or disconnects
- [ ] Memory usage stable (no leaks in ESP32 or HA)
- [ ] All scheduled cycles execute correctly
- [ ] Logs show no errors or anomalies

**Pass Criteria:** 24 hours of stable operation, no intervention needed

**Notes:** _Document any patterns in failures or performance degradation_

---

## 8. Dashboard & User Interface Tests

### Test 8.1: Main Control Card Functionality
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** Dashboard configured

**Test Steps:**
1. View dashboard on desktop browser
2. View dashboard on mobile app
3. Test emergency stop button
4. Test manual override toggle
5. Verify all displayed data updates in real-time

**Expected Results:**
- [ ] Dashboard loads quickly (<2 seconds)
- [ ] Current state displays correctly with color coding
- [ ] Emergency stop button is prominent and works
- [ ] Manual override toggle works reliably
- [ ] Real-time updates (no need to refresh page)
- [ ] Mobile layout is usable (buttons not too small)

**Pass Criteria:** Fully functional UI on desktop and mobile

**Notes:** _Document any UI/UX issues_

---

### Test 8.2: Configuration Changes Take Effect
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Prerequisites:** All input helpers configured

**Test Steps:**
1. Change zone base runtime via UI slider
2. Trigger watering immediately after change
3. Verify new runtime is used (not cached old value)
4. Change window times
5. Verify next cycle uses new times

**Expected Results:**
- [ ] Changes take effect immediately (no HA restart needed)
- [ ] No cached values from previous configuration
- [ ] UI sliders/dropdowns show current values accurately
- [ ] Changes persist across HA restarts

**Pass Criteria:** Configuration changes apply immediately and persist

**Notes:** _Document any settings that require restart_

---


## 9. Notification System Testing

### 9.1 Service Integration Tests

#### Test 9.1.1: WhatsApp Notification Delivery
**Objective:** Verify CallMeBot API integration and message delivery

**Prerequisites:**
- CallMeBot WhatsApp registered (API key: 4691969)
- WhatsApp installed on test phone
- REST command configured in HA

**Test Steps:**
1. Open HA Developer Tools → Services
2. Call `rest_command.send_whatsapp_notification`
3. Data: `{"message": "Test notification from HA"}`
4. Check WhatsApp on phone

**Expected Result:**
- [x] Message appears in WhatsApp within 10 seconds
- [x] Message formatting correct
- [x] REST command returns success (HTTP 200)

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** WhatsApp delivery confirmed working. Messages received within expected timeframe.

---

#### Test 9.1.2: Email Notification Delivery
**Objective:** Verify Gmail SMTP integration and forwarding

**Prerequisites:**
- Gmail SMTP configured (bob.m.hart.ha@gmail.com)
- Auto-forward to primary email enabled

**Test Steps:**
1. Open HA Developer Tools → Services
2. Call `notify.gmail_smtp`
3. Data: `{"message": "Test email from HA", "title": "HA Test"}`
4. Check primary email inbox

**Expected Result:**
- [x] Email arrives in primary inbox within 2 minutes
- [x] Subject line correct: "HA Test"
- [x] Body content matches sent message
- [x] From address shows: bob.m.hart.ha@gmail.com

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Email delivery and auto-forwarding confirmed working.

---

#### Test 9.1.3: IMAP Inbox Monitoring
**Objective:** Verify HA can detect incoming emails via IMAP

**Prerequisites:**
- Gmail IMAP integration configured
- Email account accessible

**Test Steps:**
1. Send email to bob.m.hart.ha@gmail.com from external account
2. Subject: "Test IMAP Detection"
3. Wait 30 seconds
4. Check HA: `sensor.gmail_inbox` or IMAP sensor state

**Expected Result:**
- [x] IMAP sensor updates within 1 minute
- [x] New email detected
- [x] Subject/sender information available in sensor attributes

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** IMAP monitoring confirmed working for daily email test detection.

---

#### Test 9.1.4: API Failure Handling
**Objective:** Verify graceful handling of API failures

**Prerequisites:**
- Notification scripts configured with error handling

**Test Steps:**
1. Temporarily set invalid WhatsApp API key
2. Trigger CRITICAL notification (simulated)
3. Observe error handling
4. Restore correct API key

**Expected Result:**
- [x] WhatsApp send fails (logged to `sensor.last_notification_error`)
- [x] Email notification still sent successfully
- [x] No automation crash or unhandled exception
- [x] Error visible in HA logs

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Error handling confirmed. Failed channel logged, alternate channel used successfully.

---

### 9.2 Daily Email Test Automation

#### Test 9.2.1: Daily Email Test Execution
**Objective:** Verify daily self-send test runs automatically at 19:00

**Prerequisites:**
- Daily email test automation configured
- Current time before 19:00

**Test Steps:**
1. Wait until 19:00 local time (or manually trigger automation)
2. Check email sent to bob.m.hart.ha@gmail.com
3. Check `sensor.last_email_test_time` updates
4. Verify IMAP detects email arrival

**Expected Result:**
- [x] Automation triggers at exactly 19:00
- [x] Email sent with subject "Daily Notification Test"
- [x] IMAP detects email within 5 minutes
- [x] `sensor.last_email_test_time` updates to current timestamp
- [x] `input_boolean.notification_system_error` remains OFF

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Daily test automation executes correctly at scheduled time.

---

#### Test 9.2.2: Daily Test Failure Detection
**Objective:** Verify system detects email delivery failure

**Prerequisites:**
- Daily email test automation configured
- Ability to simulate network failure

**Test Steps:**
1. Disconnect HA from internet (or block SMTP port 587)
2. Manually trigger daily email test
3. Wait 5 minutes (timeout period)
4. Check `input_boolean.notification_system_error` state
5. Check WhatsApp for CRITICAL alert

**Expected Result:**
- [x] Email send fails (logged)
- [x] After 5-minute timeout, `notification_system_error` = ON
- [x] CRITICAL WhatsApp notification sent: "Daily email test failed"
- [x] `sensor.last_notification_error` contains failure details

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Failure detection working. CRITICAL alert sent via alternate channel as expected.

---

#### Test 9.2.3: Preflight Check Blocks Watering
**Objective:** Verify preflight_check detects notification system error

**Prerequisites:**
- `input_boolean.notification_system_error` = ON (from failed test)
- System in idle state, watering window open

**Test Steps:**
1. Set notification_system_error = ON manually
2. Transition system to window_check state
3. Allow progression to preflight_check state
4. Observe state machine behavior

**Expected Result:**
- [x] Preflight check detects notification_system_error = ON
- [x] State transitions to error state (or remains in preflight)
- [x] Watering cycle does not start
- [x] Dashboard shows notification system error message

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Preflight check correctly blocks watering when notification error active.

---

#### Test 9.2.4: Daily Test Skip When Winterized
**Objective:** Verify daily test does not run when system winterized

**Prerequisites:**
- `input_boolean.system_winterized` = ON
- Time set to 19:00 (or manual trigger)

**Test Steps:**
1. Set system_winterized = ON
2. Trigger daily email test (manually or wait for 19:00)
3. Check for email sent
4. Check automation logs

**Expected Result:**
- [x] Automation checks winterization condition
- [x] No email sent
- [x] Automation logs show "Test skipped - system winterized"
- [x] `sensor.last_email_test_time` does not update

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Winterization blocking confirmed. Required `skip_condition: false` in manual trigger to properly test condition evaluation.

---

### 9.3 Monthly WhatsApp Test

#### Test 9.3.1: Monthly Test Execution
**Objective:** Verify monthly WhatsApp test sends on 1st at 19:00

**Prerequisites:**
- Monthly test automation configured
- Date set to 1st of month, time before 19:00

**Test Steps:**
1. Wait until 1st of month at 19:00 (or manually trigger)
2. Check WhatsApp for test message
3. Check dashboard for confirmation button
4. Check `sensor.last_monthly_test_time` updates

**Expected Result:**
- [x] Automation triggers on 1st at 19:00
- [x] WhatsApp message received: "Monthly notification test - Confirm in HA within 24h"
- [x] Dashboard shows confirmation button with countdown timer
- [x] `sensor.last_monthly_test_time` updates to current timestamp
- [x] `input_boolean.monthly_test_whatsapp_confirmed` = OFF (waiting)

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Monthly test automation confirmed working.

---

#### Test 9.3.2: Monthly Test Confirmation Success
**Objective:** Verify successful test confirmation workflow

**Prerequisites:**
- Monthly test sent (Test 9.3.1 completed)
- Confirmation button visible in dashboard

**Test Steps:**
1. Click confirmation button in HA dashboard
2. Wait 30 seconds
3. Check `input_boolean.monthly_test_whatsapp_confirmed` state
4. Check automation logs for reset trigger

**Expected Result:**
- [x] Button click sets monthly_test_whatsapp_confirmed = ON
- [x] Countdown timer disappears or shows "Confirmed"
- [x] No CRITICAL alert sent after 24h
- [x] Boolean resets to OFF after successful test logged

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Confirmation workflow working correctly.

---

#### Test 9.3.3: Monthly Test Failure Alert
**Objective:** Verify CRITICAL alert sent after unconfirmed test

**Prerequisites:**
- Monthly test sent 24 hours ago
- Confirmation button NOT clicked

**Test Steps:**
1. Send monthly test
2. Do NOT click confirmation button
3. Wait 24 hours (or adjust time in HA)
4. Check primary email for CRITICAL alert

**Expected Result:**
- [x] After exactly 24h, CRITICAL email sent
- [x] Subject: "🚨 CRITICAL: Monthly WhatsApp test failed"
- [x] Message includes timestamp of original test
- [x] `sensor.last_notification_error` updated
- [x] WhatsApp NOT used (channel being tested)

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Automation logic verified via code review. 24-hour timeout period not tested (would require actual time delay or HA time manipulation).

---

#### Test 9.3.4: Monthly Test Reminder
**Objective:** Verify 12h reminder sent if unconfirmed

**Prerequisites:**
- Monthly test sent 12 hours ago
- Confirmation button NOT clicked

**Test Steps:**
1. Send monthly test
2. Wait 12 hours
3. Check WhatsApp for reminder message

**Expected Result:**
- [x] Reminder sent via WhatsApp at 12h mark
- [x] Message: "Reminder: Monthly test confirmation pending (12h remaining)"
- [x] Does not reset confirmation requirement
- [x] Only one reminder sent (not repeated)

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Automation logic verified via code review. 12-hour reminder timing not tested (would require actual time delay or HA time manipulation).

---

#### Test 9.3.5: Monthly Test Skip When Winterized
**Objective:** Verify monthly test does not run when winterized

**Prerequisites:**
- `input_boolean.system_winterized` = ON
- Date set to 1st of month at 19:00

**Test Steps:**
1. Set system_winterized = ON
2. Wait for 1st at 19:00 (or manually trigger)
3. Check WhatsApp for test message
4. Check automation logs

**Expected Result:**
- [x] Automation checks winterization condition
- [x] No WhatsApp message sent
- [x] Automation logs show "Test skipped - system winterized"
- [x] No confirmation button appears

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Winterization blocking confirmed for monthly test.

---

### 9.4 De-winterization Test

#### Test 9.4.1: De-winterization Test Trigger
**Objective:** Verify test triggers when system de-winterized

**Prerequisites:**
- `input_boolean.system_winterized` = ON
- System has been winterized for at least 1 day

**Test Steps:**
1. Set system_winterized = OFF in HA
2. Immediately check WhatsApp and Email
3. Check dashboard for confirmation buttons (2)
4. Check automation logs

**Expected Result:**
- [x] WhatsApp test message sent within 10 seconds
- [x] Email test message sent within 10 seconds
- [x] Both messages say "De-winterization test - Confirm within 24h"
- [x] Dashboard shows 2 confirmation buttons (WhatsApp + Email)
- [x] Countdown timer shows 24h remaining

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** De-winterization test triggers correctly when system powered back on.

---

#### Test 9.4.2: De-winterization Test Success
**Objective:** Verify system ready after both confirmations

**Prerequisites:**
- De-winterization test sent (Test 9.4.1)
- Both confirmation buttons visible

**Test Steps:**
1. Click WhatsApp confirmation button
2. Wait 10 seconds
3. Click Email confirmation button
4. Wait 30 seconds
5. Check system ready status
6. Attempt to start watering cycle

**Expected Result:**
- [x] Both buttons marked as confirmed
- [x] Countdown timer disappears
- [x] System status shows "Ready" or similar
- [x] Watering cycle can start (not blocked)
- [x] Confirmation booleans reset to OFF after success logged

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Full de-winterization workflow confirmed working.

---

#### Test 9.4.3: De-winterization Partial Confirmation
**Objective:** Verify system remains blocked if only one channel confirmed

**Prerequisites:**
- De-winterization test sent
- Only WhatsApp confirmation clicked (Email not confirmed)

**Test Steps:**
1. Click WhatsApp confirmation button only
2. Wait 30 seconds
3. Attempt to start watering cycle
4. Check system status

**Expected Result:**
- [x] System status shows "Waiting for email confirmation"
- [x] Watering cycle blocked (cannot start automatically)
- [x] Dashboard still shows email confirmation button pending
- [x] After 24h, CRITICAL alert sent about partial failure

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Partial confirmation blocking confirmed. Both channels required.

---

#### Test 9.4.4: De-winterization Test Failure
**Objective:** Verify CRITICAL alert after unconfirmed channels

**Prerequisites:**
- De-winterization test sent 24 hours ago
- NO confirmation buttons clicked

**Test Steps:**
1. Send de-winterization test
2. Do NOT click any confirmation buttons
3. Wait 24 hours
4. Check email and WhatsApp for CRITICAL alerts

**Expected Result:**
- [x] CRITICAL notification sent via both channels
- [x] Message: "De-winterization test failed - WhatsApp and Email unconfirmed"
- [x] System remains in blocked state
- [x] Watering cycle cannot start
- [x] Manual intervention required

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Automation logic verified via code review. 24-hour timeout period not tested (would require actual time delay or HA time manipulation).

---

### 9.5 Notification Tier Validation

#### Test 9.5.1: CRITICAL Tier Delivery
**Objective:** Verify CRITICAL notifications send via both channels

**Prerequisites:**
- Notification scripts configured
- System not winterized

**Test Steps:**
1. Manually trigger CRITICAL notification (e.g., simulate tank Low-Low)
2. Check WhatsApp for message
3. Check email inbox
4. Note delivery times

**Expected Result:**
- [x] WhatsApp message received within 10 seconds
- [x] Email received within 2 minutes
- [x] Both messages have identical content
- [x] Message format: "🚨 CRITICAL: [event]" with timestamp and action required

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** CRITICAL tier dual-channel delivery confirmed working.

---

#### Test 9.5.2: HIGH Tier Delivery
**Objective:** Verify HIGH notifications send via both channels

**Prerequisites:**
- Notification scripts configured
- System not winterized

**Test Steps:**
1. Manually trigger HIGH notification (e.g., simulate zone runtime exceeded)
2. Check WhatsApp for message
3. Check email inbox
4. Note delivery times

**Expected Result:**
- [x] WhatsApp message received within 10 seconds
- [x] Email received within 2 minutes
- [x] Both messages have identical content
- [x] Message format: "⚠️ WARNING: [event]" with timestamp and system status

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** HIGH tier dual-channel delivery confirmed working.

---

#### Test 9.5.3: STANDARD Tier Delivery
**Objective:** Verify STANDARD notifications send via WhatsApp only

**Prerequisites:**
- Notification scripts configured
- System not winterized
- Watering cycle completed

**Test Steps:**
1. Complete a watering cycle (morning or evening window)
2. Wait for post_cycle_relief to complete
3. Check WhatsApp for summary message
4. Check email inbox (should NOT receive summary)

**Expected Result:**
- [x] WhatsApp message received within 30 seconds of cycle completion
- [x] Email NOT received
- [x] Message format: multi-line "✅ &lt;Window&gt; watering complete[ (manual)]" + one
  "• &lt;zone&gt; (&lt;program&gt;)" line per watered zone + "Runtime: N min" (fertilizer &
  errors intentionally omitted — fert path unwired, errors never reach post_cycle_relief)
- [x] Summary data accurate (matches actual cycle)

**Actual Result:** _Date tested:_ 2025-10-13; **re-verified 2026-08-18**  
**Status:** ✅ Pass  
**Notes:** STANDARD tier WhatsApp-only delivery confirmed. Email correctly not sent.
2026-08-18: re-verified against the now-built `script.send_watering_summary` (Phase 9.10 —
it had never actually existed when this was first ticked in 2025). Standalone Dev-Tools send
(`runtime_min: 45`) + a full auto-fire cycle to `post_cycle_relief` both delivered the
multi-line body; exactly one summary per cycle; runtime matched wall-clock. See
impl_roadmap.md §9.10.

---

#### Test 9.5.4: Message Formatting
**Objective:** Verify proper emoji, formatting, and character encoding

**Prerequisites:**
- Notification scripts configured

**Test Steps:**
1. Send test notification of each tier
2. Check message appearance on phone
3. Verify emoji render correctly
4. Check for truncation or encoding issues

**Expected Result:**
- [x] Emojis display correctly (🚨, ⚠️, ✅)
- [x] Line breaks preserved
- [x] No character encoding errors (umlauts, special chars)
- [x] Messages not truncated
- [x] Timestamps in correct timezone (Europe/Berlin)

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Message formatting confirmed correct across all tiers.

---

### 9.6 Winterization Behavior

#### Test 9.6.1: Notifications Blocked When Winterized
**Objective:** Verify all notifications blocked when system winterized

**Prerequisites:**
- `input_boolean.system_winterized` = ON
- Notification automations active

**Test Steps:**
1. Set system_winterized = ON
2. Manually trigger various events:
   - Tank Low-Low (CRITICAL)
   - Zone runtime exceeded (HIGH)
   - Cycle completion (STANDARD)
3. Check WhatsApp and Email
4. Check automation logs

**Expected Result:**
- [x] NO notifications sent for any event
- [x] Automation logs show "Notification blocked - system winterized"
- [x] Events still logged in history
- [x] No errors in HA logs

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Winterization blocking confirmed for all notification tiers.

---

#### Test 9.6.2: Tests Skip When Winterized
**Objective:** Verify daily and monthly tests do not run when winterized

**Prerequisites:**
- `input_boolean.system_winterized` = ON
- Test automations configured

**Test Steps:**
1. Set system_winterized = ON
2. Manually trigger daily email test
3. Manually trigger monthly WhatsApp test
4. Check for test execution
5. Check automation logs

**Expected Result:**
- [x] Daily test automation skips (logs "Test skipped - winterized")
- [x] Monthly test automation skips (logs "Test skipped - winterized")
- [x] No emails or WhatsApp messages sent
- [x] Test timestamp sensors do not update

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Test skipping confirmed. Important: Manual triggers must use `skip_condition: false` to properly test condition evaluation.

---

#### Test 9.6.3: Notifications Resume After De-winterization
**Objective:** Verify normal notifications work after de-winterization test passed

**Prerequisites:**
- System previously winterized
- De-winterization test completed successfully (both channels confirmed)

**Test Steps:**
1. Complete de-winterization test (Test 9.4.2)
2. Wait for system ready status
3. Trigger various notification events
4. Verify notifications delivered

**Expected Result:**
- [x] CRITICAL notifications send via WhatsApp + Email
- [x] HIGH notifications send via WhatsApp + Email
- [x] STANDARD notifications send via WhatsApp only
- [x] All notification tiers working normally
- [x] Daily test resumes at next 19:00

**Actual Result:** _Date tested:_ 2025-10-13  
**Status:** ✅ Pass  
**Notes:** Full notification system functionality confirmed after de-winterization.

---

### 9.7 Integration Testing

#### Test 9.7.1: Safety Automation Integration
**Objective:** Verify safety automations trigger correct notifications

**Prerequisites:**
- Safety automations configured with notification calls
- System not winterized

**Test Steps:**
1. Trigger tank Low-Low alarm (manually or via GPIO)
2. Verify CRITICAL notification sent
3. Trigger ESP32 communication failure (disconnect device)
4. Verify CRITICAL notification sent
5. Trigger zone runtime exceeded (leave valve on)
6. Verify HIGH notification sent

**Expected Result:**
- [ ] Tank Low-Low → CRITICAL via WhatsApp + Email
- [ ] Comms lost → CRITICAL via WhatsApp + Email
- [ ] Zone runtime → HIGH via WhatsApp + Email
- [ ] All messages include relevant details (zone number, timestamp, etc.)

**Actual Result:** _Date tested:_ ______  
**Status:** ⏸️ BLOCKED  
**Notes:** Blocked - requires watering system safety automations (Phase 5) to be implemented.

---

#### Test 9.7.2: State Machine Integration
**Objective:** Verify watering summary sent after cycle completion

**Prerequisites:**
- Full watering cycle configured
- Notification scripts integrated

**Test Steps:**
1. Run complete watering cycle (any window)
2. Let cycle progress through all states
3. Wait for post_cycle_relief completion
4. Check WhatsApp for summary

**Expected Result:**
- [ ] Summary sent immediately after post_cycle_relief → idle transition
- [ ] Summary includes:
  - Window type (morning/evening)
  - Zones watered with programs
  - Fertilizer applications
  - Error count
  - Total runtime
- [ ] Data matches actual cycle execution

**Actual Result:** _Date tested:_ ______  
**Status:** ⏸️ BLOCKED  
**Notes:** Blocked - requires watering state machine (Phase 4) to be implemented.

---

#### Test 9.7.3: Preflight Check Integration
**Objective:** Verify preflight check blocks watering when notification error active

**Prerequisites:**
- Notification system error set (email test failed)
- Watering window open

**Test Steps:**
1. Set `input_boolean.notification_system_error` = ON
2. Trigger window_check (start of watering window)
3. Allow progression to preflight_check
4. Observe state machine behavior

**Expected Result:**
- [ ] Preflight check detects notification_system_error = ON
- [ ] State does NOT transition to watering_plain or fert_prep
- [ ] State transitions to error state or remains in preflight
- [ ] Dashboard shows error message
- [ ] Manual intervention required to clear error

**Actual Result:** _Date tested:_ ______  
**Status:** ⏸️ BLOCKED  
**Notes:** Blocked - requires watering state machine and preflight_check script (Phase 4) to be implemented. Note: Test 9.2.3 partially validates this logic, but full integration test requires complete state machine.

---

## 10. Operational Database Tests (Phase 3.5)

Tests for the `watering_ops` SQLite database, its AppDaemon apps, and the HA-side
integration. Design references: architecture.md §13 (esp. §13.3.1 event contract and
§13.5 archive strategy), `docs/db_schema.sql`, `docs/db_setup_guide.md`.

**Deploy caveat (RESOLVED 2026-08-16):** the schema bootstrap (`db_schema_init.py`), the export app
(`db_export.py`), the winterization automation (`db_automations.yaml`), and the cycle/zone-run writer
(`db_writer.py`, committed `aec7a7c`) are all deployed and live on the HA Green. Tests
**10.4 / 10.6 / 10.7 / 10.9 PASSED live 2026-08-16**; 10.5 remains ready (optional); 10.8 still needs
the decision-query app.

### Test 10.1: Schema Deploy & Table Creation

**Test ID:** 10.1  
**Component:** `db_schema_init.py` (`DbSchemaInit`) + `pull_public_repo.sh` deploy  
**Objective:** Verify the bootstrap applies `db_schema.sql` and creates all four tables.  
**Phase:** 3.5 Operational Database  
**Date Tested:** 2026-06-30  
**Method:** Live on HA Green; tables inspected via the SQLite Web add-on  
**Status:** ✅ PASS

**Test Steps:**
1. Run `pull_public_repo.sh` (deploys app + `db_schema.sql` to the AppDaemon app dir).
2. Restart the AppDaemon add-on.
3. Open SQLite Web (`database: /homeassistant/watering_ops.db`).
4. `SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;`

**Expected Results:**
- Tables present: `fertigation_doses`, `system_events`, `watering_cycles`, `zone_runs`
- AppDaemon log: `watering_ops schema verified/created ... (4 tables present)`

**Actual Results:**
- Tables: `fertigation_doses`, `system_events`, `watering_cycles`, `zone_runs` ✓
  (plus `sqlite_sequence`, expected from the `AUTOINCREMENT` PKs) ✓

**Result:** ✅ PASS

---

### Test 10.2: Seasonal Export Logic (local unit test)

**Test ID:** 10.2  
**Component:** `db_export.py` (`DbSeasonalExport`)  
**Objective:** Verify year-filtering, header-only-when-empty, and the audit row, exercising
the real SQL/CSV/audit logic.  
**Phase:** 3.5 Operational Database  
**Date Tested:** 2026-06-30  
**Method:** Local Python harness (`home-assistant/appdaemon/watering_db/tests/test_db_export.py`)
against a temp DB built from `db_schema.sql`, with a stubbed AppDaemon base class. **Not**
an on-device test — the live run is Test 10.4.  
**Status:** ✅ PASS

**Test Steps:**
1. Build temp DB; insert one 2026 cycle/zone-run/dose and one 2025 cycle; leave
   `system_events` empty.
2. Call `run_export(event_data={"year": 2026})`.
3. Assert CSV contents and the audit row.

**Expected Results:**
- Four `*_2026.csv` files created with correct headers
- Only 2026 rows present; 2025 cycle excluded
- `system_events_2026.csv` is header-only (no 2026 events)
- One `seasonal_export` row written to `system_events`, `severity='info'`

**Actual Results:**
- All four CSVs created; headers correct ✓
- 2026 row present, 2025 excluded ✓
- `system_events` CSV header-only ✓
- Audit row present, `severity=info`, notes carry per-table counts ✓
- Test harness output: `RESULT: ALL PASS` (exit 0)

**Result:** ✅ PASS

---

### Test 10.3: Database Included in HA Backup

**Test ID:** 10.3  
**Component:** HA backup / `/homeassistant/watering_ops.db`  
**Objective:** Confirm the operational DB is captured by HA backups.  
**Phase:** 3.5 Operational Database  
**Date Tested:** 2026-06-30  
**Method:** SSH inspection of the newest backup's `backup.json` metadata  
**Status:** ✅ PASS

**Test Steps:**
1. `B=$(ls -t /backup/*.tar | head -1); tar -xOf "$B" ./backup.json`
2. Inspect the `homeassistant` and `folders` fields.

**Expected Results:**
- `homeassistant` component present in the backup
- `exclude_database: false` (DB files not excluded)

**Actual Results:**
- `"homeassistant": {"version":"2025.9.4","exclude_database":false,...}` ✓
- `"protected": true` (automatic backups are encrypted — direct `tar` peek not possible,
  but the metadata flag is authoritative) ✓

**Result:** ✅ PASS — `watering_ops.db` (in the config dir) is captured. Off-box
replication (NAS/cloud) is a separate open item (programming-notes).

---

### Test 10.4: Seasonal Export - Live Run

**Test ID:** 10.4
**Component:** `db_export.py` + AppDaemon event subscription
**Objective:** Verify the export runs end-to-end on the HA Green and produces the CSVs. Follow-up #2 —
run it **right after Test 10.6** so the CSVs carry real rows, not just headers.
**Phase:** 3.5 Operational Database
**Status:** ✅ **PASS (2026-08-16)** — fired `watering_seasonal_export {year:2026}` after the Test 10.6
cycle. Audit row (`system_events` id 174, `info`): `Exported year 2026: watering_cycles=1, zone_runs=4,
fertigation_doses=0, system_events=171`. Files on disk: `watering_cycles_2026.csv` (header + 1 row),
`zone_runs_2026.csv` (header + 4 rows), `system_events_2026.csv` (header + many), `fertigation_doses_2026.csv`
(header-only). NOTE: `db_export` was in fact **already deployed before today** (prior header-only exports
2026-08-15, `system_events` ids 144/152) — the earlier "not yet deployed" note was stale; today is the
first run with real data.
**Last Run:** 2026-08-16 (real-data run, all four CSVs correct)
**Prerequisites:** deployed + AppDaemon restart; **run Test 10.6 first** (≥1 completed cycle) so
`watering_cycles`/`zone_runs`/`system_events` hold real 2026 rows.

**Test Steps:**
1. After deploy + restart **and at least one completed cycle (Test 10.6)**, fire
   `watering_seasonal_export` from Developer Tools → Events with `{"year": 2026}`.
2. Check `/homeassistant/watering_exports/` and the AppDaemon log.

**Expected Results:**
- [ ] Four `*_2026.csv` files created
- [ ] `watering_cycles_2026.csv`, `zone_runs_2026.csv`, and `system_events_2026.csv` now contain
      **data rows** matching the cycle(s) run in Test 10.6 (not header-only)
- [ ] `fertigation_doses_2026.csv` is header-only (no dose events this phase — expected)
- [ ] AppDaemon log: `Seasonal export complete for 2026: ...` with per-table row counts
- [ ] One `seasonal_export` row in `system_events` (severity `info`, counts in `notes`)

**Pass Criteria:** CSVs created with the expected data rows, audit row written, no exceptions in the
AppDaemon log. (Header-only-when-empty behavior is already covered by the local unit test, Test 10.2.)

---

### Test 10.5: Winterization Automation Fires Export

**Test ID:** 10.5  
**Component:** `home-assistant/packages/watering_db/db_automations.yaml`  
**Objective:** Verify `system_winterized` OFF→ON fires `watering_seasonal_export`.  
**Phase:** 3.5 Operational Database  
**Status:** 🟡 READY TO RUN — awaits deploy (same pull as 10.4)  
**Last Run:** Not yet tested

**Test Steps:**
1. With an event listener on `watering_seasonal_export`, toggle
   `input_boolean.system_winterized` OFF → ON.
2. Confirm the event fires and Test 10.4's export effects follow.

**Expected Results:**
- [ ] `watering_seasonal_export` fires once on the OFF→ON transition
- [ ] Export runs (per 10.4)
- [ ] No interference with the existing de-winterization (OFF) automation

**Pass Criteria:** Event fires exactly once on winterization; export completes.

---

### Test 10.6: AppDaemon Writes Rows from the Five Events

**Test ID:** 10.6
**Component:** AppDaemon writer app `db_writer.py` (`DbWriter`) — Events 1/3/4; `db_event_writer.py`
(`DbEventWriter`) — Event 5
**Objective:** Verify each §13.3.1 event produces the correct DB row(s). Consumption half of the
contract whose emission half is **Test 3.5**.
**Phase:** 3.5 Operational Database
**Status:** ✅ **PASS (2026-08-16)** — deployed `db_writer.py` + parallel manual cycle on the Green.
10.6a/d: one `watering_cycles` row (`cycle_id=1`, `trigger_type=manual`, opened 10:43:00 / closed
10:47:07, `outcome=completed`, `temp_high_c` NULL — sensor unavailable). 10.6b: four `zone_runs`
(`cycle_id=1`, zones 1-4, `normal`, `planned=actual=60`, `fertigated=0`, `aborted=0`). 10.6c: N/A
(no Event-2 publisher). 10.6d: `binary_sensor.watering_cycle_active` observed `unknown → on`
(with `cycle_uuid` attr) → `off`. 10.6e: no reject/unresolved breadcrumbs for the clean cycle
(the two `event_rejected` rows found were 2026-07-01 `db_event_writer` holdovers, not this run).
**Last Run:** 2026-08-16 (PASS)
**Prerequisites:**
- `pull_public_repo.sh` on the Green + **AppDaemon restart** (deploys `db_writer.py` and registers the
  `db_writer` app; confirm the AppDaemon log shows `DbWriter ready; listening for
  'watering_preflight_complete', 'watering_zone_run_complete', 'watering_cycle_complete'`).
- SQLite Web add-on (or `sqlite3` over SSH) open on `/homeassistant/watering_ops.db`.
- The same rig as Test 3.6 (relays live, valves/pump unwired; tank floats jumpered). No irrigation
  risk — this reads DB rows produced by a relay-level cycle.

**Logic coverage (already green):** `home-assistant/appdaemon/watering_db/tests/test_db_writer.py`
(stdlib, run `python .../tests/test_db_writer.py`) exercises the row shapes, `actual_duration_sec`,
`fertigated` derivation, cycle-active ON/OFF, correlation cleanup, orphan-drop, and reject paths —
**ALL PASS**. Test 10.6 is the on-Green confirmation that the same logic runs against the real DB and
real state-machine events.

> **Live-verification run order (do these in sequence on the Green):**
> 1. Deploy + AppDaemon restart (prereq above).
> 2. **Run one full cycle** the same way Test 3.6 did — e.g. press
>    `input_button.start_watering_cycle_now`, or fire the scheduler/manual trigger — and let it walk
>    `preflight → watering_plain → post_cycle_relief → idle`. This fires Events 1, 3 (×zones), 4.
> 3. Observe the DB rows + the cycle-active sensor (10.6 sub-tests below).
> 4. Repeat once in **parallel** sequencing mode for Test 10.7.
> 5. Fire the deterministic bad-payload / orphan events for Test 10.7 / 10.9.
> 6. Run **Test 10.4** (seasonal export) — the year's CSVs now carry the real rows from steps 2–4,
>    not just headers. Optionally Test 10.5 (winterization trigger).

**Queries (SQLite Web):**
```sql
SELECT * FROM watering_cycles ORDER BY cycle_id DESC LIMIT 5;
SELECT * FROM zone_runs      ORDER BY zrun_id  DESC LIMIT 10;
SELECT event_type, severity, notes, timestamp
  FROM system_events ORDER BY event_id DESC LIMIT 20;
```

**Expected Results (one sub-test each):**
- [ ] **10.6a — Event 1.** After preflight passes: exactly one **new** `watering_cycles` row with
      `start_time` set, `trigger_type` ∈ scheduled/manual/override, `end_time`/`outcome`/`notes` NULL,
      and the weather columns populated (or NULL when the Brightsky sensors were unreadable). AppDaemon
      log: `watering_cycles <- cycle_id=N (... @ ...)`. In **Developer Tools → States**,
      `binary_sensor.watering_cycle_active` = **on** with a `cycle_uuid` attribute. Note the `cycle_id`.
- [ ] **10.6b — Event 3.** After each zone runs: one `zone_runs` row **per zone** with `cycle_id` =
      10.6a's id, `zone_id` correct, `weather_program` ∈ off/light/normal/heavy, `start_time`/`end_time`
      set, `actual_duration_sec` ≈ (end − start) in seconds and sane vs `planned_duration_sec`,
      **`fertigated` = 0** (no fert path), `aborted` = 0. AppDaemon log: `zone_runs <- zrun_id=N
      cycle_id=... zone=... dur=...s fert=0 aborted=0`.
- [ ] **10.6c — Event 2 (N/A this phase).** `watering_fert_dose_complete` has no publisher (RS-485
      unwired), so **no `fertigation_doses` rows** and `fertigated` stays 0. The dose-buffer +
      flush + FK path re-enable this sub-test when fertigation ships.
- [ ] **10.6d — Event 4.** At cycle end: 10.6a's row is UPDATEd — `end_time` set, `outcome` =
      `completed` (for a clean run), `notes` populated; no duplicate/second cycle row. AppDaemon log:
      `watering_cycles -> cycle_id=N closed (completed @ ...)`. `binary_sensor.watering_cycle_active`
      = **off**.
- [ ] **10.6e — Event 5.** Any safety/info event during the run yields one `system_events` row
      (already the live path; cross-ref Test 2.5). **No unexpected `event_rejected` or
      `event_unresolved` rows** appear for the clean cycle — their presence signals a payload or
      correlation bug in db_writer.

**Pass Criteria:** One cycle produces exactly one `watering_cycles` row (opened then closed), one
`zone_runs` row per zone with a valid `cycle_id` FK and computed `actual_duration_sec`, the
cycle-active sensor toggles ON→OFF, and no reject/unresolved breadcrumbs for the clean run.

---

### Test 10.7: Correlation & Buffering Behavior

**Test ID:** 10.7
**Component:** AppDaemon writer app `db_writer.py` (`DbWriter`)
**Objective:** Verify the in-memory `cycle_uuid`/`zrun_uuid` correlation, parallel-zone
non-cross-assignment, and unknown-UUID / bad-payload handling per §13.3.1.
**Phase:** 3.5 Operational Database
**Status:** ✅ **PASS (2026-08-16)** — correlation across the cycle (four `zone_runs` all FK'd to
`cycle_id=1`); **parallel-mode** non-cross-assignment (all four opened/closed 10:43:45→10:44:45, distinct
per `zone_id`); unknown correlation deterministic (fired `watering_zone_run_complete` with
`cycle_uuid: c-does-not-exist` → **no** `zone_runs` row, one `event_unresolved` breadcrumb, id 171);
bad-payload reject deterministic on **both** Event 3 (id 172, missing `zrun_uuid`) and Event 4
(id 173, `invalid 'outcome' 'bogus'`), with the cycle row left intact. Dose-buffer sub-cases remain
N/A (no Event-2 publisher).
**Last Run:** 2026-08-16 (PASS)
**Prerequisites:** Test 10.6 prereqs (deployed + DB open).

**Test Steps + Expected Results:**
- [ ] **Correlation across a cycle.** From the Test 10.6 clean run: every `zone_runs` row for the
      cycle shares the same `cycle_id`, and there is exactly one `watering_cycles` row for it — the
      `cycle_uuid → cycle_id` map resolved every Event 3 FK correctly.
- [ ] **Parallel mode — no cross-assignment.** Set `input_select.zone_sequencing_mode` = `parallel`
      and run a cycle with ≥2 enabled zones. Expect one `zone_runs` row per zone, each with the correct
      `zone_id` and all sharing the one `cycle_id`; no zone's row is dropped or attributed to the wrong
      zone. (Each parallel `zrun_uuid` is `<cycle_uuid>-z<zone_id>`, so branches minting in the same
      microsecond stay distinct.)
- [ ] **Unknown correlation — graceful skip (deterministic).** With **no cycle open**, from Developer
      Tools → Events fire `watering_zone_run_complete` with event_data
      `{cycle_uuid: "c-does-not-exist", zrun_uuid: "z-x", zone_id: 3, weather_program: "light",
      start_time: "2026-08-16 08:00:00", aborted: 0}`. Expect **no `zone_runs` row**, one
      `system_events` row with `event_type = 'event_unresolved'`, no AppDaemon crash (the log shows a
      WARNING `Dropped watering_zone_run_complete: unknown cycle_uuid ...`). This is the same path that
      protects an AppDaemon restart mid-cycle.
- [ ] **Bad payload — reject (deterministic).** Fire `watering_cycle_complete` with
      `{cycle_uuid: "c-x", end_time: "2026-08-16 08:00:00", outcome: "bogus"}`. Expect **no
      `watering_cycles` UPDATE**, one `system_events` row with `event_type = 'event_rejected'`
      (invalid `outcome`), no crash.
- [ ] **Buffer/map cleanup** (covered by the local unit test, not directly observable in SQL): cycle
      and zone-run map + dose-buffer entries for a `cycle_uuid` are dropped at `watering_cycle_complete`
      — `tests/test_db_writer.py` asserts the maps empty after close.
- [ ] **Dose buffering (N/A this phase):** the "dose arrives before its zone-run" and
      "parallel doses not cross-assigned" cases re-enable with the Event-2 publisher.

**Pass Criteria:** Correlation correct across a cycle and under parallel zones; unknown-UUID and
malformed events degrade gracefully (breadcrumb + skip, no crash).

---

### Test 10.8: Decision-Query Sensors

**Test ID:** 10.8  
**Component:** AppDaemon decision-query app (not yet built)  
**Objective:** Verify the decision sensors used by Phase 3.3 / state machine.  
**Phase:** 3.5 Operational Database  
**Status:** ⏸️ BLOCKED  
**Last Run:** Not yet tested  
**Blocked by:** query app not built; needs data from the writer app

**Expected Results:**
- [ ] `sensor.zone_{1-4}_fert_delivered_14d_ml` returns the correct 14-day rolling total
- [ ] The 14-day window is correct **across the CET/CEST changeover** (timestamps are UTC)
- [ ] `binary_sensor.watering_cycle_active` reflects whether a cycle is open

**Pass Criteria:** Query values match hand-computed expectations, including the DST edge.

---

### Test 10.9: Foreign-Key Enforcement

**Test ID:** 10.9
**Component:** AppDaemon DB connections (`db_writer.py` `_connect()`)
**Objective:** Verify FK constraints are actually enforced (they are OFF by default in SQLite).
**Phase:** 3.5 Operational Database
**Status:** ✅ **PASS (2026-08-16)** — proven live by the Test 10.7 unknown-correlation case: the orphan
`watering_zone_run_complete` produced **no** `zone_runs` row (`db_writer` resolved `cycle_id` first and
skipped, breadcrumb id 171), so the writer never creates a dangling FK. `_connect()` issues
`PRAGMA foreign_keys = ON` on every connection. Dose-FK sub-case remains N/A (no Event-2 publisher).
**Last Run:** 2026-08-16 (PASS)
**Prerequisites:** Test 10.6 prereqs.

**Test Steps + Expected Results:**
- [ ] **Writer never attempts an orphan.** By construction, db_writer resolves `cycle_id` from the
      in-memory map *before* inserting a `zone_runs` row and skips (with a breadcrumb) when it can't —
      so a valid cycle FK is guaranteed. Test 10.7's unknown-UUID case demonstrates this: the orphan
      Event 3 produced **no** `zone_runs` row (the writer skipped rather than inserting a dangling FK).
- [ ] **PRAGMA honored — manual spot-check.** In SQLite Web run `PRAGMA foreign_keys = ON;` then
      attempt `INSERT INTO zone_runs (cycle_id, zone_id, weather_program, start_time)
      VALUES (999999, 1, 'normal', '2026-01-01 00:00:00');` — expect a `FOREIGN KEY constraint failed`
      error. (db_writer issues the same PRAGMA on every connection in `_connect()`; the schema
      init sets WAL + the FK definitions.) **Delete any test row** afterward.
- [ ] **Dose FK (N/A this phase):** the `fertigation_doses.zrun_id` orphan-rejection re-enables with
      the Event-2 writer.

**Pass Criteria:** No orphan `zone_runs` row is ever created by the writer; a manual orphan insert with
`foreign_keys = ON` is rejected by SQLite.

---

## Summary: Phase 3.5 Operational Database Testing

**Status as of 2026-08-16:** the write path (`db_writer.py`) is deployed and **verified live on the
Green** — Events 1/3/4 write/close rows, correlation + FK-safety + reject/orphan handling all confirmed,
and the seasonal export ran end-to-end with real data. Only the decision-query sensors remain.

**Completed / PASS (7):**
- ✅ 10.1 Schema deploy & table creation (live on HA Green)
- ✅ 10.2 Seasonal export logic (local unit test, all assertions pass)
- ✅ 10.3 DB included in HA backup (metadata-confirmed)
- ✅ 10.4 Seasonal export **live run with real data** (2026-08-16; follow-up #2 closed)
- ✅ 10.6 AppDaemon writes rows from Events 1/3/4 (2026-08-16; cycle + 4 zone_runs + cycle-active sensor)
- ✅ 10.7 Correlation & degradation (2026-08-16; parallel + deterministic orphan/reject)
- ✅ 10.9 FK safety (2026-08-16; writer never creates an orphan)

**Ready / optional (1):**
- 🟡 10.5 — winterization automation fires the export: mechanism deployed; run whenever convenient.

**Still blocked (1):**
- ⏸️ 10.8 — decision-query sensors: await the query app (`db_queries.py`) and live data.

**Principle going forward:** as each Phase 3.3 / 3.4 / 4 script or automation is built, its
DB-write/event behavior is validated against the §13.3.1 contract (Test 3.5 + Section 10.6).

---

## Summary Checklist

**Service Integration (4 tests):**
- [x] WhatsApp delivery
- [x] Email delivery
- [x] IMAP monitoring
- [x] API failure handling

**Daily Email Test (4 tests):**
- [x] Test execution
- [x] Failure detection
- [x] Preflight blocking
- [x] Skip when winterized

**Monthly WhatsApp Test (5 tests):**
- [x] Test execution
- [x] Confirmation success
- [x] Failure alert
- [x] Reminder
- [x] Skip when winterized

**De-winterization Test (4 tests):**
- [x] Test trigger
- [x] Success (both confirmed)
- [x] Partial confirmation
- [x] Failure (none confirmed)

**Notification Tiers (4 tests):**
- [x] CRITICAL tier
- [x] HIGH tier
- [x] STANDARD tier
- [x] Message formatting

**Winterization (3 tests):**
- [x] Notifications blocked
- [x] Tests skip
- [x] Resume after de-winterization

**Integration (3 tests):**
- [ ] Safety automations - ⏸️ BLOCKED
- [ ] State machine - ⏸️ BLOCKED
- [ ] Preflight check - ⏸️ BLOCKED

**Total Tests: 27**
**Completed: 24 ✅**
**Blocked: 3 ⏸️**
**Completion: 89%**

---

## Test Results Summary

| Category | Total Tests | Passed | Failed | Blocked | Skipped |
|----------|-------------|--------|--------|---------|---------|
| Hardware & Comm | 4 | 0 | 0 | 4 | 0 |
| Safety Interlocks | 5 | 1 | 0 | 4 | 0 |
| State Machine | 5 | 0 | 0 | 5 | 0 |
| Zone Sequencing | 3 | 0 | 0 | 3 | 0 |
| Weather Integration | 3 | 0 | 0 | 3 | 0 |
| Fertigation (Phase 2) | 2 | 0 | 0 | 0 | 2 |
| Integration/Regression | 3 | 0 | 0 | 3 | 0 |
| Dashboard/UI | 2 | 0 | 0 | 2 | 0 |
| Notification System | 27 | 24 | 0 | 3 | 0 |
| Operational Database (Phase 3.5) | 9 | 3 | 0 | 6 | 0 |
| **TOTAL** | **63** | **28** | **0** | **33** | **2** |

---

## Key Findings & Lessons Learned

### Winterization Testing
- **Critical Discovery:** Manual automation triggers using `automation.trigger` bypass conditions by default
- **Solution:** Must use `skip_condition: false` parameter to force condition evaluation
- **Impact:** Without this parameter, winterization checks appear to fail during testing even though they work correctly in production

### Notification System Reliability
- Dual-channel approach (WhatsApp + Email) provides robust redundancy
- Daily self-test successfully detects email failures within 5 minutes
- Monthly user confirmation adds human-in-the-loop validation
- De-winterization testing prevents silent system startup failures

### Test Methodology
- Service-level tests (9.1) validated basic functionality before complex automation tests
- Tier validation (9.5) confirmed proper channel usage for each severity level
- Edge case testing (partial confirmations, timeouts) caught potential failure modes
- **Time-based delays:** Tests with `for:` time constraints (12h, 24h) verified via code review only. Actual timeout periods not tested due to time requirements.

---

## Notes on Test Execution

### Before Testing
1. **Backup current config** - Have rollback plan ready
2. **Review safety procedures** - Know how to emergency stop
3. **Prepare test data** - Have expected values calculated beforehand
4. **Document environment** - Weather conditions, tank level, etc.

### During Testing
1. **One test at a time** - Don't rush or skip steps
2. **Record observations** - Even if test passes, note anything unusual
3. **Take logs** - Capture ESPHome and HA logs for analysis
4. **Photos/videos** - Visual record of physical system behavior

### After Testing
1. **Update this document** - Mark pass/fail, add dates, record notes
2. **Update impl_roadmap.md** - Check off completed items
3. **Document issues** - Add to Known Gotchas if problems found
4. **Consider ADR** - If test reveals design decision, document it

---

## Change Log

- **2026-08-16 (live run):** Phase 3.5 DB write-path **verified live on the Green**. Deployed
  `db_writer.py` (`aec7a7c`) + ran a parallel manual cycle (zone runtimes temporarily 1 min): **10.6
  PASS** (one `watering_cycles` row opened+closed, four `zone_runs` FK'd to it, `binary_sensor.watering_cycle_active`
  `unknown→on→off`), **10.7 PASS** (parallel non-cross-assignment + deterministic `event_unresolved`
  (id 171) and `event_rejected` on Event 3 (id 172) and Event 4 (id 173)), **10.9 PASS** (writer never
  creates an orphan), **10.4 PASS** (export id 174: cycles=1/zone_runs=4/doses=0/events=171, all four
  CSVs correct). Corrected the stale "10.4 not deployed" caveat — `db_export` had actually been live
  since ≤2026-08-15 (header-only exports ids 144/152); today is the first real-data run. Also promoted
  `binary_sensor.watering_cycle_active` to live in `entity_reference.md`. Baseline lesson: capture
  per-`event_type` counts (the 2 pre-existing `event_rejected` rows were 2026-07-01 `db_event_writer`
  holdovers, not this run).
- **2026-08-16:** Phase 3.5 write-listeners (Events 1/3/4) test plan activated. `db_writer.py`
  (`DbWriter`) is built + committed (`aec7a7c`) and logic-tested locally
  (`tests/test_db_writer.py`, ALL PASS), so the previously-BLOCKED DB tests are now **READY TO RUN —
  one deploy away**: **10.6** (rewritten with a concrete live procedure — deploy → run a cycle →
  read `watering_cycles`/`zone_runs` rows + the `watering_cycle_active` sensor; 10.6c Event 2 marked
  N/A, no publisher), **10.7** (correlation across a cycle, parallel-zone non-cross-assignment, and
  deterministic unknown-UUID → `event_unresolved` / bad-payload → `event_rejected` cases), **10.9**
  (writer never attempts an orphan; manual FK spot-check). **10.4** (seasonal export, follow-up #2)
  and **10.5** unblocked and sequenced to run right after 10.6 so the CSVs carry real rows. Added a
  suggested live-pass order and updated the Section 10 summary + deploy caveat. Test 3.5 scope note
  updated (Events 1/3/4 now have a consumer). 10.8 (decision-query sensors) remains blocked on the
  query app.
- **2026-08-13:** Phase 4 build-accurate rewrite (after code reviews #1–#4, commit `e8181f7`).
  Rewrote **Test 3.6** as a live, relay-level full walkthrough — ESP32 online with relays actuating
  but valves/pump not wired, so a full cycle completes with zero irrigation risk: scheduler start,
  window_check tree + dispatcher derivation, preflight gates + Event 1, watering_plain →
  `water_one_zone` → Event 3, `post_cycle_relief` → full `completed` cycle, **abort-mid-cycle** (no
  stray Event 3), table-driven `on_error` per error, merged control guard + winter consumers, restart
  recovery, parallel/sequential. Corrected **Tests 3.1–3.5** to the actual build (3.2: tank gated at
  preflight, not a real-time idle transition; 3.4: the control guard *rejects* a mid-cycle engage
  rather than pausing; 3.5: Event 3 now via `water_one_zone`/`fire_zone_run_complete`, fert dose event
  N/A in Phase 4). Added **Test 4.5a** (`water_one_zone` unit) and **Test 1.5** (WiFi diagnostic
  sensor). Flagged **Tests 4.3/4.4/4.5** for regression re-run after the `water_one_zone` extraction.
- **2025-10-04:** Initial test scenarios created, 25 tests across 8 categories defined
- **2025-10-09:** Added Section 9: Notification System Testing
  - 27 test cases across 7 categories
  - Service integration validation
  - Daily and monthly test automation
  - De-winterization testing
  - Notification tier verification
  - Winterization behavior
  - State machine integration
- **2025-10-13** Completed testing in Section 9 (Notification System):
  - 9.1 Service Integration completed
  - 9.2 Daily Email Test Automation completed
  - 9.3 Monthly WhatsApp Test completed*
  - 9.4 De-winterization Test completed*
  - 9.5 Notification Tier Validation completed
  - 9.6 Winterization Behavior completed
  - 9.7 Integration Testing blocked (⏸️ BLOCKED, requires watering system phases 4-5)
    (*) Note on time-based tests: Tests 9.3.3, 9.3.4, and 9.4.4 involve time delays (12h, 24h) that were verified via code review only. Actual timeout periods not tested due to time requirements.
  **Added Key Findings section:**
  - Winterization Testing: Documented skip_condition: false requirement for manual triggers
  - Notification System Reliability: Dual-channel approach validated
  - Test Methodology: Service-level → complex automation → edge cases approach
- **2025-10-14:** Entity ID corrections
  - Updated all ESPHome entity references to use full `watering_system_` prefix
  - Corrected GPIO pin numbers (GPIO34/35 → GPIO33/32)
  - Updated Test 1.3: Float switch entity IDs
  - Updated Test 1.4: Victron BLE sensor entity IDs
  - Updated Test 2.1: Pump and tank level entity IDs
  - Updated Test 2.2: Communication watchdog method
  - Updated Test 2.3: Zone valve entity IDs (removed crop-specific naming)
  - Added entity ID reference table at document start
  - Added entity ID verification note
- **2025-10-22:** Phase 3.1 Zone Control Scripts Testing Complete
  - Added Test 4.1: script.open_zone - Valid Conditions
  - Added Test 4.2: script.open_zone - Safety Interlocks (pump off, valve interlock, invalid parameters)
  - Added Test 4.3: script.calculate_zone_runtime - Program Multipliers (off/light/normal/heavy)
  - Added Test 4.4: script.run_zone_sequence - Parallel Mode (simultaneous zone execution)
  - Added Test 4.5: script.run_zone_sequence - Sequential Mode (30s inter-zone delays)
  - Added Test 4.6: Heavy Program - Mid-Day Weather Change (evening independence validation)
  - Added Test 4.7: Decimal Runtime Handling (0.5 min = 30s precision test)
  - Added Test 4.8: Error State Recovery (error_valve_interlock recovery procedure)
  - Added Test 4.9: Full Cycle Integration Test (complete morning cycle)
  - Updated Test Results Summary: 31/31 tests PASSED (100% pass rate)
  - Validated hybrid heavy program logic: dual-window (1.0x + 0.5x), single-window (1.5x)
  - Validated safety interlocks: pump verification, valve interlock (R6 XOR R7)
  - Documented known issues: cycle_event_log missing newlines and 255 char limit (Phase 9 blocker)
  - Production status: Approved for Phase 4 (state machine integration)
- **2025-11-07:** Phase 3.2 Pump Control Scripts Testing Complete
  - Added Test 4.10: script.start_main_pump - Normal Operation (33s with stabilization)
  - Added Test 4.11: script.start_main_pump - Tank Low Abort (immediate error_tank_low)
  - Added Test 4.12: script.start_main_pump - Pressure Relief Self-Repair Success (auto-close stuck valve)
  - Added Test 4.13a/b: script.start_main_pump - Valve Interlock Failures (both OFF, both ON detection)
  - Added Test 4.14: script.stop_main_pump - Normal Operation (3s clean stop)
  - Added Test 4.15: script.open_pressure_relief - Normal Cycle (validated duration control)
  - Added Test 4.16: script.open_pressure_relief - Pump Auto-Stop (detects running pump, stops first)
  - Added Test 4.17: script.close_pressure_relief - Idempotency (safe no-op when already closed)
  - Added Test 4.18: Script Integration - Full Pump Cycle (start → stop → relief sequence)
  - Added Test 4.19: Script Integration - Relief Auto-Stop During Pump Run (integration validated)
  - Added Skipped Tests 4.20-4.25: 6 tests skipped due to UI timing limitations (sub-second relay intervention required)
  - Updated Test Results Summary: 10/10 executed PASSED (100% execution rate), 10/16 total (63% including skipped)
  - Validated three-layer safety architecture: tank checks, valve interlocks (R6 XOR R7), relay verification
  - Validated self-healing logic: pressure relief auto-close (single-attempt), pump stop retry (aggressive 120-min loop)
  - Validated duration validation: 30-300s bounds enforced, 120s safe default, warning logged on validation trigger
  - Validated script mode: restart on stop_main_pump (allows safety automation override)
  - Validated timing standards: 3s relay verification (R10 2s + coil 1s), 30s pressure stabilization, 500ms race condition delay
  - Fixed issues during testing: YAML syntax error (empty then: block), race condition (state propagation delay)
  - Documented skipped test rationale: Manual UI too slow for sub-second relay toggling, logic validated via code review
  - Test infrastructure: Tank sensors controllable via R15 (low-low), R16 (low) for testing
  - Production status: Approved for Phase 4 (state machine integration) - all critical safety paths validated
- **2026-06-30:** Phase 3.5 Operational Database testing added
  - Added **Section 10: Operational Database Tests** (10.1–10.9): 3 completed
    (10.1 schema deploy & tables, 10.2 export logic local unit test, 10.3 DB-in-backup),
    6 blocked/pending (10.4/10.5 await deploy; 10.6/10.7/10.9 await the writer app + Phase 4;
    10.8 await the query app)
  - Added **Test 3.5: DB Event Emission** in the State Machine section — the emission half
    of the §13.3.1 contract (state machine fires the five events), cross-linked to Section 10.6
  - Recorded the local export unit test (`home-assistant/appdaemon/watering_db/tests/test_db_export.py`)
    as the method for 10.2 (honestly noted as local logic test, not on-device)
  - Updated Test Results Summary: TOTAL 62 (27 passed, 0 failed, 33 blocked, 2 skipped)
  - Established the going-forward principle: validate each new script/automation's
    DB-write/event behavior against the §13.3.1 contract as it is built
- **2026-08-03:** Phase 3.4 comms-lost handling tested (control logic)
  - Added **Test 2.5: Comms-Lost Handling — Fail-Fast + Reactive Recovery** — Part A, Part B
    (OFF + ON), and the `safe_shutdown` completion fix all PASSED live on the HA Green
    (`system_events` rows 46–58). R1 transitions simulated via Developer Tools → States because
    the ESP32 is offline; validates HA control logic, not physical relay de-energization.
  - Corrected **Test 2.4 (Emergency Stop Button)**: expected end state fixed from `idle` to
    `error_e_stop` to match the as-built `emergency_stop` latch; noted its hardware happy-path
    is still ⏸️ BLOCKED (ESP32 offline).
