"""EcoFlow Cloud – Home Assistant integration entry point."""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import (
    DOMAIN, CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_DEVICE_SN, CONF_API_HOST,
    CONF_AUTH_MODE, CONF_EMAIL, CONF_PASSWORD,
    CONF_DEV_ACCESS_KEY, CONF_DEV_SECRET_KEY, CONF_DEV_API_HOST,
    AUTH_MODE_PRIVATE,
    API_HOST_DEFAULT, API_HOST_EU, MQTT_KEEPALIVE, MQTT_RECONNECT_INTERVAL,
    REST_SET_BLOCKED_SN_PREFIXES,
)
from .api_client import EcoFlowAPI, EcoFlowPrivateAPI, EcoFlowAPIError
from .coordinator import EcoflowCoordinator
from .devices.registry import detect_model
from .proto_codec import dump_fields, decode_proto_telemetry

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT, Platform.BUTTON]

# v0.2.19: Delta 3 expects JSON GET (latestQuotas) on /get topic — NOT protobuf.
# APP sends after connect: latestQuotas + getBmsInfo + getAllTaskCfg + setRtcTime.
# Device accepts set-commands after receiving get_reply (latestQuotas).
# Repeat every 20s to keep the session alive.
_GET_INTERVAL = 20   # seconds — APP cadence

# id format: small integer (5-9 digits), NOT epoch seconds.
# APP uses incrementing counters per session, e.g. 12251-1001, 12352-1002.
# Use a random prefix + incrementing seq to avoid collision with the APP session.
import random as _random
_ID_PREFIX = _random.randint(10000, 99999)
_id_seq = 0

def _next_id() -> int:
    global _id_seq
    _id_seq += 1
    return _ID_PREFIX * 1000 + _id_seq


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data       = entry.data
    access_key = data.get(CONF_ACCESS_KEY, "")
    secret_key = data.get(CONF_SECRET_KEY, "")
    sn         = data[CONF_DEVICE_SN]
    auth_mode  = data.get(CONF_AUTH_MODE, "public")
    api_host   = data.get(CONF_API_HOST, API_HOST_DEFAULT)

    _LOGGER.info("EcoFlow: setting up %s mode=%s host=%s", sn, auth_mode, api_host)

    if auth_mode == AUTH_MODE_PRIVATE:
        email    = data.get(CONF_EMAIL, "")
        password = data.get(CONF_PASSWORD, "")
        api      = EcoFlowPrivateAPI(email, password, sn)
    else:
        api = EcoFlowAPI(access_key, secret_key, sn, api_host)

    # ── Developer API for REST SET (hybrid mode) ─────────────────────────
    # If Developer API credentials are configured, create a separate client
    # for SET commands via REST PUT. This enables reliable device control
    # for Delta 3 devices where MQTT SET is ignored (H-G confirmed).
    dev_ak = data.get(CONF_DEV_ACCESS_KEY, "")
    dev_sk = data.get(CONF_DEV_SECRET_KEY, "")
    dev_api: EcoFlowAPI | None = None

    # Skip REST SET for devices where EcoFlow blocks the Developer API (code=1006).
    # These devices use MQTT JSON SET with "from":"Android" instead.
    rest_blocked = any(sn.upper().startswith(p) for p in REST_SET_BLOCKED_SN_PREFIXES)

    if dev_ak and dev_sk and not rest_blocked:
        dev_host = data.get(CONF_DEV_API_HOST, API_HOST_EU)
        dev_api  = EcoFlowAPI(dev_ak, dev_sk, sn, dev_host)
        _LOGGER.info("EcoFlow: Developer API configured for REST SET (host=%s)", dev_host)
        # In private mode, attach to the PrivateAPI so set_quota() delegates
        if isinstance(api, EcoFlowPrivateAPI):
            api.attach_developer_api(dev_api)
    elif dev_ak and dev_sk and rest_blocked:
        _LOGGER.info(
            "EcoFlow: REST SET skipped for %s — SN prefix blocked by EcoFlow API. "
            "Using MQTT JSON SET instead.", sn
        )
    elif auth_mode == AUTH_MODE_PRIVATE:
        _LOGGER.warning(
            "EcoFlow: No Developer API credentials — switches/numbers will use "
            "MQTT protobuf (experimental, may not work for Delta 3)"
        )

    coordinator = EcoflowCoordinator(hass, api)

    # ── MQTT credentials ──────────────────────────────────────────────────
    try:
        mqtt_info = await hass.async_add_executor_job(api.get_mqtt_credentials)
    except EcoFlowAPIError as exc:
        _LOGGER.error("EcoFlow: cannot get MQTT credentials: %s", exc)
        return False

    if not mqtt_info:
        _LOGGER.error("EcoFlow: empty MQTT credentials response")
        return False

    _LOGGER.info("EcoFlow: MQTT credentials OK: %s", {
        k: v for k, v in mqtt_info.items() if k != "certificatePassword"
    })

    # ── REST quota snapshot (optional, non-fatal) ─────────────────────────
    try:
        initial = await hass.async_add_executor_job(api.get_all_quota)
        if initial:
            coordinator.async_set_updated_data(initial)
            _LOGGER.warning("EcoFlow: REST initial data OK: %d keys", len(initial))
        elif api.rest_quota_unavailable:
            coordinator.disable_rest_polling()
        else:
            _LOGGER.info("EcoFlow: REST initial data empty — waiting for MQTT push")
    except Exception as exc:
        _LOGGER.warning("EcoFlow: REST initial data failed (non-fatal): %s", exc)

    # ── Device model detection ────────────────────────────────────────────
    device_model = detect_model(sn)

    # ── Store objects ─────────────────────────────────────────────────────
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api, "coordinator": coordinator, "sn": sn,
        "rest_api": dev_api,  # None if no Developer API configured
        "device_model": device_model,
    }

    # ── MQTT topics ───────────────────────────────────────────────────────
    mqtt_host = mqtt_info.get("url", "mqtt.ecoflow.com")
    mqtt_port = int(mqtt_info.get("port", 8883))

    is_private = mqtt_info.get("_private_api", False)
    user_id    = mqtt_info.get("_user_id", "")
    if is_private:
        topic_sub        = f"/app/device/property/{sn}"
        topic_get        = f"/app/{user_id}/{sn}/thing/property/get"
        topic_set        = f"/app/{user_id}/{sn}/thing/property/set"
        topic_set_reply  = f"/app/{user_id}/{sn}/thing/property/set_reply"
        topic_get_reply  = f"/app/{user_id}/{sn}/thing/property/get_reply"
        # v0.2.18: wildcard trace — temporary, for APP session analysis
        # Logs everything on /app/{uid}/#: APP client_id, commands, sequence
        topic_wildcard   = f"/app/{user_id}/#"
    else:
        topic_sub        = f"/open/{mqtt_info.get('certificateAccount', '')}/{sn}/quota"
        topic_get        = f"/open/{mqtt_info.get('certificateAccount', '')}/{sn}/quota/get"
        topic_set        = f"/open/{mqtt_info.get('certificateAccount', '')}/{sn}/set"
        topic_set_reply  = None
        topic_get_reply  = None
        topic_wildcard   = None

    _LOGGER.info(
        "EcoFlow: MQTT host=%s port=%d topic_sub=%s",
        mqtt_host, mqtt_port, topic_sub
    )

    # ── Client factory ────────────────────────────────────────────────────
    # v0.2.18: extracted as inner function so recertification can create a
    # fresh Client with the new client_id returned by the API.
    # The EcoFlow broker routes set-commands only to the session whose
    # client_id matches the most recently issued certificate. Reusing an
    # old client_id after recertification causes silent command drops.

    # Track mid→topic per client so on_subscribe logs the correct topic.
    _subscribe_mid: dict[int, str] = {}

    def _send_json_get(c: mqtt.Client, label: str = "keepalive") -> None:
        """Send JSON latestQuotas GET — session initiation and keepalive.

        v0.2.19: Delta 3 ignores protobuf GET entirely. The device responds
        to a JSON latestQuotas GET with a get_reply (7979 bytes), after which
        it accepts set-commands (setRtcTime ack=1 confirmed).
        Proven via log analysis 2026-03-12: get_reply only on JSON GET.
        """
        payload = json.dumps({
            "id":          _next_id(),
            "version":     "1.0",
            "operateType": "latestQuotas",
            "moduleType":  0,
        })
        result = c.publish(topic_get, payload, qos=1)
        _LOGGER.debug(
            "EcoFlow: JSON GET (%s) published → %s mid=%s rc=%s",
            label, topic_get, result.mid, result.rc,
        )

    def _send_init_sequence(c: mqtt.Client) -> None:
        """Send the full APP init sequence after connect.

        Proven order from log analysis (get_reply + set_reply patterns):
          1. latestQuotas GET -> triggers get_reply with full device state
          2. getBmsInfo     -> set_reply with BMS info
          3. getAllTaskCfg  -> set_reply with task schedule
          4. setRtcTime     -> set_reply ack=1 (confirms session active)
        Device accepts set-commands after step 4.
        """
        ts = int(time.time())

        # 1. latestQuotas — triggert get_reply
        _send_json_get(c, label="init")

        # 2. getBmsInfo
        bms_info = json.dumps({
            "id": _next_id(), "version": "1.0",
            "operateType": "getBmsInfo", "moduleType": 2, "params": {},
        })
        c.publish(topic_set, bms_info, qos=1)
        _LOGGER.debug("EcoFlow: init getBmsInfo sent")

        # 3. getAllTaskCfg
        task_cfg = json.dumps({
            "id": _next_id(), "version": "1.0",
            "operateType": "getAllTaskCfg", "moduleType": 1, "params": {},
        })
        c.publish(topic_set, task_cfg, qos=1)
        _LOGGER.debug("EcoFlow: init getAllTaskCfg sent")

        # 4. setRtcTime — confirms session, ack=1 = device ready for commands
        rtc = json.dumps({
            "id": _next_id(), "version": "1.0",
            "operateType": "setRtcTime", "moduleType": 2,
            "params": {"rtc": ts},
        })
        c.publish(topic_set, rtc, qos=1)

        # 5. v0.3.4: getOutputMemory — pd.outputMemoryEn is not in latestQuotas
        # or regular telemetry push. This dedicated GET retrieves the current state
        # so the Output Memory switch shows the correct value at startup.
        output_mem = json.dumps({
            "id": _next_id(), "version": "1.0",
            "operateType": "getOutputMemory", "moduleType": 1, "params": {},
        })
        c.publish(topic_set, output_mem, qos=1)
        _LOGGER.debug("EcoFlow: init getOutputMemory sent")

        _LOGGER.info("EcoFlow: init sequence sent (latestQuotas + getBmsInfo + getAllTaskCfg + setRtcTime + getOutputMemory)")

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info("EcoFlow: MQTT connected OK sn=%s", sn)
            _LOGGER.debug(
                "EcoFlow: on_connect flags=%s subscribing to %d topics",
                flags, 2 + (1 if topic_set_reply else 0) + (1 if topic_get_reply else 0) + (1 if topic_wildcard else 0),
            )
            r = c.subscribe(topic_sub, qos=1)
            _subscribe_mid[r[1]] = topic_sub
            if topic_set_reply:
                r = c.subscribe(topic_set_reply, qos=1)
                _subscribe_mid[r[1]] = topic_set_reply
            if topic_get_reply:
                r = c.subscribe(topic_get_reply, qos=1)
                _subscribe_mid[r[1]] = topic_get_reply
            if topic_wildcard:
                r = c.subscribe(topic_wildcard, qos=0)
                _subscribe_mid[r[1]] = topic_wildcard
                _LOGGER.info("EcoFlow: wildcard trace ACTIVE on %s", topic_wildcard)
            # v0.2.19: schedule init sequence via threading.Timer — does NOT block MQTT event loop.
            # time.sleep() in on_connect blocks the paho network loop (all MQTT I/O stops).
            # threading.Timer runs _send_init_sequence in a separate thread after 5s
            # while the MQTT loop continues normally.
            # v0.3.9: Stream AC uses protobuf latestQuotas (separate keepalive loop) and
            # does NOT respond to Delta 3 JSON init. Skip init sequence for Stream AC models.
            if device_model in {"Stream AC", "Stream AC Pro", "Stream Ultra"}:
                _LOGGER.debug(
                    "EcoFlow: skipping JSON init sequence for %s — uses protobuf latestQuotas",
                    device_model,
                )
            else:
                _LOGGER.debug("EcoFlow: init sequence scheduled in 5s (threading.Timer)")
                threading.Timer(5.0, _send_init_sequence, args=(c,)).start()
        else:
            _LOGGER.error("EcoFlow: MQTT connect FAILED rc=%d sn=%s", rc, sn)

    def on_subscribe(c, userdata, mid, granted_qos):
        topic = _subscribe_mid.pop(mid, "unknown")
        _LOGGER.info("EcoFlow: MQTT subscribed mid=%d qos=%s topic=%s",
                        mid, granted_qos, topic)

    def on_disconnect(c, userdata, rc):
        if rc == 0:
            _LOGGER.info("EcoFlow: MQTT clean disconnect for %s", sn)
        else:
            _LOGGER.warning(
                "EcoFlow: MQTT unexpected disconnect rc=%d for %s — "
                "paho will auto-reconnect", rc, sn
            )

    def on_message(c, userdata, msg):
        raw_bytes = msg.payload
        _LOGGER.debug(
            "EcoFlow: MQTT rx topic=%s len=%d",
            msg.topic, len(raw_bytes),
        )

        # ── Protobuf detection & decoding ─────────────────────────────────
        # PowerStream and Smart Plug send binary protobuf telemetry on topic_sub.
        # Delta 3 also sends binary protobuf replies (ack messages).
        # Bytes 0x0a / 0x12 are standard protobuf wire tags (field 1/2, LEN).
        if raw_bytes and raw_bytes[0] not in (0x7B, 0x5B):  # 0x7B='{', 0x5B='['
            is_proto = len(raw_bytes) >= 2 and raw_bytes[0] in (0x0a, 0x12)
            _LOGGER.debug(
                "EcoFlow: MQTT binary payload topic=%s proto_likely=%s len=%d hex=%s",
                msg.topic, is_proto, len(raw_bytes), raw_bytes[:64].hex(),
            )
            if is_proto:
                # v0.3.4: Try to decode protobuf telemetry into coordinator data
                decoded = decode_proto_telemetry(raw_bytes)
                if decoded:
                    _LOGGER.info(
                        "EcoFlow: proto telemetry decoded: %d keys → %s",
                        len(decoded), sorted(decoded.keys())[:10],
                    )
                    hass.loop.call_soon_threadsafe(
                        coordinator.update_from_mqtt, decoded
                    )
                else:
                    # Not a recognized heartbeat — log for analysis (ack, command reply, etc.)
                    _LOGGER.debug(
                        "EcoFlow: proto message (not heartbeat) topic=%s len=%d hex=%s",
                        msg.topic, len(raw_bytes), raw_bytes[:100].hex(),
                    )
                    _LOGGER.debug(
                        "EcoFlow: proto fields:\n%s",
                        dump_fields(raw_bytes),
                    )
            else:
                _LOGGER.warning(
                    "EcoFlow: MQTT unknown binary payload topic=%s hex=%s",
                    msg.topic, raw_bytes[:64].hex(),
                )
            return

        # ── JSON parse ────────────────────────────────────────────────────
        try:
            raw = raw_bytes.decode("utf-8")
            payload = json.loads(raw)
        except UnicodeDecodeError:
            _LOGGER.debug(
                "EcoFlow: MQTT UTF-8 decode error topic=%s hex=%s",
                msg.topic, raw_bytes[:64].hex(),
            )
            return
        except json.JSONDecodeError as exc:
            _LOGGER.warning(
                "EcoFlow: MQTT JSON parse error topic=%s exc=%s raw=%s",
                msg.topic, exc, raw_bytes[:200],
            )
            return

        # ── set_reply analyse ─────────────────────────────────────────────
        # Flat structure: operateType + code at root, data.ack = device result
        # ack=1 -> device accepted command, ack=0 -> device rejected
        if topic_set_reply and msg.topic == topic_set_reply:
            try:
                operate_type = payload.get("operateType", "unknown") if isinstance(payload, dict) else "unknown"
                http_code    = payload.get("code", "?")   if isinstance(payload, dict) else "?"
                _data        = payload.get("data")        if isinstance(payload, dict) else None
                ack          = _data.get("ack", "?")      if isinstance(_data, dict) else "?"
            except Exception:
                operate_type, http_code, ack = "parse_error", "?", "?"
            _LOGGER.info(
                "EcoFlow: set_reply operateType=%s code=%s ack=%s len=%d",
                operate_type, http_code, ack, len(raw_bytes),
            )
            _LOGGER.debug(
                "EcoFlow: set_reply full payload=%s",
                payload,
            )

        elif topic_get_reply and msg.topic == topic_get_reply:
            keys_count = len(payload) if isinstance(payload, dict) else 0
            _LOGGER.info(
                "EcoFlow: get_reply received len=%d keys=%d",
                len(raw_bytes), keys_count,
            )
            _LOGGER.debug(
                "EcoFlow: get_reply full payload=%s",
                payload,
            )

        elif topic_wildcard and msg.topic not in (topic_sub, topic_set_reply, topic_get_reply):
            # Wildcard trace — APP commands, init sequence, other clients
            # JSON payloads as text, binary as hex
            try:
                readable = raw_bytes[:400].decode("utf-8", errors="replace")
            except Exception:
                readable = raw_bytes[:200].hex()
            _LOGGER.info(
                "EcoFlow: WILDCARD topic=%s len=%d payload=%s",
                msg.topic, len(raw_bytes), readable,
            )

        else:
            # Regular telemetry message from topic_sub
            keys_count = len(payload) if isinstance(payload, dict) else 0
            _LOGGER.debug(
                "EcoFlow: telemetry topic=%s keys=%d",
                msg.topic, keys_count,
            )

        hass.loop.call_soon_threadsafe(coordinator.update_from_mqtt, payload)

    def on_publish(c, userdata, mid):
        _LOGGER.debug("EcoFlow: MQTT publish ACK mid=%d (command delivered to broker)", mid)

    def _build_client(cid: str, user: str, passwd: str) -> mqtt.Client:
        """Create, configure and return a new paho Client.

        Called at startup and on every recertification. Using a fresh Client
        object is required because paho.client_id is immutable after __init__,
        and the EcoFlow broker routes set-commands only to the session matching
        the most recently issued client_id.
        """
        c = mqtt.Client(
            client_id=cid,
            clean_session=True,
            protocol=mqtt.MQTTv311,
        )
        c.username_pw_set(user, passwd)
        c.tls_set(cert_reqs=ssl.CERT_NONE)
        c.tls_insecure_set(True)
        c.on_connect    = on_connect
        c.on_subscribe  = on_subscribe
        c.on_disconnect = on_disconnect
        c.on_message    = on_message
        c.on_publish    = on_publish
        c.reconnect_delay_set(min_delay=5, max_delay=60)
        _LOGGER.info("EcoFlow: MQTT client_id=%s", cid)
        return c

    # Initial connect
    init_cid  = mqtt_info.get("_client_id") or f"HA-{mqtt_info.get('certificateAccount','')}-{sn}"[:23]
    init_user = mqtt_info.get("certificateAccount", "")
    init_pass = mqtt_info.get("certificatePassword", "")

    # _build_client calls tls_set synchronously — run in executor to avoid
    # blocking the event loop (tls_set can do file I/O for CA bundles).
    client = await hass.async_add_executor_job(
        _build_client, init_cid, init_user, init_pass
    )
    client.connect_async(mqtt_host, mqtt_port, keepalive=MQTT_KEEPALIVE)
    client.loop_start()

    hass.data[DOMAIN][entry.entry_id].update({
        "mqtt_client":    client,
        "mqtt_topic_set": topic_set,
        "mqtt_topic_get": topic_get,
        "mqtt_user":      init_user,
        "mqtt_send_get":  lambda label="post_set": _send_json_get(client, label),
    })

    # ── Periodic recertification ──────────────────────────────────────────
    # v0.2.18: creates a new Client object per cycle so the broker receives
    # a connection from the correct client_id that was just issued.
    # Previous approach (client.reconnect() with old client_id) caused the
    # broker to ignore all set-commands after the first recertification cycle.
    RECERT_INTERVAL = 600  # seconds

    async def _recertify_loop():
        while True:
            await asyncio.sleep(RECERT_INTERVAL)
            _LOGGER.info("EcoFlow: periodic recertification starting…")
            try:
                new_info = await hass.async_add_executor_job(api.get_mqtt_credentials)
            except Exception as exc:
                _LOGGER.warning("EcoFlow: recertification failed (will retry): %s", exc)
                continue

            new_cid  = new_info.get("_client_id", "")
            new_user = new_info.get("certificateAccount", "")
            new_pass = new_info.get("certificatePassword", "")

            if not new_pass:
                _LOGGER.warning("EcoFlow: recertification returned empty password — skipping")
                continue
            if not new_cid:
                _LOGGER.warning("EcoFlow: recertification returned empty client_id — skipping")
                continue

            _LOGGER.info(
                "EcoFlow: recertification OK — new client_id=%s, building new MQTT client",
                new_cid
            )

            try:
                new_client = await hass.async_add_executor_job(
                    _build_client, new_cid, new_user, new_pass
                )
            except Exception as exc:
                _LOGGER.warning("EcoFlow: failed to build new MQTT client: %s — keeping old", exc)
                continue

            # Stop old client before starting new one
            old_client = hass.data[DOMAIN][entry.entry_id].get("mqtt_client")
            if old_client:
                try:
                    old_client.loop_stop()
                    old_client.disconnect()
                except Exception as exc:
                    _LOGGER.debug("EcoFlow: error stopping old client (non-fatal): %s", exc)

            # Atomic update — switch.py and number.py read this reference on every publish
            new_client.connect_async(mqtt_host, mqtt_port, keepalive=MQTT_KEEPALIVE)
            new_client.loop_start()
            hass.data[DOMAIN][entry.entry_id]["mqtt_client"] = new_client
            _LOGGER.info("EcoFlow: new MQTT client active (client_id=%s)", new_cid)

    hass.loop.create_task(_recertify_loop())

    # ── JSON GET keepalive ────────────────────────────────────────────────
    # v0.2.19: Send JSON latestQuotas GET every 20s to keep session alive.
    # Protobuf GET (v0.2.18) was completely ignored by the device.
    # Proven via log analysis: get_reply (latestQuotas) triggers device acceptance.
    # v0.3.9: Stream AC uses protobuf latestQuotas instead (see loop below).
    _STREAM_AC_MODELS = {"Stream AC", "Stream AC Pro", "Stream Ultra"}
    if is_private and device_model not in _STREAM_AC_MODELS:
        async def _get_keepalive_loop():
            await asyncio.sleep(25)   # wait after init sequence
            while True:
                current_client = hass.data[DOMAIN][entry.entry_id].get("mqtt_client")
                if current_client:
                    try:
                        _send_json_get(current_client, label="keepalive")
                    except Exception as exc:
                        _LOGGER.debug("EcoFlow: GET keepalive error (non-fatal): %s", exc)
                await asyncio.sleep(_GET_INTERVAL)

        hass.loop.create_task(_get_keepalive_loop())
        _LOGGER.info(
            "EcoFlow: JSON GET keepalive started (interval=%ds, topic=%s)",
            _GET_INTERVAL, topic_get,
        )

    # ── Stream AC protobuf latestQuotas keepalive (v0.3.9) ────────────────
    # Source: foxthefox/ioBroker.ecoflow-mqtt ef_stream_inverter_data.js
    # Stream AC family needs a minimal protobuf session ping (header only,
    # no pdata) to keep DisplayPropertyUpload telemetry flowing. Unlike
    # Delta 3, Stream AC ignores the JSON latestQuotas GET used above.
    # This protobuf message is published to topic_set (same as commands).
    if is_private and device_model in _STREAM_AC_MODELS:
        from .proto_codec import stream_build_latest_quotas

        async def _stream_ac_keepalive_loop():
            await asyncio.sleep(15)   # wait after MQTT connect
            while True:
                current_client = hass.data[DOMAIN][entry.entry_id].get("mqtt_client")
                if current_client:
                    try:
                        payload = stream_build_latest_quotas()
                        result = current_client.publish(topic_set, payload, qos=1)
                        _LOGGER.debug(
                            "EcoFlow: Stream AC protobuf keepalive → %s mid=%s rc=%s (%d bytes)",
                            topic_set, result.mid, result.rc, len(payload),
                        )
                    except Exception as exc:
                        _LOGGER.debug(
                            "EcoFlow: Stream AC keepalive error (non-fatal): %s", exc,
                        )
                await asyncio.sleep(15)  # foxthefox uses ~15s interval

        hass.loop.create_task(_stream_ac_keepalive_loop())
        _LOGGER.info(
            "EcoFlow: Stream AC protobuf keepalive started "
            "(interval=15s, model=%s, topic=%s)",
            device_model, topic_set,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        d = hass.data[DOMAIN].pop(entry.entry_id, {})
        c = d.get("mqtt_client")
        if c:
            c.loop_stop()
            c.disconnect()
    return ok
