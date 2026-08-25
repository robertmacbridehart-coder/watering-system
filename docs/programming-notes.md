# Watering System – Programming Notes (Canonical)

This file is the **canonical technical reference** for the project. It now lives in the public repo under `/docs/programming-notes.md` at:

👉 [https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md](https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md)

All future conversations should reference this file as the source of truth. The older canvas version may still exist, but this document takes precedence.

---

## Workflow Guardrails

* **Start**: Read `docs/START_HERE.md` first (session manifest: phase, blockers,
  top gotchas, doc index); pull only the docs the task needs. See START_HERE.md §5.
* **Code**: Put non-trivial YAML/scripts in artifacts, or write directly to the
  local repo via filesystem MCP; keep chat for rationale and diffs.
* **Sources**: Cite primary docs (datasheets, official READMEs/wikis, API refs) for all new parts/configs.
* **Repo Reference**: Before recommending or generating any code, read the relevant
  files from the local repo (`C:\Users\rober\watering-system-private`) via
  filesystem MCP. `entity_reference.md` is canonical for entity IDs.
* **Debugging**: Log first (raw payloads/serial/BLE), validate against spec, then minimal repro.
* **Close**: Update START_HERE.md §1-3 and add Change Log entries to docs touched.
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

This project maintains several authoritative documents that work together.
**Loading model (current):** read `docs/START_HERE.md` first — it carries current
phase, blockers, top gotchas, and a doc index — then pull only the specific
file/section the task needs from the local repo via filesystem MCP. Do **not**
bulk-load the whole doc set; that web-era ritual is superseded (see Change Log
2026-06-28). The table below is a reference for *what each doc covers*, not a
load-everything checklist.

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

### Loading Documents (current workflow)

Read `docs/START_HERE.md` first, then open the specific file the task needs
directly from the local repo via filesystem MCP. The old "paste raw GitHub URLs
one at a time" procedure is **superseded** — it was a workaround for the
project-knowledge / web-fetch era and caused dual-source drift. Web-only raw-URL
fetch remains a fallback when no Desktop/MCP is available (base URL is in the
project-instructions block at the end of this file).

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
  * ESP32: ESP32-DEVKITC-32UE (ESP32-WROOM-32UE module — u.FL/IPEX external-antenna connector; swapped from DEVKITC-VE on 2026-08-18)
  * WiFi antenna: Linx ANT-W63WS3-SMA blade antenna (WiFi 4/5/6/6E — 802.11 n/ac/ax), external, on a Mueller Electric BU-4150031MM500 SMA-female bulkhead lead routed through the cabinet wall (6.5 mm hole). RSSI improved ~-63 → ~-53 dBm.
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

### State-Machine & Automation Patterns

Distilled from the Phase 4 state-machine build and its code-review passes (review
records in docs/phase_4_review_1.md / _2.md; per-fix detail in the git history).
Reusable beyond Phase 4:

* **Derive state-set membership; don't maintain parallel literal lists.** When
  several automations need "is this an operational state," derive it — dispatch
  iff a `script.state_<state>` handler exists; classify "in-flight" as the
  complement (`not in ['idle', <control states>]` **and not**
  `startswith('error_')`) — rather than repeating a literal list that drifts when
  a state is added.
* **Reporting/telemetry calls on a control path get `continue_on_error: true`.** A
  DB/event-reporting subscript (e.g. `finalize_cycle_record`,
  `fire_zone_run_complete`) must never abort real watering/safety work. If a call
  is reporting-only, wrap it.
* **Move a `delay` into a subscript → add that subscript to the abort set.**
  `abort_cycle_scripts` cancels in-flight waits via `script.turn_off`; a delay
  hidden inside a called helper is NOT cancelled unless the helper is in the
  turn_off set, so an aborted cycle would run it to completion (and fire spurious
  reporting).
* **Consumer automations trigger off the `input_select` state, never the raw
  control boolean.** A rejected control-engage reverts its boolean; keying
  consumers off the state (entered/left only via the guard) stops a rejected
  toggle being mistaken for a confirmed transition.
* **Re-read live state before each error-set; don't snapshot once at entry.** A
  one-time `already_errored` snapshot lets a later check overwrite a
  higher-severity error latched concurrently. Re-read
  `not states(...).startswith('error_')` at each set.
* **Safing / e-stop must preserve control states** (e.g. `winterized`) that other
  automations use as transition sources — clobbering them fires spurious
  downstream automations.
* **Prefer a documented id-format check over a multi-value sentinel list** for "is
  X open/set" (e.g. `(uuid | string).startswith('c-')` vs `['', 'unknown',
  'unavailable', …]`), especially when the check is duplicated across files.
* **HA template extensions confirmed available** (used in Phase 4): the `bool`
  filter and the `match` / `search` / `is_number` tests.

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

### Dashboard-Derived Sensors (Gate 7.2): SQL `db_url` Path & Multi-Sensor `rest:` Startup Fetch
The Phase 7 derived sensors (`packages/watering_ui/derived_sensors.yaml`) surface the
operational DB and forecast data read-only for the dashboard. Two silent-failure traps hit
during the 2026-08-22 deploy — both cost a pull+restart cycle because neither logs an error.

**1. SQL sensor `db_url` — HA Core reads from `/config`, NOT `/homeassistant`.**

**Symptom:** The `sensor.zone_{1-4}_watering` SQL sensors (HA `sql:` integration, secondary
`watering_ops.db`) never register — no entity, and **no error in `home-assistant.log`**.
Template sensors in the *same package file* load fine, so the file itself is valid.

**Root Cause:** `db_url` pointed at `sqlite:////homeassistant/watering_ops.db`. That
`/homeassistant` path is the **AppDaemon add-on's** mount of the HA config dir (what
`db_writer.py` correctly uses). **HA Core** sees that same directory as `/config`, so it
cannot open `/homeassistant/...`. The SQL config-flow *imports* a YAML entry by connecting to
the DB during validation; a bad `db_url` makes the import **abort silently** — no config
entry, no entity, no logged error.

**Solution:**
```yaml
sql:
  - name: "Zone 1 Watering"
    # ✅ HA Core is /config-rooted (verified: sensor.repo_pull reads /config/version.json)
    db_url: "sqlite:////config/watering_ops.db"
    # ❌ NOT sqlite:////homeassistant/watering_ops.db — that is AppDaemon's mount name
    query: >-
      SELECT ...
```

**Prevention:**
- `/homeassistant` is add-on-space; HA Core is `/config`-rooted. Cross-check any Core-side
  file path against a known-good one (`sensor.repo_pull` reads `/config/version.json`).
- A silently-absent entity with **zero log output** almost always means the config was never
  processed — check the DB connection/path, not the query syntax.
- SQLite JSON1 (`json_group_array` / `json_object`) IS present on HAOS (verified live 2026-08-22).

**2. Two `- platform: rest` sensors on the same URL race at startup.**

**Symptom:** Of two identical-resource REST sensors (`brightsky_forecast_rain` +
`brightsky_forecast_temp_high`), one consistently came up `unavailable` (`restored: true`)
after each restart while the other fetched fine; no error logged. It self-heals only at the
next `scan_interval`.

**Root Cause:** Both fire the same BrightSky URL near-simultaneously at boot; the second is
throttled / misses the startup fetch and holds its restored state until the next scan. NOT a
template or data bug — both render correctly against live data, and the sibling on the same
URL works.

**Solution:** Use ONE top-level `rest:` resource with multiple child `sensor:` entries — a
single fetch feeds both, eliminating the duplicate call and the race (and halving API load).
Verified live 2026-08-22: both forecast sensors update together on the shared fetch.

**Impact:** Both classes are read-only dashboard sensors (no safety impact), but the failures
are invisible in the log — diagnose by checking config load/path and startup fetch timing,
not by re-reading the query/template.

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

### Cycle Event Log Limitations (Phase 3.1 Discovery)

**Problem:**  
`input_text.cycle_event_log` has two critical limitations:
1. Home Assistant hard limit: 255 characters max (not 1000 as initially designed)
2. Implementation bug: Missing newline separators between log entries

**Impact:**
- Capacity: Only ~4-5 error messages before truncation
- Readability: Entries run together without newlines
- **Blocks Phase 9:** End-of-cycle email summaries require readable, comprehensive logs

**Workaround Options Evaluated:**
1. ~~Shell command to write file~~ - Shell command integration has recurring bugs in 2025.x HA versions, 60s timeout limit, user has negative experience
2. ~~Multiple input_text helpers~~ - Adds complexity, still limited to 255 each
3. **Recommended:** Template-based dynamic summaries or notify.persistent_notification during cycle

**Status:** Requires redesign before Phase 9 implementation

**Temporary Solution:**  
Continue using for Phase 3 testing, redesign for Phase 9.

---

### Invalid zone_id Handling (Acceptable by Design)

**Behavior:**  
Scripts called with invalid `zone_id` (e.g., 5, 99, "invalid") fail silently via template condition check. No error is logged to system log.

**Example:**
```yaml
service: script.open_zone
data:
  zone_id: 99  # Invalid - only 1-4 exist
```

**Result:** Script completes successfully, no relays toggle, no error log entry.

**Rationale:**
- **Safe by design:** Invalid inputs cause no physical actions
- **Trade-off:** Reduced logging vs. preventing invalid relay operations
- **Decision:** Silent failure preferred over risk of acting on invalid data

**Mitigation:**  
State machine (Phase 4) will only call zone scripts with valid IDs (1-4). This gotcha only affects manual testing or external integrations.

---

### Script Abort Procedure

**Situation:**  
Long-running scripts (e.g., `script.run_zone_sequence` with 10-minute runtimes) can be aborted mid-execution if needed.

**Procedure:**
```yaml
# 1. Stop the running script
service: script.turn_off
target:
  entity_id: script.run_zone_sequence

# 2. Clean up open valves
service: script.close_all_zones

# 3. Optionally stop pump (if Phase 3.2 complete)
service: script.stop_main_pump
```

**Discovered:** During Test 7.3 when zones 1+2 were accidentally left enabled.

**Use Cases:**
- Emergency stop during testing
- Aborting long sequential cycles
- Recovery from unexpected conditions

**Note:** Will be superseded by `script.emergency_stop` (Phase 3.4) for production use

---

### Pressure Relief Duration Validation (Phase 3.2)

**Issue:** Defense-in-depth for safety-critical input parameters

**Problem:** If `input_number.pressure_relief_duration_sec` helper is unavailable or returns invalid value, `| int` filter returns 0, resulting in 0-second delay and no actual pressure relief.

**Solution:** Multi-layer validation pattern:
```yaml
- variables:
    raw_duration: "{{ states('input_number.pressure_relief_duration_sec') }}"
    duration_valid: "{{ raw_duration not in ['unavailable', 'unknown', 'none'] }}"
    parsed_duration: "{{ raw_duration | int(0) }}"
    safe_duration: >-
      {% if not duration_valid or parsed_duration < 30 %}
        120
      {% elif parsed_duration > 300 %}
        300
      {% else %}
        {{ parsed_duration }}
      {% endif %}
    used_default: "{{ not duration_valid or parsed_duration < 30 or parsed_duration > 300 }}"

# Log if validation triggered
- if:
    - condition: template
      value_template: "{{ used_default }}"
  then:
    - service: system_log.write
      data:
        message: "Pressure relief duration validation: Helper value '{{ raw_duration }}' invalid or out of bounds (30-300s). Using safe value: {{ safe_duration }}s."
        level: warning

- delay:
    seconds: "{{ safe_duration }}"
```

**Protection provided:**
1. Detects unavailable/unknown states
2. Enforces minimum: 30s (prevents ineffective relief)
3. Enforces maximum: 300s (prevents excessive delay)
4. Safe default: 120s (architecture.md initial value)
5. Logs when validation triggers (debugging aid)

**Rationale:**
- UI constraints are first line of defense
- Code validation is second line of defense (defense in depth)
- Safety-critical operations should never trust input values blindly
- Helper unavailability during HA restart could cause 0-second delay

**When to use this pattern:**
- Any delay derived from user input helper
- Any safety-critical numeric parameter
- Any configurable timeout/duration

**Discovery:** Issue #8, identified during adversarial code review (2025-10-27)

---

### Gmail IMAP IDLE Blind Spot (Notification System)

**Reference:** GitHub issue [#86407](https://github.com/home-assistant/core/issues/86407)

**Symptom:** Emails arriving during an IMAP IDLE session are sometimes registered
immediately but other times silently missed and only detected at the next IDLE
reconnect — causing detection delays of up to ~14 minutes.

**Root Cause:**
- HA's IMAP integration uses the `aioimaplib` library with a default IDLE timeout
  of **29 minutes**.
- Gmail's IMAP server stops sending IDLE push notifications to the client at
  roughly the **15-minute mark** into the session.
- Emails arriving in the window **~minutes 15–29** of the IDLE cycle are not pushed
  to HA. They are only detected when the 29-minute timeout fires and the IDLE
  session is re-established.
- Result: a **~14-minute detection blind spot** in the second half of every
  IDLE cycle.

**HA Version History:**
- Bug reported January 2023 (HA 2023.1.7), affects Gmail and Outlook.
- PR #74623 (merged 2023.2) improved IDLE handling but did not eliminate the
  29-minute cycle or the mid-cycle notification failure.
- HA 2026.4 added IMAP connection-loss cleanup (issue #168662) but this addresses
  reconnection robustness, not the underlying blind spot.
- As of 2026.06: blind spot is still present when using Gmail IMAP IDLE.

**Workarounds:**

1. **Time sends to the first half of the IDLE cycle** (chosen for this project).
   The daily 19:00 email self-test is sent at a fixed time. If the IDLE reconnect
   last occurred before 18:45, the email will land in the safe first 15 minutes;
   if it landed after 18:45, the worst case is a ~14 min delay in detection, which
   is still well within the 5-minute timeout threshold tracked by
   `input_boolean.notification_system_error`. The daily test at 19:00 is therefore
   low-risk but not guaranteed to arrive during the safe window.

2. **Force IDLE reconnect periodically** (not implemented).
   A 15-minute automation calling `homeassistant.update_entity` on the IMAP sensor
   forces a reconnect before the blind spot opens. This adds automation complexity
   and is unnecessary given the self-test's existing 5-minute detection window.

**Impact on this project:**
- The daily email self-test (19:00 send, 5-minute IMAP detection window) may
  occasionally fail to detect email arrival in time, incorrectly triggering
  `notification_system_error`. This would then block morning watering in the
  preflight check.
- **False-positive `notification_system_error` events** are the primary risk,
  not a true notification failure.
- If spurious errors are observed in production, implement Workaround 2.

**Prevention:**
- Monitor `notification_system_error` in production for unexplained activations.
- If false positives occur, add a 15-minute `update_entity` automation for the
  IMAP sensor (simple addition to `notification/config.yaml`).

**Discovery:** Research session 2026-06-28; bug verified against issue #86407
and HA changelogs through 2026.4.

---

### Script Mode for Safety-Critical Operations (Phase 3.2)

**Issue:** Safety automations blocked by long-running scripts

**Problem:** With `mode: single` and 120-minute retry loop in `stop_main_pump`, if one caller triggers the script, ALL OTHER callers (including safety automations) are blocked until completion.

**Scenario:**
1. Normal cycle calls stop_main_pump
2. Pump doesn't stop, enters 120-min retry loop
3. Tank level drops critically
4. Safety automation tries to call stop_main_pump
5. **Call is DROPPED** (mode: single)
6. Safety automation thinks it handled situation, but pump still running

**Impact:** Defeats purpose of safety automation - CRITICAL SAFETY HAZARD

**Solution:** Use `mode: restart` for scripts callable by safety automations
```yaml
stop_main_pump:
  mode: restart  # Latest stop request kills previous attempt and starts fresh
```

**Rationale:**
- `mode: restart` ensures latest request takes priority
- Previous retry loop is killed, new one starts
- Safety automations always get through
- Trade-off: Retry counter resets (acceptable for safety)

**When to use `mode: restart`:**
- Any script that safety automations must be able to call
- Scripts that handle emergency conditions
- Operations where latest request should always win

**When NOT to use `mode: restart`:**
- Scripts with sequential dependencies (state machine transitions)
- Scripts that should never interrupt themselves
- Most normal operational scripts (use `mode: single`)

**Discovery:** Issue #9 (CRITICAL), identified during adversarial code review (2025-10-28)

---

### State Verification Pattern for Unavailable Entities (Phase 3.2)

**Issue:** Incorrect state checking pattern misses unavailable entities

**Problem:** Using `condition: state, state: 'on'` only checks for exact match, misses 'unavailable' and 'unknown' states, causing false negatives in failure detection.

**Example (WRONG):**
```yaml
# This MISSES unavailable state:
- if:
    - condition: state
      entity_id: switch.watering_system_relay_9_pressure_relief
      state: 'on'  # Only True if exactly 'on', False for 'off', 'unavailable', 'unknown'
  then:
    - # Error handling
```

**Testing Logic:**
- Valve = 'on': Triggers error ✓
- Valve = 'off': Continues ✓
- Valve = 'unavailable': **Continues** ✗ (WRONG - should error)

**Solution (CORRECT):** Use `not is_state()` pattern for failure detection
```yaml
# This CATCHES unavailable state:
- if:
    - condition: template
      value_template: "{{ not is_state('switch.watering_system_relay_9_pressure_relief', 'off') }}"
  then:
    - # Error handling (triggered for 'on', 'unavailable', 'unknown')
```

**Why This Works:**
- `is_state('entity', 'desired')` returns `True` ONLY if exact match
- `is_state('entity', 'desired')` returns `False` for all non-matches INCLUDING 'unavailable'
- Therefore `not is_state('entity', 'desired')` catches ALL failure states

**Pattern Summary:**
```yaml
# For checking if entity IS in desired state:
is_state('entity_id', 'desired_state')  # True only if exact match

# For checking if entity is NOT in desired state (failure detection):
not is_state('entity_id', 'desired_state')  # True for ALL non-matches including unavailable
```

**Reference:** https://www.home-assistant.io/docs/configuration/templating/

**Affected Locations:** Issues #15, #16, #17 - Fixed in 3 locations across pump scripts

**Discovery:** Adversarial code review (2025-10-28)

---

### YAML Syntax: Empty then: Block Failures (Phase 3.2)

**Issue:** Empty conditional blocks cause silent script failures

**Problem:** Refactoring conditional logic can leave empty `then:` sections, which are invalid YAML syntax but may not be immediately obvious.

**Example (WRONG):**
```yaml
- if:
    - condition: template
      value_template: "{{ some_check }}"
  then:  # ← Empty! YAML syntax error
```

**Symptom:** Script fails to load or execute, error message may not clearly identify empty block

**Solution:** Ensure all `if:` blocks have non-empty `then:` sections

**Correct Patterns:**
```yaml
# Pattern 1: Action in then block
- if:
    - condition: template
      value_template: "{{ some_check }}"
  then:
    - service: system_log.write
      data:
        message: "Action taken"

# Pattern 2: No-op using delay (if truly no action needed)
- if:
    - condition: template
      value_template: "{{ some_check }}"
  then:
    - delay:
        milliseconds: 1  # No-op

# Pattern 3: Invert logic to avoid empty block
- if:
    - condition: template
      value_template: "{{ not some_check }}"  # ← Inverted
  then:
    - # Now this block has content
```

**Prevention:**
- Code review all `if:` blocks before committing
- Look for `then:` followed immediately by next top-level key
- Consider using linters that catch empty YAML sequences

**Discovery:** Phase 3.2 testing, fixed in pressure relief self-repair logic (2025-11-02)

---

### Relay State Verification Race Condition (Phase 3.2)

**Issue:** State propagation delay causes false verification failures

**Problem:** When calling a script that closes a relay (e.g., `close_pressure_relief`) from another script and then immediately checking the relay state, a race condition can occur. The calling script may check the relay state before ESPHome has propagated the state change to Home Assistant, causing false verification failures.

**Example:**
```yaml
# In start_main_pump script - self-repair logic
- service: script.close_pressure_relief
- wait_template: "{{ is_state('script.close_pressure_relief', 'off') }}"
  timeout: 10
- if:  # ← Race condition here
    - condition: template
      value_template: "{{ not is_state('switch.watering_system_relay_9_pressure_relief', 'off') }}"
  then:
    - # False error: "valve failed to close"
```

**Symptom:** Script aborts with "valve failed to close" error even though relay successfully closed (verified by checking state immediately after script completes).

**Root Cause:** 
- `close_pressure_relief` has 3s delay for relay de-energization
- `wait_template` confirms script completion
- BUT: State propagation from ESPHome → HA may take additional milliseconds
- Immediate state check can read stale cached value

**Solution:** Add 500ms delay before re-checking relay state after waiting for called script to complete
```yaml
- service: script.close_pressure_relief
- wait_template: "{{ is_state('script.close_pressure_relief', 'off') }}"
  timeout: 10
- delay:  # ← Add this
    milliseconds: 500
- if:  # Now safe to check
    - condition: template
      value_template: "{{ not is_state('switch.watering_system_relay_9_pressure_relief', 'off') }}"
  then:
    - # Error handling
```

**Duration:** 500ms is conservative; 100-200ms may suffice but not tested.

**Affected Scripts:**
- `start_main_pump` (pressure relief self-repair logic) - FIXED
- Any future script calling another relay control script + immediate verification

**Discovery:** Phase 3.2 testing, Test 1.3 initial failure (2025-11-02)

**Prevention:**
- Always add 500ms delay after calling relay control subscripts
- Document pattern for future script development
- Consider making this a standard pattern in template library

---

### `continue_on_error` Scope: Catches Sub-Script Errors, NOT Missing Services (Phase 3.4)

**Issue:** `continue_on_error: true` does **not** make a step non-halting for *all*
failure kinds — the distinction is subtle and was the root cause of a real bug.

**Verified behavior (Dev-Tools probe, 2026-08-03, Core 2025.9.4):**

| Failing step under `continue_on_error: true` | Sequence continues? |
|-----------------------------------------------|---------------------|
| A called script ends with `stop: … error: true` | **YES** — error is caught, next step runs |
| A call to a **non-existent** service/script (`ServiceNotFound`) | **NO** — halts the sequence |

HA's docs state `continue_on_error` "will not suppress/ignore misconfiguration or errors
that Home Assistant does not handle" — a missing service is a *misconfiguration* (not a
runtime error), so it is not suppressed.

**The bug it caused (the `safe_shutdown` early-halt):** `safe_shutdown` wrapped
`service: script.stop_dosing_pumps` in `continue_on_error: true`, expecting it to "fail
gracefully if not implemented." But Phase 3.3 isn't built, so `stop_dosing_pumps` does not
exist → `ServiceNotFound` → the whole `safe_shutdown` sequence halted at that step (only the
"started" row was ever logged). The `stop_main_pump` step earlier in the same sequence was a
red herring — its `stop: error:true` was correctly caught.

**Probe used to confirm** (throwaway scripts, notifications as markers): a parent with
`continue_on_error: true` calling (a) a child that does `- stop: "boom"` `error: true`
reached the step *after* the call; (b) a non-existent `script.xyz` did **not**.

**Prevention / patterns:**
- To tolerate a **possibly-non-existent** script, guard on the entity existing instead of
  relying on `continue_on_error`:
  ```yaml
  - if:
      - condition: template
        value_template: >-
          {{ states.script.stop_dosing_pumps is not none
             and states('script.stop_dosing_pumps') not in ['unavailable', 'unknown'] }}
    then:
      - alias: "Stop dosing pumps"
        continue_on_error: true
        service: script.stop_dosing_pumps
  ```
- `continue_on_error` is still the right tool for a **called script that may `stop` with
  `error: true`** (runaway pump, comms-lost fail-fast) — that IS caught.

**Discovered:** Phase 3.4 comms-lost implementation (2026-08-03). Fix landed in
`watering_scripts/watering_safety_scripts.yaml` (`safe_shutdown`).

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

**WhatsApp not delivering — diagnosing & the CallMeBot "paused account" (observed 2026-08-18):**
Every production notify call wraps the CallMeBot `rest_command` in `continue_on_error: true`
(a notify failure must never stall a watering cycle or safety path), so a failed send is
**silent** — nothing useful in the logs. To see the real HTTP result, run the manual diagnostic
(Developer Tools → Actions):

```yaml
action: script.diagnose_whatsapp_path
```

It calls the same `rest_command` but *captures* the response (`response_variable`) and surfaces
`status=` + the body via a persistent notification ("WhatsApp Path Diagnostic") + `log_system_event`.
It bypasses the winter gate on purpose (transport test). `diagnose_whatsapp_path` lives in
`notification/scripts.yaml`. Interpretation:

| Result | Meaning | Fix |
|---|---|---|
| `status=200`, body "Message queued…", msg arrives | healthy | none |
| `status=208`, body "Your Account is Paused … send the word 'resume'" | CallMeBot **paused the account** (periodic — their outages/inactivity) | send `resume` (below) |
| `2xx` body "APIKey not valid" / "not registered" | key/registration lapsed | re-request the key from CallMeBot |
| `status=none (transport error)` | network/DNS/TLS from the AppDaemon/HA container | check host outbound to `api.callmebot.com` |

**First, always check the winter gate:** the STANDARD tier + the monthly WhatsApp test are
suppressed while `input_boolean.system_winterized` is ON. Confirm it is `off` before diagnosing
transport (CRITICAL/HIGH can bypass the gate; STANDARD cannot).

**Paused-account fix:** from the phone that owns the `whatsapp_phone` number, send the single word
`resume` in WhatsApp **to the CallMeBot registration number +34 694 242 562** (the bot that issued
the API key). Reactivation takes seconds to a couple of minutes; it must be done from the phone —
it cannot be automated from HA. The pause is unrelated to the API key value, phone number, or HA
config (all were correct throughout — only CallMeBot's server-side account state was paused).
**Verify:** re-run `script.diagnose_whatsapp_path` for `status=200` **and** confirm the 🔧 test
message physically lands (200 only means CallMeBot *accepted* it — a paused/unauthorized number can
still 200-and-drop, so confirm actual receipt).

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
- Gmail IMAP IDLE blind spot (see Known Gotchas below): emails arriving in minutes
  15–29 of the 29-minute IDLE cycle are silently dropped until the next reconnect.
  Workaround: time test emails to arrive in the first ~15 minutes of the cycle.
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

**Addendum 2026-08-05 -- the state set grew 11 -> 15 during Phase 3:**
The original decision enumerated 11 states. Phase 3 implementation added four
more as the concrete scripts needed distinct latch/branch points, and
`input_select.watering_system_state` (config_helpers.yaml) now defines **15**.
The added states:
- `winterized` -- seasonal shutdown state (distinct from the
  `input_boolean.system_winterized` control that gates cycles).
- `error_e_stop` -- latched by `script.emergency_stop`
  (watering_safety_scripts.yaml); prevents auto-restart until cleared.
- `error_valve_interlock` -- set by the zone/pump scripts when the R6 XOR R7
  flow-path interlock is violated or the valves read unavailable.
- `error_relay_state` -- set when a relay fails post-command verification
  (e.g. pump did not energize/de-energize).
The decision itself (single master state machine, one automation watching the
select, error states isolate failures) is unchanged; only the count grew. The
canonical list is `input_select.watering_system_state` in
config_helpers.yaml, mirrored in entity_reference.md. architecture.md §2.1/§2.2
and impl_roadmap.md were reconciled to 15 the same day (they had lagged at 11/12
with a duplicated `error_tank_low`).

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
**Status:** Partially superseded by ADR-021 (2026-08-25, DRAFT) — the 3-day-average-high
is **demoted** from the decision path (de-lagged to forecast/current high) and retained for
DB/reporting only.

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

### ADR-007: Heavy Program Single-Window Mode Behavior

**Date:** 2025-10-22  
**Status:** Superseded by ADR-020 (2026-08-22) — the same-day heavy split was
retired for a mid-interval booster. The single-window `1.5×` survives only as the
`N==1` (daily) edge; for `N≥2` single-window, heavy is `1.0×` main + a separate
`0.5×` booster on a different day. See ADR-020 / architecture.md §3.3.

**Context:**  
Heavy program behavior when only one watering window is enabled.

**Decision:**  
In single-window mode (only morning OR evening enabled), the heavy program applies 1.5x runtime ONLY to the enabled window. The disabled window receives 0.0 runtime.

**Rationale:**
- **Defensive programming:** Prevents watering if state machine erroneously calls script with disabled window
- **Clear semantics:** "Heavy program in single-window mode" means "water heavily during the one available window"
- **Fail-safe:** If window is disabled, nothing should water regardless of program

**Implementation:**
```jinja2
{% if dual_window %}
  # Both windows enabled: split watering
  # morning: 1.0x, evening: 0.5x
{% else %}
  # Single window: check which is enabled
  {% if window == 'morning' and morning_enabled %}
    {{ base_runtime * 1.5 }}
  {% elif window == 'evening' and evening_enabled %}
    {{ base_runtime * 1.5 }}
  {% else %}
    {{ 0.0 }}  # Requested window not enabled
  {% endif %}
{% endif %}
```

**Alternatives Considered:**
1. Always return 1.5x in single-window mode regardless of which window requested
   - Rejected: Could water disabled window if state machine has bug
2. Return 1.5x for any window in single-window mode
   - Rejected: Same issue, less defensive

**Consequences:**
- Positive: Defensive against state machine bugs
- Positive: Clear, predictable behavior
- Neutral: Requires state machine to only call with enabled windows (should already do this)

---

### ADR-008: Valve Interlock Check in Zone Scripts

**Date:** 2025-10-22  
**Status:** Accepted

**Context:**  
Zone control scripts need to verify valid flow path exists before opening zone valves.

**Decision:**  
Zone scripts check that exactly one flow path valve is open (R6 XOR R7) before opening any zone valve. State machine is responsible for configuring valves, but zone scripts verify as defense-in-depth.

**Valid Configurations:**
- (R6 on AND R7 off) - Bypass valve open, fert line closed
- (R6 off AND R7 on) - Bypass closed, fert line open

**Invalid Configurations:**
- (R6 on AND R7 on) - Dual flow path (wastes fertilizer)
- (R6 off AND R7 off) - No flow path (dry run, pump damage)

**Error State:** Sets `error_valve_interlock` if invalid configuration detected.

**Rationale:**
- **Defense-in-depth:** Catches state machine logic errors
- **Prevents damage:** Stops dry running (no flow path) and fertilizer waste (dual path)
- **Manual intervention protection:** User can't break system by manually toggling valves in UI

**Alternatives Considered:**
1. Trust state machine exclusively
   - Rejected: Single point of failure
2. Auto-correct valve configuration in scripts
   - Deferred: Future enhancement, keep simple for Phase 3

**Consequences:**
- Positive: Multiple layers of protection
- Positive: Catches manual UI valve toggling errors
- Neutral: Small overhead (~1 condition check per zone open)
- Future: Can add auto-correction logic without changing error detection

---

### ADR-009: Evening Window Independence for Heavy Programs

**Date:** 2025-10-22  
**Status:** Superseded by ADR-020 (2026-08-22). The same-day dual-window heavy
split (morning `1.0×` + evening `0.5×`) was retired; heavy's extra `0.5×` now
falls at the interval midpoint as a separate `booster` run, re-evaluated against
current weather at that window. The "adapt to mid-day change" intent is preserved
by the booster's fresh weather re-evaluation. See ADR-020.

**Context:**  
In dual-window heavy programs, should the evening 0.5x watering depend on whether the morning 1.0x executed?

**Decision:**  
Evening window runs 0.5x for heavy programs INDEPENDENTLY - it does not check whether morning watered.

**Scenario:**
```
Morning: Program = normal (1.0x), waters at 06:00
Mid-day: Weather changes, user/automation changes program to heavy
Evening: Program = heavy (0.5x), waters at 18:00
Total: 1.0x + 0.5x = 1.5x (appropriate for conditions)
```

**Rationale:**
- **Adapts to changing conditions:** Weather and plant needs can change during the day
- **Simpler logic:** No tracking booleans needed (was considered, rejected)
- **Conservative approach:** Better to water 0.5x extra than miss critical irrigation
- **Operator flexibility:** Manual program override works as expected

**Alternatives Considered:**
1. Track morning completion with `input_boolean.zone_X_morning_heavy_complete`
   - Rejected: Added complexity, no clear benefit
   - Would prevent adaptation to mid-day condition changes
2. Run evening only if morning ran
   - Rejected: Breaks mid-day program changes
   - Less flexible for manual overrides

**Consequences:**
- Positive: Simpler implementation (no tracking booleans)
- Positive: Adapts naturally to mid-day program changes
- Positive: Manual overrides work intuitively
- Potential: Could water 0.5x "extra" if user changes heavy→normal after morning (acceptable trade-off)

**Validation:**
Test 7.3 confirmed this behavior works correctly in production testing.

---

### ADR-010: Self-Healing Logic Patterns

**Date:** 2025-11-07  
**Status:** Accepted  
**Phase:** 3.2 Pump Control Scripts

**Context:**  
Multiple pump control scripts encounter transient failure states (relay stuck open, pump won't stop). Need consistent approach to auto-correction vs. immediate error.

**Decision:**  
Implement self-healing logic with two distinct patterns based on severity and risk profile:

#### Pattern 1: Single-Attempt Self-Repair (Pressure Relief Valve)
**Used in:** `script.start_main_pump`

**Process:**
1. Detect R9 open during pump startup safety checks
2. Log to cycle_event_log: "Pressure relief valve unexpectedly open, attempting to close"
3. Call `script.close_pressure_relief`
4. Wait 500ms for state propagation (prevents race condition)
5. Re-assess valve state after 3-second verification
6. If still open → Set `error_valve_interlock` and abort
7. If closed → Log success and continue pump startup

**Rationale:** Low-risk repair (closing safety valve), single retry sufficient.

#### Pattern 2: Aggressive Retry Loop (Pump Stop)
**Used in:** `script.stop_main_pump`

**Process:**
1. Command pump OFF, verify after 3s
2. If still ON → Enter retry loop:
   - Re-send stop command every 2 seconds
   - Log every 10th attempt (every 20s) to prevent log spam
   - Continue for up to 120 minutes
   - Hardware backstop: ESPHome auto-off timer at 120 min
3. Exit loop when pump stops OR hardware timer triggers

**Rationale:** High-risk failure (runaway pump), requires aggressive correction. Hardware timer provides ultimate safety backstop.

**Key Difference: Script Mode**
- Pressure relief self-repair: Scripts use `mode: single` (sequential execution)
- Pump stop retry: Uses `mode: restart` (latest request kills previous attempt)
- **Critical:** `mode: restart` ensures safety automations can always override in-progress stop attempts

**Logging:**
- All self-repairs logged to both system_log (permanent) AND cycle_event_log (per-cycle)
- Repair attempts always logged before outcome
- Success/failure logged after verification
- Format: "{timestamp} - {event description}" in cycle_event_log

**Alternatives Considered:**
1. Immediate error without repair attempt
   - Rejected: Less resilient to transient issues
2. Same retry count for all repairs
   - Rejected: Different risk profiles require different strategies
3. Circuit breaker pattern (max retries then disable)
   - Rejected: Hardware timer provides safer backstop than software circuit breaker

**Consequences:**
- **Positive:** System resilient to transient issues
- **Positive:** Reduces manual intervention needs
- **Positive:** All repair attempts logged for debugging
- **Positive:** Dual strategy (single vs. aggressive) matches risk profile
- **Risk:** Aggressive retry could mask hardware failures (mitigated by logging every 20s)
- **Future:** Pattern can extend to R6/R7 valve auto-correction if needed

**Validation:**
- Test 1.3: Pressure relief self-repair success path validated
- Test 3.2: Pump auto-stop (relief script calls stop) validated
- Tests 2.2, 2.3: Pump stop retry logic validated via code review (UI too slow for testing)

---

### ADR-011: Operational Database Architecture

**Date:** 2026-06-28 (SQLite revision)
**Status:** Accepted — supersedes the original MariaDB formulation (drafted 2026-04-08, never implemented)
**Author:** Bob / Claude collaboration

---

#### Context

The watering system lacks persistent structured storage for operational history. The current
temporary solution — `input_text.cycle_event_log` (255 character max) — was flagged in
programming-notes.md as requiring redesign and is insufficient for the system's needs.

Persistent structured storage is a foundational requirement for:
- State machine decision support (e.g., 14-day rolling fertigation window queries)
- Daily operational reports
- Future LLM-based advisory and summarization features
- Safety event correlation with cycle history
- Long-term trend analysis across seasons

Without a queryable historical record, the state machine can only see current entity states,
not operational history. This blocks multiple planned features in Phases 3.3, 4, and beyond.

The system runs on a Home Assistant Green (HAOS appliance). All solutions must operate
within the HAOS supervised add-on ecosystem. Direct OS-level services are not available.
`shell_command` is unreliable in HAOS containers.

---

#### Decision

Implement a two-layer architecture:

**Layer 1 — SQLite (single database file)** for a dedicated `watering_ops` database in one
file at `/homeassistant/watering_ops.db`, completely separate from HA's own recorder
database. Living in the HA config directory means it is captured by HA's normal backup and
is reachable from the AppDaemon container. The version-controlled physical schema lives in
`docs/db_schema.sql`.

**Layer 2 — AppDaemon add-on** as the Python bridge between HA and SQLite. AppDaemon
listens for HA events fired by the state machine, writes records, and answers decision
queries by returning results as HA sensor states or script response variables. It uses the
`sqlite3` standard library (no database driver add-on) and runs in its own isolated
container; its failure does not affect watering operations (DB writes are fire-and-forget).

The schema is applied by an idempotent AppDaemon bootstrap app (`db_schema_init.py`, all
`CREATE ... IF NOT EXISTS`) on start-up — no manual SQL execution on HAOS.

#### Why SQLite (revision of the original MariaDB decision)

The original ADR-011 specified the MariaDB add-on. Re-evaluation found MariaDB to be the
wrong fit and the source of avoidable complexity:

- **Workload is tiny and single-writer** — one or two cycles a day, four zone runs each, a
  handful of doses/events (tens of rows/day, a few thousand/season). AppDaemon is the only
  writer, on sequential state-machine events. Nowhere near where a client/server RDBMS pays
  off.
- **SQLite removes every MariaDB complication on HAOS** — no second persistent add-on, no
  creating the DB/user through add-on config, no driver (`PyMySQL`), no charset config, and
  no awkward schema-application path. One file, applied by code, openable in any SQLite
  browser.
- **No loss of capability** — fully relational and ACID; same normalized schema, foreign
  keys, indexes, and CHECK constraints; the same 14-day rolling-window query; separate from
  the recorder by definition; trivially backed up.

**Read-after-write:** SQLite is serializable — once a write commits, the next read sees it
(no replication lag). The only timing gap is the async HA-event → AppDaemon-handler path,
identical under any engine. Mitigations: the eligibility read runs at cycle start while
dose INSERTs happen at dose conclusion (never a tight write-then-read on the same new row);
any genuine read-after-write goes through a synchronous AppDaemon service that writes,
commits, then reads on the same connection — not via an async sensor.

**Engine specifics:** foreign keys are OFF by default and per-connection (`PRAGMA
foreign_keys = ON` on every connection); WAL journal mode and a `busy_timeout` are set;
timestamps are stored as TEXT `'YYYY-MM-DD HH:MM:SS'` in UTC (display converts to local),
keeping the 14-day window correct across the CET/CEST changeover.

**Revisit only if** concurrent external/networked clients must query live while AppDaemon
writes, or the HA recorder itself moves to MariaDB. Neither is anticipated.

---

#### Database Schema

> The **Type** columns below are logical. The physical SQLite mapping (BOOLEAN -> INTEGER,
> DECIMAL -> REAL, DATETIME -> TEXT in UTC, VARCHAR -> TEXT), foreign keys, indexes, and
> CHECK constraints are defined in `docs/db_schema.sql`, the version-controlled source of
> truth.

##### Table: `watering_cycles`

One row per complete cycle run. Written in two phases.

| Column | Type | Description |
|--------|------|-------------|
| `cycle_id` | INT AUTO_INCREMENT PK | Unique cycle identifier |
| `start_time` | DATETIME | Written at preflight check |
| `trigger_type` | VARCHAR(20) | `scheduled` / `manual` / `override` — written at preflight |
| `rainfall_24h_mm` | DECIMAL(5,1) | Weather snapshot at preflight |
| `rainfall_72h_mm` | DECIMAL(5,1) | Weather snapshot at preflight |
| `temp_high_c` | DECIMAL(4,1) | Weather snapshot at preflight |
| `end_time` | DATETIME | Updated on cycle completion |
| `outcome` | VARCHAR(20) | `completed` / `aborted` / `error` — updated on completion |
| `notes` | VARCHAR(500) | Optional detail on outcome — updated on completion |

**Write pattern:**
- Row created at preflight with `cycle_id`, `start_time`, `trigger_type`, and weather snapshot
- `end_time`, `outcome`, `notes` updated when state machine concludes the cycle
- Row exists during the cycle, enabling "is a cycle currently running?" DB queries

---

##### Table: `zone_runs`

One row per zone per cycle. Written at conclusion of zone run (completed or aborted).

| Column | Type | Description |
|--------|------|-------------|
| `zrun_id` | INT AUTO_INCREMENT PK | Unique zone run identifier |
| `cycle_id` | INT FK → watering_cycles | Parent cycle |
| `zone_id` | TINYINT | Zone number 1–4 |
| `weather_program` | VARCHAR(10) | `off` / `light` / `normal` / `heavy` — per-zone evaluation |
| `start_time` | DATETIME | Zone valve open time |
| `end_time` | DATETIME | Zone valve close time |
| `planned_duration_sec` | INT | From `script.calculate_zone_runtime` result |
| `actual_duration_sec` | INT | Derived from start/end times |
| `program_multiplier` | DECIMAL(3,2) | e.g. 1.0, 1.5, 0.5 — for audit trail |
| `fertigated` | BOOLEAN | True if fertigation dose records exist for this run |
| `aborted` | BOOLEAN | True if zone run did not complete planned duration |
| `abort_reason` | VARCHAR(200) | Populated if aborted = true |

**Design notes:**
- `weather_program` lives here (not in `watering_cycles`) because the state machine
  evaluates program per zone. Future per-zone override capability is preserved.
- `fertigated` boolean allows zone-level fertigation queries without a JOIN to
  `fertigation_doses`. Kept for query convenience; may be re-evaluated once query
  patterns are established.
- `actual_duration_sec` is derived from `start_time` / `end_time` rather than stored
  independently, reducing inconsistency risk. AppDaemon calculates on write.

---

##### Table: `fertigation_doses`

One row per dose event. Written at conclusion of dosing event.

| Column | Type | Description |
|--------|------|-------------|
| `dose_id` | INT AUTO_INCREMENT PK | Unique dose identifier |
| `zrun_id` | INT FK → zone_runs | Parent zone run |
| `zone_id` | TINYINT | Denormalized from zone_runs for query convenience |
| `timestamp` | DATETIME | When dose was delivered |
| `nutrient_product` | VARCHAR(100) | Product name/identifier |
| `target_dose_ml` | DECIMAL(6,2) | Planned dose from helper configuration |
| `actual_dose_ml` | DECIMAL(6,2) | Actual dose delivered (pump feedback or estimated) |
| `pump_id` | INTEGER | Logical pump number 1-3 (maps to Modbus 0x02-0x04) |
| `phase` | TINYINT | Dose phase: 1 or 2 |

**Design notes:**
- `zone_id` is intentionally denormalized (also derivable via JOIN through `zrun_id`).
  Retained for simpler dose-only queries, e.g. 14-day rolling window per zone.
- No foreign key from `zone_runs` to `fertigation_doses`. Relationship is
  `fertigation_doses.zrun_id → zone_runs.zrun_id` only. `fertigated` boolean in
  `zone_runs` provides the downward indicator without a circular reference.

---

##### Table: `system_events`

Append-only log for safety events, errors, state transitions, and manual overrides.
Written immediately after the event occurs.

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | INT AUTO_INCREMENT PK | Unique event identifier |
| `timestamp` | DATETIME | When event occurred |
| `event_type` | VARCHAR(50) | e.g. `safety_interlock`, `manual_override`, `error_state` |
| `severity` | VARCHAR(20) | `info` / `warning` / `critical` |
| `entity_id` | VARCHAR(100) | HA entity involved, if applicable |
| `value_before` | VARCHAR(200) | State/value before event |
| `value_after` | VARCHAR(200) | State/value after event |
| `notes` | VARCHAR(500) | Human-readable detail |

**Design notes:**
- Intentionally has no foreign key to `watering_cycles`. Safety events may occur
  outside of any cycle, and the table must remain independent.
- Correlation with cycle history is done at query time by timestamp range:
  ```sql
  SELECT * FROM system_events
  WHERE timestamp BETWEEN
    (SELECT start_time FROM watering_cycles WHERE cycle_id = X)
    AND
    (SELECT end_time FROM watering_cycles WHERE cycle_id = X);
  ```
- `value_before` / `value_after` stored as VARCHAR to accommodate any entity type
  (boolean, numeric, string state).

---

#### Outcome Vocabulary

`watering_cycles.outcome` is a controlled vocabulary:

| Value | Meaning |
|-------|---------|
| `completed` | State machine reached IDLE via normal post-cycle relief path |
| `aborted` | Cycle stopped by manual intervention or scheduled skip |
| `error` | Cycle stopped by safety interlock or fault condition |

---

#### Write Trigger Architecture

AppDaemon listens for HA events fired by the state machine at defined transition points:

| DB Write | Trigger Point | HA Event |
|----------|---------------|----------|
| `watering_cycles` INSERT | Preflight check passes | `watering_preflight_complete` |
| `zone_runs` INSERT | Zone run concludes | `watering_zone_run_complete` |
| `fertigation_doses` INSERT | Dosing event concludes | `watering_fert_dose_complete` |
| `watering_cycles` UPDATE | Cycle concludes | `watering_cycle_complete` |
| `system_events` INSERT | Safety/error event fires | `watering_system_event` |

**Note:** HA event names above are proposed conventions — not yet implemented in the
state machine. Event design must be confirmed during Phase 4 (state machine) implementation.

---

#### Query Return Mechanism

Two patterns depending on use case:

**For state machine decision queries** (latency-sensitive, during cycle execution):
AppDaemon updates a dedicated HA sensor entity with the query result. The state machine
reads the sensor value via template. Slightly less real-time than a direct response
variable, but simpler and more robust for the HAOS environment.

**For reporting queries** (non-latency-sensitive, daily reports):
AppDaemon generates report content and fires a HA event or updates a persistent
notification. Report delivery via existing notification infrastructure (Phase 9).

This decision may be revisited once AppDaemon response variable patterns are validated
in the HAOS environment.

---

#### Backup and Archive Strategy

##### Ongoing Backup
The SQLite database file (`/homeassistant/watering_ops.db`) lives in the HA config directory
and is included in HA's standard automated backup. HA backups should be configured to
replicate to network storage or cloud to protect operational history.

##### Seasonal CSV Export
At the end of each growing season, AppDaemon exports all four tables as dated CSV files.
This provides a human-readable, portable archive suitable for review, import into
spreadsheet tools, or use as context for LLM-based seasonal analysis.

**Export file naming convention:**
```
watering_cycles_YYYY.csv
zone_runs_YYYY.csv
fertigation_doses_YYYY.csv
system_events_YYYY.csv
```

**Trigger:** Seasonal export is initiated manually or via a HA automation tied to the
de-winterization / winterization workflow already planned in the notification system.

**Destination:** Local HA storage path, then included in the next HA backup cycle.
Optionally copied to NAS or cloud storage via existing backup infrastructure.

**Retention:** CSV archives retained indefinitely. The `watering_ops` database continues
to accumulate across seasons (no truncation) unless explicitly decided otherwise. This
allows multi-season SQL queries without merging archive files.

---

#### Alternatives Considered

##### HA Recorder / Statistics (Rejected)
HA's built-in recorder is designed for entity state history, not application data.
Writing structured operational records into the recorder works against its design,
and HA upgrades could affect the schema. Rejected in favour of a dedicated database.

##### Single Flat Log Table (Rejected)
A single table with all fields nullable would be simpler initially but would make
queries for the 14-day fertigation window, per-zone reporting, and safety correlation
significantly more complex. Normalized schema preferred for long-term maintainability.

##### External Database Server (Rejected)
Running a separate database server outside of HAOS (e.g., on a NAS or separate machine)
adds network dependency and operational complexity. A local SQLite file via the AppDaemon
add-on provides the needed capability within the supervised ecosystem with no extra service.

##### File-Based Logging (Rejected)
CSV or JSON file logging via shell commands has known reliability issues in HAOS
(documented in programming-notes.md) and is not queryable by the state machine.
Rejected.

##### MariaDB add-on (Rejected in 2026-06-28 SQLite revision)
The original Layer 1 choice. Rejected on re-evaluation: a client/server RDBMS is unjustified
for a tens-of-rows-per-day single-writer workload, and on HAOS it adds a second persistent
add-on plus DB/user-via-add-on-config, a driver, and charset setup — friction with no
benefit here. See "Why SQLite" above.

---

#### Consequences

**Positive:**
- Queryable operational history enables state machine decision support for 14-day
  fertigation window and other future queries
- Schema is extensible — new columns or tables can be added without breaking existing queries
- Normalized structure supports daily reports, LLM summarization, and trend analysis
- `system_events` table is independent of cycle lifecycle — safety events always logged
- Two-phase write pattern for `watering_cycles` enables "cycle in progress" queries

**Neutral:**
- The AppDaemon add-on adds one infrastructure component; SQLite is a single file (no
  second add-on, no driver, no charset setup)
- AppDaemon requires Python maintenance — adds a new skill/dependency to the project
- `zone_id` denormalization in `fertigation_doses` is a minor schema impurity accepted
  for query convenience

**Negative / Risks:**
- AppDaemon is an additional failure point in the write path. If AppDaemon is down,
  DB writes are missed. Mitigation: AppDaemon failure should not affect watering
  operations (DB writes are fire-and-forget from the state machine perspective)
- The SQLite file requires a backup strategy — it is automatically in HA backups, but
  operational history is valuable and off-box replication is recommended

---

#### Open Items

- [x] ADR number confirmed as ADR-011; lives in this file (no standalone ADR file)
- [x] Implementation phase confirmed: Phase 3.5 (between 3.4 and Phase 4)
- [x] Define complete HA event payload schemas for each trigger point (Phase 4 prerequisite)
  (done 2026-06-30: full contract in architecture.md §13.3.1)
- [ ] Confirm AppDaemon sensor update pattern vs. response variable in HAOS environment
- [x] Confirm HA backup includes the SQLite file
  (done 2026-06-30: backup.json shows `homeassistant` included + `exclude_database: false`)
- [ ] Define off-box replication (NAS/cloud) for the operational DB / CSV archives
- [x] Implement seasonal CSV export AppDaemon script
  (done 2026-06-30: `home-assistant/appdaemon/watering_db/db_export.py`, year-filtered
  CSVs to `/homeassistant/watering_exports/`, `system_events` audit row; not yet run live)
- [x] Integrate seasonal export trigger into winterization automation (Phase 9)
  (done 2026-06-30: `home-assistant/packages/watering_db/db_automations.yaml` fires
  `watering_seasonal_export` on `system_winterized` OFF -> ON)
- [x] Wire the docs/db_schema.sql -> AppDaemon app-folder copy into the publish/pull workflow
  (done 2026-06-30: `pull_public_repo.sh` deploys apps.yaml + db_schema_init.py +
  a copy of db_schema.sql to `/homeassistant/appdaemon/apps/watering_db/`; app moved
  to `home-assistant/appdaemon/watering_db/` out of packages/; sanitize.py whitelist updated)

---

#### Related Documents

- `docs/db_schema.sql` — version-controlled SQLite physical schema (source of truth)
- `docs/db_setup_guide.md` — HA-side setup (AppDaemon add-on, no MariaDB)
- `docs/architecture.md` §13 — Operational Database Architecture (mirrors this decision)
- `docs/impl_roadmap.md` — Phase 3.5 tracking
- ADR-007 — Heavy Program Single-Window Mode Behavior
- ADR-008 — Valve Interlock Check Design
- ADR-009 — Evening Window Independence

---

### ADR-012: Repo Pull via AppDaemon Event Trigger (2026-07-01)

**Status:** Accepted — verified live on the HA Green (Core 2025.9.4)

**Context:**
The 2025-10-05 incident (`docs/repo_pull_incident_report.md`) closed the automated
repo pull as non-functional: the HAOS `shell_command` integration ran from
Developer Tools but never from a script/automation context, and returned cached
output. Manual SSH pull was the accepted workaround. Since then AppDaemon was
deployed for the operational DB (ADR-011), proving it (a) listens for HA bus
events and (b) writes into `/homeassistant/` reliably.

**Decision:**
Add an AppDaemon app (`home-assistant/appdaemon/repo_pull/`) that listens for the
`watering_repo_pull` bus event (fired by `input_button.repo_pull` via
`home-assistant/packages/repo_pull.yaml`) and runs a guarded pipeline:
preflight interlock → partial config backup → run `pull_public_repo.sh` as a
`subprocess` → validate via HA-core `check_config` → full restart. The shell
script (the proven file-copy map) is **reused via subprocess, NOT via
`shell_command`**; the SSH path is retained as fallback.

**Key design points:**
- **Interlock fail-closed:** abort if any watering relay is ON or the state
  machine is in an active (actuating) state. The hardware relay check is the
  load-bearing guard. (The original design also blocked on `manual_override`;
  that was removed 2026-08-18 — see the addendum below.)
- **Validation** uses HA-core `POST /api/config/core/check_config` via the
  `homeassistant_api` proxy (SUPERVISOR_TOKEN), NOT the Supervisor-native
  `/core/check` (which 403s at the add-on's role). Restart is gated on an explicit
  `{"result":"valid"}` and **fails safe** (skip restart + notify) otherwise —
  never restart into an unverified config.
- **Backup** uses `hassio.backup_partial` (`homeassistant=True`) with a generous
  `hass_timeout`; AppDaemon's ~10 s default gives up mid-job.
- The ~40 s pull runs in a **worker thread** so AppDaemon's scheduler is not
  blocked.
- **Verify-by-side-effect:** success requires exit 0 AND a fresh `version.json`;
  every stage writes a persistent notification + a `system_events` audit row.

**Consequences:**
- Repo pulls are now push-button from the HA UI, guarded against mid-cycle
  execution, with an automatic pre-pull backup and validated auto-restart. SSH
  remains available.
- The pull self-overwrites its own AppDaemon app during a pull, causing a brief
  AppDaemon reload; the trailing HA restart supersedes it. Benign.
- The AppDaemon path is additive (reuses the script's copy map); pruning of
  upstream-deleted files still relies on the script's rsync behavior via SSH.

**Verified 2026-07-01** on the HA Green (Core 2025.9.4): interlock abort, pre-pull
backup, pull, config-valid, and auto-restart all confirmed in the AppDaemon log.

**Related:** `docs/repo_pull_incident_report.md` (resolution), ADR-011 (AppDaemon
/ operational DB), START_HERE gotcha on `shell_command`.

**Addendum 2026-07-01 -- pruning requires rsync in the add-on containers:**
`pull_public_repo.sh` mirrors `packages/`, `scripts/`, and `esphome/` with
`rsync -a --delete` **only when rsync is present**; otherwise it falls back to
`cp` which copies but NEVER deletes. The pull runs in the AppDaemon container
(button) or the SSH container (manual) -- neither ships rsync by default, so a
file removed from the repo lingered on the Green. This bit us: a
`packages/repo_pull/` subdir was removed from the repo but not from the Green,
and its duplicate `!include_dir_named` basename silently dropped the whole
`repo_pull` package (button + sensors). Fix / setup:
- Install rsync via **add-on config** (persistent; a manual `apk add` is wiped on
  restart): AppDaemon add-on `system_packages: [rsync]`; Terminal & SSH add-on
  `packages: [rsync]` (Advanced SSH add-on uses `apks:`). Restart the add-on.
- The first `--delete` pull prunes anything on the Green not in the repo. Preview
  it first with **`PULL_DRY_RUN=1 /bin/sh /config/scripts/pull_public_repo.sh`**
  (rsync `--dry-run -i`; removals print as `*deleting <path>`; writes nothing).
  `secrets.yaml`, `.esphome/`, and `.gitignore` are excluded from the esphome
  mirror; the AppDaemon apps deploy is cp-only (never pruned).
- The button pull's pre-pull partial backup is the safety net if a prune is wrong.
Verified 2026-07-01: dry-run showed zero deletions, then a live prune-test
(`touch /config/scripts/_prune_test` -> pull -> gone) confirmed rsync `--delete`
active in the AppDaemon container.

**Addendum 2026-08-18 -- parked control states no longer block a pull:**
The preflight interlock originally blocked on THREE signals: any relay ON, an
active `state_entity` state (which listed `manual_override`), and the
`manual_override_entity` boolean being ON. In practice this collided with the
end-of-testing park SOP (ADR / START_HERE): the system is deliberately parked in
`manual_override` between sessions, so every pull required first un-parking to
`idle`, then re-parking afterward — pure friction with no safety gain. Removed
both `manual_override` blockers:
- `active_states` in `apps.yaml` no longer lists `manual_override` (it never
  listed `winterized`, so both parked control states are now non-blocking, on par
  with the already-excluded error-idle states).
- the `manual_override_entity` config key + its `_preflight_block_reason` check
  were deleted from `repo_pull.py`.

**Safety reasoning:** the parked control states have relays de-energized by
definition; the relay-ON check remains the load-bearing, fail-closed guard, so a
manually-energized relay still blocks a pull. Both `input_boolean.manual_override_active`
and `input_select.watering_system_state` are RestoreEntity (ADR-017), so the park
is preserved across the pull's validated auto-restart — the system comes back up
still parked in `manual_override`. Net effect: you can pull while parked, safely,
without touching the park. (Files: `home-assistant/appdaemon/repo_pull/apps.yaml`,
`repo_pull.py`; the app self-updates on the next pull.)

**Related:** ADR-016 (R6/R7 rest CLOSED, so an idle system passes the relay check),
ADR-017 (RestoreEntity park persistence), START_HERE repo_pull gotcha.

---

### ADR-013: Script Event Logging to `system_events` via Bus Event (2026-07-31)

**Status:** Accepted.

**Context:** Phase 3.1/3.2 zone and pump scripts logged safety/error/info events
to `system_log` (permanent but unstructured) and `input_text.cycle_event_log` (a
255-char-capped, non-persistent helper that resets each cycle). Neither gave a
durable, queryable record. The operational DB (ADR-011) already existed, and its
`system_events` table (Event 5 of the §13.3.1 contract) needs no cycle
correlation, so it could be wired up independently of the Phase 4 state machine.

**Decision:**
- Scripts call a single reusable HA script, `script.log_system_event`
  (`home-assistant/packages/watering_scripts/logging_scripts.yaml`), instead of
  writing `system_log` directly. It (1) writes `system_log` (kept as the free,
  always-available diagnostic channel) and (2) fires the `watering_system_event`
  bus event.
- A new AppDaemon app, `DbEventWriter`
  (`home-assistant/appdaemon/watering_db/db_event_writer.py`), listens for that
  event and INSERTs one `system_events` row. Scripts NEVER write SQLite directly
  — a DB error must never stall the watering/safety path (§13.1). The writer
  validates and never raises (bad payload -> `event_rejected` row + skip).
- **Severity ladder** extended to `info / warning / error / critical` (added
  `error`; see architecture.md v1.5.3) so the DB severity maps 1:1 to the HA
  `system_log` level with no lossy remap. `error` = operation aborted/failed but
  contained (interlock, tank low, relay-verify); `critical` reserved for
  catastrophic events needing physical intervention (pump runaway). `debug`
  deliberately excluded — transient diagnostics stay in `system_log` only.
- One deliberate exception stays `system_log`-only: the `stop_main_pump` runaway
  retry heartbeat (logs every ~20 s for up to 120 min), to avoid hundreds of DB
  rows; the DB captures the runaway's start/resolution/failure transitions only.

**Consequences:** `input_text.cycle_event_log` is superseded and can be retired
once the (Phase 3.4) safety scripts stop using it. Adding a severity value
requires a one-time SQLite table rebuild (CHECK cannot be `ALTER`ed; the
bootstrap's `CREATE TABLE IF NOT EXISTS` skips an existing table) — see the
`db_schema.sql` change log. Verified on the HA Green: fault-path rows
(`pump_relay_fault`, `zone_open_abort`, etc.) persist correctly; happy-path rows
that need working relays were pending a relay-board hardware fix.

**Related:** ADR-011 (operational DB), architecture.md §13.1 / §13.3.1 / v1.5.3.

---

### ADR-014: Correlation-ID Minting for Cycle / Zone-Run Events — Timestamp Scheme (2026-08-05)

**Status:** Accepted.

**Context:** The §13.3.1 event contract requires the Phase 4 state machine to stamp
two opaque correlation identifiers — `cycle_uuid` (Events 1/3/4) and `zrun_uuid`
(Events 2/3). They are needed because the SQLite primary keys (`cycle_id`,
`zrun_id`) are assigned at INSERT time — *after* the events fire — and several
events for one cycle/run are fired at different moments across separate script
executions and `wait`/`delay` states. AppDaemon resolves the ids to real keys via
an in-memory map (`cycle_uuid -> cycle_id`, `zrun_uuid -> zrun_id`). The generation
mechanism was left open: HA Jinja has no native UUID filter, and the candidates
were an execution `context.id` (ULID) or a dedicated generated value, "confirm
against the deployed HA version when Phase 4 is built."

Key constraints that shape the choice:
- The id must survive across separate script executions and waits → it **cannot be
  a run-scoped variable**; it must be stored where later events can read it.
- Uniqueness is required **only within one live cycle's in-memory map** — the id is
  never persisted to the DB and never needs to be distinguishable from a cycle that
  ran last season.
- On this single installation **cycles never overlap and zone runs are strictly
  sequential** (§13.1), so nothing is ever "live" at the same instant.

**Decision:**
- **Generation.** Mint each id as a microsecond-precision UTC timestamp taken at the
  start of its scope, with a scope prefix so a cycle id and a zone-run id can never
  collide even in the same microsecond:
  - `cycle_uuid` = `{{ 'c-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') }}` → e.g. `c-20260805043012123456`
  - `zrun_uuid`  = `{{ 'z-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') }}` → e.g. `z-20260805043118654321`
- **Storage.** Two reusable `input_text` helpers, overwritten each scope (safe
  because nothing overlaps):
  - `input_text.cycle_uuid` — set by `script.state_preflight_check` immediately
    before firing Event 1 (`watering_preflight_complete`); read unchanged by Event 3
    (`watering_zone_run_complete`) and Event 4 (`watering_cycle_complete`).
  - `input_text.zone_run_uuid` — set at the start of each zone run; read by every
    Event 2 (`watering_fert_dose_complete`) for that run and by that run's Event 3.
- **Field names unchanged.** The contract fields stay `cycle_uuid` / `zrun_uuid` —
  they name the *role* (a self-minted correlation handle following the UUID
  pattern), not the format. AppDaemon treats the value as an opaque string, so there
  is no consumer-side change.

**Rejected alternatives:**
- **Execution `context.id` (ULID)** — a genuinely opaque, globally-unique id, but
  its template access (`this.context.id`) is version-sensitive and would leave a
  live-verification tail against the deployed HA — the very open item this ADR
  closes. The timestamp scheme depends only on `utcnow().strftime`, already used in
  `logging_scripts.yaml`, so it needs no HA-version confirmation.
- **Native UUID filter** — HA Jinja has none.
- **Auto-increment / serial number** — impossible: the state machine cannot know the
  DB serial before the INSERT it is announcing.

**Consequences:**
- Closes START_HERE follow-up #1 with no outstanding live check. (Optional sanity
  check: paste `{{ utcnow().strftime('%Y%m%d%H%M%S%f') }}` into Dev Tools →
  Template and confirm a 20-digit microsecond string.)
- The value is human-readable and encodes the scope's start moment (a debugging
  nicety), but it **must be treated as opaque** — nothing may parse it back into a
  time or assume ordering semantics beyond "distinct."
- Uniqueness holds **only** under the single-cycle / sequential-run invariant. If
  concurrent cycles or parallel zone runs were ever introduced, a microsecond
  timestamp would no longer guarantee distinctness and this scheme would need a
  counter or a switch to ULID. Documented here so that invariant is explicit.
- The helpers persist across HA restarts (input_text), but per §13.3.1 the
  AppDaemon map does not survive an *AppDaemon* restart; a restart mid-cycle drops
  correlation regardless of the id scheme (accepted — non-safety reporting).
- Phase 4 implementation must: create the two `input_text` helpers, set them at the
  two minting points above, and include them in the `event_data` of the relevant
  events.

**Related:** ADR-011 (operational DB), ADR-013 (Event 5 logging),
architecture.md §13.3.1 / v1.5.4. **Amended by ADR-015** — parallel plain-watering
zone runs DO occur (they are the case this ADR's consequences flagged); ADR-015
resolves them with per-zone-scope minting rather than the shared helper.

---

### ADR-015: Phase 4 State-Machine Control Structure (2026-08-05)

**Status:** Accepted; **implemented 2026-08-09** (Phase 4 Steps 1-5, plain-watering
path — see the "Build addendum 2026-08-09" at the end of this ADR for the
build-time decisions and any deviations). Committed to main; not yet deployed
(pending adversarial review).

**Context:** Phase 4 builds the plain-watering path
(`idle → window_check → preflight_check → watering_plain → post_cycle_relief → idle`)
as scripts + automations that fire the §13.3.1 events. Four control-structure
questions had to be settled before writing YAML — how transitions are driven, how
context crosses stateless transitions, where per-zone Event 3 is emitted (given a
conflict with ADR-014, below), and how the cycle DB row is always closed even when
a cycle aborts. Fertigation states and live-hardware validation are out of scope
(RS-485 pumps unwired; ESP32 offline — Dev Tools only).

**Decision:**

- **D4 — Transition mechanism: dispatcher + self-advancing scripts.**
  - A single **dispatcher automation** triggers on `input_select.watering_system_state`
    changing and `choose`s on the new value to call `script.state_<state>`. Runs
    `mode: queued` so a rapid next-state change is never dropped.
  - Each `state_*` script **sets the next state at its own tail** — the next
    operational state on success, or an `error_*` state on failure — matching the
    existing Phase 3 idiom (`safe_shutdown` sets `idle`; the pump/zone scripts set
    `error_*` themselves).
  - A **separate scheduler automation** owns cycle *start*: time triggers for the
    morning/evening windows (gated by `enable_*_window`) plus a manual test trigger;
    condition `state == idle and not winterized/override`; action sets the D2 context
    helpers then moves `idle → window_check`.
  - Rejected: an *orchestrator* automation that awaits each script then sets the next
    state centrally (scripts would lose the self-contained error-setting idiom); and
    *pure script chaining* with no dispatcher (breaks the roadmap's "manually set a
    state in Dev Tools to test it" requirement).

- **D2 — Cross-transition context via helpers.** State transitions carry no
  parameters, so the scheduler records cycle context in two new helpers the
  downstream scripts read: `input_select.active_watering_window` (`morning`/`evening`,
  consumed by `run_zone_sequence`) and `input_select.active_trigger_type`
  (`scheduled`/`manual`/`override`, → Event 1 `trigger_type`).

- **D1 — Event 3 emitted inside `run_zone_sequence`; parallel-safe per-zone uuids.**
  ADR-014 assumed "zone runs are strictly sequential" and reused one
  `input_text.zone_run_uuid`. That holds for fertigation (single-zone) but **not** for
  plain watering's `parallel` sequencing mode, where zone runs overlap and a shared
  helper would be overwritten before a zone's Event 3 fires. Resolution:
  - `run_zone_sequence` is instrumented so **each zone's sub-sequence mints its own
    `zrun_uuid` as a local (run-scoped) variable**, captures that zone's start/end
    time, and fires Event 3 (`watering_zone_run_complete`) at the zone's close with
    the uuid in the payload. Local scope makes it parallel-safe.
  - To guarantee distinctness even if two `parallel:` branches read `utcnow()` in the
    same microsecond, the zone id is appended:
    `zrun_uuid = 'z-' ~ utcnow().strftime('%Y%m%d%H%M%S%f') ~ '-' ~ zone_id`.
    AppDaemon treats the value as opaque, so the longer form is contract-compatible.
  - The shared `input_text.zone_run_uuid` helper is **reserved for the fertigation
    path** (strictly sequential, single-zone), where Event 2 doses fired mid-run must
    read the same uuid as the run's Event 3. §13.3.1 clarified accordingly.
  - Rejected: re-implementing the per-zone loop in `state_watering_plain` (duplicates
    tested zone logic, and per-zone close times are hard to recover in parallel mode);
    and forcing plain watering to sequential-only (drops a shipped feature).

- **D3 — `script.finalize_cycle_record`: reporting-layer cleanup ONLY.** Event 1 opens the
  `watering_cycles` row and turns `binary_sensor.watering_cycle_active` on; only
  Event 4 closes it — so every cycle-ending path (normal, abort, error, e-stop) must
  fire Event 4 or the row leaks. A single `script.finalize_cycle_record(outcome, notes)`:
  - fires Event 4 (`watering_cycle_complete`) from `input_text.cycle_uuid`, then
    clears the helper; **no-ops** when no cycle is open (empty `cycle_uuid` /
    `watering_cycle_active` off), so calling it outside a cycle is safe.
  - is **strictly DB + cycle-sensor bookkeeping**: it must **never** run pressure
    relief, stop hardware, or set the system state. It does **not** supersede or
    trigger any error-state teardown. `emergency_stop` / `safe_shutdown` retain sole
    ownership of hardware safing and state latching; they merely *also* call
    `finalize_cycle_record` afterward to tidy the report. This keeps `finalize_cycle_record` off the
    safety path entirely (§13.1, DB is fire-and-forget).
  - Happy path: `state_post_cycle_relief` (built from subscripts — `close_all_zones`
    defensively, `open_pressure_relief`, R10 off) calls `finalize_cycle_record('completed')`
    then sets `idle`. Abort/error paths call `finalize_cycle_record('aborted'|'error')` from
    their existing teardown, changing nothing about how they safe the hardware.

**Consequences:**
- New Phase 4 helpers: `input_text.cycle_uuid`, `input_text.zone_run_uuid`
  (ADR-014), `input_select.active_watering_window`, `input_select.active_trigger_type`.
- New scripts: `state_window_check`, `state_preflight_check`, `state_watering_plain`,
  `state_post_cycle_relief`, `finalize_cycle_record`. New automations: dispatcher + scheduler
  (`watering_state/state_machine.yaml`).
- `run_zone_sequence` (Phase 3.1) will be modified — it gains per-zone uuid minting,
  timing capture, and Event 3 firing. Its existing zone-control behaviour is
  unchanged; the additions are reporting-only and must not alter watering logic.
- Fertigation zone-run correlation (future) still uses the shared
  `input_text.zone_run_uuid` per ADR-014; the two paths mint `zrun_uuid`
  differently by design (local per-zone for parallel plain; shared helper for
  sequential fert).

**Related:** ADR-011, ADR-013, ADR-014 (amended here re: parallel runs),
architecture.md §2 / §13.3.1, impl_roadmap.md §4.

**Addendum 2026-08-05 — design-walkthrough decisions (D-A…D-H).** A step-by-step
walkthrough of the plain-watering states (needs / transition / branches / hang
risks) settled the following; these complement the D1–D4 control structure above.

- **D-A — Weather unavailable in `window_check`:** fall back to a safe default
  program (`normal`) and log a warning; never abort the cycle on a missing API read,
  never blind-water heavy.
- **D-B — Fert-due branch while fert is out of scope:** `preflight_check` falls back
  to `watering_plain` (+ log) and never routes to the unbuilt `fert_prep`. Deployment
  default: set the fertigation 14-day targets to 0 in HA so the fert-eligibility check
  returns "none due" and the branch is never reached anyway (belt-and-suspenders).
- **D-C — Cadence gate:** none *(CLOSED 2026-08-22 by ADR-020)*. Was deferred because
  no last-watered helper existed; `sensor.zone_N_watering` now supplies it, so
  `state_window_check` gates each zone on a per-zone interval. See ADR-020.
- **D-D — Error handling = one thin automation PER error state** (not a single
  multi-error automation), each triggering on the state changing *to* that error and
  calling the shared `finalize_cycle_record` script (Layer-1 DB/sensor cleanup: fires
  Event 4, clears `cycle_uuid`, no-op if no cycle open). **Sequencing:** the script
  that detects a fault does its work and sets the error state as its *final action*;
  that state change fires the matching cleanup automation (e.g. `emergency_stop` safes
  all relays + notifies, THEN sets `error_e_stop` → `on_error_e_stop` → finalize).
  - `on_error_e_stop`, `on_error_comms_lost` → **finalize only** (hardware already
    safed / unreachable; comms recovery owned by Part B).
  - `on_error_tank_low`, `on_error_valve_interlock`, `on_error_relay_state` →
    `safe_shutdown` then `finalize_cycle_record`.
  - **D-D1:** `safe_shutdown` runs **uniformly** for the three hardware errors even if
    nothing had started (idempotent; simpler than detecting "nothing ran").
  - Each automation sets **no** state: `safe_shutdown`'s `ended_in_error` guard
    preserves the latch, and the `already_errored` guards in the pump/zone scripts
    stop `safe_shutdown` from mutating state, so each fires exactly once.
- **D-E — HA-restart recovery (thorough, D-E1):** one automation on
  `homeassistant.start`; for **any non-idle state** call `safe_shutdown` then
  `finalize_cycle_record` (both `continue_on_error`). Operational states clear to
  `idle`; error states keep their latch (guards); a row leaked by a crash mid-handler
  gets closed. `input_text.cycle_uuid` persists across restart so finalize can still
  fire (AppDaemon-map loss = accepted unresolved-correlation, §13.3.1).
- **D-F — `manual_override` / `winterized` engagement = GUARD, not auto-abort
  (revised).** The boolean is the source of truth; the matching state mirrors it. But
  the system NEVER silently aborts a running cycle to satisfy an override — the user
  must stop the cycle first, deliberately. An entry automation per control boolean
  (`input_boolean.manual_override_active`, `input_boolean.system_winterized`) gates on
  current state, three ways:
  - `idle` → engage (park in `manual_override` / `winterized`).
  - any **operational** state (`window_check`/`preflight_check`/`watering_plain`/
    `post_cycle_relief`) → **reject**: revert the boolean to OFF and notify *"a cycle
    is running; stop it before proceeding."*
  - any **`error_*`** → show the error as a warning, require **acknowledgement**, then
    engage. (Ack mechanism = UX/build detail; shares D-H's reset UX.)
  - Exit (boolean → OFF): plain return to `idle` (no forced re-safe — the next cycle's
    `preflight_check` re-verifies; manual mode may have intentionally left a relay set).
  - **Consequence:** with no auto-abort on engage, the `'aborted'` outcome producer
    moves to the **future safe-stop UX button** (`safe_shutdown` + `finalize('aborted')`).
    In current Phase 4 scope, stopping a running cycle = `emergency_stop`
    (→ `error_e_stop`, finalized `'error'`); there is no `'aborted'` producer yet.
  - **Deferred (another day):** safe-stop / emergency-stop dashboard buttons; the
    fertigation **flush branch** on safe-stop (flush-then-proceed, or a flush branch
    inside safe-stop).
  - **Build watch-item:** the seasonal-export trigger currently fires on
    `system_winterized` OFF→ON; ensure a *rejected* (reverted) winterization doesn't
    fire a spurious export — trigger the export off the `winterized` **state** (entered
    only after the guard passes) or gate it on `idle`.
- **D-G — Tank sensor `unavailable` at `preflight_check`:** treat as
  `error_comms_lost` (read/comms failure), distinct from `error_tank_low` (a genuine
  low reading).
- **D-H — Reset model:** manual reset for `error_tank_low` / `error_valve_interlock` /
  `error_relay_state` (user clears to `idle` after fixing the fault); only
  `error_comms_lost` auto-recovers (Part B).

**Mid-cycle abort — A1 (mandatory) + A2 (script cancellation).** A safety event can
fire *in parallel* while a long-running state script is mid-delay (e.g. a tank
monitor or comms loss calls `emergency_stop` during `run_zone_sequence`). Without
protection, when the delay ends the script's tail would set the *next* state and
**overwrite the latched `error_*`**, un-latching the emergency and running a normal
teardown. Two parts:
- **A1 (mandatory correctness rule):** every `state_*` script guards its advance —
  *only set the next state if the system is still in my own state.* If a parallel
  event moved us to an `error_*`/control state, the script exits without advancing.
  Enshrined like the no-`continue_on_error` rule; A1 alone makes the system correct.
- **A2 (prompt cancellation):** a single `abort_cycle_scripts` script `script.turn_off`s
  the in-flight progression scripts (HA `script.turn_off` does NOT cascade to
  subscripts, so the set must be named). Called by the five per-error automations,
  restart recovery, and the D-F control-state automations, **before** `safe_shutdown`.
  - **In the list:** `state_window_check`, `state_preflight_check`, `state_watering_plain`,
    `state_post_cycle_relief`, `run_zone_sequence` (the important long-delay one).
  - **NEVER in the list** (would sabotage cleanup): `safe_shutdown`, `emergency_stop`,
    `stop_main_pump`, `close_all_zones`, `close_pressure_relief`,
    `finalize_cycle_record`, `log_system_event`.
  - The list is **best-effort** (maintained in ONE place): because A1 owns
    correctness, a missing entry only leaves a harmless delay running to completion.

**Resolved build-detail decisions:**
- **Scheduler manual trigger:** one `input_button.start_watering_cycle_now`
  (testing/on-demand) → set `active_trigger_type: manual`, pick `active_watering_window`
  by time of day (morning before midday, else evening), then `idle → window_check`
  (same `state == idle` guard). Time triggers use `active_trigger_type: scheduled`.
  **`override` trigger_type is NOT used in Phase 4** (reserved for a future forced /
  weather-bypass run; `manual_override` parks the machine so nothing runs "in override").
- **Event 1 `temp_high_c`:** record `sensor.brightsky_temp_high_yesterday` (matches the
  "high temp" field semantics). The decision driver (`temp_avg_high_3day`) need not
  live here — the decision *outcome* is captured per zone as `weather_program` (Event 3).
- **Error notifications wired in Phase 4** (Phase 9 notification system is built): each
  per-error entry automation sends a tier-appropriate notification as part of its
  trigger — EXCEPT `on_error_e_stop` (`emergency_stop` already sends its own critical
  notification). Keeps `notify` out of the pump/zone script branches.

**Invariant — "the cycle row always closes":** every path that fires Event 1 has
exactly one Event-4 owner — `post_cycle_relief` (`completed`), the per-error automation
(`error`), restart recovery (`error`), or the future safe-stop UX (`aborted`; no
producer in current scope).

**Principle enshrined:** operational `state_*` scripts must NOT `continue_on_error`
around safety-critical subscripts — let the error propagate so the subscript's
`error_*` state fires the matching per-error automation. This removes finalize-on-
error logic from the state scripts (notably simplifying `post_cycle_relief`). Paired
with **A1** (guard the state-advance) as the two correctness rules for the state scripts.

**Full automation roster (Phase 4):** scheduler, dispatcher, five per-error entry
automations (D-D, each also notifying per #3 except e-stop), restart recovery (D-E),
two control-state guard automations (D-F: `on_manual_override_active`,
`on_system_winterized`), plus the existing comms Part B
(`watering_safety_r1_comms_recovery`). Shared scripts: `finalize_cycle_record`,
`abort_cycle_scripts`.

**Build addendum 2026-08-09 — implementation & revisable build-time decisions.**
Steps 1-5 were built as designed; the following calls were made during the build.
All are revisable — revisit here if the adversarial review or Test 3.6 surfaces a
reason.
- **File placement:** `finalize_cycle_record` + `abort_cycle_scripts` live in
  `watering_state/state_scripts.yaml` alongside the `state_*` scripts (not
  `logging_scripts.yaml`) — cohesive with the cycle lifecycle, and `abort_cycle_scripts`
  names the `state_*` set so co-location keeps that list in one place. Automations in
  `watering_state/state_machine.yaml`. Both basenames verified globally unique.
- **D-F `error_*` engagement = engage-with-warning** (the ADR left the ack UX
  deferred). From an `error_*` state, toggling override/winterize ENGAGES it and sends
  a high-tier warning that the error was not auto-cleared, rather than blocking —
  manual control is often wanted precisely to fix a fault; the deliberate toggle is the
  acknowledgement. Confirmed by the user 2026-08-09. (Alternative if ever needed:
  reject-until-cleared.)
- **Error notification tiers:** `error_tank_low` / `_valve_interlock` / `_relay_state`
  → `send_critical_notification`; `error_comms_lost` → `send_high_notification` (Part B
  auto-recovers); `error_e_stop` → none (`emergency_stop` already sends its own
  critical). Each per-error automation calls `abort_cycle_scripts` +
  `finalize_cycle_record` with `continue_on_error` so finalize always runs (invariant).
- **Valve physical-travel delay = 12 s** (datasheet travel 6-10 s) wherever a step
  depends on a valve's ACTUAL position: in `state_watering_plain`, 12 s after the R6/R7
  interlock (before `start_main_pump` reads it) and 12 s after `close_all_zones` (before
  `post_cycle_relief` opens R9). Relay-state `is_state()` checks reflect fast coil ack
  and keep their existing ~3 s delays — distinct concern.
- **preflight ESP32-online check** uses R1 (`relay_1_main_pump`) availability as the
  proxy (all relays share the one ESP32/WiFi link); tank-sensor `unavailable` →
  `error_comms_lost` (D-G).
- **Seasonal-export retarget (D-F watch-item):** `watering_db/db_automations.yaml` now
  triggers the export on `input_select.watering_system_state` → `winterized` (entered
  only after the winterized guard passes), not the `system_winterized` boolean edge, so
  a rejected winterization no longer fires a spurious export.
- **`run_zone_sequence` Event 3 `aborted` is always 0** in the emitted events: an
  aborted zone is killed mid-delay by `abort_cycle_scripts` before reaching its Event 3,
  so it emits none. Only the CYCLE row is guaranteed to close (finalize); zone-run rows
  are best-effort telemetry — consistent with the invariant's scope.
- **Deferred, unchanged by the build:** fert states; live-hardware validation (ESP32
  offline); the AppDaemon write-listeners that CONSUME Events 1/3/4 (Phase 3.5 — only
  Event 5 is consumed today, so Events 1/3/4 fire to no DB writer yet); the safe-stop UX
  + `'aborted'` outcome producer. Test plan: test_scenarios.md Test 3.6.

---

### ADR-016: Fert-Manifold Valves Closed at Rest (Valve Discipline) (2026-08-14)

**Context.** R6 (fert bypass) / R7 (fert line) were left with R6 **open** at rest
(bypass selected), on the reading that the R6-XOR-R7 interlock requires *exactly one*
path open at all times. Operator practice (marine cargo PIC discipline) argues the
opposite: a valve not in use is closed. Holding R6 energized 24/7 also had two concrete
costs surfaced during the Phase 4 Test 3.6 dry run: (a) it is wear/leak-prone to pin a
motorized valve open indefinitely, and (b) it broke the `repo_pull` preflight interlock,
whose "all actuating relays off" guard (R1–R7, R9) can never be satisfied at rest while
R6 is held on — the pull button aborted silently on every press.

**Decision.** The resting state is **both R6 and R7 closed** (no flow path selected).
The R6-XOR-R7 requirement is re-scoped as a **pump-start precondition**, not a standing
invariant:
- `state_watering_plain` already opens R6 (closes R7) as its first step, then waits the
  12 s valve-travel delay *before* `start_main_pump` reads the interlock — so the check
  still sees a valid XOR at the only moment it runs.
- `state_post_cycle_relief` and `safe_shutdown` now **close both R6 and R7** as cleanup,
  after the pressure-relief bleed and before cutting 24 V cabinet power (R10), so the
  motorized valves still have power to travel.
- No continuous monitor enforces XOR (verified: `error_valve_interlock` is set only in
  `start_main_pump` and `open_zone`, both operational-path checks that run after R6 is
  open), so both-closed-at-rest trips nothing.

**Consequences.**
- Rest is now `R6 off / R7 off`; a fresh idle snapshot shows both closed.
- `repo_pull`'s relay list is left **unchanged** and is now *correct*: at rest all listed
  relays are off so the guard passes; if R6 is ever found open, blocking the pull is the
  right call. (Supersedes the interim idea of dropping R6/R7 from the list.)
- architecture.md §5 "both ON or both OFF → error" is clarified: both-OFF is the valid
  resting state; the XOR error applies at pump-start.
- Supersedes the prior guidance "R6 open / R7 closed is the safe resting interlock."

**Related:** ADR-012 (repo_pull interlock), ADR-015 (state scripts), architecture.md §5.

---

### ADR-017: State / Latch Helpers Are RestoreEntity (No `initial:`) (2026-08-15)

**Context.** The Phase 4 restart-recovery automation (`watering_state_restart_recovery`,
ADR-015 D-E) and `safe_shutdown` are written to assume that the system-state and control
booleans **restore** their last value across an HA restart — the recovery comments say
verbatim "Both booleans are RestoreEntity, so a control state simply persists across the
restart." They did not. `input_select.watering_system_state` (`initial: idle`),
`input_boolean.manual_override_active` (`initial: false`), and
`input_boolean.system_winterized` (`initial: off`) each had `initial:` set. In Home
Assistant, an `input_*` helper with `initial:` configured returns early in
`async_added_to_hass` and **never calls `async_get_last_state()`** — so it resets to the
`initial:` value on every restart instead of restoring. Only `cycle_uuid` / `zone_run_uuid`
(no `initial:`) restored, which is why the "cycle row always closes" invariant held while
the rest of recovery silently failed.

Confirmed empirically (2026-08-15): set `watering_system_state` → `error_e_stop`, restarted
HA via the repo-pull button, system came up `idle`. Verified there is no code path that
turns a *restored* `error_e_stop` into `idle` (recovery branch (a) → `safe_shutdown`
preserves `error_*` via its `ended_in_error` guard; the inner idle-backstop and `on_error`
both exclude `error_*`), so the `idle` reading proves the state did not restore.

Consequences of the pre-fix behaviour: (a) a **mid-cycle restart came up `idle`**, so
recovery branch (a) was skipped and hardware was **never safed** (relays held whatever
ESPHome left them); (b) **error latches were lost** (defeats "latched for human review");
(c) **winterization silently cleared** on any restart — a winter power-blip un-winterized
the system and skipped the de-winterization test (it left `winterized` via reset, not via
the `control_guard`).

**Decision.** Persistence-across-restart is a **safety requirement** for these three
entities, so they must be RestoreEntity: **remove `initial:`** from
`watering_system_state`, `manual_override_active` (config_helpers.yaml), and
`system_winterized` (notification/helpers.yaml). Each carries a comment forbidding the
re-addition of `initial:`.

First-boot fallback (no stored state) is safe and needs no code:
- `input_select` with no `initial:` and no restorable state defaults to **`options[0]`**,
  which is `idle` — the safe resting state. (It does **not** come up `unknown`; the
  recovery branch (a) `unknown` handling is harmless belt-and-suspenders that is not
  reached, because `homeassistant.start` fires after the entity already holds its default.)
- `input_boolean` with no `initial:` and no restore defaults to **`off`** — override and
  winterized both off, i.e. safe/operational.

**Consequences.**
- A mid-cycle restart now comes up in its real operational/error state, so recovery
  branch (a) fires and safes the hardware; error latches survive; winterization survives.
- General rule (already a Top Gotcha): **when persistence-across-restart is required, do
  NOT set `initial:`.** `initial:` is for entities that should reset to a known default
  each boot — the `active_*` cycle-context selects (the scheduler overwrites them at cycle
  start) and the `input_number` config/test values (`max_single_zone_runtime_min`,
  `pressure_relief_duration_sec`; `watering_cycle_days` was retired 2026-08-22 — the new
  per-zone `zone_N_watering_interval_days` is RestoreEntity, NOT `initial:`-reset).
- Same-class cleanup applied together with the three latch entities: **`initial:` also
  removed from `enable_morning_window` / `enable_evening_window` and `zone_sequencing_mode`**
  (config_helpers.yaml) — these are operator preferences that should survive a restart, not
  reset. With `initial: true`, a restart silently re-enabled a window the operator had
  disabled for the season; `zone_sequencing_mode` snapped back to `parallel`. First-boot
  fallback: the two window booleans default to `off` (window disabled = fail-safe, no
  watering) and `zone_sequencing_mode` defaults to `options[0] = parallel` (unchanged from
  the old default). The `input_number` values above were deliberately LEFT with `initial:`.
- Verification owed at deploy (mirror test): remove `initial:`, set `error_e_stop`, allow
  the recorder to persist (a graceful restart dumps restore-state on shutdown), restart,
  and confirm it comes up `error_e_stop`; re-check `manual_override` / `winterized`
  persistence. Give the recorder a moment before restarting — a near-instant restart can
  fail to restore even with the fix (false negative).

**Related:** ADR-015 (D-E restart recovery, D-F control guard), START_HERE §2
restart-recovery bug + §3 `initial:` gotcha, architecture.md §13 (state machine).

---

### ADR-018: Weather Observations Database + Decision-Criteria Recording (2026-08-18)

**Status:** Accepted 2026-08-18; **amended 2026-08-25 by ADR-021.** ADR-021 folded its
decision-recording need into this ADR (no separate `decisions` table): the moisture-primary
§3.2 tree is the logic the shared decision routine computes, and the `decision_criteria` /
`zone_decisions` JSON now also carries the moisture-primary inputs (moisture % +
contributing-sensor count, de-lagged temp used, forecast POP/volume, thresholds live at the
time, the branch/`skip_reason`). ADR-021 **resolves** the two "Deferred / open" items below:
the temperature metric → de-lagged forecast/current high; threshold helpers → pure RestoreEntity.
Implementation remains HELD for the sensor hardware (same gate as ADR-021).

**Context.** The §3.2 weather decision tree (`state_window_check`) chooses each zone's program
(off/light/normal/heavy) from Brightsky weather + per-zone/per-season thresholds held in
**modifiable** `input_number` helpers. Two gaps block any future evaluation of *decision
effectiveness* against the sensor hardware the user is about to install (weather station + rain
sensor + wireless soil-moisture):
1. **No record of WHY a decision was made.** The thresholds change (operator tuning; the coming
   §6.2 rework) with no trace of what was live at each decision. The ops DB records the resulting
   `weather_program` per zone and a weather snapshot on the cycle, but NOT the criteria — and
   `watering_cycles.temp_high_c` stores `temp_high_yesterday`, NOT the `temp_avg_high_3day` the
   tree actually compares. A stored decision is therefore not reproducible.
2. **No record on days we DON'T water.** `zone_runs` rows exist only for cycles that run; if all
   zones resolve `off` (or the system is parked / winterized), `window_check` returns to idle
   before any row is written. The days the system *correctly skipped* — the most informative for
   tuning — are invisible.

Surfaced 2026-08-18 when a cool, post-rain day evaluated to `heavy×4` (a localized ~10 mm shower
missed the DWD station; the trailing `temp_avg_high_3day` still carried a broken heatwave).
Late-summer extremes make this a good window to catalogue edge cases.

**Decision.** Two coordinated changes.

**(A) Record decision criteria on `zone_runs` (ops DB).** Add `season TEXT` (CHECK
spring/summer/fall/winter) and `decision_criteria TEXT` (JSON: the five thresholds, the actual
weather inputs compared — including the real `temp_avg_high_3day` — and the branch that fired).
Rows-not-changelog: each decision becomes self-explanatory, no reconstruction, no drift between
"the log" and "what ran." JSON, not wide threshold columns, because the criteria set WILL change
with the §6.2 rework — new keys carry through with no migration.

**(B) New separate weather-observations database** — a twice-daily time series independent of
whether we water, with the computed decision stored alongside, so effectiveness can be analyzed
in one place.
- **Separate SQLite file** (`watering_weather.db`), not a table in `watering_ops`: different
  lifecycle (continuous series vs event-driven cycles) and retention (long-term, no pruning vs
  ops' 14-day rolling window). Correlate to ops by `observed_at` / `window` (`ATTACH` for joins).
- **Wide schema + JSON catch-all.** `weather_snapshots` = one row per window with typed columns
  for the Brightsky set + a `raw` JSON column so a new sensor is never *lost* before it earns a
  typed column (the station integration is the natural migration point). Wide, not tall/EAV,
  because the analysis is multi-variable per observation and the per-zone decision is a
  heterogeneous bundle; a tall table's "never migrate" upside is small at twice-daily volume and
  fights every cross-metric query. (A future soil-moisture *array* — many homogeneous nodes — is
  where a tall table earns its place; it can be its own table then.)
- **Parent/child**, mirroring `watering_cycles → zone_runs`: `weather_snapshots (1) →
  zone_decisions (N=4)`. `zone_decisions` = per-zone `season`, `computed_program`,
  `program_multiplier`, `decision_criteria` JSON, `would_water` (0/1 convenience).
- **Store raw, derive semantics later.** Snapshot every temperature/rain sensor raw; defer
  "which value is *the* high" (the afternoon-window concern — yesterday 17:00 can exceed today's
  actual high) until the station is in. Nothing is lost by deferring.
- **Always-on trigger, NOT inside `window_check`.** A standalone HA automation on the SAME
  `input_datetime.morning_window_start` / `evening_window_start` helpers fires regardless of
  system state (parked, winterized, mid-cycle, idle), so skip/parked days are captured.
  Embedding in `window_check` would log only on days we water (it is gated on idle + override-off
  + winterized-off) — losing exactly the data we want.
- **One shared decision routine.** Extract the §6.2 math into a single side-effect-free routine
  (weather + zone/season config → program + multiplier + criteria). `window_check` calls it then
  *applies* (sets `zone_N_program`); the weather logger calls it to *log*. The SAME source feeds
  both `zone_runs.decision_criteria` (real runs) and `zone_decisions` (always). Single source of
  truth; de-risks the §6.2 rework (one place to change). All logic stays in HA (CORE PRINCIPLE);
  the AppDaemon writer remains a dumb sink consuming a `watering_weather_snapshot` event,
  mirroring `db_writer.py`.
- **Export-only winterized dump.** Reuse the existing winterization trigger (the `winterized`-
  state event the ops seasonal export hangs off) to ALSO dump `weather_snapshots` +
  `zone_decisions` to CSV — synchronized landing so a season's ops + weather bundles are analyzed
  together — but **export-only, NO delete** (the weather DB keeps full history in-DB; it is not
  pruned like ops). Aligns bundles to the year (winterization is annual); per-season CSVs would
  need a season-change trigger, a later add.

**Consequences.**
- Every window, every zone — run, skip, or parked — has the conditions + the exact criteria +
  the computed decision in one queryable place, ready to validate against the incoming sensors.
- New build surface: `watering_weather.db` + schema source (`docs/weather_schema.sql`), an
  AppDaemon `weather_logger` app + writer, an HA snapshot automation + package, the shared
  decision routine (a refactor of `window_check`), the two `zone_runs` columns + `db_writer.py`
  change, and the export-only winter dump. Tracked in impl_roadmap §3.5 (zone_runs) + §3.6.
- The `window_check` refactor touches a safety-adjacent script → full "Before You Code"
  checklist + code review when built. The extraction is behaviour-preserving (same math, same
  apply step).
- `decision_criteria` as JSON trades queryability/constraints for change-tolerance; acceptable
  for an audit blob (query via json1 or pandas).
- Threshold helpers (`zone_N_{season}_*`) still carry `initial:` (reset on restart) — the same
  class as the season bug fixed 2026-08-18; making them RestoreEntity was part of the §3.2 rework
  (START_HERE follow-up #4) — **now RESOLVED by ADR-021** (pure RestoreEntity).

**Related:** §3.2 rework (ADR-021, START_HERE follow-up #4), ADR-004 (program uses average daily
high — the lagging metric at issue), ADR-011 (ops DB architecture), ADR-013 (event → AppDaemon
writer), architecture.md §3.2 (decision tree) / §13.3.1 (event payload contract).

---

### ADR-019: Front-End (Dashboard UI) — Gated Process, Repo-YAML Dashboards, Glassmorphism Stack, Read-Only MCP (2026-08-18)

**Context.** Phase 7 builds the operator UI over a deliberately robust backend; the UI must match
that quality in **form and function**. The user has no UI-design experience but is exacting, and
graphic design is a known weakness of the assistant — so the process is built around a tight
**see-and-correct feedback loop** rather than blind generation. Initial scope is the **desktop**
HA UI; mobile/iPad and a minimal Apple Watch surface are explicit later tiers. Style direction is
**glassmorphism** (blurred gradient background, light/airy translucent cards); the user's
ChatGPT-made moodboards + a reference mockup are a starting point, not rules.

**Decision.** Several coordinated choices.

**(1) Seven-gate process (impl_roadmap §7.0–7.6).** Requirements & Inventory → Design Tokens →
Information Architecture → Hi-Fi Static Mockup → HA Build → Responsive Tiers → Interaction &
Hardening. Each gate has an exit checklist + user sign-off before the next. Rationale: a
non-designer reacts to concrete artifacts; the cheap iteration lives in an HTML-Artifact mockup
(Gate 7.3) *outside* HA, where the assistant is strongest, before any YAML exists.

**(2) Lovelace + Sections view + a curated HACS set** (card-mod for the glass effect;
mushroom/button-card/layout-card/kiosk-mode as needed), NOT a bespoke custom panel (which would
throw away HA's entity plumbing and break the mobile app). Each custom card is a documented
dependency.

**(3) Dashboards stored as repo YAML-mode files** under `home-assistant/dashboards/` — canonical
repo, review-before-push, deployed by the existing repo-pull (ADR-012) — NOT storage-mode.
**Provisional:** switch if it fights us (keep-decisions-revisable). Trade-off: lose the UI
drag-drop editor and live MCP card-editing; gain version control and the same discipline as the
rest of the system. Back up the existing storage dashboard before the YAML-mode conversion (it
can wipe existing views).

**(4) Fast feedback loop.** Author in the repo → direct-sync the dashboard file to the Green via
SSH/Samba (bypassing the slow guarded repo-pull) → hard browser refresh (YAML dashboards
re-render without a restart — **to be verified live**) → browser screenshot → reconcile against
the mockup → batch-commit. The Green copy is transient; the next repo-pull overwrites it
identically. Authoring uses the Write/Edit tools (repo is canonical); the browser is used only to
view/screenshot.

**(5) Tooling (all free/OSS).** `frontend-design` (Anthropic) + `ha-dashboard-design` (aurora)
skills installed at `~/.claude/skills`; `hass-mcp` (voska v0.6.0, via `uvx`, user scope) for live
inspection; in-app browser as the "eyes". Windows setup gotchas recorded in assistant memory
(full `uvx.exe` path required in the MCP `command`; the `claude` CLI is invoked via the VS Code
extension binary).

**(6) hass-mcp is READ-ONLY.** Standing rule: no operating switches/entities, no service/script
calls, no helper/variable edits, no dashboard/config writes, and no code changes without the
user's **express, per-action consent**. Any destructive step is independently verified not to
harm the system or wipe data; everything must be **recoverable** (backups / git); the "Before You
Code" checklist applies to HA/MCP/dashboard work, not just code. The token grants full HA control
and the system is parked in `manual_override` pre-go-live, so read-only is the safe default.

**(7) Glassmorphism discipline.** `backdrop-filter: blur()` is GPU-heavy → a blur-desktop /
flat-mobile performance tier. Never globally blur `ha-card` (breaks Bubble-Card pop-ups and
dropdown placement) — scope card-mod to specific cards. Legibility beats aesthetics: solid,
high-contrast values on glass. Apple Watch is a separate minimal paradigm (HA actions /
complications), not Lovelace.

**Consequences.**
- New build surface: `docs/ui_design.md` (design tokens), `home-assistant/dashboards/` (YAML +
  theme), curated HACS deps on the Green, and possibly a project-specific design skill encoding
  the locked tokens.
- `entity_reference.md` + `test_scenarios.md` get updated once UI files exist (verified IDs, UI
  test cases) — deferred until then.
- The original Phase 7 placeholder card list is retained as impl_roadmap §7.7 (content targets),
  superseded as *process* by the gates.
- All decisions here are provisional and revisable as the build informs them — update this ADR
  rather than treating it as fixed.

**Related:** impl_roadmap §7.0–7.7, ADR-012 (repo-pull deploy path), ADR-016/017 (park/restore
persistence — the `manual_override` park this read-only rule protects), CLAUDE.md (Before You
Code / all-logic-in-HA / safety defaults), START_HERE §1. Standing read-only rule is also held in
assistant memory (`hass-mcp-read-only`).

---

### ADR-020: Per-Zone Watering Cadence + Master Enable; Heavy Split → Mid-Interval Booster (2026-08-22)

**Date:** 2026-08-22
**Status:** Accepted (Phase 7). Supersedes ADR-007 and ADR-009; closes ADR-015 D-C.

**Context:**
Watering frequency was ungated — every enabled window watered, weather-modulated
(ADR-015 D-C deferred the cadence gate because no last-watered signal existed).
The operator wanted (a) per-crop cadence ("water every N days") so thirsty zones
(e.g. lettuce) run daily while others space out, and (b) a durable per-zone
on/off. `sensor.zone_N_watering` (Gate 7.2, SQL on `watering_ops.db`) now provides
the last-run timestamp, unblocking the gate.

**Decision:**
1. **Per-zone interval** `input_number.zone_N_watering_interval_days` ("water on
   day N"), RestoreEntity. Retires the unused system-wide `watering_cycle_days`.
   `state_window_check` computes days-since from `sensor.zone_N_watering` (last
   MAIN dose) and runs a MAIN dose only when `days_since >= N`.
2. **Master enable** `input_boolean.zone_N_enabled`, RestoreEntity (first-boot
   OFF = fail-safe opt-in). OFF forces the zone's program to `off` on every
   evaluation — durable, unlike selecting `off` in `zone_N_program` (which
   window_check overwrites each window). Zeroes watering AND fert.
3. **Layering** in `state_window_check`: weather tree → `wp`; then enable gate →
   rain-`off` gate (anchor NOT advanced, so a rained-off due day stays overdue and
   retries) → due→`wp` (main) → heavy mid-interval booster → else `off`.
4. **Heavy split retired** (supersedes ADR-007/009). Heavy's extra `0.5×` moves
   from a same-day evening dose to a `booster` run from the interval midpoint (N/2
   days) onward, always in the evening window (fallback morning if evening is
   disabled). There is no odd/even parity branch and no "afternoon" window — the
   parity difference is absorbed by day granularity (see the 2026-08-23 addendum
   for the retry refinement). The booster **re-evaluates** weather at the target
   window (fires only if still `heavy`), preserving ADR-009's adapt-to-conditions
   intent. Runtime is now window-independent: `heavy=1.0×`, `booster=0.5×`.
   **Edge:** N==1 single-window collides main+booster → single `1.5×` dose, no
   booster (the one survivor of ADR-007's single-window `1.5×`).

**Anchor / DB (Option 1 — no schema or AppDaemon change):**
The booster is recorded as `weather_program='heavy'` with `program_multiplier=0.5`
(mapped at the Event-3 boundary in `fire_zone_run_complete`), so the `zone_runs`
CHECK vocabulary and `db_writer.WEATHER_PROGRAMS` are untouched. `program_multiplier`
was already a column read from the payload (previously written NULL); it is now
populated. `sensor.zone_N_watering` excludes `(weather_program='heavy' AND
COALESCE(program_multiplier,1.0)=0.5)` so the interval anchor tracks MAIN doses
only — a booster must not reset the clock. `COALESCE` keeps legacy (NULL-multiplier)
rows counted as main.

**Alternatives considered:**
- *First-class `booster` weather_program value.* Rejected for v1: needs a live
  SQLite `CHECK`-constraint rebuild + `db_writer` whitelist change. Option 1 gets
  the same behaviour with zero DB migration; promote later if history display wants
  an explicit label. (Booster is fully explicit in HA — it IS a `zone_N_program`
  value — only its DB row reuses `heavy`+multiplier.)
- *Off-DB anchor helper (`input_datetime`).* Rejected: the run pipeline's only
  per-zone channel is `zone_N_program`, so the run type must ride it anyway;
  reusing the existing DB sensor is more contained.

**Consequences:**
- Zones now water LESS than before (frequency is gated) — intended. First boot
  after deploy: all zones come up disabled (RestoreEntity fail-safe) → each must be
  enabled once at go-live. System is parked in `manual_override` pre-go-live, so no
  surprise watering.
- `sensor.zone_N_watering` state AND `history` attribute both exclude boosters
  (main-dose-only semantics). Revisit if the dashboard later wants boosters shown.
- Docs updated: architecture.md v1.8.0 (§3.1–3.3, §4.1, §7.1), entity_reference,
  ui_design §7, test_scenarios (heavy runtime cases change), START_HERE §1.

**Revisable:** all thresholds/edges provisional; update this ADR as the build and
first live season inform it.

**Addendum (2026-08-23) — code-review fixes on downstream consumers:**
A high-effort review of the ADR-020 build found the state-machine core correct but
6 downstream consumers un-updated for the reworked multipliers / new `booster`.
Resolved before go-live:
- **Fix #4b (booster retry — behavior change, operator decision):** the original
  single-shot `[mid, mid+1)` band gave the booster exactly one firing chance; a
  missed evening (override engaged / evening disabled) skipped it with no retry,
  unlike the main dose. Changed to **retry**: fire on the target (evening) window
  whenever `mid <= days_since < N` **and** the booster is still pending for the
  interval — i.e. no booster recorded since the last main dose. Tracked by a new
  per-zone SQL sensor `sensor.zone_N_last_booster` (last `(heavy, 0.5×)` run) vs
  `sensor.zone_N_watering` (last main dose). Lands exactly once per interval; a
  missed evening is picked up later. Cost: one SQL sensor per zone.
- **Fix #3/#5 (single-source multiplier):** `program_multiplier` is now threaded
  from `calculate_zone_runtime` (which returns `multiplier` alongside
  `program`/`runtime_minutes`) through `run_zone_sequence` → `water_one_zone` →
  `fire_zone_run_complete`, replacing the static per-site map. This removes the
  3rd copy of the program→multiplier mapping and is the only way to record the
  **N==1 single-window heavy = 1.5×** edge correctly (the static map recorded
  1.0). The 12 fert flow-rate maps (Fix #1) still encode the mapping separately
  but now carry a KEEP-IN-SYNC comment; extracting a shared Jinja macro
  (`custom_templates`) to fully de-duplicate is logged as a follow-up (fert path
  is hardware-blocked, so not pre-go-live).
- **Fix #2:** the end-of-cycle summary now lists `booster` runs.
- **Fix #6:** corrected the `state_window_check` booster comment.

---

### ADR-021: Moisture-Primary §3.2 Program Selection + Dynamic Sensor→Zone Mapping (2026-08-25)

**Date:** 2026-08-25
**Status:** **ACCEPTED** (Phase 7, 2026-08-25). Implementation and deploy remain **HELD**
until the soil-moisture hardware is installed and calibrated.
Reworks the §3.2 weather tree (the `wp` intensity; this is the rework long tracked colloquially
as "the §6.2 rework"). **Partially supersedes ADR-004** (demotes the 3-day-average-high from the
decision path). Layers *underneath* ADR-020's cadence/booster/runtime gate, which is **unchanged**
— this ADR only changes how the `wp ∈ {off,light,normal,heavy}` fed into that gate is computed.

**Context:**
The §3.2 weather tree keys on trailing accumulations
(`rain_72h`, `temp_avg_high_3day`) with hard single-value thresholds and no current,
forecast, or soil input. On 2026-08-18 (Phase 9.10 test cycle) it set all four zones
`heavy` on a cool, overcast, just-rained day. Root causes (START_HERE follow-up #4):
(a) `temp_avg_high_3day` **lags** a broken heatwave by 2–3 days (read 30.4 °C while
yesterday's high was 25.6 and the day was 21.5 °C / 100 % cloud); (b) **no
current-conditions path** — nothing lets "cool + overcast + just rained" force a skip
short of the `rain_72h > rain_off` gate a light shower never reaches; (c) the DWD
station (~5 km away) **missed a localized ~10 mm downpour**, recording only 4.9 mm;
(d) **knife-edge** threshold — 4.9 vs `rain_min` 5.0 decided it by 0.1 mm. The design
always anticipated soil moisture (per-zone/season `*_moisture_min` helpers exist;
`fert_helpers` §4.5 deferred them to "Phase 3") but no sensor fed them. The operator is
now installing ground-truth: **4× Ecowitt WH52** wireless + **3× DFRobot SEN0600**
(RS-485) soil-moisture sensors, and an **Ecowitt WH40H** local rain gauge. Operator
decisions (this session): moisture **strictly primary**; the failure day should have
resolved to **`off`**; scope = **full design now, hold for hardware**.

**Decision:**

1. **Moisture is PRIMARY; weather MODULATES.** A per-zone aggregate
   `sensor.zone_N_soil_moisture` (%) = the **average** of every sensor currently
   assigned to the zone drives a base intensity via the existing per-zone/season
   thresholds:
   `moisture ≥ off_min → off` · `≥ light_min → light` · `≥ normal_min → normal` ·
   `else → heavy`. Weather can only nudge this base (steps 3–4); it can never escalate
   a moist zone straight to `heavy`.
2. **Wet-skip (hard → `off`):** `moisture ≥ off_min` **OR** currently raining
   (`rain_now > 0`). **Recent** rain does NOT independently skip — it defers to
   moisture (wet soil already reads high). Rationale: DWD recent-rain is exactly the
   signal that *missed* the local storm (root cause c); current rain still skips (don't
   run valves in active rain). Revisit once the WH40H local gauge is online.
3. **Weather modifiers (± one step on the moisture base):** recent rain
   (`rain_24h > rain_light`) → down 1; hot (**forecast/current** high ≥ `temp_heavy`) →
   up to `heavy`; cool (**forecast/current** high < `temp_normal`) → down 1. The
   temperature signal is **de-lagged**: it uses `brightsky_forecast_temp_high` and/or
   the current high, **not** the trailing 3-day average (fixes root cause a).
4. **Forecast-rain downgrade (soft, capped)** — tuned for Jul–Aug localized storms at
   peak demand: triggers **only if** the **whole-day chance of rain > 80 %** **AND**
   the **forecast volume `≥ 5 mm`** (both), over **today until midnight** (operator
   choice, 2026-08-25). Both are aggregated from the **hourly** BrightSky forecast rows
   (same shared fetch) — POP = **max hourly `precipitation_probability`**, volume = **sum
   of hourly `precipitation`** — via a **dedicated** `forecast_pop_today` /
   `forecast_rain_today` pair, NOT the DWD `precipitation_probability_6h` (a fixed
   synoptic 00/06/12/18-UTC block, coarse and misaligned to the windows) and NOT the
   existing `brightsky_forecast_rain` card sensor (which uses an 04:00 rollover, a
   different window). Window boundary = **remainder of today (now → 24:00 local)** (operator-confirmed
   2026-08-25: "just until midnight," no roll into tomorrow). Note DWD POP is "chance of >0.1 mm," so the
   `≥ 5 mm` volume gate is what stops a high-POP/low-volume drizzle from downgrading.
   Bumps **down at most 2 steps**, floored so a hot/dry zone still waters:
   **heavy → light** (never `off`), **normal → off**, light → off. Never strands a
   `heavy` (hot, dry) zone on the *hope* of an evening shower localized convection may
   miss (fixes the "skip on forecast" over-suppression risk).
5. **Graceful degradation:** moisture unknown/unavailable (no sensor assigned to the
   zone, or all its sensors unavailable) → fall back to the **weather-only tree** (the
   current tree, but WITH the de-lag of (3) and the current-conditions skip of (2)).
   Fail-safe, never fail-`heavy`.
6. **Knife-edge robustness (root cause d):** the moisture ladder is inherently graded;
   add small **hysteresis** on the wet-skip / rain gates so a single sub-threshold
   reading cannot flip the decision. Band values provisional — tune against ground-truth.

**Sensor → zone mapping (new sub-system):**
- **4× wireless WH52** are moved between beds → each gets a runtime tag
  `input_select.moisture_wireless_N_zone` with **friendly options**
  {Raspberries (z1), Blueberries (z2), Vegetables (z3-pool), Unassigned}.
- **3× hard-wired SEN0600** are **fixed** to zones (config), addresses `0x05–0x10` on
  the pump RS-485 bus.
- `sensor.zone_N_soil_moisture` = average of all sensors tagged/fixed to zone N; no
  sensor → `unknown` → weather-only fallback (5).
- **Zones 3 & 4 share one veg bed** (3 = leafy, 4 = fruiting/root). Sensors in it are
  tagged **"Vegetables" (the zone-3 pool)**; **zone 4 reads the zone-3 pool** for its
  moisture but keeps its **own distinct thresholds**. One physical sensor set, two
  threshold sets.

**WH52 sensor capabilities (verified 2026-08-25):** the WH52 is a NEW **3-in-1** Ecowitt
soil sensor (Moisture / Temperature / EC), not the moisture-only WH51. Moisture is
**native 0–100 %** (1 % res, ±5 %) → drops straight into the `moisture_min` thresholds
with **no calibration map**. Reports every **70 s**, battery (always-on, no bus conflict →
ideal Phase A). Requires an **Ecowitt gateway** (GW1200/2000/3000/HP2xxx…; same gateway
the WH40H needs) and shares soil channels with the WH51. **Bonus channels** (out of the
§3.2 tree's core scope but captured as opportunities): soil **temperature** = real
root-zone temp per bed (could later feed/localize the temp signal), and **EC** (0–10000
µS/cm) = salt/fert monitoring — directly relevant to moorbeet (EC <1.0) and salt-sensitive
strawberries, and a natural fert-dose feedback input. **Verify at setup:** whether the
current HA Ecowitt integration exposes the EC channel (moisture + soil-temp are standard;
EC is newer).

**SEN0600 read strategy — PULSE-POLL (accepted):**
The SEN0600 share the dosing pumps' RS-485 bus, isolated behind **R10 (24 V cabinet
enable)** and energized only during dosing; moisture must be read at `window_check`
when the bus is down. Pulse-poll: at decision time (plus a **bounded** periodic cache
refresh) — (1) guard that no cycle/dosing is active + interlocks hold, (2) close R10,
(3) wait for the signal to stabilize (≥ the existing 500 ms bus-settle; sensor-specific
settle from the SEN0600 datasheet), (4) read holding registers (FC 0x03), (5) open R10,
(6) cache the value for the decision. `mode: restart`. Failure/timeout → last-known-good,
or weather-only if stale. Poll frequency **bounded** to spare R10 (roughly once per
`window_check` + a slow refresh, **not** continuous) and a poll must never coincide with
or trigger dosing. The moisture register + scaling come from the SEN0600 datasheet at
implementation (the RS-485 doc has addressing, not the register map, yet).

**Local rain priority (WH40H):** only *rain* is localized; temp/humidity/forecast stay
DWD (~5 km acceptable per operator). Abstract the rain source behind the `rain_now` /
`rain_24h` / `rain_72h` names so that when the WH40H is online it becomes the source for
current + accumulation with **zero tree rewrite** (config swap). Forecast POP/volume stay
DWD.

**Bundled cleanups (follow-up #4 (e) + the DB note):**
- Threshold helpers (`zone_N_{season}_*`, weather **and** moisture) → **RestoreEntity**
  (drop `initial:`) so operator tuning survives restart (ADR-017 pattern). **Resolved
  2026-08-25: pure RestoreEntity, no first-boot seed.**
- **Record the ACTUAL decision inputs** to the DB so the tree's effectiveness is evaluable
  against ground-truth — the tuning feedback loop this rework needs. **Handled by ADR-018,
  NOT a new table (reconciled 2026-08-25):** ADR-018 (Weather Observations DB +
  Decision-Criteria Recording, accepted 2026-08-18) already designs exactly this — a separate
  `watering_weather.db` with `weather_snapshots (1) → zone_decisions (N=4)` written by an
  **always-on** window-time automation (captures run/skip/parked days), plus
  `zone_runs.decision_criteria` (JSON) + `season` for real runs, all fed by **one shared,
  side-effect-free decision routine**. It satisfies every requirement here (dedicated
  `zone_decisions` table, adaptable JSON criteria, skip-days, cross-ref to `zone_runs`) and its
  always-on capture is stronger than a `window_check`-fired write. **ADR-021's contribution to
  ADR-018:** (i) the moisture-primary tree below IS the logic that shared routine computes;
  (ii) the `decision_criteria` / `zone_decisions` JSON gains the moisture-primary inputs
  (moisture % + contributing-sensor count, rain now/24/72, the de-lagged temp used, humidity,
  forecast POP/volume, thresholds live at the time, the branch/`skip_reason` fired) — ADR-018's
  JSON was explicitly designed to absorb these with no migration; (iii) ADR-018's two
  **deferred** items are now resolved by ADR-021 — the temperature metric (→ de-lagged
  forecast/current high) and the threshold-helper RestoreEntity question (→ yes, pure
  RestoreEntity). *No separate `decisions` table is introduced (the earlier ADR-021 draft's
  table is retired in favour of ADR-018).*

**Phasing (fits "hold for sensors"):**
- **Phase A (near-term):** wireless WH52 (always-on, no bus conflict) → moisture-primary
  live for tagged zones; weather-only fallback covers untagged zones.
- **Phase B:** SEN0600 hard-wired — gated on the fert-hardware buildout (RS-485 dosing
  still unwired) + the pulse-poll implementation.
- **Phase C:** WH40H local-rain swap.

**Alternatives considered:**
- *Weather-only rework (fix lag + add a current path, no moisture).* Rejected: cannot
  solve the localized-rain miss (root cause c) — the failure case is inherently a
  moisture question (operator success-criterion call).
- *Moisture as override, weather primary.* Rejected: operator chose moisture **strictly**
  primary; soil state is the physically correct "does it need water" signal.
- *Forecast rain as a hard skip.* Rejected: localized Jul–Aug convection over a 5 km-distant
  DWD makes a forecast-driven full skip risky at peak demand — hence the capped 2-step,
  `POP>80 % ∧ ≥5 mm`, heavy-floored-at-light rule.
- *SEN0600 on an always-on segment / defer entirely.* Not chosen — operator accepts the
  pulse-poll's R10 actuation + stabilization cost to reuse existing wiring.

**Consequences:**
- Watering tracks real soil state → the all-`heavy`-on-wet failure is stopped **by
  construction** (wet soil reads high → `off`).
- New dependency on sensor health: mapping/averaging must fail safe (untagged/unavailable
  → weather-only, never `heavy`).
- R10 actuation frequency rises (pulse-poll) — bounded; note relay wear and the
  never-trigger-dosing guard.
- New helpers (4 wireless-tag selects; per-zone aggregate-moisture templates; a rain-source
  abstraction). Threshold helpers change persistence to RestoreEntity.
- **Reshapes** the deferred preview (ui_design §7 #1): a true "next program" forecast would
  require predicting *future soil moisture* (a soil-water-balance/ET model, uncalibratable
  pre-season), so it is rescoped to a per-zone **"Current Status"** tile — the live tree
  evaluated on *current* inputs, framed as status not prediction (operator, 2026-08-25).
  Forward-modelling revisited only after a season of ground-truth.
- Docs cascaded **on acceptance** (2026-08-25): architecture.md §3.1–§3.2 (tree rewrite) + §4.2
  (mapping helpers) + v1.9.0; entity_reference (new sensors/helpers + PLANNED block); START_HERE
  follow-up #4 (rescope) + §1; ui_design §7 #1; test_scenarios Test 4.24. Decision recording
  reconciled into ADR-018 (see Decision above); ADR-018 amended accordingly.

**Open items for operator review:**
- Hysteresis band sizes (tune against ground-truth).

**Deferred (operator, 2026-08-25):**
- **Wireless WH52 → zone tag mechanism** (HA `input_select` per unit vs. reading the
  Ecowitt gateway channel→name). Revisit once the sensors are physically set up and their
  HA entities are visible.

**Resolved (2026-08-25):**
- Threshold helpers → pure RestoreEntity (no first-boot seed).
- Forecast-rain window → evaluation time → midnight tonight (no roll into tomorrow).
- DB decision recording → **handled by ADR-018** (its `zone_decisions` / `decision_criteria` JSON
  extended with the moisture-primary inputs); no separate `decisions` table. ADR-018's two
  deferred items (temp metric, threshold RestoreEntity) resolved by ADR-021.
- Wireless model → Ecowitt **WH52** confirmed (3-in-1 M/T/EC; moisture native 0–100 %); see
  the WH52-capabilities note above.

**Revisable:** all thresholds, hysteresis bands, the POP aggregation window, and the
moisture-averaging/mapping details are provisional — tune against the first live season and
the incoming ground-truth sensors.

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
- Programs selected per-zone: off/light/normal/heavy (+ system-set `booster`, the
  heavy mid-interval 0.5× top-up — ADR-020)

### Scheduling

**Time-Based with Condition Evaluation:**
- Per-zone cadence: each zone waters every N days (`zone_N_watering_interval_days`,
  Phase 7; replaces the retired system-wide `watering_cycle_days`)
- Morning and/or evening check windows
- Within windows: system evaluates weather (intensity) then applies the per-zone
  enable + interval + heavy-booster gates (ADR-020) to select per-zone programs
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
| ESP32-DEVKITC-32UE | ESP32-WROOM-32UE | 2026-08-18 | Espressif devkit, u.FL external-antenna variant (swapped from DEVKITC-VE 2026-08-18) |
| Linx ANT-W63WS3-SMA | WiFi 4/5/6/6E | 2026-08-18 | External blade WiFi antenna; Mueller BU-4150031MM500 SMA bulkhead lead, 6.5 mm cabinet-wall hole |
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
- **AppDaemon event-triggered subprocess (adopted 2026-07-01, see ADR-012):** an
  AppDaemon app runs `pull_public_repo.sh` via `subprocess` on a bus-event
  trigger. This is NOT the `shell_command` integration, so it does not hit the
  failure modes above. Now the primary repo-pull path (button in the HA UI).
  Verified live on Core 2025.9.4.
- Manual execution via SSH (retained as fallback)
- Node-RED add-on (~45 min setup)
- Custom integration (~10+ hours development)

**Recommendation:**
Still do not use the `shell_command` integration in HAOS for automations. For work
that must run a shell script from an automation context, trigger an AppDaemon app
(bus event) that runs the script via `subprocess` — see ADR-012 and
`home-assistant/appdaemon/repo_pull/`. Manual SSH remains the fallback.

**Full incident report:**
https://github.com/robertmacbridehart-coder/watering-system-private/blob/main/docs/repo_pull_incident_report.md

---

## Change Log

* **2026-08-23**: **ADR-020 cadence-rework code-review fixes (6 findings on downstream
  consumers; core state machine confirmed correct).** All applied to local `main`
  (code-only, not yet deployed). **#1** aligned the 12 `fert_helpers.yaml` flow-rate
  multiplier maps to the authoritative values (`heavy` 1.5→1.0, added `booster` 0.5) with a
  KEEP-IN-SYNC comment + a fert-phase TODO. **#2** added `booster` (labeled "booster (0.5×)")
  to the end-of-cycle watering summary (`notification/scripts.yaml`). **#3/#5** made
  `calculate_zone_runtime` the single source of the program→multiplier: it now returns
  `multiplier`, threaded through `run_zone_sequence` → `water_one_zone` →
  `fire_zone_run_complete` (static map deleted), so the recorded `program_multiplier` matches
  the actual runtime — including the N==1 single-window heavy = 1.5× edge. **#4b** (operator
  chose retry): the heavy booster now retries on each target/evening window while
  `mid <= days_since < N` and pending, tracked by new SQL sensors
  `sensor.zone_{1-4}_last_booster` (`derived_sensors.yaml`), replacing the single-shot
  `[mid, mid+1)` band. **#6** corrected the `state_window_check` booster comment. Logic
  re-verified by offline Jinja simulation (9 multiplier + 8 gate cases, all pass). Docs:
  architecture.md v1.8.1 (§3.2, §13.3.1, change log), ADR-020 addendum, entity_reference,
  test_scenarios Test 4.22. **Follow-up:** extract a shared Jinja macro to de-duplicate the
  fert-map copy (deferred; fert path hardware-blocked). Dev-Tools Test 4.22 + push pending
  operator approval.
  **Second review pass (same day):** caught that the sequential-mode **zone-4** `water_one_zone`
  call (unconditional, top-level in the sequence → different indentation) was missed by the
  per-zone `replace_all`, so it still lacked `program_multiplier` — a real correctness bug (a
  sequential zone-4 booster would record NULL → read as a main dose). Fixed (all 8 call sites now
  pass it). Also added a single authoritative `| float(1.0)` guard on the Event-3
  `program_multiplier` emit (write boundary; HA `required:` is advisory and the emit is
  `continue_on_error`, so a missing value must not write NULL nor error the row out), and
  documented the N==1 heavy=1.5× cross-script coupling (state_window_check vs calculate_zone_runtime
  read the same window/interval helpers independently — latent, refactor deferred). Fert-map
  duplication (#4) and the vestigial `window` param (#5) left as-is (already commented / deferred).

* **2026-08-22**: **Agent input-fidelity guardrail added.** Updated `AGENTS.md` to require
  stopping for focused clarification whenever supplied material is unreadable or incomplete,
  rather than inferring labels, mappings, geometry, or requirements. Per user instruction,
  `CLAUDE.md` was not modified.

* **2026-08-22**: **Per-zone watering cadence + master enable; heavy split → mid-interval booster
  (ADR-020).** New helpers `input_number.zone_N_watering_interval_days` +
  `input_boolean.zone_N_enabled` (both RestoreEntity, `zone_helpers.yaml`); retired the unused
  system-wide `input_number.watering_cycle_days`. `state_window_check` now wraps the §6.2 weather
  tree with an enable gate, a per-zone interval gate (anchored on `sensor.zone_N_watering` = last
  MAIN dose), and a heavy mid-interval `booster` (0.5×, re-evaluated at the midpoint window).
  `calculate_zone_runtime` retired the same-day heavy split (heavy→1.0×, booster→0.5×, N==1
  single-window→1.5×). Booster recorded at the DB boundary as `weather_program='heavy'` +
  `program_multiplier=0.5` (`fire_zone_run_complete`) — no schema or AppDaemon change; the anchor
  sensor excludes `(heavy, 0.5)`. Closes ADR-015 D-C; supersedes ADR-007/009. Docs: architecture.md
  v1.8.0, entity_reference, ui_design §7, START_HERE §1. **Code-only, NOT yet deployed on the Green**
  (awaiting operator code review + Dev-Tools test pass). Logic verified by offline simulation (16
  scenarios). Test-scenarios update pending.

* **2026-08-22**: **Gate 7.2 derived dashboard sensors — first tranche deployed & verified live.**
  Added `packages/watering_ui/derived_sensors.yaml`: `sensor.zone_{1-4}_watering` (HA `sql:` on the
  secondary `watering_ops.db` — last / last-4 waterings via `json_group_array`) and
  `sensor.zone_{1-4}_fert_next_due` (template). Added the BrightSky forecast inputs
  `sensor.brightsky_forecast_rain` / `brightsky_forecast_temp_high` (one shared `rest:` resource) to
  `weather/dwd_brightsky.yaml`. All ten verified live on the Green. Two silent-failure gotchas found
  & fixed (new Known-Gotchas subsection "Dashboard-Derived Sensors (Gate 7.2)"): the SQL `db_url`
  must use HA Core's `/config` path, not AppDaemon's `/homeassistant`; and two identical-URL
  `- platform: rest` sensors race at startup — collapse them into one `rest:` resource. The per-zone
  "Next Program" forecast decision templates remain deferred (they will differ from the live tree;
  wait for the zone-interval helper / §6.2 rework).

* **2026-08-18**: **Phase 7 front-end (Dashboard UI) design process + tooling defined (ADR-019).**
  Established the seven-gate implementation path (impl_roadmap §7.0–7.6) with per-gate exit
  checklists; kept the original placeholder cards as §7.7. Key decisions: repo YAML-mode
  dashboards (provisional), Lovelace + curated HACS cards (card-mod glassmorphism), and an
  HTML-Artifact-mockup feedback loop. Installed `frontend-design` + `ha-dashboard-design` skills
  (`~/.claude/skills`) and wired `hass-mcp` (voska v0.6.0 via `uvx`, user scope) for live HA
  inspection — established **READ-ONLY**: no state/service/helper/config/code change without
  express per-action consent, destructive steps independently verified, always recoverable,
  "Before You Code" applies. Windows setup gotchas: MCP `command` needs the full `uvx.exe` path
  (the app's spawn PATH lacks `~/.local/bin`); the `claude` CLI is invoked via the VS Code
  extension binary; `-e KEY=value` env args must be quoted as one string.

* **2026-08-18**: **`zone_N_season` selectors made RestoreEntity (fixed a silent reset-to-spring
  bug).** Found during the Phase 9.10 test cycle: `state_window_check` set all zones to `heavy` on
  a cool, post-rain day. One contributing cause — every `input_select.zone_N_season` was defined
  with `initial: spring`, and *nothing in the codebase ever sets season* (it's read-only, consumed
  by `state_window_check`). Per the documented `initial:` gotcha (an `input_*` with `initial:`
  returns early in `async_added_to_hass` and never restores), season therefore reverted to `spring`
  on **every** HA restart — so the operator's summer/fall selection was silently lost (e.g. the
  Core/HAOS upgrade + repo pulls earlier the same day reset it, leaving spring thresholds applied in
  mid-August). **Fix:** removed `initial:` from all four `zone_N_season` helpers
  (`watering_helpers/zone_helpers.yaml`) → RestoreEntity, mirroring `zone_sequencing_mode` (ADR-017).
  First boot with no stored state falls back to `options[0]` = `spring` (unchanged first-boot
  behavior). **Deploy order matters:** pull + restart to load the fix FIRST, then set the season, so
  the chosen value is stored under the new RestoreEntity behavior and persists. Note the deeper §6.2
  decision-tree issues this cycle exposed (lagging `temp_avg_high_3day`, no current-conditions path,
  knife-edge thresholds, and the `zone_N_{season}_*` threshold helpers sharing the same
  reset-on-restart `initial:` property) are logged as a START_HERE follow-up, NOT fixed here.
* **2026-08-18**: **Version display now mirrors the PRIVATE repo (`git describe`), end to end.**
  Problem: `sensor.repo_pull`'s "current tag" read the public repo's `releases/latest`, stuck at
  `v.0.1.1` (2025-09-26, the only Release); and the public mirror is a `git init` + force-push squash
  (publish.yml), so its commit SHAs are random and share no history with the private repo — the
  public SHA can never equal the private one. Fix carries the private version *through* the pipeline:
  - **publish.yml** — new "Stamp private version" step writes `_publish/version_source.json`
    (`{"version": git describe --tags --always, "sha": <private HEAD>, "built_at": …}`) into the
    published tree; `fetch-tags: true` added to the checkout so `git describe` sees tags. The private
    repo is semver-tagged (`v0.1.0`…`v0.2.1`), so describe yields e.g. `v0.2.1-10-ge10fc6e`.
  - **pull_public_repo.sh** — `fetch_version_info` now prefers `$SRCDIR/version_source.json` (private
    version + SHA) and only falls back to the old GitHub-API method (public branch SHA + Release tag)
    when the stamp is absent. Bonus: drops the API round trip / rate-limit dependency for versioning.
  - **repo_pull.yaml** — `sensor.repo_pull` displays `value_json.tag` directly (now the describe
    string), short-SHA fallback, then `unknown`. (Supersedes the interim `tag+shortsha` composite —
    describe already ends in `-g<sha>`.)
  Net: the dashboard shows `v0.2.1-10-ge10fc6e`, advancing every pull, mirroring the private repo.
  NOTE: `publish.yml` triggers on push-to-main, not tag pushes, so bump/propagate a version by
  pushing a commit (tag a commit you then push). Also: the SHA/Time sensors had *separately* been
  frozen only because no pull completed (manual_override interlock, fixed same day, below).
* **2026-08-18**: **ESP32 board swapped to ESP32-DEVKITC-32UE + external WiFi antenna installed.**
  Replaced the DEVKITC-VE (PCB-antenna) devkit with an ESP32-DEVKITC-32UE (ESP32-WROOM-32UE, u.FL
  external-antenna connector) and routed an external Linx ANT-W63WS3-SMA blade antenna (WiFi 4/5/6/6E)
  through the cabinet wall on a Mueller Electric BU-4150031MM500 SMA-female bulkhead lead (6.5 mm hole).
  RSSI improved ~-63 → ~-53 dBm (~10 dB / ~10× power). First flash was over serial (new board, no OTA
  yet) via web.esphome.io; the ESPHome `board: esp32dev` target is UNCHANGED (generic, correct for all
  DevKitC variants). New board = new MAC, so HA re-registered the device — the new entities came up
  **CANONICAL** (`switch.watering_system_*`, no `back_garden_` area prefix), confirming the
  freshly-compiled firmware advertises no `suggested_area`; this resolves the former follow-up #3
  (stale-area flush). Old device deleted to free the canonical IDs; relay control physically
  re-verified; system re-parked in `manual_override`. Docs only, no runtime YAML changed.
* **2026-08-18**: **repo_pull interlock — parked control states no longer block a pull (ADR-012
  addendum).** The preflight interlock blocked on `manual_override` two ways (its `active_states`
  membership + the `manual_override_entity` boolean check), which collided with the end-of-testing
  park SOP: every pull required un-parking to `idle` first. Removed both `manual_override` blockers
  (`apps.yaml` `active_states` no longer lists it; the `manual_override_entity` config + check
  deleted from `repo_pull.py`). `winterized` was already non-blocking, so both parked control states
  are now on par with the error-idle carve-out. The relay-ON check stays the load-bearing guard
  (a manually-energized relay still blocks), and both park entities are RestoreEntity (ADR-017), so
  the park survives the pull's auto-restart. See the ADR-012 addendum + START_HERE repo_pull gotcha.
* **2026-08-18**: **Phase 9.10 — end-of-cycle Watering Summary BUILT + WhatsApp path diagnostic
  added.** `script.send_watering_summary` (which had never actually been created despite the §9.4
  tick) compiles a compact one-liner from HA state and routes through the STANDARD tier; wired into
  `state_post_cycle_relief` after `finalize_cycle_record` with runtime captured before Event 4 flips
  `binary_sensor.watering_cycle_active` OFF. Also added `script.diagnose_whatsapp_path` (manual
  Dev-Tools diagnostic that surfaces the CallMeBot HTTP status the tier scripts swallow). See
  impl_roadmap.md §9.10.
* **2026-08-18**: **HA Core 2025.9.4 → 2026.8.2 + HAOS 16.2 → 18.2 upgrade COMPLETE — ESP32 entity
  collision RESOLVED.** The stale Core was confirmed as the cause: after the upgrade all 16 relays,
  both tank-float binary_sensors, and the MPPT/WiFi sensors register individually again (the
  "Platform esphome does not generate unique IDs" collision is gone). This unblocks Phase 5.1
  safety-monitor Dev-Tools testing (was gated on the missing relay/sensor entities).
  **Side effect handled same day — area-prefixed entity_ids.** HA 2026.06+ (core#170560) prepends
  the device's Area to *newly-created* entity_ids, so the re-registered entities came up as
  `switch.back_garden_watering_system_*` (the ESP32 is in Area "Back Garden") instead of the
  canonical `switch.watering_system_*` — which silently breaks every script/automation, since they
  reference the canonical IDs. Deleting the area + device + restarting did NOT clear it (the prefix
  is applied at entity *creation* and something kept re-asserting the area on re-discovery — most
  likely a firmware `suggested_area`, the deprecated path core#149970; note the tracked
  `esphome/watering-system.yaml` has never had an `area:` key, per `git log -S area`). Fixed
  deterministically by **manually renaming each entity_id in the UI back to canonical** (strip the
  `back_garden_` segment) — stable through reconnects. Root-cause flush is a new low-urgency
  follow-up (#4). Added a §3 gotcha documenting the area-prefix trap. System re-parked in
  `manual_override` after the work. Docs only this entry (START_HERE §1–3 + follow-ups, this
  change-log); no runtime YAML changed by the rename (it's live-registry state).

* **2026-08-17**: **Core upgraded to 2026.8.2 (follow-up #2 step c) — 2 new deprecation follow-ups
  spun out.** Upgrade itself succeeded; two HA Repair notices surfaced afterward, both
  non-blocking ("stops working in 2027.1.0/2027.2.0"): legacy `notify: platform: smtp` YAML
  (auto-imported to a UI config entry, but `notify.gmail_smtp` is called from production code —
  `notification/scripts.yaml:60,113` + 3 sites in `tests.yaml` — so this needs the entity_id
  confirmed live + call sites updated before the YAML can be removed, not a quick delete) and the
  `http:` block (`use_x_forwarded_for`/`trusted_proxies` for the Funnel proxy setup — a live
  upstream issue, home-assistant/core#178330, confirms Settings → System → Network has no UI field
  for those yet, so removing the YAML now would break proxy access; holding until the UI catches
  up). Tracked as START_HERE follow-ups #4 (SMTP) and #5 (http:); docs only, no runtime YAML
  changed this entry. HAOS upgrade (step d) still pending.

* **2026-08-17**: **`fert_helpers.yaml` migrated to modern `template:` sensor syntax**
  (follow-up #2 step b, pre-Core-upgrade prep). HA 2026.6 removed the legacy
  `sensor: - platform: template` / `sensors:` form outright, so this had to land before
  the Core bump to 2026.8.2 or config validation fails. All 27 template sensors
  (12 zone/pump flow-rate + 12 zone/pump command + 3 calibration-status) converted:
  `friendly_name` → `name`, `icon_template` → `icon`, `value_template` → `state`,
  `attribute_templates` → `attributes`. Each sensor also gained `default_entity_id:`
  pinning its exact `sensor.fert_*` ID — the modern format otherwise seeds entity_id
  from the (dynamic, Jinja) `name:` at first setup, which would silently produce a
  different ID than the legacy YAML-key-derived one. Verified locally: `yaml.safe_load`
  parses clean, and the 27 `default_entity_id`s match the 27 legacy keys exactly (no
  drift, no dupes) — the same IDs already referenced in architecture.md,
  entity_reference.md, and fert_prog_design.md. No functional/behavioral change; fert
  hardware still unwired so nothing live consumes these entities yet. Not yet deployed
  to the Green (this package only matters once the Core upgrade runs; deploying earlier
  is harmless but not required).

* **2026-08-16**: **Brightsky startup-warm automation** (closes the follow-up added earlier today).
  New `brightsky_warm_slow_sensors_on_start` (weather/dwd_brightsky.yaml): on `homeassistant.start`,
  after a 30 s settle delay, calls `homeassistant.update_entity` for the four decision-relevant
  Brightsky REST sensors (`brightsky_temp_avg_high_3day` + `temp_high_yesterday`, both 1800 s;
  `rain_72h` 900 s; `rain_24h` 600 s) so they populate promptly instead of coming up
  `unavailable`/`unknown` until their first scheduled poll. Prevents a restart shortly before a
  window from sending `state_window_check` down the D-A fail-safe fallback (all zones `normal`, temp
  tree skipped). Placed in the weather package (co-located with the sensor defs) rather than folded
  into `watering_state_restart_recovery` — keeps weather-warming out of the safety-critical restart
  path. `continue_on_error: true` so one failing fetch can't block the others; read-only, touches no
  relays/state. BUILT; **light-verified PASS on the Green 2026-08-16** — after a restart, all four
  sensors populated within the 30 s delay window (not `unavailable`/`unknown`) and the automation
  trace fired clean. Follow-up closed.

* **2026-08-16**: **Phase 4 Test 3.6 COMPLETE (a–l all PASS) + end-of-testing park SOP.**
  Closed the last Test 3.6 sub-tests on the Green (build `13fa378`): c (weather-program tree +
  all-off→idle), d (comms gate — validated by a **physical control-cabinet power-cycle**:
  cabinet OFF → R1 + Low-Low `unavailable` → preflight Check 1 D-G → `error_comms_lost` + HIGH
  notify; cabinet ON → `watering_safety_r1_comms_recovery` auto-cleared to idle), j Part 3
  (`0c085c5` engage-from-error re-verify), k (idle→no-op restart), l (sequential). The plain-watering
  state machine is validated at the relay/logic level. **CLAUDE.md adaptation:** added an END OF
  SESSION SOP — park the system in `manual_override` (RestoreEntity, persists across restarts) after
  testing, so no scheduled/manual cycle can fire while valves/pump are unwired; hold until go-live.
  Also: cleaned up START_HERE follow-up #1 to show only live/due work (long-term blocked items —
  fert states, wired-hardware delivery, Phase 3.5 write-listeners — now tracked in test_scenarios.md
  / impl_roadmap.md, not the fast-follow list); added follow-up #6 (warm the slow Brightsky REST
  sensors on `homeassistant.start` — they come up `unavailable` after a restart until their first
  scheduled poll, sending `window_check` down the D-A fallback). Docs only (test_scenarios.md,
  START_HERE.md, CLAUDE.md); no runtime YAML changed.

* **2026-08-15**: **ADR-017 follow-on — restart-persistence VERIFIED + same-class cleanup.**
  Mirror test passed on the HA Green after deploy: `error_e_stop` → wait → restart → came up
  `error_e_stop` (latch survived); `manual_override` and `winterized` likewise restored their
  state + boolean across a restart. Fix confirmed on all three latch entities. Same session,
  extended the same fix to two operator-preference helpers that also reset on restart:
  removed `initial:` from `enable_morning_window` / `enable_evening_window` (was silently
  re-enabling a seasonally-disabled window) and `zone_sequencing_mode` (was snapping back to
  `parallel`), both in config_helpers.yaml. First-boot fallbacks are fail-safe (windows →
  `off`/disabled; sequencing → `parallel`, unchanged). The three `input_number` config values
  were LEFT with `initial:` on purpose (follow-up #1 test flow relies on their reset). See
  ADR-017.

* **2026-08-15**: **ADR-017 — state/latch helpers made RestoreEntity (removed `initial:`).**
  Removed `initial:` from `input_select.watering_system_state`,
  `input_boolean.manual_override_active` (config_helpers.yaml), and
  `input_boolean.system_winterized` (notification/helpers.yaml) so they restore across an HA
  restart instead of resetting. As configured they reset (an `input_*` helper with `initial:`
  set never calls `async_get_last_state()`), which defeated restart-recovery branch (a): a
  mid-cycle restart came up `idle` → hardware never safed, error latches lost, winterization
  silently cleared. The recovery + `safe_shutdown` code already ASSUMED RestoreEntity. First
  boot is safe with no code change (`input_select` → `options[0]` = idle; `input_boolean` →
  off). Confirmed empirically before the fix (`error_e_stop` → restart → came up `idle`); the
  mirror test (restart preserves `error_e_stop`) is owed at deploy. Each entity now carries a
  comment forbidding re-adding `initial:`. See ADR-017.

* **2026-08-15**: **Control guard — audit trail + honest messaging on engage-from-error.**
  When a control state (`manual_override` / `winterized`) is engaged from an `error_*` state,
  `watering_state_control_guard` now captures the prior error BEFORE overwriting the state,
  logs a `control_engage_from_error` system_event (`value_before` = the error), and names the
  error in the HIGH notification. Reworded the message to stop conflating the cleared
  error-state **latch** with the un-fixed **hardware fault**: it now says the latch is cleared
  (returns to idle on release) but the underlying fault is NOT auto-resolved — verify hardware.
  Found during Phase 4 Test 3.6.j: `error_e_stop → manual_override → idle` silently cleared the
  latch with no record of which error, while the old message claimed "NOT auto-cleared." The
  `exit → idle` behavior is unchanged (audit + wording only — Option C); Option B (return to the
  prior error on release) stays deferred with the recovery UX.

* **2026-08-14**: **ADR-016 — fert-manifold valves closed at rest (valve discipline).**
  Reversed the "R6 open at rest" resting state: R6 (bypass) + R7 (fert line) now rest
  CLOSED; the R6-XOR-R7 rule is re-scoped as a pump-start precondition (checked in
  `start_main_pump` after `state_watering_plain` opens R6). `state_post_cycle_relief`
  and `safe_shutdown` now close both valves as cleanup (after the relief bleed, before
  R10 power-down). Fixes the silent `repo_pull` abort — its "all relays off" guard could
  never pass while R6 was pinned on — without touching the repo_pull relay list.
  Clarified architecture.md §5 (both-OFF is the valid resting state; the XOR error is
  pump-start only). Drove code changes in state_scripts.yaml + watering_safety_scripts.yaml.
  (Same session also fixed the preflight error-branch log race, commit fc06fc9 — code
  fix, recorded as a gotcha in START_HERE §3, not logged separately here.)

* **2026-08-13**: **Added "State-Machine & Automation Patterns" to Coding & YAML Standards.**
  Distilled the reusable, project-agnostic lessons from the Phase 4 state-machine build and its
  four code-review passes into a standing guidance subsection: derive state-set membership
  instead of maintaining parallel literal lists; wrap reporting-only subscript calls in
  `continue_on_error`; add any delay-bearing subscript to `abort_cycle_scripts`' turn_off set;
  trigger consumer automations off the `input_select` state (not the raw control boolean);
  re-read live state before each error-set; preserve control states across safing/e-stop; prefer
  a documented id-format check over a sentinel list. (The code-review *fixes* themselves are not
  logged here — they live in the git history + docs/phase_4_review_1.md / _2.md; this entry
  records the guidance addition, which is an actual programming-notes content change.)

* **2026-08-05**: **ADR-015 — Phase 4 state-machine control structure decided (D1–D4).**
  Settled the four control-structure questions before writing Phase 4 YAML:
  **D4** dispatcher automation (state change → call `state_x`, `mode: queued`) with
  scripts self-advancing + a separate scheduler; **D2** context via new
  `input_select.active_watering_window` / `active_trigger_type` helpers; **D1** Event 3
  fired inside `run_zone_sequence` with parallel-safe local per-zone `zrun_uuid`
  (`z-<ts>-<zone_id>`) — resolving the ADR-014 "parallel runs" caveat (shared helper
  reserved for the sequential fert path); **D3** a reporting-only `script.finalize_cycle_record`
  that fires Event 4 + clears `cycle_uuid` and **never** touches hardware/relief/state
  (error scripts keep sole teardown ownership and just call it to tidy the DB/sensor).
  Amended ADR-014, clarified architecture.md §13.3.1, and rewrote impl_roadmap.md
  §4.1/§4.2 to the decided shape. No code yet (design only). **Later same day:** added
  the ADR-015 **D-A…D-H addendum** from a full state-walkthrough — weather-unavailable
  fallback (D-A), fert-due→plain + fert-target=0 default (D-B), no cadence gate (D-C),
  five per-error entry automations calling `finalize_cycle_record`/`safe_shutdown`
  (D-D, uniform), thorough HA-restart recovery (D-E), safe-first override/winterize
  (D-F), tank-`unavailable`→`error_comms_lost` (D-G), manual reset model (D-H); plus
  the "cycle row always closes" invariant and the no-`continue_on_error`-around-
  safety-subscripts principle. **Final capture pass same day:** added **A1** (state
  scripts guard their advance — mandatory correctness against a parallel safety event
  overwriting a latched error) + **A2** (`abort_cycle_scripts` cancels in-flight
  progression scripts, best-effort since A1 owns correctness); **revised D-F** to a
  **guard** model (reject engage mid-cycle / ack-from-error / engage-from-idle; no
  auto-abort — moves the `'aborted'` producer to a future safe-stop UX; fert flush
  branch deferred); resolved the minor build-details (manual trigger =
  `input_button.start_watering_cycle_now`, no `override` trigger_type; Event 1
  `temp_high_c` = `brightsky_temp_high_yesterday`; error notifications wired now via
  the per-error automations). architecture.md §5.3 stale snippets superseded (v1.5.6).
* **2026-08-05**: **State machine reconciled to 15 states + ADR-002 addendum (Phase 4 prep).**
  Cross-checked every doc's state-machine definition against the runtime entity
  `input_select.watering_system_state` (config_helpers.yaml, canonical = 15 states)
  and found the design docs had lagged at 11/12. Added an **ADR-002 addendum**
  recording the 11 → 15 growth during Phase 3 (`winterized`, `error_e_stop`,
  `error_valve_interlock`, `error_relay_state` added by the concrete scripts).
  Fixed architecture.md §2.1 (de-duped `error_tank_low`, added the two missing
  states) and §2.2 (added the missing error/`winterized` transitions; two-tier
  preflight tank gate — plain=Low-Low/GPIO32, fert=Low/GPIO33; entity name
  `winterization_mode` → `system_winterized`), the same fix in fert_prog_design.md,
  and impl_roadmap.md (state count; GPIO35 typo → the two-tier gate). architecture.md
  bumped v1.5.2 → v1.5.5. No code changes — the runtime was already correct.
* **2026-08-03**: **Phase 3.4 comms-lost handling + `continue_on_error` gotcha.** Added a
  Known Gotcha documenting the verified scope of `continue_on_error` (catches a called
  script's `stop: error:true`; does NOT catch a `ServiceNotFound` from a missing service) —
  the actual root cause of the `safe_shutdown` early-halt, fixed
  with an existence guard on `stop_dosing_pumps`. Comms-lost fail-fast (Part A) added to
  `stop_main_pump`; reactive-recovery automation (Part B) added as
  `packages/watering_safety/safety_automations.yaml` (R1-back-on → `emergency_stop`,
  R1-back-off → clear to `idle`). Generalize pass: `open_pressure_relief`'s `stop_main_pump`
  call given `continue_on_error`; `safe_shutdown` no longer forces `idle` when it ends in an
  `error_` state; Part B OFF-branch closes zones before clearing to `idle`. Design detail
  and status in impl_roadmap.md §3.4.
* **2026-07-01** (later same day): Hardened the repo-pull package + pull script after
  live deployment. Consolidated all repo-pull HA config into the flat
  `packages/repo_pull.yaml` (a `packages/repo_pull/` subdir collided on the
  `!include_dir_named` basename key and dropped the package -- button + sensors).
  Made "Repo Pull Time" a plain (non-trigger) template sensor so it survives the
  per-pull HA restart. Added `PULL_DRY_RUN=1` preview mode to `pull_public_repo.sh`
  and documented that pruning needs rsync installed in the AppDaemon/SSH add-on
  containers (`system_packages` / `packages`); see the ADR-012 addendum. All
  verified live on Core 2025.9.4 (dry-run + prune-test).
* **2026-07-01**: **Repo pull automation resolved via AppDaemon (ADR-012).** New app
  `home-assistant/appdaemon/repo_pull/` (repo_pull.py + apps.yaml) runs a guarded
  pipeline (interlock → partial backup → `pull_public_repo.sh` subprocess → HA-core
  `check_config` → restart) on the `watering_repo_pull` event from
  `input_button.repo_pull` (`home-assistant/packages/repo_pull.yaml`).
  Generalized `pull_public_repo.sh` to deploy every `appdaemon/<app>/` folder and
  added a `PULL_SKIP_VALIDATE` gate. Updated the "Shell Commands (Non-Functional in
  HAOS)" limitation to point at the AppDaemon-subprocess pattern. Verified live on
  Core 2025.9.4.
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
* **2025-10-22**:
  - **Phase 3.1 Complete:** Zone Control Scripts (31/31 tests passed)
    - `script.open_zone` - Opens zone with pump and valve safety checks
    - `script.close_zone` - Closes single zone valve
    - `script.close_all_zones` - Parallel close of all zones
    - `script.calculate_zone_runtime` - Returns runtime based on program/window (uses response_variable)
    - `script.run_zone_sequence` - Executes watering in parallel or sequential mode
  - **New Helper:** `input_text.cycle_event_log` (max: 255 chars) for non-critical event tracking
  - **New Error States:** `error_relay_state`, `error_valve_interlock` added to state machine
  - **Heavy Program Logic Validated:**
    - Dual-window mode: morning=1.0x, evening=0.5x (splits 1.5x total)
    - Single-window mode: enabled=1.5x, disabled=0.0x
    - Evening independence: adapts to mid-day program changes (Test 7.3 confirmed)
  - **ADR-007:** Heavy Program Single-Window Mode Behavior (defensive window checking)
  - **ADR-008:** Valve Interlock Check Design (R6 XOR R7 defense-in-depth)
  - **ADR-009:** Evening Independence for Heavy Programs (adapts to conditions)
  - **Known Issues Identified:**
    - Cycle event log 255-char limit blocks Phase 9 (redesign required)
  - **Design Decisions:**
    - UI helper locking will prevent runtime changes during execution
    - Invalid zone_id fails silently by design (safe behavior)
    - Script abort procedure documented for testing
  - **Implementation Deviations:**
    - `input_text.cycle_event_log` max: 255 (not 1000) - HA hard limit
    - Heavy program logic clarified with defensive window checks
    - Pump errors use `error_relay_state` (distinct from valve errors)
  - **Files Created:**
    - `home-assistant/packages/watering_scripts/zone_scripts.yaml` (5 scripts, 450+ lines)
    - Updated: `home-assistant/packages/watering_helpers/config_helpers.yaml` (added cycle_event_log)
* **2025-11-07:**
  - **Phase 3.2 Complete:** Pump Control Scripts - Full development cycle (design → implementation → review → testing)
  - **ADR-010 Added:** Self-Healing Logic Patterns
    - Single-attempt pattern (pressure relief valve)
    - Aggressive retry pattern (pump stop with 120-minute loop)
    - Script mode considerations (restart vs. single)
  - **Critical Gotchas Added:** 5 new patterns documented
    1. Pressure relief duration validation (Issue #8 - defense-in-depth for safety parameters)
    2. Script mode for safety-critical operations (Issue #9 - use `mode: restart` to prevent blocking)
    3. State verification pattern (Issues #15-17 - use `not is_state()` for failure detection)
    4. YAML syntax: Empty `then:` blocks cause silent failures
    5. Relay state verification race condition (500ms delay after subscript calls)
  - **Testing Results:** 13/19 tests passed (68%), all critical safety paths validated
  - **Code Quality:** 6 issues identified and fixed through adversarial review process
  - **Test Infrastructure:** Tank sensors (low/low-low) now controllable via R15/R16 for testing
* **2026-04-08:**
  - **ADR-011: Operational Database Architecture** — Created and accepted
    - Decision: Two-layer architecture — MariaDB add-on (dedicated `watering_ops`
      database, separate from HA recorder) + AppDaemon add-on as Python bridge
    - Schema: Four tables — `watering_cycles`, `zone_runs`, `fertigation_doses`,
      `system_events`
    - Key design decisions:
      - `weather_program` at zone_runs level (per-zone evaluation)
      - `watering_cycles` written in two phases: INSERT at preflight, UPDATE on completion
      - `zone_id` denormalized into `fertigation_doses` for query convenience
      - `fertigated` boolean in `zone_runs` (no circular FK to fertigation_doses)
      - `system_events` has no FK to watering_cycles — correlated by timestamp at query time
      - Outcome vocabulary: `completed` / `aborted` / `error`
    - Archive strategy: Ongoing HA backup + seasonal CSV export via AppDaemon,
      triggered alongside winterization workflow
    - Foundational for: Phase 3.3 fertigation decisions, Phase 4 state machine
      decision queries, daily reports, future LLM advisory features
* **2026-06-28:**
  - **Gmail IMAP IDLE blind spot documented** (issue #86407).
    - Bug confirmed real and still present as of HA 2026.06.
    - Root cause: `aioimaplib` 29-minute IDLE timeout; Gmail stops pushing
      notifications at ~minute 15, creating a ~14-minute detection blind spot.
    - Impact: may cause false-positive `notification_system_error`, which would
      block morning watering preflight.
    - Added full write-up to "Known Gotchas & Solutions" in this file.
    - Added short bullet to START_HERE.md §3.
    - Open follow-up in START_HERE.md marked resolved.
  - **Workflow reconciliation — desktop / filesystem-MCP norm.** Superseded the
    web-era documentation-loading ritual throughout this file to match the
    START_HERE.md + local-git/MCP workflow established in the prior session.
    - **Workflow Guardrails:** Start now reads `START_HERE.md` first; Code uses
      artifacts / direct local-repo writes (not "canvas"); Repo Reference points
      at the local private repo via MCP; Close updates START_HERE.md §1-3.
    - **Canonical Documents:** reframed the four-doc table as a reference of what
      each doc covers, not a load-everything checklist; removed the "paste raw
      GitHub URLs one at a time" procedure (superseded; dual-source drift).
    - **Embedded instructions (for ChatGPT and Claude):** START-of-thread
      load-order replaced with START_HERE-first; "GitHub Desktop" replaced with
      "Git for Windows + VS Code Source Control."
    - **Embedded instructions (for Claude):** START-of-thread
      `project_knowledge_search` ritual and REPOSITORY web_fetch-primary replaced
      with filesystem-MCP-first (+ raw-URL web-only fallback); removed the
      `[X%]/190000` token-length-warning block in favour of a soft truncation
      note; SYSTEM SUMMARY now points to START_HERE.md §1-3 + architecture.md
      instead of restating a stale (~180) helper count; END OF THREAD now leads
      with updating START_HERE.md §1-3.
  - **Instruction blocks consolidated:** merged the two trailing project-instruction
    blocks ("for ChatGPT and Claude" + "for Claude") into a single canonical
    "Project Instructions (Claude project field)" block. Kept the lean orchestration
    layer plus the adaptation-policy note and the Europe/Berlin + absolute-dates
    preference; dropped the duplicated standards (debugging policy, code & config,
    RS-485 defaults, safety, version control) that already live in the body of this
    file.
  - **Rationale:** the local repo is canonical and START_HERE.md is the single
    fast-load entry point; keeping these instructions consistent with that removes
    the dual-source drift the new workflow exists to prevent.
  - **Open follow-up:** verify the Gmail IMAP #86407 timing gotcha is real; if so,
    document it in the body of this file and add it to START_HERE.md §3.
* **2026-06-28:**
  - **ADR-011 revised to SQLite (operational database).** Re-evaluated the 2026-04-08
    MariaDB decision; Layer 1 changed from the MariaDB add-on to a single SQLite file
    (`/homeassistant/watering_ops.db`), AppDaemon unchanged as the bridge. Rationale: tiny
    single-writer workload; SQLite removes the second add-on, the DB/user-via-add-on config,
    the driver, and charset setup with no loss of capability.
  - **ADR-011 heading nesting fixed:** was a top-level `#` heading with `##`/`###`
    subsections; demoted to `### ADR-011` with `####`/`#####` subsections to match the other
    ADRs and nest correctly.
  - **Consolidated to a single source of truth:** removed the duplicate standalone
    `docs/ADR-011-operational-database.md`; ADR-011 lives only in this file. Repointed
    references in `architecture.md`, `db_schema.sql`, `db_schema_init.py`, `db_setup_guide.md`,
    and the START_HERE doc index to this file.
  - **Created:** `docs/db_schema.sql`, `docs/db_setup_guide.md`, and the AppDaemon bootstrap
    (`home-assistant/packages/watering_appdaemon/db_schema_init.py` + `apps.yaml`).
  - **impl_roadmap.md Phase 3.5** updated from the MariaDB approach to the SQLite design.
  - **Schema refinements:** `fertigation_doses.pump_id` now stores the logical pump number
    (1-3), not the raw Modbus address (0x02-0x04), so the record survives any re-addressing
    or rewiring. `UNIQUE(cycle_id, zone_id)` on `zone_runs` deliberately NOT enforced (a
    zone may run more than once per cycle); noted in impl_roadmap.md Phase 3.5 for future
    visibility.

---

## Project Instructions (Claude project field)

Use this exact block in the Claude project instructions field. Single canonical
copy — the older dual "(for ChatGPT and Claude)" / "(for Claude)" blocks were
merged 2026-06-28. Detailed standards (debugging, code & config, RS-485, safety,
version control) are not repeated here; they live in the body of this file.

These instructions are copied in CLAUDE.md.  Any changes made here should also be
mirrored there.

```
#Watering System Project

ADAPTATION POLICY
Proactively suggest improvements to these instructions when they would improve
workflow or reliability. On user approval, update this block and add a
programming-notes.md change-log entry.

## START OF THREAD

**Read `docs/START_HERE.md` first** — from the local repo via the filesystem MCP
(`C:\Users\rober\watering-system-private`). It is the session manifest: current
phase, active blockers, top gotchas, and the doc index.

- Pull only what the task needs (doc index in START_HERE.md §4). Do NOT bulk-load
  the whole doc set. `project_knowledge_search` and raw-GitHub-URL fetching are
  deprecated as the default loading path (dual-source drift was the core problem
  this workflow replaces).
- Read impl_roadmap.md for live status only if START_HERE.md §1 looks stale or
  the task touches phase tracking.
- Confirm current phase/position (START_HERE.md §1) and readiness before proceeding.
- If START_HERE.md cannot be read, say so, confirm the filesystem MCP is
  connected and scoped to the repo, and do not start coding tasks until oriented.

---

## REPOSITORY

Primary: local repo via filesystem MCP at `C:\Users\rober\watering-system-private`.
Read directly; write only when asked. The repo is canonical.

Web-only fallback (no Desktop/MCP): raw URLs may be fetched.
Base: https://raw.githubusercontent.com/robertmacbridehart-coder/watering-system/refs/heads/main/
When user says "check /path/to/file.yaml" → construct the raw URL and web_fetch it.

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
Not duplicated here — see START_HERE.md §1-3 (position/blockers/gotchas) and
architecture.md (full design). Single source avoids drift.

DURING THREAD
- Propose approach BEFORE writing code (what, where, why); wait for approval
- Artifacts for code >20 lines
- Complete code (no placeholders, no TODOs)
- Show diffs for modifications
- Explain approach and trade-offs before generating code
- Europe/Berlin timezone; prefer absolute dates in replies
- If the conversation is getting long enough to risk truncation, say so and
  suggest wrapping up and starting a fresh session (START_HERE.md makes
  re-orienting cheap).

END OF THREAD
1. Update START_HERE.md §1-3 (Current Position, Blockers, Gotchas)
2. Add change-log entries to any docs touched
3. If significant architectural decision made, propose ADR entry
4. Provide diff-style summary of file changes or clearly marked replacements
5. List follow-ups as bullet points (become repo issues)

Methodical, requirements-first. Programming-notes.md instructions are mandatory.
```
