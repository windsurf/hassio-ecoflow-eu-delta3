"""Select platform for EcoFlow Cloud."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from . import _next_id
from .devices.delta3_1500 import (
    KEY_DC_CHG_CURRENT,
    KEY_LCD_TIMEOUT,
    KEY_STANDBY_TIME,
    KEY_AC_STANDBY_TIME,
    KEY_DC12V_STANDBY,
    DC_CHG_CURRENT_OPTIONS,
)
from .devices import wave2 as w2
from .devices import powerstream as ps
from .proto_codec import ps_build_supply_priority

_LOGGER = logging.getLogger(__name__)

# Module type constants (EcoFlow MQTT protocol)
MODULE_PD   = 1
MODULE_BMS  = 2
MODULE_INV  = 3
MODULE_MPPT = 5


@dataclass(frozen=True, kw_only=True)
class EcoFlowSelectDescription(SelectEntityDescription):
    """Select description with MQTT command definition."""
    state_key:   str
    options_map: dict[str, int]  = field(default_factory=dict)  # label → raw value
    cmd_module:  int             = 0
    cmd_operate: str             = ""
    cmd_param_key: str           = ""
    # proto_builder_sn: (raw_value, device_sn) → bytes for protobuf binary commands (PowerStream)
    proto_builder_sn: Any        = None
    entity_registry_enabled_default: bool = True


# ── Helper: build symmetric label ↔ value maps ───────────────────────────────
def _amp_map(ma_values: list[int]) -> dict[str, int]:
    """Convert list of mA values to {label: raw} dict.  4000 → '4 A'."""
    return {f"{v // 1000} A": v for v in ma_values}


_D361_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    # ── Standby / timeouts ───────────────────────────────────────────────
    # v0.2.23: moved from number to select — these are discrete options, not free values
    EcoFlowSelectDescription(
        key="screen_timeout",
        name="Screen Timeout",
        icon="mdi:monitor-off",
        state_key=KEY_LCD_TIMEOUT,
        options_map={
            "Never":   0,
            "10 sec":  10,
            "30 sec":  30,
            "1 min":   60,
            "5 min":   300,
            "30 min":  1800,
        },
        cmd_module=MODULE_PD,
        cmd_operate="lcdCfg",
        cmd_param_key="delayOff",
    ),
    EcoFlowSelectDescription(
        key="unit_standby_time",
        name="Unit Standby Time",
        icon="mdi:sleep",
        state_key=KEY_STANDBY_TIME,
        options_map={
            "Never":    0,
            "30 min":   30,
            "1 hr":     60,
            "2 hr":     120,
            "4 hr":     240,
            "6 hr":     360,
            "12 hr":    720,
            "24 hr":    1440,
        },
        cmd_module=MODULE_PD,
        cmd_operate="standbyTime",
        cmd_param_key="standbyMin",
    ),
    EcoFlowSelectDescription(
        key="ac_standby_time",
        name="AC Standby Time",
        icon="mdi:power-sleep",
        state_key=KEY_AC_STANDBY_TIME,
        options_map={
            "Never":    0,
            "30 min":   30,
            "1 hr":     60,
            "2 hr":     120,
            "4 hr":     240,
            "6 hr":     360,
            "12 hr":    720,
            "24 hr":    1440,
        },
        cmd_module=MODULE_MPPT,
        cmd_operate="standbyTime",  # confirmed: standbyTime not standby (live test 2026-04-03)
        cmd_param_key="standbyMins",
    ),
    EcoFlowSelectDescription(
        key="dc_12v_standby_time",
        name="DC 12V Standby Time",
        icon="mdi:car-clock",
        state_key=KEY_DC12V_STANDBY,
        options_map={
            "Never":    0,
            "30 min":   30,
            "1 hr":     60,
            "2 hr":     120,
            "4 hr":     240,
            "6 hr":     360,
            "12 hr":    720,
            "24 hr":    1440,
        },
        cmd_module=MODULE_MPPT,
        cmd_operate="carStandby",
        cmd_param_key="standbyMins",
    ),

    # ── DC charging ───────────────────────────────────────────────────────
    EcoFlowSelectDescription(
        key="dc_charge_current",
        name="DC Charge Current",
        icon="mdi:current-dc",
        state_key=KEY_DC_CHG_CURRENT,
        options_map=_amp_map(DC_CHG_CURRENT_OPTIONS),  # {'4 A': 4000, '6 A': 6000, '8 A': 8000}
        cmd_module=MODULE_MPPT,  # protocol analysis: p(): dcChgCfg mod=5 {"dcChgCfg": value_in_mA}
        cmd_operate="dcChgCfg",
        cmd_param_key="dcChgCfg",  # protocol verified: key is dcChgCfg not dcChgCurrent
    ),
)

from .devices.delta2_max import KEY_INV_STANDBY, KEY_DC_STANDBY_D2M

_D2M_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(
        key="screen_timeout", name="Screen Timeout", icon="mdi:monitor-off",
        state_key=KEY_LCD_TIMEOUT,
        options_map={"Never": 0, "10 sec": 10, "30 sec": 30, "1 min": 60, "5 min": 300, "30 min": 1800},
        cmd_module=MODULE_PD, cmd_operate="lcdCfg", cmd_param_key="delayOff",
    ),
    EcoFlowSelectDescription(
        key="unit_standby_time", name="Unit Standby Time", icon="mdi:sleep",
        state_key=KEY_INV_STANDBY,
        options_map={"Never": 0, "30 min": 30, "1 hr": 60, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440},
        cmd_module=MODULE_PD, cmd_operate="standbyTime", cmd_param_key="standbyMin",
    ),
    EcoFlowSelectDescription(
        key="ac_standby_time", name="AC Standby Time", icon="mdi:power-sleep",
        state_key=KEY_DC_STANDBY_D2M,
        options_map={"Never": 0, "30 min": 30, "1 hr": 60, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440},
        cmd_module=MODULE_MPPT, cmd_operate="standbyTime", cmd_param_key="standbyMins",
    ),
)

from .devices.river2 import (
    KEY_CHG_TYPE as R2_CHG_TYPE,
    KEY_SCR_STANDBY as R2_SCR_STANDBY,
    KEY_POW_STANDBY as R2_POW_STANDBY,
)

_R2_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(
        key="dc_charge_current", name="DC Charge Current", icon="mdi:current-dc",
        state_key=KEY_DC_CHG_CURRENT,
        options_map=_amp_map(DC_CHG_CURRENT_OPTIONS),
        cmd_module=MODULE_MPPT, cmd_operate="dcChgCfg", cmd_param_key="dcChgCfg",
    ),
    EcoFlowSelectDescription(
        key="dc_mode", name="DC Mode", icon="mdi:current-dc",
        state_key=R2_CHG_TYPE,
        options_map={"Auto": 0, "Solar Recharging": 1, "Car Recharging": 2},
        cmd_module=MODULE_MPPT, cmd_operate="chaType", cmd_param_key="chaType",
    ),
    EcoFlowSelectDescription(
        key="screen_timeout", name="Screen Timeout", icon="mdi:monitor-off",
        state_key=R2_SCR_STANDBY,
        options_map={"Never": 0, "10 sec": 10, "30 sec": 30, "1 min": 60, "5 min": 300, "30 min": 1800},
        cmd_module=MODULE_MPPT, cmd_operate="lcdCfg", cmd_param_key="delayOff",
    ),
    EcoFlowSelectDescription(
        key="unit_standby_time", name="Unit Standby Time", icon="mdi:sleep",
        state_key=R2_POW_STANDBY,
        options_map={"Never": 0, "30 min": 30, "1 hr": 60, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440},
        cmd_module=MODULE_MPPT, cmd_operate="standby", cmd_param_key="standbyMins",
    ),
    EcoFlowSelectDescription(
        key="ac_standby_time", name="AC Standby Time", icon="mdi:power-sleep",
        state_key=KEY_AC_STANDBY_TIME,
        options_map={"Never": 0, "30 min": 30, "1 hr": 60, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440},
        cmd_module=MODULE_MPPT, cmd_operate="acStandby", cmd_param_key="standbyMins",
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Gen 1 selects — TCP command protocol
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro as dp

UNIT_TIMEOUT_LIMITED = {"Never": 0, "30 min": 30, "1 hr": 60, "2 hr": 120, "6 hr": 360, "12 hr": 720}
AC_TIMEOUT_LIMITED   = {"Never": 0, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440}
DC_TIMEOUT_LIMITED   = {"Never": 0, "2 hr": 120, "4 hr": 240, "6 hr": 360, "12 hr": 720, "24 hr": 1440}
SCREEN_TIMEOUT_OPTS  = {"Never": 0, "10 sec": 10, "30 sec": 30, "1 min": 60, "5 min": 300, "30 min": 1800}

# Delta Pro: 4 selects (DC Charge Current, Screen, Unit Standby, AC Standby)
_DPRO_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(key="dc_charge_current", name="DC Charge Current", icon="mdi:current-dc",
        state_key=dp.KEY_DC_CHG_CURRENT, options_map=_amp_map(dp.DC_CHG_CURRENT_OPTIONS),
        cmd_module=0, cmd_operate="TCP", cmd_param_key="currMa"),
    EcoFlowSelectDescription(key="screen_timeout", name="Screen Timeout", icon="mdi:monitor-off",
        state_key=dp.KEY_LCD_TIMEOUT, options_map=SCREEN_TIMEOUT_OPTS,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="lcdTime"),
    EcoFlowSelectDescription(key="unit_standby_time", name="Unit Standby Time", icon="mdi:sleep",
        state_key=dp.KEY_STANDBY_MODE, options_map=UNIT_TIMEOUT_LIMITED,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="standByMode"),
    EcoFlowSelectDescription(key="ac_standby_time", name="AC Standby Time", icon="mdi:power-sleep",
        state_key=dp.KEY_AC_STANDBY, options_map=AC_TIMEOUT_LIMITED,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="standByMins"),
)

# River Max: 3 selects (Unit Standby, DC Timeout, AC Timeout)
_RMAX_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(key="unit_standby_time", name="Unit Standby Time", icon="mdi:sleep",
        state_key="pd.standByMode", options_map=UNIT_TIMEOUT_LIMITED,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="standByMode"),
    EcoFlowSelectDescription(key="dc_standby_time", name="DC Standby Time", icon="mdi:car-clock",
        state_key="pd.carDelayOffMin", options_map=DC_TIMEOUT_LIMITED,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="carDelayOffMin"),
    EcoFlowSelectDescription(key="ac_standby_time", name="AC Standby Time", icon="mdi:power-sleep",
        state_key="inv.cfgStandbyMin", options_map=AC_TIMEOUT_LIMITED,
        cmd_module=0, cmd_operate="TCP", cmd_param_key="standByMins"),
)

# ══════════════════════════════════════════════════════════════════════════════
# Wave 2 — 4 selects (Main Mode, Fan Speed, Remote Mode, Sub-Mode)
# JSON protocol: moduleType=1, operateType per command
# ══════════════════════════════════════════════════════════════════════════════

_W2_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(
        key="main_mode", name="Main Mode", icon="mdi:hvac",
        state_key=w2.KEY_MAIN_MODE,
        options_map={"Cool": 0, "Heat": 1, "Fan": 2},
        cmd_module=1, cmd_operate="mainMode", cmd_param_key="mainMode",
    ),
    EcoFlowSelectDescription(
        key="fan_speed", name="Fan Speed", icon="mdi:fan",
        state_key=w2.KEY_FAN_VALUE,
        options_map={"Low": 0, "Medium": 1, "High": 2},
        cmd_module=1, cmd_operate="fanValue", cmd_param_key="fanValue",
    ),
    EcoFlowSelectDescription(
        key="remote_mode", name="Remote Startup/Shutdown", icon="mdi:power",
        state_key=w2.KEY_POWER_MODE,
        options_map={"Startup": 1, "Standby": 2, "Shutdown": 3},
        cmd_module=1, cmd_operate="powerMode", cmd_param_key="powerMode",
    ),
    EcoFlowSelectDescription(
        key="sub_mode", name="Sub-Mode", icon="mdi:tune-variant",
        state_key=w2.KEY_SUB_MODE,
        options_map={"Max": 0, "Sleep": 1, "Eco": 2, "Manual": 3},
        cmd_module=1, cmd_operate="subMode", cmd_param_key="subMode",
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# PowerStream — 1 select (Power Supply Priority)
# Protobuf binary protocol: cmd_func=20, cmd_id=130
# ══════════════════════════════════════════════════════════════════════════════

_PS_SELECTS: tuple[EcoFlowSelectDescription, ...] = (
    EcoFlowSelectDescription(
        key="supply_priority", name="Power Supply Mode", icon="mdi:lightning-bolt",
        state_key=ps.KEY_SUPPLY_PRIO,
        options_map={"Prioritize power supply": 0, "Prioritize power storage": 1},
        proto_builder_sn=lambda v, sn: ps_build_supply_priority(int(v), sn),
    ),
)

# ── Description registry — keyed by device model ─────────────────────────────
SELECT_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowSelectDescription, ...]] = {
    "Delta 3 1500": _D361_SELECTS,
    "Delta 2": _D361_SELECTS,
    "Delta 2 Max": _D2M_SELECTS,
    "Delta Pro": _DPRO_SELECTS,
    "Delta Max": (),              # selects commented out in tolwi source
    "Delta Mini": _DPRO_SELECTS,  # same selects as Pro (confirmed in tolwi)
    "River 2": _R2_SELECTS,
    "River 2 Max": _R2_SELECTS,
    "River 2 Pro": _R2_SELECTS,
    "River Max": _RMAX_SELECTS,
    "River Pro": _RMAX_SELECTS,   # same selects as Max (confirmed in tolwi)
    "River Mini": (),
    "PowerStream": _PS_SELECTS,
    "PowerStream 600W": _PS_SELECTS,
    "PowerStream 800W": _PS_SELECTS,
    "Glacier": (),  # no selects (tolwi confirms empty)
    "Wave 2": _W2_SELECTS,
}


def _get_select_descriptions(model: str) -> tuple[EcoFlowSelectDescription, ...]:
    """Get select descriptions for a device model. Falls back to empty tuple."""
    return SELECT_DESCRIPTIONS_BY_MODEL.get(model, ())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow select entities from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]
    device_model = entry_data.get("device_model", "Delta 3 1500")

    descriptions = _get_select_descriptions(device_model)

    async_add_entities(
        EcoFlowSelectEntity(coordinator, desc, entry_data, sn, device_model)
        for desc in descriptions
    )


class EcoFlowSelectEntity(CoordinatorEntity[EcoflowCoordinator], SelectEntity):
    """A select entity for an EcoFlow discrete parameter."""

    entity_description: EcoFlowSelectDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowSelectDescription,
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
        # Build reverse map: raw value → label
        self._value_to_label: dict[int, str] = {
            v: k for k, v in description.options_map.items()
        }
        self._attr_options = list(description.options_map.keys())

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None
        raw = self.coordinator.data.get(self.entity_description.state_key)
        if raw is None:
            return None
        return self._value_to_label.get(int(raw))

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)

    def _publish(self, raw_value: int) -> None:
        desc   = self.entity_description
        params = {desc.cmd_param_key: raw_value}

        # ── Priority 1: REST API SET (Developer API) ─────────────────────
        rest_api = self._entry_data.get("rest_api")
        if rest_api is not None and desc.cmd_operate:
            try:
                rest_api.set_quota(desc.cmd_module, desc.cmd_operate, params)
                _LOGGER.info(
                    "EcoFlow: REST SET select %s value=%s module=%d operate=%s",
                    desc.key, raw_value, desc.cmd_module, desc.cmd_operate,
                )
                return
            except Exception as exc:
                _LOGGER.warning(
                    "EcoFlow: REST SET select %s failed (%s) — falling back to MQTT",
                    desc.key, exc,
                )

        # ── Priority 2: Protobuf binary MQTT SET (PowerStream) ─────────
        if desc.proto_builder_sn is not None:
            client = self._entry_data.get("mqtt_client")
            topic  = self._entry_data.get("mqtt_topic_set")
            if not client or not topic:
                _LOGGER.error("EcoFlow: no MQTT client — cannot send %s proto command", desc.key)
                return
            payload = desc.proto_builder_sn(raw_value, self._sn)
            _LOGGER.info(
                "EcoFlow: PROTO SET select %s value=%s topic=%s len=%d",
                desc.key, raw_value, topic, len(payload),
            )
            result = client.publish(topic, payload, qos=1)
            _LOGGER.debug("EcoFlow: Proto publish mid=%s rc=%s", result.mid, result.rc)
            return

        # ── Priority 3: JSON MQTT SET (fallback) ─────────────────────────
        client = self._entry_data.get("mqtt_client")
        topic  = self._entry_data.get("mqtt_topic_set")
        if not client or not topic:
            _LOGGER.error("No MQTT client and no REST API — cannot send select command")
            return
        cmd = {
            "id":          _next_id(),
            "version":     "1.1",
            "sn":          self._sn,
            "moduleType":  desc.cmd_module,
            "operateType": desc.cmd_operate,
            "params":      params,
        }
        _LOGGER.info("EcoFlow: JSON SET select %s value=%s (no REST — may be ignored)", desc.key, raw_value)
        result = client.publish(topic, json.dumps(cmd), qos=0)
        _LOGGER.debug("EcoFlow: Select publish mid=%s rc=%s", result.mid, result.rc)

    async def async_select_option(self, option: str) -> None:
        raw = self.entity_description.options_map.get(option)
        if raw is None:
            _LOGGER.error("Unknown option '%s' for %s", option, self.entity_description.key)
            return
        await self.hass.async_add_executor_job(self._publish, raw)
