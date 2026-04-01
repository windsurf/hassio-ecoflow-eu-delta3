"""Sensor platform for EcoFlow Cloud."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoflowCoordinator
from .devices.delta3_1500 import (
    DEVICE_MODEL,
    # Battery
    KEY_SOC, KEY_SOH, KEY_CYCLES,
    KEY_BATT_VOLT, KEY_BATT_CURR, KEY_BATT_TEMP,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_MIN_MOS_TEMP, KEY_MAX_MOS_TEMP,
    # EMS
    KEY_REMAIN_TIME, KEY_CHARGE_TIME,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_EMS_CHG_VOL, KEY_EMS_CHG_AMP, KEY_EMS_FAN_LEVEL,
    KEY_EMS_CHG_LINE,
    # Kit
    KEY_KIT_WATTS, KEY_KIT_NUM,
    # BmsInfo lifetime
    KEY_INFO_SOH, KEY_INFO_CYCLES,
    KEY_INFO_ACCU_CHG, KEY_INFO_ACCU_DSG,
    KEY_INFO_ACCU_CHG_E, KEY_INFO_ACCU_DSG_E,
    KEY_INFO_ROUND_TRIP, KEY_INFO_SELF_DSG,
    KEY_INFO_DEEP_DSG, KEY_INFO_OHM_RES,
    # AC / Inverter
    KEY_AC_OUT_W, KEY_AC_IN_W,
    KEY_AC_IN_VOLT, KEY_AC_IN_AMP, KEY_AC_IN_FREQ,
    KEY_AC_OUT_VOLT, KEY_AC_OUT_AMP, KEY_AC_OUT_FREQ_RT,
    KEY_AC_FAST_CHG_W, KEY_AC_SLOW_CHG_W,
    KEY_AC_TEMP, KEY_AC_FAN_STATE,
    KEY_DC_IN_VOLT, KEY_DC_IN_AMP, KEY_DC_IN_TEMP,
    # Solar / MPPT
    KEY_SOLAR_W, KEY_SOLAR_VOLT, KEY_SOLAR_AMP,
    KEY_SOLAR_OUT_W,
    KEY_MPPT_TEMP,
    KEY_DC12V_OUT_W, KEY_DC12V_OUT_VOLT, KEY_DC12V_OUT_AMP,
    KEY_DC12V_TEMP, KEY_DC12V_IN_W,
    KEY_DC_OUT_TEMP, KEY_DCDC12V_W,
    # USB
    KEY_USB1_W, KEY_USB2_W, KEY_USB_QC1_W, KEY_USB_QC2_W,
    KEY_USBC1_W, KEY_USBC2_W,
    KEY_USBC1_TEMP, KEY_USBC2_TEMP,
    # PD / System
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_CHG_POWER_AC, KEY_CHG_POWER_DC,
    KEY_DSG_POWER_AC, KEY_DSG_POWER_DC,
    KEY_CHG_SUN_POWER,
    KEY_WIFI_RSSI,
    KEY_BP_POWER_SOC,
    KEY_GEN_MIN_SOC,
    KEY_GEN_MAX_SOC,
    KEY_MPPT_BEEP,
    KEY_AC_CFG_FREQ,
    KEY_DC12V_OUT_VOLT,
    KEY_DC12V_OUT_AMP,
    KEY_SOC_FLOAT,
    KEY_MAX_VOL_DIFF,
    KEY_DC12V_STATE,
    KEY_EMS_SYS_STATE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EcoFlowSensorDescription(SensorEntityDescription):
    """Sensor description with optional scaling and rounding."""
    scale:        float       = 1.0
    round_digits: int | None  = 2
    # Optional fallback key used when the primary key is absent in coordinator data
    fallback_key: str | None  = None


SENSOR_DESCRIPTIONS: tuple[EcoFlowSensorDescription, ...] = (

    # ── Battery ──────────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_SOC,
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOC_FLOAT,
        name="Battery Level (precise)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOH,
        name="State of Health (BMS Status)",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_CYCLES,
        name="Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_REMAIN_CAP,
        name="Remaining Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-medium",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_FULL_CAP,
        name="Full Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_DESIGN_CAP,
        name="Design Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_BATT_VOLT,
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_BATT_CURR,
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_BATT_TEMP,
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_MIN_CELL_TEMP,
        name="Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MAX_CELL_TEMP,
        name="Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MIN_MOS_TEMP,
        name="Min MOS Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_MAX_MOS_TEMP,
        name="Max MOS Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_MIN_CELL_VOLT,
        name="Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MAX_CELL_VOLT,
        name="Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MAX_VOL_DIFF,
        name="Max Cell Voltage Difference",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── EMS ──────────────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_REMAIN_TIME,
        name="Time Remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        fallback_key="pd.remainTime",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_CHARGE_TIME,
        name="Time to Full",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-plus-outline",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_MAX_CHG_SOC,
        name="Max Charge Level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-arrow-up",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_MIN_DSG_SOC,
        name="Min Discharge Level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-arrow-down",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_VOL,
        name="EMS Charge Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_AMP,
        name="EMS Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_FAN_LEVEL,
        name="Fan Level",
        icon="mdi:fan",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_LINE,
        name="AC Plug Connected",
        icon="mdi:power-plug",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_SYS_STATE,
        name="System Charge/Discharge State",
        icon="mdi:battery-arrow-up-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── Extra battery kit ─────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_KIT_WATTS,
        name="Extra Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-plus",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_KIT_NUM,
        name="Extra Batteries Connected",
        icon="mdi:battery-plus-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── AC / Inverter ─────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_AC_OUT_W,
        name="AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:power-socket-eu",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_IN_W,
        name="AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_IN_VOLT,
        name="AC Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_IN_AMP,
        name="AC Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_IN_FREQ,
        name="AC Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_OUT_VOLT,
        name="AC Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_OUT_AMP,
        name="AC Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_OUT_FREQ_RT,
        name="AC Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_CFG_FREQ,
        name="AC Configured Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_FAST_CHG_W,
        name="AC Fast Charge Watts",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_SLOW_CHG_W,
        name="AC Slow Charge Watts",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_TEMP,
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC_IN_VOLT,
        name="Inverter DC Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        entity_registry_enabled_default=False,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC_IN_AMP,
        name="Inverter DC Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        entity_registry_enabled_default=False,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC_IN_TEMP,
        name="Inverter DC Input Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        round_digits=1,
    ),

    # ── Solar / MPPT ─────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_SOLAR_W,
        name="Solar Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOLAR_VOLT,
        name="Solar Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOLAR_AMP,
        name="Solar Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOLAR_OUT_W,
        name="MPPT Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power-variant",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_TEMP,
        name="MPPT Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC12V_OUT_W,
        name="DC 12V Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-electric",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC12V_IN_W,
        name="DC 12V Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-arrow-right",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC12V_TEMP,
        name="DC 12V Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC12V_STATE,
        name="DC 12V Port State",
        icon="mdi:car-electric",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_DC_OUT_TEMP,
        name="DC Output Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_DCDC12V_W,
        name="MPPT DC Converter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-battery",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── USB / PD ─────────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_IN_W_TOTAL,
        name="Total Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-collapse-down",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_OUT_W_TOTAL,
        name="Total Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-expand-up",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB1_W,
        name="USB-A 1 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB2_W,
        name="USB-A 2 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB_QC1_W,
        name="USB-A QC 1 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB_QC2_W,
        name="USB-A QC 2 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USBC1_W,
        name="USB-C 1 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-c-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USBC2_W,
        name="USB-C 2 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:usb-c-port",
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USBC1_TEMP,
        name="USB-C 1 Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_USBC2_TEMP,
        name="USB-C 2 Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),

    # ── Energy totals ─────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_CHG_POWER_AC,
        name="Cumulative AC Charged",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_CHG_POWER_DC,
        name="Cumulative DC Charged",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_CHG_SUN_POWER,
        name="Solar Charge Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-panel",
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── System ───────────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_BP_POWER_SOC,
        name="Battery Protection SOC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-lock",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_WIFI_RSSI,
        name="WiFi Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),

    # ── Battery lifetime statistics (bms_bmsInfo) ─────────────────────────
    EcoFlowSensorDescription(
        key=KEY_INFO_SOH,
        name="State of Health (BMS Info)",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart-variant",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_CYCLES,
        name="Total Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_ACCU_CHG,
        name="Cumulative Charged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-plus-variant",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_ACCU_DSG,
        name="Cumulative Discharged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-minus-variant",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_ACCU_CHG_E,
        name="Cumulative Charged Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_ACCU_DSG_E,
        name="Cumulative Discharged Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_ROUND_TRIP,
        name="Round-Trip Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:lightning-bolt-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_SELF_DSG,
        name="Self-Discharge Rate",
        native_unit_of_measurement=f"{PERCENTAGE}/day",
        icon="mdi:battery-minus",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_DEEP_DSG,
        name="Deep Discharge Count",
        icon="mdi:battery-alert",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_OHM_RES,
        name="Internal Resistance",
        native_unit_of_measurement="mΩ",
        icon="mdi:omega",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        round_digits=1,
    ),

    # ── Generator SOC thresholds (bms_emsStatus) ──────────────────────────
    EcoFlowSensorDescription(
        key=KEY_GEN_MIN_SOC,
        name="Generator Start SOC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:engine-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_GEN_MAX_SOC,
        name="Generator Stop SOC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:engine-off-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),

    # ── MPPT beep state ───────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_MPPT_BEEP,
        name="MPPT Beep",
        icon="mdi:volume-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensors from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]

    entities: list = [
        EcoFlowSensorEntity(coordinator, desc, sn)
        for desc in SENSOR_DESCRIPTIONS
    ]
    # Diagnostic sensor — always added, shows connection mode in HA UI
    entities.append(EcoFlowConnectionModeSensor(entry_data, sn))
    async_add_entities(entities)


class EcoFlowSensorEntity(CoordinatorEntity[EcoflowCoordinator], SensorEntity):
    """One sensor backed by the EcoFlow coordinator."""

    entity_description: EcoFlowSensorDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowSensorDescription,
        sn: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description  = description
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
    def native_value(self) -> float | str | None:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get(self.entity_description.key)
        # Fall back to secondary key when primary is absent or zero
        if (val is None or val == 0) and self.entity_description.fallback_key:
            val = self.coordinator.data.get(self.entity_description.fallback_key)
        if val is None:
            return None
        try:
            scaled = float(val) * self.entity_description.scale
            r = self.entity_description.round_digits
            return round(scaled, r) if r is not None else scaled
        except (TypeError, ValueError):
            return str(val)

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data)


class EcoFlowConnectionModeSensor(SensorEntity):
    """Diagnostic sensor showing the active connection mode.

    Values:
      hybrid    — MQTT telemetry (Private API) + REST SET (Developer API)
      mqtt_only — MQTT telemetry only, REST SET unavailable
      rest_only — Developer API only (no MQTT / fallback)

    Always enabled regardless of coordinator data — useful for diagnosing
    setup problems before any telemetry arrives.
    """

    _attr_has_entity_name                 = True
    _attr_entity_registry_enabled_default = True
    _attr_icon                            = "mdi:connection"
    _attr_entity_category                 = EntityCategory.DIAGNOSTIC

    def __init__(self, entry_data: dict, sn: str) -> None:
        self._entry_data       = entry_data
        self._sn               = sn
        self._attr_unique_id   = f"{sn}_connection_mode"
        self._attr_name        = "Connection Mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=f"EcoFlow {DEVICE_MODEL}",
            manufacturer=MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @property
    def native_value(self) -> str:
        """Return active connection mode string."""
        has_mqtt = self._entry_data.get("mqtt_client") is not None
        has_rest = self._entry_data.get("rest_api") is not None
        if has_mqtt and has_rest:
            return "hybrid"
        if has_mqtt:
            return "mqtt_only"
        return "rest_only"

    @property
    def extra_state_attributes(self) -> dict:
        """Extra diagnostic detail visible in HA developer tools."""
        has_rest   = self._entry_data.get("rest_api") is not None
        has_mqtt   = self._entry_data.get("mqtt_client") is not None
        api        = self._entry_data.get("api")
        is_private = hasattr(api, "_email")
        return {
            "mqtt_connected":    has_mqtt,
            "rest_api_attached": has_rest,
            "auth_mode":         "private" if is_private else "public",
            "sn":                self._sn,
        }

    @property
    def available(self) -> bool:
        return True  # always available — diagnostic sensor
