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

### Sensors (82)

| Entity | Unit | Default |
|--------|------|---------|
| Battery Level | % | ✅ |
| Battery Level (precise) | % | off |
| State of Health (BMS Status) | % | ✅ |
| Charge Cycles | | ✅ |
| Time Remaining (discharge) | min | ✅ |
| Time to Full (charge) | min | ✅ |
| Battery Voltage | V | ✅ |
| Battery Current | A | ✅ |
| Battery Temperature | °C | ✅ |
| Remaining / Full / Design Capacity | mAh | ✅ / ✅ / off |
| Min / Max Cell Temperature | °C | off |
| Min / Max Cell Voltage | mV | off |
| Max Cell Voltage Difference | mV | off |
| Min / Max MOS Temperature | °C | off |
| Max / Min Charge Level (EMS) | % | ✅ |
| EMS Charge Voltage / Current | V / A | off |
| Fan Level | | off |
| AC Plug Connected | | off |
| System Charge/Discharge State | | off |
| Generator Start SOC | % | off |
| Generator Stop SOC | % | off |
| Extra Battery Power | W | off |
| Extra Batteries Connected | | off |
| **AC / Inverter** | | |
| AC Output Power | W | ✅ |
| AC Input Power | W | ✅ |
| AC Input Voltage / Current / Frequency | V / A / Hz | off |
| AC Output Voltage / Current / Frequency | V / A / Hz | off |
| AC Configured Frequency | Hz | off |
| AC Fast / Slow Charge Watts | W | off |
| Inverter Temperature | °C | off |
| Inverter DC Input Voltage / Current / Temperature | V / A / °C | off |
| **Solar / MPPT** | | |
| Solar Input Power | W | ✅ |
| Solar Input Voltage / Current | V / A | off |
| MPPT Output Power | W | off |
| MPPT Temperature | °C | off |
| DC 12V Output Power | W | ✅ |
| DC 12V Input Power | W | off |
| DC 12V Voltage / Current | V / A | off |
| DC 12V Temperature | °C | off |
| DC 12V Port State | | off |
| DC Output Temperature | °C | off |
| MPPT DC Converter Power | W | off |
| MPPT Beep State | | off |
| **USB / PD** | | |
| Total Input / Output Power | W | ✅ |
| USB-A 1 / 2 Power | W | ✅ |
| USB-A QC 1 / 2 Power | W | ✅ |
| USB-C 1 / 2 Power | W | ✅ |
| USB-C 1 / 2 Temperature | °C | off |
| Solar Charge Power | W | off |
| **Energy totals** | | |
| Cumulative AC / DC Charged | kWh | off |
| Cumulative Charged / Discharged Energy | Wh | off |
| Cumulative Charged / Discharged Capacity | mAh | off |
| **System** | | |
| Battery Protection SOC | % | off |
| WiFi Signal | dBm | off |
| **Battery lifetime** | | |
| State of Health (BMS Info) | % | off |
| Total Charge Cycles | | off |
| Round-Trip Efficiency | % | off |
| Self-Discharge Rate | %/day | off |
| Deep Discharge Count | | off |
| Internal Resistance | mΩ | off |

### Switches (11)

| Entity | Default | Notes |
|--------|---------|-------|
| AC Output | ✅ | Turn 230V output on/off |
| X-Boost | ✅ | Enable/disable X-Boost |
| USB Output | ✅ | USB-A + USB-C ports on/off |
| DC Output | ✅ | Car/Anderson port on/off |
| AC Charging | ✅ | Pause/resume mains charging — temporary, resets on replug |
| Solar Charge Priority | ✅ | Prioritise solar over AC |
| UPS Mode | ✅ | Enable/disable UPS pass-through |
| AC Auto-On | off | AC turns on automatically when mains is connected |
| AC Always-On | off | Keep AC on regardless of SOC |
| Bypass | off | Enable/disable bypass (doorsluizen) mode |
| Beep Sound | off | Enable/disable device beeps |

### Number Controls (12)

| Entity | Range | Default |
|--------|-------|---------|
| AC Charging Speed | 200–1500 W (step 100) | ✅ |
| Max Charge Level | 50–100% (step 5) | ✅ |
| Min Discharge Level | 0–30% (step 5) | ✅ |
| Generator Start SOC | 0–30% (step 5) | off |
| Generator Stop SOC | 50–100% (step 5) | off |
| Battery Protection SOC | 0–100% (step 5) | ✅ |
| Min SOC for AC Auto-On | 0–100% (step 5) | off |
| Device Standby Time | 0–1440 min | ✅ |
| AC Output Standby Time | 0–1440 min | ✅ |
| DC 12V Standby Time | 0–720 min | off |
| LCD Brightness | 0–100% (step 25) | ✅ |
| LCD Timeout | 0–300 s | off |

### Select Controls (1)

| Entity | Options | Default |
|--------|---------|---------|
| DC Charge Current | 4 A / 6 A / 8 A | ✅ |

> Entities marked **off** are disabled by default. Enable them in Settings → Devices & Services → your device → the entity.

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

### v0.2.14 – Fix: acOutCfg silent reject (outFreq) + MQTT improvements

**Root cause fixed: HA switch commands silently rejected by device**

- Fixed: `acOutCfg` command parameter `outFreq` changed from enum index `1` to Hz literal `50`
  — the device silently rejected `outFreq=1` without any error or reply; `outFreq=50` is required
- Fixed: command publish QoS changed from `QoS=1` to `QoS=0` (matches EcoFlow app behaviour)
- Fixed: command payload `version` changed from `"1.0"` to `"1.1"` (matches app)
- Fixed: command payload `id` changed from string to integer (matches app)
- Added: `set_reply` and `get_reply` MQTT topic subscriptions — device acknowledgements now visible in log
- Added: `latestQuotas` (Shape F) parsing in `coordinator.py` — full state dump on get_reply
- Added: periodic MQTT recertification every 10 minutes (`__init__.py`)

**State key corrections (verified via live MQTT trace, app toggle):**

- `ac_auto_on`: state key `pd.acAutoOnCfg` → `pd.watchIsConfig`
- `dc_output`: `cmd_module` `MODULE_MPPT` → `MODULE_PD`
- `beep_sound`: `cmd_module` `MODULE_PD` → `MODULE_MPPT`

**Logging improvements:**

- `api_client.py`: WARNING → INFO for setup messages; INFO/DEBUG privacy split (credentials never logged)
- `__init__.py`: `on_publish` ACK callback added; setup logs WARNING → INFO
- `switch.py`, `number.py`, `select.py`: INFO log per command (topic + full payload)

> **Note:** `acOutCfg` (AC Output switch) confirmed working after this fix.  
> `dcOutCfg` (DC Output) and `usb_output` commands still under investigation — broker ACK received but no device reply. To be resolved in v0.2.15.

### v0.2.13 – Fix: entity key alignment

- `switch` key `pv_charge_priority` → `solar_charge_priority` (matches entity ID)
- `switch` name `Bypass (Doorsluizen)` → `Bypass` (English, key `bypass` now consistent)
- `number` key `min_ac_soc` → `min_soc_for_ac_auto_on`
- `number` key `standby_time` → `device_standby_time`
- `number` key `ac_standby_time` → `ac_output_standby_time`
- `number` key `dc12v_standby_time` → `dc_12v_standby_time`

> **Note:** These are internal key renames only. Entity IDs in Home Assistant are unchanged — no cleanup required after upgrade.

### v0.2.12 – New entities + bugfixes + alignment

**New: Select platform**
- Added: `select.py` — new platform for list-based controls
- Added: `dc_charge_current` — DC charge current configurable: 4 A / 6 A / 8 A (`mppt.dcChgCurrent`)
- `__init__.py`: `PLATFORMS` extended with `Platform.SELECT`

**New: Bypass switch**
- Added: `switch.bypass` — enable/disable bypass mode (`pd.acAutoOutPause`, `inverted=True`)

**New: Generator SOC controls (number)**
- Added: `number.generator_start_soc` — generator start SOC 0–30% (`bms_emsStatus.minOpenOilEb`)
- Added: `number.generator_stop_soc` — generator stop SOC 50–100% (`bms_emsStatus.maxCloseOilEb`)

**New: Sensors (+9)**
- Added: `Battery Level (precise)` — float SOC (`bms_bmsStatus.f32ShowSoc`, 2 decimals, off)
- Added: `Max Cell Voltage Difference` — battery balance indicator in mV (`bms_bmsStatus.maxVolDiff`, off)
- Added: `AC Configured Frequency` — configured AC frequency in Hz (`inv.cfgAcOutFreq`, off)
- Added: `DC 12V Port State` — 12V port state sensor (`mppt.carState`, off)
- Added: `System Charge/Discharge State` — EMS charge/discharge state (`bms_emsStatus.sysChgDsgState`, off)
- Added: `Generator Start SOC` sensor (`bms_emsStatus.minOpenOilEb`, off)
- Added: `Generator Stop SOC` sensor (`bms_emsStatus.maxCloseOilEb`, off)
- Added: `MPPT Beep State` sensor (`mppt.beepState`, off)
- Added: `KEY_GEN_MIN_SOC`, `KEY_GEN_MAX_SOC`, `KEY_EMS_SYS_STATE`, `KEY_SOC_FLOAT`, `KEY_MAX_VOL_DIFF`, `KEY_DC12V_STATE`, `KEY_AC_CFG_FREQ`, `KEY_MPPT_BEEP` — new constants in `delta3_1500.py`

**Bugfix: switch state_keys (4× inv → mppt)**
- `KEY_AC_ENABLED`: `inv.cfgAcEnabled` → `mppt.cfgAcEnabled`
- `KEY_AC_XBOOST`: `inv.cfgAcXboost` → `mppt.cfgAcXboost`
- `KEY_AC_CHG_PAUSE`: `inv.chgPauseFlag` → `mppt.chgPauseFlag`
- `KEY_AC_STANDBY_TIME`: `inv.standbyMins` → `mppt.acStandbyMins`

*Reason: `inv.*` keys only appear in the infrequent full status dump (~every 5 min). The `mppt.*` equivalents are consistently present in the ~30s update cycle and provide reliable state.*

**Bugfix: switch command parameters**
- `ac_output`: `outFreq: 255, outVol: 255, xboost: 255` → `outFreq: 1, outVol: 230, xboost: 0`
- `x_boost`: `outFreq: 255, outVol: 255` → `outFreq: 1, outVol: 230`
- `ac_charging`: removed redundant `slowChgWatts: 255, fastChgWatts: 255` — only `chgPauseFlag` is sent

*Reason: value 255 is silently ignored by the device; correct EU values are outFreq=1 (50 Hz), outVol=230.*

**Bugfix: ac_auto_on / ac_always_on commands separated**
- `ac_auto_on`: `cmd_operate` was `acAutoOutConfig` → corrected to `acAutoOnCfg`
- Both switches were sending the same command; each now has its own `operateType` and payload

**Fix: delta3_1500.py alignment**
- All constants rewritten with uniform column alignment: `=` at column 20, `#` at column 55

**number.py**
- `standby_time` and `ac_standby_time` max: `720` → `1440` min (app supports 24h)
- Hardcoded `cmd_module` integers replaced by named constants `MODULE_PD`, `MODULE_BMS`, `MODULE_MPPT`

**Upgrade procedure:** HACS update → full HA restart required.

**Stale entities — remove manually (Settings → Entities → filter ecoflow):**
- `switch.ecoflow_delta_3_1500_x_boost_2` and `switch.ecoflow_delta_3_1500_beep_sound_2` (duplicate registrations from v0.2.11 → v0.2.12 upgrade)

---

### v0.2.11 – Bugfix: entity ID alignment + code cleanup

**Entity ID fixes (switch.py):**
- Fixed: `x_boost` — was `xboost` (entity ID mismatch with HA slug)
- Fixed: `beep_sound` — was `beep` (entity ID mismatch with HA slug)

**Entity ID fix (number.py):**
- Fixed: `dc12v_standby_time` — was `car_standby_time` (removed legacy "car" prefix, consistent with v0.2.9 DC 12V naming)

**Code cleanup:**
- Removed: unused import `KEY_DC12V_STATE` from `switch.py`
- Removed: unused import `KEY_AC_SLOW_CHG_W` from `number.py`
- Fixed: `_LOGGER.warning` → `_LOGGER.debug` for switch and number MQTT commands (was causing log spam in production)

**Dashboard fix:**
- Fixed: `sensor.ecoflow_delta_3_1500_state_of_health` → `state_of_health_bms_status` in `dashboard_ecoflow_v1.0.yaml`

**README fix:**
- Fixed: sensor table entry "Solar Charge Power (PD)" → "Solar Charge Power" (name changed in v0.2.9)

**Upgrade note — manual HA cleanup required:**
After upgrading, remove these stale entity registrations in HA (Settings → Devices & Services → Entities → filter on ecoflow → delete):
- `switch.ecoflow_delta_3_1500_ac_charging_230v` (→ now `ac_charging`)
- `switch.ecoflow_delta_3_1500_ac_auto_on_on_plug_in` (→ now `ac_auto_on`)
- `switch.ecoflow_delta_3_1500_solar_charge_priority` (→ now `pv_charge_priority`)
- `number.ecoflow_delta_3_1500_min_soc_for_ac_auto_on` (→ now `min_ac_soc`)
- `number.ecoflow_delta_3_1500_car_port_standby_time` (→ now `dc12v_standby_time`)
- `sensor.ecoflow_delta_3_1500_solar_charge_power_pd` (→ now `solar_charge_power`)
- `sensor.ecoflow_delta_3_1500_battery_health` (→ now `state_of_health_bms_info`)

### v0.2.10 – Merge: v0.2.9 base + v0.2.8 extras

**Merged from v0.2.8:**
- Added: `RESTART_WARNING.md` — guidance on disabling rate-limited integrations before repeated HA restarts
- Added: `examples/ecoflow_optimal_charging_v1.3.yaml` — smart AC charging automation based on PV surplus (entity IDs updated to v0.2.9 naming)
- Added: `examples/dashboard_ecoflow_v1.0.yaml` — alternative compact dashboard (entity IDs updated to v0.2.9 naming, 33 corrections)
- Added: `examples/test_credentials.py` — EcoFlow API credential diagnostic tool

**Fixes:**
- Fixed: `coordinator.py` MQTT data log level set back to `DEBUG` (was accidentally set to `WARNING` in v0.2.9)

### v0.2.9 – Refactor: full naming overhaul + AC charging speed fix + USB switch fix

**Fixes:**
- Fixed: AC Charging Speed slider now uses `mppt.cfgChgWatts` as `state_key` — shows 200W correctly even when AC cable is unplugged
- Fixed: AC charging command now sends `slowChgWatts` + `fastChgWatts` (was: `chgWatts` — ignored by device)
- Fixed: USB Output switch now uses `MODULE_PD` (moduleType 1) — was MODULE_MPPT (5), device did not respond

**Switch renames:**
- `dc_output` → `usb_output` / "USB Output" (`pd.dcOutState`) — USB-A + USB-C ports
- `dc24v_output` → `dc_output` / "DC Output" (`mppt.dc24vState`) — 12V car port + Anderson connectors
- `AC Charging 230V` → `AC Charging`

**Sensor renames:**
- Car Port Output Power → DC 12V Output Power
- Car Charger Input Power → DC 12V Input Power
- Car Port Temperature → DC 12V Temperature
- DC-DC 12V Power → MPPT DC Converter Power
- DC 24V Temperature → DC Output Temperature
- AC Input Power (Mains) → AC Input Power
- AC Slow/Fast Charge Limit → AC Slow/Fast Charge Watts
- Solar Charge Power (PD) → Solar Charge Power
- DC Input Current/Voltage/Temperature → Inverter DC Input Current/Voltage/Temperature
- Battery Health (BMS) → State of Health (BMS Status)
- Battery Health → State of Health (BMS Info)
- Removed: Wireless Charging Power (not present on Delta 3 1500)

**Number renames:**
- Car Port Standby Time → DC 12V Standby Time
- Standby Time → Device Standby Time
- AC Standby Time → AC Output Standby Time

**Code refactor:**
- All `KEY_CAR_*` constants → `KEY_DC12V_*`
- `KEY_DC_OUT_STATE` → `KEY_USB_OUT_STATE` (`pd.dcOutState`)
- `KEY_DC24V_STATE` → `KEY_DC_OUT_STATE` (`mppt.dc24vState`)
- `KEY_DC24V_TEMP` → `KEY_DC_OUT_TEMP`
- Added: `KEY_MPPT_CFG_CHG_W` = `mppt.cfgChgWatts`

### v0.2.8 – Bugfix: AC Charging Speed slider NameError
- Fixed: `NameError: KEY_AC_IN_W` — import statement corrected in `number.py`

### v0.2.7 – Added: AC Charging Speed slider
- Added: `number.ecoflow_delta_3_1500_ac_charging_speed` — slider 200–1500W (step 100W) to control AC charging limit

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

### v0.0.21–v0.1.3
- Fixed: Time to Full key corrected; coordinator MQTT debug logging added (v0.0.21)
- Added 65+ sensors, 9 switches, 9 number controls; full MQTT key coverage for Delta 3 1500; multiple command payload fixes (v0.1.0)
- Fixed: "Time Remaining" / "Time to Full" unavailable after HA restart (v0.1.1)
- Fixed: 85+ entities enabled by default; added `fallback_key` support for resilient key resolution (v0.1.2)
- Fixed: MQTT keepalive 120s, reconnect max 60s, QoS 1 subscribe, log spam reduced to DEBUG (v0.1.3)

### v0.0.11–v0.0.20
- Added App Login mode as alternative to Developer API (v0.0.11)
- Fixed MQTT ClientID format to `ANDROID_{8digits}_{userId_decimal}`; removed `Host` header (v0.0.16)
- Fixed App Login password encoding: Base64 confirmed via mmiller7/ecoflow-withoutflow (v0.0.18)
- Added Auto-detect connection mode based on serial number prefix; added 12 UI translations (v0.0.20)

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
