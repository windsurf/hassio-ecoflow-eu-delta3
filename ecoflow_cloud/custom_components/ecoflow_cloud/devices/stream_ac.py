"""Device definition for EcoFlow Stream AC, Stream AC Pro, and Stream Ultra.

SN prefix: BK (all Stream AC variants)
  - Stream AC:     BK?1Z (base inverter, no battery)
  - Stream AC Pro: BK31Z (with battery, 1920Wh)
  - Stream Ultra:  BK11Z (with battery, 1920Wh, 4×PV)

Protocol: Protobuf (cmdFunc=254) — same envelope as Delta 3 / Delta Pro 3.
  - Telemetry: cmdId=21 (DisplayPropertyUpload), cmdId=22 (RuntimePropertyUpload)
  - SET command: cmdId=17 (ConfigWrite), wrapped in setMessage protobuf
  - SET response: cmdId=18 (ConfigWriteAck)
  - Envelope: src=32, dest=2, dSrc=1, dDest=1, cmdFunc=254, cmdId=17

The Stream AC family is a grid-tied micro-inverter with optional battery.
Unlike portable power stations, it feeds solar power directly into the grid
via a Schuko plug and manages battery charging/discharging automatically.

Source: foxthefox/ioBroker.ecoflow-mqtt (ef_stream_ac_pro_data.js, ef_stream_ultra_data.js,
        ef_stream_inverter_data.js) — protobuf schemas and community-confirmed MQTT telemetry.
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# Protobuf field numbers → coordinator key names
# Source: foxthefox DisplayPropertyUpload proto definition (cmdFunc=254, cmdId=21)
#
# These map proto field numbers to flat coordinator keys.
# The proto uses snake_case field names; we use camelCase keys to match
# the foxthefox/ioBroker convention for HA entity naming.
#
# Wire types:
#   - float fields (proto: float) → wire type 5 (32-bit fixed)
#   - uint32/int32 fields → wire type 0 (varint)
#   - string fields → wire type 2 (LEN)
#   - nested message fields → wire type 2 (LEN) — skipped in flat decode
# ══════════════════════════════════════════════════════════════════════════════

# ── DisplayPropertyUpload (cmdId=21) — telemetry field map ──────────────────
# Format: proto_field_number → coordinator_key
DISPLAY_FIELDS: dict[int, str] = {
    # ── Energy backup state ─────────────────────────────────────────────────
    6:    "energyBackupState",

    # ── PV inputs ───────────────────────────────────────────────────────────
    70:   "powGetPv2",                  # PV2 power (W) — float
    71:   "plugInInfoPv2Amp",           # PV2 current (A) — float
    133:  "utcTimezone",                # UTC timezone offset
    212:  "devSleepState",              # Sleep status (0/1)

    # ── Battery (AC Pro / Ultra only) ───────────────────────────────────────
    242:  "bmsBattSoc",                 # Battery SOC (%) — float
    243:  "bmsBattSoh",                 # Battery SOH (%) — float
    248:  "bmsDesignCap",               # Battery design capacity (mAh)
    254:  "bmsDsgRemTime",              # Remaining discharge time (min)
    255:  "bmsChgRemTime",              # Remaining charge time (min)
    258:  "bmsMinCellTemp",             # Min battery cell temp (°C)
    259:  "bmsMaxCellTemp",             # Max battery cell temp (°C)
    260:  "bmsMinMosTemp",              # Min MOSFET temp (°C)
    261:  "bmsMaxMosTemp",              # Max MOSFET temp (°C)
    262:  "cmsBattSoc",                 # Overall SOC (%) — float
    263:  "cmsBattSoh",                 # Overall SOH (%) — float
    268:  "cmsDsgRemTime",              # Overall discharge time remaining (min)
    269:  "cmsChgRemTime",              # Overall charge time remaining (min)
    270:  "cmsMaxChgSoc",               # Max charge SOC setting (%)
    271:  "cmsMinDsgSoc",               # Min discharge SOC setting (%)
    275:  "cmsBmsRunState",             # On/Off status (0=off, 1=on)
    281:  "bmsChgDsgState",             # Charge/discharge state (0=idle, 1=dsg, 2=chg)
    282:  "cmsChgDsgState",             # Overall charge/discharge state

    # ── PV1 input ───────────────────────────────────────────────────────────
    361:  "powGetPv",                   # PV1 power (W) — float
    362:  "plugInInfoPvFlag",           # PV1 connected (0/1)
    371:  "invNtcTemp3",                # Inverter NTC temp 3 (°C)
    380:  "plugInInfoPvVol",            # PV1 voltage (V) — float
    381:  "plugInInfoPvAmp",            # PV1 current (A) — float

    # ── PV2 flag ────────────────────────────────────────────────────────────
    421:  "plugInInfoPv2Flag",          # PV2 connected (0/1)
    442:  "plugInInfoPv2Vol",           # PV2 voltage (V) — float

    # ── Battery power limits ────────────────────────────────────────────────
    459:  "cmsBattPowOutMax",           # Max battery discharge power (W)
    460:  "cmsBattPowInMax",            # Max battery charge power (W)
    461:  "backupReverseSoc",           # Backup reserve SOC setting (%)
    462:  "cmsBattFullEnergy",          # Battery full energy (Wh)

    # ── Grid / system power ─────────────────────────────────────────────────
    515:  "powGetSysGrid",              # Grid power (W) — float
    516:  "powGetSysLoad",              # System load (W) — float
    517:  "powGetPvSum",                # Total PV power (W) — float
    518:  "powGetBpCms",                # Battery power (W) — float
    520:  "feedGridMode",               # Feed grid mode
    521:  "feedGridModePowLimit",       # Feed grid power limit (W)

    # ── Grid connection ─────────────────────────────────────────────────────
    613:  "gridConnectionVol",          # Grid voltage (V) — float
    614:  "gridConnectionAmp",          # Grid current (A) — float
    615:  "gridConnectionFreq",         # Grid frequency (Hz) — float
    616:  "gridConnectionPower",        # Grid connection power (W) — float
    618:  "gridConnectionPowerFactor",  # Grid power factor — float
    619:  "gridConnectionSta",          # Grid status (0=invalid, 1=in, 2=not online, 3=feed)
    638:  "invTargetPwr",               # Inverter target power (W) — float
    727:  "feedGridModePowMax",         # Feed grid max power (W)
    760:  "powConsumptionMeasurement",  # Power consumption measurement

    # ── Relay / AC output switches ──────────────────────────────────────────
    980:  "relay2Onoff",                # Relay 2 — AC output #1 (0=off, 1=on)
    981:  "relay4Onoff",                # Relay 4 — diagnostic
    982:  "relay3Onoff",                # Relay 3 — AC output #2 (0=off, 1=on)
    983:  "relay1Onoff",                # Relay 1 — diagnostic

    # ── System info ─────────────────────────────────────────────────────────
    984:  "systemGroupId",              # System group ID
    985:  "powSysAcOutMax",             # Max AC output power (W)
    989:  "powSysAcInMax",              # Max AC input power (W)
    992:  "sysGridConnectionPower",     # System grid connection power (W) — float
    993:  "socketMeasurePower",         # Socket measure power (W) — float
    994:  "brightness",                 # Display brightness

    # ── PV3/PV4 (Ultra: 4×PV) ──────────────────────────────────────────────
    987:  "plugInInfoPv3Flag",          # PV3 connected (0/1)
    988:  "plugInInfoPv4Flag",          # PV4 connected (0/1)
    996:  "powGetPv3",                  # PV3 power (W) — float
    997:  "powGetPv4",                  # PV4 power (W) — float
    998:  "plugInInfoPv3Vol",           # PV3 voltage (V) — float
    999:  "plugInInfoPv3Amp",           # PV3 current (A) — float
    1000: "plugInInfoPv4Vol",           # PV4 voltage (V) — float
    1001: "plugInInfoPv4Amp",           # PV4 current (A) — float

    # ── Power source breakdown ──────────────────────────────────────────────
    1002: "powGetSysLoadFromPv",        # Load from PV (W) — float
    1003: "powGetSysLoadFromBp",        # Load from battery (W) — float
    1004: "powGetSysLoadFromGrid",      # Load from grid (W) — float

    # ── Schuko output power ─────────────────────────────────────────────────
    1210: "powGetSchuko1",              # Schuko 1 output power (W) — float
    1211: "powGetSchuko2",              # Schuko 2 output power (W) — float

    # ── Battery heating ─────────────────────────────────────────────────────
    1212: "bmsBattHeating",             # Battery heating active (0/1)
}

# ── RuntimePropertyUpload (cmdId=22) — diagnostic telemetry ─────────────────
RUNTIME_FIELDS: dict[int, str] = {
    293:  "displayPropertyFullUploadPeriod",
    294:  "displayPropertyIncrementalUploadPeriod",
    295:  "runtimePropertyFullUploadPeriod",
    296:  "runtimePropertyIncrementalUploadPeriod",
}

# ── Proto field numbers that are FLOAT (wire type 5 = 32-bit IEEE 754) ──────
# All other fields are varint (wire type 0).
# Source: foxthefox proto definition — "optional float" fields
FLOAT_FIELDS: set[int] = {
    70, 71,                     # PV2 power, PV2 current
    242, 243,                   # BMS SOC, SOH
    262, 263,                   # CMS SOC, SOH
    361,                        # PV1 power
    380, 381,                   # PV1 voltage, current
    442,                        # PV2 voltage
    515, 516, 517, 518,         # Grid, load, PV sum, battery power
    613, 614, 615, 616, 618,    # Grid connection (V, A, Hz, W, PF)
    638,                        # Inverter target power
    992, 993,                   # System grid power, socket measure
    996, 997,                   # PV3, PV4 power
    998, 999, 1000, 1001,       # PV3/4 voltage, current
    1002, 1003, 1004,           # Load from PV/battery/grid
    1210, 1211,                 # Schuko 1/2 power
}

# ══════════════════════════════════════════════════════════════════════════════
# ConfigWrite SET command field numbers (cmdFunc=254, cmdId=17)
# Source: foxthefox ConfigWrite proto definition
# ══════════════════════════════════════════════════════════════════════════════

# Field 6 = cfgUtcTime (always included as timestamp in every command)
CMD_UTC_TIME_FIELD      = 6

CMD_MAX_CHG_SOC_FIELD   = 33    # cmsMaxChgSoc (%)
CMD_MIN_DSG_SOC_FIELD   = 34    # cmsMinDsgSoc (%)
CMD_BACKUP_SOC_FIELD    = 102   # backupReverseSoc (%)
CMD_RELAY2_FIELD        = 380   # relay2Onoff (AC output #1)
CMD_RELAY3_FIELD        = 381   # relay3Onoff (AC output #2)
CMD_POW_MEASURE_FIELD   = 239   # powConsumptionMeasurement
CMD_FEED_LIMIT_FIELD    = 169   # cfgFeedGridModePowLimit (W)
CMD_BRIGHTNESS_FIELD    = 384   # cfgBrightness

# ── ConfigWriteAck (cmdId=18) — field numbers → coordinator keys ────────────
# The ack contains the same field numbers as ConfigWrite.
# Maps command field numbers back to the same coordinator keys used by sensors.
# This allows command confirmations to update entity state immediately.
CONFIG_ACK_FIELDS: dict[int, str] = {
    33:   "cmsMaxChgSoc",
    34:   "cmsMinDsgSoc",
    102:  "backupReverseSoc",
    239:  "powConsumptionMeasurement",
    380:  "relay2Onoff",
    381:  "relay3Onoff",
    169:  "feedGridModePowLimit",
    384:  "brightness",
}

# ── Command envelope constants (identical to Delta 3 protobuf) ──────────────
STREAM_CMD_FUNC = 254
STREAM_CMD_ID   = 17
STREAM_SRC      = 32
STREAM_DEST     = 2
STREAM_D_SRC    = 1
STREAM_D_DEST   = 1

# ── Device model names ──────────────────────────────────────────────────────
DEVICE_MODEL_STREAM_AC      = "Stream AC"
DEVICE_MODEL_STREAM_AC_PRO  = "Stream AC Pro"
DEVICE_MODEL_STREAM_ULTRA   = "Stream Ultra"
