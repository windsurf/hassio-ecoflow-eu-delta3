"""Switch platform for EcoFlow Cloud."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from . import _next_id
from .devices.delta3_1500 import (
    DEVICE_MODEL,
    KEY_AC_ENABLED,
    KEY_AC_XBOOST,
    KEY_USB_OUT_STATE,
    KEY_AC_CHG_PAUSE,
    KEY_BEEP_MODE,
    KEY_PV_CHG_PRIO,
    KEY_AC_AUTO_ON,
    KEY_AC_AUTO_OUT,
    KEY_EMS_UPS_FLAG,
    KEY_DC_OUT_STATE,
    KEY_AC_BYPASS_PAUSE,
    KEY_OUTPUT_MEMORY,
    KEY_BP_IS_CONFIG,   # v0.2.23: was KEY_BP_POWER_SOC — corrected to pd.watchIsConfig
)
from .proto_codec import (
    build_ac_output,
    build_xboost,
    build_dc_output,
    build_ac_charging,
    build_beep,
    build_ups_mode,
)

_LOGGER = logging.getLogger(__name__)

MODULE_PD   = 1
MODULE_BMS  = 2
MODULE_INV  = 3
MODULE_MPPT = 5


@dataclass(frozen=True, kw_only=True)
class EcoFlowSwitchDescription(SwitchEntityDescription):
    """Switch description with MQTT command definition."""
    state_key:    str
    cmd_module:   int                        = 0
    cmd_operate:  str                        = ""
    cmd_params:   Any                        = None
    inverted:     bool                       = False
    proto_builder: Optional[Callable[[bool], bytes]] = None
    entity_registry_enabled_default: bool = True



SWITCH_DESCRIPTIONS: tuple[EcoFlowSwitchDescription, ...] = (
    # ── Outputs ──────────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="ac_output",
        name="AC Output",
        icon="mdi:power-socket-eu",
        state_key=KEY_AC_ENABLED,
        cmd_module=MODULE_MPPT,
        cmd_operate="acOutCfg",
        cmd_params=lambda on: {
            "enabled":     1 if on else 0,
            "xboost":      255,
            "out_voltage": -1,
            "out_freq":    255,
        },
        proto_builder=build_ac_output,
    ),
    EcoFlowSwitchDescription(
        key="x_boost",
        name="X-Boost",
        icon="mdi:lightning-bolt",
        state_key=KEY_AC_XBOOST,
        cmd_module=MODULE_MPPT,
        cmd_operate="acOutCfg",
        cmd_params=lambda on: {
            "enabled":     255,
            "xboost":      1 if on else 0,
            "out_voltage": 4294967295,
            "out_freq":    255,
        },
        proto_builder=build_xboost,
    ),
    EcoFlowSwitchDescription(
        key="usb_output",
        name="USB Output",
        icon="mdi:usb-port",
        entity_registry_enabled_default=False,  # dcOutCfg returns ack=0 — risk of DC-bus shutdown
        state_key=KEY_USB_OUT_STATE,
        cmd_module=MODULE_PD,
        cmd_operate="dcOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="dc_output",
        name="DC Output",
        icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE,
        cmd_module=MODULE_MPPT,
        cmd_operate="mpptCar",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
        proto_builder=build_dc_output,
    ),

    # ── AC Charging ───────────────────────────────────────────────────────
    # v0.2.24: read-only — D361 does not support acChgCfg chgPauseFlag via MQTT.
    # Confirmed via live test: command is received (beep) but has no effect.
    # mppt.chgPauseFlag is never pushed in D361 telemetry.
    # Use inv.inputWatts > 0 or bms_emsStatus.sysChgDsgState == 2 to detect active charging.
    EcoFlowSwitchDescription(
        key="ac_charging",
        name="AC Charging",
        icon="mdi:transmission-tower",
        state_key=KEY_AC_CHG_PAUSE,
        inverted=True,
        entity_registry_enabled_default=False,  # read-only, state key never pushed on D361
        cmd_module=0,
        cmd_operate="",
        cmd_params=None,
    ),

    # ── Charging behaviour ────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="solar_charge_priority",
        name="Solar Charge Priority",
        icon="mdi:solar-power",
        entity_registry_enabled_default=False,  # not in app, effect unconfirmed
        state_key=KEY_PV_CHG_PRIO,
        cmd_module=MODULE_PD,
        cmd_operate="pvChangePrio",
        cmd_params=lambda on: {"pvChangeSet": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_auto_on",
        name="AC Auto-On",
        icon="mdi:power-plug-outline",
        entity_registry_enabled_default=False,  # not in app, effect unconfirmed
        state_key=KEY_AC_AUTO_ON,
        cmd_module=MODULE_INV,
        cmd_operate="acAutoOnCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_always_on",
        name="AC Always-On",
        icon="mdi:power-plug",
        entity_registry_enabled_default=False,  # not in app, effect unconfirmed
        state_key=KEY_AC_AUTO_OUT,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params=lambda on: {"acAutoOutConfig": 1 if on else 0, "minAcOutSoc": 0},
    ),

    # ── System ───────────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="ups_mode",
        name="UPS Mode",
        icon="mdi:power-socket",
        entity_registry_enabled_default=False,  # effect unconfirmed on D361
        state_key=KEY_EMS_UPS_FLAG,
        cmd_module=MODULE_BMS,
        cmd_operate="upsConfig",
        cmd_params=lambda on: {"openUpsFlag": 1 if on else 0},
        proto_builder=build_ups_mode,
    ),
    EcoFlowSwitchDescription(
        key="bypass",
        name="Bypass",
        icon="mdi:electric-switch",
        state_key=KEY_AC_BYPASS_PAUSE,
        # inverted=False: pd.acAutoOutPause is always 0 on D361 — never pushed via telemetry.
        # Switch will always show OFF. Command (bypassBan) does work — relay switches
        # as confirmed by pd.relaySwitchCnt incrementing. State feedback unavailable.
        entity_registry_enabled_default=False,  # ACK only — state unreliable on D361
        cmd_module=MODULE_PD,
        cmd_operate="bypassBan",
        cmd_params=lambda on: {"banBypassEn": 0 if on else 1},
    ),
    EcoFlowSwitchDescription(
        key="beep_sound",
        name="Beep Sound",
        icon="mdi:volume-high",
        state_key=KEY_BEEP_MODE,
        cmd_module=MODULE_MPPT,
        cmd_operate="quietMode",
        # inverted: beepState=1=sound ON; enabled=1=quiet ON=sound OFF
        cmd_params=lambda on: {"enabled": 0 if on else 1},
        proto_builder=build_beep,
    ),

    # ── Memory & Reserve ─────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="output_memory",
        name="Output Memory",
        icon="mdi:memory",
        entity_registry_enabled_default=False,  # ACK only — no telemetry feedback on D361; state unknown
        state_key=KEY_OUTPUT_MEMORY,
        cmd_module=MODULE_PD,
        cmd_operate="outputMemory",
        cmd_params=lambda on: {"outputMemoryEn": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="backup_reserve",
        name="Backup Reserve",
        icon="mdi:battery-charging-medium",
        # v0.2.23: corrected from KEY_BP_POWER_SOC to KEY_BP_IS_CONFIG (pd.watchIsConfig)
        # confirmed via live MQTT: pd.watchIsConfig 0→1 when enabling Backup Reserve in app
        state_key=KEY_BP_IS_CONFIG,
        cmd_module=MODULE_PD,
        cmd_operate="watthConfig",
        cmd_params=lambda on: {
            "isConfig":   1 if on else 0,
            "bpPowerSoc": 0,
            "minDsgSoc":  0,
            "minChgSoc":  0,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switches from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]

    async_add_entities(
        EcoFlowSwitchEntity(coordinator, desc, entry_data, sn)
        for desc in SWITCH_DESCRIPTIONS
    )


class EcoFlowSwitchEntity(CoordinatorEntity[EcoflowCoordinator], SwitchEntity):
    """A togglable output on the EcoFlow device."""

    entity_description: EcoFlowSwitchDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowSwitchDescription,
        entry_data: dict,
        sn: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description  = description
        self._entry_data         = entry_data
        self._sn                 = sn
        self._attr_unique_id     = f"{sn}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info   = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=f"EcoFlow {DEVICE_MODEL}",
            manufacturer=MANUFACTURER,
            model=DEVICE_MODEL,
        )


    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        if val is None:
            return None
        active = int(val) == 1
        return (not active) if self.entity_description.inverted else active

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self, turn_on: bool) -> None:
        desc = self.entity_description

        # Priority 1: REST API SET
        rest_api = self._entry_data.get("rest_api")
        if rest_api is not None and desc.cmd_operate:
            params = desc.cmd_params(turn_on) if desc.cmd_params else {}
            if desc.cmd_operate == "acOutCfg":
                xboost_val = int((self.coordinator.data or {}).get(KEY_AC_XBOOST, 0))
                params["xboost"] = xboost_val
            try:
                rest_api.set_quota(desc.cmd_module, desc.cmd_operate, params)
                _LOGGER.info(
                    "EcoFlow: REST SET %s turn_on=%s module=%d operate=%s params=%s",
                    desc.key, turn_on, desc.cmd_module, desc.cmd_operate, params,
                )
                return
            except Exception as exc:
                _LOGGER.debug(
                    "EcoFlow: REST SET %s failed (%s) — falling back to MQTT",
                    desc.key, exc,
                )

        # Priority 2: JSON MQTT SET
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")

        if not client or not topic:
            _LOGGER.error(
                "EcoFlow: no MQTT client and no REST API — cannot send %s command",
                desc.key,
            )
            return

        params = desc.cmd_params(turn_on) if desc.cmd_params else {}
        cmd = {
            "id":          _next_id(),
            "version":     "1.0",
            "sn":          self._sn,
            "moduleType":  desc.cmd_module,
            "operateType": desc.cmd_operate,
            "from":        "Android",
            "params":      params,
        }
        _LOGGER.info(
            "EcoFlow: JSON SET %s turn_on=%s topic=%s params=%s",
            desc.key, turn_on, topic, params,
        )
        result = client.publish(topic, json.dumps(cmd), qos=1)
        _LOGGER.debug("EcoFlow: JSON publish mid=%s rc=%s", result.mid, result.rc)

        # After SET: trigger a GET-ALL so coordinator refreshes state keys
        # that don't update via telemetry push (e.g. chgPauseFlag, outputMemoryEn)
        import time as _time
        _time.sleep(1.0)
        send_get = self._entry_data.get("mqtt_send_get")
        if send_get:
            try:
                send_get("post_set")
                _LOGGER.debug("EcoFlow: GET-ALL triggered after SET %s", desc.key)
            except Exception as exc:
                _LOGGER.debug("EcoFlow: GET-ALL after SET failed: %s", exc)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, False)
