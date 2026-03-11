"""Device definition for EcoFlow Delta 3 1500.

All quota keys sourced from:
  - Live MQTT payload dump (HA log 2026-03-09)
  - https://github.com/foxthefox/ioBroker.ecoflow-mqtt (Delta 2/3 reference)
  - https://pkg.go.dev/git.myservermanager.com/varakh/go-ecoflow
  - https://developer-eu.ecoflow.com/us/document/delta2
"""
from __future__ import annotations

# ── Battery / BMS ─────────────────────────────────────────────────────────────
# bms_bmsStatus.* arrives every ~5 min in the full status dump.
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

# Capacity keys — confirmed in bms_bmsStatus full dump
KEY_DESIGN_CAP      = "bms_bmsStatus.designCap"        # Design capacity           (mAh)
KEY_FULL_CAP        = "bms_bmsStatus.fullCap"          # Full capacity             (mAh)
KEY_REMAIN_CAP      = "bms_bmsStatus.remainCap"        # Remaining capacity        (mAh)
KEY_BATT_VOLT       = "bms_bmsStatus.vol"              # Battery voltage           (mV)
KEY_BATT_CURR       = "bms_bmsStatus.amp"              # Battery current           (mA)
KEY_SOC_FLOAT       = "bms_bmsStatus.f32ShowSoc"       # SOC float (nauwkeurig)    (%)
KEY_MAX_VOL_DIFF    = "bms_bmsStatus.maxVolDiff"       # Max celvoltage-verschil   (mV)
KEY_DC12V_STATE     = "mppt.carState"                  # 12V DC port state         (0/1, read-only sensor)

# ── EMS (Energy Management System) ───────────────────────────────────────────
# bms_emsStatus.* arrives every ~5 min in the full status dump.
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
KEY_EMS_SYS_STATE   = "bms_emsStatus.sysChgDsgState"   # Systeem laad/ontlaad state

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
KEY_INFO_OHM_RES    = "bms_bmsInfo.ohmRes"             # Internal resistance       (mΩ)

# ── AC Inverter ───────────────────────────────────────────────────────────────
KEY_AC_OUT_W        = "inv.outputWatts"                # AC output power           (W)
KEY_AC_IN_W         = "inv.inputWatts"                 # AC input (mains) power    (W)
KEY_AC_IN_VOLT      = "inv.acInVol"                    # AC input voltage          (mV)
KEY_AC_IN_AMP       = "inv.acInAmp"                    # AC input current          (mA)
KEY_AC_IN_FREQ      = "inv.acInFreq"                   # AC input frequency        (Hz)
KEY_AC_OUT_VOLT     = "inv.invOutVol"                  # AC output voltage         (mV)
KEY_AC_OUT_AMP      = "inv.invOutAmp"                  # AC output current         (mA)
KEY_AC_OUT_FREQ_RT  = "inv.invOutFreq"                 # AC output freq (actual)   (Hz)
KEY_AC_ENABLED      = "pd.acEnabled"                   # AC output on/off          (0/1) — pd authoritative (confirmed by app MQTT trace)
KEY_AC_XBOOST       = "mppt.cfgAcXboost"               # X-Boost on/off            (0/1) — mppt structural
KEY_AC_CFG_FREQ     = "inv.cfgAcOutFreq"               # Configured AC freq        (Hz)
KEY_AC_CFG_VOLT     = "inv.cfgAcOutVol"                # Configured AC voltage     (V)
KEY_AC_FAST_CHG_W   = "inv.FastChgWatts"               # AC fast charge limit      (W)
KEY_AC_SLOW_CHG_W   = "inv.SlowChgWatts"               # AC slow charge limit      (W)
KEY_AC_CHG_PAUSE    = "mppt.chgPauseFlag"              # AC charging paused        (0/1) — mppt structural
KEY_AC_FAN_STATE    = "inv.fanState"                   # Inverter fan on           (0/1)
KEY_AC_TEMP         = "inv.outTemp"                    # Inverter temperature      (°C)
KEY_DC_IN_VOLT      = "inv.dcInVol"                    # DC input voltage          (mV)
KEY_DC_IN_AMP       = "inv.dcInAmp"                    # DC input current          (mA)
KEY_DC_IN_TEMP      = "inv.dcInTemp"                   # DC input temperature      (°C)
KEY_AC_STANDBY_TIME = "mppt.acStandbyMins"             # AC standby time           (min) — mppt structural

# Delta 3 1500 AC charging limits (different from Delta 2 which is max 1200W)
AC_CHG_WATTS_MIN    = 200
AC_CHG_WATTS_MAX    = 1500
AC_CHG_WATTS_STEP   = 100

# ── Solar / MPPT ──────────────────────────────────────────────────────────────
KEY_SOLAR_W         = "mppt.inWatts"                   # Solar input power         (W)
KEY_SOLAR_VOLT      = "mppt.inVol"                     # Solar input voltage       (mV)
KEY_SOLAR_AMP       = "mppt.inAmp"                     # Solar input current       (mA)
KEY_SOLAR_OUT_W     = "mppt.outWatts"                  # MPPT output power         (W)
KEY_MPPT_TEMP       = "mppt.mpptTemp"                  # MPPT temperature          (°C)
KEY_MPPT_CFG_CHG_W  = "mppt.cfgChgWatts"               # Configured AC charge limit (W)
KEY_DC12V_OUT_W     = "mppt.carOutWatts"               # DC 12V output power       (W)
KEY_DC12V_OUT_VOLT  = "mppt.carOutVol"                 # DC 12V voltage            (mV)
KEY_DC12V_OUT_AMP   = "mppt.carOutAmp"                 # DC 12V current            (mA)
# KEY_DC12V_STATE removed in v0.2.12: mppt.carState switch not implemented (read-only sensor sufficient)
KEY_DC12V_TEMP      = "mppt.carTemp"                   # DC 12V temperature        (°C)
KEY_DC12V_STANDBY   = "mppt.carStandbyMin"             # DC 12V standby time       (min)
KEY_DC_OUT_STATE    = "pd.carState"                    # DC output on/off          (0/1) — pd authoritative (confirmed by app MQTT trace)
KEY_DC_OUT_TEMP     = "mppt.dc24vTemp"                 # DC output temperature     (°C)
KEY_DC_CHG_CURRENT  = "mppt.dcChgCurrent"              # DC charge current cfg     (mA)
KEY_DCDC12V_W       = "mppt.dcdc12vWatts"              # DC-DC 12V power           (W)
KEY_DCDC12V_VOLT    = "mppt.dcdc12vVol"                # DC-DC 12V voltage         (mV)
KEY_MPPT_BEEP       = "mppt.beepState"                 # Beep state                (0/1)
KEY_PV_CHG_PRIO     = "pd.pvChgPrioSet"                # Solar charge priority     (0/1)

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
KEY_BEEP_MODE       = "mppt.beepState"                 # Beep on/off               (0/1) — mppt authoritative (confirmed by app MQTT trace)
KEY_WIFI_RSSI       = "pd.wifiRssi"                    # WiFi signal strength      (dBm)
KEY_CHG_DSG_STATE   = "pd.chgDsgState"                 # Charge/discharge state
KEY_CHG_SUN_POWER   = "pd.chgSunPower"                 # Solar charge power        (W)
KEY_CHG_POWER_AC    = "pd.chgPowerAC"                  # Cumul. AC charged         (×0.001 kWh)
KEY_CHG_POWER_DC    = "pd.chgPowerDC"                  # Cumul. DC charged         (×0.001 kWh)
KEY_DSG_POWER_AC    = "pd.dsgPowerAC"                  # Cumul. AC discharged      (×0.1 W)
KEY_DSG_POWER_DC    = "pd.dsgPowerDC"                  # Cumul. DC discharged      (×0.1 W)
KEY_AC_AUTO_ON      = "pd.watchIsConfig"               # Memory AC outputs on/off  (0/1) — confirmed by app MQTT trace (was pd.acAutoOnCfg)
KEY_AC_AUTO_OUT     = "pd.acAutoOutConfig"             # AC always-on enabled      (0/1)
KEY_AC_BYPASS_PAUSE = "pd.acAutoOutPause"              # Bypass paused             (0=active, 1=paused)
KEY_MIN_AC_SOC      = "pd.minAcoutSoc"                 # Min SOC for AC auto-on    (%)
KEY_BP_POWER_SOC    = "pd.bpPowerSoc"                  # Battery protection SOC    (%)
KEY_DC12V_IN_W      = "pd.carWatts"                    # DC 12V input power        (W)

# ── Device info ───────────────────────────────────────────────────────────────
DEVICE_MODEL = "Delta 3 1500"
