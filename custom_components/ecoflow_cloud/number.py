"""Number platform for EcoFlow Cloud."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from . import _next_id
from .devices.delta3_1500 import (
    DEVICE_MODEL,
    KEY_EMS_MAX_CHG_SOC,
    KEY_EMS_MIN_DSG_SOC,
    KEY_LCD_BRIGHTNESS,
    KEY_LCD_TIMEOUT,
    KEY_STANDBY_TIME,
    KEY_AC_STANDBY_TIME,
    KEY_MPPT_CFG_CHG_W,
    KEY_DC12V_STANDBY,
    KEY_MIN_AC_SOC,
    KEY_BP_POWER_SOC,
    KEY_GEN_MIN_SOC,
    KEY_GEN_MAX_SOC,
    AC_CHG_WATTS_MIN,
    AC_CHG_WATTS_MAX,
    AC_CHG_WATTS_STEP,
)

_LOGGER = logging.getLogger(__name__)

# Module type constants (EcoFlow MQTT protocol) — mirrors switch.py
MODULE_PD   = 1
MODULE_BMS  = 2
MODULE_INV  = 3
MODULE_MPPT = 5


@dataclass(frozen=True, kw_only=True)
class EcoFlowNumberDescription(NumberEntityDescription):
    """Number description with MQTT command definition."""
    state_key:      str
    cmd_module:     int   = 0
    cmd_operate:    str   = ""
    cmd_param_key:  str   = ""
    cmd_params_fn:  Any   = None


NUMBER_DESCRIPTIONS: tuple[EcoFlowNumberDescription, ...] = (
    # ── AC Charging ───────────────────────────────────────────────────────
    EcoFlowNumberDescription(
        key="ac_charging_speed",
        name="AC Charging Speed",
        native_unit_of_measurement="W",
        native_min_value=AC_CHG_WATTS_MIN,
        native_max_value=AC_CHG_WATTS_MAX,
        native_step=AC_CHG_WATTS_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:transmission-tower-import",
        state_key=KEY_MPPT_CFG_CHG_W,  # mppt.cfgChgWatts — configured charge power limit
        cmd_module=MODULE_MPPT,
        cmd_operate="acChgCfg",
        cmd_params_fn=lambda v: {
            "chgWatts":     int(v),
            "chgPauseFlag": 255,  # 255 = keep current pause state unchanged
        },
    ),

    # ── Charge / discharge limits ─────────────────────────────────────────
    EcoFlowNumberDescription(
        key="max_charge_level",
        name="Max Charge Level",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-arrow-up",
        state_key=KEY_EMS_MAX_CHG_SOC,
        cmd_module=MODULE_BMS,
        cmd_operate="maxChargeSoc",
        cmd_param_key="maxChargeSoc",
    ),
    EcoFlowNumberDescription(
        key="min_discharge_level",
        name="Min Discharge Level",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=30,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-arrow-down",
        state_key=KEY_EMS_MIN_DSG_SOC,
        cmd_module=MODULE_BMS,
        cmd_operate="minDsgSoc",
        cmd_param_key="minDsgSoc",
    ),
    EcoFlowNumberDescription(
        key="generator_start_soc",
        name="Generator Start SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=30,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:engine-outline",
        state_key=KEY_GEN_MIN_SOC,
        cmd_module=MODULE_BMS,
        cmd_operate="openOilSoc",
        cmd_param_key="openOilSoc",
    ),
    EcoFlowNumberDescription(
        key="generator_stop_soc",
        name="Generator Stop SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:engine-off-outline",
        state_key=KEY_GEN_MAX_SOC,
        cmd_module=MODULE_BMS,
        cmd_operate="closeOilSoc",
        cmd_param_key="closeOilSoc",
    ),
    EcoFlowNumberDescription(
        key="battery_protection_soc",
        name="Battery Protection SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-lock",
        state_key=KEY_BP_POWER_SOC,
        cmd_module=MODULE_PD,
        cmd_operate="watthConfig",
        cmd_params_fn=lambda v: {
            "isConfig":   1,
            "bpPowerSoc": int(v),
            "minDsgSoc":  255,
            "minChgSoc":  255,
        },
    ),
    EcoFlowNumberDescription(
        key="min_soc_for_ac_auto_on",
        name="Min SOC for AC Auto-On",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:power-plug-outline",
        state_key=KEY_MIN_AC_SOC,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params_fn=lambda v: {
            "acAutoOutConfig": 255,
            "minAcOutSoc": int(v),
        },
    ),

    # ── Standby times ─────────────────────────────────────────────────────
    EcoFlowNumberDescription(
        key="device_standby_time",
        name="Device Standby Time",
        native_unit_of_measurement="min",
        native_min_value=0,
        native_max_value=1440,
        native_step=30,
        mode=NumberMode.BOX,
        icon="mdi:sleep",
        state_key=KEY_STANDBY_TIME,
        cmd_module=MODULE_PD,
        cmd_operate="standbyTime",
        cmd_param_key="standbyMin",
    ),
    EcoFlowNumberDescription(
        key="ac_output_standby_time",
        name="AC Output Standby Time",
        native_unit_of_measurement="min",
        native_min_value=0,
        native_max_value=720,
        native_step=30,
        mode=NumberMode.BOX,
        icon="mdi:power-sleep",
        state_key=KEY_AC_STANDBY_TIME,
        cmd_module=MODULE_MPPT,
        cmd_operate="standbyTime",
        cmd_param_key="standbyMins",
    ),
    EcoFlowNumberDescription(
        key="dc_12v_standby_time",
        name="DC 12V Standby Time",
        native_unit_of_measurement="min",
        native_min_value=0,
        native_max_value=720,
        native_step=30,
        mode=NumberMode.BOX,
        icon="mdi:car-clock",
        state_key=KEY_DC12V_STANDBY,
        cmd_module=MODULE_MPPT,
        cmd_operate="carStandby",
        cmd_param_key="standbyMins",
    ),

    # ── Display ───────────────────────────────────────────────────────────
    EcoFlowNumberDescription(
        key="lcd_brightness",
        name="LCD Brightness",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=25,
        mode=NumberMode.SLIDER,
        icon="mdi:brightness-percent",
        state_key=KEY_LCD_BRIGHTNESS,
        cmd_module=MODULE_PD,
        cmd_operate="lcdCfg",
        cmd_param_key="brightness",
    ),
    EcoFlowNumberDescription(
        key="lcd_timeout",
        name="LCD Timeout",
        native_unit_of_measurement="s",
        native_min_value=0,
        native_max_value=300,
        native_step=30,
        mode=NumberMode.BOX,
        icon="mdi:monitor-off",
        state_key=KEY_LCD_TIMEOUT,
        cmd_module=MODULE_PD,
        cmd_operate="lcdCfg",
        cmd_param_key="delayOff",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]

    async_add_entities(
        EcoFlowNumberEntity(coordinator, desc, entry_data, sn)
        for desc in NUMBER_DESCRIPTIONS
    )


class EcoFlowNumberEntity(CoordinatorEntity[EcoflowCoordinator], NumberEntity):
    """A configurable numeric parameter on the EcoFlow device."""

    entity_description: EcoFlowNumberDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowNumberDescription,
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
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self, value: float) -> None:
        desc = self.entity_description
        if desc.cmd_params_fn is not None:
            params = desc.cmd_params_fn(value)
        else:
            params = {desc.cmd_param_key: int(value)}

        # ── Priority 1: REST API SET (Developer API) ─────────────────────
        rest_api = self._entry_data.get("rest_api")
        if rest_api is not None and desc.cmd_operate:
            try:
                rest_api.set_quota(desc.cmd_module, desc.cmd_operate, params)
                _LOGGER.info(
                    "EcoFlow: REST SET number %s value=%s module=%d operate=%s",
                    desc.key, value, desc.cmd_module, desc.cmd_operate,
                )
                return
            except Exception as exc:
                _LOGGER.warning(
                    "EcoFlow: REST SET number %s failed (%s) — falling back to MQTT",
                    desc.key, exc,
                )

        # ── Priority 2: JSON MQTT SET (fallback) ─────────────────────────
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")
        if not client or not topic:
            _LOGGER.error("No MQTT client and no REST API — cannot send number command")
            return
        cmd = {
            "id":          _next_id(),
            "version":     "1.0",
            "sn":          self._sn,
            "moduleType":  desc.cmd_module,
            "operateType": desc.cmd_operate,
            "params":      params,
        }
        _LOGGER.info("EcoFlow: JSON SET number %s value=%s (no REST — may be ignored)", desc.key, value)
        result = client.publish(topic, json.dumps(cmd), qos=0)
        _LOGGER.debug("EcoFlow: Number publish mid=%s rc=%s", result.mid, result.rc)

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(self._publish, value)
