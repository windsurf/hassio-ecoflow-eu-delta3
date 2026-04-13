"""Device definition for EcoFlow Delta 2 Max.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/delta2_max.py — confirmed)
  - snell-evan-itt/hassio-ecoflow-cloud-US (internal/delta2_max.py — confirmed)

Key differences vs Delta 2:
  - Dual solar inputs (mppt.pv2InWatts/Vol/Amp)
  - Dual numbered slave batteries (bms_slave_bmsSlaveStatus_1/2.*)
  - AC control via inv module (3) not mppt module (5)
  - Beeper on pd.beepMode not mppt.beepState
  - AC charging via inv.SlowChgWatts (max 2400W)
  - AC Always-On via pd.newAcAutoOnCfg not pd.acAutoOutConfig
  - Generator keys: bms_emsStatus.minOpenOilEbSoc (different suffix)
  - Standby via inv.standbyMin not pd.standbyMin
  - Accumulative energy sensors from bms_bmsInfo
"""
from __future__ import annotations

# ── Shared keys (same MQTT paths as Delta 2 / Delta 3) ───────────────────────
from .delta3_1500 import (
    KEY_SOC, KEY_SOH, KEY_CYCLES,
    KEY_BATT_VOLT, KEY_BATT_TEMP,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_SOC_FLOAT,
    KEY_EMS_SOC_LCD,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_AC_OUT_W, KEY_AC_IN_W,
    KEY_AC_IN_VOLT, KEY_AC_OUT_VOLT,
    KEY_AC_TEMP,
    KEY_SOLAR_W, KEY_SOLAR_OUT_W,
    KEY_SOLAR_VOLT, KEY_SOLAR_AMP,
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_USB1_W, KEY_USB2_W, KEY_USB_QC1_W, KEY_USB_QC2_W,
    KEY_USBC1_W, KEY_USBC2_W,
    KEY_CHARGE_TIME,
    KEY_BP_POWER_SOC, KEY_BP_IS_CONFIG,
    KEY_DC_OUT_STATE,
    KEY_LCD_TIMEOUT,
)

# ── Delta 2 Max specific keys ────────────────────────────────────────────────

# Solar input 2 (dual MPPT)
KEY_SOLAR2_W    = "mppt.pv2InWatts"              # Solar 2 input power       (W)
KEY_SOLAR2_VOLT = "mppt.pv2InVol"                # Solar 2 input voltage     (mV)
KEY_SOLAR2_AMP  = "mppt.pv2InAmp"                # Solar 2 input current     (mA)

# AC / Inverter — D2Max uses inv module for AC control
KEY_AC_ENABLED_D2M   = "inv.cfgAcEnabled"        # AC output on/off          (0/1)
KEY_AC_XBOOST_D2M    = "inv.cfgAcXboost"         # X-Boost on/off            (0/1)
KEY_AC_CHG_W_D2M     = "inv.SlowChgWatts"        # AC slow charge limit      (W)
KEY_INV_STANDBY      = "inv.standbyMin"           # Unit standby time         (min)

# Beeper — D2Max uses pd.beepMode (not mppt.beepState)
KEY_BEEP_D2M         = "pd.beepMode"              # Beep on/off               (0/1)

# AC Always-On — different key than D2
KEY_AC_ALWAYS_ON_D2M = "pd.newAcAutoOnCfg"        # AC auto-on config         (0/1)

# Generator — different suffix than D2
KEY_GEN_START_D2M    = "bms_emsStatus.minOpenOilEbSoc"   # Generator start SOC (%)
KEY_GEN_STOP_D2M     = "bms_emsStatus.maxCloseOilEbSoc"  # Generator stop SOC  (%)

# Accumulative energy (lifetime stats)
KEY_ACCU_CHG_CAP     = "bms_bmsInfo.accuChgCap"          # Cumul. charged cap  (mAh)
KEY_ACCU_DSG_CAP     = "bms_bmsInfo.accuDsgCap"          # Cumul. discharged   (mAh)
KEY_ACCU_CHG_ENERGY  = "bms_bmsInfo.accuChgEnergy"       # Cumul. charge       (Wh)
KEY_ACCU_DSG_ENERGY  = "bms_bmsInfo.accuDsgEnergy"       # Cumul. discharge    (Wh)

# EMS discharge time
KEY_EMS_DSG_TIME_D2M = "bms_emsStatus.dsgRemainTime"     # Remaining discharge (min)

# DC standby
KEY_DC_STANDBY_D2M   = "mppt.carStandbyMin"              # DC standby time     (min)

# ── Slave batteries (numbered: _1 and _2) ────────────────────────────────────
# Delta 2 Max uses bms_slave_bmsSlaveStatus_N.* (not bms_slave.*)
KEY_SLV1_SOC        = "bms_slave_bmsSlaveStatus_1.soc"
KEY_SLV1_SOH        = "bms_slave_bmsSlaveStatus_1.soh"
KEY_SLV1_SOC_FLOAT  = "bms_slave_bmsSlaveStatus_1.f32ShowSoc"
KEY_SLV1_TEMP       = "bms_slave_bmsSlaveStatus_1.temp"
KEY_SLV1_MIN_CT     = "bms_slave_bmsSlaveStatus_1.minCellTemp"
KEY_SLV1_MAX_CT     = "bms_slave_bmsSlaveStatus_1.maxCellTemp"
KEY_SLV1_VOLT       = "bms_slave_bmsSlaveStatus_1.vol"
KEY_SLV1_MIN_CV     = "bms_slave_bmsSlaveStatus_1.minCellVol"
KEY_SLV1_MAX_CV     = "bms_slave_bmsSlaveStatus_1.maxCellVol"
KEY_SLV1_REMAIN_CAP = "bms_slave_bmsSlaveStatus_1.remainCap"
KEY_SLV1_FULL_CAP   = "bms_slave_bmsSlaveStatus_1.fullCap"
KEY_SLV1_DESIGN_CAP = "bms_slave_bmsSlaveStatus_1.designCap"
KEY_SLV1_CYCLES     = "bms_slave_bmsSlaveStatus_1.cycles"
KEY_SLV1_INPUT_W    = "bms_slave_bmsSlaveStatus_1.inputWatts"
KEY_SLV1_OUTPUT_W   = "bms_slave_bmsSlaveStatus_1.outputWatts"

KEY_SLV2_SOC        = "bms_slave_bmsSlaveStatus_2.soc"
KEY_SLV2_SOH        = "bms_slave_bmsSlaveStatus_2.soh"
KEY_SLV2_SOC_FLOAT  = "bms_slave_bmsSlaveStatus_2.f32ShowSoc"
KEY_SLV2_TEMP       = "bms_slave_bmsSlaveStatus_2.temp"
KEY_SLV2_MIN_CT     = "bms_slave_bmsSlaveStatus_2.minCellTemp"
KEY_SLV2_MAX_CT     = "bms_slave_bmsSlaveStatus_2.maxCellTemp"
KEY_SLV2_VOLT       = "bms_slave_bmsSlaveStatus_2.vol"
KEY_SLV2_MIN_CV     = "bms_slave_bmsSlaveStatus_2.minCellVol"
KEY_SLV2_MAX_CV     = "bms_slave_bmsSlaveStatus_2.maxCellVol"
KEY_SLV2_REMAIN_CAP = "bms_slave_bmsSlaveStatus_2.remainCap"
KEY_SLV2_FULL_CAP   = "bms_slave_bmsSlaveStatus_2.fullCap"
KEY_SLV2_DESIGN_CAP = "bms_slave_bmsSlaveStatus_2.designCap"
KEY_SLV2_CYCLES     = "bms_slave_bmsSlaveStatus_2.cycles"
KEY_SLV2_INPUT_W    = "bms_slave_bmsSlaveStatus_2.inputWatts"
KEY_SLV2_OUTPUT_W   = "bms_slave_bmsSlaveStatus_2.outputWatts"

# Slave accumulative energy
KEY_SLV1_ACCU_CHG_CAP    = "bms_slave_bmsSlaveInfo_1.accuChgCap"
KEY_SLV1_ACCU_DSG_CAP    = "bms_slave_bmsSlaveInfo_1.accuDsgCap"
KEY_SLV1_ACCU_CHG_ENERGY = "bms_slave_bmsSlaveInfo_1.accuChgEnergy"
KEY_SLV1_ACCU_DSG_ENERGY = "bms_slave_bmsSlaveInfo_1.accuDsgEnergy"
KEY_SLV2_ACCU_CHG_CAP    = "bms_slave_bmsSlaveInfo_2.accuChgCap"
KEY_SLV2_ACCU_DSG_CAP    = "bms_slave_bmsSlaveInfo_2.accuDsgCap"
KEY_SLV2_ACCU_CHG_ENERGY = "bms_slave_bmsSlaveInfo_2.accuChgEnergy"
KEY_SLV2_ACCU_DSG_ENERGY = "bms_slave_bmsSlaveInfo_2.accuDsgEnergy"

# ── Constants ────────────────────────────────────────────────────────────────
AC_CHG_WATTS_MIN    = 200
AC_CHG_WATTS_MAX    = 2400   # Delta 2 Max = 2400W
AC_CHG_WATTS_STEP   = 100

# ── Device info ──────────────────────────────────────────────────────────────
DEVICE_MODEL = "Delta 2 Max"
