# EcoFlow Cloud – Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/windsurf/hassio-ecoflow-eu-delta3.svg)](https://github.com/windsurf/hassio-ecoflow-eu-delta3/releases)
[![Validate](https://github.com/windsurf/hassio-ecoflow-eu-delta3/actions/workflows/validate.yml/badge.svg)](https://github.com/windsurf/hassio-ecoflow-eu-delta3/actions/workflows/validate.yml)

> **Disclaimer:** This software is not affiliated with or endorsed by EcoFlow in any way. It is provided "as-is" without warranty or support, for the educational use of developers and enthusiasts. Use at your own risk.

Real-time monitoring and control of EcoFlow power stations via MQTT. Supports two connection modes:

- **App Login** (email + password) — MQTT telemetry + JSON SET control for all devices including Delta 3
- **Developer API** (Access Key + Secret Key) — REST API for device list and credentials (SET commands blocked for D361 series)

> **Actively tested with:** EcoFlow Delta 3 1500 (`D361` series, App Login + MQTT JSON SET)

---

## Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=windsurf&repository=hassio-ecoflow-eu-delta3&category=integration)

1. Click the button above **or** go to HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/windsurf/hassio-ecoflow-eu-delta3` — category: **Integration**
3. Search for **EcoFlow Cloud** and click **Download**
4. **Restart Home Assistant** (full restart required — not just reload)
5. Go to **Settings → Devices & Services → Add Integration → EcoFlow Cloud**

## Manual Installation

1. Download the [latest release](https://github.com/windsurf/hassio-ecoflow-eu-delta3/releases/latest)
2. Extract and copy `custom_components/ecoflow_cloud/` to your HA `config/custom_components/` directory
3. **Restart Home Assistant** (full restart — reload integration is not sufficient after code updates)

> **Important:** Always do a full HA restart after updating this integration. The `reload integration` shortcut does not clear Python bytecode cache (`.pyc`) and may run the old code silently.

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

**Step 3 (App Login only):** Optionally enter Developer API keys. For Delta 3 (D361) devices this has no effect on control — REST SET is blocked by EcoFlow for this series. Leave empty to skip.

**Step 4:** Automatic connection test — confirms login and shows which devices are on your account.

After setup, use the **gear icon** on the integration card to change credentials, add Developer API keys, or switch API mode.

### How Control Works (Delta 3)

Confirmed via live protocol analysis (v0.2.22–v0.2.24): Delta 3 uses **MQTT JSON SET** with `"from": "Android"` in the payload.

| Function | Channel | Notes |
|----------|---------|-------|
| Real-time sensor data | MQTT push | `/app/device/property/{sn}` — pushed every ~3s (pd) or ~3-5 min (mppt) |
| Switch/number control | MQTT JSON SET | `"from":"Android"` required |
| REST API SET | Blocked | EcoFlow blocks D361/D362/D381/R641/R651 (code=1006) |

**SET command payload:** `{id, version:"1.0", sn, moduleType, operateType, from:"Android", params:{...}}`

### D361-Specific Behaviour (confirmed via live tests)

| Feature | Behaviour |
|---------|-----------|
| AC Charging pause (`chgPauseFlag`) | Not supported — command received (beep) but has no effect. `mppt.chgPauseFlag` never in telemetry. |
| LCD Brightness | Not controllable via MQTT — `lcdCfg brighLevel` received (beep) but no visible effect |
| Screen Timeout (`lcdCfg delayOff`) | Works — do not send `brighLevel=255` alongside it; D361 writes 65535 literally |
| AC Standby (`standbyTime` mod5) | Works — operateType must be `standbyTime`, not `standby` |
| MPPT keys update frequency | Every 3–5 minutes (not real-time), periodic full upload |
| `mppt.chgPauseFlag` in telemetry | Never pushed — not a supported state key on D361 |
| `bms_emsStatus.sysChgDsgState` | Charge state indicator: 0=idle, 1=discharging, 2=charging |
| `pd.lcdOffSec = 65535` | Sentinel value for "Never" (not 0) |
| `pd.acAutoOutPause` | Always 0 on D361 -- never pushed via telemetry. Bypass state unavailable. SET command works (relay confirmed). |
| `mppt.cfgAcEnabled` | Updates 2s before `pd.acEnabled` and `inv.cfgAcEnabled` on AC Output toggle |

---

## Supported Entities

### Switches (13)

| Entity | Default | Notes |
|--------|---------|-------|
| AC Output | ✅ | Turn 230V output on/off |
| X-Boost | ✅ | Enable/disable X-Boost |
| USB Output | ✅ | USB-A + USB-C ports on/off |
| DC Output | ✅ | Car/Anderson port on/off |
| AC Charging | off | **Read-only** — D361 does not support chgPauseFlag via MQTT. State key `mppt.chgPauseFlag` never pushed. Disabled by default. |
| Solar Charge Priority | ✅ | Prioritise solar over AC |
| AC Auto-On | off | AC turns on automatically when mains connected |
| AC Always-On | off | Keep AC on regardless of SOC |
| UPS Mode | off | UPS mode — effect unconfirmed on D361, disabled by default |
| Backup Reserve | off | Enable/disable backup reserve mode |
| Output Memory | off | Remember output states after power loss — ACK only, no state feedback on D361 |
| Bypass | off | Enable/disable bypass mode — ACK only, no state feedback on D361 |
| Beep Sound | off | Enable/disable device beeps |

### Number Controls (9)

| Entity | Range | Default |
|--------|-------|---------|
| AC Charging Speed | 200–1500 W (step 100) | ✅ |
| Max Charge Level | 50–100% (step 5) | ✅ |
| Min Discharge Level | 0–30% (step 5) | ✅ |
| Generator Start SOC | 0–30% (step 5) | off |
| Generator Stop SOC | 50–100% (step 5) | off |
| Backup Reserve SOC | 5–100% (step 5) | off |
| Min SOC for AC Auto-On | 0–100% (step 5) | off |
| Screen Standby Time (read-only) | min | off |
| Overall Standby Time (read-only) | min | off |

> Note: Battery Protection SOC removed in v0.2.23 (duplicate of Min Discharge Level).

### Select Controls (5)

| Entity | Options | Default | operateType (confirmed) |
|--------|---------|---------|------------------------|
| DC Charge Current | 4 A / 6 A / 8 A | ✅ | `dcChgCfg` mod5 |
| Screen Timeout | Never / 10s / 30s / 1min / 5min / 30min | off | `lcdCfg` mod1 — `delayOff` only |
| Unit Standby Time | Never / 30min–24hr | off | `standbyTime` mod1 — `standbyMin` |
| AC Output Standby Time | Never / 30min–24hr | off | `standbyTime` mod5 — `standbyMins` |
| DC 12V Standby Time | Never / 30min–24hr | off | `carStandby` mod5 — `standbyMins` |

> Entities marked **off** are disabled by default. Enable them in Settings → Devices & Services → your device → the entity.

### Sensors (221)

See [v0.2.23 README](https://github.com/windsurf/hassio-ecoflow-eu-delta3/releases/tag/v0.2.23) for full sensor list. No sensor changes in v0.2.24.

---

## How It Works

```
EcoFlow Cloud (App Login mode — recommended for Delta 3)
 |
 +-- REST API (App Login — Email + Password)
 |   +-- /auth/login                    -> token + userId
 |   +-- /iot-auth/app/certification    -> MQTT credentials (renewed every 10 min)
 |
 +-- MQTT TLS :8883  mqtt-e.ecoflow.com
     subscribe: /app/device/property/{sn}                  (telemetry push)
     set:       /app/{userId}/{sn}/thing/property/set       (JSON SET commands)
     set_reply: /app/{userId}/{sn}/thing/property/set_reply (command ACK)
     get:       /app/{userId}/{sn}/thing/property/get       (GET-ALL keepalive every 20s)

SET command payload:
  {"id":<seq>, "version":"1.0", "sn":"<SN>", "moduleType":<n>,
   "operateType":"<cmd>", "from":"Android", "params":{...}}

REST API: used only for MQTT credential retrieval. SET commands blocked for D361 series.
```

MQTT push is the primary data source. Telemetry frequency varies by module:
- `pd.*` keys: every ~3 seconds
- `mppt.*` keys: every ~3-5 minutes (full upload), ~2 minutes (incremental)
- `bms_emsStatus.*` / `bms_bmsStatus.*`: every ~3 seconds

MQTT credentials are renewed every 10 minutes (periodic recertification) — this is normal behaviour and does not interrupt telemetry.

---

## Diagnostic Tools

Test scripts in the `examples/` directory:

| Script | Purpose |
|--------|---------|
| `test_credentials.py` / `.ps1` | Developer API credentials against EU/US/Global servers |
| `test_developer_api.py` / `.ps1` | Signing validation, device list, MQTT credentials, quota GET + SET |

```bash
# Python
pip install requests
python3 examples/test_developer_api.py

# PowerShell
PowerShell -ExecutionPolicy Bypass -File examples/test_developer_api.ps1
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

### v0.3.1 -- Gen 1 full control + PowerStream, Glacier, Wave 2

**Gen 1 devices now have switches, numbers, and selects:**
- Delta Pro (DAEB) -- 6 switches, 6 numbers, 4 selects
- Delta Max (DCAB) -- 7 switches, 5 numbers
- Delta Mini (DAAZ) -- 4 switches, 3 numbers, 4 selects
- River Max (R601) -- 5 switches, 1 number, 3 selects
- River Pro (R602) -- 7 switches, 1 number, 3 selects
- River Mini (R501) -- 2 switches, 1 number

Gen 1 TCP commands (moduleType=0, operateType=TCP, params.id) work through the existing _publish() infrastructure -- no protocol changes needed.

**New device profiles:**
- PowerStream / 600W / 800W (HW51, HW52, BKW) -- 21 sensors + 1 switch + 4 numbers + 1 select (full control, protobuf binary protocol)
- Glacier (BX11) -- 21 sensors + 3 switches + 3 numbers (full control, JSON protocol)
- Wave 2 (KT21) -- 13 sensors + 1 number + 4 selects (full control, JSON protocol)

Glacier and Wave 2 use JSON protocol (moduleType=1) -- same infrastructure as Gen 1/Gen 2.
PowerStream uses protobuf binary protocol with pure-Python encoder -- no protobuf library dependency.

**Infrastructure:**
- Added `proto_builder_sn` to switch/number/select descriptions for protobuf binary commands (PowerStream)
- Added `cmd_params_coord_fn` to EcoFlowNumberDescription for commands needing sibling entity state (Glacier temp sync)
- Dispatch priority in all _publish(): REST API > Proto binary > JSON MQTT
- 6 PowerStream protobuf command builders in proto_codec.py

15 devices total. All 15 with full control.

### v0.3.0 – Multi-device architecture + 12 device profiles

**Architecture: multi-device support**
- Added device registry (`devices/registry.py`) with SN prefix to model mapping for 27+ EcoFlow devices
- Device model is now auto-detected from serial number at setup time
- Entity descriptions are dispatched per device model -- platform files (sensor.py, switch.py, number.py, select.py) load the correct description tuple based on detected device
- DeviceInfo (model name in HA UI) is now dynamic instead of hardcoded
- All entity unique_ids unchanged -- zero breaking changes for existing Delta 3 1500 users
- Integration name updated from "EcoFlow Cloud (EU Delta 3)" to "EcoFlow Cloud"

**Gen 2 devices -- full control (sensors + switches + numbers + selects):**
- Delta 3 1500 (D361) -- 185 sensors, 13 switches, 9 numbers, 5 selects
- Delta 2 (R331) -- 46 sensors, 8 switches, 6 numbers, 5 selects
- Delta 2 Max (R351) -- 68 sensors, 7 switches, 6 numbers, 3 selects (dual solar, dual slave)
- River 2 (R621) -- 32 sensors, 5 switches, 4 numbers, 5 selects
- River 2 Max (R631) -- 32 sensors, 5 switches, 4 numbers, 5 selects
- River 2 Pro (R622) -- 30 sensors, 3 switches, 3 numbers, 5 selects

**Gen 1 devices -- read-only sensors (TCP command protocol not yet supported):**
- Delta Pro (DAEB) -- ~57 sensors incl. dual slave + energy counters
- Delta Max (DCAB) -- ~56 sensors incl. dual slave + energy counters
- Delta Mini (DAAZ) -- ~40 sensors incl. energy counters
- River Max (R601) -- ~38 sensors incl. slave + energy counters
- River Pro (R602) -- ~32 sensors incl. slave + energy counters
- River Mini (R501) -- ~17 sensors incl. energy counters

**Device detection (SN prefix mapping):**
- Delta series: D361, D362, D381, DGEA, DGEB, DAEB, R331, R351, DCAB, DAAZ
- River series: R641, R651, R621, R631, R622, R601, R602, R501
- PowerStream: HW51, HW52, BKW
- Smart Plug: SP10
- Climate: BX11, KT21

### v0.2.25 – Slave battery sensors + Bypass fix

**Added: Slave battery sensors (delta3_1500.py, sensor.py)**
- Added 35 sensors for the P361Z1H4PGBR0251 slave battery, confirmed present via live MQTT telemetry
- Primary sensors enabled by default: SOC, SoH, voltage, current, temperature, remaining capacity, input/output power, charge cycles
- Diagnostics disabled by default: cell temperatures, cell voltages, cumulative capacity/energy, internal resistance, round-trip efficiency, deep discharge count, error codes
- Keys follow bms_slave.* prefix, units/scale identical to main battery bms_bmsStatus.*
- bms_slave.diffSoc and bms_slave.cycSoh arrive as comma-decimal strings from device firmware

**Fixed: Bypass switch state (switch.py)**
- Removed inverted=True from bypass switch -- pd.acAutoOutPause is always 0 on D361, never pushed via telemetry
- Switch now shows OFF consistently (correct: bypass is inactive by default)
- SET command (bypassBan mod1) confirmed working -- pd.relaySwitchCnt increments on each toggle
- State feedback remains unavailable on D361; entity stays disabled by default

**Investigated: Beep Sound switch**
- Confirmed correct: mppt.beepState=1 means sound ON, switch shows ON
- If switch shows ON: device beep is actually enabled -- turn off in app or via HA

**MQTT telemetry analysis (this release)**
- Confirmed via live MQTT listener: pd.acAutoOutPause never changes (Bypass state unavailable)
- Confirmed: mppt.beepState is authoritative for beep state; pd.beepMode is static on D361
- Confirmed: all three keys update on AC Output toggle: mppt.cfgAcEnabled (first), then inv.cfgAcEnabled and pd.acEnabled (~2s later)
- bms_slave.* full telemetry confirmed: all primary keys arrive in latestQuotas and periodic push

### v0.2.24 – AC Standby fix + AC Charging read-only + UPS Mode + switch corrections

**Fixed: AC Standby Time operateType (select.py)**
- Fixed: AC Output Standby Time select sent `operateType="standby"` — device ignored it (4 hr never changed)
- Correct operateType is `"standbyTime"` mod5 with `standbyMins` — confirmed via live test on D361 1500
- Screen Timeout: removed `brighLevel=255` from `lcdCfg` command — D361 writes 65535 literally when sent as keep-current; only `delayOff` is now sent

**Fixed: AC Charging switch — made read-only (switch.py)**
- AC Charging switch now read-only: `cmd_params=None`, `cmd_operate=""`, disabled by default
- Root cause: confirmed via live test — `acChgCfg chgPauseFlag` command is received (beep) but has no effect on D361
- `mppt.chgPauseFlag` is never pushed in D361 telemetry and does not exist in the D361 protocol schema
- The switch was in an unknown/unavailable state permanently — now explicitly marked as not actionable
- Use `inv.inputWatts > 0` or `bms_emsStatus.sysChgDsgState == 2` to detect active charging

**Added: UPS Mode switch (switch.py)**
- Added `ups_mode` switch on `bms_emsStatus.openUpsFlag` — state key confirmed in D361 telemetry
- Command: mod2 `upsConfig` `{openUpsFlag: 1/0}` — effect on D361 unconfirmed, disabled by default

**Improved: Bypass and Output Memory comments (switch.py)**
- Both entities documented as "ACK only — no telemetry feedback on D361; state unknown"

**D361 protocol findings documented (this release)**
- `mppt.*` keys update every 3-5 minutes — not real-time; `pd.*` updates every ~3s
- `pd.lcdOffSec = 65535` is the "Never" sentinel (not 0)
- `bms_emsStatus.sysChgDsgState`: 0=idle, 1=discharging, 2=charging — reliable charge state indicator
- Full restart required after code update — `reload integration` does not clear `.pyc` cache


### v0.2.23 – Realtime telemetry fix + AC Charging Speed sync + entity corrections

**Critical fix: typeCode mapping in coordinator**
- Fixed: all telemetry sensors never updated in HA without opening the EcoFlow app
- Root cause: D361 sends telemetry pushes with short typeCode names (`pdStatus`, `mpptStatus`, `invStatus`) — coordinator was storing them as `pdStatus.*` instead of `pd.*`
- Added typeCode → module prefix mapping: `pdStatus→pd`, `mpptStatus→mppt`, `invStatus→inv`, `bmsStatus→bms_bmsStatus`, `emsStatus→bms_emsStatus`, `bmsInfo→bms_bmsInfo`

**AC Charging Speed (cfgChgWatts=255 sentinel)**
- Fixed: AC Charging Speed slider showed 255W in HA after every keepalive GET-ALL (every 20s)
- Root cause: device always echoes `cfgChgWatts=255` (sentinel meaning "keep current value") in `latestQuotas` reply
- Coordinator now filters 255 from quotaMap; real values still arrive via telemetry push

**AC Charging switch — chgWatts sentinel**
- Fixed: AC Charging switch sent `chgWatts=255` with every toggle, writing 255W as the actual charge speed
- Now sends only `chgPauseFlag` — device keeps current charge speed when chgWatts is omitted

**Entity corrections**
- Backup Reserve switch: `state_key` corrected to `pd.watchIsConfig` (was `pd.bpPowerSoc`)
- Battery Protection SOC: removed — duplicate of Min Discharge Level (same key + command)
- 4 standby/timeout sliders moved from number.py to select.py with human-readable options

**New entities (68 sensors + 4 selects)**
- Added 68 new sensors (all disabled by default): extended BMS, EMS, MPPT, PD, INV telemetry keys
- Added selects: Screen Timeout, Unit Standby Time, AC Output Standby Time, DC 12V Standby Time

### v0.2.22 – Major: MQTT JSON control working for Delta 3 (protocol analysis)

- Breakthrough: Delta 3 uses JSON MQTT SET with `"from": "Android"` — REST API returns code=1006 for D361
- Fixed all switch/number command parameters from protocol analysis
- Added Output Memory, Backup Reserve switch, Backup Reserve SOC, Connection Mode sensor
- REST SET auto-skipped for D361/D362/D381/R641/R651 by SN prefix

### v0.2.11–v0.2.21

- v0.2.21: Hybrid Mode — REST API SET via Developer API; HMAC signing corrected
- v0.2.20: manifest.json key order; brand/icon.png; GitHub Actions checkout@v5; enBeep dataLen=2
- v0.2.19: proto_codec.py pure-Python protobuf encoder for Delta 3 SET commands
- v0.2.17: moduleType ac_output→MPPT; command id overflow; client_id recertification; QoS 1
- v0.2.14: set_reply/get_reply subscriptions; periodic MQTT recertification
- v0.2.12: select.py platform; DC Charge Current; Bypass; Generator SOC; 9 new sensors

### v0.0.1–v0.2.10

- Full history available in previous release notes

---

## Inspiration & Acknowledgements

| Resource | Used for |
|----------|---------|
| [EcoFlow Developer Portal](https://developer-eu.ecoflow.com/us/document/introduction) | Official Open API docs |
| [mmiller7/ecoflow-withoutflow](https://github.com/mmiller7/ecoflow-withoutflow) | App Login protocol analysis, Base64 password |
| [foxthefox/ioBroker.ecoflow-mqtt](https://github.com/foxthefox/ioBroker.ecoflow-mqtt) | Device key reference, set-command payloads |
| [tolwi/hassio-ecoflow-cloud](https://github.com/tolwi/hassio-ecoflow-cloud) | HA integration architecture, Delta 3 proto schema |
| [EcoFlow Developer Docs — Delta 2](https://developer-eu.ecoflow.com/us/document/delta2) | MQTT command reference for D361 |
| [EcoFlow Developer Docs — Delta Pro 3](https://developer-eu.ecoflow.com/us/document/deltaPro3) | Delta 3 protocol schema reference |

---

## Disclaimer

This software is **not affiliated with or endorsed by EcoFlow** in any way. The EcoFlow name, logo, and product names are trademarks of EcoFlow Inc.

This integration uses undocumented private APIs that EcoFlow may change at any time. Provided **"as-is"** without warranty. The authors accept no liability for any damage, loss of data, or service disruption.
