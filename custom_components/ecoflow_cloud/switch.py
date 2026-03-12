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

# Module type constants (EcoFlow MQTT protocol — JSON fallback only)
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
    # v0.2.18: optional protobuf builder — if set, used instead of JSON command
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
            "enabled":  1 if on else 0,
            "xboost":   0,
            "outFreq":  1,
            "outVol":   230,
        },
        # v0.2.18: protobuf builder for Delta 3
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
            "enabled":  255,
            "xboost":   1 if on else 0,
            "outFreq":  1,
            "outVol":   230,
        },
        # v0.2.19: X-Boost protobuf builder — operate_code 3, inner field 1
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
    EcoFlowSwitchDescription(
        key="ac_charging",
        name="AC Charging",
        icon="mdi:transmission-tower",
        state_key=KEY_AC_CHG_PAUSE,
        inverted=True,
        cmd_module=MODULE_MPPT,
        cmd_operate="acChgCfg",
        cmd_params=lambda on: {
            "chgWatts":     255,
            "chgPauseFlag": 0 if on else 1,
        },
        proto_builder=build_ac_charging,
    ),

    # ── Charging behaviour ────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="solar_charge_priority",
        name="Solar Charge Priority",
        icon="mdi:solar-power",
        state_key=KEY_PV_CHG_PRIO,
        cmd_module=MODULE_PD,
        cmd_operate="pvChangePrio",
        cmd_params=lambda on: {"pvChangeSet": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_auto_on",
        name="AC Auto-On",
        icon="mdi:power-plug-outline",
        state_key=KEY_AC_AUTO_ON,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOnCfg",
        cmd_params=lambda on: {"acAutoOnCfg": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_always_on",
        name="AC Always-On",
        icon="mdi:power-plug",
        state_key=KEY_AC_AUTO_OUT,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params=lambda on: {"acAutoOutConfig": 1 if on else 0, "minAcOutSoc": 0},
    ),
    EcoFlowSwitchDescription(
        key="ups_mode",
        name="UPS Mode",
        icon="mdi:shield-battery",
        state_key=KEY_EMS_UPS_FLAG,
        cmd_module=MODULE_BMS,
        cmd_operate="openUpsFlag",
        cmd_params=lambda on: {"openUpsFlag": 1 if on else 0},
        proto_builder=build_ups_mode,
    ),

    # ── System ───────────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="bypass",
        name="Bypass",
        icon="mdi:electric-switch",
        state_key=KEY_AC_BYPASS_PAUSE,
        inverted=True,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params=lambda on: {"acAutoOutPause": 0 if on else 1},
    ),
    EcoFlowSwitchDescription(
        key="beep_sound",
        name="Beep Sound",
        icon="mdi:volume-high",
        state_key=KEY_BEEP_MODE,
        cmd_module=MODULE_MPPT,
        cmd_operate="quietMode",
        cmd_params=lambda on: {"enabled": 0 if on else 1},
        proto_builder=build_beep,
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
        result = (not active) if self.entity_description.inverted else active
        return result

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self, turn_on: bool) -> None:
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")
        desc   = self.entity_description

        if not client or not topic:
            _LOGGER.error(
                "EcoFlow: MQTT client unavailable — cannot send %s command",
                desc.key,
            )
            return

        # ── v0.2.19: proto_builder takes priority over JSON ──────────────
        # Delta 3 (D361) only accepts protobuf set-commands.
        # Switches without proto_builder fall back to JSON (experimental).
        if desc.proto_builder is not None:
            proto_payload = desc.proto_builder(turn_on)
            _LOGGER.info(
                "EcoFlow: proto SET %s turn_on=%s topic=%s hex=%s",
                desc.key, turn_on, topic, proto_payload.hex(),
            )
            _LOGGER.debug(
                "EcoFlow: proto SET detail key=%s operate=%s module=%d "
                "builder=%s payload_len=%d",
                desc.key, desc.cmd_operate, desc.cmd_module,
                desc.proto_builder.__name__, len(proto_payload),
            )
            result = client.publish(topic, proto_payload, qos=1)
            _LOGGER.debug(
                "EcoFlow: proto publish mid=%s rc=%s",
                result.mid, result.rc,
            )
            return

        # ── JSON fallback (no proto_builder) ─────────────────────────────
        params = desc.cmd_params(turn_on) if desc.cmd_params else {}

        # acOutCfg: always include live xboost value
        if desc.cmd_operate == "acOutCfg":
            xboost_val = int((self.coordinator.data or {}).get(KEY_AC_XBOOST, 0))
            params["xboost"] = xboost_val
            _LOGGER.debug(
                "EcoFlow: acOutCfg xboost live waarde=%d meegestuurd", xboost_val,
            )

        cmd = {
            "id":          _next_id(),
            "version":     "1.0",
            "sn":          self._sn,
            "moduleType":  desc.cmd_module,
            "operateType": desc.cmd_operate,
            "params":      params,
        }
        _LOGGER.info(
            "EcoFlow: JSON SET %s turn_on=%s topic=%s cmd=%s",
            desc.key, turn_on, topic, cmd,
        )
        _LOGGER.debug(
            "EcoFlow: JSON SET detail key=%s operate=%s module=%d "
            "params=%s (no proto_builder — may be ignored by device)",
            desc.key, desc.cmd_operate, desc.cmd_module, params,
        )
        result = client.publish(topic, json.dumps(cmd), qos=1)
        _LOGGER.debug(
            "EcoFlow: JSON publish mid=%s rc=%s",
            result.mid, result.rc,
        )


    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, False)
