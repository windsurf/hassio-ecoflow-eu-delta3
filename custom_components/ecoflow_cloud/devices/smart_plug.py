"""Device definition for EcoFlow Smart Plug.

MQTT key sources:
  - tolwi/hassio-ecoflow-cloud (internal/smart_plug.py + proto/smartplug.proto)

Uses protobuf protocol (cmdFunc=2). Telemetry via WnPlugHeartbeatPack.
Commands: switch on/off (cmdId=129), brightness (cmdId=130), max watts (cmdId=137).

NOTE: Sensor telemetry requires protobuf decoder in on_message handler.
Commands work via proto_builder_sn (binary MQTT SET).
"""
from __future__ import annotations

# Heartbeat sensor keys (flat — no prefix, from WnPlugHeartbeatPack)
KEY_TEMP         = "temp"
KEY_VOLT         = "volt"
KEY_CURRENT      = "current"
KEY_WATTS        = "watts"
KEY_FREQ         = "freq"
KEY_MAX_CUR      = "maxCur"
KEY_SWITCH_STA   = "switchSta"
KEY_BRIGHTNESS   = "brightness"
KEY_MAX_WATTS    = "maxWatts"
KEY_ERR_CODE     = "errCode"
KEY_WARN_CODE    = "warnCode"

DEVICE_MODEL = "Smart Plug"
