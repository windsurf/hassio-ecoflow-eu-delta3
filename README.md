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
| Battery Health | % | ✅ |
| Charge Cycles | | ✅ |
| Time Remaining (discharge) | min | ✅ |
| Time to Full (charge) | min | ✅ |
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
| AC Output Power | W | ✅ |
| AC Input Power (Mains) | W | ✅ |
| AC Input Voltage / Current / Frequency | V / A / Hz | off |
| AC Output Voltage / Current / Frequency | V / A / Hz | off |
| AC Fast / Slow Charge Limit | W | off |
| Inverter Temperature | °C | off |
| DC Input Voltage / Current / Temperature | V / A / °C | off |
| **Solar / MPPT** | | |
| Solar Input Power | W | ✅ |
| Solar Input Voltage / Current | V / A | off |
| MPPT Output Power | W | off |
| MPPT Temperature | °C | off |
| Car Port Output Power | W | ✅ |
| Car Charger Input Power | W | off |
| Car Port Temperature | °C | off |
| DC 24V Temperature | °C | off |
| DC-DC 12V Power | W | off |
| **USB / PD** | | |
| Total Input / Output Power | W | ✅ |
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
| Total Charge Cycles | | ✅ |
| Round-Trip Efficiency | % | off |
| Self-Discharge Rate | %/day | off |
| Deep Discharge Count | | off |
| Internal Resistance | mΩ | off |

### Switches (9)

| Entity | Default | Notes |
|--------|---------|-------|
| AC Output | ✅ | Turn 230V output on/off |
| X-Boost | ✅ | Enable/disable X-Boost |
| DC Output | ✅ | Car/DC port on/off |
| AC Charging (230V) | ✅ | **Pause/resume mains charging** — temporary, resets on replug |
| Solar Charge Priority | ✅ | Prioritise solar over AC |
| UPS Mode | ✅ | Enable/disable UPS pass-through |
| AC Auto-On (on plug-in) | off | AC turns on when mains is connected |
| AC Always-On | off | Keep AC on even at low SOC |
| Beep Sound | off | Enable/disable device beeps |

### Number Controls (9)

| Entity | Range | Default |
|--------|-------|---------|
| AC Charging Speed | 200–1500 W (step 100) | ✅ |
| Max Charge Level | 50–100% (step 5) | ✅ |
| Min Discharge Level | 0–30% (step 5) | ✅ |
| Battery Protection SOC | 0–100% (step 5) | ✅ |
| Standby Time | 0–720 min | ✅ |
| AC Standby Time | 0–720 min | ✅ |
| Car Port Standby Time | 0–720 min | off |
| LCD Brightness | 0–100% (step 25) | ✅ |
| LCD Timeout | 0–300 s | off |
| Min SOC for AC Auto-On | 0–100% (step 5) | off |

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

`test_credentials.py` in the repository root lets you verify credentials from the command line:

```bash
pip install requests
python3 test_credentials.py
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

### v0.1.3
- Fixed: MQTT connection dropping over time — keepalive increased from 60s to 120s, reconnect max from 30s to 60s
- Fixed: MQTT subscribe now uses QoS 1 for more reliable message delivery
- Fixed: Log spam reduced — MQTT messages now logged at DEBUG level instead of WARNING


### v0.1.2
- **85+ entities enabled by default** — removed unnecessary `entity_registry_enabled_default=False` from most sensors, all switches and all number controls
- Fixed: "Time Remaining" and "Time to Full" showing unavailable — added `pd.remainTime` as fallback key when EMS keys are absent (device only sends them while actively charging/discharging)
- Added `fallback_key` support in sensor entity for resilient key resolution

### v0.1.1
- Fixed: "Time Remaining" and "Time to Full" sensors showing unavailable after HA restart

### v0.1.0
- **65+ sensors** — complete coverage of all MQTT keys observed on Delta 3 1500
- **9 switches** — added Solar Charge Priority, UPS Mode, AC Auto-On, AC Always-On, DC 24V Output, Beep
- **9 number controls** — added Battery Protection SOC, Car Port Standby, LCD Timeout, Min SOC for AC Auto-On
- **AC Charging Speed** slider: correct 200–1500 W range for Delta 3 1500 (Delta 2 is max 1200 W)
- Fixed: `tls_set()` blocking call moved to executor thread (removes HA event loop warnings)
- Fixed: `rest_quota_unavailable` attribute missing on `EcoFlowPrivateAPI` (removed setup error)
- Fixed: `moduleType` now correct per command (was always `0`)
- Fixed: `acOutCfg` params use `255` for unchanged fields (was `0`, risked resetting voltage/frequency)
- Fixed: AC Charging pause now sends `slowChgWatts/fastChgWatts` instead of deprecated `chgWatts`
- Added: `bms_bmsInfo` lifetime statistics sensors (SOH, cumulative energy, internal resistance, etc.)
- Added: energy totals with correct scaling (kWh ×0.001, Wh raw)
- Added: voltage/current sensors with correct mV→V and mA→A scaling

### v0.0.21
- Fixed: Time to Full using correct key `bms_emsStatus.chgRemainTime` (was `bms_bmsStatus.chgTime`)
- Added: coordinator logs all MQTT keys at WARNING level for debugging

### v0.0.20
- Added Auto-detect connection mode based on serial number prefix
- Added 12 UI translations: NL, DE, FR, ES, IT, PL, PT, SV, DA, FI, CS, HU
- Fixed: `KeyError` on setup when using App Login

### v0.0.18
- Fixed App Login password encoding: **Base64** (confirmed from mmiller7/ecoflow-withoutflow)

### v0.0.16
- Removed `Host` header from requests session
- Fixed MQTT ClientID format to `ANDROID_{8digits}_{userId_decimal}`

### v0.0.11
- Added App Login mode as alternative to Developer API

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
