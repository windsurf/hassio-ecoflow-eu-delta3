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
    ps_build_feed_protect,
    sp_build_switch,
)
from .devices import glacier as gl
from .devices import powerstream as ps
from .devices import smart_plug as sp

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
    # proto_builder_sn: like proto_builder but receives (value, device_sn) → bytes
    # Used by PowerStream which needs device_sn in the protobuf envelope
    proto_builder_sn: Optional[Callable] = None
    # optimistic: update coordinator.data immediately after SET command
    # Use when the device does not push state feedback via telemetry
    optimistic:   bool                       = False
    entity_registry_enabled_default: bool = True



_D361_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
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
        # openUpsFlag: firmware-controlled AC pass-through. Command accepted (ack=1)
        # but flag is managed by firmware based on battery state + AC input.
        # Not a user-toggleable switch in the EcoFlow app. Kept as diagnostic.
        entity_registry_enabled_default=False,
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
        # pd.acAutoOutPause is always 0 in D361 telemetry — state feedback unavailable.
        # Command (bypassBan) works: relay switches as confirmed by relaySwitchCnt.
        # Optimistic: update state immediately after SET command.
        optimistic=True,
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
        # beepState=1 means quiet mode ON (sound OFF) — inverted so switch shows ON when sound is ON
        cmd_params=lambda on: {"enabled": 0 if on else 1},
        inverted=True,
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


# ══════════════════════════════════════════════════════════════════════════════
# Delta 2 — 8 switches
# Source: tolwi/hassio-ecoflow-cloud (internal/delta2.py)
# All commands identical to Delta 3 1500 subset
# ══════════════════════════════════════════════════════════════════════════════

_D2_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(
        key="beep_sound",
        name="Beep Sound",
        icon="mdi:volume-high",
        state_key=KEY_BEEP_MODE,
        cmd_module=MODULE_MPPT,
        cmd_operate="quietMode",
        cmd_params=lambda on: {"enabled": 0 if on else 1},
    ),
    EcoFlowSwitchDescription(
        key="usb_output",
        name="USB Output",
        icon="mdi:usb-port",
        state_key=KEY_USB_OUT_STATE,
        cmd_module=MODULE_PD,
        cmd_operate="dcOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
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
        key="solar_charge_priority",
        name="Solar Charge Priority",
        icon="mdi:solar-power",
        state_key=KEY_PV_CHG_PRIO,
        cmd_module=MODULE_PD,
        cmd_operate="pvChangePrio",
        cmd_params=lambda on: {"pvChangeSet": 1 if on else 0},
    ),
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
    ),
    EcoFlowSwitchDescription(
        key="dc_output",
        name="DC Output",
        icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE,
        cmd_module=MODULE_MPPT,
        cmd_operate="mpptCar",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="backup_reserve",
        name="Backup Reserve",
        icon="mdi:battery-charging-medium",
        state_key=KEY_BP_IS_CONFIG,
        cmd_module=MODULE_PD,
        cmd_operate="watthConfig",
        cmd_params=lambda on: {
            "isConfig":   1 if on else 0,
            "bpPowerSoc": 50 if on else 0,
            "minDsgSoc":  0,
            "minChgSoc":  0,
        },
    ),
)

from .devices.delta2_max import (
    KEY_BEEP_D2M, KEY_AC_ENABLED_D2M, KEY_AC_XBOOST_D2M,
    KEY_AC_ALWAYS_ON_D2M,
)

# ══════════════════════════════════════════════════════════════════════════════
# Delta 2 Max — 7 switches
# Source: tolwi/hassio-ecoflow-cloud (internal/delta2_max.py)
# Key differences: beep on pd.beepMode, AC via inv module (3), newAcAutoOnCfg
# ══════════════════════════════════════════════════════════════════════════════

_D2M_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(
        key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=KEY_BEEP_D2M,
        cmd_module=MODULE_PD, cmd_operate="quietCfg",
        cmd_params=lambda on: {"enabled": 0 if on else 1},
    ),
    EcoFlowSwitchDescription(
        key="usb_output", name="USB Output", icon="mdi:usb-port",
        state_key=KEY_USB_OUT_STATE,
        cmd_module=MODULE_PD, cmd_operate="dcOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="ac_always_on", name="AC Always-On", icon="mdi:power-plug",
        state_key=KEY_AC_ALWAYS_ON_D2M,
        cmd_module=MODULE_PD, cmd_operate="newAcAutoOnCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "minAcSoc": 5},
    ),
    EcoFlowSwitchDescription(
        key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=KEY_AC_ENABLED_D2M,
        cmd_module=MODULE_INV, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "out_voltage": -1, "out_freq": 255, "xboost": 255},
    ),
    EcoFlowSwitchDescription(
        key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=KEY_AC_XBOOST_D2M,
        cmd_module=MODULE_INV, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"xboost": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE,
        cmd_module=MODULE_MPPT, cmd_operate="mpptCar",
        cmd_params=lambda on: {"enabled": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="backup_reserve", name="Backup Reserve", icon="mdi:battery-charging-medium",
        state_key=KEY_BP_IS_CONFIG,
        cmd_module=MODULE_PD, cmd_operate="watthConfig",
        cmd_params=lambda on: {"isConfig": 1 if on else 0, "bpPowerSoc": 50 if on else 0, "minDsgSoc": 0, "minChgSoc": 0},
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# River 2 series — 5 switches (R2/R2Max), 3 switches (R2Pro)
# ══════════════════════════════════════════════════════════════════════════════

from .devices.river2 import KEY_AC_ENABLED as R2_AC_ENABLED

_R2_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=R2_AC_ENABLED, cmd_module=MODULE_MPPT, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "out_voltage": -1, "out_freq": 255, "xboost": 255}),
    EcoFlowSwitchDescription(key="ac_always_on", name="AC Always-On", icon="mdi:power-plug",
        state_key=KEY_AC_AUTO_OUT, cmd_module=MODULE_PD, cmd_operate="acAutoOutConfig",
        cmd_params=lambda on: {"acAutoOutConfig": 1 if on else 0, "minAcOutSoc": 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=KEY_AC_XBOOST, cmd_module=MODULE_MPPT, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"enabled": 255, "out_voltage": -1, "out_freq": 255, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE, cmd_module=MODULE_MPPT, cmd_operate="mpptCar",
        cmd_params=lambda on: {"enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="backup_reserve", name="Backup Reserve", icon="mdi:battery-charging-medium",
        state_key=KEY_BP_IS_CONFIG, cmd_module=MODULE_PD, cmd_operate="watthConfig",
        cmd_params=lambda on: {"isConfig": 1 if on else 0, "bpPowerSoc": 50 if on else 0, "minDsgSoc": 0, "minChgSoc": 0}),
)

# River 2 Pro: no AC Always-On, no Backup Reserve
_R2PRO_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=R2_AC_ENABLED, cmd_module=MODULE_MPPT, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "out_voltage": -1, "out_freq": 255, "xboost": 255}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=KEY_AC_XBOOST, cmd_module=MODULE_MPPT, cmd_operate="acOutCfg",
        cmd_params=lambda on: {"enabled": 255, "out_voltage": -1, "out_freq": 255, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=KEY_DC_OUT_STATE, cmd_module=MODULE_MPPT, cmd_operate="mpptCar",
        cmd_params=lambda on: {"enabled": 1 if on else 0}),
)

# ══════════════════════════════════════════════════════════════════════════════
# Gen 1 devices — TCP command protocol (moduleType=0, operateType="TCP", params.id)
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro as dp
from .devices import river1 as r1

# Delta Pro: 6 switches (Beeper, DC, AC, X-Boost, AC Always-On, Backup Reserve)
_DPRO_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=dp.KEY_BEEP, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 38, "enabled": 0 if on else 1}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=dp.KEY_DC_OUT_STATE, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 81, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_always_on", name="AC Always-On", icon="mdi:power-plug",
        state_key=dp.KEY_AC_AUTO_OUT, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 95, "acautooutConfig": 1 if on else 0}),
    EcoFlowSwitchDescription(key="backup_reserve", name="Backup Reserve", icon="mdi:battery-charging-medium",
        state_key=dp.KEY_BP_IS_CONFIG, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 94, "isConfig": 1 if on else 0, "bpPowerSoc": 50 if on else 0, "minDsgSoc": 0, "maxChgSoc": 0}),
)

# Delta Max: 7 switches (same + USB + PV Priority)
_DMAX_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=dp.KEY_BEEP, cmd_module=5, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 38, "enabled": 0 if on else 1}),
    EcoFlowSwitchDescription(key="usb_output", name="USB Output", icon="mdi:usb-port",
        state_key="pd.dcOutState", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "id": 34}),
    EcoFlowSwitchDescription(key="ac_always_on", name="AC Always-On", icon="mdi:power-plug",
        state_key="pd.acAutoOnCfg", cmd_module=1, cmd_operate="acAutoOn",
        cmd_params=lambda on: {"cfg": 1 if on else 0}),
    EcoFlowSwitchDescription(key="solar_charge_priority", name="Solar Charge Priority", icon="mdi:solar-power",
        state_key="pd.pvChgPrioSet", cmd_module=1, cmd_operate="pvChangePrio",
        cmd_params=lambda on: {"pvChangeSet": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "id": 66}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=5, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=dp.KEY_DC_OUT_STATE, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"enabled": 1 if on else 0, "id": 81}),
)

# Delta Mini: 4 switches (Beeper, DC, AC, X-Boost)
_DMINI_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=dp.KEY_BEEP, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 38, "enabled": 0 if on else 1}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key=dp.KEY_DC_OUT_STATE, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 81, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
)

# River Max: 5 switches (Beeper, AC, DC, X-Boost, Auto Fan)
_RMAX_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=dp.KEY_BEEP, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 38, "enabled": 0 if on else 1}),
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key="pd.carSwitch", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 34, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="auto_fan_speed", name="Auto Fan Speed", icon="mdi:fan-auto",
        state_key="inv.cfgFanMode", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 73, "fanMode": 1 if on else 0}),
)

# River Pro: 7 switches (Beeper, AC Always-On, DC, AC, X-Boost, AC Slow Charge, Auto Fan)
_RPRO_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=dp.KEY_BEEP, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 38, "enabled": 0 if on else 1}),
    EcoFlowSwitchDescription(key="ac_always_on", name="AC Always-On", icon="mdi:power-plug",
        state_key="inv.acAutoOutConfig", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 95, "acAutoOutConfig": 1 if on else 0}),
    EcoFlowSwitchDescription(key="dc_output", name="DC Output", icon="mdi:car-electric",
        state_key="pd.carSwitch", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 34, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
    EcoFlowSwitchDescription(key="ac_slow_charge", name="AC Slow Charging", icon="mdi:ev-plug-type2",
        state_key="inv.cfgAcChgModeFlg", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 69, "workMode": 1 if on else 0}),
    EcoFlowSwitchDescription(key="auto_fan_speed", name="Auto Fan Speed", icon="mdi:fan-auto",
        state_key="inv.cfgFanMode", cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 73, "fanMode": 1 if on else 0}),
)

# River Mini: 2 switches (AC, X-Boost)
_RMINI_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(key="ac_output", name="AC Output", icon="mdi:power-socket-eu",
        state_key=dp.KEY_AC_ENABLED, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "enabled": 1 if on else 0}),
    EcoFlowSwitchDescription(key="x_boost", name="X-Boost", icon="mdi:lightning-bolt",
        state_key=dp.KEY_AC_XBOOST, cmd_module=0, cmd_operate="TCP",
        cmd_params=lambda on: {"id": 66, "xboost": 1 if on else 0}),
)

# ══════════════════════════════════════════════════════════════════════════════
# Glacier — 3 switches (Beeper, Eco Mode, Power)
# JSON protocol: moduleType=1, operateType per command
# ══════════════════════════════════════════════════════════════════════════════

_GL_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(
        key="beep_sound", name="Beep Sound", icon="mdi:volume-high",
        state_key=gl.KEY_BEEP_EN, cmd_module=1, cmd_operate="beepEn",
        cmd_params=lambda on: {"flag": 0 if on else 1},
        inverted=True,
    ),
    EcoFlowSwitchDescription(
        key="eco_mode", name="Eco Mode", icon="mdi:leaf",
        state_key=gl.KEY_COOL_MODE, cmd_module=1, cmd_operate="ecoMode",
        cmd_params=lambda on: {"mode": 1 if on else 0},
    ),
    EcoFlowSwitchDescription(
        key="power", name="Power", icon="mdi:power",
        state_key=gl.KEY_PWR_STATE, cmd_module=1, cmd_operate="powerOff",
        cmd_params=lambda on: {"enable": 1 if on else 0},
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# PowerStream — 1 switch (Feed-in Control)
# Protobuf binary protocol: cmd_func=20, cmd_id per command
# ══════════════════════════════════════════════════════════════════════════════

_PS_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(
        key="feed_in_control", name="Feed-in Control", icon="mdi:transmission-tower-export",
        state_key=ps.KEY_SMART_LOADS,
        proto_builder_sn=lambda on, sn: ps_build_feed_protect(on, sn),
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Smart Plug — 1 switch (Power on/off)
# Protobuf binary protocol: cmdFunc=2, cmdId=129
# NOTE: sensor telemetry requires protobuf decoder (not yet implemented)
# ══════════════════════════════════════════════════════════════════════════════

_SP_SWITCHES: tuple[EcoFlowSwitchDescription, ...] = (
    EcoFlowSwitchDescription(
        key="power", name="Power", icon="mdi:power-plug",
        state_key=sp.KEY_SWITCH_STA,
        proto_builder_sn=lambda on, sn: sp_build_switch(on, sn),
    ),
)

# ── Description registry — keyed by device model ─────────────────────────────
SWITCH_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowSwitchDescription, ...]] = {
    "Delta 3 1500": _D361_SWITCHES,
    "Delta 2": _D2_SWITCHES,
    "Delta 2 Max": _D2M_SWITCHES,
    "Delta Pro": _DPRO_SWITCHES,
    "Delta Max": _DMAX_SWITCHES,
    "Delta Mini": _DMINI_SWITCHES,
    "River 2": _R2_SWITCHES,
    "River 2 Max": _R2_SWITCHES,
    "River 2 Pro": _R2PRO_SWITCHES,
    "River Max": _RMAX_SWITCHES,
    "River Pro": _RPRO_SWITCHES,
    "River Mini": _RMINI_SWITCHES,
    "PowerStream": _PS_SWITCHES,
    "PowerStream 600W": _PS_SWITCHES,
    "PowerStream 800W": _PS_SWITCHES,
    "Glacier": _GL_SWITCHES,
    "Wave 2": (),  # no switches (tolwi confirms empty)
    "Smart Plug": _SP_SWITCHES,
}


def _get_switch_descriptions(model: str) -> tuple[EcoFlowSwitchDescription, ...]:
    """Get switch descriptions for a device model. Falls back to empty tuple."""
    return SWITCH_DESCRIPTIONS_BY_MODEL.get(model, ())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switches from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]
    device_model = entry_data.get("device_model", "Delta 3 1500")

    descriptions = _get_switch_descriptions(device_model)

    async_add_entities(
        EcoFlowSwitchEntity(coordinator, desc, entry_data, sn, device_model)
        for desc in descriptions
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

        # Priority 2: Protobuf binary MQTT SET (PowerStream)
        if desc.proto_builder_sn is not None:
            client = self._entry_data.get("mqtt_client")
            topic  = self._entry_data.get("mqtt_topic_set")
            if not client or not topic:
                _LOGGER.error("EcoFlow: no MQTT client — cannot send %s proto command", desc.key)
                return
            payload = desc.proto_builder_sn(turn_on, self._sn)
            _LOGGER.info(
                "EcoFlow: PROTO SET %s turn_on=%s topic=%s len=%d",
                desc.key, turn_on, topic, len(payload),
            )
            result = client.publish(topic, payload, qos=1)
            _LOGGER.debug("EcoFlow: Proto publish mid=%s rc=%s", result.mid, result.rc)
            return

        # Priority 3: JSON MQTT SET
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
        if self.entity_description.optimistic:
            raw = 0 if self.entity_description.inverted else 1
            self.coordinator.data[self.entity_description.state_key] = raw
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._publish, False)
        if self.entity_description.optimistic:
            raw = 1 if self.entity_description.inverted else 0
            self.coordinator.data[self.entity_description.state_key] = raw
            self.async_write_ha_state()
