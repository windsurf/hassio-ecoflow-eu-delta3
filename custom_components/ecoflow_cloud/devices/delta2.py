"""Device definition for EcoFlow Delta 2.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/delta2.py — confirmed)
  - snell-evan-itt/hassio-ecoflow-cloud-US (internal/delta2.py — confirmed)
  - EcoFlow Developer API documentation (delta2)

The Delta 2 shares ~95% of its MQTT keys with the Delta 3 1500.
Keys that are identical are imported from delta3_1500.py.
Only Delta 2-specific keys and constants are defined here.
"""
from __future__ import annotations

# ── Re-export shared keys from Delta 3 1500 ──────────────────────────────────
# These keys use the same MQTT paths on both Delta 2 and Delta 3 1500.
from .delta3_1500 import (
    # Battery / BMS
    KEY_SOC, KEY_SOH, KEY_CYCLES,
    KEY_BATT_VOLT, KEY_BATT_CURR, KEY_BATT_TEMP,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_SOC_FLOAT,
    # EMS
    KEY_REMAIN_TIME, KEY_CHARGE_TIME,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_EMS_SOC_LCD, KEY_EMS_CHG_STATE,
    KEY_GEN_MIN_SOC, KEY_GEN_MAX_SOC,
    # AC / Inverter
    KEY_AC_OUT_W, KEY_AC_IN_W,
    KEY_AC_IN_VOLT, KEY_AC_OUT_VOLT,
    KEY_AC_ENABLED, KEY_AC_XBOOST, KEY_AC_CHG_PAUSE,
    KEY_AC_TEMP,
    KEY_AC_STANDBY_TIME,
    # Solar / MPPT
    KEY_SOLAR_W, KEY_SOLAR_OUT_W,
    KEY_MPPT_CFG_CHG_W,
    KEY_DC12V_STANDBY,
    KEY_DC_OUT_STATE, KEY_DC_CHG_CURRENT,
    KEY_BEEP_MODE, KEY_PV_CHG_PRIO,
    # USB / PD
    KEY_USB1_W, KEY_USB2_W, KEY_USB_QC1_W, KEY_USB_QC2_W,
    KEY_USBC1_W, KEY_USBC2_W,
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_BP_POWER_SOC, KEY_BP_IS_CONFIG,
    KEY_LCD_TIMEOUT, KEY_STANDBY_TIME,
    KEY_AC_AUTO_OUT,
    # Slave battery
    KEY_SLV_SOC, KEY_SLV_SOH, KEY_SLV_TEMP,
    KEY_SLV_VOLT, KEY_SLV_CURR, KEY_SLV_CYCLES,
    KEY_SLV_MIN_CELL_T, KEY_SLV_MAX_CELL_T,
    KEY_SLV_MIN_CELL_V, KEY_SLV_MAX_CELL_V,
    KEY_SLV_REMAIN_CAP, KEY_SLV_FULL_CAP, KEY_SLV_DESIGN_CAP,
    KEY_SLV_INPUT_W, KEY_SLV_OUTPUT_W,
    # DC charge current options
    DC_CHG_CURRENT_OPTIONS,
)

# ── EMS extended (Delta 2) ───────────────────────────────────────────────────
KEY_EMS_DSG_TIME    = "bms_emsStatus.dsgRemainTime"    # Remaining discharge time  (min)

# ── Delta 2 specific constants ───────────────────────────────────────────────
AC_CHG_WATTS_MIN    = 200
AC_CHG_WATTS_MAX    = 1200   # Delta 2 max = 1200W (vs 1500W on Delta 3)
AC_CHG_WATTS_STEP   = 100

# ── Device info ──────────────────────────────────────────────────────────────
DEVICE_MODEL = "Delta 2"
