"""Device definition for EcoFlow Wave 3 (mobile air conditioner with battery).

The Wave 3 is the successor to the Wave 2 but uses a fundamentally different
protocol: protobuf cmdFunc=254 (same as Stream AC and Delta 3 Plus/Max), not
the Gen 2 moduleType JSON used by Wave 2.

Wave 3 features (mobile AC with optional 1024Wh LFP battery):
  - Inverter-based cooling/heating with variable speed
  - PV input + DC plug-in port + AC charging
  - Pet care warning (over-temperature notification)
  - Mood lighting and condensate drainage management
  - 4 USB-C/QC ports for device charging

PROTOCOL NOTES:
  - Telemetry: cmdFunc=254, cmdId=21 (DisplayPropertyUpload) — 89 proto fields
  - Keepalive: foxthefox 'latestQuotas' minimal setMessage (same as Stream AC)
  - SET commands: foxthefox source has //cmd markers on a few fields
    (drainageMode, moodLightMode, enPetCare, tempAmbient, humiAmbient,
    userTempUnit, tempPetCareWarning) but NO ConfigWrite implementation.
    Wave 3 is read-only in v0.3.10 — switches/numbers will follow when
    community provides a confirmed wire capture.

SN PREFIX: foxthefox does not document a confirmed SN prefix for Wave 3.
Placeholder "KT3" used analogous to Wave 2 (KT21). Update in registry.py
when a Wave 3 owner reports their actual SN prefix via GitHub issue.

Source: foxthefox/ioBroker.ecoflow-mqtt (ef_wave3_data.js)
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# Protobuf field numbers → coordinator key names
# Source: foxthefox DisplayPropertyUpload proto definition (cmdFunc=254, cmdId=21)
# ══════════════════════════════════════════════════════════════════════════════

DISPLAY_FIELDS: dict[int, str] = {
    # ── Power summary (always-on) ───────────────────────────────────────────
    1:    "errcode",                    # System error code
    3:    "powInSumW",                  # Total input power (W) — float
    4:    "powOutSumW",                 # Total output power (W) — float
    5:    "lcdLight",                   # Screen brightness (0-100)

    # ── USB / Type-C ports ──────────────────────────────────────────────────
    9:    "powGetQcusb1",               # USB QC port 1 power (W) — float
    11:   "powGetTypec1",               # Type-C port 1 power (W) — float
    13:   "flowInfoQcusb1",             # USB port 1 switch status
    15:   "flowInfoTypec1",             # Type-C port 1 switch status

    # ── Standby / display timeouts ──────────────────────────────────────────
    17:   "devStandbyTime",             # Device timeout (min)
    18:   "screenOffTime",              # Screen timeout (min)

    # ── Cooling system ──────────────────────────────────────────────────────
    30:   "pcsFanLevel",                # Compressor fan level

    # ── AC input / output ───────────────────────────────────────────────────
    45:   "flowInfoAc2dc",              # AC-to-DC flow indicator
    47:   "flowInfoAcIn",               # AC input switch status
    53:   "powGetAc",                   # Real-time AC output power (W) — float
    54:   "powGetAcIn",                 # Real-time AC input power (W) — float
    61:   "plugInInfoAcInFlag",         # AC input charger connected (0/1)
    62:   "plugInInfoAcInFeq",          # AC input frequency (Hz)

    # ── Time / timezone ─────────────────────────────────────────────────────
    133:  "utcTimezone",                # UTC timezone offset
    134:  "utcTimezoneId",              # UTC timezone ID string
    135:  "utcSetMode",                 # UTC set mode (manual/auto)

    # ── BMS errors and flow ─────────────────────────────────────────────────
    140:  "bmsErrCode",                 # BMS error code
    152:  "flowInfoBmsDsg",             # BMS discharge flow indicator
    153:  "flowInfoBmsChg",             # BMS charge flow indicator
    158:  "powGetBms",                  # BMS power flow (W) — float

    # ── User preferences ────────────────────────────────────────────────────
    195:  "enBeep",                     # Beep enabled (0/1)
    202:  "plugInInfoAcChargerFlag",    # AC charger connected (0/1)
    209:  "plugInInfoAcInChgPowMax",    # Max AC charging power (W)
    212:  "devSleepState",              # Sleep status (0/1)
    213:  "pdErrCode",                  # PD module error code
    238:  "plugInInfoAcOutDsgPowMax",   # Max AC discharge power (W)

    # ── BMS battery (single-pack) ───────────────────────────────────────────
    242:  "bmsBattSoc",                 # Battery SOC (%) — float
    243:  "bmsBattSoh",                 # Battery SOH (%) — float
    248:  "bmsDesignCap",               # Battery design capacity (mAh)
    254:  "bmsDsgRemTime",              # Remaining discharge time (min)
    255:  "bmsChgRemTime",              # Remaining charge time (min)
    258:  "bmsMinCellTemp",             # Min battery cell temp (°C)
    259:  "bmsMaxCellTemp",             # Max battery cell temp (°C)
    260:  "bmsMinMosTemp",              # Min MOSFET temp (°C)
    261:  "bmsMaxMosTemp",              # Max MOSFET temp (°C)

    # ── CMS overall (system-wide) ───────────────────────────────────────────
    262:  "cmsBattSoc",                 # Overall SOC (%) — float
    263:  "cmsBattSoh",                 # Overall SOH (%) — float
    268:  "cmsDsgRemTime",              # Overall discharge time (min)
    269:  "cmsChgRemTime",              # Overall charge time (min)
    270:  "cmsMaxChgSoc",               # Max charge SOC limit (%)
    271:  "cmsMinDsgSoc",               # Min discharge SOC limit (%)
    275:  "cmsBmsRunState",             # On/Off status (0=off, 1=on)
    281:  "bmsChgDsgState",             # BMS charge/discharge state
    282:  "cmsChgDsgState",             # Overall charge/discharge state

    # ── Time tasks ──────────────────────────────────────────────────────────
    285:  "timeTaskConflictFlag",       # Time task conflict flag
    286:  "timeTaskChangeCnt",          # Time task change counter

    # ── PV input ────────────────────────────────────────────────────────────
    356:  "plugInInfoPvDcAmpMax",       # PV DC max current (A)
    360:  "flowInfoPv",                 # PV flow indicator
    361:  "powGetPv",                   # PV input power (W) — float
    363:  "plugInInfoPvType",           # PV source type
    364:  "plugInInfoPvChargerFlag",    # PV charger connected (0/1)
    365:  "plugInInfoPvChgAmpMax",      # PV charge current max (A)
    366:  "plugInInfoPvChgVolMax",      # PV charge voltage max (V)

    # ── BMS identification ──────────────────────────────────────────────────
    392:  "bmsMainSn",                  # BMS main serial number

    # ── DC plug-in (DCP) port ───────────────────────────────────────────────
    423:  "flowInfoDcpIn",              # DCP input flow
    424:  "flowInfoDcpOut",             # DCP output flow
    425:  "powGetDcp",                  # DCP power (W) — float
    426:  "plugInInfoDcpInFlag",        # DCP input connected (0/1)
    427:  "plugInInfoDcpType",          # DCP source type
    428:  "plugInInfoDcpDetail",        # DCP detail string
    431:  "plugInInfoDcpDsgChgType",    # DCP charge/discharge type
    433:  "plugInInfoDcpSn",            # DCP serial number
    434:  "plugInInfoDcpFirmVer",       # DCP firmware version
    435:  "plugInInfoDcpChargerFlag",   # DCP charger active (0/1)
    436:  "plugInInfoDcpRunState",      # DCP run state
    438:  "plugInInfoDcpErrCode",       # DCP error code
    458:  "plugInInfoAcInChgHalPowMax", # AC half-power charging max (W)

    # ── Climate / environment ───────────────────────────────────────────────
    484:  "tempAmbient",                # Ambient temperature (°C) — float
    485:  "humiAmbient",                # Ambient humidity (%) — float
    486:  "waveOperatingMode",          # Operating mode (cool/heat/fan/auto)
    494:  "tempIndoorSupplyAir",        # Supply air temperature (°C) — float
    504:  "condensateWaterLevel",       # Condensate water level (%) — float
    505:  "inDrainage",                 # Currently draining (0/1)
    506:  "drainageMode",               # Drainage mode setting
    507:  "moodLightMode",              # Mood light mode
    508:  "lcdShowTempType",            # Display temp unit setting
    509:  "enPetCare",                  # Pet care mode enabled (0/1)
    510:  "tempPetCareWarning",         # Pet care warning temp threshold (°C) — float
    512:  "userTempUnit",               # User temp unit (Celsius/Fahrenheit)
    513:  "petCareWarning",             # Pet care warning active (0/1)

    # ── Self-consumption ────────────────────────────────────────────────────
    777:  "powGetSelfConsume",          # Self-consumption power (W) — float
    778:  "powerOffDelaySet",           # Power-off delay setting (min)
    779:  "powerOffDelayRemaining",     # Power-off delay remaining (min)
}

# ── Proto field numbers that are FLOAT (wire type 5 = 32-bit IEEE 754) ──────
# All other fields are varint (wire type 0).
# Source: foxthefox proto definition — "optional float" fields
FLOAT_FIELDS: set[int] = {
    3, 4,                       # powInSumW, powOutSumW
    9, 11,                      # USB/Type-C port power
    53, 54,                     # AC out/in power
    158,                        # BMS power flow
    242, 243,                   # BMS SOC, SOH
    262, 263,                   # CMS SOC, SOH
    361,                        # PV power
    425,                        # DCP power
    484, 485,                   # Ambient temp, humidity
    494,                        # Indoor supply air temp
    504,                        # Condensate water level
    510,                        # Pet care warning temp
    777,                        # Self-consumption power
}

# Wave 3 uses the same protobuf envelope as Stream AC (cmdFunc=254).
# latestQuotas keepalive is structurally identical — reuses
# stream_build_latest_quotas() from proto_codec.py.

DEVICE_MODEL = "Wave 3"
