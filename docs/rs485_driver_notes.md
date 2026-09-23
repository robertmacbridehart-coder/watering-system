# RS-485 Dosing Pump Driver Notes

**Document Version:** 1.0  
**Date:** 2025-10-28  
**Driver Model:** IRS42 Integrated 485 Bus Open-Loop Stepper Driver  
**Purpose:** Complete reference for implementing Modbus control of 3 peristaltic dosing pumps

---

## Table of Contents

1. [Hardware Overview](#1-hardware-overview)
2. [DIP Switch Configuration](#2-dip-switch-configuration)
3. [RS-485 Bus Topology](#3-rs-485-bus-topology)
4. [Power Control Strategy](#4-power-control-strategy)
5. [Modbus Communication Parameters](#5-modbus-communication-parameters)
6. [Register Map - Essential Registers](#6-register-map---essential-registers)
7. [Command Sequences](#7-command-sequences)
8. [Calibration Procedure](#8-calibration-procedure)
9. [Error Handling](#9-error-handling)
10. [Operational Limits](#10-operational-limits)
11. [Tubing Specifications](#11-tubing-specifications)
12. [Implementation TODO List](#12-implementation-todo-list)
13. [Quick Reference Tables](#13-quick-reference-tables)

---

## 1. Hardware Overview

### 1.1 Driver Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Model** | IRS42 Integrated RS-485 Stepper Driver | Open-loop control |
| **Input Voltage** | DC 12-40V | 24V nominal |
| **Output Current** | 0-2000 mA | Configurable via register |
| **Control Current** | 7-16 mA typical | At control inputs |
| **Operating Temp** | -25°C to 55°C | Ambient |
| **Humidity** | 40% to 90% RH | Non-condensing |
| **Communication** | RS-485/Modbus RTU | Half-duplex |

### 1.2 Pump System Configuration

| Pump ID | Modbus Address | Function | Notes |
|---------|----------------|----------|-------|
| **Pump 1** | 0x02 (decimal 2) | NPK fertilizer | Primary nutrient |
| **Pump 2** | 0x03 (decimal 3) | Micronutrients | Secondary nutrient |
| **Pump 3** | 0x04 (decimal 4) | pH adjustment | Optional |

**Peristaltic Pump Type:**
- 3-roller design
- Unidirectional flow (forward only in normal operation)
- Typical capacity: 1-16 mL/min (dependent on motor speed and tube size)

---

## 2. DIP Switch Configuration

### 2.1 DIP Switch Functions

The IRS42 has **6 DIP switches (SW1-SW6)** located on the driver board:

| Switch | Function | Values |
|--------|----------|--------|
| **SW1** | Address bit 0 | OFF=0, ON=1 |
| **SW2** | Address bit 1 | OFF=0, ON=2 |
| **SW3** | Address bit 2 | OFF=0, ON=4 |
| **SW4** | Address bit 3 | OFF=0, ON=8 |
| **SW5** | Baud rate | OFF=9600, ON=115200 |
| **SW6** | 120Ω termination | OFF=disabled, ON=enabled |

**Address Formula:**  
`Modbus_Address = (SW1 × 1) + (SW2 × 2) + (SW3 × 4) + (SW4 × 8)`

### 2.2 Configured Settings

#### Pump 1 (Address 0x02)
```
SW1: OFF    (bit 0 = 0)
SW2: ON     (bit 1 = 1)   → Address = 0 + 2 + 0 + 0 = 2
SW3: OFF    (bit 2 = 0)
SW4: OFF    (bit 3 = 0)
SW5: OFF    (9600 baud)
SW6: OFF    (no termination - stub connection)
```

#### Pump 2 (Address 0x03)
```
SW1: ON     (bit 0 = 1)
SW2: ON     (bit 1 = 1)   → Address = 1 + 2 + 0 + 0 = 3
SW3: OFF    (bit 2 = 0)
SW4: OFF    (bit 3 = 0)
SW5: OFF    (9600 baud)
SW6: OFF    (no termination - middle of bus)
```

#### Pump 3 (Address 0x04)
```
SW1: OFF    (bit 0 = 0)
SW2: OFF    (bit 1 = 0)   → Address = 0 + 0 + 4 + 0 = 4
SW3: ON     (bit 2 = 1)
SW4: OFF    (bit 3 = 0)
SW5: OFF    (9600 baud)
SW6: OFF    (no termination - middle of bus)
```

### 2.3 Visual Reference

```
Legend: [■ ON] [□ OFF]

Pump 1:  [□][■][□][□] [□][□]  Address: 2, 9600 baud, no termination
Pump 2:  [■][■][□][□] [□][□]  Address: 3, 9600 baud, no termination
Pump 3:  [□][□][■][□] [□][□]  Address: 4, 9600 baud, no termination
         SW1 SW2 SW3 SW4 SW5 SW6
```

---

## 3. RS-485 Bus Topology

### 3.1 Physical Layout

**Hub/Star Topology with Terminal Block Junction:**

```
Cabinet A                          Cabinet B
┌─────────────┐                   ┌────────────────────┐
│   ESP32     │                   │  Terminal Block    │
│   UART2     │    1m cable       │  (2cm A+/B-/GND)   │
│  GPIO25/26  │◄─────────────────►│   Hub Junction     │
│             │                   │                    │
│  120Ω Term  │                   │  No Termination    │
└─────────────┘                   └──────┬─────────────┘
                                         │
                              ┌──────────┼──────────┐
                              │          │          │
                            10cm       10cm       10cm
                              │          │          │
                          ┌───▼──┐   ┌──▼───┐   ┌──▼───┐
                          │Pump 1│   │Pump 2│   │Pump 3│
                          │(0x02)│   │(0x03)│   │(0x04)│
                          └──────┘   └──────┘   └──────┘
                          SW6=OFF    SW6=OFF    SW6=OFF
                          
                          (Future: 5m stubs to field sensors)
                                         │
                                    ┌────┴────┐
                                    │ Sensors │
                                    │ 0x05+   │
                                    └─────────┘
```

**Key Characteristics:**
- **Main bus:** 1m cable from ESP32 to terminal block
- **Hub point:** Terminal block in Cabinet B (2cm bus bar)
- **Pump stubs:** 10cm from terminal block to each pump
- **Sensor stubs (future):** Up to 5m from terminal block to field locations
- **Termination:** Single 120Ω at ESP32 end only

### 3.2 Wiring Specifications

| Component | Specification | Notes |
|-----------|---------------|-------|
| **Main Cable (ESP32→Terminal)** | 1m shielded twisted pair | 22-24 AWG, recommend Belden 3105A |
| **Pump Stub Cables** | 10cm twisted pair | Short enough to be electrically negligible |
| **Sensor Stub Cables** | Up to 5m shielded twisted pair | Future expansion, acceptable at 9600 baud |
| **Terminal Block** | 2cm A+/B-/GND bus bar | Phoenix Contact or equivalent |
| **Shield Ground** | ESP32 end only | Prevents ground loops |
| **Common Ground** | All devices | CRITICAL - must be connected |

### 3.3 Termination Strategy

**Single termination at ESP32 end:**

| Location | Termination | Method |
|----------|-------------|--------|
| **ESP32 RS-485 Adapter** | 120Ω enabled | Enable on adapter hardware |
| **Terminal Block** | None | Hub point, not an endpoint |
| **Pump 1** | SW6 = OFF | Stub connection, no termination |
| **Pump 2** | SW6 = OFF | Stub connection, no termination |
| **Pump 3** | SW6 = OFF | Stub connection, no termination |

**Why this works:**
- At 9600 baud, signal reflections from short stubs are negligible
- 10cm stub delay: ~1 nanosecond (0.001% of 104µs bit time)
- 5m stub delay: ~50 nanoseconds (0.05% of 104µs bit time)
- Single termination at ESP32 prevents reflections on main 1m cable

**If you experience communication errors (unlikely):**
1. Add second 120Ω resistor at terminal block (between A+ and B-)
2. Increase ESPHome `send_wait_time` from 8ms to 15-20ms
3. Verify cable quality and shield grounding

### 3.4 Future Sensor Integration

**DFRobot SEN0600 Soil Moisture Sensors:**
- Connect to same terminal block via 5m stubs
- Address range: 0x05, 0x06, 0x07, 0x08... (avoid 0x02-0x04 used by pumps)
- Configure address via register 0x07D0 (power only ONE sensor during address change)
- Same 9600 8N1 settings as pumps
- No topology or termination changes required

**Address Planning:**

| Device Type | Address Range | Notes |
|-------------|---------------|-------|
| **Pumps** | 0x02, 0x03, 0x04 | Fixed, configured via DIP switches |
| **Sensors** | 0x05 - 0x10 | Up to 12 sensors (or more if needed) |
| **Reserved** | 0x01 | Avoid (common default address) |
| **Available** | 0x11 - 0xF7 | Future expansion (247 max addresses) |

**Sensor wiring from terminal block:**
- A+ (yellow/orange wire)
- B- (green/blue wire)  
- GND (black wire)
- 12-24V power (red wire, if sensors require external power)

---

## 4. Power Control Strategy

### 4.1 24V Power Switching

**All pumps powered via R10 (24V Cabinet Enable):**
- Relay R10 (`switch.watering_system_relay_10_24v_cabinet`)
- Controls 24V supply to all 3 pumps simultaneously
- Default state: OFF (no standby power consumption)
- Enables/disables 24V to pump DC+ terminals

### 4.2 RS-485 Bus Isolation

**When R10 is OFF (pumps unpowered):**
- RS-485 bus to pumps is isolated via relays
- Isolation typically occurs at relay board in Cabinet A or at terminal block in Cabinet B
- Prevents backfeeding or ghost communications
- Protects ESP32 UART from floating bus conditions

**When R10 is ON (pumps powered):**
- RS-485 bus connected through 1m cable to terminal block
- Isolation relays close, connecting ESP32 UART to pump bus
- Wait **500ms** after R10 closes before sending first Modbus command
- Allows pumps to complete boot sequence

**Physical layout:**
- **Cabinet A:** ESP32, relay board, RS-485 adapter with termination
- **Cabinet B:** 24V power distribution, terminal block hub, pumps
- **Connection:** 1m cable (A+/B-/GND) between cabinets

### 4.3 Power Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Voltage** | DC 24V nominal | 12-40V supported |
| **Current per pump** | 1-2A typical | At operating speed |
| **Total for 3 pumps** | 3-6A @ 24V | Size power supply accordingly |
| **Standby current** | 0A (R10 OFF) | No power when not in use |

### 4.4 Startup Sequence

```yaml
1. Close R10 (enable 24V to pumps)
2. Wait 500ms (pump boot time)
3. Close RS-485 isolation relays (if separate)
4. Wait 100ms (bus stabilization)
5. Send first Modbus command (read address verification)
```

---

## 5. Modbus Communication Parameters

### 5.1 Serial Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Baud Rate** | 9600 bps | Set via SW5=OFF |
| **Data Bits** | 8 | |
| **Parity** | None | 8N1 format |
| **Stop Bits** | 1 | |
| **Frame Format** | Modbus RTU | |
| **CRC** | CRC16 | Low byte first, high byte last |
| **Inter-frame delay** | 3.5 char times | ~3.6ms at 9600 baud |

### 5.2 Supported Modbus Function Codes

| Function Code | Description | Max Registers |
|---------------|-------------|---------------|
| **0x03** | Read holding registers | 16 per read |
| **0x06** | Write single register | 1 |
| **0x10** | Write multiple registers | Multiple |

### 5.3 Timing Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Response timeout** | 200-500ms | Suggested conservative value |
| **Inter-command delay** | 10-20ms | Between sequential commands |
| **Send wait time** | 8ms | ESPHome `send_wait_time` parameter |
| **RX buffer size** | 512 bytes | ESPHome `rx_buffer_size` parameter |

---

## 6. Register Map - Essential Registers

### 6.1 Status Registers (Read-Only)

| Address | Name | Values | Description |
|---------|------|--------|-------------|
| **0x0000** | Drive Version | varies | Firmware version |
| **0x0002** | Node Number | 1-247 | Current Modbus address |
| **0x0003** | Operating Mode | 0=None, 1=Speed, 2=RelPos, 4=AbsPos, 8=Home | Current mode |
| **0x0004** | Movement Status | 0=Standstill, 1=Locked, 2=Motion, 3=Locked+Motion | Motor state |
| **0x0005** | Home Status | 0=None, 1=Homing, 2=Complete | Homing state |
| **0x0006** | Direction | 0=Forward, 1=Reverse, 2=Stopped | Motion direction |
| **0x0007** | Error Code | 0=Normal, others=error | Primary error code |
| **0x0008** | Error Subcode | 0=Normal, others=subcode | Error detail |

### 6.2 Control Registers (Read/Write)

#### Speed Control
| Address | Name | Range | Default | Units | Description |
|---------|------|-------|---------|-------|-------------|
| **0x0030** | Start Speed | 1-300 | 5 | rev/min | Initial ramp speed |
| **0x0031** | Acceleration Time | 0-2000 | 100 | ms | Time to reach max speed |
| **0x0032** | Deceleration Time | 0-2000 | 100 | ms | Time to stop |
| **0x0033** | Maximum Speed | -3000 to +3000 | 60 | rev/min | Target speed (sign = direction) |

**CRITICAL:** Units are **motor rev/min**, NOT mL/min!

#### Command Registers
| Address | Name | Values | Description |
|---------|------|--------|-------------|
| **0x0037** | Start Command | 0x0001 = Speed mode | Bit 0 triggers speed mode start |
| **0x0038** | Stop Command | 0x0001 = Normal stop | Bit 0 triggers normal stop |
| **0x0039** | Enable Control | 0x0001 = Software enable | Bit 0 enables motor |

#### Configuration Registers
| Address | Name | Range | Default | Units | Description |
|---------|------|-------|---------|-------|-------------|
| **0x001E** | Operating Current | 0-6000 | 1000 | mA | Motor current |
| **0x001F** | Microstepping | 200-60000 | 10000 | pulses/rev | Step resolution |
| **0x0022** | Holding Current % | 0-100 | 50 | % | Current when stationary |

### 6.3 Register Usage Summary

**For dosing pump control, you only need:**
1. **0x0030-0x0033** - Speed parameters (set once per dose)
2. **0x0037** - Start command (trigger flow)
3. **0x0038** - Stop command (end flow)
4. **0x0039** - Enable/disable motor (set at initialization)
5. **0x0004** - Read movement status (verify running)
6. **0x0007/0x0008** - Read error codes (fault detection)

---

## 7. Command Sequences

### 7.1 Initialization Sequence

**Run once after R10 powers pumps:**

```yaml
# For each pump address (0x02, 0x03, 0x04):

Step 1: Verify communication
  Read register 0x0002 (should return pump address)
  
Step 2: Enable motor
  Write 0x0001 to register 0x0039
  
Step 3: Set ramp parameters
  Write 5 to register 0x0030 (start speed = 5 rev/min)
  Write 500 to register 0x0031 (accel time = 500ms)
  Write 500 to register 0x0032 (decel time = 500ms)
  
Step 4: Set operating current (optional, default 1000mA is OK)
  Write 1000 to register 0x001E (1000mA = 1A)
```

### 7.2 Start Pump Sequence

**To start dosing at a specific flow rate:**

```yaml
# Calculate required rev/min from calibration curve:
# rev_min = (target_flow_mL_min - intercept) / slope

Step 1: Set target speed
  Write calculated_rev_min to register 0x0033
  Example: Write 25 to 0x0033 for 25 rev/min
  
Step 2: Trigger start
  Write 0x0001 to register 0x0037 (start in speed mode)
  
Step 3: Verify running (optional)
  Read register 0x0004
  Expected: 2 (motion) or 3 (locked+motion)
```

**Modbus command examples (for pump at address 0x02):**
```
Set 25 rev/min:  02 06 00 33 00 19 [CRC]
Start pump:      02 06 00 37 00 01 [CRC]
```

### 7.3 Stop Pump Sequence

**To stop dosing:**

```yaml
Step 1: Send stop command
  Write 0x0001 to register 0x0038 (normal stop)
  
Step 2: Wait for deceleration
  Wait for decel_time (500ms default)
  
Step 3: Verify stopped (optional)
  Read register 0x0004
  Expected: 0 (standstill) or 1 (locked/holding)
```

**Modbus command example:**
```
Stop pump:  02 06 00 38 00 01 [CRC]
```

### 7.4 Emergency Stop

**For immediate halt (no deceleration ramp):**

```yaml
Write 0x0002 to register 0x0038 (emergency stop)
Command: 02 06 00 38 00 02 [CRC]
```

---

## 8. Calibration Procedure

### 8.1 Overview

**Goal:** Establish relationship between motor speed (rev/min) and flow rate (mL/min)

**Method:** Gravimetric measurement at 5 setpoints × 3 repeats

**Output:** Linear calibration curve: `flow_mL_min = slope × rev_min + intercept`

**Full procedure:** See `/docs/fert_pump_cal_v2.md`

### 8.2 Initial Estimates

**Estimated mL per revolution:** ~0.3 mL/rev (3-roller, 1mm ID silicone tube)

**Starting calibration speeds:**

| Setpoint | Target Flow | Estimated Speed | Expected Mass (180s, SG=1.05) |
|----------|-------------|-----------------|--------------------------------|
| 1 | 2 mL/min | 7 rev/min | ~6.3 g |
| 2 | 4 mL/min | 13 rev/min | ~12.6 g |
| 3 | 8 mL/min | 27 rev/min | ~25.2 g |
| 4 | 12 mL/min | 40 rev/min | ~37.8 g |
| 5 | 16 mL/min | 53 rev/min | ~50.4 g |

**Note:** These are initial guesses. Actual speeds will be refined during calibration.

### 8.3 Calibration Curve Usage

**At runtime, to calculate required speed:**

```python
# Given: target dose (mL) and runtime (minutes)
required_flow_mL_min = target_dose_ml / runtime_min

# Using stored calibration coefficients:
slope = input_number.fert_pump1_cal_slope  # mL per rev
intercept = input_number.fert_pump1_cal_intercept  # mL/min offset

# Calculate required motor speed:
required_rev_min = (required_flow_mL_min - intercept) / slope

# Clamp to valid range:
required_rev_min = max(1, min(3000, required_rev_min))

# Write to register 0x0033
```

### 8.4 Calibration Storage

**Home Assistant helpers (per pump):**
- `input_number.fert_pump{n}_cal_slope` - Slope (mL per rev)
- `input_number.fert_pump{n}_cal_intercept` - Intercept (mL/min)
- `input_number.fert_pump{n}_cal_r2` - R² fit quality
- `input_datetime.fert_pump{n}_last_cal` - Calibration date
- `input_number.fert_pump{n}_cal_pressure` - Test pressure (bar)
- `input_text.fert_pump{n}_cal_notes` - Notes

**Acceptance criteria:**
- R² ≥ 0.995
- CV ≤ 3% across repeats at each setpoint
- Residuals ≤ ±5% or ±0.3 mL/min

### 8.5 Tubing Break-In Procedure

**Before first calibration:**

```yaml
1. Install new tubing in pump head
2. Run pump at 30 rev/min for 2-3 hours (water only)
3. Stop and let tubing rest for 30 minutes
4. Check for permanent deformation
5. If OK, proceed with calibration
```

**Why:** Silicone tubing stretches 5-10% in first hours of use.

**Automation:** Create Home Assistant script for automated break-in cycle.

### 8.6 Recalibration Schedule

**Full recalibration required when:**
- Tubing replaced or pump head serviced
- Dosing error >10% detected in operation
- Stock solution density changes >3%
- PRV pressure adjusted
- Every 90 days (quarterly maintenance)

---

## 9. Error Handling

### 9.1 Error Code Table

| Error Code (0x0007) | Subcode (0x0008) | Meaning | LED Pattern | Action |
|---------------------|------------------|---------|-------------|--------|
| **0x00** | 0x00 | Normal operation | Steady green | None |
| **0x01** | 0x10 | Overcurrent | Flickering | Check wiring, power cycle |
| **0x02** | 0x20 | Overvoltage | Flickering | Check power supply |
| **0x03** | 0x30 | Undervoltage | Flickering | Check power supply |
| **0x04** | 0x41-0x42 | EEPROM error | None | Non-resettable fault |
| **0x05** | 0x51 | CRC check error | None | Resend command |
| **0x05** | 0x52 | Invalid function code | None | Check command format |
| **0x05** | 0x53 | Illegal register (read) | None | Check register address |
| **0x05** | 0x54 | Illegal register (write) | None | Check register address |
| **0x05** | 0x55 | Too many registers | None | Read ≤16 registers |
| **0x05** | 0x56 | Permission violation | None | Check register read/write access |
| **0x05** | 0x57 | Data out of range | None | Check value limits |
| **0x06** | 0x60-0x62 | Phase loss | Flashing | Check motor wiring |
| **0x07** | 0x70-0x72 | Out of tolerance | Flashing | Check current/power settings |
| **0x08** | 0x80 | Home timeout | Flashing | Not applicable (dosing mode) |

### 9.2 Error Detection Strategy

**Poll error registers periodically:**

```yaml
# Every 5 seconds while pump running:
1. Read registers 0x0007 and 0x0008
2. If error_code != 0:
   - Stop dosing immediately
   - Set state to error_fert_pump_fault
   - Send CRITICAL notification
   - Log error code and subcode
```

### 9.3 Error Recovery

**For communication errors (0x05/0x51-0x57):**
- Retry command once with 100ms delay
- If still failing, abort and notify

**For hardware errors (0x01-0x03, 0x06-0x07):**
- Abort fertigation immediately
- Do NOT attempt automatic recovery
- Require manual investigation and reset

**For EEPROM errors (0x04):**
- Pump is non-functional
- Notify user, replace driver board

### 9.4 Home Assistant Error Handling

**Recommended approach (from your answer #6):**

```yaml
# Option A: Abort immediately on any error
- If pump error detected:
  - Stop all pumps
  - Close all valves
  - Set state to error_fert_pump_fault
  - Send CRITICAL notification (WhatsApp + Email)
  - Block further fertigation until manual reset
```

---

## 10. Operational Limits

### 10.1 Speed Limits

| Parameter | Min | Max | Recommended for Dosing |
|-----------|-----|-----|------------------------|
| **Maximum Speed** | 1 rev/min | 3000 rev/min | 1-100 rev/min |
| **Start Speed** | 1 rev/min | 300 rev/min | 5 rev/min |
| **Practical limit** | 1 rev/min | ~1000 rev/min | Depends on tube life |

**Why limit speed?**
- Higher speeds = faster tube wear
- Higher speeds = reduced accuracy
- Dosing typically needs 2-16 mL/min = 7-53 rev/min at 0.3 mL/rev

### 10.2 Ramp Parameters

**Recommended values for dosing:**

| Parameter | Conservative | Aggressive | Calibration |
|-----------|-------------|------------|-------------|
| **Start Speed** | 5 rev/min | 10 rev/min | 5 rev/min |
| **Accel Time** | 500 ms | 200 ms | 100 ms |
| **Decel Time** | 500 ms | 200 ms | 100 ms |

**Trade-offs:**
- Slower ramps: smoother flow, less pressure spike, longer startup
- Faster ramps: quicker response, may cause pressure transients

### 10.3 Duty Cycle

**Continuous operation:** ✅ Supported
- No duty cycle limitations mentioned in manual
- Pure sine wave control reduces heat
- Monitor motor temperature; if >60°C, reduce current

**Typical dosing cycle:**
- Phase 1: Run for 5-30 minutes
- Phase 2: Run for 5-30 minutes
- Rest: Hours to days between fertigation events

### 10.4 Current Limits

| Parameter | Range | Default | Recommended for Dosing |
|-----------|-------|---------|------------------------|
| **Operating Current** | 0-6000 mA | 1000 mA | 800-1200 mA |
| **Holding Current %** | 0-100% | 50% | 50% |

**Current tuning:**
- Too low: Motor stalls or vibrates
- Too high: Excessive heat, wasted power
- Start with 1000mA, increase if motor stalls under back pressure

---

## 11. Tubing Specifications

### 11.1 Pump Head Tubing

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Material** | Silicone (generic peristaltic grade) | No specific part number available |
| **Inner Diameter** | 1 mm | Critical for flow calculation |
| **Outer Diameter** | 3 mm | Wall thickness = 1mm |
| **Hardness** | Unknown (typical Shore A 60-70) | Softer = more compression, faster wear |
| **Expected Lifetime** | 100-500 hours | Depends on speed and pressure |

### 11.2 Feed/Discharge Lines

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Inner Diameter** | 2 mm | Larger to reduce resistance |
| **Outer Diameter** | 4 mm | |
| **Material** | Silicone (assumed) | Or compatible flexible tubing |

### 11.3 Replacement Schedule

**Replace tubing when:**
- Calibration R² drops below 0.995
- Dosing error >10% despite recalibration
- Visual inspection shows cracking or permanent deformation
- Every 6 months (preventative)

**After replacement:**
- Run 2-3 hour break-in cycle
- Perform full calibration
- Update `input_datetime.fert_pump{n}_last_cal`

---

## 12. Implementation TODO List

### Phase 1: Hardware Setup ⚙️

- [ ] **1.1** Configure DIP switches on all 3 pumps
  - Pump 1: SW1=OFF, SW2=ON, SW3=OFF, SW4=OFF, SW5=OFF, SW6=OFF
  - Pump 2: SW1=ON, SW2=ON, SW3=OFF, SW4=OFF, SW5=OFF, SW6=OFF
  - Pump 3: SW1=OFF, SW2=OFF, SW3=ON, SW4=OFF, SW5=OFF, SW6=OFF
  - **Note:** All SW6=OFF (no termination on pumps)
  
- [ ] **1.2** Wire RS-485 bus
  - Run 1m cable (A+/B-/GND) from ESP32 in Cabinet A to terminal block in Cabinet B
  - Connect 10cm stub cables from terminal block to each pump (A+/B-/GND)
  - Verify common ground: All pump DC- terminals to system 0V
  - Enable 120Ω termination on ESP32 RS-485 adapter
  - Do NOT add termination at terminal block (hub point)
  - Verify shield grounded at ESP32 end only
  
- [ ] **1.3** Connect 24V power
  - Wire all 3 pump DC+ terminals to R10 relay output
  - Wire all 3 pump DC- terminals to system 0V (common ground)
  - Verify power supply can provide 6A @ 24V
  
- [ ] **1.4** Install RS-485 bus isolation relays (if not already done)
  - Relay between ESP32 and 1m cable (controlled by R10 or separate)
  - Ensures bus is isolated when pumps are unpowered
  
- [ ] **1.5** Verify wiring with multimeter
  - Check continuity: A+ from ESP32 through 1m cable to terminal block to all pumps
  - Check continuity: B- from ESP32 through 1m cable to terminal block to all pumps
  - Check no shorts: A+ to B-, A+ to GND, B- to GND
  - Measure ~120Ω resistance: A+ to B- at ESP32 end (should see termination resistor)

---

### Phase 2: ESPHome Configuration 📝

- [ ] **2.1** Add Modbus UART configuration to ESPHome
  - Configure UART2 (TX=GPIO25, RX=GPIO26)
  - Set baud_rate: 9600, parity: NONE, stop_bits: 1
  - Set send_wait_time: 8ms, rx_buffer_size: 512
  
- [ ] **2.2** Define pump entities in ESPHome
  - Create Modbus controller for addresses 0x02, 0x03, 0x04
  - Create sensor entities for status registers (0x0004, 0x0007, 0x0008)
  - Create number entities for speed setpoint (0x0033)
  
- [ ] **2.3** Flash updated config to ESP32
  
- [ ] **2.4** Verify entities appear in Home Assistant
  - Check Developer Tools → States
  - Verify entity names follow pattern: `sensor.fert_pump_{n}_*`

---

### Phase 3: Communication Testing 📡

- [ ] **3.1** Enable 24V power (close R10)
  - Via Home Assistant: turn on `switch.watering_system_relay_10_24v_cabinet`
  - Wait 500ms for pump boot
  
- [ ] **3.2** Test read address verification
  - For each pump, read register 0x0002
  - Verify returns: 2, 3, 4 respectively
  
- [ ] **3.3** Test firmware version read
  - For each pump, read register 0x0000
  - Record firmware version numbers
  
- [ ] **3.4** Test write/read speed setpoint
  - Write 25 to register 0x0033
  - Read back register 0x0033
  - Verify returns 25
  
- [ ] **3.5** Monitor for communication errors
  - Check ESPHome logs for CRC errors, timeouts
  - Check register 0x0007/0x0008 for error codes
  - If errors: verify wiring, termination, baud rate

---

### Phase 4: Motion Testing 🔄

- [ ] **4.1** Write initialization parameters (all pumps)
  - Write 0x0001 to register 0x0039 (enable motor)
  - Write 5 to register 0x0030 (start speed)
  - Write 500 to register 0x0031 (accel time)
  - Write 500 to register 0x0032 (decel time)
  
- [ ] **4.2** Test start command at low speed
  - Write 10 to register 0x0033 (target 10 rev/min)
  - Write 0x0001 to register 0x0037 (start)
  - Verify pump rotates smoothly
  - Read register 0x0004 (should be 2 or 3 = motion)
  
- [ ] **4.3** Test stop command
  - Write 0x0001 to register 0x0038 (normal stop)
  - Verify pump decelerates and stops
  - Read register 0x0004 (should be 0 or 1 = stopped)
  
- [ ] **4.4** Test emergency stop
  - Start pump at 50 rev/min
  - Write 0x0002 to register 0x0038 (emergency stop)
  - Verify immediate halt (no ramp)
  
- [ ] **4.5** Test speed changes
  - Start at 20 rev/min
  - Change to 40 rev/min (write 40 to 0x0033)
  - Verify smooth acceleration
  
- [ ] **4.6** Test all 3 pumps independently
  - Repeat steps 4.2-4.5 for each pump
  - Verify no crosstalk or interference

---

### Phase 5: Break-In Automation 🔁

- [ ] **5.1** Create Home Assistant script: `script.fert_pump_breakin`
  - Input parameters: pump_id (1, 2, or 3)
  - Actions:
    1. Enable 24V (R10)
    2. Initialize pump (registers 0x0030-0x0032, 0x0039)
    3. Set speed 30 rev/min (register 0x0033)
    4. Start pump (register 0x0037)
    5. Wait 2 hours (7200 seconds)
    6. Stop pump (register 0x0038)
    7. Send notification: "Break-in complete for pump {n}"
  
- [ ] **5.2** Test break-in script (dry run, short duration)
  - Run script with 60-second duration for testing
  - Verify all commands execute correctly
  - Verify notification sent
  
- [ ] **5.3** Run full break-in on all 3 pumps
  - Pump 1: 2-hour cycle
  - Pump 2: 2-hour cycle
  - Pump 3: 2-hour cycle
  - Can run sequentially or one at a time over multiple days

---

### Phase 6: Initial Calibration 🧪

- [ ] **6.1** Prepare calibration equipment
  - 0.01g scale
  - 100 mL graduated cylinder
  - Stopwatch or timer
  - Stock fertilizer solution
  
- [ ] **6.2** Measure specific gravity (SG)
  - Weigh 100 mL of stock solution
  - Calculate: SG = mass / 100
  - Record in `input_number.fert_stock_sg` (if exists)
  
- [ ] **6.3** Run single-point calibration (Pump 1 only)
  - Target: 8 mL/min (mid-range)
  - Estimated speed: 27 rev/min (based on 0.3 mL/rev)
  - Run for 180 seconds
  - Measure collected mass
  - Calculate actual flow: (mass / SG) × (60 / 180)
  - Calculate actual mL/rev: flow / 27
  - Record in notes
  
- [ ] **6.4** Adjust speed estimate if needed
  - If flow significantly different from 8 mL/min, recalculate:
    - New mL/rev = actual_flow / 27
    - Recalculate all 5 setpoint speeds using new mL/rev
  
- [ ] **6.5** Run full 5-point × 3-repeat calibration (Pump 1)
  - Use revised speed estimates from 6.4
  - Follow procedure in fert_pump_cal_v2.md
  - Record all 15 data points in spreadsheet or Home Assistant
  
- [ ] **6.6** Fit calibration curve
  - Plot flow (mL/min) vs. speed (rev/min)
  - Fit linear model: flow = slope × speed + intercept
  - Calculate R² (must be ≥ 0.995)
  - Store coefficients in Home Assistant:
    - `input_number.fert_pump1_cal_slope`
    - `input_number.fert_pump1_cal_intercept`
    - `input_number.fert_pump1_cal_r2`
    - `input_datetime.fert_pump1_last_cal`
  
- [ ] **6.7** Repeat calibration for Pumps 2 and 3
  - Use same setpoint speeds as Pump 1 (likely similar flow rates)
  - Store coefficients in respective helpers

---

### Phase 7: Integration with Fertigation Scripts 🧩

- [ ] **7.1** Create helper script: `script.calculate_pump_speed`
  - Input: target_dose_ml, runtime_min, pump_id
  - Calculate required_flow = dose / runtime
  - Calculate required_speed = (flow - intercept) / slope
  - Clamp to valid range (1-3000 rev/min)
  - Return speed value
  
- [ ] **7.2** Update `script.start_dosing_pumps`
  - Input: zone_id, phase (1 or 2)
  - For each pump with dose > 0:
    1. Calculate required speed using helper
    2. Write speed to register 0x0033
    3. Write 0x0001 to register 0x0037 (start)
  - Add error checking: read 0x0007/0x0008 after start
  
- [ ] **7.3** Update `script.stop_dosing_pumps`
  - For each running pump:
    1. Write 0x0001 to register 0x0038 (stop)
    2. Wait for decel_time (500ms)
    3. Verify stopped: read 0x0004
  
- [ ] **7.4** Add error monitoring automation
  - Trigger: Every 5 seconds while dosing active
  - Condition: Any pump has error code != 0
  - Action:
    - Stop all pumps immediately
    - Close fert line valve
    - Set state to error_fert_pump_fault
    - Send CRITICAL notification
  
- [ ] **7.5** Test complete fertigation cycle (dry run)
  - Use test zone with short runtime (2-3 minutes)
  - Verify pumps start at calculated speeds
  - Verify pumps stop after dose duration
  - Verify no errors logged

---

### Phase 8: Production Testing 🚀

- [ ] **8.1** Test single-dose cycle (light program)
  - Select zone with light program
  - Set small dose (e.g., 10 mL)
  - Run watering cycle
  - Measure actual delivered volume (collect from emitter)
  - Verify accuracy within 10%
  
- [ ] **8.2** Test split-dose cycle (normal/heavy program)
  - Select zone with normal program
  - Set dose (e.g., 30 mL)
  - Run Phase 1, collect output, measure
  - Run Phase 2, collect output, measure
  - Verify total dose accuracy within 10%
  
- [ ] **8.3** Test error handling
  - Trigger error condition (e.g., disconnect one pump mid-cycle)
  - Verify system aborts immediately
  - Verify notification sent
  - Verify system blocks further fertigation
  
- [ ] **8.4** Test recalibration trigger
  - Manually adjust calibration coefficient by 20%
  - Run dosing cycle
  - Measure actual vs. expected dose
  - Verify calibration status shows warning/expired

---

### Phase 9: Documentation Updates 📚

- [ ] **9.1** Update `impl_roadmap.md`
  - Mark Phase 3.3 (Fert Scripts) as complete
  - Add notes on calibration results
  - Add notes on any issues encountered
  
- [ ] **9.2** Update `programming-notes.md`
  - Add section: "RS-485 Pump Configuration"
  - Include DIP switch settings
  - Include register map quick reference
  - Add to Change Log
  
- [ ] **9.3** Update `architecture.md`
  - Update Section 5.4 with actual register addresses
  - Update Section 4.4 with final calibration storage structure
  - Add notes on error handling
  
- [ ] **9.4** Update `test_scenarios.md`
  - Add new test section: "Fertigation Pump Tests"
  - Include tests for:
    - Communication verification
    - Speed control accuracy
    - Error detection and recovery
    - Multi-pump coordination
    - Calibration validation

---

## 13. Quick Reference Tables

### 13.1 Command Summary

| Operation | Register | Value | Modbus Example (Pump 2 @ 0x02) |
|-----------|----------|-------|--------------------------------|
| **Enable motor** | 0x0039 | 0x0001 | `02 06 00 39 00 01 [CRC]` |
| **Set start speed** | 0x0030 | 5 | `02 06 00 30 00 05 [CRC]` |
| **Set accel time** | 0x0031 | 500 | `02 06 00 31 01 F4 [CRC]` |
| **Set decel time** | 0x0032 | 500 | `02 06 00 32 01 F4 [CRC]` |
| **Set target speed** | 0x0033 | 25 | `02 06 00 33 00 19 [CRC]` |
| **Start (speed mode)** | 0x0037 | 0x0001 | `02 06 00 37 00 01 [CRC]` |
| **Stop (normal)** | 0x0038 | 0x0001 | `02 06 00 38 00 01 [CRC]` |
| **Stop (emergency)** | 0x0038 | 0x0002 | `02 06 00 38 00 02 [CRC]` |
| **Read status** | 0x0004 | N/A | `02 03 00 04 00 01 [CRC]` |
| **Read errors** | 0x0007 | N/A | `02 03 00 07 00 02 [CRC]` |

### 13.2 DIP Switch Quick Reference

```
         SW1   SW2   SW3   SW4   SW5   SW6
Pump 1:  OFF   ON    OFF   OFF   OFF   OFF    (Addr 2, no term)
Pump 2:  ON    ON    OFF   OFF   OFF   OFF    (Addr 3, no term)
Pump 3:  OFF   OFF   ON    OFF   OFF   OFF    (Addr 4, no term)

Note: Termination via 120Ω at ESP32 RS-485 adapter only
```

### 13.3 Recommended Default Settings

| Parameter | Value | Register | Notes |
|-----------|-------|----------|-------|
| **Baud Rate** | 9600 bps | SW5=OFF | ESPHome default |
| **Start Speed** | 5 rev/min | 0x0030 | Gentle ramp |
| **Accel Time** | 500 ms | 0x0031 | Smooth flow |
| **Decel Time** | 500 ms | 0x0032 | Prevent backflow |
| **Operating Current** | 1000 mA | 0x001E | Default is OK |
| **Holding Current %** | 50% | 0x0022 | Default is OK |
| **Enable Mode** | Software only | 0x0039 = 0x0001 | No external IO |

---

## Document Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-28 | 1.0 | Initial comprehensive reference document |
| 2025-10-28 | 1.1 | **Topology corrections:** Updated to hub/star topology with terminal block junction. Corrected termination strategy (ESP32 only, all pumps SW6=OFF). Added 1m main cable + 10cm stubs specification. Added future sensor integration notes. |

---

**Next Steps:**
1. Complete Phase 1 hardware setup (DIP switches all SW6=OFF, wiring with 1m main cable + 10cm stubs)
2. Begin Phase 2 ESPHome configuration in separate conversation
3. Update this document with actual calibration results after Phase 6

**Document Status:** v1.1 - Topology corrected to hub/star configuration with terminal block junction

**Related Documents:**
- `/docs/fert_pump_cal_v2.md` - Full calibration procedure
- `/docs/architecture.md` - System architecture
- `/docs/impl_roadmap.md` - Implementation status
- Technical Manual: `IRS42485总线型_enUS.pdf` (uploaded to separate conversation)
