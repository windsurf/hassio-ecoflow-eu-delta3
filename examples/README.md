# Examples

## Diagnostic Tools

Two diagnostic scripts to verify your EcoFlow API credentials. Available in Python and PowerShell.

### test_credentials (.py / .ps1)

Tests your **Developer API** credentials (Access Key + Secret Key) against all three EcoFlow API servers (EU, US, Global). Shows which server works and lists devices on your account.

```
# Python
pip install requests
python3 test_credentials.py

# PowerShell
PowerShell -ExecutionPolicy Bypass -File test_credentials.ps1
```

### test_developer_api (.py / .ps1)

Extended credential test that validates **HMAC signing** for GET and PUT requests. Tests device list, MQTT certification, quota GET, and REST SET signing. Also tests MQTT JSON SET for D361 devices. Use this to confirm credentials and connectivity.

```
# Python
pip install requests
python3 test_developer_api.py

# PowerShell
PowerShell -ExecutionPolicy Bypass -File test_developer_api.ps1
```

**Prerequisites:** Register at [EcoFlow Developer Portal](https://developer-eu.ecoflow.com/) and create an Access Key + Secret Key pair.

## Dashboard

### dashboard_ecoflow_v1.0.yaml

A complete Home Assistant dashboard for the EcoFlow Delta 3 1500, covering all integration entities:

- Battery status & health
- AC input / output
- Solar input
- DC outputs (12V, 24V, car port)
- USB outputs (USB-A, USB-A QC, USB-C, wireless)
- Settings & controls
- Battery detail (BMS)
- Lifetime statistics

**How to use:**

1. In Home Assistant, go to **Settings > Dashboards**
2. Click **Add Dashboard** and give it a name (e.g. `EcoFlow`)
3. Open the new dashboard, click the three dots menu, then **Raw configuration editor**
4. Paste the contents of `dashboard_ecoflow_v1.0.yaml`
5. Save

> **Note:** The dashboard uses entity IDs for a device named `EcoFlow Delta 3 1500`. If your device has a different name, adjust the entity IDs accordingly.

## Automation

### ecoflow_optimal_charging_v1.3.yaml

A Home Assistant automation that optimizes EcoFlow charging based on solar surplus. Uses P1 meter data and Solcast forecasting to control charge speed.
