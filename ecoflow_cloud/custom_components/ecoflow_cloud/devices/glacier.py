"""Device definition for EcoFlow Glacier (portable fridge).

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/glacier.py)

Uses bms_bmsStatus/bms_emsStatus for battery + pd.* for fridge sensors.
Commands use JSON protocol (moduleType=1, operateType per command).
"""
from __future__ import annotations

# Battery (shared key names with Gen 2 but specific to Glacier)
KEY_SOC          = "bms_bmsStatus.soc"
KEY_DESIGN_CAP   = "bms_bmsStatus.designCap"
KEY_FULL_CAP     = "bms_bmsStatus.fullCap"
KEY_REMAIN_CAP   = "bms_bmsStatus.remainCap"
KEY_COMBINED_SOC = "bms_emsStatus.f32LcdSoc"
KEY_CHG_STATE    = "bms_emsStatus.chgState"
KEY_IN_W         = "bms_bmsStatus.inWatts"
KEY_OUT_W        = "bms_bmsStatus.outWatts"
KEY_MOTOR_W      = "pd.motorWat"
KEY_CHG_REMAIN   = "bms_emsStatus.chgRemain"
KEY_DSG_REMAIN   = "bms_emsStatus.dsgRemain"
KEY_CYCLES       = "bms_bmsStatus.cycles"
KEY_BATT_TEMP    = "bms_bmsStatus.tmp"
KEY_MIN_CELL_T   = "bms_bmsStatus.minCellTmp"
KEY_MAX_CELL_T   = "bms_bmsStatus.maxCellTmp"
KEY_BATT_VOLT    = "bms_bmsStatus.vol"
KEY_MIN_CELL_V   = "bms_bmsStatus.minCellVol"
KEY_MAX_CELL_V   = "bms_bmsStatus.maxCellVol"
KEY_BAT_PRESENT  = "pd.batFlag"
KEY_XT60         = "pd.xt60InState"
KEY_FAN_LEVEL    = "bms_emsStatus.fanLvl"

# Fridge temperatures (decicelsius — value / 10)
KEY_AMBIENT_T    = "pd.ambientTmp"
KEY_EXHAUST_T    = "pd.exhaustTmp"
KEY_WATER_T      = "pd.tempWater"
KEY_LEFT_T       = "pd.tmpL"
KEY_RIGHT_T      = "pd.tmpR"
KEY_DUAL_ZONE    = "pd.flagTwoZone"

# Ice maker
KEY_ICE_TIME     = "pd.iceTm"
KEY_ICE_PCT      = "pd.icePercent"
KEY_ICE_MODE     = "pd.iceMkMode"
KEY_ICE_ALERT    = "pd.iceAlert"
KEY_WATER_LINE   = "pd.waterLine"

# Temperature set points
KEY_LEFT_SET_T   = "pd.tmpLSet"
KEY_RIGHT_SET_T  = "pd.tmpRSet"
KEY_COMBINED_SET = "pd.tmpMSet"

# Command keys (switches)
KEY_BEEP_EN      = "pd.beepEn"
KEY_COOL_MODE    = "pd.coolMode"
KEY_PWR_STATE    = "pd.pwrState"

DEVICE_MODEL = "Glacier"
