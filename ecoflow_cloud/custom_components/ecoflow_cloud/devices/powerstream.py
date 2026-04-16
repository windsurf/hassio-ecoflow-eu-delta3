"""Device definition for EcoFlow PowerStream (micro-inverter).

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/powerstream.py)
  - snell-evan-itt/hassio-ecoflow-cloud-US (confirmed)

Unique protocol — keys prefixed with 20_1.* (module addressing).
Commands use protobuf — not yet supported. Sensors are read-only.
"""
from __future__ import annotations

# Solar PV inputs
KEY_PV1_W        = "20_1.pv1InputWatts"
KEY_PV1_IN_VOLT  = "20_1.pv1InputVolt"
KEY_PV1_OP_VOLT  = "20_1.pv1OpVolt"
KEY_PV1_CURR     = "20_1.pv1InputCur"
KEY_PV1_TEMP     = "20_1.pv1Temp"
KEY_PV1_RELAY    = "20_1.pv1RelayStatus"
KEY_PV1_ERR      = "20_1.pv1ErrCode"
KEY_PV1_WARN     = "20_1.pv1WarnCode"

KEY_PV2_W        = "20_1.pv2InputWatts"
KEY_PV2_IN_VOLT  = "20_1.pv2InputVolt"
KEY_PV2_OP_VOLT  = "20_1.pv2OpVolt"
KEY_PV2_CURR     = "20_1.pv2InputCur"
KEY_PV2_TEMP     = "20_1.pv2Temp"
KEY_PV2_RELAY    = "20_1.pv2RelayStatus"
KEY_PV2_ERR      = "20_1.pv2ErrCode"
KEY_PV2_WARN     = "20_1.pv2WarnCode"

# Battery
KEY_BAT_SOC      = "20_1.batSoc"
KEY_BAT_W        = "20_1.batInputWatts"
KEY_BAT_IN_VOLT  = "20_1.batInputVolt"
KEY_BAT_OP_VOLT  = "20_1.batOpVolt"
KEY_BAT_CURR     = "20_1.batInputCur"
KEY_BAT_TEMP     = "20_1.batTemp"
KEY_BAT_CHG_T    = "20_1.chgRemainTime"
KEY_BAT_DSG_T    = "20_1.dsgRemainTime"
KEY_BAT_ERR      = "20_1.batErrCode"
KEY_BAT_WARN     = "20_1.batWarningCode"
KEY_BAT_TYPE     = "20_1.bpType"

# Inverter
KEY_INV_ON       = "20_1.invOnOff"
KEY_INV_W        = "20_1.invOutputWatts"
KEY_INV_OUT_VOLT = "20_1.invOutputVolt"
KEY_INV_OP_VOLT  = "20_1.invOpVolt"
KEY_INV_CURR     = "20_1.invOutputCur"
KEY_INV_DC_CURR  = "20_1.invDcCur"
KEY_INV_FREQ     = "20_1.invFreq"
KEY_INV_TEMP     = "20_1.invTemp"
KEY_INV_RELAY    = "20_1.invRelayStatus"
KEY_INV_ERR      = "20_1.invErrCode"
KEY_INV_WARN     = "20_1.invWarnCode"

# LLC
KEY_LLC_IN_VOLT  = "20_1.llcInputVolt"
KEY_LLC_OP_VOLT  = "20_1.llcOpVolt"
KEY_LLC_TEMP     = "20_1.llcTemp"

# System
KEY_ESP_TEMP     = "20_1.espTempsensor"
KEY_OTHER_LOADS  = "20_1.dynamicWatts"
KEY_SMART_LOADS  = "20_1.feedProtect"
KEY_RATED_POWER  = "20_1.ratedPower"
KEY_LOWER_LIMIT  = "20_1.lowerLimit"
KEY_UPPER_LIMIT  = "20_1.upperLimit"
KEY_BRIGHTNESS   = "20_1.invBrightness"
KEY_HEARTBEAT    = "20_1.heartbeatFrequency"
KEY_WIRELESS_ERR = "20_1.wirelessErrCode"
KEY_WIRELESS_WARN = "20_1.wirelessWarnCode"
KEY_SUPPLY_PRIO  = "20_1.supplyPriority"

DEVICE_MODEL = "PowerStream"
