"""EcoFlow Cloud – Home Assistant integration entry point."""
from __future__ import annotations

import json
import logging
import ssl
import time
from typing import Any

import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import (
    DOMAIN, CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_DEVICE_SN, CONF_API_HOST,
    CONF_AUTH_MODE, CONF_EMAIL, CONF_PASSWORD,
    AUTH_MODE_PRIVATE,
    API_HOST_DEFAULT, MQTT_KEEPALIVE, MQTT_RECONNECT_INTERVAL,
)
from .api_client import EcoFlowAPI, EcoFlowPrivateAPI, EcoFlowAPIError
from .coordinator import EcoflowCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data       = entry.data
    access_key = data.get(CONF_ACCESS_KEY, "")
    secret_key = data.get(CONF_SECRET_KEY, "")
    sn         = data[CONF_DEVICE_SN]
    auth_mode  = data.get(CONF_AUTH_MODE, "public")
    api_host   = data.get(CONF_API_HOST, API_HOST_DEFAULT)

    _LOGGER.warning("EcoFlow: setting up %s mode=%s host=%s", sn, auth_mode, api_host)

    if auth_mode == AUTH_MODE_PRIVATE:
        email    = data.get(CONF_EMAIL, "")
        password = data.get(CONF_PASSWORD, "")
        api      = EcoFlowPrivateAPI(email, password, sn)
    else:
        api = EcoFlowAPI(access_key, secret_key, sn, api_host)
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

    _LOGGER.warning("EcoFlow: MQTT credentials OK: %s", {
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

    # ── Store objects ─────────────────────────────────────────────────────
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api, "coordinator": coordinator, "sn": sn,
    }

    # ── MQTT setup ────────────────────────────────────────────────────────
    mqtt_user = mqtt_info.get("certificateAccount", "")
    mqtt_pass = mqtt_info.get("certificatePassword", "")
    mqtt_host = mqtt_info.get("url", "mqtt.ecoflow.com")
    mqtt_port = int(mqtt_info.get("port", 8883))

    is_private = mqtt_info.get("_private_api", False)
    user_id    = mqtt_info.get("_user_id", "")
    if is_private:
        topic_sub = f"/app/device/property/{sn}"
        topic_get = f"/app/{user_id}/{sn}/thing/property/get"
        topic_set = f"/app/{user_id}/{sn}/thing/property/set"
    else:
        topic_sub = f"/open/{mqtt_user}/{sn}/quota"
        topic_get = f"/open/{mqtt_user}/{sn}/quota/get"
        topic_set = f"/open/{mqtt_user}/{sn}/set"

    _LOGGER.warning(
        "EcoFlow: MQTT host=%s port=%d user=%s topic_sub=%s",
        mqtt_host, mqtt_port, mqtt_user, topic_sub
    )

    client_id = mqtt_info.get("_client_id") or f"HA-{mqtt_user}-{sn}"[:23]
    _LOGGER.warning("EcoFlow: MQTT client_id=%s", client_id)

    client = mqtt.Client(
        client_id=client_id,
        clean_session=True,
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(mqtt_user, mqtt_pass)

    def _configure_tls():
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

    await hass.async_add_executor_job(_configure_tls)

    def _request_full_state(c: mqtt.Client) -> None:
        """Send a get-all-properties request to the device."""
        c.publish(topic_get, json.dumps({
            "id":      str(int(time.time() * 1000)),
            "version": "1.0",
            "sn":      sn,
            "params":  {},
        }), qos=0)

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            _LOGGER.warning("EcoFlow: MQTT connected OK for %s", sn)
            c.subscribe(topic_sub, qos=1)
            _request_full_state(c)
        else:
            _LOGGER.error("EcoFlow: MQTT connect FAILED rc=%d for %s", rc, sn)

    def on_subscribe(c, userdata, mid, granted_qos):
        _LOGGER.warning("EcoFlow: MQTT subscribed mid=%d qos=%s topic=%s",
                        mid, granted_qos, topic_sub)

    def on_disconnect(c, userdata, rc):
        if rc == 0:
            _LOGGER.warning("EcoFlow: MQTT clean disconnect for %s", sn)
        else:
            _LOGGER.warning(
                "EcoFlow: MQTT unexpected disconnect rc=%d for %s — "
                "paho will auto-reconnect", rc, sn
            )

    def on_message(c, userdata, msg):
        raw_bytes = msg.payload
        _LOGGER.debug(
            "EcoFlow: MQTT message topic=%s len=%d",
            msg.topic, len(raw_bytes)
        )
        try:
            raw = raw_bytes.decode("utf-8")
            payload = json.loads(raw)
            hass.loop.call_soon_threadsafe(coordinator.update_from_mqtt, payload)
        except UnicodeDecodeError:
            _LOGGER.warning(
                "EcoFlow: MQTT payload is binary (protobuf?) — hex: %s",
                raw_bytes[:64].hex()
            )
        except json.JSONDecodeError as exc:
            _LOGGER.warning("EcoFlow: MQTT JSON parse error: %s — raw: %s",
                            exc, raw_bytes[:200])

    client.on_connect    = on_connect
    client.on_subscribe  = on_subscribe
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # Auto-reconnect: start na 5s, max 60s tussen pogingen
    client.reconnect_delay_set(min_delay=5, max_delay=60)
    client.connect_async(mqtt_host, mqtt_port, keepalive=MQTT_KEEPALIVE)
    client.loop_start()

    hass.data[DOMAIN][entry.entry_id].update({
        "mqtt_client":    client,
        "mqtt_topic_set": topic_set,
        "mqtt_user":      mqtt_user,
    })

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
