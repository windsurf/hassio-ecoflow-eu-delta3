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
from .devices.registry import UNKNOWN_MODEL
from .devices.delta3_1500 import (
    # Battery
    KEY_SOC, KEY_SOH, KEY_CYCLES,
    KEY_BATT_VOLT, KEY_BATT_CURR, KEY_BATT_TEMP,
    KEY_REMAIN_CAP, KEY_FULL_CAP, KEY_DESIGN_CAP,
    KEY_MIN_CELL_TEMP, KEY_MAX_CELL_TEMP,
    KEY_MIN_CELL_VOLT, KEY_MAX_CELL_VOLT,
    KEY_MIN_MOS_TEMP, KEY_MAX_MOS_TEMP,
    KEY_SOC_FLOAT, KEY_MAX_VOL_DIFF, KEY_DC12V_STATE,
    # BMS extended (v0.2.23)
    KEY_BMS_ACT_SOC, KEY_BMS_SOC, KEY_BMS_CHG_STATE, KEY_BMS_SYS_STATE,
    KEY_BMS_MOS_STATE, KEY_BMS_FAULT, KEY_BMS_ALL_FAULT,
    KEY_BMS_ERR_CODE, KEY_BMS_ALL_ERR, KEY_BMS_BALANCE,
    KEY_BMS_CHG_CAP, KEY_BMS_DSG_CAP, KEY_BMS_INPUT_W, KEY_BMS_OUTPUT_W,
    KEY_BMS_REAL_SOH, KEY_BMS_CALC_SOH, KEY_BMS_CYC_SOH,
    KEY_BMS_DIFF_SOC, KEY_BMS_TARGET_SOC, KEY_BMS_TAG_AMP,
    KEY_BMS_REMAIN_T, KEY_BMS_BQ_REG,
    # BmsInfo lifetime (v0.2.23)
    KEY_INFO_HIGH_T_CHG, KEY_INFO_HIGH_T, KEY_INFO_LOW_T_CHG, KEY_INFO_LOW_T,
    KEY_INFO_PWR_CAP,
    # EMS
    KEY_REMAIN_TIME, KEY_CHARGE_TIME,
    KEY_EMS_MAX_CHG_SOC, KEY_EMS_MIN_DSG_SOC,
    KEY_EMS_CHG_VOL, KEY_EMS_CHG_AMP, KEY_EMS_FAN_LEVEL,
    KEY_EMS_CHG_LINE, KEY_EMS_SYS_STATE,
    # EMS extended (v0.2.23)
    KEY_EMS_DSG_TIME, KEY_EMS_CHG_STATE, KEY_EMS_CHG_CMD, KEY_EMS_DSG_CMD,
    KEY_EMS_CHG_COND, KEY_EMS_DSG_COND, KEY_EMS_WARN, KEY_EMS_NORMAL,
    KEY_EMS_SOC_FLOAT, KEY_EMS_SOC_LCD, KEY_EMS_PARA_V_MAX, KEY_EMS_PARA_V_MIN,
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
    KEY_DC_IN_VOLT, KEY_DC_IN_AMP, KEY_DC_IN_TEMP, KEY_AC_CFG_FREQ,
    # INV extended (v0.2.23)
    KEY_INV_WORK_MODE, KEY_INV_CHARGER_T, KEY_INV_DSG_TYPE,
    KEY_INV_ERR_CODE, KEY_INV_DIP,
    # Solar / MPPT
    KEY_SOLAR_W, KEY_SOLAR_VOLT, KEY_SOLAR_AMP,
    KEY_SOLAR_OUT_W, KEY_MPPT_TEMP,
    KEY_DC12V_OUT_W, KEY_DC12V_OUT_VOLT, KEY_DC12V_OUT_AMP,
    KEY_DC12V_TEMP, KEY_DC12V_IN_W, KEY_DC_OUT_TEMP, KEY_DCDC12V_W,
    # MPPT extended (v0.2.23)
    KEY_MPPT_CHG_STATE, KEY_MPPT_CHG_TYPE, KEY_MPPT_CFG_CHG_T,
    KEY_MPPT_DSG_TYPE, KEY_MPPT_FAULT, KEY_MPPT_OUT_AMP, KEY_MPPT_OUT_VOLT,
    KEY_MPPT_DC24V_ST, KEY_SCR_STANDBY, KEY_POW_STANDBY,
    # USB
    KEY_USB1_W, KEY_USB2_W, KEY_USB_QC1_W, KEY_USB_QC2_W,
    KEY_USBC1_W, KEY_USBC2_W,
    KEY_USBC1_TEMP, KEY_USBC2_TEMP,
    # PD / System
    KEY_IN_W_TOTAL, KEY_OUT_W_TOTAL,
    KEY_CHG_POWER_AC, KEY_CHG_POWER_DC,
    KEY_DSG_POWER_AC, KEY_DSG_POWER_DC,
    KEY_CHG_SUN_POWER, KEY_WIFI_RSSI,
    KEY_BP_POWER_SOC, KEY_GEN_MIN_SOC, KEY_GEN_MAX_SOC, KEY_MPPT_BEEP,
    # PD extended (v0.2.23)
    KEY_PD_CAR_TEMP, KEY_PD_CAR_TIME, KEY_PD_CHG_TYPE, KEY_PD_DCIN_TIME,
    KEY_PD_ERR_CODE, KEY_PD_RJ45, KEY_PD_EXT38, KEY_PD_EXT48,
    KEY_PD_HYSTERESIS, KEY_PD_INV_TIME, KEY_PD_MPPT_TIME, KEY_PD_RELAY_CNT,
    KEY_PD_TYPEC_TIME, KEY_PD_USB_TIME, KEY_PD_USBQC_TIME, KEY_PD_WIFI_RCV,
    # Slave battery (v0.2.25)
    KEY_SLV_SOC, KEY_SLV_SOC_FLOAT, KEY_SLV_SOH, KEY_SLV_REAL_SOH,
    KEY_SLV_VOLT, KEY_SLV_CURR, KEY_SLV_TEMP,
    KEY_SLV_MIN_CELL_T, KEY_SLV_MAX_CELL_T,
    KEY_SLV_MIN_MOS_T, KEY_SLV_MAX_MOS_T,
    KEY_SLV_MIN_CELL_V, KEY_SLV_MAX_CELL_V, KEY_SLV_MAX_VOL_D,
    KEY_SLV_REMAIN_CAP, KEY_SLV_FULL_CAP, KEY_SLV_DESIGN_CAP,
    KEY_SLV_INPUT_W, KEY_SLV_OUTPUT_W, KEY_SLV_CYCLES, KEY_SLV_REMAIN_T,
    KEY_SLV_DIFF_SOC, KEY_SLV_CHG_CAP, KEY_SLV_DSG_CAP,
    KEY_SLV_ACCU_CHG, KEY_SLV_ACCU_DSG, KEY_SLV_ACCU_CHG_E, KEY_SLV_ACCU_DSG_E,
    KEY_SLV_OHM_RES, KEY_SLV_ROUND_TRIP, KEY_SLV_DEEP_DSG,
    KEY_SLV_ERR_CODE, KEY_SLV_CYC_SOH,
)
from .devices.delta2 import (
    DEVICE_MODEL as D2_MODEL,
    AC_CHG_WATTS_MIN as D2_CHG_MIN,
    AC_CHG_WATTS_MAX as D2_CHG_MAX,
    AC_CHG_WATTS_STEP as D2_CHG_STEP,
    KEY_EMS_DSG_TIME as D2_EMS_DSG_TIME,
)
from .devices.delta2_max import (
    DEVICE_MODEL as D2M_MODEL,
    KEY_SOLAR2_W, KEY_SOLAR2_VOLT, KEY_SOLAR2_AMP,
    KEY_ACCU_CHG_ENERGY, KEY_ACCU_DSG_ENERGY,
    KEY_EMS_DSG_TIME_D2M,
    KEY_SLV1_SOC, KEY_SLV1_SOH, KEY_SLV1_SOC_FLOAT, KEY_SLV1_TEMP,
    KEY_SLV1_MIN_CT, KEY_SLV1_MAX_CT, KEY_SLV1_VOLT, KEY_SLV1_MIN_CV, KEY_SLV1_MAX_CV,
    KEY_SLV1_REMAIN_CAP, KEY_SLV1_FULL_CAP, KEY_SLV1_DESIGN_CAP,
    KEY_SLV1_CYCLES, KEY_SLV1_INPUT_W, KEY_SLV1_OUTPUT_W,
    KEY_SLV2_SOC, KEY_SLV2_SOH, KEY_SLV2_SOC_FLOAT, KEY_SLV2_TEMP,
    KEY_SLV2_MIN_CT, KEY_SLV2_MAX_CT, KEY_SLV2_VOLT, KEY_SLV2_MIN_CV, KEY_SLV2_MAX_CV,
    KEY_SLV2_REMAIN_CAP, KEY_SLV2_FULL_CAP, KEY_SLV2_DESIGN_CAP,
    KEY_SLV2_CYCLES, KEY_SLV2_INPUT_W, KEY_SLV2_OUTPUT_W,
)
from .devices import delta_pro as dp
from .devices import delta_pro_3 as dp3
from .devices import delta_max as dm
from .devices import delta_mini as dmi
from .devices import river2 as r2
from .devices import river1 as r1
from .devices import powerstream as ps
from .devices import glacier as gl
from .devices import wave2 as w2
from .devices import smart_plug as sp_dev

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EcoFlowSensorDescription(SensorEntityDescription):
    """Sensor description with optional scaling and rounding."""
    scale:        float       = 1.0
    round_digits: int | None  = 2
    # Optional fallback key used when the primary key is absent in coordinator data
    fallback_key: str | None  = None


_D361_SENSORS: tuple[EcoFlowSensorDescription, ...] = (

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

    # ── Slave battery (bms_slave) — v0.2.25 ──────────────────────────────
    # Slave battery confirmed present via MQTT telemetry (April 2026).
    # Primary sensors enabled by default; diagnostics disabled by default.

    EcoFlowSensorDescription(
        key=KEY_SLV_SOC,
        name="Slave Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_SOC_FLOAT,
        name="Slave Battery Level (precise)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_SOH,
        name="Slave State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_VOLT,
        name="Slave Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_CURR,
        name="Slave Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_TEMP,
        name="Slave Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_REMAIN_CAP,
        name="Slave Remaining Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-medium",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_FULL_CAP,
        name="Slave Full Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_DESIGN_CAP,
        name="Slave Design Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_INPUT_W,
        name="Slave Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_OUTPUT_W,
        name="Slave Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_CYCLES,
        name="Slave Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_REMAIN_T,
        name="Slave Time Remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    # Slave diagnostics
    EcoFlowSensorDescription(
        key=KEY_SLV_MIN_CELL_T,
        name="Slave Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_CELL_T,
        name="Slave Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MIN_MOS_T,
        name="Slave Min MOS Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_MOS_T,
        name="Slave Max MOS Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MIN_CELL_V,
        name="Slave Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_CELL_V,
        name="Slave Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_VOL_D,
        name="Slave Max Cell Voltage Difference",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_REAL_SOH,
        name="Slave Real State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart-variant",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_CHG_CAP,
        name="Slave Charged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-plus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_DSG_CAP,
        name="Slave Discharged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-minus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ACCU_CHG,
        name="Slave Cumulative Charged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-plus-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ACCU_DSG,
        name="Slave Cumulative Discharged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-minus-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ACCU_CHG_E,
        name="Slave Cumulative Charged Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ACCU_DSG_E,
        name="Slave Cumulative Discharged Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_OHM_RES,
        name="Slave Internal Resistance",
        native_unit_of_measurement="mOhm",
        icon="mdi:omega",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ROUND_TRIP,
        name="Slave Round-Trip Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-sync-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_DEEP_DSG,
        name="Slave Deep Discharge Count",
        icon="mdi:battery-alert",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_ERR_CODE,
        name="Slave Error Code",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_DIFF_SOC,
        name="Slave SOC Difference",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-arrow-up-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_CYC_SOH,
        name="Slave Cycle State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=2,
        entity_registry_enabled_default=False,
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

    # ── BMS extended diagnostics (v0.2.23) ───────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_BMS_ACT_SOC,
        name="Battery Actual SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_SOC,
        name="Battery SOC (BMS)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_CHG_STATE,
        name="BMS Charge State",
        icon="mdi:battery-charging",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_SYS_STATE,
        name="BMS System State",
        icon="mdi:information",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_MOS_STATE,
        name="BMS MOS State",
        icon="mdi:chip",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_FAULT,
        name="BMS Fault",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_ALL_FAULT,
        name="BMS All Faults",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_ERR_CODE,
        name="BMS Error Code",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_ALL_ERR,
        name="BMS All Error Codes",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_BALANCE,
        name="BMS Cell Balancing",
        icon="mdi:scale-balance",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_CHG_CAP,
        name="BMS Charged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-charging",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_DSG_CAP,
        name="BMS Discharged Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-minus",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_INPUT_W,
        name="BMS Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_OUTPUT_W,
        name="BMS Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_REAL_SOH,
        name="BMS Real SoH",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_CALC_SOH,
        name="BMS Calculated SoH",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_CYC_SOH,
        name="BMS Cycle SoH",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart-variant",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_DIFF_SOC,
        name="BMS SOC Difference",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_TARGET_SOC,
        name="BMS Target SOC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-arrow-up",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_TAG_AMP,
        name="BMS Target Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_REMAIN_T,
        name="BMS Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:clock",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_BMS_BQ_REG,
        name="BMS BQ Status Register",
        icon="mdi:chip",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    # BmsInfo lifetime (v0.2.23)
    EcoFlowSensorDescription(
        key=KEY_INFO_HIGH_T_CHG,
        name="High Temp Charge Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:thermometer-high",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_HIGH_T,
        name="High Temp Total Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:thermometer-high",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_LOW_T_CHG,
        name="Low Temp Charge Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:thermometer-low",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_LOW_T,
        name="Low Temp Total Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:thermometer-low",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INFO_PWR_CAP,
        name="Power Capability",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── EMS extended (v0.2.23) ────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_EMS_DSG_TIME,
        name="Discharge Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:battery-clock",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_STATE,
        name="EMS Charge State",
        icon="mdi:battery-charging",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_CMD,
        name="EMS Charge Command",
        icon="mdi:battery-charging",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_DSG_CMD,
        name="EMS Discharge Command",
        icon="mdi:battery-minus",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_COND,
        name="EMS Charge Condition",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_DSG_COND,
        name="EMS Discharge Condition",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_WARN,
        name="EMS Warning State",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_NORMAL,
        name="EMS Normal Flag",
        icon="mdi:check-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_SOC_FLOAT,
        name="Display SOC (float)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_SOC_LCD,
        name="Display SOC (LCD)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_PARA_V_MAX,
        name="Parallel Voltage Max",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_PARA_V_MIN,
        name="Parallel Voltage Min",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── INV extended (v0.2.23) ────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_INV_WORK_MODE,
        name="AC Work Mode",
        icon="mdi:power-settings",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INV_CHARGER_T,
        name="Charger Type (INV)",
        icon="mdi:ev-plug-type2",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INV_DSG_TYPE,
        name="Discharge Type",
        icon="mdi:battery-arrow-down",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INV_ERR_CODE,
        name="INV Error Code",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_INV_DIP,
        name="AC DIP Switch",
        icon="mdi:toggle-switch",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    # ── MPPT extended (v0.2.23) ───────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_MPPT_CHG_STATE,
        name="MPPT Charge State",
        icon="mdi:solar-power",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_CHG_TYPE,
        name="MPPT Charge Type",
        icon="mdi:ev-plug-type2",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_CFG_CHG_T,
        name="MPPT Configured Charge Type",
        icon="mdi:ev-plug-type2",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_DSG_TYPE,
        name="MPPT Discharge Type",
        icon="mdi:battery-arrow-down",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_FAULT,
        name="MPPT Fault Code",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_OUT_AMP,
        name="MPPT Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_OUT_VOLT,
        name="MPPT Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_DC24V_ST,
        name="DC 24V Port State",
        icon="mdi:power-socket",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SCR_STANDBY,
        name="Screen Standby Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:monitor",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_POW_STANDBY,
        name="Overall Standby Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    # ── PD extended (v0.2.23) ─────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_PD_CAR_TEMP,
        name="DC 12V Temperature (PD)",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_CAR_TIME,
        name="DC 12V Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_CHG_TYPE,
        name="Charger Type (PD)",
        icon="mdi:ev-plug-type2",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_DCIN_TIME,
        name="DC Input Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_ERR_CODE,
        name="PD Error Code",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_RJ45,
        name="RJ45 Port Status",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_EXT38,
        name="3.8V Port Status",
        icon="mdi:power-socket",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_EXT48,
        name="4.8V Port Status",
        icon="mdi:power-socket",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_HYSTERESIS,
        name="Hysteresis SOC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_INV_TIME,
        name="Inverter Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_MPPT_TIME,
        name="MPPT Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_RELAY_CNT,
        name="Relay Switch Count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_TYPEC_TIME,
        name="USB-C Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_USB_TIME,
        name="USB-A Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_USBQC_TIME,
        name="USB QC Use Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_PD_WIFI_RCV,
        name="WiFi Auto Recovery Mode",
        icon="mdi:wifi-sync",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MPPT_BEEP,
        name="MPPT Beep",
        icon="mdi:volume-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Delta 2 — 45 sensors
# Source: tolwi/hassio-ecoflow-cloud (internal/delta2.py) + US repo (confirmed)
# ══════════════════════════════════════════════════════════════════════════════

_D2_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
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
        key=KEY_SOH,
        name="State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_SOC_LCD,
        name="Battery Level (Combined)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_EMS_CHG_STATE,
        name="Battery Charging State",
        icon="mdi:battery-charging",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_REMAIN_CAP,
        name="Remaining Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-medium",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_FULL_CAP,
        name="Full Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_DESIGN_CAP,
        name="Design Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_CYCLES,
        name="Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
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
        key=KEY_BATT_VOLT,
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MIN_CELL_VOLT,
        name="Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_MAX_CELL_VOLT,
        name="Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),

    # ── Power ────────────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_IN_W_TOTAL,
        name="Total Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_OUT_W_TOTAL,
        name="Total Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_IN_W,
        name="AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_AC_OUT_W,
        name="AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
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
        key=KEY_AC_OUT_VOLT,
        name="AC Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=1,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOLAR_W,
        name="Solar Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SOLAR_OUT_W,
        name="DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),

    # ── USB / Type-C ─────────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_USBC1_W,
        name="Type-C (1) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USBC2_W,
        name="Type-C (2) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB1_W,
        name="USB (1) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB2_W,
        name="USB (2) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB_QC1_W,
        name="USB QC (1) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_USB_QC2_W,
        name="USB QC (2) Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),

    # ── Time remaining ───────────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_CHARGE_TIME,
        name="Charge Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=D2_EMS_DSG_TIME,
        name="Discharge Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_REMAIN_TIME,
        name="Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),

    # ── Inverter temperature ─────────────────────────────────────────────
    EcoFlowSensorDescription(
        key=KEY_AC_TEMP,
        name="Inverter Output Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
    ),

    # ── Slave battery (optional extra battery pack) ──────────────────────
    EcoFlowSensorDescription(
        key=KEY_SLV_SOC,
        name="Slave Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_SOH,
        name="Slave State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_TEMP,
        name="Slave Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MIN_CELL_T,
        name="Slave Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_CELL_T,
        name="Slave Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=1,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_VOLT,
        name="Slave Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_digits=2,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MIN_CELL_V,
        name="Slave Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_MAX_CELL_V,
        name="Slave Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_REMAIN_CAP,
        name="Slave Remaining Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-medium",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_FULL_CAP,
        name="Slave Full Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery-high",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_DESIGN_CAP,
        name="Slave Design Capacity",
        native_unit_of_measurement="mAh",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_CYCLES,
        name="Slave Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_INPUT_W,
        name="Slave Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
    EcoFlowSensorDescription(
        key=KEY_SLV_OUTPUT_W,
        name="Slave Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        round_digits=0,
        entity_registry_enabled_default=False,
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# Delta 2 Max — 67 sensors
# Source: tolwi/hassio-ecoflow-cloud (internal/delta2_max.py)
# Key differences: dual solar, dual numbered slaves, accumulative energy
# ══════════════════════════════════════════════════════════════════════════════

_D2M_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    # ── Battery ──────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_SOH, name="State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_EMS_SOC_LCD, name="Battery Level (Combined)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=KEY_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=KEY_MIN_CELL_TEMP, name="Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_MAX_CELL_TEMP, name="Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_MIN_CELL_VOLT, name="Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_MAX_CELL_VOLT, name="Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SOC_FLOAT, name="Battery Level SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=2, entity_registry_enabled_default=False),

    # ── Accumulative energy ──────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_ACCU_CHG_ENERGY, name="Cumulative Charge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=KEY_ACCU_DSG_ENERGY, name="Cumulative Discharge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),

    # ── Power ────────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_AC_IN_VOLT, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),

    # ── Solar (dual MPPT) ────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_SOLAR_W, name="Solar (1) Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_SOLAR2_W, name="Solar (2) Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_SOLAR_VOLT, name="Solar (1) Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=KEY_SOLAR2_VOLT, name="Solar (2) Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=KEY_SOLAR_AMP, name="Solar (1) Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=KEY_SOLAR2_AMP, name="Solar (2) Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=KEY_SOLAR_OUT_W, name="DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── USB / Type-C ─────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_USBC1_W, name="Type-C (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_USBC2_W, name="Type-C (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_USB1_W, name="USB (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_USB2_W, name="USB (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_USB_QC1_W, name="USB QC (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_USB_QC2_W, name="USB QC (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── Time remaining ───────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_CHARGE_TIME, name="Charge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=KEY_EMS_DSG_TIME_D2M, name="Discharge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── Inverter ─────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_AC_TEMP, name="Inverter Output Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),

    # ── Slave 1 battery ──────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_SLV1_SOC, name="Slave 1 Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_SOH, name="Slave 1 State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_SOC_FLOAT, name="Slave 1 Battery Level SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_TEMP, name="Slave 1 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_MIN_CT, name="Slave 1 Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_MAX_CT, name="Slave 1 Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_VOLT, name="Slave 1 Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_MIN_CV, name="Slave 1 Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_MAX_CV, name="Slave 1 Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_REMAIN_CAP, name="Slave 1 Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_FULL_CAP, name="Slave 1 Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_DESIGN_CAP, name="Slave 1 Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_CYCLES, name="Slave 1 Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_INPUT_W, name="Slave 1 Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV1_OUTPUT_W, name="Slave 1 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),

    # ── Slave 2 battery ──────────────────────────────────────────────────
    EcoFlowSensorDescription(key=KEY_SLV2_SOC, name="Slave 2 Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_SOH, name="Slave 2 State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_SOC_FLOAT, name="Slave 2 Battery Level SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_TEMP, name="Slave 2 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_MIN_CT, name="Slave 2 Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_MAX_CT, name="Slave 2 Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_VOLT, name="Slave 2 Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_MIN_CV, name="Slave 2 Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_MAX_CV, name="Slave 2 Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_REMAIN_CAP, name="Slave 2 Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_FULL_CAP, name="Slave 2 Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_DESIGN_CAP, name="Slave 2 Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_CYCLES, name="Slave 2 Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_INPUT_W, name="Slave 2 Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=KEY_SLV2_OUTPUT_W, name="Slave 2 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
)

# ══════════════════════════════════════════════════════════════════════════════
# Gen 1 helper — shared sensor builder for Delta Pro / Max / Mini
# These devices use bmsMaster.* / ems.* / bmsSlave1/2.* key schema
# Sensors are READ-ONLY — SET commands use TCP protocol not yet supported
# ══════════════════════════════════════════════════════════════════════════════

def _gen1_main_sensors(d) -> list:
    """Main battery + power + time sensors for a Gen 1 device module d."""
    return [
        EcoFlowSensorDescription(key=d.KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_SOC_FLOAT, name="Battery Level (precise)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_SOH, name="State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_EMS_SOC_LCD, name="Battery Level (Combined)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
        EcoFlowSensorDescription(key=d.KEY_MIN_CELL_TEMP, name="Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_MAX_CELL_TEMP, name="Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_BATT_CURR, name="Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_MIN_CELL_VOLT, name="Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=d.KEY_MAX_CELL_VOLT, name="Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
        # Power
        EcoFlowSensorDescription(key=d.KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_AC_IN_VOLT, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
        EcoFlowSensorDescription(key=d.KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
        EcoFlowSensorDescription(key=d.KEY_SOLAR_W, name="Solar Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_SOLAR_VOLT, name="Solar Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
        EcoFlowSensorDescription(key=d.KEY_SOLAR_AMP, name="Solar Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
        EcoFlowSensorDescription(key=d.KEY_SOLAR_OUT_W, name="DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_SOLAR_OUT_VOLT, name="DC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
        # USB / Type-C
        EcoFlowSensorDescription(key=d.KEY_USBC1_W, name="Type-C (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_USBC2_W, name="Type-C (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_USB1_W, name="USB (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_USB2_W, name="USB (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_USB_QC1_W, name="USB QC (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_USB_QC2_W, name="USB QC (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        # Time
        EcoFlowSensorDescription(key=d.KEY_CHARGE_TIME, name="Charge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_DSG_TIME, name="Discharge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    ]


def _gen1_energy_sensors(d) -> list:
    """Energy counter sensors for Gen 1 devices."""
    return [
        EcoFlowSensorDescription(key=d.KEY_CHG_SUN_POWER, name="Solar Input Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_CHG_POWER_AC, name="AC Charge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_CHG_POWER_DC, name="DC Charge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_DSG_POWER_AC, name="AC Discharge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=d.KEY_DSG_POWER_DC, name="DC Discharge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    ]


def _gen1_slave_sensors(d, n: int, prefix: str) -> list:
    """Slave battery sensors for Gen 1 devices. n=1 or 2, prefix=KEY_SLVn_*"""
    slv = {a: getattr(d, f"KEY_SLV{n}_{a}") for a in
           ["SOC", "SOC_FLOAT", "SOH", "TEMP", "MIN_CT", "MAX_CT",
            "VOLT", "CURR", "MIN_CV", "MAX_CV",
            "REMAIN_CAP", "FULL_CAP", "DESIGN_CAP",
            "CYCLES", "INPUT_W", "OUTPUT_W"]}
    return [
        EcoFlowSensorDescription(key=slv["SOC"], name=f"Slave {n} Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["SOC_FLOAT"], name=f"Slave {n} Battery Level (precise)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["SOH"], name=f"Slave {n} State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["TEMP"], name=f"Slave {n} Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["VOLT"], name=f"Slave {n} Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["CURR"], name=f"Slave {n} Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["MIN_CV"], name=f"Slave {n} Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["MAX_CV"], name=f"Slave {n} Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["CYCLES"], name=f"Slave {n} Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["INPUT_W"], name=f"Slave {n} Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
        EcoFlowSensorDescription(key=slv["OUTPUT_W"], name=f"Slave {n} Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    ]


# Delta Pro specific sensors
_DP_EXTRA = (
    EcoFlowSensorDescription(key=dp.KEY_DC_CAR_OUT_W, name="DC Car Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dp.KEY_DC_ANDERSON_W, name="DC Anderson Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
)

_DPRO_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple(
    _gen1_main_sensors(dp) + list(_DP_EXTRA) + _gen1_energy_sensors(dp)
    + _gen1_slave_sensors(dp, 1, "bmsSlave1") + _gen1_slave_sensors(dp, 2, "bmsSlave2")
)

# Delta Max — same as Pro but with DC car out (no Anderson)
_DM_EXTRA = (
    EcoFlowSensorDescription(key=dm.KEY_DC_CAR_OUT_W, name="DC Car Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
)

_DMAX_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple(
    _gen1_main_sensors(dm) + list(_DM_EXTRA) + _gen1_energy_sensors(dm)
    + _gen1_slave_sensors(dm, 1, "bmsSlave1") + _gen1_slave_sensors(dm, 2, "bmsSlave2")
)

# Delta Mini — no slaves, no DC car/anderson, has energy counters
_DMI_EXTRA = (
    EcoFlowSensorDescription(key=dmi.KEY_DC_CAR_OUT_W, name="DC Car Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dmi.KEY_DC_ANDERSON_W, name="DC Anderson Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
)

_DMINI_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple(
    _gen1_main_sensors(dmi) + list(_DMI_EXTRA) + _gen1_energy_sensors(dmi)
)

# ══════════════════════════════════════════════════════════════════════════════
# River 2 series — Gen 2 protocol (full control)
# Shared base sensors, per-variant differences in AC charging and DC solar
# ══════════════════════════════════════════════════════════════════════════════

_R2_BASE_SENSORS: list[EcoFlowSensorDescription] = [
    EcoFlowSensorDescription(key=r2.KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_SOH, name="State of Health", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_EMS_SOC_LCD, name="Battery Level (Combined)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_EMS_CHG_STATE, name="Battery Charging State", icon="mdi:battery-charging", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r2.KEY_MIN_CELL_TEMP, name="Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_MAX_CELL_TEMP, name="Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_MIN_CELL_VOLT, name="Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r2.KEY_MAX_CELL_VOLT, name="Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    # Power
    EcoFlowSensorDescription(key=r2.KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_AC_IN_VOLT, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r2.KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r2.KEY_TYPEC_IN_W, name="Type-C Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_SOLAR_W, name="Solar Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_DC_OUT_W, name="DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_USBC1_W, name="Type-C Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_USB1_W, name="USB Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    # Time
    EcoFlowSensorDescription(key=r2.KEY_CHARGE_TIME, name="Charge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_EMS_DSG_TIME, name="Discharge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_REMAIN_TIME, name="Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r2.KEY_AC_TEMP, name="Inverter Output Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
]

# River 2 / River 2 Max: add DC solar current + voltage sensors
_R2_DC_SOLAR = [
    EcoFlowSensorDescription(key=r2.KEY_DC_IN_AMP, name="Solar Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=r2.KEY_DC_IN_VOLT, name="Solar Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
]

_R2_SENSORS:    tuple[EcoFlowSensorDescription, ...] = tuple(_R2_BASE_SENSORS + _R2_DC_SOLAR)
_R2MAX_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple(_R2_BASE_SENSORS + _R2_DC_SOLAR)
_R2PRO_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple(_R2_BASE_SENSORS)  # no DC solar sensors

# ══════════════════════════════════════════════════════════════════════════════
# River 1 series — Gen 1 protocol (read-only, TCP commands not yet supported)
# River Max: bmsMaster + slave, River Pro: pd.soc + slave, River Mini: inv.soc
# ══════════════════════════════════════════════════════════════════════════════

def _r1_energy_sensors() -> list:
    """Energy counter sensors shared by all River 1 variants."""
    return [
        EcoFlowSensorDescription(key=r1.KEY_CHG_SUN_POWER, name="Solar Input Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=r1.KEY_CHG_POWER_AC, name="AC Charge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=r1.KEY_CHG_POWER_DC, name="DC Charge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=r1.KEY_DSG_POWER_AC, name="AC Discharge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
        EcoFlowSensorDescription(key=r1.KEY_DSG_POWER_DC, name="DC Discharge Energy", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    ]

# ── River Max (40 sensors) ───────────────────────────────────────────────────
_RMAX_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple([
    EcoFlowSensorDescription(key=r1.RMAX_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.RMAX_COMBINED_SOC, name="Battery Level (Combined)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.RMAX_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=r1.RMAX_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.RMAX_MIN_CELL_TEMP, name="Min Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_MAX_CELL_TEMP, name="Max Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_MIN_CELL_VOLT, name="Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_MAX_CELL_VOLT, name="Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    # Power
    EcoFlowSensorDescription(key=r1.KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_VOLT, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_DC_OUT_W, name="DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_TYPEC_OUT_W, name="Type-C Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB1_W, name="USB (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB2_W, name="USB (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB3_W, name="USB (3) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_REMAIN_TIME, name="Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_INV_IN_TEMP, name="Inverter Inside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_INV_OUT_TEMP, name="Inverter Outside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    # Slave
    EcoFlowSensorDescription(key=r1.RMAX_SLV_SOC, name="Slave Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_TEMP, name="Slave Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_VOLT, name="Slave Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_MIN_CV, name="Slave Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_MAX_CV, name="Slave Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_CYCLES, name="Slave Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0, entity_registry_enabled_default=False),
] + _r1_energy_sensors())

# ── River Pro (similar to Max but pd.soc primary, has AC slow charge flag) ───
_RPRO_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple([
    EcoFlowSensorDescription(key=r1.RPRO_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.RMAX_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=r1.RMAX_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.RMAX_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_BATT_CURR, name="Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_MIN_CELL_VOLT, name="Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_MAX_CELL_VOLT, name="Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    # Power
    EcoFlowSensorDescription(key=r1.KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_DC_IN_AMP, name="Solar Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=r1.KEY_DC_IN_VOLT, name="Solar Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_VOLT_BE, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_DC_OUT_W, name="DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_TYPEC_OUT_W, name="Type-C Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB1_W, name="USB (1) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB2_W, name="USB (2) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_USB3_W, name="USB (3) Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_REMAIN_TIME, name="Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_INV_IN_TEMP, name="Inverter Inside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_INV_OUT_TEMP, name="Inverter Outside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    # Slave
    EcoFlowSensorDescription(key=r1.RMAX_SLV_SOC, name="Slave Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_TEMP, name="Slave Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_VOLT, name="Slave Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_MIN_CV, name="Slave Min Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_MAX_CV, name="Slave Max Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=r1.RMAX_SLV_CYCLES, name="Slave Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0, entity_registry_enabled_default=False),
] + _r1_energy_sensors())

# ── River Mini (17 sensors — minimal, inv.soc, no slaves) ────────────────────
_RMINI_SENSORS: tuple[EcoFlowSensorDescription, ...] = tuple([
    EcoFlowSensorDescription(key=r1.RMINI_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_IN_W_TOTAL, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_OUT_W_TOTAL, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_W, name="AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=r1.KEY_AC_IN_VOLT_BE, name="AC Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_AC_OUT_VOLT, name="AC Output Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_DC_IN_VOLT, name="Solar Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_DC_IN_AMP, name="Solar Input Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=r1.KEY_INV_IN_TEMP, name="Inverter Inside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.KEY_INV_OUT_TEMP, name="Inverter Outside Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=r1.RMINI_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
] + _r1_energy_sensors())

# ══════════════════════════════════════════════════════════════════════════════
# PowerStream — 57 sensors (read-only, protobuf commands not supported)
# ══════════════════════════════════════════════════════════════════════════════

_PS_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    # Solar 1 (deciWatts, deciVolts, deciAmps, deciCelsius from protobuf)
    EcoFlowSensorDescription(key=ps.KEY_PV1_W, name="Solar 1 Watts", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_PV1_IN_VOLT, name="Solar 1 Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_PV1_OP_VOLT, name="Solar 1 Op Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.01, round_digits=2),
    EcoFlowSensorDescription(key=ps.KEY_PV1_CURR, name="Solar 1 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_PV1_TEMP, name="Solar 1 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    # Solar 2
    EcoFlowSensorDescription(key=ps.KEY_PV2_W, name="Solar 2 Watts", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_PV2_IN_VOLT, name="Solar 2 Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_PV2_OP_VOLT, name="Solar 2 Op Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.01, round_digits=2),
    EcoFlowSensorDescription(key=ps.KEY_PV2_CURR, name="Solar 2 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_PV2_TEMP, name="Solar 2 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    # Battery
    EcoFlowSensorDescription(key=ps.KEY_BAT_SOC, name="Battery Charge", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_BAT_W, name="Battery Input Watts", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_BAT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_BAT_CHG_T, name="Charge Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_BAT_DSG_T, name="Discharge Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    # Inverter
    EcoFlowSensorDescription(key=ps.KEY_INV_W, name="Inverter Output Watts", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_INV_FREQ, name="Inverter Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_INV_TEMP, name="Inverter Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    # System
    EcoFlowSensorDescription(key=ps.KEY_ESP_TEMP, name="ESP Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=ps.KEY_OTHER_LOADS, name="Other Loads", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=ps.KEY_RATED_POWER, name="Rated Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
)

# ══════════════════════════════════════════════════════════════════════════════
# Glacier — 33 sensors (read-only)
# Note: temperature keys use decicelsius (value/10) — scale=0.1
# ══════════════════════════════════════════════════════════════════════════════

_GL_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    EcoFlowSensorDescription(key=gl.KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=gl.KEY_FULL_CAP, name="Full Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=gl.KEY_DESIGN_CAP, name="Design Capacity", native_unit_of_measurement="mAh", icon="mdi:battery", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=gl.KEY_COMBINED_SOC, name="Battery Level (Combined)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_CHG_STATE, name="Battery Charging State", icon="mdi:battery-charging", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_IN_W, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_OUT_W, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_MOTOR_W, name="Motor Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_CHG_REMAIN, name="Charge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_DSG_REMAIN, name="Discharge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_CYCLES, name="Charge Cycles", icon="mdi:battery-sync", state_class=SensorStateClass.TOTAL_INCREASING, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=gl.KEY_BATT_VOLT, name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.001, round_digits=2, entity_registry_enabled_default=False),
    # Fridge temps (decicelsius)
    EcoFlowSensorDescription(key=gl.KEY_AMBIENT_T, name="Ambient Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=gl.KEY_EXHAUST_T, name="Exhaust Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=gl.KEY_WATER_T, name="Water Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=gl.KEY_LEFT_T, name="Left Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=gl.KEY_RIGHT_T, name="Right Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    # Ice maker
    EcoFlowSensorDescription(key=gl.KEY_ICE_TIME, name="Ice Time Remain", native_unit_of_measurement=UnitOfTime.SECONDS, icon="mdi:snowflake", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=gl.KEY_ICE_PCT, name="Ice Percentage", native_unit_of_measurement=PERCENTAGE, icon="mdi:snowflake", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
)

# ══════════════════════════════════════════════════════════════════════════════
# Wave 2 — 27 sensors (read-only)
# ══════════════════════════════════════════════════════════════════════════════

_W2_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    EcoFlowSensorDescription(key=w2.KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_BATT_TEMP, name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=w2.KEY_REMAIN_CAP, name="Remaining Capacity", native_unit_of_measurement="mAh", icon="mdi:battery-medium", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=w2.KEY_CHG_REMAIN, name="Charge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_DSG_REMAIN, name="Discharge Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    # Power
    EcoFlowSensorDescription(key=w2.KEY_PV_W, name="PV Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_BAT_OUT_W, name="Battery Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_PV_CHG_W, name="PV Charging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_AC_IN_W, name="AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_SYS_POWER_W, name="System Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=w2.KEY_MOTOR_W, name="Motor Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    # Climate
    EcoFlowSensorDescription(key=w2.KEY_SET_TEMP, name="Set Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=w2.KEY_AMBIENT_T, name="Ambient Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
)

# ── Description registry — keyed by device model ─────────────────────────────
SENSOR_DESCRIPTIONS_BY_MODEL: dict[str, tuple[EcoFlowSensorDescription, ...]] = {
    "Delta 3 1500": _D361_SENSORS,
    "Delta 3 Plus": _D361_SENSORS,
    "Delta 3 Max": _D361_SENSORS,
    "Delta 2": _D2_SENSORS,
    "Delta 2 Max": _D2M_SENSORS,
    "Delta Pro": _DPRO_SENSORS,
    "Delta Max": _DMAX_SENSORS,
    "Delta Mini": _DMINI_SENSORS,
    "River 2": _R2_SENSORS,
    "River 2 Max": _R2MAX_SENSORS,
    "River 2 Pro": _R2PRO_SENSORS,
    "River Max": _RMAX_SENSORS,
    "River Pro": _RPRO_SENSORS,
    "River Mini": _RMINI_SENSORS,
    "PowerStream": _PS_SENSORS,
    "PowerStream 600W": _PS_SENSORS,
    "PowerStream 800W": _PS_SENSORS,
    "Glacier": _GL_SENSORS,
    "Wave 2": _W2_SENSORS,
}

# ══════════════════════════════════════════════════════════════════════════════
# Smart Plug — 5 sensors (protobuf telemetry — requires decoder in on_message)
# Keys are flat (no prefix), from WnPlugHeartbeatPack
# ══════════════════════════════════════════════════════════════════════════════

_SP_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    EcoFlowSensorDescription(key=sp_dev.KEY_WATTS, name="Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=0),
    EcoFlowSensorDescription(key=sp_dev.KEY_VOLT, name="Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, scale=0.1, round_digits=1),
    EcoFlowSensorDescription(key=sp_dev.KEY_CURRENT, name="Current", native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EcoFlowSensorDescription(key=sp_dev.KEY_TEMP, name="Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
    EcoFlowSensorDescription(key=sp_dev.KEY_FREQ, name="Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, round_digits=1),
)

SENSOR_DESCRIPTIONS_BY_MODEL["Smart Plug"] = _SP_SENSORS

# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro 3 (DGEA) — sensors with flat keys (no module prefix)
# Source: EcoFlow Developer docs (deltaPro3), GetCmdResponse quota keys
# NOTE: DP3 uses flat keys unlike D361's dotted keys (pd.soc, mppt.*)
# Sensor data arrives via MQTT latestQuotas or telemetry push with flat keys.
# Additional sensors will be added when live telemetry dumps are available.
# ══════════════════════════════════════════════════════════════════════════════

_DP3_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    # Settings readback (these double as sensors to show current config values)
    EcoFlowSensorDescription(key=dp3.KEY_MAX_CHG_SOC, name="Max Charge SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-charging-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dp3.KEY_MIN_DSG_SOC, name="Min Discharge SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-charging-low", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dp3.KEY_AC_STANDBY_TIME, name="AC Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_DC_STANDBY_TIME, name="DC Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_DEV_STANDBY_TIME, name="Device Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_LCD_LIGHT, name="LCD Brightness", icon="mdi:brightness-6", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_AC_OUT_FREQ, name="AC Output Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_AC_CHG_POW_MAX, name="AC Max Charging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dp3.KEY_PV_LV_DC_AMP_MAX, name="Solar LV Max Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_PV_HV_DC_AMP_MAX, name="Solar HV Max Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_ENERGY_BACKUP_SOC, name="Energy Backup Start SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_OIL_ON_SOC, name="Generator Start SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:gas-station", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_OIL_OFF_SOC, name="Generator Stop SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:gas-station-off", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dp3.KEY_MULTI_BP_MODE, name="Multi Battery Mode", icon="mdi:battery-sync", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
)

SENSOR_DESCRIPTIONS_BY_MODEL["Delta Pro 3"] = _DP3_SENSORS

# ══════════════════════════════════════════════════════════════════════════════
# Delta Pro Ultra (DGEB) — cmdCode protocol, prefixed quota keys
# Source: EcoFlow Developer docs (deltaProUltra), 14 April 2026, 18 pages
# ══════════════════════════════════════════════════════════════════════════════

from .devices import delta_pro_ultra as dpu_s

_DPU_SENSORS: tuple[EcoFlowSensorDescription, ...] = (
    # ── Core status ──────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_SOC, name="Battery Level", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_TOTAL_IN_POWER, name="Total Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_TOTAL_OUT_POWER, name="Total Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_REMAIN_TIME, name="Remaining Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-sand", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_BP_NUM, name="Battery Pack Count", icon="mdi:battery-sync", state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── AC output power per port ─────────────────────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_TT_PWR, name="AC 30A Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_L11_PWR, name="AC Port 1 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_L12_PWR, name="AC Port 2 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_L21_PWR, name="AC Port 3 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_L22_PWR, name="AC Port 4 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_L14_PWR, name="AC Port 5 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_AC_5P8_PWR, name="POWER IN/OUT Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── DC / USB output power ────────────────────────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_ADS_PWR, name="DC Anderson Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_TYPEC1_PWR, name="Type-C 1 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_TYPEC2_PWR, name="Type-C 2 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_USB1_PWR, name="USB 1 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_USB2_PWR, name="USB 2 Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_OUT_PR_PWR, name="Parallel Box Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),

    # ── Input power ──────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_HV_MPPT_PWR, name="Solar HV Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_LV_MPPT_PWR, name="Solar LV Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_C20_PWR, name="AC C20 Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_5P8_PWR, name="POWER IN/OUT Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),

    # ── Settings sensors (read from SET namespace) ───────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_CHG_MAX_SOC, name="Max Charge SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-charging-high", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_DSG_MIN_SOC, name="Min Discharge SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-charging-low", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_AC_OUT_FREQ, name="AC Output Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_CHG_C20_SET, name="AC Charging Power Setting", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_CHG_5P8_SET, name="POWER IN/OUT Charging Setting", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_SYS_BACKUP_SOC, name="Backup Reserve SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-heart-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_SYS_WORD_MODE, name="System Operating Mode", icon="mdi:cog", state_class=SensorStateClass.MEASUREMENT, round_digits=0),
    EcoFlowSensorDescription(key=dpu_s.KEY_POWER_STANDBY, name="Device Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_AC_STANDBY, name="AC Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_DC_STANDBY, name="DC Standby Time", native_unit_of_measurement=UnitOfTime.MINUTES, icon="mdi:timer-outline", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_SCREEN_STANDBY, name="Screen Standby Time", native_unit_of_measurement=UnitOfTime.SECONDS, icon="mdi:monitor-off", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),

    # ── Status / info ────────────────────────────────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_SHOW_FLAG, name="Status Flag", icon="mdi:flag", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_SYS_ERR_CODE, name="Error Code", icon="mdi:alert-circle", state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_C20_CHG_MAX, name="Max AC C20 Charge Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_PARA_CHG_MAX, name="Max POWER IN/OUT Charge Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, round_digits=0, entity_registry_enabled_default=False),

    # ── Backend V/A sensors (detailed per-port) ──────────────────────────────
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_C20_VOL, name="AC C20 Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_C20_AMP, name="AC C20 Input Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_5P8_VOL, name="POWER IN/OUT Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_AC_5P8_AMP, name="POWER IN/OUT Input Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_LV_MPPT_VOL, name="Solar LV Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_LV_MPPT_AMP, name="Solar LV Input Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_HV_MPPT_VOL, name="Solar HV Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
    EcoFlowSensorDescription(key=dpu_s.KEY_IN_HV_MPPT_AMP, name="Solar HV Input Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, round_digits=1, entity_registry_enabled_default=False),
)

SENSOR_DESCRIPTIONS_BY_MODEL["Delta Pro Ultra"] = _DPU_SENSORS


def _get_sensor_descriptions(model: str) -> tuple[EcoFlowSensorDescription, ...]:
    """Get sensor descriptions for a device model. Falls back to empty tuple."""
    descs = SENSOR_DESCRIPTIONS_BY_MODEL.get(model)
    if descs is not None:
        return descs
    _LOGGER.warning("EcoFlow: no sensor descriptions for model '%s'", model)
    return ()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensors from a config entry."""
    entry_data  = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    sn          = entry_data["sn"]
    device_model = entry_data.get("device_model", "Delta 3 1500")

    descriptions = _get_sensor_descriptions(device_model)

    entities: list = [
        EcoFlowSensorEntity(coordinator, desc, sn, device_model)
        for desc in descriptions
    ]
    # Diagnostic sensor — always added, shows connection mode in HA UI
    entities.append(EcoFlowConnectionModeSensor(entry_data, sn, device_model))
    async_add_entities(entities)


class EcoFlowSensorEntity(CoordinatorEntity[EcoflowCoordinator], SensorEntity):
    """One sensor backed by the EcoFlow coordinator."""

    entity_description: EcoFlowSensorDescription

    def __init__(
        self,
        coordinator: EcoflowCoordinator,
        description: EcoFlowSensorDescription,
        sn: str,
        device_model: str = "Delta 3 1500",
    ) -> None:
        super().__init__(coordinator)
        self.entity_description  = description
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
            # Handle comma-decimal strings (e.g. bms_slave.diffSoc = "1,11")
            if isinstance(val, str) and "," in val:
                val = val.replace(",", ".")
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

    def __init__(self, entry_data: dict, sn: str, device_model: str = "Delta 3 1500") -> None:
        self._entry_data       = entry_data
        self._sn               = sn
        self._attr_unique_id   = f"{sn}_connection_mode"
        self._attr_name        = "Connection Mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=f"EcoFlow {device_model}",
            manufacturer=MANUFACTURER,
            model=device_model,
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
