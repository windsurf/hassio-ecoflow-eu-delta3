"""Device definition for EcoFlow PowerKit (modular off-grid power system).

The PowerKit is EcoFlow's modular setup for RVs, vans, and off-grid cabins.
A single PowerKit installation can contain multiple submodules:
  - bp1, bp2, ... (battery packs)
  - bbcin, bbcout (DC-DC converters — in/out)
  - iclow, ichigh (low/high voltage chargers)
  - ldac, lddc (load AC/DC outputs)
  - wireless (wireless charging)
  - kitscc (solar charge controller)
  - bp2000 (small 2000Wh battery pack)
  - mN_moduleType (module slot N metadata, N=0..9)

PROTOCOL: JSON over MQTT, similar to Gen 2 moduleType but structured as
a nested submodule tree. Telemetry arrives as heartbeat JSON messages
under keys per submodule (e.g. payload.bp1.soc, payload.ldac.outWatts).

READ-ONLY: foxthefox documents only GET commands (per-submodule quotas
fetch and latestQuotas). No SET commands are documented. All 12 "switch"
entities in foxthefox are GET-action triggers, not controllable toggles.
PowerKit remains sensor-only in v0.3.10.

KEY NAMING: submodule-prefixed flat keys, e.g. "bp1.soc", "ldac.outWatts".
foxthefox uses this dotted prefix convention in their state-dict model.

SN PREFIX: foxthefox example is "M106ZAB4Z..." suggesting "M106" prefix.
Placeholder registered; update when community confirms.

Source: foxthefox/ioBroker.ecoflow-mqtt (ef_powerkit_data.js)
"""
from __future__ import annotations

# ── Battery pack 1 (bp1) — primary battery ──────────────────────────────────
KEY_BP1_SOC             = "bp1.soc"                 # Battery SOC (%)
KEY_BP1_TOTAL_SOC       = "bp1.totalSoc"            # Overall SOC (%)
KEY_BP1_VOL             = "bp1.vol"                 # Battery voltage (V)
KEY_BP1_AMP             = "bp1.amp"                 # Battery current (A)
KEY_BP1_IN_WATTS        = "bp1.inWatts"             # Input power (W)
KEY_BP1_OUT_WATTS       = "bp1.outWatts"            # Output power (W)
KEY_BP1_TOTAL_IN_WATTS  = "bp1.totalInWatts"        # Total input power (W)
KEY_BP1_TOTAL_OUT_WATTS = "bp1.totalOutWatts"       # Total output power (W)
KEY_BP1_TEMP            = "bp1.temp"                # Battery temperature (°C)
KEY_BP1_MAX_CELL_TEMP   = "bp1.maxCellTemp"         # Max cell temperature (°C)
KEY_BP1_MIN_CELL_TEMP   = "bp1.minCellTemp"         # Min cell temperature (°C)
KEY_BP1_REMAIN_TIME     = "bp1.remainTime"          # Remaining time (min)
KEY_BP1_TOTAL_REM_TIME  = "bp1.totalRemainTime"     # Total remaining time (min)
KEY_BP1_CHG_SET_SOC     = "bp1.chgSetSoc"           # Charge target SOC (%)
KEY_BP1_DSG_SET_SOC     = "bp1.dsgSetSoc"           # Discharge limit SOC (%)

# ── Battery pack 2 (bp2) — secondary battery if present ─────────────────────
KEY_BP2_SOC             = "bp2.soc"                 # Battery SOC (%)
KEY_BP2_IN_WATTS        = "bp2.inWatts"             # Input power (W)
KEY_BP2_OUT_WATTS       = "bp2.outWatts"            # Output power (W)

# ── BBC (DC-DC) converter ───────────────────────────────────────────────────
KEY_BBCIN_WATTS         = "bbcin.inWatts"           # BBC input power (W)
KEY_BBCIN_VOL           = "bbcin.inVol"             # BBC input voltage (V)
KEY_BBCIN_AMP           = "bbcin.inAmp"             # BBC input current (A)
KEY_BBCOUT_WATTS        = "bbcout.outWatts"         # BBC output power (W)
KEY_BBCOUT_VOL          = "bbcout.outVol"           # BBC output voltage (V)

# ── Chargers ───────────────────────────────────────────────────────────────
KEY_ICHIGH_WATTS        = "ichigh.inWatts"          # High-voltage charger power (W)
KEY_ICLOW_WATTS         = "iclow.inWatts"           # Low-voltage charger power (W)

# ── Load outputs ───────────────────────────────────────────────────────────
KEY_LDAC_OUT_WATTS      = "ldac.outWatts"           # AC load output (W)
KEY_LDAC_OUT_VOL        = "ldac.outVol"             # AC output voltage (V)
KEY_LDAC_OUT_FREQ       = "ldac.outFreq"            # AC output frequency (Hz)
KEY_LDDC_OUT_WATTS      = "lddc.outWatts"           # DC load output (W)

# ── Solar charge controller ────────────────────────────────────────────────
KEY_KITSCC_IN_WATTS     = "kitscc.inWatts"          # Solar input power (W)
KEY_KITSCC_IN_VOL       = "kitscc.inVol"            # Solar input voltage (V)
KEY_KITSCC_IN_AMP       = "kitscc.inAmp"            # Solar input current (A)

# ── Wireless charger ───────────────────────────────────────────────────────
KEY_WIRELESS_OUT_WATTS  = "wireless.outWatts"       # Wireless output (W)

DEVICE_MODEL = "PowerKit"
