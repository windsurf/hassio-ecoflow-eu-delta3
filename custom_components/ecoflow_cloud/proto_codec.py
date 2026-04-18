"""
Pure-Python protobuf encoder for EcoFlow Delta 3 MQTT commands.

The Delta 3 series (D361/D371) uses protobuf-encoded binary messages on the
/set and /get topics instead of the JSON format used by older devices.

Wire format derived from:
  - nalditopr gist (Delta 3 Node-Red flow): github.com/nalditopr/493af377e9928b88c2639a9e1607f127
  - foxthefox ioBroker.ecoflow-mqtt: github.com/foxthefox/ioBroker.ecoflow-mqtt

Message structure (reverse-engineered):
    root {
      field 1 (LEN) = subMessage {          # outer wrapper
        field 1 (LEN) = innerMessage {      # command payload
          ... command-specific fields ...
        }
        field 2  (varint) = 32              # static
        field 3  (varint) = 2               # static
        field 4  (varint) = 1               # static
        field 5  (varint) = 1               # static
        field 8  (varint) = 254             # static
        field 9  (varint) = 17              # static
        field 10 (varint) = <operate_code>  # command selector
        field 11 (varint) = 1               # static
        field 14 (varint) = <cmd_id>        # timestamp (32-bit, epoch seconds)
        field 15 (varint) = 1               # static
        field 16 (varint) = 19              # static
        field 17 (varint) = 1               # static
      }
    }

Operate codes (gist + foxthefox analysis):
    0  = get (property poll, session initiation)
    2  = beep / quietMode
    3  = general: charge target, ac_charging, mpptCar, acOutCfg, acChgCfg
    11 = self-powered on (complex inner)
"""
from __future__ import annotations

import struct
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Wire encoding primitives
# ---------------------------------------------------------------------------

def _varint(v: int) -> bytes:
    """Encode integer as protobuf varint (little-endian 7-bit groups)."""
    v = v & 0xFFFFFFFF   # clamp to 32-bit unsigned
    buf: list[int] = []
    while True:
        byte = v & 0x7F
        v >>= 7
        if v:
            buf.append(byte | 0x80)
        else:
            buf.append(byte)
            break
    return bytes(buf)


def _fv(field_num: int, value: int) -> bytes:
    """Encode varint field: tag(wire=0) + value."""
    return _varint((field_num << 3) | 0) + _varint(value & 0xFFFFFFFF)


def _fb(field_num: int, data: bytes) -> bytes:
    """Encode length-delimited field: tag(wire=2) + length + data."""
    return _varint((field_num << 3) | 2) + _varint(len(data)) + data


def _fs(field_num: int, text: str) -> bytes:
    """Encode string field (UTF-8)."""
    return _fb(field_num, text.encode("utf-8"))


# ---------------------------------------------------------------------------
# GET command (session initiation + keepalive)
# ---------------------------------------------------------------------------

# Session IDs observed in nalditopr gist (field 14 of inner GET message).
# These appear to be app-instance identifiers; we use a fixed value derived
# from the device serial to stay consistent across restarts.
_GET_APP_ID = 128301330


def build_get(cmd_id: Optional[int] = None) -> bytes:
    """
    Build a protobuf GET message (session ping / property request).

    The APP sends this every ~15 s. Sending it allows the device to
    recognise our MQTT session as an active app session and accept
    subsequent set-commands.

    Structure:
        root { field1 { field1 { field14=<app_id> field23="Android" } } }
    """
    if cmd_id is None:
        cmd_id = int(time.time()) & 0xFFFFFFFF
    inner = _fv(14, _GET_APP_ID) + _fs(23, "Android")
    outer = _fb(1, inner)
    return _fb(1, outer)


# ---------------------------------------------------------------------------
# SET command wrapper
# ---------------------------------------------------------------------------

def _wrap_cmd(inner_fields: bytes, operate_code: int, cmd_id: int) -> bytes:
    """Wrap inner command fields in the standard Delta 3 outer envelope."""
    outer = (
        _fb(1, inner_fields) +          # NestedsubMesssage_1
        _fv(2, 32) + _fv(3, 2) + _fv(4, 1) + _fv(5, 1) +
        _fv(8, 254) + _fv(9, 17) +
        _fv(10, operate_code) +
        _fv(11, 1) +
        _fv(14, cmd_id & 0xFFFFFFFF) +
        _fv(15, 1) + _fv(16, 19) + _fv(17, 1)
    )
    return _fb(1, outer)


# ---------------------------------------------------------------------------
# Command builders  (operate_codes from nalditopr gist + foxthefox)
# ---------------------------------------------------------------------------

def _ts() -> int:
    return int(time.time()) & 0xFFFFFFFF


def build_ac_output(enabled: bool) -> bytes:
    """AC output ON/OFF — operate_code 3, inner field 2 (acOut)."""
    # Field 2 in inner = acOut (0/1)
    inner = _fv(2, 1 if enabled else 0)
    return _wrap_cmd(inner, 3, _ts())

def build_xboost(enabled: bool) -> bytes:
    """X-Boost ON/OFF — operate_code 3, inner field 1 (xboost).
    
    X-Boost is a separate field within the same acOutCfg operate_code (3).
    Inner field 1 = xboost enable (0/1).
    Field assignment derived from nalditopr gist acOutCfg structure.
    """
    inner = _fv(1, 1 if enabled else 0)
    return _wrap_cmd(inner, 3, _ts())


def build_dc_output(enabled: bool) -> bytes:
    """DC/car output ON/OFF — operate_code 3, inner field 3."""
    inner = _fv(3, 1 if enabled else 0)
    return _wrap_cmd(inner, 3, _ts())


def build_ac_charging(enabled: bool) -> bytes:
    """AC charging pause ON/OFF — operate_code 3, inner field 5."""
    # field 5 = chgPauseFlag: 0 = charging active, 1 = paused
    inner = _fv(5, 0 if enabled else 1)
    return _wrap_cmd(inner, 3, _ts())


def build_beep(enabled: bool) -> bytes:
    """Beep sound ON/OFF — operate_code 2, inner field 9.

    foxthefox correction (ioBroker.ecoflow-mqtt): enBeep requires dataLen=2,
    meaning the field must be length-delimited (wire=2) with a 2-byte payload:
    one byte for the value (0/1) and one padding byte (0x00).
    Encoding as a plain varint (wire=0) is silently rejected by the device.
    """
    # field 9, wire=2 (length-delimited), data = [value, 0x00] (2 bytes)
    val = 1 if enabled else 0
    data = bytes([val, 0x00])
    inner = _fb(9, data)
    return _wrap_cmd(inner, 2, _ts())


def build_ups_mode(enabled: bool) -> bytes:
    """UPS mode ON/OFF — operate_code 3, inner field 8."""
    inner = _fv(8, 1 if enabled else 0)
    return _wrap_cmd(inner, 3, _ts())


def build_charge_target(soc: int) -> bytes:
    """Charge target % (15–100) — operate_code 3, inner field 102."""
    soc = max(15, min(100, int(soc)))
    inner = _fv(102, soc)
    return _wrap_cmd(inner, 3, _ts())


# ---------------------------------------------------------------------------
# PowerStream protobuf command builders
# ---------------------------------------------------------------------------
#
# PowerStream uses a different envelope than Delta 3.  The outer message is
# PowerStreamSendHeaderMsg (proto schema in tolwi/powerstream.proto).
#
# Header fields (PowerStreamHeader — field numbers from .proto):
#   1  pdata (bytes)      — serialized inner payload
#   2  src (int32)        — 32 (APP)
#   3  dest (int32)       — 53 (MQTT)
#   4  d_src (int32)      — 1
#   5  d_dest (int32)     — 1
#   7  check_type (int32) — 3
#   8  cmd_func (int32)   — 20
#   9  cmd_id (int32)     — per command
#  10  data_len (int32)   — len(pdata)
#  11  need_ack (int32)   — 1
#  14  seq (int32)        — timestamp
#  16  version (int32)    — 19
#  17  payload_ver (int32) — 1
#  23  from_ (string)     — "HomeAssistant"
#  25  device_sn (string) — serial number
#
# PowerStreamSendHeaderMsg wraps one header in repeated field 1.
#
# All inner payloads are a single varint at field 1.
# Source: tolwi/powerstream.proto + internal/powerstream.py Command enum.

# Command IDs (cmd_func=20 for all)
PS_CMD_PERMANENT_WATTS = 129   # output limit (deciWatts)
PS_CMD_SUPPLY_PRIORITY = 130   # 0=supply first, 1=storage first
PS_CMD_BAT_LOWER       = 132   # battery lower limit %
PS_CMD_BAT_UPPER       = 133   # battery upper limit %
PS_CMD_BRIGHTNESS      = 135   # LED brightness 0-1023
PS_CMD_FEED_PROTECT    = 143   # feed-in control 0/1

# Address constants
_PS_SRC_APP  = 32
_PS_DEST_MQTT = 53


def _ps_header(cmd_id: int, pdata: bytes, device_sn: str) -> bytes:
    """Build a PowerStreamHeader protobuf message."""
    seq = _ts()
    header = (
        _fb(1, pdata) +             # pdata
        _fv(2, _PS_SRC_APP) +       # src = APP
        _fv(3, _PS_DEST_MQTT) +     # dest = MQTT
        _fv(4, 1) +                 # d_src
        _fv(5, 1) +                 # d_dest
        _fv(7, 3) +                 # check_type
        _fv(8, 20) +                # cmd_func
        _fv(9, cmd_id) +            # cmd_id
        _fv(10, len(pdata)) +       # data_len
        _fv(11, 1) +                # need_ack
        _fv(14, seq) +              # seq (timestamp)
        _fv(16, 19) +               # version
        _fv(17, 1) +                # payload_ver
        _fs(23, "HomeAssistant") +   # from_
        _fs(25, device_sn)           # device_sn
    )
    return header


def _ps_wrap(cmd_id: int, pdata: bytes, device_sn: str) -> bytes:
    """Wrap a PowerStream command in SendHeaderMsg (repeated field 1)."""
    header = _ps_header(cmd_id, pdata, device_sn)
    # PowerStreamSendHeaderMsg: field 1 (LEN) = header
    return _fb(1, header)


def ps_build_permanent_watts(watts: int, device_sn: str) -> bytes:
    """Set output limit (permanentWatts) in deciWatts.

    The EcoFlow app sends this value in deciWatts (watts * 10).
    E.g. 200W → value=2000.  Range: 0–800 (PowerStream 800W).
    """
    deci = max(0, int(watts * 10))
    pdata = _fv(1, deci)
    return _ps_wrap(PS_CMD_PERMANENT_WATTS, pdata, device_sn)


def ps_build_supply_priority(priority: int, device_sn: str) -> bytes:
    """Set power supply priority.

    0 = Prioritize power supply (feed into household first)
    1 = Prioritize power storage (charge battery first)
    """
    pdata = _fv(1, int(priority))
    return _ps_wrap(PS_CMD_SUPPLY_PRIORITY, pdata, device_sn)


def ps_build_bat_lower(limit: int, device_sn: str) -> bytes:
    """Set battery lower discharge limit (0–30%)."""
    limit = max(0, min(30, int(limit)))
    pdata = _fv(1, limit)
    return _ps_wrap(PS_CMD_BAT_LOWER, pdata, device_sn)


def ps_build_bat_upper(limit: int, device_sn: str) -> bytes:
    """Set battery upper charge limit (50–100%)."""
    limit = max(50, min(100, int(limit)))
    pdata = _fv(1, limit)
    return _ps_wrap(PS_CMD_BAT_UPPER, pdata, device_sn)


def ps_build_brightness(level: int, device_sn: str) -> bytes:
    """Set LED brightness (0–1023)."""
    level = max(0, min(1023, int(level)))
    pdata = _fv(1, level)
    return _ps_wrap(PS_CMD_BRIGHTNESS, pdata, device_sn)


def ps_build_feed_protect(enabled: bool, device_sn: str) -> bytes:
    """Set feed-in control ON/OFF."""
    pdata = _fv(1, 1 if enabled else 0)
    return _ps_wrap(PS_CMD_FEED_PROTECT, pdata, device_sn)


# ---------------------------------------------------------------------------
# Smart Plug protobuf command builders
# ---------------------------------------------------------------------------
#
# Smart Plug uses the same envelope structure as PowerStream but with:
#   cmdFunc = 2 (CMD_FUNC_WN_SMART_PLUG)
#   src = 32 (APP), dest = 53 (MQTT)
#
# Source: tolwi/smartplug.proto + internal/smart_plug.py
#
# Command IDs (cmdFunc=2 for all):
#   129 = switch on/off (WnPlugSwitchMessage: field 1 = bool)
#   130 = brightness (WnBrightnessPack: field 1 = int32)
#   137 = max watts (WnMaxWattsPack: field 1 = int32)

SP_CMD_FUNC      = 2
SP_CMD_SWITCH    = 129
SP_CMD_BRIGHTNESS = 130
SP_CMD_MAX_WATTS = 137


def _sp_header(cmd_id: int, pdata: bytes, device_sn: str) -> bytes:
    """Build a SmartPlugHeader protobuf message."""
    seq = _ts()
    header = (
        _fb(1, pdata) +             # pdata
        _fv(2, _PS_SRC_APP) +       # src = APP (32)
        _fv(3, _PS_DEST_MQTT) +     # dest = MQTT (53)
        _fv(8, SP_CMD_FUNC) +       # cmdFunc = 2
        _fv(9, cmd_id) +            # cmdId
        _fv(10, len(pdata)) +       # dataLen
        _fv(11, 1) +                # needAck
        _fv(14, seq) +              # seq (timestamp)
        _fs(25, device_sn)           # deviceSn
    )
    return header


def _sp_wrap(cmd_id: int, pdata: bytes, device_sn: str) -> bytes:
    """Wrap a Smart Plug command in SendSmartPlugHeaderMsg (repeated field 1)."""
    header = _sp_header(cmd_id, pdata, device_sn)
    return _fb(1, header)


def sp_build_switch(enabled: bool, device_sn: str) -> bytes:
    """Switch Smart Plug ON/OFF."""
    # WnPlugSwitchMessage: field 1 = bool (varint 0/1)
    pdata = _fv(1, 1 if enabled else 0)
    return _sp_wrap(SP_CMD_SWITCH, pdata, device_sn)


def sp_build_brightness(level: int, device_sn: str) -> bytes:
    """Set Smart Plug LED brightness (0–1023)."""
    level = max(0, min(1023, int(level)))
    pdata = _fv(1, level)
    return _sp_wrap(SP_CMD_BRIGHTNESS, pdata, device_sn)


def sp_build_max_watts(watts: int, device_sn: str) -> bytes:
    """Set Smart Plug max power limit (0–2500W)."""
    watts = max(0, min(2500, int(watts)))
    pdata = _fv(1, watts)
    return _sp_wrap(SP_CMD_MAX_WATTS, pdata, device_sn)


# ---------------------------------------------------------------------------
# Stream AC / AC Pro / Ultra protobuf command builders
# ---------------------------------------------------------------------------
#
# The Stream AC family uses the same Delta 3 protobuf envelope (cmdFunc=254)
# but with different inner field numbers mapped to the ConfigWrite schema.
#
# Envelope (setMessage > setHeader):
#   src=32, dest=2, dSrc=1, dDest=1, cmdFunc=254, cmdId=17
#   productId=56, version=3, payloadVer=1
#
# The ConfigWrite pdata always includes cfgUtcTime (field 6) as a timestamp.
# Additional fields depend on the command.
#
# Source: foxthefox/ioBroker.ecoflow-mqtt ef_stream_inverter_data.js prepareProtoCmd
#

from .devices.stream_ac import (
    CMD_UTC_TIME_FIELD, CMD_RELAY2_FIELD, CMD_RELAY3_FIELD,
    CMD_MAX_CHG_SOC_FIELD, CMD_MIN_DSG_SOC_FIELD, CMD_BACKUP_SOC_FIELD,
    CMD_FEED_LIMIT_FIELD, CMD_BRIGHTNESS_FIELD,
)

# Stream AC envelope constants (same as Delta 3 but with productId/version)
_STREAM_SRC     = 32
_STREAM_DEST    = 2
_STREAM_D_SRC   = 1
_STREAM_D_DEST  = 1
_STREAM_CMD_FUNC = 254
_STREAM_CMD_ID  = 17


def _stream_wrap_cmd(pdata_fields: bytes) -> bytes:
    """Wrap ConfigWrite pdata in Stream AC setMessage protobuf envelope.

    Structure (from foxthefox prepareProtoCmd):
        setMessage {
          header {                  (field 1 = LEN)
            pdata: ConfigWrite      (field 1 = LEN)
            src: 32                 (field 2)
            dest: 2                 (field 3)
            dSrc: 1                 (field 4)
            dDest: 1                (field 5)
            cmdFunc: 254            (field 8)
            cmdId: 17               (field 9)
            dataLen: <len>          (field 10)
            needAck: 1              (field 11)
            seq: <timestamp_ms>     (field 14)
            productId: 56           (field 15)
            version: 3              (field 16)
            payloadVer: 1           (field 17)
            from: "Android"         (field 23)
          }
        }
    """
    seq = int(time.time() * 1000) & 0xFFFFFFFF  # milliseconds
    header = (
        _fb(1, pdata_fields) +
        _fv(2, _STREAM_SRC) +
        _fv(3, _STREAM_DEST) +
        _fv(4, _STREAM_D_SRC) +
        _fv(5, _STREAM_D_DEST) +
        _fv(8, _STREAM_CMD_FUNC) +
        _fv(9, _STREAM_CMD_ID) +
        _fv(10, len(pdata_fields)) +
        _fv(11, 1) +
        _fv(14, seq) +
        _fv(15, 56) +              # productId
        _fv(16, 3) +               # version
        _fv(17, 1) +               # payloadVer
        _fs(23, "Android")
    )
    return _fb(1, header)


def _stream_pdata_with_timestamp(*field_pairs: tuple[int, int]) -> bytes:
    """Build ConfigWrite pdata with cfgUtcTime + additional fields.

    Always includes cfgUtcTime (field 6) as unix timestamp.
    Additional fields are (field_num, value) tuples.
    """
    ts = int(time.time()) & 0xFFFFFFFF
    pdata = _fv(CMD_UTC_TIME_FIELD, ts)
    for field_num, value in field_pairs:
        pdata += _fv(field_num, int(value))
    return pdata


def stream_build_relay2(enabled: bool) -> bytes:
    """Toggle AC output relay #1 (relay2Onoff) — ConfigWrite field 380."""
    pdata = _stream_pdata_with_timestamp(
        (CMD_RELAY2_FIELD, 1 if enabled else 0),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_relay3(enabled: bool) -> bytes:
    """Toggle AC output relay #2 (relay3Onoff) — ConfigWrite field 381."""
    pdata = _stream_pdata_with_timestamp(
        (CMD_RELAY3_FIELD, 1 if enabled else 0),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_max_chg_soc(soc: int, current_min_dsg_soc: int = 5) -> bytes:
    """Set max charge SOC (%) — ConfigWrite fields 33 + 34.

    Both cmsMaxChgSoc and cmsMinDsgSoc must be sent together
    (foxthefox: dataLen=12, both fields required).
    """
    soc = max(5, min(100, int(soc)))
    pdata = _stream_pdata_with_timestamp(
        (CMD_MAX_CHG_SOC_FIELD, soc),
        (CMD_MIN_DSG_SOC_FIELD, int(current_min_dsg_soc)),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_min_dsg_soc(soc: int, current_max_chg_soc: int = 100) -> bytes:
    """Set min discharge SOC (%) — ConfigWrite fields 34 + 33.

    Both cmsMinDsgSoc and cmsMaxChgSoc must be sent together.
    """
    soc = max(0, min(30, int(soc)))
    pdata = _stream_pdata_with_timestamp(
        (CMD_MAX_CHG_SOC_FIELD, int(current_max_chg_soc)),
        (CMD_MIN_DSG_SOC_FIELD, soc),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_backup_soc(soc: int) -> bytes:
    """Set backup reserve SOC (%) — ConfigWrite field 102."""
    soc = max(0, min(100, int(soc)))
    pdata = _stream_pdata_with_timestamp(
        (CMD_BACKUP_SOC_FIELD, soc),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_feed_limit(watts: int) -> bytes:
    """Set grid feed-in power limit (W) — ConfigWrite field 169."""
    watts = max(0, min(800, int(watts)))
    pdata = _stream_pdata_with_timestamp(
        (CMD_FEED_LIMIT_FIELD, watts),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_brightness(level: int) -> bytes:
    """Set display brightness — ConfigWrite field 384."""
    level = max(0, min(100, int(level)))
    pdata = _stream_pdata_with_timestamp(
        (CMD_BRIGHTNESS_FIELD, level),
    )
    return _stream_wrap_cmd(pdata)


def stream_build_latest_quotas() -> bytes:
    """Build a minimal Stream AC session ping (latestQuotas).

    Source: foxthefox/ioBroker.ecoflow-mqtt ef_stream_inverter_data.js
      prepareProtoCmd() — when state === 'latestQuotas':

        muster = {
          header: {
            src: 32,
            dest: 32,
            seq: Date.now(),
            from: 'ios',
          }
        }

    This message has NO pdata, NO cmdFunc, NO cmdId — it is a minimal
    keep-alive that signals "I am an active app session" to the device.
    Without this ping, Stream AC may stop publishing DisplayPropertyUpload
    telemetry after a short idle period.

    Structure (protobuf wire format):
        setMessage {
          header {                  (field 1 = LEN)
            src: 32                 (field 2)
            dest: 32                (field 3)
            seq: <timestamp_ms>     (field 14)
            from: "ios"             (field 23)
          }
        }

    Note: dest=32 (app-to-app loopback style) — NOT dest=2 like command messages.
    """
    seq = int(time.time() * 1000) & 0xFFFFFFFF  # milliseconds
    header = (
        _fv(2, _STREAM_SRC) +          # src = 32
        _fv(3, _STREAM_SRC) +          # dest = 32 (not 2!)
        _fv(14, seq) +
        _fs(23, "ios")
    )
    return _fb(1, header)




# ---------------------------------------------------------------------------
# Protobuf telemetry DECODER — parse binary MQTT push into coordinator data
# ---------------------------------------------------------------------------
#
# EcoFlow protobuf telemetry structure (reverse-engineered):
#
#   PowerStream / Smart Plug use a header-wrapped format:
#     root {
#       field 1 (LEN) = header {
#         field 1 (LEN)  = pdata (serialized heartbeat payload)
#         field 2 (VAR)  = src        (32=APP, 2=device)
#         field 3 (VAR)  = dest       (32=APP, 53=MQTT)
#         field 8 (VAR)  = cmd_func   (20=PowerStream, 2=SmartPlug)
#         field 9 (VAR)  = cmd_id     (1=heartbeat, 129..137=commands)
#         ...
#       }
#     }
#
#   The pdata contains the actual sensor values as varint fields.
#
# Sources:
#   - tolwi/hassio-ecoflow-cloud (proto/powerstream.proto, internal/smart_plug.py)
#   - foxthefox/ioBroker.ecoflow-mqtt (protobuf decoding, field analysis)
#   - moifort (GitHub issue #136, Smart Plug proto definition)
#

import logging as _logging

_DECODE_LOGGER = _logging.getLogger(__name__)


def _parse_fields(data: bytes) -> dict[int, int | bytes]:
    """Parse protobuf wire-format into {field_num: value} dict.

    Handles wire type 0 (varint) and wire type 2 (length-delimited).
    For varint fields, value is int. For LEN fields, value is bytes.
    Duplicate field numbers: last value wins (consistent with protobuf spec).
    """
    fields: dict[int, int | bytes] = {}
    pos = 0
    try:
        while pos < len(data):
            tag, pos = _read_varint(data, pos)
            field_num = tag >> 3
            wire_type = tag & 0x07
            if wire_type == 0:  # varint
                val, pos = _read_varint(data, pos)
                fields[field_num] = val
            elif wire_type == 2:  # length-delimited
                length, pos = _read_varint(data, pos)
                fields[field_num] = data[pos:pos + length]
                pos += length
            elif wire_type == 5:  # 32-bit fixed
                fields[field_num] = int.from_bytes(data[pos:pos + 4], "little")
                pos += 4
            elif wire_type == 1:  # 64-bit fixed
                fields[field_num] = int.from_bytes(data[pos:pos + 8], "little")
                pos += 8
            else:
                break  # unknown wire type — stop parsing
    except Exception:
        pass  # partial parse is OK — return what we got
    return fields


def _extract_header(raw: bytes) -> dict[str, int | bytes] | None:
    """Extract header fields from EcoFlow protobuf envelope.

    Returns dict with keys: pdata, src, dest, cmd_func, cmd_id, data_len, seq.
    Returns None if the envelope cannot be parsed.
    """
    root = _parse_fields(raw)
    header_bytes = root.get(1)
    if not isinstance(header_bytes, bytes):
        return None

    hdr = _parse_fields(header_bytes)
    pdata = hdr.get(1)
    if not isinstance(pdata, bytes):
        return None

    return {
        "pdata":    pdata,
        "src":      hdr.get(2, 0),
        "dest":     hdr.get(3, 0),
        "cmd_func": hdr.get(8, 0),
        "cmd_id":   hdr.get(9, 0),
        "data_len": hdr.get(10, 0),
        "seq":      hdr.get(14, 0),
    }


# ---------------------------------------------------------------------------
# Field mappings: protobuf field number → coordinator key
# ---------------------------------------------------------------------------
# These map the varint field numbers inside the pdata (heartbeat payload)
# to the flat key names used by coordinator.data and sensor.py descriptions.

# PowerStream inverter_heartbeat (cmd_func=20, cmd_id=1)
# Source: tolwi powerstream.proto, foxthefox inverter_heartbeat definition
_PS_HEARTBEAT_FIELDS: dict[int, str] = {
    1:  "20_1.pv1ErrCode",
    2:  "20_1.pv1WarnCode",
    3:  "20_1.pv1Status",
    4:  "20_1.pv2ErrCode",
    5:  "20_1.pv2WarningCode",
    6:  "20_1.pv2Status",
    7:  "20_1.batErrCode",
    8:  "20_1.batWarningCode",
    9:  "20_1.llcErrCode",
    10: "20_1.llcWarningCode",
    11: "20_1.pv1InputWatts",
    12: "20_1.pv1OpVolt",
    13: "20_1.pv1InputCur",
    14: "20_1.pv1InputVolt",
    15: "20_1.pv1Temp",
    16: "20_1.pv1RelayStatus",
    17: "20_1.pv2InputWatts",
    18: "20_1.pv2OpVolt",
    19: "20_1.pv2InputCur",
    20: "20_1.pv2InputVolt",
    21: "20_1.pv2Temp",
    22: "20_1.pv2RelayStatus",
    23: "20_1.batInputWatts",
    24: "20_1.batInputVolt",
    25: "20_1.batOpVolt",
    26: "20_1.batInputCur",
    27: "20_1.batTemp",
    29: "20_1.batSoc",
    30: "20_1.invOnOff",
    31: "20_1.invOutputWatts",
    32: "20_1.invOutputCur",
    33: "20_1.invOutputVolt",
    34: "20_1.invDcCur",
    35: "20_1.invFreq",
    36: "20_1.invTemp",
    37: "20_1.invRelayStatus",
    38: "20_1.invErrCode",
    39: "20_1.invWarnCode",
    40: "20_1.llcInputVolt",
    41: "20_1.llcOpVolt",
    42: "20_1.llcTemp",
    43: "20_1.chgRemainTime",
    44: "20_1.dsgRemainTime",
    46: "20_1.bpType",
    47: "20_1.invOpVolt",
    48: "20_1.espTempsensor",
    49: "20_1.ratedPower",
    50: "20_1.dynamicWatts",
    51: "20_1.supplyPriority",
    52: "20_1.lowerLimit",
    53: "20_1.upperLimit",
    54: "20_1.invBrightness",
    55: "20_1.heartbeatFrequency",
    56: "20_1.wirelessErrCode",
    57: "20_1.wirelessWarnCode",
    58: "20_1.feedProtect",
}

# Smart Plug heartbeat (cmd_func=2, cmd_id=2 or 1)
# Source: tolwi smartplug.proto (WnPlugHeartbeatPack), foxthefox plug data
# Keys are flat (no prefix) — matching smart_plug.py device definition
_SP_HEARTBEAT_FIELDS: dict[int, str] = {
    1:  "watts",
    2:  "volt",
    3:  "current",
    4:  "temp",
    5:  "freq",
    6:  "maxCur",
    7:  "switchSta",
    8:  "brightness",
    9:  "maxWatts",
    10: "errCode",
    11: "warnCode",
}

# cmdFunc → field mapping table
_HEARTBEAT_DECODERS: dict[int, dict[int, str]] = {
    20: _PS_HEARTBEAT_FIELDS,   # PowerStream
    2:  _SP_HEARTBEAT_FIELDS,   # Smart Plug
}

# cmdFunc → human-readable label for logging
_CMD_FUNC_NAMES: dict[int, str] = {
    20: "PowerStream",
    2:  "SmartPlug",
    254: "StreamAC",
}

# Stream AC uses cmdFunc=254 with multiple cmdIds for different message types.
# We need a (cmdFunc, cmdId) → field_map lookup for these.
from .devices.stream_ac import DISPLAY_FIELDS as _SA_DISPLAY_FIELDS
from .devices.stream_ac import RUNTIME_FIELDS as _SA_RUNTIME_FIELDS
from .devices.stream_ac import FLOAT_FIELDS as _SA_FLOAT_FIELDS
from .devices.stream_ac import CONFIG_ACK_FIELDS as _SA_CONFIG_ACK_FIELDS

# (cmdFunc, cmdId) → (field_map, float_fields_set)
_STREAM_AC_DECODERS: dict[tuple[int, int], tuple[dict[int, str], set[int]]] = {
    (254, 21): (_SA_DISPLAY_FIELDS, _SA_FLOAT_FIELDS),    # DisplayPropertyUpload
    (254, 22): (_SA_RUNTIME_FIELDS, set()),                # RuntimePropertyUpload
    (254, 18): (_SA_CONFIG_ACK_FIELDS, set()),             # ConfigWriteAck — confirms SET values
}


def _decode_float_bits(raw_int: int) -> float:
    """Convert raw 32-bit integer (from wire type 5) to IEEE 754 float."""
    try:
        return struct.unpack('<f', struct.pack('<I', raw_int & 0xFFFFFFFF))[0]
    except (struct.error, OverflowError):
        return 0.0


def decode_proto_telemetry(raw: bytes) -> dict[str, int | float] | None:
    """Decode a protobuf telemetry message into coordinator-compatible dict.

    Returns {coordinator_key: value} for known heartbeat messages.
    Returns None if the message is not a recognized heartbeat or cannot be parsed.

    Supports:
      - PowerStream (cmdFunc=20, all cmdIds)
      - Smart Plug (cmdFunc=2, all cmdIds)
      - Stream AC (cmdFunc=254, cmdId=21 DisplayPropertyUpload, cmdId=22 RuntimePropertyUpload)
    """
    header = _extract_header(raw)
    if header is None:
        _DECODE_LOGGER.debug("proto decode: envelope parse failed")
        return None

    cmd_func = header["cmd_func"]
    cmd_id = header["cmd_id"]
    pdata = header["pdata"]
    device_name = _CMD_FUNC_NAMES.get(cmd_func, f"unknown(func={cmd_func})")

    # Check Stream AC decoders first (cmdFunc=254 with specific cmdIds)
    stream_decoder = _STREAM_AC_DECODERS.get((cmd_func, cmd_id))
    if stream_decoder is not None:
        field_map, float_fields = stream_decoder
        return _decode_stream_pdata(pdata, field_map, float_fields, device_name, cmd_id)

    # Fall back to simple cmdFunc-based decoders (PowerStream, Smart Plug)
    field_map = _HEARTBEAT_DECODERS.get(cmd_func)
    if field_map is None:
        _DECODE_LOGGER.debug(
            "proto decode: no decoder for cmd_func=%d cmd_id=%d (%s)",
            cmd_func, cmd_id, device_name,
        )
        return None

    # Parse the pdata (inner heartbeat payload)
    pdata_fields = _parse_fields(pdata)

    # Map field numbers to coordinator keys — only varint (int) values
    result: dict[str, int] = {}
    unmapped: list[int] = []
    for field_num, value in pdata_fields.items():
        if not isinstance(value, int):
            continue  # skip nested LEN fields
        key = field_map.get(field_num)
        if key:
            result[key] = value
        else:
            unmapped.append(field_num)

    if result:
        _DECODE_LOGGER.debug(
            "proto decode OK: %s cmd_id=%d → %d keys mapped, %d unmapped %s",
            device_name, cmd_id, len(result), len(unmapped),
            unmapped[:10] if unmapped else "",
        )
    else:
        _DECODE_LOGGER.debug(
            "proto decode: %s cmd_id=%d — pdata has %d fields but none mapped",
            device_name, cmd_id, len(pdata_fields),
        )
        return None

    return result


def _decode_stream_pdata(
    pdata: bytes,
    field_map: dict[int, str],
    float_fields: set[int],
    device_name: str,
    cmd_id: int,
) -> dict[str, int | float] | None:
    """Decode Stream AC pdata with float-aware field mapping.

    Stream AC proto uses both varint (uint32/int32) and 32-bit fixed (float)
    wire types.  Fields listed in float_fields are decoded as IEEE 754 float;
    all others are kept as int.
    """
    pdata_fields = _parse_fields(pdata)

    result: dict[str, int | float] = {}
    unmapped: list[int] = []
    for field_num, raw_value in pdata_fields.items():
        if not isinstance(raw_value, int):
            continue  # skip nested LEN fields (bytes)
        key = field_map.get(field_num)
        if key:
            if field_num in float_fields:
                result[key] = round(_decode_float_bits(raw_value), 2)
            else:
                result[key] = raw_value
        else:
            unmapped.append(field_num)

    if result:
        _DECODE_LOGGER.debug(
            "proto decode OK: %s cmd_id=%d → %d keys mapped, %d unmapped %s",
            device_name, cmd_id, len(result), len(unmapped),
            unmapped[:10] if unmapped else "",
        )
    else:
        _DECODE_LOGGER.debug(
            "proto decode: %s cmd_id=%d — pdata has %d fields but none mapped",
            device_name, cmd_id, len(pdata_fields),
        )
        return None

    return result


# ---------------------------------------------------------------------------
# DEBUG helpers — decode received protobuf for analysis
# ---------------------------------------------------------------------------

def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read varint at position pos. Returns (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return result, pos


def dump_fields(data: bytes, depth: int = 0, max_depth: int = 3) -> str:
    """
    Decode protobuf wire-format to readable field dump (for DEBUG logging).

    Example output:
        f1(LEN  12): 0a 08 ...  [nested]
          f1(LEN   8): 0a 04 ...
        f2(VAR   32)
        f10(VAR   3)
    """
    indent = "  " * depth
    lines: list[str] = []
    pos = 0
    try:
        while pos < len(data):
            tag, pos = _read_varint(data, pos)
            field_num = tag >> 3
            wire_type = tag & 0x07
            if wire_type == 0:        # varint
                val, pos = _read_varint(data, pos)
                lines.append(f"{indent}f{field_num}(VAR {val:5d})")
            elif wire_type == 2:      # length-delimited
                length, pos = _read_varint(data, pos)
                chunk = data[pos:pos + length]
                pos += length
                hex_str = chunk[:16].hex()
                if depth < max_depth and length >= 2 and chunk[0] in (0x08, 0x0a, 0x10, 0x12, 0x18, 0x1a):
                    nested = dump_fields(chunk, depth + 1, max_depth)
                    lines.append(f"{indent}f{field_num}(LEN {length:4d}) [nested]")
                    lines.append(nested)
                else:
                    lines.append(f"{indent}f{field_num}(LEN {length:4d}): {hex_str}")
            elif wire_type == 5:      # 32-bit fixed (float or fixed32)
                raw = data[pos:pos + 4]
                pos += 4
                int_val = int.from_bytes(raw, "little")
                try:
                    float_val = struct.unpack('<f', raw)[0]
                    lines.append(f"{indent}f{field_num}(F32 {float_val:8.2f}  raw=0x{int_val:08x})")
                except (struct.error, OverflowError):
                    lines.append(f"{indent}f{field_num}(F32 raw=0x{int_val:08x})")
            elif wire_type == 1:      # 64-bit fixed
                raw = data[pos:pos + 8]
                pos += 8
                int_val = int.from_bytes(raw, "little")
                lines.append(f"{indent}f{field_num}(F64 raw=0x{int_val:016x})")
            else:
                lines.append(f"{indent}  <wire_type {wire_type} unknown, stop>")
                break
    except Exception as exc:
        lines.append(f"{indent}  <parse error: {exc}>")
    return "\n".join(lines)

