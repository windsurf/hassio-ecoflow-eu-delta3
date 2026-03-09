#!/usr/bin/env python3
"""
EcoFlow API Credential Diagnostic Tool
=======================================
Tests all three EcoFlow API servers with your credentials and shows:
  - Which server works for authentication
  - Which devices are linked to your API key
  - Whether your device serial number is found

Usage (from HA Terminal add-on or any PC with Python):
    pip install requests
    python3 test_credentials.py

Fill in your credentials below before running.
"""

import hashlib
import hmac
import json
import random
import time

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package not found. Run: pip install requests")
    exit(1)

# ── Fill in your credentials ───────────────────────────────────────────────
ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"
SECRET_KEY = "YOUR_SECRET_KEY_HERE"
DEVICE_SN  = "YOUR_SERIAL_NUMBER_HERE"
# ──────────────────────────────────────────────────────────────────────────

SERVERS = {
    "EU     (api-e.ecoflow.com)": "https://api-e.ecoflow.com",
    "US     (api-a.ecoflow.com)": "https://api-a.ecoflow.com",
    "Global (api.ecoflow.com)  ": "https://api.ecoflow.com",
}


def _headers(params: dict, ak: str, sk: str) -> dict:
    nc  = str(random.randint(100_000, 999_999))
    ts  = str(int(time.time() * 1000))
    ps  = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    msg = f"{ps}&accessKey={ak}&nonce={nc}&timestamp={ts}" if ps \
          else f"accessKey={ak}&nonce={nc}&timestamp={ts}"
    sig = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return {"accessKey": ak, "nonce": nc, "timestamp": ts, "sign": sig}


def test_server(label: str, host: str) -> bool:
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"URL    : {host}")

    # Step 1: authentication
    try:
        h    = _headers({}, ACCESS_KEY, SECRET_KEY)
        resp = requests.get(f"{host}/iot-open/sign/certification",
                            headers=h, timeout=10)
        body = resp.json()
    except Exception as e:
        print(f"Auth   : ❌ {e}")
        return False

    if str(body.get("code")) != "0":
        print(f"Auth   : ❌ {body.get('code')}: {body.get('message')}")
        return False

    print(f"Auth   : ✅ OK")

    # Step 2: device list
    try:
        h    = _headers({}, ACCESS_KEY, SECRET_KEY)
        resp = requests.get(f"{host}/iot-open/sign/device/list",
                            headers=h, timeout=10)
        body = resp.json()
    except Exception as e:
        print(f"Devices: ❌ {e}")
        return True  # auth worked even if device list fails

    if str(body.get("code")) != "0":
        print(f"Devices: ❌ {body.get('code')}: {body.get('message')}")
        return True

    devices = body.get("data", [])
    if isinstance(devices, dict):
        devices = devices.get("list", [])

    if not devices:
        print(f"Devices: ⚠️  No devices found on this account")
        return True

    print(f"Devices: ✅ {len(devices)} device(s) found:")
    for d in devices:
        sn   = d.get("sn", "?")
        name = d.get("deviceName") or d.get("productName") or "Unknown"
        mark = " ← YOUR DEVICE" if sn == DEVICE_SN else ""
        print(f"           {name} | SN: {sn}{mark}")

    sns = [d.get("sn") for d in devices]
    if DEVICE_SN not in sns:
        print(f"\n⚠️  Serial '{DEVICE_SN}' NOT found on this account!")
        print(f"   Check for typos. Found SNs: {', '.join(sns)}")

    return True


if __name__ == "__main__":
    if "YOUR_" in ACCESS_KEY:
        print("ERROR: Fill in ACCESS_KEY, SECRET_KEY and DEVICE_SN at the top of this file!")
        exit(1)

    print("EcoFlow API Credential Diagnostic Tool")
    print(f"Access Key : {ACCESS_KEY[:6]}...{ACCESS_KEY[-4:]}")
    print(f"Device SN  : {DEVICE_SN}")

    working = []
    for label, host in SERVERS.items():
        ok = test_server(label, host)
        if ok:
            working.append(host)

    print(f"\n{'='*60}")
    print("SUMMARY")
    if working:
        print(f"✅ Working server(s): {', '.join(working)}")
        print(f"   Use the first one in the HA integration setup.")
    else:
        print("❌ No server worked. Check your credentials.")
