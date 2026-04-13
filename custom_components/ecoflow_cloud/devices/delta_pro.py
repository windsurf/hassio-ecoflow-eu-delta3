"""Device definition for EcoFlow Delta Pro.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/delta_pro.py — confirmed)
  - snell-evan-itt/hassio-ecoflow-cloud-US (internal/delta_pro.py — confirmed)

Gen 1 protocol — key differences vs Delta 2/3:
  - Battery: bmsMaster.* (not bms_bmsStatus.*)
  - EMS: ems.* (not bms_emsStatus.*)
  - Slaves: bmsSlave1/2.* (not bms_slave.*)
  - Commands: TCP protocol with id numbers (not moduleType/operateType/params)
  - SET commands not yet supported in our _publish() — sensors are read-only for now
"""
from __future__ import annotations

# ── Battery / bmsMaster ──────────────────────────────────────────────────────
KEY_SOC             = "bmsMaster.soc"
KEY_SOC_FLOAT       = "bmsMaster.f32ShowSoc"
KEY_SOH             = "bmsMaster.soh"
KEY_CYCLES          = "bmsMaster.cycles"
KEY_BATT_TEMP       = "bmsMaster.temp"
KEY_MIN_CELL_TEMP   = "bmsMaster.minCellTemp"
KEY_MAX_CELL_TEMP   = "bmsMaster.maxCellTemp"
KEY_BATT_VOLT       = "bmsMaster.vol"
KEY_BATT_CURR       = "bmsMaster.amp"
KEY_MIN_CELL_VOLT   = "bmsMaster.minCellVol"
KEY_MAX_CELL_VOLT   = "bmsMaster.maxCellVol"
KEY_REMAIN_CAP      = "bmsMaster.remainCap"
KEY_FULL_CAP        = "bmsMaster.fullCap"
KEY_DESIGN_CAP      = "bmsMaster.designCap"

# ── EMS ──────────────────────────────────────────────────────────────────────
KEY_EMS_SOC_LCD     = "ems.lcdShowSoc"
KEY_EMS_SOC_FLOAT   = "ems.f32LcdShowSoc"
KEY_CHARGE_TIME     = "ems.chgRemainTime"
KEY_DSG_TIME        = "ems.dsgRemainTime"
KEY_EMS_MAX_CHG_SOC = "ems.maxChargeSoc"
KEY_EMS_MIN_DSG_SOC = "ems.minDsgSoc"
KEY_GEN_START       = "ems.minOpenOilEbSoc"
KEY_GEN_STOP        = "ems.maxCloseOilEbSoc"

# ── AC / Inverter ────────────────────────────────────────────────────────────
KEY_AC_IN_W         = "inv.inputWatts"
KEY_AC_OUT_W        = "inv.outputWatts"
KEY_AC_IN_VOLT      = "inv.acInVol"
KEY_AC_OUT_VOLT     = "inv.invOutVol"
KEY_AC_TEMP         = "inv.outTemp"
KEY_AC_ENABLED      = "inv.cfgAcEnabled"
KEY_AC_XBOOST       = "inv.cfgAcXboost"
KEY_AC_CHG_W        = "inv.cfgSlowChgWatts"
KEY_AC_STANDBY      = "inv.cfgStandbyMin"

# ── Solar / MPPT ─────────────────────────────────────────────────────────────
KEY_SOLAR_W         = "mppt.inWatts"
KEY_SOLAR_VOLT      = "mppt.inVol"
KEY_SOLAR_AMP       = "mppt.inAmp"
KEY_SOLAR_OUT_W     = "mppt.outWatts"
KEY_SOLAR_OUT_VOLT  = "mppt.outVol"
KEY_DC_CAR_OUT_W    = "mppt.carOutWatts"
KEY_DC_ANDERSON_W   = "mppt.dcdc12vWatts"
KEY_DC_OUT_STATE    = "mppt.carState"
KEY_DC_CHG_CURRENT  = "mppt.cfgDcChgCurrent"

# ── PD / System ──────────────────────────────────────────────────────────────
KEY_IN_W_TOTAL      = "pd.wattsInSum"
KEY_OUT_W_TOTAL     = "pd.wattsOutSum"
KEY_USBC1_W         = "pd.typec1Watts"
KEY_USBC2_W         = "pd.typec2Watts"
KEY_USB1_W          = "pd.usb1Watts"
KEY_USB2_W          = "pd.usb2Watts"
KEY_USB_QC1_W       = "pd.qcUsb1Watts"
KEY_USB_QC2_W       = "pd.qcUsb2Watts"
KEY_LCD_TIMEOUT     = "pd.lcdOffSec"
KEY_STANDBY_MODE    = "pd.standByMode"
KEY_BEEP            = "pd.beepState"
KEY_AC_AUTO_OUT     = "pd.acautooutConfig"
KEY_BP_IS_CONFIG    = "pd.watthisconfig"
KEY_BP_POWER_SOC    = "pd.bppowerSoc"

# ── Energy counters ──────────────────────────────────────────────────────────
KEY_CHG_SUN_POWER   = "pd.chgSunPower"
KEY_CHG_POWER_AC    = "pd.chgPowerAc"
KEY_CHG_POWER_DC    = "pd.chgPowerDc"
KEY_DSG_POWER_AC    = "pd.dsgPowerAc"
KEY_DSG_POWER_DC    = "pd.dsgPowerDc"

# ── Slave 1 (bmsSlave1) ─────────────────────────────────────────────────────
KEY_SLV1_SOC        = "bmsSlave1.soc"
KEY_SLV1_SOC_FLOAT  = "bmsSlave1.f32ShowSoc"
KEY_SLV1_SOH        = "bmsSlave1.soh"
KEY_SLV1_TEMP       = "bmsSlave1.temp"
KEY_SLV1_MIN_CT     = "bmsSlave1.minCellTemp"
KEY_SLV1_MAX_CT     = "bmsSlave1.maxCellTemp"
KEY_SLV1_VOLT       = "bmsSlave1.vol"
KEY_SLV1_CURR       = "bmsSlave1.amp"
KEY_SLV1_MIN_CV     = "bmsSlave1.minCellVol"
KEY_SLV1_MAX_CV     = "bmsSlave1.maxCellVol"
KEY_SLV1_REMAIN_CAP = "bmsSlave1.remainCap"
KEY_SLV1_FULL_CAP   = "bmsSlave1.fullCap"
KEY_SLV1_DESIGN_CAP = "bmsSlave1.designCap"
KEY_SLV1_CYCLES     = "bmsSlave1.cycles"
KEY_SLV1_INPUT_W    = "bmsSlave1.inputWatts"
KEY_SLV1_OUTPUT_W   = "bmsSlave1.outputWatts"

# ── Slave 2 (bmsSlave2) ─────────────────────────────────────────────────────
KEY_SLV2_SOC        = "bmsSlave2.soc"
KEY_SLV2_SOC_FLOAT  = "bmsSlave2.f32ShowSoc"
KEY_SLV2_SOH        = "bmsSlave2.soh"
KEY_SLV2_TEMP       = "bmsSlave2.temp"
KEY_SLV2_MIN_CT     = "bmsSlave2.minCellTemp"
KEY_SLV2_MAX_CT     = "bmsSlave2.maxCellTemp"
KEY_SLV2_VOLT       = "bmsSlave2.vol"
KEY_SLV2_CURR       = "bmsSlave2.amp"
KEY_SLV2_MIN_CV     = "bmsSlave2.minCellVol"
KEY_SLV2_MAX_CV     = "bmsSlave2.maxCellVol"
KEY_SLV2_REMAIN_CAP = "bmsSlave2.remainCap"
KEY_SLV2_FULL_CAP   = "bmsSlave2.fullCap"
KEY_SLV2_DESIGN_CAP = "bmsSlave2.designCap"
KEY_SLV2_CYCLES     = "bmsSlave2.cycles"
KEY_SLV2_INPUT_W    = "bmsSlave2.inputWatts"
KEY_SLV2_OUTPUT_W   = "bmsSlave2.outputWatts"

# ── Constants ────────────────────────────────────────────────────────────────
AC_CHG_WATTS_MIN    = 200
AC_CHG_WATTS_MAX    = 2900
AC_CHG_WATTS_STEP   = 100

DC_CHG_CURRENT_OPTIONS = [4000, 6000, 8000]

DEVICE_MODEL = "Delta Pro"
