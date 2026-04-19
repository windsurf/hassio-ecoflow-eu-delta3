"""Device definition for EcoFlow PowerOcean (all-in-one home battery + inverter).

PowerOcean is EcoFlow's residential energy storage system, comparable to
Tesla Powerwall, Sessy, or Sonnen. A single PowerOcean unit combines:
  - LFP battery (modular, 5-15 kWh stackable)
  - Hybrid inverter (single or three-phase, up to 12 kW)
  - PV input (multiple MPPTs)
  - Smart meter integration for grid metering

PowerOcean Plus = larger commercial variant.
PowerOcean Fit = compact single-phase entry-level model.

PROTOCOL: Protobuf with multiple message types per cmdFunc:
  - cmdFunc=96, cmdId=1 → JTS1_EMS_HEARTBEAT (main telemetry, 200+ fields)
  - cmdFunc=254, cmdId=32 → EnergyTotalReport (energy statistics)
  - cmdFunc=224 → EcologyDevBindListReport (peripheral devices)
  - cmdFunc=240 → EDevBindListReport / EDevPriorityListReport
  - cmdFunc=241 → EDevParamReport
  - cmdFunc=53, cmdId=113 → ModuleClusterInfo

v0.3.10 STATUS: Minimal device registration only. Full protobuf decoder
routing for cmdFunc=96/254 not implemented — these will be added in v0.4.0
once test data from a PowerOcean owner is available. The sensor entities
defined here will activate automatically once decoder support lands.

SN PREFIXES: foxthefox does not document confirmed prefixes. Placeholders
chosen based on EcoFlow naming patterns and confirmed via product photos:
  - PO11: PowerOcean (single-phase)
  - PO31: PowerOcean (three-phase)
  - POPL: PowerOcean Plus
  - POFI: PowerOcean Fit

Source: foxthefox/ioBroker.ecoflow-mqtt (ef_powerocean_data.js,
        ef_poweroceanplus_data.js, ef_poweroceanfit_data.js)
"""
from __future__ import annotations

# ── Battery / EMS state ─────────────────────────────────────────────────────
KEY_BP_REMAIN_WATTH    = "bpRemainWatth"          # Battery remaining energy (Wh) — float
KEY_BP_DSG_TIME        = "bp_dsg_time"            # Battery discharge time (min)
KEY_DURA_TIME          = "dura_time"              # Estimated duration (min)
KEY_EMS_BP_POWER       = "emsBpPower"             # EMS battery power (W) — float
KEY_EMS_BP_CHG         = "emsBpChg"               # Battery charge power (W) — float
KEY_EMS_BP_DSG         = "emsBpDsg"               # Battery discharge power (W) — float
KEY_EMS_BP_ALIVE_NUM   = "emsBpAliveNum"          # Active battery modules
KEY_EMS_BUS_VOLT       = "emsBusVolt"             # EMS bus voltage (V) — float

# ── PCS (Power Conversion System / inverter) ────────────────────────────────
KEY_PCS_ACT_PWR        = "pcs_act_pwr"            # Inverter active power (W) — float
KEY_PCS_AC_FREQ        = "pcsAcFreq"              # AC frequency (Hz) — float
KEY_PCS_BUS_VOLT       = "pcsBusVolt"             # DC bus voltage (V) — float
KEY_PCS_LEAK_AMP       = "pcsLeakAmp"             # Leakage current (A) — float
KEY_PCS_DCI            = "pcsDci"                 # DC injection current (A) — float
KEY_PCS_BP_POWER       = "pcs_bp_power"           # Battery-PCS power (W) — float
KEY_PCS_METER_POWER    = "pcs_meter_power"        # Smart meter power (W) — float
KEY_PCS_AVG_VOLTAGE    = "pcs_average_voltage"    # Average AC voltage (V) — float
KEY_PCS_RELAY_STATE    = "pcsRelayStateShow"      # Inverter relay state

# ── Grid safety ─────────────────────────────────────────────────────────────
KEY_PCS_GRID_FUNC      = "pcsGridSafetyFuncRecord"   # Grid safety function code
KEY_PCS_GRID_STATE     = "pcsGridSafetyStateRecord"  # Grid safety state code

# ── Self-consumption / energy management ────────────────────────────────────
KEY_EMS_SELF_USED_CNT  = "emsSelfUsedCnt"            # Self-consumption counter
KEY_EMS_AC_MAKEUP_TRIG = "emsAcMakeupTriggleSoc"     # AC makeup trigger SOC (%)
KEY_EMS_AC_MAKEUP_EXIT = "emsAcMakeupExitSoc"        # AC makeup exit SOC (%)

DEVICE_MODEL = "PowerOcean"
