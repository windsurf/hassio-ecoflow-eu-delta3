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

from .const import DOMAIN, MANUFACTURER, CHG_WATTS_SENTINEL
from .coordinator import EcoflowCoordinator
from . import _next_id
from .devices.delta3_1500 import (
    KEY_EMS_MAX_CHG_SOC,
    KEY_EMS_MIN_DSG_SOC,
    KEY_LCD_BRIGHTNESS,
    KEY_MPPT_CFG_CHG_W,
    KEY_MIN_AC_SOC,
    KEY_BP_POWER_SOC,
    KEY_GEN_MIN_SOC,
    KEY_GEN_MAX_SOC,
    KEY_SCR_STANDBY,
    KEY_POW_STANDBY,
    AC_CHG_WATTS_MIN,
    AC_CHG_WATTS_MAX,
    AC_CHG_WATTS_STEP,
)

_LOGGER = logging.getLogger(__name__)

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
    # v0.2.23: read_only=True means the entity is a sensor-like number —
    # state is shown but no SET command is sent (operateType unknown)
    read_only:      bool  = False


_D361_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
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
        # v0.2.23: shadow state — cfgChgWatts=255 is sentinel, never written to HA state
        state_key=KEY_MPPT_CFG_CHG_W,
        cmd_module=MODULE_MPPT,
        cmd_operate="acChgCfg",
        cmd_params_fn=lambda v: {
            "chgWatts":     int(v),
            "chgPauseFlag": 255,  # 255 = keep current pause state
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
        cmd_operate="upsConfig",
        cmd_param_key="maxChgSoc",
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
        cmd_operate="dsgCfg",
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

    # ── Backup Reserve ────────────────────────────────────────────────────
    # battery_protection_soc removed — identical to min_discharge_level (same key + command)
    EcoFlowNumberDescription(
        key="backup_reserve_soc",
        name="Backup Reserve SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-charging-medium",
        state_key=KEY_BP_POWER_SOC,
        cmd_module=MODULE_PD,
        cmd_operate="watthConfig",
        cmd_params_fn=lambda v: {
            "isConfig":   1,
            "bpPowerSoc": int(v),
            "minDsgSoc":  0,
            "minChgSoc":  0,
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
        entity_registry_enabled_default=False,
        state_key=KEY_MIN_AC_SOC,
        cmd_module=MODULE_PD,
        cmd_operate="acAutoOutConfig",
        cmd_params_fn=lambda v: {
            "acAutoOutConfig": 255,
            "minAcOutSoc": int(v),
        },
    ),


    # v0.2.23: nieuwe standby numbers — operateType nog onbekend, read_only voorlopig
    EcoFlowNumberDescription(
        key="screen_standby_time",
        name="Screen Standby Time",
        native_unit_of_measurement="min",
        native_min_value=0,
        native_max_value=720,
        native_step=1,
        mode=NumberMode.BOX,
        icon="mdi:monitor",
        entity_registry_enabled_default=False,
        state_key=KEY_SCR_STANDBY,
        read_only=True,  # operateType unknown — read-only until confirmed
    ),
    EcoFlowNumberDescription(
        key="overall_standby_time",
        name="Overall Standby Time",
        native_unit_of_measurement="min",
        native_min_value=0,
        native_max_value=1440,
        native_step=1,
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False,
        state_key=KEY_POW_STANDBY,
        read_only=True,  # operateType unknown — read-only until confirmed
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
        entity_registry_enabled_default=False,
        state_key=KEY_LCD_BRIGHTNESS,
        cmd_module=MODULE_PD,
        cmd_operate="lcdCfg",
        cmd_params_fn=lambda v: {"brighLevel": int(v), "delayOff": 65535},
    ),

)

# ══════════════════════════════════════════════════════════════════════════════
# Delta 2 — 6 numbers
# Source: tolwi/hassio-ecoflow-cloud (internal/delta2.py)
# Differences vs D361: AC charging max 1200W, generator start/stop levels added
# ══════════════════════════════════════════════════════════════════════════════

from .devices.delta2 import (
    AC_CHG_WATTS_MIN as D2_AC_MIN,
    AC_CHG_WATTS_MAX as D2_AC_MAX,
    AC_CHG_WATTS_STEP as D2_AC_STEP,
)

_D2_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="ac_charging_speed",
        name="AC Charging Speed",
        native_unit_of_measurement="W",
        native_min_value=D2_AC_MIN,
        native_max_value=D2_AC_MAX,
        native_step=D2_AC_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:transmission-tower-import",
        state_key=KEY_MPPT_CFG_CHG_W,
        cmd_module=MODULE_MPPT,
        cmd_operate="acChgCfg",
        cmd_params_fn=lambda v: {
            "chgWatts":     int(v),
            "chgPauseFlag": 255,
        },
    ),
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
        cmd_operate="upsConfig",
        cmd_param_key="maxChgSoc",
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
        cmd_operate="dsgCfg",
        cmd_param_key="minDsgSoc",
    ),
    EcoFlowNumberDescription(
        key="backup_reserve_soc",
        name="Backup Reserve SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-charging-medium",
        state_key=KEY_BP_POWER_SOC,
        cmd_module=MODULE_PD,
        cmd_operate="watthConfig",
        cmd_params_fn=lambda v: {
            "isConfig":   1,
            "bpPowerSoc": int(v),
            "minDsgSoc":  0,
            "minChgSoc":  0,
        },
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
)

from .devices.delta2_max import (
    AC_CHG_WATTS_MIN as D2M_AC_MIN,
    AC_CHG_WATTS_MAX as D2M_AC_MAX,
    AC_CHG_WATTS_STEP as D2M_AC_STEP,
    KEY_AC_CHG_W_D2M, KEY_GEN_START_D2M, KEY_GEN_STOP_D2M,
    KEY_INV_STANDBY,
)

_D2M_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="ac_charging_speed", name="AC Charging Speed",
        native_unit_of_measurement="W",
        native_min_value=D2M_AC_MIN, native_max_value=D2M_AC_MAX, native_step=D2M_AC_STEP,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=KEY_AC_CHG_W_D2M,
        cmd_module=MODULE_INV, cmd_operate="acChgCfg",
        cmd_params_fn=lambda v: {"slowChgWatts": int(v), "fastChgWatts": 2000, "chgPauseFlag": 0},
    ),
    EcoFlowNumberDescription(
        key="max_charge_level", name="Max Charge Level",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=KEY_EMS_MAX_CHG_SOC,
        cmd_module=MODULE_BMS, cmd_operate="upsConfig", cmd_param_key="maxChgSoc",
    ),
    EcoFlowNumberDescription(
        key="min_discharge_level", name="Min Discharge Level",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
        state_key=KEY_EMS_MIN_DSG_SOC,
        cmd_module=MODULE_BMS, cmd_operate="dsgCfg", cmd_param_key="minDsgSoc",
    ),
    EcoFlowNumberDescription(
        key="backup_reserve_soc", name="Backup Reserve SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-medium",
        state_key=KEY_BP_POWER_SOC,
        cmd_module=MODULE_PD, cmd_operate="watthConfig",
        cmd_params_fn=lambda v: {"isConfig": 1, "bpPowerSoc": int(v), "minDsgSoc": 0, "minChgSoc": 0},
    ),
    EcoFlowNumberDescription(
        key="generator_start_soc", name="Generator Start SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:engine-outline",
        state_key=KEY_GEN_START_D2M,
        cmd_module=MODULE_BMS, cmd_operate="openOilSoc", cmd_param_key="openOilSoc",
    ),
    EcoFlowNumberDescription(
        key="generator_stop_soc", name="Generator Stop SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:engine-off-outline",
        state_key=KEY_GEN_STOP_D2M,
        cmd_module=MODULE_BMS, cmd_operate="closeOilSoc", cmd_param_key="closeOilSoc",
    ),
)

from .devices.river2 import (
    AC_CHG_WATTS_MIN as R2_AC_MIN, AC_CHG_WATTS_MAX as R2_AC_MAX, AC_CHG_WATTS_STEP as R2_AC_STEP,
    R2MAX_AC_CHG_MIN, R2MAX_AC_CHG_MAX, R2MAX_AC_CHG_STEP,
    R2PRO_AC_CHG_MIN, R2PRO_AC_CHG_MAX, R2PRO_AC_CHG_STEP,
)

def _r2_numbers(ac_min, ac_max, ac_step, with_backup=True):
    """Build River 2 number descriptions with per-variant AC charging limits."""
    nums = [
        EcoFlowNumberDescription(
            key="ac_charging_speed", name="AC Charging Speed",
            native_unit_of_measurement="W",
            native_min_value=ac_min, native_max_value=ac_max, native_step=ac_step,
            mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
            state_key=KEY_MPPT_CFG_CHG_W, cmd_module=MODULE_MPPT, cmd_operate="acChgCfg",
            cmd_params_fn=lambda v: {"chgWatts": int(v), "chgPauseFlag": 255},
        ),
        EcoFlowNumberDescription(
            key="max_charge_level", name="Max Charge Level",
            native_unit_of_measurement=PERCENTAGE,
            native_min_value=50, native_max_value=100, native_step=5,
            mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
            state_key=KEY_EMS_MAX_CHG_SOC, cmd_module=MODULE_BMS, cmd_operate="upsConfig", cmd_param_key="maxChgSoc",
        ),
        EcoFlowNumberDescription(
            key="min_discharge_level", name="Min Discharge Level",
            native_unit_of_measurement=PERCENTAGE,
            native_min_value=0, native_max_value=30, native_step=5,
            mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
            state_key=KEY_EMS_MIN_DSG_SOC, cmd_module=MODULE_BMS, cmd_operate="dsgCfg", cmd_param_key="minDsgSoc",
        ),
    ]
    if with_backup:
        nums.append(EcoFlowNumberDescription(
            key="backup_reserve_soc", name="Backup Reserve SOC",
            native_unit_of_measurement=PERCENTAGE,
            native_min_value=5, native_max_value=100, native_step=5,
            mode=NumberMode.SLIDER, icon="mdi:battery-charging-medium",
            state_key=KEY_BP_POWER_SOC, cmd_module=MODULE_PD, cmd_operate="watthConfig",
            cmd_params_fn=lambda v: {"isConfig": 1, "bpPowerSoc": int(v), "minDsgSoc": 0, "minChgSoc": 0},
        ))
    return tuple(nums)

_R2_NUMBERS:    tuple[EcoFlowNumberDescription, ...] = _r2_numbers(R2_AC_MIN, R2_AC_MAX, R2_AC_STEP)
_R2MAX_NUMBERS: tuple[EcoFlowNumberDescription, ...] = _r2_numbers(R2MAX_AC_CHG_MIN, R2MAX_AC_CHG_MAX, R2MAX_AC_CHG_STEP)
_R2PRO_NUMBERS: tuple[EcoFlowNumberDescription, ...] = _r2_numbers(R2PRO_AC_CHG_MIN, R2PRO_AC_CHG_MAX, R2PRO_AC_CHG_STEP, with_backup=False)

# ── Description registry — keyed by device model ─────────────────────────────
NUMBER_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowNumberDescription, ...]] = {
    "Delta 3 1500": _D361_NUMBERS,
    "Delta 2": _D2_NUMBERS,
    "Delta 2 Max": _D2M_NUMBERS,
    "Delta Pro": (),   # TCP commands not yet supported
    "Delta Max": (),
    "Delta Mini": (),
    "River 2": _R2_NUMBERS,
    "River 2 Max": _R2MAX_NUMBERS,
    "River 2 Pro": _R2PRO_NUMBERS,
    "River Max": (),   # Gen 1 TCP commands not yet supported
    "River Pro": (),
    "River Mini": (),
}


def _get_number_descriptions(model: str) -> tuple[EcoFlowNumberDescription, ...]:
    """Get number descriptions for a device model. Falls back to empty tuple."""
    return NUMBER_DESCRIPTIONS_BY_MODEL.get(model, ())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]
    device_model = entry_data.get("device_model", "Delta 3 1500")

    descriptions = _get_number_descriptions(device_model)

    async_add_entities(
        EcoFlowNumberEntity(coordinator, desc, entry_data, sn, device_model)
        for desc in descriptions
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
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        val = self.coordinator.data.get(self.entity_description.state_key)

        # AC Charging Speed: 255 is sentinel — never show it, use minimum as fallback.
        # Real values (set via app or HA) arrive via telemetry push and are stored
        # in coordinator.data without filtering. The quotaMap filter in coordinator.py
        # prevents 255 from overwriting a real value during keepalive GET-ALL.
        if self.entity_description.key == "ac_charging_speed":
            try:
                raw = int(val) if val is not None else None
            except (TypeError, ValueError):
                raw = None
            if raw is None or raw == CHG_WATTS_SENTINEL:
                return float(AC_CHG_WATTS_MIN)
            return float(raw)

        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self, value: float) -> None:
        desc = self.entity_description

        if desc.read_only:
            _LOGGER.warning(
                "EcoFlow: %s is read-only (operateType unknown) — SET ignored",
                desc.key,
            )
            return

        if desc.cmd_params_fn is not None:
            params = desc.cmd_params_fn(value)
        else:
            params = {desc.cmd_param_key: int(value)}

        # Priority 1: REST API SET
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
                _LOGGER.debug(
                    "EcoFlow: REST SET number %s failed (%s) — falling back to MQTT",
                    desc.key, exc,
                )

        # Priority 2: JSON MQTT SET
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
            "from":        "Android",
            "params":      params,
        }
        _LOGGER.info(
            "EcoFlow: JSON SET number %s value=%s topic=%s params=%s",
            desc.key, value, topic, params,
        )
        result = client.publish(topic, json.dumps(cmd), qos=1)
        _LOGGER.debug("EcoFlow: Number publish mid=%s rc=%s", result.mid, result.rc)

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(self._publish, value)
