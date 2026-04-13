"""Device definition for EcoFlow Delta Mini.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/delta_mini.py — confirmed)

Gen 1 protocol — same key schema as Delta Pro/Max (bmsMaster/ems).
No slave battery support. AC charging max 900W.
"""
from __future__ import annotations

# Shares Gen 1 key schema with Delta Pro
from .delta_pro import (
    KEY_SOC, KEY_SOC_FLOAT, KEY_SOH, KEY_CYCLES,
    KEY_BATT_TEMP, KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_BATT_VOLT, KEY_BATT_CURR, KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_EMS_SOC_LCD, KEY_EMS_SOC_FLOAT,
    KEY_CHARGE_TIME, KEY_DSG_TIME,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_AC_IN_W, KEY_AC_OUT_W, KEY_AC_IN_VOLT, KEY_AC_OUT_VOLT,
    KEY_AC_ENABLED, KEY_AC_XBOOST,
    KEY_SOLAR_W, KEY_SOLAR_VOLT, KEY_SOLAR_AMP,
    KEY_SOLAR_OUT_W, KEY_SOLAR_OUT_VOLT,
    KEY_DC_CAR_OUT_W, KEY_DC_ANDERSON_W, KEY_DC_OUT_STATE,
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_USBC1_W, KEY_USBC2_W, KEY_USB1_W, KEY_USB2_W,
    KEY_USB_QC1_W, KEY_USB_QC2_W,
    KEY_LCD_TIMEOUT, KEY_BEEP,
    KEY_CHG_SUN_POWER, KEY_CHG_POWER_AC, KEY_CHG_POWER_DC,
    KEY_DSG_POWER_AC, KEY_DSG_POWER_DC,
    DC_CHG_CURRENT_OPTIONS,
)

KEY_AC_CHG_W = "inv.cfgSlowChgWatts"

AC_CHG_WATTS_MIN  = 200
AC_CHG_WATTS_MAX  = 900    # Delta Mini = 900W
AC_CHG_WATTS_STEP = 100

DEVICE_MODEL = "Delta Mini"
