"""Button platform for EcoFlow Cloud."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from . import _next_id

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EcoFlowButtonDescription(ButtonEntityDescription):
    """Button description with MQTT command definition."""
    cmd_module:  int  = 0
    cmd_operate: str  = ""
    cmd_params:  Any  = None   # static dict or callable() → dict
    dp3_cmd_key: str  = ""     # if set, use Delta Pro 3 command envelope


# ══════════════════════════════════════════════════════════════════════════════
# Glacier — 3 buttons (Make Small Ice, Make Large Ice, Detach Ice)
# JSON protocol: moduleType=1, operateType per command
# Source: tolwi/hassio-ecoflow-cloud (internal/glacier.py buttons())
# ══════════════════════════════════════════════════════════════════════════════

_GL_BUTTONS: tuple[EcoFlowButtonDescription, ...] = (
    EcoFlowButtonDescription(
        key="make_small_ice", name="Make Small Ice", icon="mdi:snowflake",
        cmd_module=1, cmd_operate="iceMake",
        cmd_params={"enable": 1, "iceShape": 0},
    ),
    EcoFlowButtonDescription(
        key="make_large_ice", name="Make Large Ice", icon="mdi:snowflake",
        cmd_module=1, cmd_operate="iceMake",
        cmd_params={"enable": 1, "iceShape": 1},
    ),
    EcoFlowButtonDescription(
        key="detach_ice", name="Detach Ice", icon="mdi:snowflake-off",
        cmd_module=1, cmd_operate="deIce",
        cmd_params={"enable": 1},
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro 3 (DGEA) — Power Off button
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro_3 as dp3_btn

_DP3_BUTTONS: tuple[EcoFlowButtonDescription, ...] = (
    EcoFlowButtonDescription(
        key="dp3_power_off", name="Power Off", icon="mdi:power-off",
        dp3_cmd_key=dp3_btn.CMD_POWER_OFF,
    ),
)

# ── Description registry — keyed by device model ─────────────────────────────
BUTTON_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowButtonDescription, ...]] = {
    "Delta 3 1500": (),
    "Delta 3 Plus": (),
    "Delta 3 Max": (),
    "Delta 2": (),
    "Delta 2 Max": (),
    "Delta Pro": (),
    "Delta Max": (),
    "Delta Mini": (),
    "River 2": (),
    "River 2 Max": (),
    "River 2 Pro": (),
    "River Max": (),
    "River Pro": (),
    "River Mini": (),
    "PowerStream": (),
    "PowerStream 600W": (),
    "PowerStream 800W": (),
    "Glacier": _GL_BUTTONS,
    "Wave 2": (),
    "Smart Plug": (),  # no buttons
    "Delta Pro 3": _DP3_BUTTONS,
    "Delta Pro Ultra": (),  # no button commands in DPU developer docs
    "River 3": (),          # no button commands in community docs
    "River 3 Plus": (),     # no button commands in community docs
    "Stream AC": (),        # no button commands
    "Stream AC Pro": (),    # no button commands
    "Stream Ultra": (),     # no button commands
}


# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro 3 (DGEA) — Power Off button
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro_3 as dp3_btn

_DP3_BUTTONS: tuple[EcoFlowButtonDescription, ...] = (
    EcoFlowButtonDescription(
        key="dp3_power_off", name="Power Off", icon="mdi:power-off",
        dp3_cmd_key=dp3_btn.CMD_POWER_OFF,
    ),
)


def _get_button_descriptions(model: str) -> tuple[EcoFlowButtonDescription, ...]:
    """Get button descriptions for a device model. Falls back to empty tuple."""
    return BUTTON_DESCRIPTIONS_BY_MODEL.get(model, ())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow buttons from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]
    device_model = entry_data.get("device_model", "Delta 3 1500")

    descriptions = _get_button_descriptions(device_model)

    async_add_entities(
        EcoFlowButtonEntity(coordinator, desc, entry_data, sn, device_model)
        for desc in descriptions
    )


class EcoFlowButtonEntity(CoordinatorEntity[EcoflowCoordinator], ButtonEntity):
    """A one-shot command button on the EcoFlow device."""

    entity_description: EcoFlowButtonDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowButtonDescription,
        entry_data: dict,
        sn: str,
        device_model: str = "Delta 3 1500",
    ) -> None:
        super().__init__(coordinator)
        self.entity_description  = description
        self._entry_data         = entry_data
        self._sn                 = sn
        self._attr_unique_id     = f"{sn}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info   = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=f"EcoFlow {device_model}",
            manufacturer=MANUFACTURER,
            model=device_model,
        )

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self) -> None:
        desc = self.entity_description

        params = desc.cmd_params if isinstance(desc.cmd_params, dict) else desc.cmd_params()

        # Priority 1: REST API SET
        rest_api = self._entry_data.get("rest_api")
        if rest_api is not None and desc.cmd_operate:
            try:
                rest_api.set_quota(desc.cmd_module, desc.cmd_operate, params)
                _LOGGER.info(
                    "EcoFlow: REST SET button %s module=%d operate=%s params=%s",
                    desc.key, desc.cmd_module, desc.cmd_operate, params,
                )
                return
            except Exception as exc:
                _LOGGER.debug(
                    "EcoFlow: REST SET button %s failed (%s) — falling back to MQTT",
                    desc.key, exc,
                )

        # Priority 2: JSON MQTT SET
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")
        if not client or not topic:
            _LOGGER.error("EcoFlow: no MQTT client — cannot send button %s command", desc.key)
            return

        # Priority 2.5: Delta Pro 3 envelope
        if desc.dp3_cmd_key:
            from .devices.delta_pro_3 import DP3_CMD_ID, DP3_CMD_FUNC, DP3_DEST, DP3_DIR_DEST, DP3_DIR_SRC
            cmd = {
                "sn":       self._sn,
                "id":       _next_id(),
                "version":  "1.0",
                "cmdId":    DP3_CMD_ID,
                "dirDest":  DP3_DIR_DEST,
                "dirSrc":   DP3_DIR_SRC,
                "cmdFunc":  DP3_CMD_FUNC,
                "dest":     DP3_DEST,
                "needAck":  True,
                "params":   {desc.dp3_cmd_key: True},
            }
            _LOGGER.info("EcoFlow: DP3 button %s topic=%s key=%s", desc.key, topic, desc.dp3_cmd_key)
            result = client.publish(topic, json.dumps(cmd), qos=1)
            _LOGGER.debug("EcoFlow: DP3 button publish mid=%s rc=%s", result.mid, result.rc)
            return

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
            "EcoFlow: JSON SET button %s topic=%s params=%s",
            desc.key, topic, params,
        )
        result = client.publish(topic, json.dumps(cmd), qos=1)
        _LOGGER.debug("EcoFlow: Button publish mid=%s rc=%s", result.mid, result.rc)

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self._publish)
