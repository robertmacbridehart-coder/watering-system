# Watering System – Programming Notes (Canonical)

This file is the **canonical technical reference** for the project. It now lives in the public repo under `/docs/programming-notes.md` at:

👉 [https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md)

All future conversations should reference this file as the source of truth. The older canvas version may still exist, but this document takes precedence.

---

## Workflow Guardrails

* **Start**: Read this document first; load prior context and open items.
* **Code**: Use canvas for any non-trivial YAML/scripts; keep chat minimal.
* **Sources**: Cite primary docs (datasheets, official READMEs/wikis, API refs) for all new parts/configs.
* **Repo Reference**: Before recommending or generating any code, reference the code and configuration files in the public repo to maintain consistency.
* **Debugging**: Log first (raw payloads/serial/BLE), validate against spec, then minimal repro.
* **Close**: Update Change Log + TODOs here and sync repo.
* **Safety**: Do not enable actuation without interlocks; relays default `ALWAYS_OFF`.

---

## Before You Code - Mandatory Checklist

This checklist **must** be completed before writing any new code or configuration. It formalizes the "requirements first" principle and prevents wasted effort.

### The Checklist

Before writing a single line of code, verify:

#### 1. Complete Understanding
- [ ] I understand the **complete** requirement, not just the first sentence
- [ ] I know what success looks like (acceptance criteria)
- [ ] I understand the context (why is this needed?)
- [ ] I've asked clarifying questions if anything is ambiguous
- [ ] **I am reasoning from facts only, not assumptions** - if I don't know something for certain, I ask

#### 2. Documentation & Existing Code Review
- [ ] I've reviewed relevant documentation (architecture.md, programming-notes.md, impl_roadmap.md)
- [ ] I've checked the public repo for related existing code
- [ ] I've verified entity IDs in Home Assistant Developer Tools (NOT from ESPHome config)
- [ ] I've checked `/docs/entity_reference.md` for correct entity naming patterns
- [ ] I know what already exists that I can reuse
- [ ] I've reviewed similar implementations in the codebase
- [ ] I'm not duplicating functionality that already exists
- [ ] I understand how this fits into the overall system design

#### 3. File Placement
- [ ] I know exactly which file this code belongs in
- [ ] I've confirmed the package/module structure
- [ ] I understand the separation of concerns (ESPHome vs HA)
- [ ] I know if this is a new file or modifying existing

#### 4. Safety Implications
- [ ] I've identified what could go wrong if this fails
- [ ] I've considered interlocks needed (hardware + software)
- [ ] I know the safe default state (relays off, valves closed)
- [ ] I've planned for error conditions and recovery

#### 5. Testing Strategy
- [ ] I know how this will be tested (manual, automated, both)
- [ ] I've identified test cases (happy path + failure modes)
- [ ] I know what observable behavior indicates success
- [ ] I have a way to verify without risking hardware damage

#### 6. Rollback Plan
- [ ] I know how to undo this change if it fails
- [ ] I've considered impact on existing automations
- [ ] I know if this requires coordinated ESPHome + HA changes
- [ ] I have a backup of current working state

#### 7. Documentation Impact
- [ ] I know if this requires ADR documentation
- [ ] I've identified what needs updating (roadmap, notes, architecture)
- [ ] I know if this creates new gotchas to document
- [ ] I've planned the change log entry

---

### When in Doubt: ASK

**If you answer "no" or "unsure" to ANY item above:**
- **STOP** - Do not write code yet
- **ASK** - Request clarification, examples, or guidance
- **RESEARCH** - Check docs, repo, similar implementations
- **DISCUSS** - Talk through the approach before coding

**Critical Rule: Facts Over Assumptions**
- If you don't **know** something, don't **assume** it
- "I think this might work" → Ask for confirmation
- "This is probably configured as X" → Check the actual config
- "Users typically want Y" → Ask what this user wants
- **When uncertain, always err on the side of asking**

**Never assume. Always verify.**

---

### Examples of Good vs. Bad Starts

#### ❌ Bad: Jumping to Implementation
```
User: "Add a sensor for soil moisture"
Assistant: [immediately generates 50 lines of YAML]
```

#### ✅ Good: Requirements First
```
User: "Add a sensor for soil moisture"
Assistant: "Before I write code, let me clarify:
- Which zone(s) need soil sensors?
- Are these the DFRobot SEN0600 RS-485 sensors?
- What Modbus addresses should they use (0x05-0x07)?
- Should this go in a new package or existing inputs.yaml?
- How will this integrate with watering decisions?
- Should I check if similar sensors already exist in the repo?"
```

---

### Assistant Responsibilities

When the assistant (me) receives a coding request, I must:

1. **Review documentation first** - Load architecture.md, programming-notes.md, and impl_roadmap.md to understand context
2. **Check the repo** - Fetch and review existing related code before proposing solutions
3. **Verify checklist completion** - Ask clarifying questions if requirements are unclear
4. **Propose approach before coding** - Describe what I'll do, where it goes, and why
5. **Wait for approval** - Don't write code until user confirms the approach
6. **Implement carefully** - Follow all coding standards, safety rules, and YAML style guidelines
7. **Provide complete code** - No placeholders, no "TODO" comments, fully working implementations
8. **Document changes** - Suggest change log entries and ADRs when appropriate

**The assistant should explicitly state when checking these items**, for example:

```
"Before I implement this, let me verify:
✓ Reviewed architecture.md - this fits in the state machine's preflight_check state
✓ Checked repo - no existing tank level validation script found
✓ File placement - this belongs in home-assistant/packages/watering_safety_scripts.yaml
✓ Safety implications - needs to stop pump immediately and set error state
✓ Testing - can test by manually triggering low-low float switch

Ready to proceed with implementation?"
```

This transparency helps catch issues before code is written.
---

## Canonical Documents

This project maintains four authoritative documents that work together. **When doing coding/implementation work, load all four documents** - each provides essential context.

### Core Documentation

| Document | Purpose | Critical For |
|----------|---------|--------------|
| **[programming-notes.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md)** | Coding standards, patterns, workflow guardrails, tribal knowledge | Every session |
| **[architecture.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/architecture.md)** | System design, state machine, entity definitions | Understanding what we're building |
| **[impl_roadmap.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/impl_roadmap.md)** | Implementation status, blockers, file ownership | Knowing where we are and what's next |
| **[test_scenarios.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/test_scenarios.md)** | Concrete test cases with pass/fail tracking | Validating implementations |

### Why All Four Matter for Coding

**programming-notes.md** isn't just standards - it's **tribal knowledge**:
- The "why" behind design decisions
- Gotchas discovered and resolved
- Patterns that work (and those that don't)
- Hardware quirks and workarounds
- Lessons learned from debugging sessions

Combined with the other three documents, you get complete context:
- **What** we're building (architecture)
- **Where** we are (roadmap) 
- **How** we build it + **why** we do it that way (notes)
- **How** we validate it works (test scenarios)

### Loading Documents for Coding Sessions

**Copy and paste these raw URLs into chat ONE AT A TIME** (prevents chat length errors):

**1. programming-notes.md (load first - standards & tribal knowledge):**
```
https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/programming-notes.md
```

**2. architecture.md (system design & flow):**
```
https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/architecture.md
```

**3. impl_roadmap.md (current status & next steps):**
```
https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/impl_roadmap.md
```

**4. test_scenarios.md (validation approach):**
```
https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/test_scenarios.md
```

**Important:** Wait for the assistant to confirm each document loaded before adding the next URL.

### Document Hierarchy

```
architecture.md      → What we're building (design, entities, flow)
        ↓
impl_roadmap.md     → Where we are (status, phases, blockers)
        ↓
programming-notes   → How we build (standards, patterns, tribal knowledge)
        ↓
test_scenarios      → How we validate (test cases, results)
```

### When to Update Each Document

- **architecture.md**: Design decisions change (state machine, entity structure, automation flow)
- **impl_roadmap.md**: Tasks complete, blockers emerge, status changes
- **programming-notes.md**: Standards evolve, new patterns emerge, snippets refined, **lessons learned**
- **test_scenarios.md**: Tests run (record pass/fail, dates, observations)
---

## Project Index

* **Hardware**

  * Battery: Acconic A40 12 V 40 Ah LiFePO₄
  * Solar: ECTIVE MSP 100s 100 W panel
  * Charge Controller: Victron SmartSolar MPPT 100/20 (LOAD 15 A, charge 20 A, PV max 100 V)
  * SmartShunt + SmartSolar via BLE (Fabian-Schmidt’s `esphome-victron_ble`)
  * Switches & Relays: 19 mm IP67 3-position rotary (12–24 V), RS PRO DPDT 121-7804 + socket 121-7825, CZH-LABS 10 A DC-DC SSR (DIN)
  * Sensors: ELO 204KS22G01H float switches (SPDT, 2× for tank levels), DFRobot SEN0600 RS-485 soil moisture/temperature (future)
  * ESP32: ESP32-DEVKITC-VE
* **ESPHome (ESP32)**

  * UART2: TX=GPIO25, RX=GPIO26 → RS-485 relay board
  * Relays default OFF on reboot
  * Inputs: GPIO33=Low water level, GPIO32=Low-Low water level (float switches with INPUT_PULLUP)
    * Note: GPIO32/33 chosen over GPIO34/35 because they have internal pull-up resistors (GPIO34/35 are input-only and lack internal pull-ups)
  * Modbus relay board at addr 0x01, 9600 8N1
  * ESPHome config structured into **packages**:
    - `packages/modbus_rs485.yaml` → UART + relay board
    - `packages/inputs.yaml` → GPIO sensors (Low/Low-Low)
    - `packages/victron_ble.yaml` → SmartSolar BLE sensors
  * Victron BLE: include all available SmartSolar + SmartShunt entities
* **Home Assistant**

  * Automations split into modules: Watering Schedule, UI dashboard, Fertilizer dosing, Safety/Alarms, Maintenance/Stats, Weather integration

---

## Coding & YAML Standards

* Use `snake_case` for ids and Title Case for friendly names.
* Add icons for switches/valves/pumps.
* Relays: `ALWAYS_OFF` + `auto_off` for long-open valves (e.g., 120min).
* Logger: DEBUG during dev, INFO in production.
* Filters: Binary sensors with debounce ≥50 ms; delayed\_off if noisy.
* Secrets: **All sensitive values** (`wifi_ssid`, `wifi_password`, API keys, BLE bindkeys, MACs, lat/lon, MQTT creds) must be `!secret` in YAML. Public repo mirrors only `secrets.example.yaml`.

---

## RS-485 / Modbus Rules

* Topology: Linear bus (daisy chain). Avoid star; short stubs only.
* Termination: 120 Ω across A/B at **both ends** (ESP32 RS-485 adapter + pump block).
* Reference: share a common 0 V/COM along with A/B. Shield to earth at master only.
* Baud: 9600 8N1 (stub lengths 6–20 m acceptable).
* Addressing: DFRobot SEN0600 defaults to 1. Change via register 0x07D0 (2000). Only one powered sensor when changing.

---

## Victron BLE (SmartSolar / SmartShunt)

* Vendored component code goes in: `esphome/components/victron_ble/`
* No `external_components:` block needed when vendored.
* Enable `esp32_ble_tracker:` in the **root YAML**.
* For vendored components, add `external_components:` block to reference local path:
```yaml
  external_components:
    - source:
        type: local
        path: components
      components: [victron_ble]
```
* Credentials (`mac_address`, `bindkey`) stored in `secrets.yaml`.
* Normalize entity names with the **“MPPT …”** scheme for easy filtering in Home Assistant.

---

## Relay Naming Convention

**ESPHome Internal IDs (for use within ESPHome YAML only):**
- `relay_pump_main` - Main irrigation pump
- `relay_zone_1` through `relay_zone_4` - Zone valves (Relays 2-5)
- `relay_fert_bypass_valve` - Fertilizer bypass
- `relay_fert_line_valve` - Fertilizer injection line
- `relay_pressure_relief` - Pressure relief valve
- `relay_24v_cabinet` - 24V cabinet enable
- `relay_8`, `relay_11` through `relay_16` - Reserved

**Home Assistant Entity IDs (for use in automations/scripts/dashboards):**
- `switch.watering_system_relay_1_main_pump` - Main irrigation pump
- `switch.watering_system_relay_2_zone_1` through `switch.watering_system_relay_5_zone_4` - Zone valves
- `switch.watering_system_relay_6_fert_bypass` - Fertilizer bypass
- `switch.watering_system_relay_7_fert_line` - Fertilizer injection line
- `switch.watering_system_relay_9_pressure_relief` - Pressure relief valve
- `switch.watering_system_relay_10_24v_cabinet` - 24V cabinet enable
- `switch.watering_system_relay_8`, `switch.watering_system_relay_11` through `switch.watering_system_relay_16` - Reserved

**ESPHome Display Names (visible in HA UI):**
- "Relay 1 - Main Pump"
- "Relay 2 - Zone 1" through "Relay 5 - Zone 4"
- "Relay 6 - Fert Bypass"
- "Relay 7 - Fert Line"
- "Relay 9 - Pressure Relief"
- "Relay 10 - 24V Cabinet"
- "Relay 8", "Relay 11" through "Relay 16"

**Icons:**
- `mdi:pump` - Main pump
- `mdi:sprinkler-variant` - Zone valves
- `mdi:valve` - Control valves (bypass, fert line, pressure relief)
- `mdi:power` - 24V cabinet enable

**CRITICAL: How Entity IDs Are Generated**

Home Assistant entity IDs are derived from:
1. **Device name** (ESPHome): `watering-system` → slugified to `watering_system`
2. **Entity name** (ESPHome): "Relay 1 - Main Pump" → slugified to `relay_1_main_pump`
3. **Result**: `switch.watering_system_relay_1_main_pump`

**The ESPHome `id:` field is ONLY for internal ESPHome references (scripts, lambdas, conditions).**

**Example - Correct Usage:**
```yaml
# In ESPHome YAML:
switch:
  - platform: template
    id: relay_pump_main           # ← Internal reference
    name: "Relay 1 - Main Pump"   # ← Generates entity_id
    
# In Home Assistant automation:
- service: switch.turn_on
  target:
    entity_id: switch.watering_system_relay_1_main_pump  # ← Use full entity ID

# In ESPHome script:
- switch.turn_on: relay_pump_main  # ← Use internal ID
```

**Example - WRONG:**
```yaml
# ❌ This will NOT work in Home Assistant:
- service: switch.turn_on
  target:
    entity_id: switch.relay_pump_main  # Entity doesn't exist!
```

**Architecture:**
- Raw coils (`relay_X_raw`) are internal Modbus switches
- Safe scripts (`turn_on/off_relay_X_safe`) handle 24V power sequencing
- ON sequence scripts (`relay_X_on_sequence`) provide 120min auto-off timers
- Template switches (`relay_X`) are user-facing with proper timer management

**Reference:** See `/docs/entity_reference.md` for complete entity ID mapping.

---

## ESPHome Snippets (Authoritative)

### UART + Modbus

```yaml
uart:
  id: modbus_uart
  tx_pin: GPIO25
  rx_pin: GPIO26
  baud_rate: 9600
  stop_bits: 1
  rx_buffer_size: 512

modbus:
  id: modbus1
  uart_id: modbus_uart
  send_wait_time: 8ms

modbus_controller:
  - id: relay_board
    address: 0x01
    modbus_id: modbus1
    command_throttle: 100ms
```

### Relays (valves)

```yaml
switch:
  - platform: modbus_controller
    modbus_controller_id: relay_board
    id: relay_1
    name: "Relay 1"
    register_type: coil
    address: 0
    icon: mdi:valve
    restore_mode: ALWAYS_OFF
    auto_off: 120min
    write_lambda: |-
      return x;
```

### Tank Level Float Switches

**ESPHome Configuration:**
```yaml
binary_sensor:
  # Tank level monitoring with debounce and alarm delays
  - platform: gpio
    pin:
      number: GPIO33
      mode: INPUT_PULLUP
      inverted: true
    id: low_water_level                # ← Internal ESPHome reference
    name: "Low Water Level"            # ← Generates HA entity ID
    icon: mdi:water-alert
    device_class: problem
    filters:
      - delayed_on_off: 100ms   # Debounce contact bounce
      - delayed_on: 5s          # Prevent splash false alarms
      - delayed_off: 30s        # Prevent sloshing from clearing alarm

  - platform: gpio
    pin:
      number: GPIO32
      mode: INPUT_PULLUP
      inverted: true
    id: low_low_water_level            # ← Internal ESPHome reference
    name: "Low Low Water Level"        # ← Generates HA entity ID
    icon: mdi:water-alert-outline
    device_class: problem
    filters:
      - delayed_on_off: 100ms
      - delayed_on: 5s
      - delayed_off: 30s
```

**Home Assistant Entity IDs Generated:**
```
binary_sensor.watering_system_low_water_level
binary_sensor.watering_system_low_low_water_level
```

**Usage in Home Assistant Automations:**
```yaml
# Tank Low-Low emergency stop automation:
automation:
  - alias: "Safety - Tank Level Emergency Stop"
    trigger:
      - platform: state
        entity_id: binary_sensor.watering_system_low_low_water_level
        to: 'on'
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.watering_system_relay_1_main_pump
```

**Note:** Binary sensors use `delayed_on_off` for debouncing, not `debounce` (which only exists for regular sensors).

---

### YAML Style (Block vs Flow)

- **Prefer block mappings** instead of inline *flow* mappings in ESPHome/Home Assistant YAML.
  - ✅ Preferred (block):
    ```yaml
    - script.execute:
        id: set_coil_off_safe
        target_id: relay_2_raw
    ```
  - ❌ Discouraged (inline/flow):
    ```yaml
    - script.execute: {id: set_coil_off_safe, target_id: "relay_2_raw"}
    ```
- **Why**: block style is easier to diff/review, avoids yamllint “braces” findings, and prevents formatter churn.
- **Exceptions**:
  - Short lists where flow improves clarity (e.g., a few pins) are acceptable.
  - **Do not modify existing RS-485 code** that already uses inline flow maps unless we are touching those lines for other reasons.
- **Linters/formatters**:
  - Prettier is the YAML formatter (default settings).
  - `.yamllint` is configured with `comments.min-spaces-from-content: 1` to match Prettier.
  - CI has a post-format step that removes spaces just inside `{}`/`[]` to keep inline maps (if they exist) lint-clean.

## Debugging Checklist

1. Log raw inputs (JSON payloads, serial frames, BLE packets) before changing code.
2. Validate against datasheet/API: units, ranges, required keys.
3. Minimal reproducible config; confirm baseline works.
4. Instrument: enable DEBUG logging; add `on_value` prints.
5. Check timing: throttles, debounces, delays.
6. Verify wiring: RS-485 termination, common ground, voltages.
7. Revert & bisect changes in small steps.

### Advanced Debugging Techniques

**Check Basic Gotchas First (Priority Order):**
1. Basic syntax errors (wrong keywords, indentation)
2. Version compatibility (deprecated syntax - check official docs for your HA version)
3. Missing dependencies (imports, entities, services)
4. Logic errors
5. Edge cases and error handling

Wrong order wastes time: checking edge cases → finding weird behavior → discovering syntax error that masked everything.

**Syntax Version Check (Do This Early):**
- Verify syntax against current HA version docs (not old forum posts)
- Check if `service:` vs `action:` for your HA version (2024+ uses `action:`)
- Confirm entity/service names haven't changed in recent releases
- Test example code from official docs first
- Don't assume syntax from 2+ years ago still works

**Verify Execution vs Reported Success:**
- Don't trust stdout/stderr or success indicators alone
- Check file timestamps: `stat /path/to/file | grep Modify`
- Verify entity state changes independently
- Look for side effects that prove execution occurred
- Example: Shell command reports success but file timestamp unchanged = didn't actually run

**Minimal Reproduction First:**
- Create simplest possible test case before debugging complex code
- If `echo "test" > /tmp/test.log` fails, your complex script will too
- Test with minimal dependencies and configuration
- Saves hours of debugging the wrong layer

**Test Context, Not Just Components:**
- Component works in Developer Tools ≠ works in automation
- Test the actual use case (script calling service, automation triggering)
- Don't assume isolation tests predict integration behavior
- Different execution contexts have different permissions and environments

---

## Adversarial Code Review Protocol

Use this protocol after generating any significant code (>20 lines) or before committing changes. This is **standard practice**, not rescue debugging.

### When to Apply

- After generating any new code >20 lines
- Before committing significant changes
- When adding new functionality
- As final step in code generation workflow

### Review Request Format

```
Put on your adversarial debugging hat and review [files] systematically.
Assume the code is broken until proven otherwise.

Check in priority order:
1. Syntax and version compatibility (basic gotchas first)
2. Required dependencies and imports
3. Entity/service existence and naming
4. Logic flow and state transitions
5. Edge cases (null, unavailable, empty, first-run, race conditions)
6. Error handling and failure modes
7. Resource cleanup (file handles, connections, memory leaks)

Rules:
- Forget prior assumptions each iteration
- State what you're checking before checking it
- Verify against official docs, not memory or old examples
- Test logic with concrete values, not abstract reasoning
- Iterate until no issues found for 2 consecutive passes
- If circling the same issues, stop and ask for guidance

Report each issue:
- Location: [file:line or section]
- Problem: [what's wrong and why it matters]
- Impact: [what breaks and under what conditions]
- Fix: [specific change with example code]
- Severity: [critical/high/medium/low]
```

### Why Adversarial Mindset

- Code author has blind spots about their own code
- Assuming it's broken forces checking "obvious" things
- Catches issues before they manifest as mysterious bugs
- Basic errors mask deeper problems

### Priority Order Matters

```
❌ Wrong: Check edge cases → find weird behavior → realize missing import
✓ Right: Check syntax → imports → entities → logic → edge cases → errors
```

### Stop Conditions (Prevent Infinite Loops)

- 2 consecutive clean passes (nothing found)
- Same issue found 3 times (structural problem, not fixable by iteration)
- 5 total iterations (diminishing returns, need different approach)

### Integration into Workflow

1. Generate code
2. Run adversarial review (this protocol)
3. Fix critical/high severity issues
4. Document medium/low issues as known limitations
5. Present code with issue summary

### What NOT to Skip

- Don't assume imports are correct because "we used them before"
- Don't skip entity checks because "it should exist"
- Don't trust that edge cases "probably won't happen"
- Don't assume error handling from one section applies elsewhere
- Don't rely on memory about syntax - check official docs

---

## Known Gotchas & Solutions

This section documents project-specific traps, their symptoms, root causes, and solutions. Add entries as issues are discovered and resolved.

### RS-485 Termination
**Symptom:** Intermittent Modbus timeouts, communication drops under load, relay commands occasionally ignored.

**Root Cause:** Missing or incorrect 120Ω termination resistor at one or both ends of RS-485 bus. Reflections cause signal integrity issues.

**Solution:** 
- Install 120Ω resistor across A/B at **both** ends (ESP32 RS-485 adapter + furthest device on bus)
- Verify with multimeter: ~60Ω across A-B with bus powered but idle
- Use proper RS-485 termination resistors, not generic resistors

**Prevention:** Check termination before adding new devices to bus.

### Manual Automation Trigger Testing
**Symptom:** Automation conditions appear to be ignored when testing manually via `automation.trigger` service. Winterization checks fail during testing even though they work correctly in production.

**Root Cause:** The `automation.trigger` service bypasses condition checks by default. This is intentional design to allow forcing automations to run during testing/debugging.

**Solution:**
```yaml
# ❌ Wrong - bypasses conditions
service: automation.trigger
data:
  entity_id: automation.notification_test_daily_email_send

# ✅ Correct - evaluates conditions
service: automation.trigger
data:
  entity_id: automation.notification_test_daily_email_send
  skip_condition: false
```

**Prevention:** 
- **Test in actual execution context:** Manual triggers behave differently than production triggers (time-based, state changes). Always verify conditions work in production context, not just manual testing.
- **Document testing methods:** When recording test results, note whether conditions were evaluated or bypassed. This prevents false confidence in test coverage.
- **Read service documentation:** Before using any HA service for testing, check official docs for parameters that affect behavior (like `skip_condition`).

**Impact:** Critical for validating any conditional automation behavior (winterization, error states, safety interlocks)

---

### External API Integration - Method Assumptions
**Symptom:** REST API calls fail with 405 Method Not Allowed or similar HTTP errors despite correct authentication and parameters.

**Root Cause:** Not all REST APIs follow standard conventions. Some APIs use GET requests with query parameters instead of POST with body data, contrary to typical REST patterns.

**Solution:**
```yaml
# ❌ Wrong - Assuming POST is standard
rest_command:
  send_notification:
    url: "https://api.example.com/send"
    method: POST
    payload:
      param1: "{{ value1 }}"
      param2: "{{ value2 }}"

# ✅ Correct - Verify actual API requirements
rest_command:
  send_notification:
    url: >
      https://api.example.com/send?param1={{ value1 | urlencode }}&param2={{ value2 | urlencode }}
    method: GET
```

**Prevention:**
- **Always read API documentation first:** Don't assume standard REST patterns. Check official docs for exact method (GET/POST), parameter format (query string vs body), and authentication approach before writing code.
- **Test with curl/browser first:** Validate API calls outside of Home Assistant before implementing in YAML. This isolates API issues from HA configuration issues.
- **Validate assumptions:** If documentation is unclear, test both GET and POST methods to determine which works. Don't rely on what "should" be standard.

**Impact:** Prevents complete failure of external integrations due to incorrect HTTP method assumptions

---

### DateTime Storage Format Consistency
**Symptom:** Automations with time-based triggers (e.g., "wait 24 hours after event") fail to fire, or template sensors comparing timestamps return unexpected results.

**Root Cause:** Home Assistant's `input_datetime` entities can store timestamps in multiple formats depending on how they're set. Inconsistent formats break comparisons, arithmetic, and trigger conditions.

**Solution:**
```yaml
# ❌ Wrong - Inconsistent datetime handling
- service: input_datetime.set_datetime
  data:
    datetime: "{{ now() }}"  # May store in various formats

# ✅ Correct - Always use ISO format
- service: input_datetime.set_datetime
  data:
    datetime: "{{ now().isoformat() }}"  # Consistent format

# ✅ Correct - Defensive reading
- condition: template
  value_template: >
    {{ states('input_datetime.last_event') not in ['unknown', 'unavailable', 'none'] }}
```

**Prevention:**
- **Enforce consistent formats:** When storing datetime values programmatically, always use a single format (ISO format via `.isoformat()` recommended). Document this standard in code comments.
- **Defensive reading:** Before comparing or calculating with stored datetimes, always check for 'unknown'/'unavailable'/'none' states. Use `as_datetime()` for conversions.
- **Test edge cases:** When implementing time-based logic, explicitly test: first-run (when datetime is 'unknown'), restart scenarios, and actual timeout periods. Don't assume format consistency.

**Impact:** Critical for any time-based automation logic (delays, timeouts, scheduling, rate limiting)

---

### ESPHome Entity ID Generation - Name vs ID Field
**Symptom:** Automations fail with "entity not found" errors. Documentation shows entity IDs that don't exist in Home Assistant. ESPHome entities appear to integrate successfully but aren't found by entity_id in automations.

**Root Cause:** Home Assistant entity IDs are generated from the ESPHome `name:` field, NOT the `id:` field. The `id:` field is only for internal ESPHome references (lambdas, scripts, etc.). This is standard ESPHome behavior, but easy to forget when reading YAML configs.

**Example:**
```yaml
# ESPHome configuration:
esphome:
  name: watering-system    # Device name (slugified to watering_system)

switch:
  - platform: template
    id: relay_pump_main              # ← Internal ESPHome reference only
    name: "Relay 1 - Main Pump"      # ← This generates the HA entity_id
```

**What you might expect:**
`switch.relay_pump_main` (based on `id:`)

**What actually gets created:**
`switch.watering_system_relay_1_main_pump` (based on device name + slugified `name:`)

**Pattern:**
```
{platform}.{device_name}_{slugified_name}
```

Where:
- `device_name` = ESPHome device name (slugified: hyphens → underscores)
- `slugified_name` = Entity name (spaces and special chars → underscores, lowercase)

**Real Examples from Watering System:**

| ESPHome Config | Home Assistant Entity |
|----------------|----------------------|
| `id: relay_pump_main`<br>`name: "Relay 1 - Main Pump"` | `switch.watering_system_relay_1_main_pump` |
| `id: low_water_level`<br>`name: "Low Water Level"` | `binary_sensor.watering_system_low_water_level` |
| `id: mppt_battery_voltage`<br>`name: "MPPT Battery Voltage"` | `sensor.watering_system_mppt_battery_voltage` |

**Solution:**
1. **Never assume entity IDs from ESPHome config** - always verify in Home Assistant
2. **Check actual entities** before writing automations:
   - Developer Tools → States → Search for device name
   - Or use template: `{{ states | selectattr('entity_id', 'search', 'watering_system') | map(attribute='entity_id') | list }}`
3. **Reference the entity mapping document:** `/docs/entity_reference.md` (single source of truth)
4. **Test automations** in Developer Tools → Services before deploying to YAML

**Prevention:**
- Added to "Before You Code" checklist: "Entity IDs verified against actual HA entities (not ESPHome config)"
- Use entity reference document for all automation code
- When creating new ESPHome entities, plan the `name:` field carefully (it becomes the entity_id)
- Search-and-replace in docs after any ESPHome name changes

**Impact:** 
- **CRITICAL** for safety automations (tank level, emergency stop)
- **HIGH** for state machine transitions (wrong entity = automation doesn't run)
- **MEDIUM** for dashboards (entity not found = blank cards)

**Historical Note:** This issue was discovered 2025-10-14 during AI collaboration bootcamp. All prior documentation assumed entity IDs matched ESPHome `id:` field. Comprehensive doc updates required across architecture.md, programming-notes.md, impl_roadmap.md, and test_scenarios.md.

---

**YAML Boolean Interpretation:**
- Unquoted strings `off`, `on`, `yes`, `no`, `true`, `false` are interpreted as booleans
- **Must quote in input_select options:** `"off"`, `"on"`, etc.
- Without quotes: `off` becomes boolean `False`, breaking state comparisons
- **Impact:** Automations checking `state == "off"` will fail silently
- **Prevention:** Always quote boolean-like strings in YAML lists
- **Example:** `options: ["off", "light", "normal", "heavy"]`
- Discovered during Phase 2.2 validation (2025-10-15)

---
## Source Discipline

* Hardware parts → datasheet → install manual → distributor page.
* Firmware/config → official README/wiki → example configs.
* Weather/API → API reference, schema, payloads, limits.

---

## Notification System Architecture

### Service Configuration

**WhatsApp (CallMeBot):**
- Endpoint: `https://api.callmebot.com/whatsapp.php`
- Method: GET request with query parameters
- Recipient Phone: stored in secrets.yaml as `!secret whatsapp_phone` (your German mobile number)
- API Key: stored in secrets.yaml as `!secret whatsapp_api_key`
- Character limit: ~1000 characters (URL-encoded)
- Note: CallMeBot registration number (+34 694 242 562) is not used in API calls

**Email (Gmail SMTP/IMAP):**
- SMTP: smtp.gmail.com:587 (TLS required)
- IMAP: imap.gmail.com:993 (SSL required)
- Username: stored in secrets.yaml as `!secret gmail_username`
- App Password: stored in secrets.yaml as `!secret gmail_app_password`
- Dedicated account with auto-forward to primary email

### Notification Tiers

**CRITICAL:** WhatsApp + Email (simultaneous)
**HIGH:** WhatsApp + Email (simultaneous)
**STANDARD:** WhatsApp only

### Notification Tiers

**CRITICAL:** WhatsApp + Email (simultaneous)
**HIGH:** WhatsApp + Email (simultaneous)
**STANDARD:** WhatsApp only

### Testing Strategy

**Daily (19:00):** Email self-send test
- Detects email system failures within 5 minutes
- Sets `notification_system_error = ON` if failed
- Checked in preflight (blocks watering if ON)

**Monthly (1st at 19:00):** WhatsApp confirmation test
- User confirms via dashboard button within 24h
- Failure triggers CRITICAL via Email (24h delayed)

**De-winterization:** Both channels tested immediately
- Both must confirm before automatic watering enabled

### Winterization Behavior

**When `input_boolean.system_winterized = ON`:**
- All notification automations disabled
- All watering automations disabled
- Daily/monthly tests skipped

**When switched OFF:**
- De-winterization test triggers immediately
- System remains in manual mode until tests confirmed

### Silent Failure Prevention

**REST API Errors:**
- Logged immediately to `sensor.last_notification_error`
- Failed channel → notification sent via alternate channel

**Daily Email Test:**
- Self-send at 19:00, IMAP monitors for arrival
- 5-minute timeout → triggers `notification_system_error`
- Preflight check blocks watering if error active

**User Confirmation Required:**
- Monthly WhatsApp test
- De-winterization tests
- Unconfirmed test = failed test (after 24h)

### Implementation Notes

**Completed (2025-10-13):**
- All core notification functionality operational
- Daily self-test running automatically at 19:00
- Monthly test scheduled for 1st of each month at 19:00
- De-winterization testing validated
- Winterization blocking confirmed working

**Pending Integration (blocked on Phases 4-5):**
- Safety automation integration (tank low, comms lost, runtime exceeded)
- Watering summary generation (post_cycle_relief state)
- Preflight check error state handling

**Testing Limitations:**
- Time-based delays (12h reminder, 24h timeouts) verified via code review
- Actual timeout periods not tested due to time requirements
- Can be validated in production as monthly/de-winterization tests occur naturally

**Known Issues:**
- None identified during testing
- Manual trigger testing requires `skip_condition: false` (documented in Known Gotchas)

---

## Architecture Decision Records (ADRs)

This section captures **why** key architectural choices were made, not just what was implemented. Each ADR includes context, the decision, rationale, and consequences.

### ADR-001: All Logic in Home Assistant (2025-09-15)
**Context:** Need to decide where watering automation logic should live (ESPHome firmware vs Home Assistant automations).

**Decision:** All decision-making logic lives in Home Assistant. ESP32 is a "dumb" sensor/relay interface only.

**Rationale:**
- Easier debugging (HA logs vs serial console)
- No firmware recompilation for logic changes
- Rich templating and weather API integration in HA
- Can test automations without hardware
- Separation of concerns: ESPHome = hardware abstraction, HA = business logic

**Consequences:**
- Requires reliable HA ↔ ESP32 communication (mitigated by Modbus watchdog)
- HA restart temporarily disables automation (acceptable for non-critical irrigation)
- Cannot run watering if HA is down (acceptable trade-off)

---

### ADR-002: State Machine with 11 States (2025-10-01)
**Context:** Need to orchestrate complex watering sequences with plain watering, fertigation phases, safety checks, and error handling.

**Decision:** Implement a master state machine with 11 discrete states controlled by `input_select.watering_system_state`.

**Rationale:**
- Explicit state visibility in UI/logs
- Clear transition logic (one automation watches state changes)
- Easy to pause/resume/override
- Error states isolate failures without breaking system
- Testable state-by-state

**Consequences:**
- More verbose than a single monolithic script
- Requires discipline to keep state transitions clean
- State persistence across HA restarts needed (input_select handles this)

---

### ADR-003: Numeric Zone IDs with Friendly Names (2025-10-04)
**Context:** Need stable entity IDs for zones while allowing flexible naming (crop types may change).

**Decision:** All zone entity IDs use numeric format (`zone_1`, `zone_2`, etc.). Friendly names applied via `name:` attribute.

**Rationale:**
- Entity IDs are stable even if crops change (raspberries → strawberries)
- Automations don't break when renaming zones
- Consistent pattern across all 4 zones
- Easier to template/loop in scripts (`zone_{{n}}`)

**Consequences:**
- Less readable entity IDs in raw YAML
- Must remember to set friendly names consistently
- Dashboard cards need explicit friendly names

---

### ADR-004: Weather-Based Program Uses Average Daily High (2025-10-04)
**Context:** Need to determine watering program (off/light/normal/heavy) based on recent temperature. Choice between average temperature, average daily high, or growing degree days.

**Decision:** Use average of daily high temperatures over last 3 days (`sensor.brightsky_temp_avg_high_3day`).

**Rationale:**
- Berry crops most stressed by daytime heat, not overnight temps
- Daily high better indicator of peak stress than 24h average
- Simpler than GDD (growing degree days) for initial implementation
- Matches how humans think about "how hot has it been?"

**Consequences:**
- Ignores overnight recovery (may over-water in mild climates)
- Doesn't account for crop-specific base temperatures
- Can refine to GDD in future if needed

---

### ADR-005: No Hardware Pump Cycle Counting (2025-10-04)
**Context:** Original plan included GPIO32 pump activity sensor with pulse counter for tracking pump cycles and runtime.

**Decision:** Remove hardware-based pump monitoring. Use relay state duration from Home Assistant history instead.

**Rationale:**
- HA natively tracks switch on/off times via `history_stats`
- Eliminates GPIO32 wiring and complexity
- Pulse counter prone to noise/false triggers
- Relay state is ground truth (if relay is on, pump is on)
- Simpler hardware = fewer failure points

**Consequences:**
- Runtime stats only available when HA is running (acceptable)
- Cannot detect pump failure (relay on but pump not running) without flow sensor
- Flow sensor monitoring deferred to Phase 4

---

### ADR-006: Dual-Channel Notifications (WhatsApp + Email) (2025-10-09)

**Context:** Need reliable remote notifications for safety-critical watering system. Initially considered SMS + WhatsApp + Email, but Sipgate (German free SMS provider) now requires business registration.

**Decision:** Use WhatsApp (CallMeBot) + Email (Gmail) as dual-channel notification system. No SMS.

**Rationale:**
- WhatsApp delivery is instant (faster than SMS)
- WhatsApp shows read receipts (delivery confirmation)
- Email tested daily via self-send (catches failures quickly)
- Both services are truly free (no hidden costs or vendor lock-in)
- Dual redundancy sufficient for safety-critical alerts
- SMS alternatives either paid (€0.75/month minimum) or unreliable

**Consequences:**
- Requires smartphone with WhatsApp installed
- Requires internet connectivity (but all remote notification methods do)
- WhatsApp API is one-way (no replies), but not needed for alerts
- Email self-test adds daily automation complexity
- Daily email test provides better failure detection than monthly SMS test would have
- Both channels failing simultaneously = extremely unlikely scenario

**Alternative Considered:**
- Twilio SMS at €0.75/month for triple redundancy
- Rejected due to: minimal safety benefit, ongoing cost, vendor dependency

---

### ADR Template (for future decisions)

## System Architecture

**Full Document:** [architecture.md](https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/architecture.md)

### Overview

The watering system uses a **hybrid state machine architecture**:
- Master state machine handles sequential operations (watering/fertigation sequences)
- Independent safety automations run in parallel (tank level, communications watchdog)
- All logic in Home Assistant; ESP32 is sensor/command relay only

### Core States

**Primary Flow:**
`idle` → `window_check` → `preflight_check` → `watering_plain` or `fert_prep` → `fert_dose_phase1` → `fert_dose_phase2` → `post_cycle_relief` → `idle`

**Error States:**
- `error_tank_low_low` - Tank empty, system halted
- `error_comms_lost` - ESP32 communication failure
- `manual_override` - User control active

### Configuration Philosophy

**All parameters configurable via Home Assistant UI:**
- Per-zone settings: friendly names, base runtimes
- Per-phase settings: 5 growth phases per zone with configurable names and weather thresholds
- Fertigation: doses in mL (backend calculates mL/min based on runtime)
- Notification system: Winterization control, test confirmations, error tracking
- No YAML editing required for normal operation

**Total UI Helpers:** ~218 (was ~210)
- Watering system: ~210 helpers
- Notification system: 8 new helpers (5 booleans, 3 datetimes)
  - Note: Template sensors and text inputs are derived/storage, not counted in UI helper total

### Zone & Phase Structure

**Zones:** `zone_1` through `zone_4` (user-named via `input_text.zone_{id}_friendly_name`)

**Phases:** 5 configurable phases per zone
- Example: Raspberries → "Early Veg", "Bloom", "Fruit", "Late Veg", "Dormant"
- Each phase has independent weather thresholds (rain 24h/72h, temperature)
- Programs selected per-zone: off/light/normal/heavy

### Scheduling

**Time-Based with Condition Evaluation:**
- Watering cycles every N days (configurable)
- Morning and/or evening check windows
- Within windows: system evaluates weather conditions and selects per-zone programs
- Fertigation runs every N days (separate schedule)

### Fertigation Logic

**Split-Dose Strategy (Normal/Heavy programs):**
1. Phase 1: 50% fertilizer dose + flush
2. Phase 2: 50% fertilizer dose + remaining watering
3. Post-flush: Clean water flush (5 min)

**Single-Dose Strategy (Light program):**
1. Phase 1: 100% fertilizer dose + partial watering
2. Phase 2: Clean water flush only (5 min)

### Safety Interlocks

**Hardware Level (ESPHome):**
- Relay auto-off timers (120 min max)
- `ALWAYS_OFF` restore mode
- 24V cabinet enable/disable guards Modbus traffic

**Automation Level (Home Assistant):**
- Tank level monitor (aborts on Low-Low)
- Modbus communication watchdog (10s timeout)
- Zone runtime limits (configurable max per zone)
- Emergency stop script (force to idle, kill all valves/pumps)

### File Structure

**ESPHome Packages:**
- `modbus_rs485.yaml` - Relay board control
- `inputs.yaml` - Float switch sensors
- `victron_ble.yaml` - Solar/battery monitoring

**Home Assistant Packages:**
- `watering_state_machine.yaml` - Master state controller
- `watering_scripts.yaml` - State transition scripts
- `zone_control.yaml` - Zone operation scripts
- `fert_control.yaml` - RS-485 dosing pump control
- `watering_safety.yaml` - Independent safety monitors
- `sensor_scheduler.yaml` - Soil sensor reading (future)

### Key Design Decisions

1. **Per-zone program selection** - Each zone independently evaluates weather and selects off/light/normal/heavy
2. **User-selectable sequencing** - Parallel (multiple zones) or sequential (one at a time)
3. **Calendar-based fertigation** - Predictable schedule, watering program affects execution
4. **UI-first configuration** - All adjustable parameters as input helpers, no YAML editing

---

**For detailed state diagrams, complete helper definitions, safety logic, and testing procedures, see the full architecture document.**

---

## Repo & Files (structure)

### Current Home Assistant Structure

```
├── packages/                         # Home Assistant automation packages
│   ├── notification/
│   │   ├── helpers.yaml              # Notification controls
│   │   ├── config.yaml               # REST commands, IMAP config
│   │   ├── scripts.yaml              # Tiered notification sending
│   │   └── tests.yaml                # Daily/monthly/de-winterization tests
│   ├── weather/
│   │   └── dwd_brightsky.yaml        # Weather integration (DWD API)
│   ├── watering_helpers/
│   │   ├── system_helpers.yaml       # State, schedule, safety config
│   │   ├── zone_helpers.yaml         # Zone programs, thresholds
│   │   └── fert_helpers.yaml         # Dosing rates, calibration
│   ├── watering_scripts/             # (Planned - Phase 3)
│   │   ├── zone_scripts.yaml         # Zone operations
│   │   ├── pump_scripts.yaml         # Main pump control
│   │   └── fert_scripts.yaml         # Fertilizer dosing pumps
│   ├── watering_state/               # (Planned - Phase 4)
│   │   ├── state_machine.yaml        # Master state controller
│   │   └── state_scripts.yaml        # State transition scripts
│   ├── watering_safety/              # (Planned - Phase 5)
│   │   ├── automations.yaml          # Safety monitors
│   │   └── scripts.yaml              # Emergency procedures
│   ├── watering_sensors/             # (Future - Phase 3)
│   │   └── scheduler.yaml            # Soil sensor reading
│   └── watering_ui/                  # (Future - Phase 7)
│       └── dashboard.yaml            # Dashboard configuration
```

### Public Repository Structure (GitHub)

```
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
│   │   ├── watering_scripts/         # (Planned - Phase 3)
│   │   │   ├── zone_scripts.yaml     # Zone operations
│   │   │   ├── pump_scripts.yaml     # Main pump control
│   │   │   └── fert_scripts.yaml     # Fertilizer dosing pumps
│   │   ├── watering_state/           # (Planned - Phase 4)
│   │   │   ├── state_machine.yaml    # Master state controller
│   │   │   └── state_scripts.yaml    # State transition scripts
│   │   ├── watering_safety/          # (Planned - Phase 5)
│   │   │   ├── automations.yaml      # Safety monitors
│   │   │   └── scripts.yaml          # Emergency procedures
│   │   ├── watering_sensors/         # (Future - Phase 3)
│   │   │   └── scheduler.yaml        # Soil sensor reading
│   │   └── watering_ui/              # (Future - Phase 7)
│   │       └── dashboard.yaml        # Dashboard configuration
│   ├── scripts/
│   │   └── pull_public_repo.sh       # Sync script for repo updates
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
```

### Key Notes:

ESPHome packages: All modular configs in esphome/packages/
HA packages: Feature-based subfolder organization in home-assistant/packages/
Vendored component: victron_ble in esphome/components/ (GPL-3.0 licensed)
Secrets: Never committed; only .example.yaml templates in public repo
Repo sync: pull_public_repo.sh syncs from GitHub to local HA system

### Implementation Status

**For cannonical implementation tracking, see:**
- 📊 **[impl_roadmap.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/impl_roadmap.md)** - Phase-by-phase checklist with status, blockers, and test plans
- 🧪 **[test_scenarios.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/test_scenarios.md)** - Concrete test cases for validation

**Legacy Files:**
- `automations.yaml` - Standard HA automations file
- `scripts.yaml` - Standard HA scripts file
- These may contain existing non-watering automations
---

## Version Control Practices

* GitHub repo pair:

  * **Private**: full configs + real secrets (ignored).
  * **Public**: sanitized mirror, canonical docs.
* Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
* Keep `main` stable; feature branches for changes.
* Tag stable checkpoints (e.g., v0.1.0).
* CI: yamllint, gitleaks.
* `.gitignore` includes all secrets + generated files.

---

## Licensing

* Repository is dual-licensed:
  - MIT license applies to project files (YAML configs, docs, scripts).
  - GPL-3.0 applies to the vendored component in `esphome/components/victron_ble/`.
* Vendored code must include `LICENSE.GPL-3.0` (copied from Fabian-Schmidt’s repo).
* Top-level `LICENSE` should note this dual-license structure.
* README should attribute Fabian-Schmidt’s [esphome-victron_ble](https://github.com/fabian-schmidt/esphome-victron_ble).

---

## Dependency Versions & Compatibility

This section tracks component versions that are known to work together. Update dates when configurations are verified after upgrades.

### Core Platform Versions

| Component | Version | Last Verified | Notes |
|-----------|---------|---------------|-------|
| Home Assistant Core | 2024.10.x | 2025-10-04 | Requires Python 3.11+ |
| ESPHome | 2024.10.x | 2025-10-04 | Firmware compiler |
| ESP32 Framework | arduino-2.0.x | 2025-10-04 | Via ESPHome platform config |

### Hardware & Protocols

| Component | Version/Spec | Last Verified | Notes |
|-----------|--------------|---------------|-------|
| ESP32-DEVKITC-VE | Rev 1 | 2025-10-04 | Espressif official devkit |
| Modbus RTU | Standard | 2025-10-04 | 9600 8N1, addresses 0x01-0x07 |
| RS-485 | EIA-485 | 2025-10-04 | 120Ω termination both ends |

### ESPHome Components

| Component | Version | Last Verified | Notes |
|-----------|---------|---------------|-------|
| `uart` | Built-in | 2025-10-04 | TX=GPIO25, RX=GPIO26 |
| `modbus` | Built-in | 2025-10-04 | UART-based controller |
| `modbus_controller` | Built-in | 2025-10-04 | Multiple device support |
| `victron_ble` | 2024-08-15 | 2025-10-04 | Vendored from Fabian-Schmidt repo |

### External APIs

| Service | Endpoint Version | Last Verified | Notes |
|---------|------------------|---------------|-------|
| Brightsky API | v2 | 2025-10-04 | DWD weather data, no auth required |
| Home Assistant REST API | HA version | 2025-10-04 | Local API token required |

### Python Libraries (if applicable)

| Library | Version | Last Verified | Notes |
|---------|---------|---------------|-------|
| `pymodbus` | 3.x | 2025-10-04 | If using HA Modbus integration |
| `bleak` | Latest | 2025-10-04 | Bluetooth LE (via HA) |

---

### Update Process

**When to update this table:**
- After successful Home Assistant or ESPHome upgrade
- After adding new hardware or external components
- After discovering version-specific bugs or compatibility issues
- Minimum quarterly review (every 3 months)

**How to verify:**
1. Check installed versions: HA Settings → System → About
2. ESPHome version: `esphome version`
3. Test critical paths: manual relay control, sensor reads, weather API
4. Update "Last Verified" column with current date

**Breaking changes to watch:**
- ESPHome YAML schema changes (check release notes)
- Home Assistant automation syntax deprecations
- External API endpoint changes (Brightsky)
- Modbus library updates (register addressing changes)

---

## REPOSITORY STRUCTURE & AUTO-LINKING

**Public Repository:** `https://github.com/robertmacbridehart-coder/watering-system`

**Raw File Base URL:** `https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/`

**Key Documents:**
- Programming Notes: `/docs/programming-notes.md`
- Architecture Document: `/docs/architecture.md`
- ESPHome Packages: `/esphome/packages/`
- Home Assistant Packages: `/home-assistant/packages/`

**When user references a file path, automatically construct the raw URL:**
- User says: "Check `/esphome/packages/modbus_rs485.yaml`"
- You fetch: `https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/esphome/packages/modbus_rs485.yaml`

---

## Home Assistant OS Limitations

### Shell Commands (Non-Functional in HAOS)

**Status:** Broken in automation contexts on Home Assistant OS  
**Confirmed:** 2025-10-05 on HAOS 16.2, Core 2025.9.4

**Symptoms:**
- Shell commands appear to work when called via Developer Tools
- Same commands fail silently when called from scripts/automations
- Returns cached output from previous executions
- File timestamps prove script didn't actually run

**Lessons Learned:**
- Don't trust stdout/stderr output - verify file system changes
- Test in actual automation context, not just Developer Tools
- Check file timestamps: `stat /path/to/file | grep Modify`
- HAOS containerization prevents reliable shell execution from automations

**Workarounds:**
- Manual execution via SSH (most reliable)
- Node-RED add-on (~45 min setup)
- Custom integration (~10+ hours development)

**Recommendation:**
Do not use shell_command integration in HAOS for any automation. Manual execution or proper integrations only.

**Full incident report:**
https://github.com/robertmacbridehart-coder/watering-system-private/blob/main/docs/repo_pull_incident_report.md

---

## Change Log

* **2025-09-23**: Fixed formatting duplication in Workflow Guardrails (Safety). Added explicit repo-reference rule. Preparing for copy-paste into public repo.
* **2025-09-16**: Repo mirror set up (private → public with sanitizer). Public `programming-notes.md` is now canonical.
* **2025-09-15**: Standardized title to “Watering System – Programming Notes (Master)” across instructions. Added Adaptation Policy to instructions. Created master notes with standards, RS-485 rules, ESPHome snippets, debugging checklist, repo structure.
* **2025-09-25**:
  - **Project Instructions**: Clarified notes loading order (public repo → cached → not loaded). Added requirement to explicitly state when repo code cannot be loaded. Added rule to always propose a Change Log entry whenever code or programming notes change.
  - **ESPHome Refactor**: Adopted packages structure; base YAML remains minimal.
    - New packages:
      - `esphome/packages/modbus_rs485.yaml` (UART, Modbus hub, relay coils)
      - `esphome/packages/inputs.yaml` (Low/Low-Low GPIO level inputs)
      - `esphome/packages/victron_ble.yaml` (SmartSolar BLE sensors)
  - **ESP32 UART + RS-485**: Pins changed **TX=GPIO25, RX=GPIO26**; 9600 8N1; `rx_buffer_size: 512`; `send_wait_time: 8ms`.
    - Relays: `restore_mode: ALWAYS_OFF`; `auto_off: 120min`.
    - Inputs: GPIO34/35 with `INPUT_PULLUP`, `inverted: true`, `delayed_off: 30s`, `debounce: 100ms`.
  - **Victron BLE (SmartSolar)**: Decided on **vendoring** the component.
    - Vendored code path: `esphome/components/victron_ble/` (no `external_components:` when vendored).
    - Root YAML must enable `esp32_ble_tracker:`.
    - Credentials in `secrets.yaml`: `victron_smartsolar_mac`, `victron_smartsolar_bindkey`.
    - Normalized entity names to **“MPPT …”** scheme for easier filtering.
  - **Secrets Template**: Added Victron placeholders to `secrets.example.yaml`.
  - **Licensing**: Dual-license structure documented.
    - MIT for project files (YAML, docs, scripts).
    - GPL-3.0 for vendored `esphome/components/victron_ble/*`; include `LICENSE.GPL-3.0` in that folder and note GPL in top-level LICENSE + README attribution to Fabian-Schmidt.
* **2025-09-25**
  - Docs: add “YAML Style (Block vs Flow)” — use block mappings for new ESPHome/HA configs; keep existing RS-485 code unchanged.
  - Linters: align `.yamllint` with Prettier (`comments.min-spaces-from-content: 1`).
  - CI: confirm brace/Bracket normalization step runs after Prettier.
* **2025-10-01**
  - Added archetecture reference
  - Added instructions for Claude
  - Added repository structure and auto-linking
* **2025-10-04**:
  - **Removed**: GPIO32 pump activity sensor, pulse counter, and integration sensor for pump runtime tracking (hardware-based cycle counting no longer needed)
  - **Created**: `docs/impl_roadmap.md` - Implementation roadmap tracking status, build order, and testing for all system components
  - **Created**: `docs/test-scenarios.md` - 25 concrete test cases organized in 8 categories with pass/fail tracking
  - **Standardized**: All zone entity IDs now use numeric format (zone_1, zone_2, zone_3, zone_4); friendly names applied via `name:` attribute
  - **Weather Integration**: Confirmed `home-assistant/packages/dwd_brightsky.yaml` exists with rain_24h and rain_72h sensors
  - **Planned Sensors**: Added brightsky_temp_high_yesterday and brightsky_temp_avg_high_3day to roadmap (will use average of daily high temps for watering decisions)
  - **Decision**: Weather-based program logic will use average daily high temperature (3-day) rather than average temperature to better capture daytime heat stress
  - **Documentation Enhancements**: Added Architecture Decision Records, Known Gotchas & Solutions, Dependency Versions & Compatibility, and Before You Code Checklist sections
  - **Project Instructions**: Updated to reference impl_roadmap.md and test-scenarios.md; added "Before You Code" checklist enforcement; enhanced safety requirements
* **2025-10-04**:
  - **Canonical Documents Section**: Added new section after "Workflow Guardrails" 
    - Documents the four-document ecosystem (programming-notes, architecture, impl_roadmap, test_scenarios)
    - Emphasizes programming-notes as repository of tribal knowledge (the "why" behind decisions)
    - Provides raw GitHub URLs for loading documents one-at-a-time (prevents chat length errors)
    - Clarifies that all four documents should be loaded for coding/implementation work
    - Shows document hierarchy and update triggers for each
  - **File Structure Cleanup**: Renamed placeholder package files to match architecture v1.0
    - `watering_schedule.yaml` → `watering_state_machine.yaml`
    - `fertilizer.yaml` → `fert_control.yaml`
    - `safety.yaml` → `watering_safety.yaml`
    - `ui.yaml` → `watering_ui.yaml`
    - All files now use consistent `watering_*` prefix
    - Identified two additional packages: `watering_scripts.yaml`, `zone_control.yaml` (not yet created)
  - **Repo Structure**: Updated "Repo & Files (structure)" to reflect actual `/config` folder layout
    - Removed redundant mention of programming-notes.md (now covered in Canonical Documents section)
    - Implementation status tracking moved to impl_roadmap.md as single source of truth
* **2025-10-05**:
  - **Repo Pull Automation**: Investigated automated GitHub repo pulling via Home Assistant UI
  - Confirmed shell_command integration is non-functional in HAOS automation contexts
  - Documented 4-hour debugging session in [incident report](https://github.com/robertmacbridehart-coder/watering-system-private/blob/main/docs/repo_pull_incident_report.md)
  - Implemented manual pull workflow with version monitoring sensors
  - **Programming Notes Updates**:
    - Added Advanced Debugging Techniques section
    - Added Adversarial Code Review Protocol as standard practice
    - Documented HAOS shell_command limitations with workarounds
* **2025-10-05**:
  - **modbus_rs485.yaml**: Complete rewrite - fixed timer management, renamed switches to `relay_*` convention, replaced parameterized scripts with 48 individual scripts
  - **inputs.yaml**: Changed GPIO34/35 to GPIO32/33 (have internal pull-ups), corrected filter syntax (`delayed_on_off` not `debounce`), removed pump monitoring
  - **secrets.example.yaml**: Moved to archive/, fixed self-referencing format
  - **Victron BLE**: Added `external_components:` block for vendored component
  - **Documentation**: Updated zone naming to generic (zone_1, zone_2, zone_3, zone_4), documented relay naming convention, added icons
* **2025-10-09**:
  - **Notification System Architecture**: Added dual-channel (WhatsApp + Email) notification strategy
    - CallMeBot WhatsApp integration (API key: 4691969, phone: +34 694 242 562)
    - Gmail SMTP/IMAP integration (dedicated account: bob.m.hart.ha@gmail.com)
    - Tiered notification approach (Critical/High/Standard)
    - Daily email self-test at 19:00 with failure detection
    - Monthly WhatsApp test on 1st at 19:00 with user confirmation
    - De-winterization testing protocol
    - Winterization support (disables all notifications when system powered down)
    - Silent failure prevention via multi-layer testing
  - **ADR-006**: Documented decision to use WhatsApp + Email (no SMS) with rationale
  - **Service Registration**: Completed CallMeBot and Gmail setup with credentials documented
  - **Security**: Dedicated Gmail account with auto-forward isolates notification system from primary email
* **2025-10-08**:
  - **Project Instructions for Claude**: Major revision based on Week 1 AI Collaboration Bootcamp learnings
    - Added mandatory "Before You Code" checklist enforcement (7 items must be completed before code generation)
    - Added explicit "No Assumptions" protocol (verify entity IDs, hardware status, requirements against docs)
    - Added Context/Constraints/Success Criteria framework requirement for complex requests
    - Added red flag self-check (overconfidence, TODOs, untested assumptions)
    - Added impl_roadmap.md to startup document fetch (check for blockers before implementation)
    - Clarified that programming-notes.md instructions are mandatory, not guidance
    - Added requirement to confirm checklist completion before generating ANY code
    - Streamlined instructions while adding verification rigor (496 words, was ~150)
    - **Rationale**: Prevent hallucination, reduce assumptions, enforce systematic requirements verification, catch bad approaches before code generation
* **2025-10-13**:
  - **Notification System (Phase 9)**: Dual-channel implementation complete (WhatsApp + Email)
    - Created 4 package files: notification_helpers, notification_config, notification_scripts, notification_tests
    - Daily email self-test (19:00), monthly WhatsApp test (1st at 19:00), de-winterization testing
    - Winterization support: all notifications disabled when system powered down
  - **Notification Testing (Phase 10)**: 24/27 tests passed
    - Service integration, daily/monthly tests, de-winterization, tier validation, winterization behavior
    - Integration tests blocked pending watering system (Phases 4-5)
  - **Known Gotchas Added**: 
    - Manual automation triggers require `skip_condition: false` to evaluate conditions
    - CallMeBot WhatsApp API requires GET method (not POST)
    - Home Assistant datetime format inconsistencies require `.isoformat()` for consistency
  - **Documentation**: Updated test_scenarios.md (Section 9), impl_roadmap.md (Phases 9-10)
- **2025-10-14:**
  - **Entity ID Documentation Corrections** (Critical Issue Resolved)
    - **Discovery:** ESPHome entities in HA use `name:` field, not `id:` field for entity_id generation
    - **Pattern:** All ESPHome entities: `{platform}.watering_system_{slugified_name}`
    - **Files Updated:**
      - Created `/docs/entity_reference.md` (27 entities documented)
      - `architecture.md`: Sections 5.1A, 5.2, 5.3, 7.1, 7.2
      - `test_scenarios.md`: Tests 1.3, 1.4, 2.1, 2.2, 2.3 + reference table
      - `impl_roadmap.md`: Sections 1.2, 5.1, 8.2, Known Issues, Change Log
      - `programming-notes.md`: Relay Naming, ESPHome Snippets, Known Gotchas, Checklist, Project Instructions
    - **Key Examples:**
      - `id: relay_pump_main` → `switch.watering_system_relay_1_main_pump`
      - `id: low_water_level` → `binary_sensor.watering_system_low_water_level`
    - **Prevention:** Added to "Before You Code" checklist: verify entity IDs in HA before use
    - **Impact:** Safety automations, state machine, all tests required entity ID corrections
    - **Root Cause:** Documentation written from ESPHome perspective without verifying HA integration behavior
    - **Discovered:** During AI collaboration bootcamp Week 1 (2025-10-14)
- **2025-15:**
  - **Completed** Implementation phase 2.1-2.3
  - **Files Created and Verified:**
    - home-assistant/packages/watering_config_helpers.yaml
    - home-assistant/packages/watering_zone_helpers.yaml
    - home-assistant/packages/watering_fert_helpers.yaml
  - **Known Gotcha:** When "off" should be a string not a state, must include quotes
  - **Documenation Updated:** relevent reference documentaion updated.
  - **Updated Claude Instructions** documents and repo loaded into project knowledge
* **2025-10-16**:
  - **Package Reorganization**: Implemented feature-based subfolder structure for Home Assistant packages
    - **Reorganized existing files** into subfolders:
      - `notification/` - 4 files (helpers, config, scripts, tests)
      - `weather/` - 1 file (dwd_brightsky.yaml)
      - `watering_helpers/` - 3 files (system, zone, fert helpers)
    - **Planned structure** for future implementation:
      - `watering_scripts/` - All operational scripts (Phase 3)
      - `watering_state/` - State machine logic (Phase 4)
      - `watering_safety/` - Safety systems (Phase 5)
      - `watering_sensors/` - Soil sensor management (Phase 3)
      - `watering_ui/` - Dashboard configuration (Phase 7)
    - **Migration**: Private repo → sanitize.py → public repo → pull_public_repo.sh → HA system
    - **Verification**: All 218+ entities loaded correctly, notification system tested
    - **Entity IDs**: No changes (file moves only, zero functional impact)
    - **Documentation updates**: 
      - architecture.md v1.2.4 - Section 6 file paths updated
      - impl_roadmap.md - File structure table reorganized, Phase 3-5 paths updated
      - programming-notes.md - File structure and repo tree updated
    - **Note**: repo_pull.yaml intentionally excluded (not tracked in GitHub)
---

## Project Instructions (for ChatGPT and Claude)

```
PROJECT: Watering System — Working Instructions

GOAL
Build ESPHome + Home Assistant automations for the irrigation system with high reliability, traceability, and speed.

ADAPTATION POLICY
The assistant will proactively suggest improvements to these instructions whenever it would enhance workflow or efficiency. Upon user approval, the assistant will update this pinned section and reflect changes in the Programming Notes.

ALWAYS DO THIS AT THE START OF EVERY RELEVANT THREAD
1) Load context documents in this order:
   - Programming notes: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/programming-notes.md
   - Architecture: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/architecture.md
   - Implementation roadmap: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/docs/impl_roadmap.md
   - If public repo is not accessible, try cached versions
   - If neither is available, return `Notes status: not loaded`

2) Before recommending or generating any code:
   - Review relevant documentation (architecture.md, programming-notes.md, impl_roadmap.md) to understand context
   - Check the public repo for related existing code to maintain consistency
   - Review impl_roadmap.md File Ownership table to verify what exists vs. what's planned
   - If unable to load code from repo, attempt using raw links (pattern: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/[path])
   - If unable to load, explicitly state that

3) Post confirmation at the top of your first reply:
   - `Notes status: loaded` (include last change-log date if visible), `cached version loaded (last change <date>)`, or `not loaded`
   - `Architecture status: loaded` or `not loaded`
   - `Roadmap status: loaded` or `not loaded`
   - `Scope:` (module focus for this thread)

4) State where code changes belong (ESPHome vs HA packages path, reference File Ownership table).

5) Follow the "Before You Code" checklist from programming-notes.md:
   - Verify complete understanding (not just first sentence)
   - Review documentation AND existing code
   - Confirm file placement and system design fit
   - Consider safety implications
   - Plan testing strategy
   - Have rollback plan
   - Identify documentation impact
   - **Reason from facts only, not assumptions** - if uncertain, ASK

DURING THE THREAD
- Put any non-trivial code/config in Artifacts (not inline chat). Keep chat for rationale and diffs.
- Prefer small, testable diffs over large dumps.
- Always propose approach BEFORE writing code - describe what, where, and why, then wait for approval.
- Cite primary sources for all new parts/configs (datasheets, official docs, API references).
- When information might be recent or niche, search and cite the current official source.
- Use block-style YAML mappings (not inline flow style) for new configurations.
- Check impl_roadmap.md status before proposing work to avoid duplicates.

DEBUGGING POLICY (USE FIRST, NOT LAST)
1) Log first: capture raw payloads/serial/Modbus/BLE before guessing.
2) Validate against spec/schema (units, ranges, required keys).
3) Minimal reproducible config; then layer complexity.
4) Instrument temporarily (logger DEBUG, prints, on_value hooks).
5) Check timing (throttles, debounces, delays) and physical layer (termination, 0V/COM, power).
6) Reference Known Gotchas section in programming-notes.md for common issues.

END OF THREAD
1) Update "programming-notes.md": decisions, authoritative snippets, open items, change log.
2) If we made a significant architectural decision, propose an ADR entry (assistant will suggest, user approves).
3) Update impl_roadmap.md: check off completed items, update status, add notes.
4) Update test-scenarios.md: if tests were run, record results.
5) Provide a diff-style summary of file changes or clearly marked file replacements.
6) List follow-ups as bullet points (these become repo Issues later).
7) Always suggest Change Log entries for programming-notes.md and impl_roadmap.md when modified.

CODE & CONFIG STANDARDS
- YAML: snake_case ids; Title Case friendly names; add icons where helpful.
- Zone references: use numeric IDs (zone_1, zone_2, zone_3, zone_4) in entity_ids; friendly names in name: attribute.
- Relays default ALWAYS_OFF; add safety auto_off for long-open valves (120min).
- Binary sensors: debounce ≥50 ms; use delayed_off if noisy.
- Secrets in secrets.yaml (never paste tokens/keys; never commit secrets).
- Prefer HA packages and ESPHome packages for modularity.
- Block-style YAML mappings preferred over inline flow style.
- Complete, working code only - no placeholders, no TODO comments.

RS-485 / MODBUS DEFAULTS
- Topology: linear bus; short stubs only. Termination 120 Ω at both ends (ESP32 adapter + pump block).
- Common reference: share 0 V/COM; shield to earth at master only.
- 9600 8N1, send_wait_time: 8ms, rx_buffer_size: 512.
- DFRobot SEN0600 address via register 0x07D0 (2000), range 1–247; power only one sensor when changing.
- UART2: TX=GPIO25, RX=GPIO26.

SAFETY (CRITICAL)
- Do not enable pump/valve actuation without interlocks and explicit user action.
- Default relays OFF on boot (restore_mode: ALWAYS_OFF).
- Maintain dry-run/low-tank lockouts and clear alarms.
- All safety interlocks must be independent automations (not part of state machine).
- Test safety interlocks BEFORE enabling automatic operation.

VERSION CONTROL (RECOMMENDED)
- Use private repo + GitHub Desktop (full configs).
- Public sanitized repo with mirror workflow.
- Structure: /docs, /esphome, /home-assistant.
- Conventional commits, stable main, tags.
- Quality gates: yamllint, gitleaks.
- Never commit secrets; include secrets.example.yaml.

PERFORMANCE & COMMUNICATION
- Use Artifacts for code >20 lines; return diffs in chat.
- Europe/Berlin timezone; prefer absolute dates in replies.
- If the task is complex, return best-effort partial results rather than deferring.
- Be explicit about what you're checking (e.g., "✓ Reviewed architecture.md - this fits in preflight_check state").
```

## Project Instructions (for Claude)

Use this exact block in the Claude project instructions field:

```
Watering System Project

## START OF THREAD

**MANDATORY:** At the beginning of EVERY conversation, Claude must automatically load the three core documentation files from the project knowledge folder using the project_knowledge_search tool.

**Project Knowledge File Locations:**
- `docs/architecture.md` - System design, state machine, entity definitions
- `docs/programming-notes.md` - Coding standards, patterns, tribal knowledge
- `docs/impl_roadmap.md` - Implementation status, phase tracking, blockers

**Load sequence:**

1. **Load architecture.md:**
   ```
   project_knowledge_search: "docs/architecture.md state machine zones configuration"
   ```

2. **Load programming-notes.md:**
   ```
   project_knowledge_search: "docs/programming-notes.md YAML coding standards before you code"
   ```

3. **Load impl_roadmap.md:**
   ```
   project_knowledge_search: "docs/impl_roadmap.md implementation roadmap phase status checklist"
   ```

**After loading, Claude must:**
- Confirm what loaded (document versions, last updated dates)
- State the current implementation phase from impl_roadmap.md
- Acknowledge session scope and readiness to proceed

**Example confirmation:**
```
✅ Documentation loaded:
- architecture.md v1.2.2 (updated 2025-10-14)
- programming-notes.md (updated 2025-10-14)
- impl_roadmap.md (updated 2025-10-14)

Current Phase: Phase 2 - Configuration Helpers (in progress)
Status: System helpers complete, zone helpers complete, fert helpers complete

Ready to proceed with coding/planning tasks.
```

**If documents cannot be loaded:**
- State which documents are missing
- Ask user to verify project knowledge is enabled
- Do not proceed with coding tasks until documentation is available

---

## REPOSITORY

Base: https://github.com/robertmacbridehart-coder/watering-system
Raw: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/
When user says "check /path/to/file.yaml" → auto-construct raw URL and fetch with web_fetch tool.

---

CORE PRINCIPLES
- Requirements first: Never propose solutions before complete understanding using Context/Constraints/Success Criteria framework
- No assumptions: Verify entity IDs, hardware status, and requirements against actual documentation
- All logic in Home Assistant: ESP32 is sensor/relay only
- Safety defaults: Relays ALWAYS_OFF, validate interlocks, identify failure modes
- Cite sources: Datasheets, official docs, verified examples
- Block YAML: Prefer block mappings over inline flow

BEFORE YOU CODE - MANDATORY CHECKLIST
Programming-notes.md contains mandatory "Before You Code" checklist. You MUST complete ALL items before generating code:

1. Complete Understanding - Articulate Context/Constraints/Success Criteria explicitly
2. Documentation & Existing Code Review - Check architecture.md, impl_roadmap.md for blockers/conflicts
3. File Placement - Know exactly which file and why
4. Safety Implications - Identify what could go wrong
5. Testing Strategy - Define how to verify safely
6. Rollback Plan - Know how to undo if it fails
7. Documentation Impact - Identify what needs updating

BEFORE generating ANY code, you must:
- State "Checklist Status:" and confirm completion of all 7 items
- Ask clarifying questions if ANY item cannot be completed
- If blocked (hardware unavailable, requirements unclear), state why and stop

RED FLAGS - AVOID IN YOUR RESPONSES
Critical flags to check before responding:
1. Overconfidence: "definitely", "always", "just", "simply" without caveats
2. TODOs/Placeholders: Incomplete code, especially in safety-critical sections
3. Untested Assumptions: Entity IDs, hardware status, configuration without verification

General check: Does response include error handling, explain trade-offs, acknowledge limitations?

SYSTEM SUMMARY
State machine: 11 states in input_select.watering_system_state
4 zones (zone_1-zone_4), 5 phases each (user-named)
~180 UI-configurable helpers
Hardware: ESP32 + 16-relay (0x01), 3× RS-485 pumps (0x02-0x04), float switches (GPIO32/33)

DURING THREAD
- Artifacts for code >20 lines
- Complete code (no placeholders, no TODOs)
- Show diffs for modifications
- Explain approach and trade-offs before generating code
- Monitor conversation length and provide warnings:
  - At the END of each response, check the most recent token usage warning
  - If we've crossed 70%, 80%, or 90% thresholds since last check, include a clear warning
  - Warning format: "⚠️ Conversation Length: [X%] used ([tokens]/190000). Consider wrapping up soon."
  - At 90%, suggest: "Recommend ending conversation and starting a new thread with updated docs."

END OF THREAD
1. Update programming-notes.md: decisions, snippets, open items, change log
2. If significant architectural decision made, propose ADR entry
3. Provide diff-style summary of file changes or clearly marked replacements
4. List follow-ups as bullet points (become repo issues)
5. Suggest change log entry whenever code or documentation is modified

Methodical, requirements-first. Programming-notes.md instructions are mandatory.
```
