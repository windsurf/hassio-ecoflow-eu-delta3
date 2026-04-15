"""Device definition for EcoFlow Delta Pro Ultra.

SN prefix: DGEB (confirmed via EcoFlow developer docs)

Protocol: Delta Pro Ultra uses a DIFFERENT command format than all other devices:
  - Command envelope: {sn, cmdCode:"YJ751_PD_*", params:{...}}
  - Quota keys are PREFIXED: hs_yj751_pd_appshow_addr.*, hs_yj751_pd_app_set_info_addr.*, hs_yj751_pd_backend_addr.*
  - REST SET: PUT /iot-open/sign/device/quota with cmdCode envelope (NO moduleType/operateType)
  - REST GET: POST /iot-open/sign/device/quota with {sn, params:{quotas:[...]}}
  - MQTT SET: {id, version:"1.0", cmdCode:"YJ751_PD_*", params:{...}}
  - MQTT SET Reply: {data: {result: 0}, id: 123456789}

Source: EcoFlow Developer Platform docs (developer-eu.ecoflow.com/us/document/deltaProUltra)
         PDF export 14 April 2026, 18 pages
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# Namespace prefixes — DPU uses three distinct address spaces
# ══════════════════════════════════════════════════════════════════════════════

NS_SHOW = "hs_yj751_pd_appshow_addr"       # Status / power / runtime sensors
NS_SET  = "hs_yj751_pd_app_set_info_addr"   # Configurable settings
NS_BACK = "hs_yj751_pd_backend_addr"        # Detailed V/A/PF per AC port

# ══════════════════════════════════════════════════════════════════════════════
# Quota keys — appshow_addr (status sensors, read-only)
# These are the keys returned by REST GET and MQTT telemetry push.
# Source: GetAllQuotaResponse in official developer docs
# ══════════════════════════════════════════════════════════════════════════════

# ── Power sensors ────────────────────────────────────────────────────────────
KEY_SOC              = f"{NS_SHOW}.soc"                # SOC for entire device (%)
KEY_TOTAL_IN_POWER   = f"{NS_SHOW}.wasInSum"           # Total input power (W)
KEY_TOTAL_OUT_POWER  = f"{NS_SHOW}.wasOutSum"          # Total output power (W)
KEY_REMAIN_TIME      = f"{NS_SHOW}.remainTime"         # Remaining charge/discharge time (min)
KEY_BP_NUM           = f"{NS_SHOW}.bpNum"              # Battery pack quantity

# ── AC output power per port ─────────────────────────────────────────────────
KEY_OUT_AC_TT_PWR    = f"{NS_SHOW}.outAcTtPwr"        # AC 30A output power
KEY_OUT_AC_L11_PWR   = f"{NS_SHOW}.outAcL11Pwr"       # First AC port output power
KEY_OUT_AC_L12_PWR   = f"{NS_SHOW}.outAcL12Pwr"       # Second AC port output power
KEY_OUT_AC_L21_PWR   = f"{NS_SHOW}.outAcL21Pwr"       # Third AC port output power
KEY_OUT_AC_L22_PWR   = f"{NS_SHOW}.outAcL22Pwr"       # Fourth AC port output power
KEY_OUT_AC_L14_PWR   = f"{NS_SHOW}.outAcL14Pwr"       # Last AC port output power
KEY_OUT_AC_5P8_PWR   = f"{NS_SHOW}.outAc5p8Pwr"       # POWER IN/OUT port output power

# ── DC / USB / other output power ────────────────────────────────────────────
KEY_OUT_ADS_PWR      = f"{NS_SHOW}.outAdsPwr"          # DC Anderson port output power
KEY_OUT_TYPEC1_PWR   = f"{NS_SHOW}.outTypec1Pwr"      # Type-C1 output power
KEY_OUT_TYPEC2_PWR   = f"{NS_SHOW}.outTypec2Pwr"      # Type-C2 output power
KEY_OUT_USB1_PWR     = f"{NS_SHOW}.outUsb1Pwr"        # USB1 output power
KEY_OUT_USB2_PWR     = f"{NS_SHOW}.outUsb2Pwr"        # USB2 output power
KEY_OUT_PR_PWR       = f"{NS_SHOW}.outPrPwr"           # Parallel box discharging power

# ── Input power ──────────────────────────────────────────────────────────────
KEY_IN_HV_MPPT_PWR   = f"{NS_SHOW}.inHvMpptPwr"       # High-voltage PV input power
KEY_IN_LV_MPPT_PWR   = f"{NS_SHOW}.inLvMpptPwr"       # Low-voltage PV input power
KEY_IN_AC_C20_PWR    = f"{NS_SHOW}.inAcC20Pwr"        # AC C20 input power
KEY_IN_AC_5P8_PWR    = f"{NS_SHOW}.inAc5p8Pwr"        # POWER IN/OUT port input power

# ── Port types & status ──────────────────────────────────────────────────────
KEY_ACCESS_5P8_OUT   = f"{NS_SHOW}.access5p8OutType"   # POWER IN/OUT output type
KEY_ACCESS_5P8_IN    = f"{NS_SHOW}.access5p8InType"    # POWER IN/OUT input type
KEY_SHOW_FLAG        = f"{NS_SHOW}.showFlag"           # Bit field for DC/AC/heat status
KEY_SYS_ERR_CODE     = f"{NS_SHOW}.sysErrCode"        # Device error code
KEY_FULL_COMBO       = f"{NS_SHOW}.fullCombo"          # Overall data transfer plan

# ── 4G status ────────────────────────────────────────────────────────────────
KEY_4G_ON            = f"{NS_SHOW}.wireless4gOn"       # 4G switch (1=on, 0=off)
KEY_4G_CON           = f"{NS_SHOW}.wireless4gCon"      # 4G PDP status (-1/0/1)
KEY_4G_STA           = f"{NS_SHOW}.wireless4GSta"      # Network card: 0=WiFi, 1=4G, 2=WLAN
KEY_4G_ERR           = f"{NS_SHOW}.wirlesss4gErrCode"  # 4G error code (note: typo in EF docs)
KEY_SIM_ICCID        = f"{NS_SHOW}.simIccid"           # SIM ICCID

# ── Charging limits (from appshow) ───────────────────────────────────────────
KEY_C20_CHG_MAX      = f"{NS_SHOW}.c20ChgMaxWas"      # Max AC C20 charging power
KEY_PARA_CHG_MAX     = f"{NS_SHOW}.paraChgMaxWas"      # Max POWER IN/OUT charging power
KEY_REMAIN_COMBO     = f"{NS_SHOW}.remainCombo"        # Remaining data transfer plan

# ── Scheduled tasks ──────────────────────────────────────────────────────────
KEY_CHG_TASK_TYPE    = f"{NS_SHOW}.chgTimeTaskType"    # Scheduled charge task type
KEY_CHG_TASK_MODE    = f"{NS_SHOW}.chgTimeTaskMode"    # Charge task mode (0=daily, 1=weekly, etc.)
KEY_CHG_TASK_PARAM   = f"{NS_SHOW}.chgTimeTaskParam"   # Charge task param
KEY_CHG_TASK_TABLE0  = f"{NS_SHOW}.chgTimeTaskTable0"  # Charge task period 1
KEY_CHG_TASK_TABLE1  = f"{NS_SHOW}.chgTimeTaskTable1"  # Charge task period 2
KEY_CHG_TASK_TABLE2  = f"{NS_SHOW}.chgTimeTaskTable2"  # Charge task period 3
KEY_DSG_TASK_TYPE    = f"{NS_SHOW}.dsgTimeTaskType"    # Scheduled discharge task type
KEY_DSG_TASK_MODE    = f"{NS_SHOW}.dsgTimeTaskMode"    # Discharge task mode
KEY_DSG_TASK_NOTICE  = f"{NS_SHOW}.dsgTimeTaskNotice"  # Show scheduled tasks? (0/1)
KEY_DSG_TASK_TABLE0  = f"{NS_SHOW}.dsgTimeTaskTable0"  # Discharge task period 1
KEY_DSG_TASK_TABLE1  = f"{NS_SHOW}.dsgTimeTaskTable1"  # Discharge task period 2
KEY_DSG_TASK_TABLE2  = f"{NS_SHOW}.dsgTimeTaskTable2"  # Discharge task period 3

# ══════════════════════════════════════════════════════════════════════════════
# Quota keys — app_set_info_addr (configurable settings)
# ══════════════════════════════════════════════════════════════════════════════

KEY_POWER_STANDBY    = f"{NS_SET}.powerStandbyMins"    # Device standby time (min)
KEY_SCREEN_STANDBY   = f"{NS_SET}.screenStandbySec"    # Screen standby time (sec)
KEY_AC_STANDBY       = f"{NS_SET}.acStandbyMins"       # AC standby time (min)
KEY_DC_STANDBY       = f"{NS_SET}.dcStandbyMins"       # DC standby time (min)
KEY_CHG_MAX_SOC      = f"{NS_SET}.chgMaxSoc"           # Upper limit SOC for charging
KEY_DSG_MIN_SOC      = f"{NS_SET}.dsgMinSoc"           # Lower limit SOC for discharging
KEY_AC_XBOOST        = f"{NS_SET}.acXboost"            # X-Boost setting
KEY_AC_OUT_FREQ      = f"{NS_SET}.acOutFreq"           # AC output frequency (0/50/60)
KEY_AC_OFTEN_OPEN    = f"{NS_SET}.acOftenOpenFlg"      # AC Always-On flag
KEY_AC_OFTEN_MIN_SOC = f"{NS_SET}.acOftenOpenMinSoc"   # Min SOC for AC Always-On
KEY_CHG_C20_SET      = f"{NS_SET}.chgC20SetWas"        # AC C20 charging power setting
KEY_CHG_5P8_SET      = f"{NS_SET}.chg5p8SetWas"        # POWER IN/OUT charging power setting
KEY_SYS_WORD_MODE    = f"{NS_SET}.sysWordMode"         # System operating mode (0-3)
KEY_SYS_TIMEZONE     = f"{NS_SET}.sysTimezone"         # System timezone (integer)
KEY_SYS_TIMEZONE_ID  = f"{NS_SET}.sysTimezoneId"       # System timezone ID (string)
KEY_TZ_SET_TYPE      = f"{NS_SET}.timezoneSeype"       # Timezone set type (0=manual, 1=auto)
KEY_SYS_BACKUP_SOC   = f"{NS_SET}.sysBackupSoc"        # System backup power SOC
KEY_BACKUP_RATIO     = f"{NS_SET}.backupRatio"          # Backup reserve level
KEY_BMS_MODE_SET     = f"{NS_SET}.bmsModeSet"          # Battery auto-heating (0=off, 1=on)
KEY_ENERGY_MANAGE_EN = f"{NS_SET}.energyMamageEnable"  # Energy management switch (note: typo in EF docs)

# ══════════════════════════════════════════════════════════════════════════════
# Quota keys — backend_addr (detailed V/A/PF per AC port)
# ══════════════════════════════════════════════════════════════════════════════

# ── AC output V/A/PF per port ────────────────────────────────────────────────
KEY_OUT_AC_L12_AMP   = f"{NS_BACK}.outAcL12Amp"       # AC_L1_2 output current
KEY_OUT_AC_L21_VOL   = f"{NS_BACK}.outAcL21Vol"       # AC_L2_1 output voltage
KEY_OUT_AC_L21_AMP   = f"{NS_BACK}.outAcL21Amp"       # AC_L2_1 output current
KEY_OUT_AC_L22_VOL   = f"{NS_BACK}.outAcL22Vol"       # AC_L2_2 output voltage
KEY_OUT_AC_L22_AMP   = f"{NS_BACK}.outAcL22Amp"       # AC_L2_2 output current
KEY_OUT_AC_TT_VOL    = f"{NS_BACK}.outAcTtVol"        # AC_TT output voltage
KEY_OUT_AC_TT_AMP    = f"{NS_BACK}.outAcTtAmp"        # AC_TT output current
KEY_OUT_AC_L14_VOL   = f"{NS_BACK}.outAcL14Vol"       # AC_L14 output voltage
KEY_OUT_AC_L14_AMP   = f"{NS_BACK}.outAcL14Amp"       # AC_L14 output current
KEY_OUT_AC_5P8_VOL   = f"{NS_BACK}.outAc5p8Vol"       # AC POWER IN/OUT output voltage
KEY_OUT_AC_5P8_AMP   = f"{NS_BACK}.outAc5p8Amp"       # AC POWER IN/OUT output current

# ── AC input V/A ─────────────────────────────────────────────────────────────
KEY_IN_AC_5P8_VOL    = f"{NS_BACK}.inAc5p8Vol"        # AC POWER IN/OUT input voltage
KEY_IN_AC_5P8_AMP    = f"{NS_BACK}.inAc5p8Amp"        # AC POWER IN/OUT input current
KEY_IN_AC_C20_VOL    = f"{NS_BACK}.inAcC20Vol"        # AC C20 input voltage
KEY_IN_AC_C20_AMP    = f"{NS_BACK}.inAcC20Amp"        # AC C20 input current

# ── Solar input V/A ──────────────────────────────────────────────────────────
KEY_IN_LV_MPPT_VOL   = f"{NS_BACK}.inLvMpptVol"       # LV solar input voltage
KEY_IN_LV_MPPT_AMP   = f"{NS_BACK}.inLvMpptAmp"       # LV solar input current
KEY_IN_HV_MPPT_VOL   = f"{NS_BACK}.inHvMpptVol"       # HV solar input voltage
KEY_IN_HV_MPPT_AMP   = f"{NS_BACK}.inHvMpptAmp"       # HV solar input current

# ── Output frequency per port ────────────────────────────────────────────────
KEY_OUT_AC_L11_PF    = f"{NS_BACK}.outAcL11Pf"        # AC_L1_1 output frequency
KEY_OUT_AC_L12_PF    = f"{NS_BACK}.outAcL12Pf"        # AC_L1_2 output frequency
KEY_OUT_AC_L21_PF    = f"{NS_BACK}.outAcL21Pf"        # AC_L2_1 output frequency
KEY_OUT_AC_L22_PF    = f"{NS_BACK}.outAcL22Pf"        # AC_L2_2 output frequency
KEY_OUT_AC_TT_PF     = f"{NS_BACK}.outAcTtPf"         # AC_TT output frequency
KEY_OUT_AC_L14_PF    = f"{NS_BACK}.outAcL14Pf"        # AC_L14 output frequency
KEY_OUT_AC_P58_PF    = f"{NS_BACK}.outAcP58Pf"        # AC POWER IN/OUT output frequency


# ══════════════════════════════════════════════════════════════════════════════
# SET command codes — cmdCode based protocol (unique to DPU)
# Used in both REST PUT and MQTT SET
# ══════════════════════════════════════════════════════════════════════════════

CMD_BP_HEAT          = "YJ751_PD_BP_HEAT_SET"          # Battery heating (enBpHeat: 0/1)
CMD_DC_SWITCH        = "YJ751_PD_DC_SWITCH_SET"        # DC output (enable: 0/1)
CMD_POWER_STANDBY    = "YJ751_PD_POWER_STANDBY_SET"    # Device standby (powerStandbyMin: min)
CMD_SCREEN_STANDBY   = "YJ751_PD_SCREEN_STANDBY_SET"   # Screen standby (screenStandbySec: sec)
CMD_AC_STANDBY       = "YJ751_PD_AC_STANDBY_SET"       # AC standby (acStandbyMin: min)
CMD_DC_STANDBY       = "YJ751_PD_DC_STANDBY_SET"       # DC standby (dcStandbyMin: min)
CMD_CHG_SOC_MAX      = "YJ751_PD_CHG_SOC_MAX_SET"      # Max charge SOC (maxChgSoc: %)
CMD_DSG_SOC_MIN      = "YJ751_PD_DSG_SOC_MIN_SET"      # Min discharge SOC (minDsgSoc: %)
CMD_4G_SWITCH        = "YJ751_PD_4G_SWITCH_SET"        # 4G switch (en4GOpen: 0/1)
CMD_AC_OFTEN_OPEN    = "YJ751_PD_AC_OFTEN_OPEN_SET"    # AC Always-On (acOftenOpen: 0/1)
CMD_AC_DSG           = "YJ751_PD_AC_DSG_SET"           # AC output + X-Boost + freq
CMD_AC_CHG           = "YJ751_PD_AC_CHG_SET"           # AC charging power

# ══════════════════════════════════════════════════════════════════════════════
# SET command parameter names — used in the params dict of SET commands
# ══════════════════════════════════════════════════════════════════════════════

PARAM_BP_HEAT        = "enBpHeat"                       # 0=off, 1=on
PARAM_DC_ENABLE      = "enable"                         # 0=off, 1=on
PARAM_POWER_STANDBY  = "powerStandbyMin"                # 0=never, else minutes
PARAM_SCREEN_STANDBY = "screenStandbySec"               # 0=never, else seconds
PARAM_AC_STANDBY     = "acStandbyMin"                   # 0=always on, else minutes
PARAM_DC_STANDBY     = "dcStandbyMin"                   # 0=always on, else minutes
PARAM_MAX_CHG_SOC    = "maxChgSoc"                      # 50-100%
PARAM_MIN_DSG_SOC    = "minDsgSoc"                      # 0-30%
PARAM_4G_OPEN        = "en4GOpen"                       # 0=off, 1=on
PARAM_AC_OFTEN_OPEN  = "acOftenOpen"                    # 0=off, 1=on
PARAM_AC_ENABLE      = "enable"                         # AC output: 0=off, 1=on
PARAM_AC_XBOOST      = "xboost"                         # X-Boost: 0=off, 1=on
PARAM_AC_OUT_FREQ    = "outFreq"                        # 50 or 60 Hz
PARAM_CHG_C20_WATTS  = "chgC20Watts"                    # AC C20 charging power (W)
PARAM_CHG_5P8_WATTS  = "chg5p8Watts"                    # POWER IN/OUT charging power (W)

# ══════════════════════════════════════════════════════════════════════════════
# showFlag bit field — extract individual switch states from decimal value
# Convert to binary, read bit positions right-to-left:
#   bit 1 (2nd): battery heating (0=enabled, 1=prohibited)
#   bit 2 (3rd): AC output enabled
#   bit 5 (6th): DC output enabled
# ══════════════════════════════════════════════════════════════════════════════

def extract_show_flag_bit(show_flag: int, bit_position: int) -> int:
    """Extract a single bit from the showFlag field.

    Args:
        show_flag: decimal value of showFlag
        bit_position: 0-indexed bit position (right-to-left)

    Returns:
        0 or 1
    """
    return (show_flag >> bit_position) & 1


DEVICE_MODEL = "Delta Pro Ultra"
