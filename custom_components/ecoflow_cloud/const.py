"""Constants for EcoFlow Cloud integration."""

DOMAIN              = "ecoflow_cloud"
INTEGRATION_VERSION = "0.2.20"

# Config entry keys
CONF_ACCESS_KEY = "access_key"
CONF_SECRET_KEY = "secret_key"
CONF_DEVICE_SN  = "device_sn"
CONF_API_HOST   = "api_host"
CONF_AUTH_MODE  = "auth_mode"
CONF_EMAIL      = "email"
CONF_PASSWORD   = "password"

# Auth modes
AUTH_MODE_PUBLIC  = "public"   # Open API: Access Key + Secret Key
AUTH_MODE_PRIVATE = "private"  # App login: Email + Password (works for Delta 3)
AUTH_MODE_AUTO    = "auto"     # Auto-detect based on serial number prefix

# EcoFlow Open API endpoints
API_HOST_EU      = "https://api-e.ecoflow.com"
API_HOST_US      = "https://api-a.ecoflow.com"
API_HOST_GLOBAL  = "https://api.ecoflow.com"
API_HOST_DEFAULT = API_HOST_EU

API_PATH_QUOTA       = "/iot-open/sign/device/quota/all"
API_PATH_MQTT        = "/iot-open/sign/certification"
API_PATH_DEVICE_LIST = "/iot-open/sign/device/list"

# MQTT
MQTT_KEEPALIVE          = 120
MQTT_RECONNECT_INTERVAL = 60

# Coordinator polling interval
COORDINATOR_UPDATE_INTERVAL = 30  # seconds

# Device info
MANUFACTURER = "EcoFlow"

# Serial number prefixes that require App Login (private API).
# These devices return error 1006 on the Open API quota endpoint.
# Sources:
#   - https://github.com/tolwi/hassio-ecoflow-cloud
#   - https://github.com/snell-evan-itt/hassio-ecoflow-cloud-US
#   - Community reports / reverse engineering
PRIVATE_API_SN_PREFIXES = (
    "D361",   # Delta 3 / Delta 3 1500
    "D362",   # Delta 3 Plus
    "D381",   # Delta 3 Max (tentative)
    "R641",   # River 3
    "R651",   # River 3 Plus (tentative)
    "BKW",    # PowerStream micro-inverter
    "HW51",   # PowerStream 600W
    "HW52",   # PowerStream 800W
    "DGEB",   # Delta Pro Ultra
    "DGEA",   # Delta Pro 3
)
