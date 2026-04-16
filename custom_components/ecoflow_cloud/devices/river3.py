"""Device definition for EcoFlow River 3 and River 3 Plus.

SN prefix: R641 (River 3), R651 (River 3 Plus)

Protocol: Gen 3 (cmdFunc=254) — same command format as Delta Pro 3:
  - Command envelope: {sn, cmdId:17, cmdFunc:254, dest:2, dirDest:1, dirSrc:1, needAck:true, params:{...}}
  - Quota keys are FLAT (no pd./mppt./inv. prefix): enBeep, acOutFreq, cmsMaxChgSoc, etc.

Source: foxthefox/ioBroker.ecoflow-mqtt river3plus.md (community-confirmed via live MQTT telemetry)
        Protocol envelope identical to Delta Pro 3 (developer docs confirmed cmdFunc=254 for Gen 3)
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# Quota keys — flat namespace (no module prefix)
# Source: ioBroker.ecoflow-mqtt river3plus.md DisplayPropertyUpload + setDp3
# ══════════════════════════════════════════════════════════════════════════════

# ── Power sensors ────────────────────────────────────────────────────────────
KEY_SOC              = "bmsBattSoc"                    # Battery SOC (%)
KEY_SOH              = "bmsBattSoh"                    # Battery SOH (%)
KEY_TOTAL_IN_POWER   = "powInSumW"                     # Total input power (W)
KEY_TOTAL_OUT_POWER  = "powOutSumW"                    # Total output power (W)
KEY_DSG_REMAIN_TIME  = "bmsDsgRemTime"                 # Remaining discharge time (min)
KEY_CHG_REMAIN_TIME  = "bmsChgRemTime"                 # Remaining charge time (min)
KEY_DESIGN_CAP       = "bmsDesignCap"                  # Battery design capacity (mAh)
KEY_CMS_SOC          = "cmsBattSoc"                    # Overall SOC (%)
KEY_CMS_SOH          = "cmsBattSoh"                    # Overall SOH (%)
KEY_CMS_DSG_REM_TIME = "cmsDsgRemTime"                 # Overall remaining discharge time (min)
KEY_CMS_CHG_REM_TIME = "cmsChgRemTime"                 # Overall remaining charge time (min)

# ── Per-port output power ────────────────────────────────────────────────────
KEY_POW_AC_OUT       = "powGetAcOut"                   # AC output power (W)
KEY_POW_AC_IN        = "powGetAcIn"                    # AC input power (W)
KEY_POW_AC           = "powGetAc"                      # AC power (W)
KEY_POW_USB1         = "powGetQcusb1"                  # USB1 output power (W)
KEY_POW_USB2         = "powGetQcusb2"                  # USB2 output power (W)
KEY_POW_TYPEC1       = "powGetTypec1"                  # Type-C1 output power (W)
KEY_POW_TYPEC2       = "powGetTypec2"                  # Type-C2 output power (W)
KEY_POW_12V          = "powGet12v"                     # 12V output power (W)
KEY_POW_PV           = "powGetPv"                      # PV input power (W)
KEY_POW_BMS          = "powGetBms"                     # BMS power (W)
KEY_POW_DCP          = "powGetDcp"                     # DC port power (W)

# ── Temperatures ─────────────────────────────────────────────────────────────
KEY_TEMP_BMS_MIN     = "bmsMinCellTemp"                # Min battery cell temperature (°C)
KEY_TEMP_BMS_MAX     = "bmsMaxCellTemp"                # Max battery cell temperature (°C)

# ── AC input details ─────────────────────────────────────────────────────────
KEY_AC_IN_FREQ       = "plugInInfoAcInFeq"             # AC input frequency (Hz)
KEY_AC_OUT_FREQ      = "acOutFreq"                     # AC output frequency (Hz)
KEY_AC_DSG_POW_MAX   = "plugInInfoAcOutDsgPowMax"      # Max AC discharge power (W)
KEY_AC_CHG_POW_MAX   = "plugInInfoAcInChgHalPowMax"    # Max AC charging power (W)

# ── Status / diagnostics ────────────────────────────────────────────────────
KEY_CHG_DSG_STATE    = "bmsChgDsgState"                # 0=idle, 1=discharging, 2=charging
KEY_CMS_CHG_DSG_STATE = "cmsChgDsgState"               # Overall charge/discharge state
KEY_BMS_RUN_STATE    = "cmsBmsRunState"                # 0=off, 1=on
KEY_AC_IN_FLAG       = "plugInInfoAcInFlag"            # AC charger connected (0/1)
KEY_SLEEP_STATE      = "devSleepState"                 # Sleep status (0/1)

# ── Switches (bool / int 0-1) ───────────────────────────────────────────────
KEY_BEEP             = "enBeep"                        # Beep sound on/off
KEY_XBOOST           = "xboostEn"                      # X-Boost on/off
KEY_ENERGY_BACKUP_EN = "energyBackupEn"                # Backup reserve on/off
KEY_OUTPUT_MEMORY    = "outputPowerOffMemory"           # Output memory on/off

# ── Numbers (configurable settings) ─────────────────────────────────────────
KEY_DEV_STANDBY_TIME = "devStandbyTime"                # Device standby timeout (min)
KEY_SCREEN_OFF_TIME  = "screenOffTime"                 # Screen off timeout (sec)
KEY_AC_STANDBY_TIME  = "acStandbyTime"                 # AC standby timeout (min)
KEY_MAX_CHG_SOC      = "cmsMaxChgSoc"                  # Max charge SOC (%)
KEY_MIN_DSG_SOC      = "cmsMinDsgSoc"                  # Min discharge SOC (%)
KEY_ENERGY_BACKUP_SOC = "energyBackupStartSoc"         # Backup reserve SOC (%)
KEY_AC_CHG_POW_SET   = "plugInInfoAcInChgPowMax"       # AC charging power setting (W)
KEY_PV_DC_AMP_MAX    = "plugInInfoPvDcAmpMax"          # PV max charge current (A)
KEY_SILENCE_CHG_WATT = "silenceChgWatt"                # Silent mode charging watts (W)
KEY_LOW_POWER_ALARM  = "lowPowerAlarm"                 # Low power alarm threshold (W)
KEY_AC_ALWAYS_ON_SOC = "acAlwaysOnMiniSoc"             # AC Always-On min SOC (%)

# ── Port flow status (diagnostic) ───────────────────────────────────────────
KEY_FLOW_USB1        = "flowInfoQcusb1"                # USB1 status (0=off, 2=on)
KEY_FLOW_USB2        = "flowInfoQcusb2"                # USB2 status (0=off, 2=on)
KEY_FLOW_TYPEC1      = "flowInfoTypec1"                # Type-C1 status (0=off, 2=on)
KEY_FLOW_TYPEC2      = "flowInfoTypec2"                # Type-C2 status (0=off, 2=on)
KEY_FLOW_12V         = "flowInfo12v"                   # 12V status (0=off, 2=on)
KEY_FLOW_AC_IN       = "flowInfoAcIn"                  # AC input status (0=off, 2=on)
KEY_FLOW_DC2AC       = "flowInfoDc2ac"                 # DC-to-AC inverter (0=off, 2=on)
KEY_FLOW_AC2DC       = "flowInfoAc2dc"                 # AC-to-DC charger (0=off, 2=on)

# ══════════════════════════════════════════════════════════════════════════════
# SET command parameter names — cfgParam keys for Gen 3 envelope
# Source: ioBroker.ecoflow-mqtt setDp3 commands
# Envelope: {sn, cmdId:17, cmdFunc:254, dest:2, dirDest:1, dirSrc:1, needAck:true, params:{key: value}}
# ══════════════════════════════════════════════════════════════════════════════

CMD_BEEP             = "cfgBeepEn"                     # Beep on/off
CMD_XBOOST           = "cfgXboostEn"                   # X-Boost on/off
CMD_AC_OUT           = "cfgAcOutOpen"                  # AC output on/off
CMD_DC_12V_OUT       = "cfgDc12vOutOpen"               # 12V DC output on/off
CMD_OUTPUT_MEMORY    = "cfgOutputPowerOffMemory"       # Output memory on/off
CMD_DEV_STANDBY      = "cfgDevStandbyTime"             # Device standby (min)
CMD_SCREEN_OFF       = "cfgScreenOffTime"              # Screen off (sec)
CMD_AC_STANDBY       = "cfgAcStandbyTime"              # AC standby (min)
CMD_MAX_CHG_SOC      = "cfgMaxChgSoc"                  # Max charge SOC (%)
CMD_MIN_DSG_SOC      = "cfgMinDsgSoc"                  # Min discharge SOC (%)
CMD_ENERGY_BACKUP    = "cfgEnergyBackup"               # nested: {energyBackupStartSoc, energyBackupEn}
CMD_AC_CHG_POW       = "cfgPlugInInfoAcInChgPowMax"    # AC charging power (W)
CMD_PV_DC_AMP        = "cfgPlugInInfoPvDcAmpMax"       # PV max charge current (A)
CMD_PV_CHG_TYPE      = "cfgPvChgType"                  # DC charging mode (0/1/2)

# ── Gen 3 Command envelope constants (shared with Delta Pro 3) ──────────────
# Import from delta_pro_3 to avoid duplication
# DP3_CMD_ID = 17, DP3_CMD_FUNC = 254, DP3_DEST = 2, DP3_DIR_DEST = 1, DP3_DIR_SRC = 1

DEVICE_MODEL_R3      = "River 3"
DEVICE_MODEL_R3P     = "River 3 Plus"
