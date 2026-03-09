# EcoFlow Cloud – Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/windsurf/hassio-ecoflow-eu-delta3.svg)](https://github.com/windsurf/hassio-ecoflow-eu-delta3/releases)
[![Validate](https://github.com/windsurf/hassio-ecoflow-eu-delta3/actions/workflows/validate.yml/badge.svg)](https://github.com/windsurf/hassio-ecoflow-eu-delta3/actions/workflows/validate.yml)

> **Disclaimer:** This software is not affiliated with or endorsed by EcoFlow in any way. It is provided "as-is" without warranty or support, for the educational use of developers and enthusiasts. Use at your own risk.

Real-time monitoring and control of EcoFlow power stations via MQTT. Supports the **EcoFlow Developer API** (Access Key + Secret Key) and **App Login** (email + password) — the latter is required for Delta 3 and other newer devices not supported by the official Open API.

> **Actively tested with:** EcoFlow Delta 3 1500 (`D361` series, App Login mode)

---

## Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=windsurf&repository=hassio-ecoflow-eu-delta3&category=integration)

1. Click the button above **or** go to HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/windsurf/hassio-ecoflow-eu-delta3` — category: **Integration**
3. Search for **EcoFlow Cloud** and click **Download**
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration → EcoFlow Cloud**

## Manual Installation

1. Download the [latest release](https://github.com/windsurf/hassio-ecoflow-eu-delta3/releases/latest)
2. Extract and copy `custom_components/ecoflow_cloud/` to your HA `config/custom_components/` directory
3. Restart Home Assistant

---

## Getting Credentials

### Option A — App Login *(recommended for Delta 3 and newer devices)*
Use your regular EcoFlow app email and password. No extra setup needed.

### Option B — Developer API
1. Go to [developer-eu.ecoflow.com](https://developer-eu.ecoflow.com/) and sign in
2. Click **Become a Developer** and wait for the approval email
3. Go to **Security** and create an Access Key + Secret Key

---

## Setup

**Step 1:** Enter your device serial number and choose a connection method.
Select **Auto-detect** (recommended) — Delta 3, newer PowerStream and other recent devices will use App Login automatically; older devices use the Developer API.

**Step 2:** Enter credentials for the chosen method.

**Step 3:** Automatic connection test — confirms login and shows which devices are on your account.

After setup, use the **gear icon** on the integration card to change credentials or switch API mode.

---

## Supported Entities

### Sensors (65+)

| Entity | Unit | Default |
|--------|------|---------|
| Battery Level | % | ✅ |
| State of Health | % | ✅ |
| Cycles | | ✅ |
| Remaining Time | min | ✅ |
| Charge Remaining Time | min | ✅ |
| Battery Voltage | V | ✅ |
| Battery Current | A | ✅ |
| Battery Temperature | °C | ✅ |
| Remaining / Full / Design Capacity | mAh | ✅ / ✅ / off |
| Min / Max Cell Temperature | °C | off |
| Min / Max Cell Voltage | mV | off |
| Min / Max MOS Temperature | °C | off |
| Max / Min Charge Level (EMS) | % | ✅ |
| EMS Charge Voltage / Current | V / A | off |
| Fan Level | | off |
| AC Plug Connected | | off |
| Extra Battery Power | W | off |
| Extra Batteries Connected | | off |
| **AC / Inverter** | | |
| AC Out Power | W | ✅ |
| AC In Power | W | ✅ |
| AC In Volts / Current / Frequency | V / A / Hz | off |
| AC Out Volts / Current / Frequency | V / A / Hz | off |
| AC Fast / Slow Charge Limit | W | off |
| Inverter Temperature | °C | off |
| DC Input Voltage / Current / Temperature | V / A / °C | off |
| **Solar / MPPT** | | |
| Solar In Power | W | ✅ |
| Solar In Voltage / Current | V / A | off |
| MPPT Output Power | W | off |
| MPPT Temperature | °C | off |
| DC (12V) Out Power | W | ✅ |
| Car Charger Input Power | W | off |
| DC (12V) Temperature | °C | off |
| DC (24V) Temperature | °C | off |
| DC-DC 12V Power | W | off |
| **USB / PD** | | |
| Total In / Out Power | W | ✅ |
| USB-A 1 / 2 Power | W | ✅ |
| USB-A QC 1 / 2 Power | W | ✅ |
| USB-C 1 / 2 Power | W | ✅ |
| USB-C 1 / 2 Temperature | °C | off |
| Wireless Charging Power | W | off |
| Solar Charge Power (PD) | W | off |
| **Energy totals** | | |
| Cumulative AC / DC Charged | kWh | off |
| Cumulative Charged / Discharged Energy | Wh | off |
| Cumulative Charged / Discharged Capacity | mAh | off |
| **System** | | |
| Battery Protection SOC | % | off |
| WiFi Signal | dBm | off |
| **Battery lifetime** | | |
| State of Health (lifetime) | % | ✅ |
| Round-Trip Efficiency | % | off |
| Self-Discharge Rate | %/day | off |
| Deep Discharge Count | | off |
| Internal Resistance | mΩ | off |

### Switches (10)

| Entity | Default | Notes |
|--------|---------|-------|
| AC Enabled | ✅ | Turn 230V output on/off |
| X-Boost | ✅ | Enable/disable X-Boost |
| DC (12V) Enabled | ✅ | 12V car port on/off |
| DC (24V) Enabled | off | 24V DC port on/off |
| AC Charging (230V) | ✅ | **Pause/resume mains charging** — temporary, resets on replug |
| Prio Solar Charging | ✅ | Prioritise solar over AC |
| UPS Mode | ✅ | Enable/disable UPS pass-through |
| AC Auto On | off | AC turns on when mains is connected |
| AC Always On | off | Keep AC on even at low SOC |
| Beeper | off | Enable/disable device beeps |

### Number Controls (10)

| Entity | Range | Default |
|--------|-------|---------|
| AC Charging Power | 200–1500 W (step 100) | ✅ |
| Max Charge Level | 50–100% (step 5) | ✅ |
| Min Discharge Level | 0–30% (step 5) | ✅ |
| Battery Protection SOC | 0–100% (step 5) | ✅ |
| Unit Timeout | 0–720 min | ✅ |
| AC Timeout | 0–720 min | ✅ |
| DC (12V) Timeout | 0–720 min | off |
| Screen Brightness | 0–100% (step 25) | ✅ |
| Screen Timeout | 0–300 s | off |
| Min SOC for AC Auto On | 0–100% (step 5) | off |

> Entities marked **off** are disabled by default. Enable them in Settings → Devices & Services → your device → the entity.

---

## How It Works

```
EcoFlow Cloud
 |
 +-- REST API
 |   +-- /auth/login                  -> token + userId  (App Login)
 |   +-- /iot-auth/app/certification  -> MQTT credentials (App Login)
 |   +-- /iot-open/sign/certification -> MQTT credentials (Developer API)
 |   +-- /iot-open/sign/device/list   -> verify SN during setup
 |
 +-- MQTT TLS :8883  mqtt-e.ecoflow.com
     App Login  subscribe: /app/device/property/{sn}
                set:       /app/{userId}/{sn}/thing/property/set
     Developer  subscribe: /open/{account}/{sn}/quota
                set:       /open/{account}/{sn}/set
```

MQTT push is the primary data source. REST errors (1006, 8521) are non-fatal — the integration continues with MQTT-only mode.

---

## Diagnostic Tool

`examples/test_credentials.py` lets you verify credentials from the command line:

```bash
pip install requests
python3 examples/test_credentials.py
```

---

## Debug Logging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.ecoflow_cloud: debug
```

---

## Changelog

### v0.2.8 – Entity naming aligned with community standard
- Changed: sensor names — `AC Out Power` / `AC In Power` (was Input/Output), `State of Health` (was Battery Health), `Remaining Time` / `Charge Remaining Time` (was Time Remaining / Time to Full), `Solar In Power/Voltage/Current`, `Total In/Out Power`, `DC (12V) Out Power` / `DC (12V) Temperature` (was Car Port), `DC (24V) Enabled` / `DC (24V) Temperature` (was DC 24V)
- Changed: switch names — `AC Enabled`, `DC (12V) Enabled`, `Beeper`, `Prio Solar Charging`, `AC Always On`, `AC Auto On`
- Changed: number names — `AC Charging Power`, `Screen Brightness`, `Screen Timeout`, `Unit Timeout`, `AC Timeout`, `DC (12V) Timeout`
- Changed: dashboard fully translated to English
- Fixed: GitHub token no longer hardcoded in push script — use `$env:GITHUB_TOKEN`
- Note: only `ac_charging` → `ac_charging_230v` changes the entity ID; all other changes are display names only

### v0.2.7 – Bugfix: ac_charging_speed read SOC% instead of watts
- Fixed: `ac_charging_speed` (now `AC Charging Power`) was reading `bms_emsStatus.chgRemainTime` (SOC%) instead of `inv.SlowChgWatts` — corrected `state_key` to `KEY_AC_SLOW_CHG_W`
- Fixed: switch key `ac_charging` renamed to `ac_charging_230v` to match entity ID used in automations
- Changed: MQTT data log level lowered from WARNING to DEBUG to reduce log spam

### v0.2.6 – Added example dashboard
- Added: `examples/dashboard_delta3_1500.yaml` — complete HA dashboard covering all entities (battery, AC, solar, DC, USB, settings, BMS detail, statistics)

### v0.2.5 – Bugfix: 6 sensor names mismatched with HA entity registry
- Fixed: dashboard YAML corrected to use the descriptive entity IDs generated by the integration — `ac_input_power_mains`, `solar_input_voltage`, `solar_input_current`, `car_port_output_power`, `usb_a_qc_1_power`, `usb_a_qc_2_power`

### v0.2.4 – Bugfix: coordinator crash on bms_kitInfo.watts array
- Fixed: all sensors freezing when device sends `bms_kitInfo.watts` as a JSON array (triggered when AC charging starts) — non-scalar values (lists, dicts) are now filtered before updating coordinator state

### v0.2.3 – Bugfix: force update after HACS install
- Fixed: HA did not prompt for restart after HACS update when version number was unchanged — bumped version so HACS correctly detects the update and requests a restart

### v0.2.2 – Bugfix: duplicate sensor IDs
- Fixed: 7 sensors ignored by Home Assistant due to duplicate unique IDs — BMS/EMS keys in `delta3_1500.py` were incorrectly mapped to MPPT/INV keys already used by other sensors; all now point to correct `bms_bmsStatus.*` / `bms_emsStatus.*` keys (confirmed present in live MQTT dumps)

### v0.2.1 – Bugfix: sensors freezing after ~1 minute
- Fixed: all sensors freezing after ~1 minute — coordinator crashed when device sent `bms_kitInfo` as a JSON array; non-scalar MQTT values are now filtered before merging into coordinator data

### v0.2.0 – Entities cleaned up & push script improved
- Removed: `brands/icon.png` (HA has built-in EcoFlow icon via brands.home-assistant.io)
- Changed: 35 of 75 sensors disabled by default (never or rarely receive data)
- Changed: Push script now automatically removes files from GitHub that no longer exist locally

### v0.1.0–v0.1.3
- First stable release: 65+ sensors, 9 switches, 9 number controls — complete Delta 3 1500 coverage
- MQTT reliability fixes: keepalive, QoS 1, reduced log spam
- 85+ entities enabled by default; fallback key support for Time Remaining / Time to Full sensors
- Various command payload and scaling fixes (tls_set, moduleType, acOutCfg, chgWatts)

### v0.0.11–v0.0.21
- Early iterations: App Login mode, MQTT ClientID fix, Base64 password encoding, auto-detect connection mode, 12 UI translations (NL/DE/FR/ES/IT/PL/PT/SV/DA/FI/CS/HU), various key and scaling fixes

### v0.0.1–v0.0.10
- Initial versions: entity availability, payload parsing, quota/get, signing algorithm

---

## Inspiration & Acknowledgements

| Resource | Used for |
|----------|----------|
| [EcoFlow Developer Portal](https://developer-eu.ecoflow.com/us/document/introduction) | Official Open API docs |
| [mmiller7/ecoflow-withoutflow](https://github.com/mmiller7/ecoflow-withoutflow) | App Login reverse-engineering, Base64 password |
| [foxthefox/ioBroker.ecoflow-mqtt](https://github.com/foxthefox/ioBroker.ecoflow-mqtt) | Device key reference, set-command payloads |
| [varakh/go-ecoflow](https://pkg.go.dev/git.myservermanager.com/varakh/go-ecoflow) | Command payload reference |
| [berezhinskiy/ecoflow_exporter](https://github.com/berezhinskiy/ecoflow_exporter) | MQTT topic structure, payload keys |
| [tolwi/hassio-ecoflow-cloud](https://github.com/tolwi/hassio-ecoflow-cloud) | HA integration architecture inspiration |
| [snell-evan-itt/hassio-ecoflow-cloud-US](https://github.com/snell-evan-itt/hassio-ecoflow-cloud-US) | Extended device support patterns |
| [STROMDAO MQTT Credentials Tool](https://energychain.github.io/site_ecoflow_mqtt_credentials/) | Credential extraction reference |

---

## Disclaimer

This software is **not affiliated with or endorsed by EcoFlow** in any way. The EcoFlow name, logo, and product names are trademarks of EcoFlow Inc.

This integration uses undocumented private APIs that EcoFlow may change at any time. Provided **"as-is"** without warranty. The authors accept no liability for any damage, loss of data, or service disruption.
