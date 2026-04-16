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
from .devices import glacier as gl
from .devices import wave2 as w2
from .devices import powerstream as ps
from .proto_codec import (
    ps_build_permanent_watts,
    ps_build_bat_lower,
    ps_build_bat_upper,
    ps_build_brightness,
    sp_build_brightness as sp_build_brightness_fn,
    sp_build_max_watts,
)
from .devices import smart_plug as sp

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
    # cmd_params_coord_fn: like cmd_params_fn but receives (value, coordinator_data)
    # Use when the SET command needs current state of other entities (e.g. Glacier temps)
    cmd_params_coord_fn: Any = None
    # proto_builder_sn: (value, device_sn) → bytes for protobuf binary commands (PowerStream)
    proto_builder_sn: Any = None
    # state_scale: multiply raw coordinator value by this factor for display
    # Use when the MQTT raw value is in a different unit than the slider (e.g. deciWatts → Watts)
    state_scale:    float = 1.0
    # v0.2.23: read_only=True means the entity is a sensor-like number —
    # state is shown but no SET command is sent (operateType unknown)
    read_only:      bool  = False
    # dp3_cmd_key: if set, use Delta Pro 3 command envelope format
    dp3_cmd_key:    str   = ""
    # dpu_cmd_code: if set, use Delta Pro Ultra cmdCode format
    dpu_cmd_code:     str = ""
    dpu_cmd_param_key: str = ""   # param key in the cmdCode params dict


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

# ══════════════════════════════════════════════════════════════════════════════
# Gen 1 numbers — TCP command protocol (moduleType=0, operateType="TCP")
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro as dp
from .devices import river1 as r1

# Delta Pro: 6 numbers
_DPRO_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(key="max_charge_level", name="Max Charge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=dp.KEY_EMS_MAX_CHG_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 49, "maxChgSoc": int(v)}),
    EcoFlowNumberDescription(key="min_discharge_level", name="Min Discharge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
        state_key=dp.KEY_EMS_MIN_DSG_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 51, "minDsgSoc": int(v)}),
    EcoFlowNumberDescription(key="backup_reserve_soc", name="Backup Reserve SOC", native_unit_of_measurement=PERCENTAGE,
        native_min_value=5, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-charging-medium",
        state_key=dp.KEY_BP_POWER_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"isConfig": 1, "bpPowerSoc": int(v), "minDsgSoc": 0, "maxChgSoc": 0, "id": 94}),
    EcoFlowNumberDescription(key="generator_start_soc", name="Generator Start SOC", native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5, mode=NumberMode.SLIDER, icon="mdi:engine-outline",
        state_key=dp.KEY_GEN_START, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"openOilSoc": int(v), "id": 52}),
    EcoFlowNumberDescription(key="generator_stop_soc", name="Generator Stop SOC", native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:engine-off-outline",
        state_key=dp.KEY_GEN_STOP, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"closeOilSoc": int(v), "id": 53}),
    EcoFlowNumberDescription(key="ac_charging_speed", name="AC Charging Speed", native_unit_of_measurement="W",
        native_min_value=200, native_max_value=2900, native_step=100, mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dp.KEY_AC_CHG_W, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"slowChgPower": int(v), "id": 69}),
)

# Delta Max: 5 numbers (same as Pro minus backup reserve)
_DMAX_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(key="max_charge_level", name="Max Charge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=dp.KEY_EMS_MAX_CHG_SOC, cmd_module=2, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 49, "maxChgSoc": int(v)}),
    EcoFlowNumberDescription(key="min_discharge_level", name="Min Discharge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
        state_key=dp.KEY_EMS_MIN_DSG_SOC, cmd_module=2, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 51, "minDsgSoc": int(v)}),
    EcoFlowNumberDescription(key="generator_start_soc", name="Generator Start SOC", native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5, mode=NumberMode.SLIDER, icon="mdi:engine-outline",
        state_key=dp.KEY_GEN_START, cmd_module=2, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 52, "openOilSoc": int(v)}),
    EcoFlowNumberDescription(key="generator_stop_soc", name="Generator Stop SOC", native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:engine-off-outline",
        state_key=dp.KEY_GEN_STOP, cmd_module=2, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 53, "closeOilSoc": int(v)}),
    EcoFlowNumberDescription(key="ac_charging_speed", name="AC Charging Speed", native_unit_of_measurement="W",
        native_min_value=100, native_max_value=2000, native_step=100, mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dp.KEY_AC_CHG_W, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"slowChgPower": int(v), "id": 69}),
)

# Delta Mini: 3 numbers (max charge, min discharge, AC charging 900W)
_DMINI_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(key="max_charge_level", name="Max Charge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=50, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=dp.KEY_EMS_MAX_CHG_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 49, "maxChgSoc": int(v)}),
    EcoFlowNumberDescription(key="min_discharge_level", name="Min Discharge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=0, native_max_value=30, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
        state_key=dp.KEY_EMS_MIN_DSG_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 51, "minDsgSoc": int(v)}),
    EcoFlowNumberDescription(key="ac_charging_speed", name="AC Charging Speed", native_unit_of_measurement="W",
        native_min_value=200, native_max_value=900, native_step=100, mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dp.KEY_AC_CHG_W, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"slowChgPower": int(v), "id": 69}),
)

# River Max: 1 number (max charge level only, read-only in tolwi)
_RMAX_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(key="max_charge_level", name="Max Charge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=30, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key="bmsMaster.maxChargeSoc", cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 49, "maxChgSoc": int(v)}),
)

# River Pro: 1 number (max charge level)
_RPRO_NUMBERS: tuple[EcoFlowNumberDescription, ...] = _RMAX_NUMBERS  # identical

# River Mini: 1 number (max charge level via inv.maxChargeSoc)
_RMINI_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(key="max_charge_level", name="Max Charge Level", native_unit_of_measurement=PERCENTAGE,
        native_min_value=30, native_max_value=100, native_step=5, mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=r1.RMINI_MAX_CHG_SOC, cmd_module=0, cmd_operate="TCP",
        cmd_params_fn=lambda v: {"id": 0, "maxChgSoc": int(v)}),
)

# ══════════════════════════════════════════════════════════════════════════════
# Glacier — 3 numbers (Left/Right/Combined set temperature)
# JSON protocol: moduleType=1, operateType="temp"
# All three temps must be sent together; cmd_params_coord_fn reads siblings.
# ══════════════════════════════════════════════════════════════════════════════

_GL_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="left_set_temp", name="Left Set Temperature",
        native_unit_of_measurement="°C",
        native_min_value=-25, native_max_value=10, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:thermometer-chevron-down",
        state_key=gl.KEY_LEFT_SET_T, cmd_module=1, cmd_operate="temp",
        cmd_params_coord_fn=lambda v, d: {
            "tmpL": int(v),
            "tmpR": int(d.get(gl.KEY_RIGHT_SET_T, 0)),
            "tmpM": int(d.get(gl.KEY_COMBINED_SET, 0)),
        },
    ),
    EcoFlowNumberDescription(
        key="right_set_temp", name="Right Set Temperature",
        native_unit_of_measurement="°C",
        native_min_value=-25, native_max_value=10, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:thermometer-chevron-down",
        state_key=gl.KEY_RIGHT_SET_T, cmd_module=1, cmd_operate="temp",
        cmd_params_coord_fn=lambda v, d: {
            "tmpL": int(d.get(gl.KEY_LEFT_SET_T, 0)),
            "tmpR": int(v),
            "tmpM": int(d.get(gl.KEY_COMBINED_SET, 0)),
        },
    ),
    EcoFlowNumberDescription(
        key="combined_set_temp", name="Combined Set Temperature",
        native_unit_of_measurement="°C",
        native_min_value=-25, native_max_value=10, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:thermometer",
        state_key=gl.KEY_COMBINED_SET, cmd_module=1, cmd_operate="temp",
        cmd_params_coord_fn=lambda v, d: {
            "tmpL": int(d.get(gl.KEY_LEFT_SET_T, 0)),
            "tmpR": int(d.get(gl.KEY_RIGHT_SET_T, 0)),
            "tmpM": int(v),
        },
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Wave 2 — 1 number (Set Temperature)
# JSON protocol: moduleType=1, operateType="setTemp"
# ══════════════════════════════════════════════════════════════════════════════

_W2_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="set_temp", name="Set Temperature",
        native_unit_of_measurement="°C",
        native_min_value=0, native_max_value=40, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:thermometer",
        state_key=w2.KEY_SET_TEMP, cmd_module=1, cmd_operate="setTemp",
        cmd_params_fn=lambda v: {"setTemp": int(v)},
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# PowerStream — 4 numbers (Output Limit, Battery Lower/Upper, Brightness)
# Protobuf binary protocol: cmd_func=20, cmd_id per command
# Output limit is in Watts (builder converts to deciWatts internally)
# ══════════════════════════════════════════════════════════════════════════════

_PS_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="output_limit", name="Output Limit",
        native_unit_of_measurement="W",
        native_min_value=0, native_max_value=800, native_step=10,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=ps.KEY_OTHER_LOADS,
        state_scale=0.1,  # raw value is deciWatts, display in Watts
        proto_builder_sn=lambda v, sn: ps_build_permanent_watts(int(v), sn),
    ),
    EcoFlowNumberDescription(
        key="battery_lower_limit", name="Battery Lower Limit",
        native_unit_of_measurement="%",
        native_min_value=0, native_max_value=30, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-arrow-down",
        state_key=ps.KEY_LOWER_LIMIT,
        proto_builder_sn=lambda v, sn: ps_build_bat_lower(int(v), sn),
    ),
    EcoFlowNumberDescription(
        key="battery_upper_limit", name="Battery Upper Limit",
        native_unit_of_measurement="%",
        native_min_value=50, native_max_value=100, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-arrow-up",
        state_key=ps.KEY_UPPER_LIMIT,
        proto_builder_sn=lambda v, sn: ps_build_bat_upper(int(v), sn),
    ),
    EcoFlowNumberDescription(
        key="led_brightness", name="LED Brightness",
        native_min_value=0, native_max_value=1023, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:brightness-6",
        state_key=ps.KEY_BRIGHTNESS,
        proto_builder_sn=lambda v, sn: ps_build_brightness(int(v), sn),
    ),
)

# ── Description registry — keyed by device model ─────────────────────────────
NUMBER_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowNumberDescription, ...]] = {
    "Delta 3 1500": _D361_NUMBERS,
    "Delta 3 Plus": _D361_NUMBERS,
    "Delta 3 Max": _D361_NUMBERS,
    "Delta 2": _D2_NUMBERS,
    "Delta 2 Max": _D2M_NUMBERS,
    "Delta Pro": _DPRO_NUMBERS,
    "Delta Max": _DMAX_NUMBERS,
    "Delta Mini": _DMINI_NUMBERS,
    "River 2": _R2_NUMBERS,
    "River 2 Max": _R2MAX_NUMBERS,
    "River 2 Pro": _R2PRO_NUMBERS,
    "River Max": _RMAX_NUMBERS,
    "River Pro": _RPRO_NUMBERS,
    "River Mini": _RMINI_NUMBERS,
    "PowerStream": _PS_NUMBERS,
    "PowerStream 600W": _PS_NUMBERS,
    "PowerStream 800W": _PS_NUMBERS,
    "Glacier": _GL_NUMBERS,
    "Wave 2": _W2_NUMBERS,
}

# ══════════════════════════════════════════════════════════════════════════════
# Smart Plug — 2 numbers (LED Brightness, Max Power)
# Protobuf binary protocol: cmdFunc=2, cmdId per command
# NOTE: sensor telemetry requires protobuf decoder (not yet implemented)
# ══════════════════════════════════════════════════════════════════════════════

_SP_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="led_brightness", name="LED Brightness",
        native_min_value=0, native_max_value=1023, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:brightness-6",
        state_key=sp.KEY_BRIGHTNESS,
        proto_builder_sn=lambda v, sn: sp_build_brightness_fn(int(v), sn),
    ),
    EcoFlowNumberDescription(
        key="max_power", name="Max Power",
        native_unit_of_measurement="W",
        native_min_value=0, native_max_value=2500, native_step=10,
        mode=NumberMode.SLIDER, icon="mdi:flash-alert",
        state_key=sp.KEY_MAX_WATTS,
        proto_builder_sn=lambda v, sn: sp_build_max_watts(int(v), sn),
    ),
)

# ── Merged registry ──────────────────────────────────────────────────────────
NUMBER_DESCRIPTIONS_BY_MODEL["Smart Plug"] = _SP_NUMBERS

# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro 3 (DGEA) — DP3 command envelope (cmdFunc=254, flat keys)
# Source: EcoFlow Developer docs (deltaPro3)
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro_3 as dp3_num

_DP3_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="dp3_max_chg_soc", name="Max Charge SOC",
        native_unit_of_measurement="%", native_min_value=50, native_max_value=100, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-high",
        state_key=dp3_num.KEY_MAX_CHG_SOC,
        dp3_cmd_key=dp3_num.CMD_MAX_CHG_SOC,
    ),
    EcoFlowNumberDescription(
        key="dp3_min_dsg_soc", name="Min Discharge SOC",
        native_unit_of_measurement="%", native_min_value=0, native_max_value=30, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-low",
        state_key=dp3_num.KEY_MIN_DSG_SOC,
        dp3_cmd_key=dp3_num.CMD_MIN_DSG_SOC,
    ),
    EcoFlowNumberDescription(
        key="dp3_ac_standby", name="AC Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dp3_num.KEY_AC_STANDBY_TIME,
        dp3_cmd_key=dp3_num.CMD_AC_STANDBY,
    ),
    EcoFlowNumberDescription(
        key="dp3_dc_standby", name="DC Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dp3_num.KEY_DC_STANDBY_TIME,
        dp3_cmd_key=dp3_num.CMD_DC_STANDBY,
    ),
    EcoFlowNumberDescription(
        key="dp3_dev_standby", name="Device Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dp3_num.KEY_DEV_STANDBY_TIME,
        dp3_cmd_key=dp3_num.CMD_DEV_STANDBY,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_screen_off", name="Screen Off Time",
        native_unit_of_measurement="s", native_min_value=0, native_max_value=300, native_step=10,
        mode=NumberMode.SLIDER, icon="mdi:monitor-off",
        state_key=dp3_num.KEY_SCREEN_OFF_TIME,
        dp3_cmd_key=dp3_num.CMD_SCREEN_OFF,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_lcd_brightness", name="LCD Brightness",
        native_min_value=0, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:brightness-6",
        state_key=dp3_num.KEY_LCD_LIGHT,
        dp3_cmd_key=dp3_num.CMD_LCD_LIGHT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_ac_chg_power", name="AC Charging Power",
        native_unit_of_measurement="W", native_min_value=200, native_max_value=3000, native_step=100,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dp3_num.KEY_AC_CHG_POW_MAX,
        dp3_cmd_key=dp3_num.CMD_AC_CHG_POW,
    ),
    EcoFlowNumberDescription(
        key="dp3_pv_lv_amp", name="Solar LV Max Current",
        native_unit_of_measurement="A", native_min_value=2, native_max_value=13, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:solar-power",
        state_key=dp3_num.KEY_PV_LV_DC_AMP_MAX,
        dp3_cmd_key=dp3_num.CMD_PV_LV_AMP,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_pv_hv_amp", name="Solar HV Max Current",
        native_unit_of_measurement="A", native_min_value=2, native_max_value=13, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:solar-power-variant",
        state_key=dp3_num.KEY_PV_HV_DC_AMP_MAX,
        dp3_cmd_key=dp3_num.CMD_PV_HV_AMP,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_oil_on_soc", name="Generator Start SOC",
        native_unit_of_measurement="%", native_min_value=0, native_max_value=50, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:gas-station",
        state_key=dp3_num.KEY_OIL_ON_SOC,
        dp3_cmd_key=dp3_num.CMD_OIL_ON_SOC,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_oil_off_soc", name="Generator Stop SOC",
        native_unit_of_measurement="%", native_min_value=50, native_max_value=100, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:gas-station-off",
        state_key=dp3_num.KEY_OIL_OFF_SOC,
        dp3_cmd_key=dp3_num.CMD_OIL_OFF_SOC,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dp3_ble_standby", name="Bluetooth Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:bluetooth",
        state_key=dp3_num.KEY_BLE_STANDBY_TIME,
        dp3_cmd_key=dp3_num.CMD_BLE_STANDBY,
        entity_registry_enabled_default=False,
    ),
)

NUMBER_DESCRIPTIONS_BY_MODEL["Delta Pro 3"] = _DP3_NUMBERS

# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro Ultra (DGEB) — cmdCode protocol (YJ751_PD_*)
# Source: EcoFlow Developer docs (deltaProUltra), 14 April 2026, 18 pages
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro_ultra as dpu_num

_DPU_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="dpu_max_chg_soc", name="Max Charge SOC",
        native_unit_of_measurement="%", native_min_value=50, native_max_value=100, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-high",
        state_key=dpu_num.KEY_CHG_MAX_SOC,
        dpu_cmd_code=dpu_num.CMD_CHG_SOC_MAX,
        dpu_cmd_param_key=dpu_num.PARAM_MAX_CHG_SOC,
    ),
    EcoFlowNumberDescription(
        key="dpu_min_dsg_soc", name="Min Discharge SOC",
        native_unit_of_measurement="%", native_min_value=0, native_max_value=30, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-low",
        state_key=dpu_num.KEY_DSG_MIN_SOC,
        dpu_cmd_code=dpu_num.CMD_DSG_SOC_MIN,
        dpu_cmd_param_key=dpu_num.PARAM_MIN_DSG_SOC,
    ),
    EcoFlowNumberDescription(
        key="dpu_power_standby", name="Device Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dpu_num.KEY_POWER_STANDBY,
        dpu_cmd_code=dpu_num.CMD_POWER_STANDBY,
        dpu_cmd_param_key=dpu_num.PARAM_POWER_STANDBY,
    ),
    EcoFlowNumberDescription(
        key="dpu_screen_standby", name="Screen Standby Time",
        native_unit_of_measurement="s", native_min_value=0, native_max_value=600, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:monitor-off",
        state_key=dpu_num.KEY_SCREEN_STANDBY,
        dpu_cmd_code=dpu_num.CMD_SCREEN_STANDBY,
        dpu_cmd_param_key=dpu_num.PARAM_SCREEN_STANDBY,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dpu_ac_standby", name="AC Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dpu_num.KEY_AC_STANDBY,
        dpu_cmd_code=dpu_num.CMD_AC_STANDBY,
        dpu_cmd_param_key=dpu_num.PARAM_AC_STANDBY,
    ),
    EcoFlowNumberDescription(
        key="dpu_dc_standby", name="DC Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=720, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=dpu_num.KEY_DC_STANDBY,
        dpu_cmd_code=dpu_num.CMD_DC_STANDBY,
        dpu_cmd_param_key=dpu_num.PARAM_DC_STANDBY,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dpu_chg_c20_watts", name="AC Charging Power",
        native_unit_of_measurement="W", native_min_value=200, native_max_value=3000, native_step=100,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dpu_num.KEY_CHG_C20_SET,
        dpu_cmd_code=dpu_num.CMD_AC_CHG,
        dpu_cmd_param_key=dpu_num.PARAM_CHG_C20_WATTS,
    ),
    EcoFlowNumberDescription(
        key="dpu_chg_5p8_watts", name="POWER IN/OUT Charging Power",
        native_unit_of_measurement="W", native_min_value=200, native_max_value=3900, native_step=100,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=dpu_num.KEY_CHG_5P8_SET,
        dpu_cmd_code=dpu_num.CMD_AC_CHG,
        dpu_cmd_param_key=dpu_num.PARAM_CHG_5P8_WATTS,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dpu_ac_often_min_soc", name="AC Always-On Min SOC",
        native_unit_of_measurement="%", native_min_value=0, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:battery-lock",
        state_key=dpu_num.KEY_AC_OFTEN_MIN_SOC,
        dpu_cmd_code=dpu_num.CMD_AC_OFTEN_OPEN,
        dpu_cmd_param_key="acOftenOpenMinSoc",
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="dpu_backup_soc", name="Backup Reserve SOC",
        native_unit_of_measurement="%", native_min_value=5, native_max_value=100, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:battery-heart",
        state_key=dpu_num.KEY_SYS_BACKUP_SOC,
        # No dedicated SET cmdCode in docs — read-only for now
        read_only=True,
        entity_registry_enabled_default=False,
    ),
)

NUMBER_DESCRIPTIONS_BY_MODEL["Delta Pro Ultra"] = _DPU_NUMBERS

# ══════════════════════════════════════════════════════════════════════════════
# River 3 / River 3 Plus (R641/R651) — Gen 3 protocol (cmdFunc=254)
# Source: foxthefox/ioBroker.ecoflow-mqtt river3plus.md level commands
# ══════════════════════════════════════════════════════════════════════════════

from .devices import river3 as r3_num

_R3_NUMBERS: tuple[EcoFlowNumberDescription, ...] = (
    EcoFlowNumberDescription(
        key="r3_max_chg_soc", name="Max Charge SOC",
        native_unit_of_measurement="%", native_min_value=50, native_max_value=100, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-high",
        state_key=r3_num.KEY_MAX_CHG_SOC,
        dp3_cmd_key=r3_num.CMD_MAX_CHG_SOC,
    ),
    EcoFlowNumberDescription(
        key="r3_min_dsg_soc", name="Min Discharge SOC",
        native_unit_of_measurement="%", native_min_value=0, native_max_value=30, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:battery-charging-low",
        state_key=r3_num.KEY_MIN_DSG_SOC,
        dp3_cmd_key=r3_num.CMD_MIN_DSG_SOC,
    ),
    EcoFlowNumberDescription(
        key="r3_dev_standby", name="Device Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=1440, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=r3_num.KEY_DEV_STANDBY_TIME,
        dp3_cmd_key=r3_num.CMD_DEV_STANDBY,
    ),
    EcoFlowNumberDescription(
        key="r3_screen_off", name="Screen Off Time",
        native_unit_of_measurement="s", native_min_value=0, native_max_value=1800, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:monitor-off",
        state_key=r3_num.KEY_SCREEN_OFF_TIME,
        dp3_cmd_key=r3_num.CMD_SCREEN_OFF,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="r3_ac_standby", name="AC Standby Time",
        native_unit_of_measurement="min", native_min_value=0, native_max_value=1440, native_step=30,
        mode=NumberMode.SLIDER, icon="mdi:timer-outline",
        state_key=r3_num.KEY_AC_STANDBY_TIME,
        dp3_cmd_key=r3_num.CMD_AC_STANDBY,
        entity_registry_enabled_default=False,
    ),
    EcoFlowNumberDescription(
        key="r3_ac_chg_power", name="AC Charging Power",
        native_unit_of_measurement="W", native_min_value=50, native_max_value=305, native_step=5,
        mode=NumberMode.SLIDER, icon="mdi:transmission-tower-import",
        state_key=r3_num.KEY_AC_CHG_POW_SET,
        dp3_cmd_key=r3_num.CMD_AC_CHG_POW,
    ),
    EcoFlowNumberDescription(
        key="r3_pv_dc_amp", name="Solar Max Charge Current",
        native_unit_of_measurement="A", native_min_value=4, native_max_value=8, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:solar-power",
        state_key=r3_num.KEY_PV_DC_AMP_MAX,
        dp3_cmd_key=r3_num.CMD_PV_DC_AMP,
        entity_registry_enabled_default=False,
    ),
)

NUMBER_DESCRIPTIONS_BY_MODEL["River 3"] = _R3_NUMBERS
NUMBER_DESCRIPTIONS_BY_MODEL["River 3 Plus"] = _R3_NUMBERS


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
            raw = float(val) if val is not None else None
            if raw is not None and self.entity_description.state_scale != 1.0:
                raw = raw * self.entity_description.state_scale
            return raw
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

        if desc.cmd_params_coord_fn is not None:
            params = desc.cmd_params_coord_fn(value, self.coordinator.data or {})
        elif desc.cmd_params_fn is not None:
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

        # Priority 2: Protobuf binary MQTT SET (PowerStream)
        if desc.proto_builder_sn is not None:
            client = self._entry_data.get("mqtt_client")
            topic  = self._entry_data.get("mqtt_topic_set")
            if not client or not topic:
                _LOGGER.error("EcoFlow: no MQTT client — cannot send %s proto command", desc.key)
                return
            payload = desc.proto_builder_sn(value, self._sn)
            _LOGGER.info(
                "EcoFlow: PROTO SET number %s value=%s topic=%s len=%d",
                desc.key, value, topic, len(payload),
            )
            result = client.publish(topic, payload, qos=1)
            _LOGGER.debug("EcoFlow: Proto publish mid=%s rc=%s", result.mid, result.rc)
            return

        # Priority 2.5: Delta Pro 3 JSON envelope (cmdFunc=254, flat keys)
        if desc.dp3_cmd_key:
            client = self._entry_data.get("mqtt_client")
            topic  = self._entry_data.get("mqtt_topic_set")
            if not client or not topic:
                _LOGGER.error("EcoFlow: no MQTT client — cannot send DP3 %s command", desc.key)
                return
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
                "params":   {desc.dp3_cmd_key: int(value)},
            }
            _LOGGER.info(
                "EcoFlow: DP3 SET number %s value=%s topic=%s key=%s",
                desc.key, value, topic, desc.dp3_cmd_key,
            )
            result = client.publish(topic, json.dumps(cmd), qos=1)
            _LOGGER.debug("EcoFlow: DP3 publish mid=%s rc=%s", result.mid, result.rc)
            return

        # Priority 2.6: Delta Pro Ultra cmdCode format
        if desc.dpu_cmd_code:
            dpu_params = {desc.dpu_cmd_param_key: int(value)} if desc.dpu_cmd_param_key else params

            # Priority 2.6a: REST API SET with cmdCode
            rest_api = self._entry_data.get("rest_api")
            if rest_api is not None and hasattr(rest_api, 'set_quota_cmdcode'):
                try:
                    rest_api.set_quota_cmdcode(desc.dpu_cmd_code, dpu_params)
                    _LOGGER.info(
                        "EcoFlow: DPU REST SET number %s value=%s cmdCode=%s params=%s",
                        desc.key, value, desc.dpu_cmd_code, dpu_params,
                    )
                    return
                except Exception as exc:
                    _LOGGER.debug(
                        "EcoFlow: DPU REST SET number %s failed (%s) — falling back to MQTT",
                        desc.key, exc,
                    )

            # Priority 2.6b: MQTT SET with cmdCode
            client = self._entry_data.get("mqtt_client")
            topic  = self._entry_data.get("mqtt_topic_set")
            if not client or not topic:
                _LOGGER.error("EcoFlow: no MQTT client — cannot send DPU %s command", desc.key)
                return
            cmd = {
                "id":       _next_id(),
                "version":  "1.0",
                "cmdCode":  desc.dpu_cmd_code,
                "params":   dpu_params,
            }
            _LOGGER.info(
                "EcoFlow: DPU SET number %s value=%s topic=%s cmdCode=%s",
                desc.key, value, topic, desc.dpu_cmd_code,
            )
            result = client.publish(topic, json.dumps(cmd), qos=1)
            _LOGGER.debug("EcoFlow: DPU publish mid=%s rc=%s", result.mid, result.rc)
            return

        # Priority 3: JSON MQTT SET
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
