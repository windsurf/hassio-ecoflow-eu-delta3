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
            else:
                lines.append(f"{indent}  <wire_type {wire_type} unknown, stop>")
                break
    except Exception as exc:
        lines.append(f"{indent}  <parse error: {exc}>")
    return "\n".join(lines)

