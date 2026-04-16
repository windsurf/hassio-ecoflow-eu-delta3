"""Device definition for EcoFlow Wave 2 (portable AC).

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/wave2.py)

Uses bms.* for battery + pd.* for AC/climate sensors + power.* for power.
Commands use JSON protocol (moduleType=1, operateType per command).
"""
from __future__ import annotations

# Battery
KEY_SOC          = "bms.soc"
KEY_BATT_TEMP    = "bms.tmp"
KEY_MIN_CELL_T   = "bms.minCellTmp"
KEY_MAX_CELL_T   = "bms.maxCellTmp"
KEY_REMAIN_CAP   = "bms.remainCap"
KEY_CHG_REMAIN   = "pd.batChgRemain"
KEY_DSG_REMAIN   = "pd.batDsgRemain"

# Climate / temperatures
KEY_COND_TEMP    = "pd.condTemp"
KEY_COND_AIR_T   = "pd.coolTemp"
KEY_AIR_OUT_T    = "pd.coolEnv"
KEY_EVAP_TEMP    = "pd.evapTemp"
KEY_EXHAUST_T    = "pd.motorOutTemp"
KEY_EVAP_AIR_T   = "pd.heatEnv"
KEY_HEAT_AIR_OUT = "pd.airInTemp"
KEY_AMBIENT_T    = "pd.envTemp"
KEY_SET_TEMP     = "pd.setTemp"
KEY_MAIN_MODE    = "pd.mainMode"
KEY_SUB_MODE     = "pd.subMode"
KEY_FAN_VALUE    = "pd.fanValue"

# Power
KEY_PV_W         = "pd.pvPower"
KEY_BAT_OUT_W    = "pd.batPwrOut"
KEY_PV_CHG_W     = "pd.mpptPwr"
KEY_AC_IN_W      = "pd.acPwrIn"
KEY_SYS_POWER_W  = "pd.sysPowerWatts"
KEY_BAT_POWER_W  = "power.batPwrOut"
KEY_MOTOR_W      = "motor.power"
KEY_POWER_MODE   = "pd.powerMode"

# Alternate power keys (power.* module)
KEY_P_AC_IN      = "power.acPwrI"
KEY_P_BAT_OUT    = "power.batPwrOut"
KEY_P_PV_IN      = "pd.pvPower"

DEVICE_MODEL = "Wave 2"
