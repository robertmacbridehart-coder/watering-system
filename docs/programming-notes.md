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

## Project Index

* **Hardware**

  * Battery: Acconic A40 12 V 40 Ah LiFePO₄
  * Solar: ECTIVE MSP 100s 100 W panel
  * Charge Controller: Victron SmartSolar MPPT 100/20 (LOAD 15 A, charge 20 A, PV max 100 V)
  * SmartShunt + SmartSolar via BLE (Fabian-Schmidt’s `esphome-victron_ble`)
  * Switches & Relays: 19 mm IP67 3-position rotary (12–24 V), RS PRO DPDT 121-7804 + socket 121-7825, CZH-LABS 10 A DC-DC SSR (DIN)
  * Sensors: ELO 204KS22G01H float (SPDT), DFRobot SEN0600 RS-485 soil moisture/temperature
  * ESP32: ESP32-DEVKITC-VE
* **ESPHome (ESP32)**

  * UART2: TX=GPIO25, RX=GPIO26 → RS-485 relay board
  * Relays default OFF on reboot
  * Inputs: GPIO34=Low, GPIO35=Low-Low; GPIO32 (dry contact) = Pump Active
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
* Credentials (`mac_address`, `bindkey`) stored in `secrets.yaml`.
* Normalize entity names with the **“MPPT …”** scheme for easy filtering in Home Assistant.

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

### Pump Activity Input + Stats

```yaml
binary_sensor:
  - platform: gpio
    pin:
      number: GPIO32
      mode: INPUT_PULLUP
      inverted: true
    name: "Pump Active"
    id: pump_active
    device_class: running
    filters:
      - delayed_off: 1s
      - debounce: 50ms

sensor:
  - platform: pulse_counter
    pin: GPIO32
    name: "Pump Cycle Count"
    id: pump_cycle_count
    internal_filter: 100ms
    update_interval: 60s
    count_mode:
      rising_edge: INCREMENT
      falling_edge: DISABLE

  - platform: integration
    name: "Pump Total Run Time"
    sensor: pump_active
    time_unit: s
    id: pump_run_time
```

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

---

## Source Discipline

* Hardware parts → datasheet → install manual → distributor page.
* Firmware/config → official README/wiki → example configs.
* Weather/API → API reference, schema, payloads, limits.

---

## Home Assistant Automation Modules (planned)

* Watering Schedule: time/conditions, soil moisture thresholds, seasonal scaling.
* UI Dashboard: controls, tank/pump indicators, graphs.
* Fertilizer Integration: dosing schedule, lockouts, safety.
* Safety/Alarms: dry-run, low tank, overcurrent, comms loss.
* Maintenance/Stats: pump cycles/day, avg run time, energy stats.
* Weather Integration: Brightsky/DWD; rainfall skip; forecast weighting.

---

## Repo & Files (structure)

```
watering-system/
├─ docs/
│  └─ programming-notes.md   # canonical notes (this file)
├─ esphome/
│  └─ ... device YAMLs (sanitized)
├─ home-assistant/
│  ├─ configuration.yaml
│  └─ packages/
├─ README.md
├─ .gitignore
├─ secrets.example.yaml
└─ .github/
   └─ workflows/ (lint, gitleaks, publish)
```

* Secrets never committed. Only `secrets.example.yaml` with placeholders.
* Mirror workflow (`publish.yml`) sanitizes private → public.
* CI: `yamllint` + `gitleaks` run on push/PR.

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

---

## Project Instructions (for ChatGPT)

Use this exact block in the ChatGPT project instructions field:

```
PROJECT: Watering System — Working Instructions

GOAL
Build ESPHome + Home Assistant automations for the irrigation system with high reliability, traceability, and speed.

ADAPTATION POLICY
The assistant will proactively suggest improvements to these instructions whenever it would enhance workflow or efficiency. Upon user approval, the assistant will update this pinned section and reflect changes in the Programming Notes.

ALWAYS DO THIS AT THE START OF EVERY RELEVANT THREAD
1) Load context:
   - First, try to load the canonical notes from the public repo at https://github.com/robertmacbridehart-coder/watering-system/blob/main/docs/programming-notes.md.
   - If the public repo is not accessible, try to load the cached version.
   - If neither is available, return `Notes status: not loaded`.

2) Before recommending or generating any code, reference the code and configuration files in the public repo to maintain consistency.  
   - If you are unable to load the code from the repo, you must explicitly state that.

3) Post confirmation at the top of your first reply:
   - `Notes status: loaded` (include last change-log date if visible),
     `Notes status: cached version loaded (last change <date of cached notes>)`, or
     `Notes status: not loaded`.
   - `Scope:`` (module focus for this thread).

4) State where code changes belong (ESPHome vs HA packages path).

DURING THE THREAD
- Put any non-trivial code/config in Canvas (not inline chat). Keep chat for rationale and diffs.
- Prefer small, testable diffs over large dumps.
- Cite primary sources for all new parts/configs.
- When information might be recent or niche, browse and cite the current official source.

DEBUGGING POLICY (USE FIRST, NOT LAST)
1) Log first: capture raw payloads/serial/Modbus/BLE before guessing.
2) Validate against spec/schema (units, ranges, required keys).
3) Minimal reproducible config; then layer complexity.
4) Instrument temporarily (logger DEBUG, prints, on_value hooks).
5) Check timing (throttles, debounces, delays) and physical layer (termination, 0V/COM, power).

END OF THREAD
1) Update “programming-notes.md”: decisions, authoritative snippets, open items, change log.
2) Provide a diff-style summary of file changes or clearly marked file replacements.
3) List follow-ups as bullet points (these become repo Issues later).
4) Always suggest a Change Log entry whenever code or programming notes are modified.

CODE & CONFIG STANDARDS
- YAML: snake_case ids; Title Case friendly names; add icons where helpful.
- Relays default ALWAYS_OFF; add safety auto_off for long-open valves.
- Binary sensors: debounce ≥50 ms; use delayed_off if noisy.
- Secrets in secrets.yaml (never paste tokens/keys; never commit secrets).
- Prefer HA packages and ESPHome packages for modularity.

RS-485 / MODBUS DEFAULTS
- Topology: linear bus; short stubs only. Termination 120 Ω at both ends (ESP32 adapter + pump block).
- Common reference: share 0 V/COM; shield to earth at master only.
- 9600 8N1. DFRobot SEN0600 address via register 0x07D0 (2000), range 1–247; power only one sensor when changing.

VERSION CONTROL (RECOMMENDED)
- Use private repo + GitHub Desktop (full configs).
- Public sanitized repo with mirror workflow.
- Structure: /docs, /esphome, /home-assistant.
- Conventional commits, stable main, tags.
- Quality gates: yamllint, gitleaks.
- Never commit secrets; include secrets.example.yaml.

SAFETY
- Do not enable pump/valve actuation without interlocks and explicit user action.
- Default relays OFF on boot; maintain dry-run/low-tank lockouts and clear alarms.

PERFORMANCE & COMMUNICATION
- Use Canvas for heavy code; return diffs in chat.
- Europe/Berlin timezone; prefer absolute dates in replies.
- If the task is complex, return best-effort partial results rather than deferring.
```
