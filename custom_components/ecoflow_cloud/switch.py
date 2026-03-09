"""Switch platform for EcoFlow Cloud."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from .devices.delta3_1500 import (
    DEVICE_MODEL,
    KEY_AC_ENABLED,
    KEY_AC_XBOOST,
    KEY_CAR_OUT_STATE,
    KEY_DC_OUT_STATE,
    KEY_AC_CHG_PAUSE,
    KEY_BEEP_MODE,
    KEY_PV_CHG_PRIO,
    KEY_AC_AUTO_ON,
    KEY_AC_AUTO_OUT,
    KEY_EMS_UPS_FLAG,
    KEY_DC24V_STATE,
)

_LOGGER = logging.getLogger(__name__)

# Module type constants (EcoFlow MQTT protocol)
MODULE_PD   = 1
MODULE_BMS  = 2
MODULE_INV  = 3
MODULE_MPPT = 5


@dataclass(frozen=True, kw_only=True)
class EcoFlowSwitchDescription(SwitchEntityDescription):
    """Switch description with MQTT command definition."""
    state_key:    str
    cmd_module:   int   = 0
    cmd_operate:  str   = ""
    cmd_params:   Any   = None
    inverted:     bool  = False
    entity_registry_enabled_default: bool = True


SWITCH_DESCRIPTIONS: tuple[EcoFlowSwitchDescription, ...] = (
    # ── Outputs ──────────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="ac_output",
        name="AC Enabled",
        icon="mdi:power-socket-eu",
        state_key=KEY_AC_ENABLED,
        cmd_module=MODULE_INV,
        cmd_operate="acOutCfg",
        cmd_params=lambda on: {
            "enabled": 1 if on else 0,
            "xboost":  255,
            "outFreq": 255,
            "outVol":  255,
        },
    ),
    EcoFlowSwitchDescription(
        key="xboost",
        name="X-Boost",
        icon="mdi:lightning-bolt",
        state_key=KEY_AC_XBOOST,
        cmd_module=MODULE_INV,
        cmd_operate="acOutCfg",
        cmd_params=lambda on: {
            "enabled": 255,
            "xboost":  1 if on else 0,
            "outFreq": 255,
            "outVol":  255,
        },
    ),
    EcoFlowSwitchDescription(
        key="dc_output",
        name="DC (12V) Enabled",
        icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE,
        cmd_module=MODULE_MPPT,
        cmd_operate="dcOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="dc24v_output",
        name="DC (24V) Enabled",
        icon="mdi:car-battery",
        state_key=KEY_DC24V_STATE,
        cmd_module=MODULE_MPPT,
        cmd_operate="dc24vCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),

    # ── AC Charging ───────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="ac_charging_230v",
        name="AC Charging (230V)",
        icon="mdi:transmission-tower",
        state_key=KEY_AC_CHG_PAUSE,
        # chgPauseFlag=0 means charging ACTIVE → switch ON
        # chgPauseFlag=1 means charging PAUSED → switch OFF
        inverted=True,
        cmd_module=MODULE_MPPT,
        cmd_operate="acChgCfg",
        # slowChgWatts/fastChgWatts=255 means "keep current setting"
        cmd_params=lambda on: {
            "slowChgWatts": 255,
            "fastChgWatts": 255,
            "chgPauseFlag": 0 if on else 1,
        },
    ),

    # ── Charging behaviour ────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="pv_charge_priority",
        name="Prio Solar Charging",
        icon="mdi:solar-power",
        state_key=KEY_PV_CHG_PRIO,
        cmd_module=MODULE_MPPT,
        cmd_operate="pvChangeSet",
        cmd_params=lambda on: {"pvChangeSet": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_auto_on",
        name="AC Auto On",
        icon="mdi:power-plug-outline",
        state_key=KEY_AC_AUTO_ON,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params=lambda on: {"acAutoOutConfig": 1 if on else 0, "minAcOutSoc": 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_always_on",
        name="AC Always On",
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
    ),

    # ── System ───────────────────────────────────────────────────────────
    EcoFlowSwitchDescription(
        key="beep",
        name="Beeper",
        icon="mdi:volume-high",
        state_key=KEY_BEEP_MODE,
        cmd_module=MODULE_PD,
        cmd_operate="beepCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
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
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")
        if not client or not topic:
            _LOGGER.error("MQTT client unavailable — cannot send switch command")
            return
        cmd = {
            "id":          str(int(time.time() * 1000)),
            "version":     "1.0",
            "sn":          self._sn,
            "moduleType":  self.entity_description.cmd_module,
            "operateType": self.entity_description.cmd_operate,
            "params":      self.entity_description.cmd_params(turn_on),
        }
        _LOGGER.warning("Switch command → %s : %s", topic, cmd)
        client.publish(topic, json.dumps(cmd), qos=1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, False)
