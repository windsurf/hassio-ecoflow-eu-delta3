# Contributing

Thank you for your interest in contributing!

## Adding a new device

1. Create `custom_components/ecoflow_cloud/devices/your_device.py`
   modelled after `delta3_1500.py` — define all KEY_ constants and device limits.
2. Register the device in `devices/__init__.py`.
3. Add the serial number prefix to `PRIVATE_API_SN_PREFIXES` in `const.py` if it requires App Login.
4. Test with a real device and share MQTT key dumps in an Issue.

## Reporting MQTT keys

Enable debug logging, reproduce the issue, then share the log lines containing
`MQTT data received` — these list all keys the device sends.

```yaml
logger:
  logs:
    custom_components.ecoflow_cloud: debug
```

## Pull Requests

- One feature/fix per PR
- Keep Python compatible with HA's bundled Python version (3.12+)
- Run `python3 -m py_compile` on changed files before submitting
