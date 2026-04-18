"""Device definition for EcoFlow Delta 3 Plus (SN prefix D362).

The Delta 3 Plus is the larger sibling of the Delta 3 1500: same core
JSON telemetry protocol, identical command set, but with an extra PV2
MPPT input and slightly higher capacity.

Source mapping strategy:
  - Command builders are IDENTICAL to Delta 3 1500 — no duplicates needed.
  - Telemetry keys reuse Delta 3 1500 dotted-prefix keys where applicable.
  - PV2-specific keys are added here as module.key strings.

Extra fields vs Delta 3 1500 (from foxthefox ef_delta3plus_data.js):
  - powGetPv2, tempPv2, flowInfoPv2
  - plugInInfoPv2* (10 keys: voltage, current, flag, charger, limits, etc.)

Key-prefix reasoning: Delta 3 1500 uses "inv." for AC/DC power values
and "mppt." for solar-specific keys. We follow the same convention.
Until live telemetry dumps are available, these are marked
`entity_registry_enabled_default=False` in sensor.py so users can
opt-in once they've confirmed the actual keys in their HA logs.

Source: foxthefox/ioBroker.ecoflow-mqtt (ef_delta3plus_data.js)
"""
from __future__ import annotations

# Re-export all Delta 3 1500 keys so platform files can import them
# uniformly. Plus uses the same command builders, same JSON envelope,
# same BMS structure — only the sensor set differs.
from .delta3_1500 import *  # noqa: F401, F403

# ══════════════════════════════════════════════════════════════════════════════
# Delta 3 Plus — additional PV2 (second MPPT input) sensor keys
# ══════════════════════════════════════════════════════════════════════════════

# ── Solar PV2 input (second MPPT channel — Plus/Max exclusive) ──────────────
KEY_PV2_POWER       = "mppt.powGetPv2"             # PV2 input power           (W)
KEY_PV2_TEMP        = "mppt.tempPv2"               # PV2 controller temp       (°C)
KEY_PV2_FLOW_INFO   = "mppt.flowInfoPv2"           # PV2 flow status           (int)
KEY_PV2_VOLT        = "mppt.plugInInfoPv2Vol"      # PV2 input voltage         (V)
KEY_PV2_CURR        = "mppt.plugInInfoPv2Amp"      # PV2 input current         (A)
KEY_PV2_FLAG        = "mppt.plugInInfoPv2Flag"     # PV2 connected (0/1)
KEY_PV2_TYPE        = "mppt.plugInInfoPv2Type"     # PV2 source type
KEY_PV2_CHG_FLAG    = "mppt.plugInInfoPv2ChargerFlag"  # PV2 charger state
KEY_PV2_CHG_V_MAX   = "mppt.plugInInfoPv2ChgVolMax"    # PV2 max charge volt   (V)
KEY_PV2_CHG_A_MAX   = "mppt.plugInInfoPv2ChgAmpMax"    # PV2 max charge amp    (A)
KEY_PV2_DC_A_MAX    = "mppt.plugInInfoPv2DcAmpMax"     # PV2 DC max current    (A)

DEVICE_MODEL = "Delta 3 Plus"
