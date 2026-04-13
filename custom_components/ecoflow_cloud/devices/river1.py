"""Device definitions for EcoFlow River 1 series (River Max, River Pro, River Mini).

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/river_max.py, river_pro.py, river_mini.py)
  - snell-evan-itt/hassio-ecoflow-cloud-US (confirmed for Max/Pro)

Gen 1 protocol — bmsMaster.* / pd.* / inv.* key schema.
SET commands use TCP protocol with id numbers — not yet supported.
All entities are read-only sensors for now.

Key differences between variants:
  - River Max:  bmsMaster.soc, pd.soc combined, slave battery (bmsSlave1), 3x USB, energy counters
  - River Pro:  pd.soc (no bmsMaster), slave battery (bmsSlave1), 3x USB, energy counters, AC slow charge
  - River Mini: inv.soc (no bmsMaster), no slaves, no USB ports listed, energy counters, minimal sensors
"""
from __future__ import annotations

# ── River Max keys ───────────────────────────────────────────────────────────
# Uses bmsMaster.* for main battery (same as Delta Pro/Max)
RMAX_SOC             = "bmsMaster.soc"
RMAX_COMBINED_SOC    = "pd.soc"
RMAX_CYCLES          = "bmsMaster.cycles"
RMAX_BATT_TEMP       = "bmsMaster.temp"
RMAX_MIN_CELL_TEMP   = "bmsMaster.minCellTemp"
RMAX_MAX_CELL_TEMP   = "bmsMaster.maxCellTemp"
RMAX_BATT_VOLT       = "bmsMaster.vol"
RMAX_BATT_CURR       = "bmsMaster.amp"
RMAX_MIN_CELL_VOLT   = "bmsMaster.minCellVol"
RMAX_MAX_CELL_VOLT   = "bmsMaster.maxCellVol"
RMAX_REMAIN_CAP      = "bmsMaster.remainCap"
RMAX_FULL_CAP        = "bmsMaster.fullCap"
RMAX_DESIGN_CAP      = "bmsMaster.designCap"

# River Max slave (bmsSlave1)
RMAX_SLV_SOC         = "bmsSlave1.soc"
RMAX_SLV_TEMP        = "bmsSlave1.temp"
RMAX_SLV_MIN_CT      = "bmsSlave1.minCellTemp"
RMAX_SLV_MAX_CT      = "bmsSlave1.maxCellTemp"
RMAX_SLV_VOLT        = "bmsSlave1.vol"
RMAX_SLV_CURR        = "bmsSlave1.amp"
RMAX_SLV_MIN_CV      = "bmsSlave1.minCellVol"
RMAX_SLV_MAX_CV      = "bmsSlave1.maxCellVol"
RMAX_SLV_REMAIN_CAP  = "bmsSlave1.remainCap"
RMAX_SLV_FULL_CAP    = "bmsSlave1.fullCap"
RMAX_SLV_DESIGN_CAP  = "bmsSlave1.designCap"
RMAX_SLV_CYCLES      = "bmsSlave1.cycles"

# ── River Pro keys — mostly same as Max but pd.soc is primary ────────────────
RPRO_SOC             = "pd.soc"          # River Pro uses pd.soc as primary
RPRO_BATT_CURR       = "bmsMaster.amp"   # still has bmsMaster for current
# River Pro shares most PD/INV keys with Max

# ── River Mini keys — inv.* based, minimal ───────────────────────────────────
RMINI_SOC            = "inv.soc"
RMINI_CYCLES         = "inv.cycles"
RMINI_MAX_CHG_SOC    = "inv.maxChargeSoc"

# ── Shared keys (all River 1 variants) ───────────────────────────────────────
KEY_IN_W_TOTAL       = "pd.wattsInSum"
KEY_OUT_W_TOTAL      = "pd.wattsOutSum"
KEY_AC_IN_W          = "inv.inputWatts"
KEY_AC_OUT_W         = "inv.outputWatts"
KEY_AC_IN_VOLT       = "inv.acInVol"       # River Max uses this
KEY_AC_IN_VOLT_BE    = "inv.invInVol"      # River Pro/Mini use big-endian variant
KEY_AC_OUT_VOLT      = "inv.invOutVol"
KEY_DC_IN_AMP        = "inv.dcInAmp"
KEY_DC_IN_VOLT       = "inv.dcInVol"
KEY_INV_IN_TEMP      = "inv.inTemp"
KEY_INV_OUT_TEMP     = "inv.outTemp"
KEY_DC_OUT_W         = "pd.carWatts"
KEY_TYPEC_OUT_W      = "pd.typecWatts"
KEY_USB1_W           = "pd.usb1Watts"
KEY_USB2_W           = "pd.usb2Watts"
KEY_USB3_W           = "pd.usb3Watts"
KEY_REMAIN_TIME      = "pd.remainTime"

# Energy counters (note: River Max uses uppercase AC/DC, different from Delta Pro)
KEY_CHG_SUN_POWER    = "pd.chgSunPower"
KEY_CHG_POWER_AC     = "pd.chgPowerAC"     # uppercase AC (River 1 specific)
KEY_CHG_POWER_DC     = "pd.chgPowerDC"     # uppercase DC
KEY_DSG_POWER_AC     = "pd.dsgPowerAC"
KEY_DSG_POWER_DC     = "pd.dsgPowerDC"

# ── Device models ────────────────────────────────────────────────────────────
DEVICE_MODEL_RMAX  = "River Max"
DEVICE_MODEL_RPRO  = "River Pro"
DEVICE_MODEL_RMINI = "River Mini"
