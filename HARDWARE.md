## Hardware Overview

This document covers only the hardware for the antenna analyzer: components, wiring, pin mappings, setup, specifications, and troubleshooting.

---

## Components

- **ADS1115 16‑bit I2C ADC**: Measures magnitude and phase voltages from the RF bridge.
- **AD9850 DDS**: Generates the RF test signal across the desired frequency range.
- **AD8302 RF Detector**: Measures relative magnitude and phase between RF inputs; provides DC outputs for ADS1115.
- **SWR Bridge / Directional Coupler**: Samples forward and reflected power from the antenna port for SWR measurement.
- **Raspberry Pi (3B+/4B or newer)**: Hosts software, controls GPIO and I2C, renders UI.
- **Cables/Jumpers**: SDA, SCL, 3.3V, GND, and control lines to DDS.
- **Coaxial Cable**: RF interconnect between DDS, bridge/coupler, and DUT (antenna).

---

## Pin Connections

### ADS1115 (I2C ADC)

| ADS1115 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VDD         | 3.3V             | Power supply |
| GND         | GND              | Ground |
| SCL         | GPIO 3 (SCL)     | I2C clock |
| SDA         | GPIO 2 (SDA)     | I2C data |
| ADDR        | GND              | I2C address 0x48 |

Channels used in software:
- `P0` → Magnitude voltage (mag)
- `P1` → Phase voltage (phase)

### AD8302 (RF Magnitude/Phase Detector)

Power and I/O (typical module variant; verify your board silkscreen):

| AD8302 Pin | Connection | Description |
|------------|------------|-------------|
| VPOS       | 3.3V       | Power supply (3.0–5.5 V, prefer 3.3 V for Pi systems) |
| GND        | GND        | Ground |
| INPA       | RF sample A| From SWR bridge forward path (or reference) |
| INPB       | RF sample B| From SWR bridge reflected path (or test path) |
| VMAG       | ADS1115 P0 | DC output proportional to log amplitude ratio |
| VPHS       | ADS1115 P1 | DC output proportional to phase difference |
| ENBL (if present) | 3.3V | Tie high to enable |

Notes:
- Keep RF inputs within the detector’s input range; use appropriate attenuation if necessary.
- Route `VMAG` to ADS1115 `P0` and `VPHS` to ADS1115 `P1` as used by software.

### AD9850 (DDS)

| AD9850 Pin | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC        | 3.3V             | Power supply |
| GND        | GND              | Ground |
| W_CLK      | GPIO 12          | Word clock |
| FQ_UD      | GPIO 16          | Frequency update (latch) |
| DATA       | GPIO 20          | Serial data (LSB first) |
| RESET      | GPIO 21          | Reset |

Notes:
- The AD9850 reference clock is 125 MHz. Software sends a 40‑bit word (32‑bit FTW + 8‑bit control) LSB‑first using `W_CLK` and `DATA`, then toggles `FQ_UD` to latch.

---

## SWR Bridge / Directional Coupler

Purpose: Provide separate samples of forward and reflected power from the DUT (antenna) port. These samples are fed to the AD8302 inputs to derive magnitude and phase, enabling SWR estimation.

Typical connections:
- RF Source (from AD9850) → Bridge input
- Bridge output → DUT (antenna) via coax
- Forward sample → AD8302 `INPA`
- Reflected sample → AD8302 `INPB`

Guidelines:
- Use a 50 Ω system throughout. Ensure the bridge/coupler is rated for your frequency range.
- Keep RF paths short; use quality 50 Ω coax and connectors.
- Provide good shielding and grounding to reduce coupling and noise.

Optional: If using a simple resistive bridge, ensure proper scaling and buffering before AD8302 inputs to stay within its input limits.

---

## Wiring Checklist

1. Connect Pi 3.3V and GND to both ADS1115 and AD9850 modules.
2. Connect I2C lines: `SDA → GPIO 2`, `SCL → GPIO 3` (with pull‑ups, typically on module).
3. Connect DDS control lines: `W_CLK → GPIO 12`, `FQ_UD → GPIO 16`, `DATA → GPIO 20`, `RESET → GPIO 21`.
4. Wire the RF chain with coax: AD9850 → SWR bridge/coupler → DUT (antenna).
5. Connect bridge samples to AD8302 `INPA`/`INPB`.
6. Connect AD8302 `VMAG` → ADS1115 `P0`, `VPHS` → ADS1115 `P1`.
7. Keep wiring short, especially RF paths; ensure a solid ground reference.

---

## Setup (Raspberry Pi)

1. Enable I2C in `/boot/config.txt` (or raspi-config):
   - `i2c_arm=on`
   - `dtparam=i2c_arm=on`
2. Reboot the Pi after enabling I2C.
3. Verify I2C device presence:
   - `i2cdetect -y 1` → Expect `0x48` for ADS1115.
4. Install required Python packages (see `requirements_rpi.txt`).

---

## Hardware Specifications

### ADS1115

- Resolution: 16‑bit (65,536 codes)
- Input range (gain=1): ±4.096 V
- Data rate: up to 860 SPS
- Interface: I2C (address 0x48 with ADDR tied to GND)

Recommended runtime configuration (from software):
- Gain: `1` (±4.096 V)
- Data rate: `860` SPS

### AD9850

- Reference clock: 125 MHz
- Output range: ~1 Hz to ~40 MHz (practical)
- Programming: 32‑bit Frequency Tuning Word (FTW) + 8‑bit control, LSB‑first

### AD8302

- Supply: 3.0–5.5 V (use 3.3 V with Raspberry Pi systems)
- Outputs: `VMAG` (log amplitude ratio), `VPHS` (phase difference)
- Interface to ADC: Single‑ended DC voltages compatible with ADS1115

### Raspberry Pi

- Logic level: 3.3 V (match peripheral modules)
- Interfaces used: GPIO (bit‑bang to DDS), I2C (ADS1115)

---

## Verification & Tests

- I2C scan: `i2cdetect -y 1` should list `0x48`.
- Basic ADC test: run `python3 test_ads1115.py` to see voltage readings from `P0` and `P1`.
- Detailed ADC debug: run `python3 debug_ads1115.py` for step‑by‑step initialization and samples.
- RF path smoke test: drive AD9850 at a low frequency, verify AD8302 `VMAG`/`VPHS` vary when swapping bridge forward/reflected connections.

---

## Troubleshooting

- No devices on I2C bus: check SDA/SCL wiring, enable I2C, power, and pull‑ups.
- ADS1115 not found at `0x48`: confirm ADDR pin is tied to GND (or adjust address).
- No ADC readings: verify 3.3 V and ground; check channel wiring (`P0`/`P1`).
- DDS not outputting: confirm `RESET`, `W_CLK`, `FQ_UD`, `DATA` connections and 3.3 V logic.
- Excess noise/erratic values: shorten leads, improve grounding, shield RF path.
- AD8302 rails or no change: check input power level and ensure inputs are within detector specs; add attenuation if needed.
- Incorrect SWR indication: verify bridge orientation (forward vs reflected), and mapping to AD8302 `INPA`/`INPB`.

---

## Reference (Used by Software)

- ADS1115 channels: `P0` → magnitude, `P1` → phase.
- AD9850 control sequence: write 32‑bit FTW (LSB‑first), then 8‑bit control, toggle `FQ_UD` to apply.
- AD8302 outputs: `VMAG` → magnitude voltage, `VPHS` → phase voltage; both sampled by ADS1115.


