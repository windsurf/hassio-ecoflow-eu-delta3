"""Device definition for EcoFlow Delta 3 1500.

All quota keys sourced from:
  - Live MQTT payload dump (HA log 2026-03-09)
  - Live get-all MQTT observation (1 April 2026)
  - https://github.com/foxthefox/ioBroker.ecoflow-mqtt (Delta 2/3 reference)
  - https://pkg.go.dev/git.myservermanager.com/varakh/go-ecoflow
  - https://developer-eu.ecoflow.com/us/document/delta2
"""
from __future__ import annotations

# ── Battery / BMS ─────────────────────────────────────────────────────────────
KEY_SOC             = "pd.soc"                         # State of charge           (%)
KEY_BATT_TEMP       = "bms_bmsStatus.temp"             # Battery pack temperature  (°C)
KEY_CYCLES          = "bms_bmsStatus.cycles"           # Charge cycles             (#)
KEY_SOH             = "bms_bmsStatus.soh"              # State of health           (%)
KEY_MIN_CELL_TEMP   = "bms_bmsStatus.minCellTemp"      # Min cell temperature      (°C)
KEY_MAX_CELL_TEMP   = "bms_bmsStatus.maxCellTemp"      # Max cell temperature      (°C)
KEY_MIN_CELL_VOLT   = "bms_bmsStatus.minCellVol"       # Min cell voltage          (mV)
KEY_MAX_CELL_VOLT   = "bms_bmsStatus.maxCellVol"       # Max cell voltage          (mV)
KEY_MIN_MOS_TEMP    = "bms_bmsStatus.minMosTemp"       # Min MOS temperature       (°C)
KEY_MAX_MOS_TEMP    = "bms_bmsStatus.maxMosTemp"       # Max MOS temperature       (°C)

# Capacity keys
KEY_DESIGN_CAP      = "bms_bmsStatus.designCap"        # Design capacity           (mAh)
KEY_FULL_CAP        = "bms_bmsStatus.fullCap"          # Full capacity             (mAh)
KEY_REMAIN_CAP      = "bms_bmsStatus.remainCap"        # Remaining capacity        (mAh)
KEY_BATT_VOLT       = "bms_bmsStatus.vol"              # Battery voltage           (mV)
KEY_BATT_CURR       = "bms_bmsStatus.amp"              # Battery current           (mA)
KEY_SOC_FLOAT       = "bms_bmsStatus.f32ShowSoc"       # SOC float (precise)       (%)
KEY_MAX_VOL_DIFF    = "bms_bmsStatus.maxVolDiff"       # Max cell voltage diff     (mV)
KEY_DC12V_STATE     = "mppt.carState"                  # 12V DC port state         (0/1)

# BMS extended diagnostics (v0.2.23 — confirmed in get-all dump)
KEY_BMS_ACT_SOC     = "bms_bmsStatus.actSoc"           # Actual SOC                (%)
KEY_BMS_SOC         = "bms_bmsStatus.soc"              # SOC (BMS internal)        (%)
KEY_BMS_CHG_STATE   = "bms_bmsStatus.chgState"         # Charge state BMS
KEY_BMS_SYS_STATE   = "bms_bmsStatus.sysState"         # System state BMS
KEY_BMS_MOS_STATE   = "bms_bmsStatus.mosState"         # MOS transistor state
KEY_BMS_FAULT       = "bms_bmsStatus.bmsFault"         # BMS fault flag
KEY_BMS_ALL_FAULT   = "bms_bmsStatus.allBmsFault"      # All BMS faults
KEY_BMS_ERR_CODE    = "bms_bmsStatus.errCode"          # BMS error code
KEY_BMS_ALL_ERR     = "bms_bmsStatus.allErrCode"       # All BMS error codes
KEY_BMS_BALANCE     = "bms_bmsStatus.balanceState"     # Cell balancing active     (0/1)
KEY_BMS_CHG_CAP     = "bms_bmsStatus.chgCap"           # Charged capacity          (mAh)
KEY_BMS_DSG_CAP     = "bms_bmsStatus.dsgCap"           # Discharged capacity       (mAh)
KEY_BMS_INPUT_W     = "bms_bmsStatus.inputWatts"       # BMS input power           (W)
KEY_BMS_OUTPUT_W    = "bms_bmsStatus.outputWatts"      # BMS output power          (W)
KEY_BMS_REAL_SOH    = "bms_bmsStatus.realSoh"          # Real SoH                  (%)
KEY_BMS_CALC_SOH    = "bms_bmsStatus.caleSoh"          # Calculated SoH            (%)
KEY_BMS_CYC_SOH     = "bms_bmsStatus.cycSoh"           # Cycle SoH                 (%)
KEY_BMS_DIFF_SOC    = "bms_bmsStatus.diffSoc"          # SOC diff main/slave       (%)
KEY_BMS_TARGET_SOC  = "bms_bmsStatus.targetSoc"        # Target SOC                (%)
KEY_BMS_TAG_AMP     = "bms_bmsStatus.tagChgAmp"        # Target charge current     (mA)
KEY_BMS_REMAIN_T    = "bms_bmsStatus.remainTime"       # Remaining time BMS        (min)
KEY_BMS_BQ_REG      = "bms_bmsStatus.bqSysStatReg"     # BQ chip status register

# BMS Info — lifetime statistics (v0.2.23)
KEY_INFO_HIGH_T_CHG = "bms_bmsInfo.highTempChgTime"    # High temp charge time     (min)
KEY_INFO_HIGH_T     = "bms_bmsInfo.highTempTime"       # High temp total time      (min)
KEY_INFO_LOW_T_CHG  = "bms_bmsInfo.lowTempChgTime"     # Low temp charge time      (min)
KEY_INFO_LOW_T      = "bms_bmsInfo.lowTempTime"        # Low temp total time       (min)
KEY_INFO_PWR_CAP    = "bms_bmsInfo.powerCapability"    # Power capability

# ── EMS (Energy Management System) ───────────────────────────────────────────
KEY_REMAIN_TIME     = "pd.remainTime"                  # Remaining time            (min, neg=discharging)
KEY_CHARGE_TIME     = "bms_emsStatus.chgRemainTime"    # Time to full charge       (min)
KEY_EMS_MAX_CHG_SOC = "bms_emsStatus.maxChargeSoc"     # Max charge SOC            (%)
KEY_EMS_MIN_DSG_SOC = "bms_emsStatus.minDsgSoc"        # Min discharge SOC         (%)
KEY_EMS_CHG_VOL     = "bms_emsStatus.chgVol"           # EMS charge voltage        (mV)
KEY_EMS_CHG_AMP     = "bms_emsStatus.chgAmp"           # EMS charge current        (mA)
KEY_EMS_FAN_LEVEL   = "bms_emsStatus.fanLevel"         # Fan level                 (0-3)
KEY_EMS_CHG_LINE    = "bms_emsStatus.chgLinePlug"      # AC plug connected         (0/1)
KEY_EMS_UPS_FLAG    = "bms_emsStatus.openUpsFlag"      # UPS mode on/off           (0/1)
KEY_GEN_MIN_SOC     = "bms_emsStatus.minOpenOilEb"     # Generator start SOC       (%)
KEY_GEN_MAX_SOC     = "bms_emsStatus.maxCloseOilEb"    # Generator stop SOC        (%)
KEY_EMS_SYS_STATE   = "bms_emsStatus.sysChgDsgState"   # System charge/discharge state

# EMS extended (v0.2.23)
KEY_EMS_DSG_TIME    = "bms_emsStatus.dsgRemainTime"    # Remaining discharge time  (min)
KEY_EMS_CHG_STATE   = "bms_emsStatus.chgState"         # EMS charge state
KEY_EMS_CHG_CMD     = "bms_emsStatus.chgCmd"           # EMS charge command
KEY_EMS_DSG_CMD     = "bms_emsStatus.dsgCmd"           # EMS discharge command
KEY_EMS_CHG_COND    = "bms_emsStatus.chgDisCond"       # Charge condition
KEY_EMS_DSG_COND    = "bms_emsStatus.dsgDisCond"       # Discharge condition
KEY_EMS_WARN        = "bms_emsStatus.bmsWarState"      # BMS warning state
KEY_EMS_NORMAL      = "bms_emsStatus.emsIsNormalFlag"  # EMS normal flag           (0/1)
KEY_EMS_SOC_FLOAT   = "bms_emsStatus.f32LcdShowSoc"    # Display SOC float         (%)
KEY_EMS_SOC_LCD     = "bms_emsStatus.lcdShowSoc"       # Display SOC int           (%)
KEY_EMS_PARA_V_MAX  = "bms_emsStatus.paraVolMax"       # Parallel voltage max      (mV)
KEY_EMS_PARA_V_MIN  = "bms_emsStatus.paraVolMin"       # Parallel voltage min      (mV)

# ── BMS Kit Info (extra battery pack) ────────────────────────────────────────
KEY_KIT_WATTS       = "bms_kitInfo.watts"              # Extra battery power       (W)
KEY_KIT_NUM         = "bms_kitInfo.kitNum"             # Number of kits connected

# ── BMS Battery Info (lifetime statistics) ───────────────────────────────────
KEY_INFO_SOH        = "bms_bmsInfo.soh"                # State of health           (%)
KEY_INFO_CYCLES     = "bms_bmsInfo.bsmCycles"          # Total charge cycles
KEY_INFO_ACCU_CHG   = "bms_bmsInfo.accuChgCap"         # Cumul. charged cap.       (mAh)
KEY_INFO_ACCU_DSG   = "bms_bmsInfo.accuDsgCap"         # Cumul. discharged cap.    (mAh)
KEY_INFO_ACCU_CHG_E = "bms_bmsInfo.accuChgEnergy"      # Cumul. charge energy      (Wh)
KEY_INFO_ACCU_DSG_E = "bms_bmsInfo.accuDsgEnergy"      # Cumul. discharge energy   (Wh)
KEY_INFO_ROUND_TRIP = "bms_bmsInfo.roundTrip"          # Round-trip efficiency     (%)
KEY_INFO_SELF_DSG   = "bms_bmsInfo.selfDsgRate"        # Self-discharge rate       (%/day)
KEY_INFO_DEEP_DSG   = "bms_bmsInfo.deepDsgCnt"         # Deep discharge count
KEY_INFO_OHM_RES    = "bms_bmsInfo.ohmRes"             # Internal resistance       (mOhm)

# ── AC Inverter ───────────────────────────────────────────────────────────────
KEY_AC_OUT_W        = "inv.outputWatts"                # AC output power           (W)
KEY_AC_IN_W         = "inv.inputWatts"                 # AC input (mains) power    (W)
KEY_AC_IN_VOLT      = "inv.acInVol"                    # AC input voltage          (mV)
KEY_AC_IN_AMP       = "inv.acInAmp"                    # AC input current          (mA)
KEY_AC_IN_FREQ      = "inv.acInFreq"                   # AC input frequency        (Hz)
KEY_AC_OUT_VOLT     = "inv.invOutVol"                  # AC output voltage         (mV)
KEY_AC_OUT_AMP      = "inv.invOutAmp"                  # AC output current         (mA)
KEY_AC_OUT_FREQ_RT  = "inv.invOutFreq"                 # AC output freq (actual)   (Hz)
KEY_AC_ENABLED      = "pd.acEnabled"                   # AC output on/off          (0/1)
KEY_AC_XBOOST       = "mppt.cfgAcXboost"               # X-Boost on/off            (0/1)
KEY_AC_CFG_FREQ     = "inv.cfgAcOutFreq"               # Configured AC freq        (Hz)
KEY_AC_CFG_VOLT     = "inv.cfgAcOutVol"                # Configured AC voltage     (V)
KEY_AC_FAST_CHG_W   = "inv.FastChgWatts"               # AC fast charge limit      (W)
KEY_AC_SLOW_CHG_W   = "inv.SlowChgWatts"               # AC slow charge limit      (W)
KEY_AC_CHG_PAUSE    = "mppt.chgPauseFlag"              # AC charging paused        (0/1)
KEY_AC_FAN_STATE    = "inv.fanState"                   # Inverter fan on           (0/1)
KEY_AC_TEMP         = "inv.outTemp"                    # Inverter temperature      (°C)
KEY_DC_IN_VOLT      = "inv.dcInVol"                    # DC input voltage          (mV)
KEY_DC_IN_AMP       = "inv.dcInAmp"                    # DC input current          (mA)
KEY_DC_IN_TEMP      = "inv.dcInTemp"                   # DC input temperature      (°C)
KEY_AC_STANDBY_TIME = "mppt.acStandbyMins"             # AC standby time           (min)

# INV extended (v0.2.23)
KEY_INV_WORK_MODE   = "inv.cfgAcWorkMode"              # AC work mode
KEY_INV_CHARGER_T   = "inv.chargerType"                # Charger type INV
KEY_INV_DSG_TYPE    = "inv.dischargeType"              # Discharge type
KEY_INV_ERR_CODE    = "inv.errCode"                    # INV error code
KEY_INV_DIP         = "inv.acDipSwitch"                # AC DIP switch

# Delta 3 1500 AC charging limits
AC_CHG_WATTS_MIN    = 200
AC_CHG_WATTS_MAX    = 1500
AC_CHG_WATTS_STEP   = 100

# ── Solar / MPPT ──────────────────────────────────────────────────────────────
KEY_SOLAR_W         = "mppt.inWatts"                   # Solar input power         (W)
KEY_SOLAR_VOLT      = "mppt.inVol"                     # Solar input voltage       (mV)
KEY_SOLAR_AMP       = "mppt.inAmp"                     # Solar input current       (mA)
KEY_SOLAR_OUT_W     = "mppt.outWatts"                  # MPPT output power         (W)
KEY_MPPT_TEMP       = "mppt.mpptTemp"                  # MPPT temperature          (°C)
KEY_MPPT_CFG_CHG_W  = "mppt.cfgChgWatts"               # Configured AC charge limit (W) — 255=sentinel
KEY_DC12V_OUT_W     = "mppt.carOutWatts"               # DC 12V output power       (W)
KEY_DC12V_OUT_VOLT  = "mppt.carOutVol"                 # DC 12V voltage            (mV)
KEY_DC12V_OUT_AMP   = "mppt.carOutAmp"                 # DC 12V current            (mA)
KEY_DC12V_TEMP      = "mppt.carTemp"                   # DC 12V temperature        (°C)
KEY_DC12V_STANDBY   = "mppt.carStandbyMin"             # DC 12V standby time       (min)
KEY_DC_OUT_STATE    = "pd.carState"                    # DC output on/off          (0/1)
KEY_DC_OUT_TEMP     = "mppt.dc24vTemp"                 # DC output temperature     (°C)
KEY_DC_CHG_CURRENT  = "mppt.dcChgCurrent"              # DC charge current cfg     (mA)
KEY_DCDC12V_W       = "mppt.dcdc12vWatts"              # DC-DC 12V power           (W)
KEY_DCDC12V_VOLT    = "mppt.dcdc12vVol"                # DC-DC 12V voltage         (mV)
KEY_MPPT_BEEP       = "mppt.beepState"                 # Beep state                (0/1)
KEY_PV_CHG_PRIO     = "pd.pvChgPrioSet"                # Solar charge priority     (0/1)

# MPPT extended (v0.2.23)
KEY_MPPT_CHG_STATE  = "mppt.chgState"                  # MPPT charge state
KEY_MPPT_CHG_TYPE   = "mppt.chgType"                   # Current charge type
KEY_MPPT_CFG_CHG_T  = "mppt.cfgChgType"                # Configured charge type
KEY_MPPT_DSG_TYPE   = "mppt.dischargeType"             # MPPT discharge type
KEY_MPPT_FAULT      = "mppt.faultCode"                 # MPPT fault code
KEY_MPPT_OUT_AMP    = "mppt.outAmp"                    # MPPT output current       (mA)
KEY_MPPT_OUT_VOLT   = "mppt.outVol"                    # MPPT output voltage       (mV)
KEY_MPPT_DC24V_ST   = "mppt.dc24vState"                # DC 24V port state
KEY_SCR_STANDBY     = "mppt.scrStandbyMin"             # Screen standby time       (min)
KEY_POW_STANDBY     = "mppt.powStandbyMin"             # Overall standby time      (min)

# DC charge current options (mA): 4000=4A, 6000=6A, 8000=8A
DC_CHG_CURRENT_OPTIONS = [4000, 6000, 8000]

# ── USB / PD outputs ──────────────────────────────────────────────────────────
KEY_USB1_W          = "pd.usb1Watts"                   # USB-A 1 power             (W)
KEY_USB2_W          = "pd.usb2Watts"                   # USB-A 2 power             (W)
KEY_USB_QC1_W       = "pd.qcUsb1Watts"                 # USB-A QC1 power           (W)
KEY_USB_QC2_W       = "pd.qcUsb2Watts"                 # USB-A QC2 power           (W)
KEY_USBC1_W         = "pd.typec1Watts"                 # USB-C 1 power             (W)
KEY_USBC2_W         = "pd.typec2Watts"                 # USB-C 2 power             (W)
KEY_USBC1_TEMP      = "pd.typec1Temp"                  # USB-C 1 temperature       (°C)
KEY_USBC2_TEMP      = "pd.typec2Temp"                  # USB-C 2 temperature       (°C)
KEY_WIRE_W          = "pd.wireWatts"                   # Wireless charge power     (W)

# ── PD / System ───────────────────────────────────────────────────────────────
KEY_IN_W_TOTAL      = "pd.wattsInSum"                  # Total input power         (W)
KEY_OUT_W_TOTAL     = "pd.wattsOutSum"                 # Total output power        (W)
KEY_USB_OUT_STATE   = "pd.dcOutState"                  # USB output on/off         (0/1)
KEY_LCD_BRIGHTNESS  = "pd.brightLevel"                 # LCD brightness            (0-3)
KEY_LCD_TIMEOUT     = "pd.lcdOffSec"                   # LCD timeout               (s)
KEY_STANDBY_TIME    = "pd.standbyMin"                  # Device standby time       (min)
KEY_BEEP_MODE       = "mppt.beepState"                 # Beep on/off — mppt authoritative (confirmed via live MQTT)
KEY_WIFI_RSSI       = "pd.wifiRssi"                    # WiFi signal strength      (dBm)
KEY_CHG_DSG_STATE   = "pd.chgDsgState"                 # Charge/discharge state
KEY_CHG_SUN_POWER   = "pd.chgSunPower"                 # Solar charge power        (W)
KEY_CHG_POWER_AC    = "pd.chgPowerAC"                  # Cumul. AC charged         (x0.001 kWh)
KEY_CHG_POWER_DC    = "pd.chgPowerDC"                  # Cumul. DC charged         (x0.001 kWh)
KEY_DSG_POWER_AC    = "pd.dsgPowerAC"                  # Cumul. AC discharged      (x0.1 W)
KEY_DSG_POWER_DC    = "pd.dsgPowerDC"                  # Cumul. DC discharged      (x0.1 W)
KEY_AC_AUTO_ON      = "pd.acAutoOnCfg"                 # AC Auto-On config         (0/1)
KEY_AC_AUTO_OUT     = "pd.acAutoOutConfig"             # AC always-on config       (0/1)
KEY_AC_BYPASS_PAUSE = "pd.acAutoOutPause"              # Bypass paused             (0=active, 1=paused)
KEY_MIN_AC_SOC      = "pd.minAcoutSoc"                 # Min SOC for AC auto-on    (%)
KEY_BP_POWER_SOC    = "pd.bpPowerSoc"                  # Backup Reserve SOC slider (%)
KEY_BP_IS_CONFIG    = "pd.watchIsConfig"               # Backup Reserve on/off     (0/1) — confirmed via live MQTT
KEY_OUTPUT_MEMORY   = "pd.outputMemoryEn"              # Output Memory — not in telemetry, no state feedback on D361
KEY_DC12V_IN_W      = "pd.carWatts"                    # DC 12V input power        (W)

# PD extended (v0.2.23)
KEY_PD_CAR_TEMP     = "pd.carTemp"                     # DC 12V temperature PD     (°C)
KEY_PD_CAR_TIME     = "pd.carUsedTime"                 # DC 12V use time           (min)
KEY_PD_CHG_TYPE     = "pd.chargerType"                 # Charger type PD
KEY_PD_DCIN_TIME    = "pd.dcInUsedTime"                # DC input use time         (min)
KEY_PD_ERR_CODE     = "pd.errCode"                     # PD error code
KEY_PD_RJ45         = "pd.extRj45Port"                 # RJ45 port status
KEY_PD_EXT38        = "pd.ext3p8Port"                  # 3.8V port status
KEY_PD_EXT48        = "pd.ext4p8Port"                  # 4.8V port status
KEY_PD_HYSTERESIS   = "pd.hysteresisAdd"               # Hysteresis SOC            (%)
KEY_PD_INV_TIME     = "pd.invUsedTime"                 # Inverter use time         (min)
KEY_PD_MPPT_TIME    = "pd.mpptUsedTime"                # MPPT use time             (min)
KEY_PD_RELAY_CNT    = "pd.relaySwitchCnt"              # Relay switch count
KEY_PD_TYPEC_TIME   = "pd.typecUsedTime"               # USB-C use time            (min)
KEY_PD_USB_TIME     = "pd.usbUsedTime"                 # USB-A use time            (min)
KEY_PD_USBQC_TIME   = "pd.usbqcUsedTime"               # USB QC use time           (min)
KEY_PD_WIFI_RCV     = "pd.wifiAutoRcvy"                # WiFi auto recovery mode

# ── Slave battery (bms_slave) — v0.2.25 ───────────────────────────────────────
# P361Z1H4PGBR0251 slave confirmed present via MQTT telemetry (April 2026)
# Keys mirror bms_bmsStatus structure; units/scale identical to main battery.
KEY_SLV_SOC         = "bms_slave.soc"                  # Slave SOC                 (%)
KEY_SLV_SOC_FLOAT   = "bms_slave.f32ShowSoc"           # Slave SOC float (precise) (%)
KEY_SLV_SOH         = "bms_slave.soh"                  # Slave state of health     (%)
KEY_SLV_REAL_SOH    = "bms_slave.realSoh"              # Slave real SoH            (%)
KEY_SLV_VOLT        = "bms_slave.vol"                  # Slave battery voltage     (mV)
KEY_SLV_CURR        = "bms_slave.amp"                  # Slave battery current     (mA)
KEY_SLV_TEMP        = "bms_slave.temp"                 # Slave battery temperature (°C)
KEY_SLV_MIN_CELL_T  = "bms_slave.minCellTemp"          # Slave min cell temp       (°C)
KEY_SLV_MAX_CELL_T  = "bms_slave.maxCellTemp"          # Slave max cell temp       (°C)
KEY_SLV_MIN_MOS_T   = "bms_slave.minMosTemp"           # Slave min MOS temp        (°C)
KEY_SLV_MAX_MOS_T   = "bms_slave.maxMosTemp"           # Slave max MOS temp        (°C)
KEY_SLV_MIN_CELL_V  = "bms_slave.minCellVol"           # Slave min cell voltage    (mV)
KEY_SLV_MAX_CELL_V  = "bms_slave.maxCellVol"           # Slave max cell voltage    (mV)
KEY_SLV_MAX_VOL_D   = "bms_slave.maxVolDiff"           # Slave max voltage diff    (mV)
KEY_SLV_REMAIN_CAP  = "bms_slave.remainCap"            # Slave remaining cap       (mAh)
KEY_SLV_FULL_CAP    = "bms_slave.fullCap"              # Slave full capacity       (mAh)
KEY_SLV_DESIGN_CAP  = "bms_slave.designCap"            # Slave design capacity     (mAh)
KEY_SLV_INPUT_W     = "bms_slave.inputWatts"           # Slave input power         (W)
KEY_SLV_OUTPUT_W    = "bms_slave.outputWatts"          # Slave output power        (W)
KEY_SLV_CHG_STATE   = "bms_slave.chgState"             # Slave charge state
KEY_SLV_CYCLES      = "bms_slave.cycles"               # Slave charge cycles       (#)
KEY_SLV_REMAIN_T    = "bms_slave.remainTime"           # Slave remaining time      (min)
KEY_SLV_DIFF_SOC    = "bms_slave.diffSoc"              # Slave SOC difference      (%)
KEY_SLV_CHG_CAP     = "bms_slave.chgCap"               # Slave charged capacity    (mAh)
KEY_SLV_DSG_CAP     = "bms_slave.dsgCap"               # Slave discharged cap      (mAh)
KEY_SLV_ACCU_CHG    = "bms_slave.accuChgCap"           # Slave cumul. charged      (mAh)
KEY_SLV_ACCU_DSG    = "bms_slave.accuDsgCap"           # Slave cumul. discharged   (mAh)
KEY_SLV_ACCU_CHG_E  = "bms_slave.accuChgEnergy"        # Slave cumul. charge Wh    (Wh)
KEY_SLV_ACCU_DSG_E  = "bms_slave.accuDsgEnergy"        # Slave cumul. discharge Wh (Wh)
KEY_SLV_OHM_RES     = "bms_slave.ohmRes"               # Slave internal resistance (mΩ)
KEY_SLV_SELF_DSG    = "bms_slave.selfDsgRate"          # Slave self-discharge rate (%/day)
KEY_SLV_ROUND_TRIP  = "bms_slave.roundTrip"            # Slave round-trip eff.     (%)
KEY_SLV_DEEP_DSG    = "bms_slave.deepDsgCnt"           # Slave deep discharge cnt
KEY_SLV_SYS_STATE   = "bms_slave.sysState"             # Slave system state
KEY_SLV_MOS_STATE   = "bms_slave.mosState"             # Slave MOS state
KEY_SLV_BALANCE     = "bms_slave.balanceState"         # Slave cell balancing      (0/1)
KEY_SLV_ERR_CODE    = "bms_slave.errCode"              # Slave error code
KEY_SLV_ALL_ERR     = "bms_slave.allErrCode"           # Slave all error codes
KEY_SLV_FAULT       = "bms_slave.bmsFault"             # Slave BMS fault
KEY_SLV_ALL_FAULT   = "bms_slave.allBmsFault"          # Slave all BMS faults
KEY_SLV_BQ_REG      = "bms_slave.bqSysStatReg"        # Slave BQ chip status
KEY_SLV_CYC_SOH     = "bms_slave.cycSoh"               # Slave cycle SoH           (%)

# ── Device info ───────────────────────────────────────────────────────────────
DEVICE_MODEL = "Delta 3 1500"
