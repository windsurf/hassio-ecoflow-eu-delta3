"""Device definitions for EcoFlow River 2 / River 2 Max / River 2 Pro.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/river2.py, river2_max.py, river2_pro.py)
  - snell-evan-itt/hassio-ecoflow-cloud-US (confirmed identical)

Gen 2 protocol — same key schema as Delta 2 (bms_bmsStatus/bms_emsStatus/mppt).
Full control (switches/numbers/selects) supported.

Differences between River 2 variants:
  - River 2:     AC charging 100-360W, has DC solar current/voltage
  - River 2 Max: AC charging  50-660W, has DC solar current/voltage
  - River 2 Pro: AC charging 100-950W, no DC solar sensors, no AC Always-On switch
"""
from __future__ import annotations

# ── Shared keys — same MQTT paths as Delta 2/3 ──────────────────────────────
from .delta3_1500 import (
    KEY_SOC, KEY_SOH, KEY_CYCLES,
    KEY_BATT_TEMP, KEY_BATT_VOLT,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_EMS_SOC_LCD, KEY_EMS_CHG_STATE,
    KEY_REMAIN_TIME, KEY_CHARGE_TIME,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_AC_IN_W, KEY_AC_OUT_W,
    KEY_AC_IN_VOLT, KEY_AC_OUT_VOLT, KEY_AC_TEMP,
    KEY_AC_STANDBY_TIME,
    KEY_SOLAR_W,
    KEY_MPPT_CFG_CHG_W,
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_USBC1_W, KEY_USB1_W,
    KEY_BP_POWER_SOC, KEY_BP_IS_CONFIG,
    KEY_DC_OUT_STATE, KEY_DC_CHG_CURRENT,
    KEY_LCD_TIMEOUT, KEY_STANDBY_TIME,
    KEY_AC_AUTO_OUT, KEY_AC_XBOOST,
    DC_CHG_CURRENT_OPTIONS,
)

# ── River 2 specific keys ────────────────────────────────────────────────────
KEY_AC_ENABLED     = "mppt.cfgAcEnabled"          # AC output on/off (mppt module)
KEY_TYPEC_IN_W     = "pd.typecChaWatts"           # Type-C charging input (W)
KEY_DC_OUT_W       = "pd.carWatts"                # DC output power (W)
KEY_DC_IN_AMP      = "inv.dcInAmp"                # DC solar input current (mA)
KEY_DC_IN_VOLT     = "inv.dcInVol"                # DC solar input voltage (mV)
KEY_EMS_DSG_TIME   = "bms_emsStatus.dsgRemainTime"
KEY_CHG_TYPE       = "mppt.cfgChgType"            # DC charge mode (auto/solar/car)
KEY_SCR_STANDBY    = "mppt.scrStandbyMin"         # Screen standby (min)
KEY_POW_STANDBY    = "mppt.powStandbyMin"         # Unit standby (min)

# ── River 2 constants ────────────────────────────────────────────────────────
AC_CHG_WATTS_MIN  = 100
AC_CHG_WATTS_MAX  = 360    # River 2 = 360W
AC_CHG_WATTS_STEP = 50

# ── River 2 Max constants ────────────────────────────────────────────────────
R2MAX_AC_CHG_MIN  = 50
R2MAX_AC_CHG_MAX  = 660    # River 2 Max = 660W
R2MAX_AC_CHG_STEP = 50

# ── River 2 Pro constants ────────────────────────────────────────────────────
R2PRO_AC_CHG_MIN  = 100
R2PRO_AC_CHG_MAX  = 950    # River 2 Pro = 950W
R2PRO_AC_CHG_STEP = 50

# ── Device models ────────────────────────────────────────────────────────────
DEVICE_MODEL_R2     = "River 2"
DEVICE_MODEL_R2MAX  = "River 2 Max"
DEVICE_MODEL_R2PRO  = "River 2 Pro"
