"""EcoFlow API clients.

Two authentication modes:

  1. PUBLIC API (Open API)
     - Credentials: Access Key + Secret Key from developer-eu.ecoflow.com
     - MQTT host:   mqtt-e.ecoflow.com
     - MQTT topic:  /open/{certificateAccount}/{sn}/quota
     - Limitation:  Delta 3 (D361) returns 1006 on /quota/all

  2. PRIVATE API (App credentials)  ← works for ALL devices incl. Delta 3
     - Credentials: EcoFlow app email + password (plaintext)
     - Login:       POST https://api.ecoflow.com/auth/login
     - MQTT creds:  GET  https://api.ecoflow.com/iot-auth/app/certification
     - MQTT host:   mqtt.ecoflow.com
     - MQTT topics:
         subscribe: /app/device/property/{sn}
         set:       /app/{userId}/{sn}/thing/property/set
         get:       /app/{userId}/{sn}/thing/property/get
     - ClientID:    ANDROID_{uuid}_{userId_hex}  (must be 32 chars, end with userId hex)
"""
from __future__ import annotations

import hmac
import logging
import random
import time
from typing import Any

import requests

from .const import API_HOST_DEFAULT

_LOGGER = logging.getLogger(__name__)

# ── Public API paths ──────────────────────────────────────────────────────
PATH_MQTT        = "/iot-open/sign/certification"
PATH_QUOTA       = "/iot-open/sign/device/quota/all"
PATH_DEVICE_LIST = "/iot-open/sign/device/list"

# ── Private API URLs ──────────────────────────────────────────────────────
PRIVATE_LOGIN_URL = "https://api.ecoflow.com/auth/login"
PRIVATE_CERT_URL  = "https://api.ecoflow.com/iot-auth/app/certification"


def _nonce() -> str:
    return str(random.randint(100_000, 999_999))

def _ts() -> str:
    return str(int(time.time() * 1000))

def _make_headers(sign_params: dict, ak: str, sk: str) -> dict[str, str]:
    nc   = _nonce()
    ts   = _ts()
    ps   = "&".join(f"{k}={v}" for k, v in sorted(sign_params.items()))
    auth = f"accessKey={ak}&nonce={nc}&timestamp={ts}"
    msg  = f"{ps}&{auth}" if ps else auth
    sig  = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    _LOGGER.debug("sign_msg: %s", msg)
    return {"accessKey": ak, "timestamp": ts, "nonce": nc, "sign": sig,
            "Content-Type": "application/json"}


class EcoFlowAPIError(Exception):
    pass


# ── Public API client ─────────────────────────────────────────────────────

class EcoFlowAPI:
    """REST client for the EcoFlow Open (developer) API."""

    def __init__(self, access_key: str, secret_key: str,
                 device_sn: str, api_host: str = API_HOST_DEFAULT) -> None:
        self._ak   = access_key.strip()
        self._sk   = secret_key.strip()
        self._sn   = device_sn.strip()
        self._host = api_host.rstrip("/")
        self._s    = requests.Session()
        self._s.headers.update({"User-Agent": "HomeAssistant/EcoFlowCloud"})

    def _get(self, path: str, sign_params: dict,
             url_params: dict | None = None) -> dict:
        url  = f"{self._host}{path}"
        hdrs = _make_headers(sign_params, self._ak, self._sk)
        qp   = url_params if url_params is not None else sign_params
        try:
            r    = self._s.get(url, headers=hdrs, params=qp, timeout=15)
            r.raise_for_status()
            body = r.json()
        except requests.RequestException as e:
            raise EcoFlowAPIError(f"Request failed: {e}") from e
        _LOGGER.debug("Response %s: %s", path, str(body)[:300])
        if str(body.get("code")) != "0":
            raise EcoFlowAPIError(
                f"API error {body.get('code')}: {body.get('message', 'unknown')}")
        return body.get("data") or {}

    def get_mqtt_credentials(self) -> dict[str, Any]:
        return self._get(PATH_MQTT, sign_params={})

    def get_device_list(self) -> list[dict]:
        data = self._get(PATH_DEVICE_LIST, sign_params={})
        if isinstance(data, list):
            return data
        return data.get("list", [])

    def get_all_quota(self) -> dict[str, Any]:
        """Returns empty dict on 1006/8521 — not fatal, MQTT is primary."""
        try:
            raw = self._get(PATH_QUOTA, sign_params={},
                            url_params={"sn": self._sn})
            return self._normalise(raw)
        except EcoFlowAPIError as e:
            if "1006" in str(e) or "8521" in str(e):
                _LOGGER.warning(
                    "Quota REST failed for %s (%s) — will rely on MQTT push", self._sn, e)
                self.rest_quota_unavailable = True
                return {}
            raise

    @property
    def rest_quota_unavailable(self) -> bool:
        return getattr(self, "_rest_quota_unavailable", False)

    @rest_quota_unavailable.setter
    def rest_quota_unavailable(self, value: bool) -> None:
        self._rest_quota_unavailable = value

    @staticmethod
    def _normalise(raw: dict) -> dict[str, Any]:
        return {k: (v["value"] if isinstance(v, dict) and "value" in v else v)
                for k, v in raw.items()}


# ── Private API client ────────────────────────────────────────────────────

class EcoFlowPrivateAPI:
    """
    Authenticates with EcoFlow app email + password.
    Works for ALL EcoFlow devices including Delta 3 (D361 series).

    Login:        POST https://api.ecoflow.com/auth/login
                  Body: {email, password (plaintext), scene, userType,
                         appVersion, os, osVersion}
    MQTT creds:   GET  https://api.ecoflow.com/iot-auth/app/certification
                  Header: Authorization: Bearer {token}
    MQTT topic:   /app/device/property/{sn}           (subscribe)
                  /app/{userId}/{sn}/thing/property/set (set commands)
    ClientID:     ANDROID_{random_hex}_{userId_hex}, exactly 32 chars
    """

    def __init__(self, email: str, password: str, device_sn: str) -> None:
        self._email   = email.strip()
        self._passwd  = password.strip()
        self._sn      = device_sn.strip()
        self._token   = ""
        self._user_id = ""
        self._s       = requests.Session()
        # Android app headers (okhttp/3.14.9) — do NOT set Host manually,
        # requests handles that correctly per-request.
        self._s.headers.update({
            "Content-Type": "application/json",
            "lang":         "en-us",
            "platform":     "android",
            "sysversion":   "11",
            "version":      "4.1.2.02",
            "phonemodel":   "SM-G998B",
            "User-Agent":   "okhttp/3.14.9",
        })

    def _login(self) -> dict:
        """
        POST to /auth/login.

        EcoFlow API requires the password as Base64-encoded string.
          code=1005 = "Incorrect format of password" -> wrong encoding sent
          code=2026 = "Account doesn't exist or incorrect password" -> wrong base64/credentials
          code=0    = success

        Source: mmiller7/ecoflow-withoutflow script uses:
          passvar_encoded=`echo -n $passvar | base64`
        which is standard Base64 (no line breaks, UTF-8 input).
        """
        import base64
        b64_password = base64.b64encode(self._passwd.encode("utf-8")).decode("utf-8")
        _LOGGER.warning(
            "EcoFlow login: email=%s pw_b64_prefix=%s…", self._email, b64_password[:8]
        )
        try:
            resp = self._s.post(PRIVATE_LOGIN_URL, json={
                "email":      self._email,
                "password":   b64_password,
                "scene":      "IOT_APP",
                "userType":   "ECOFLOW",
                "appVersion": "4.1.2.02",
                "os":         "android",
                "osVersion":  "30",
            }, timeout=15)
            body = resp.json()
        except requests.RequestException as e:
            raise EcoFlowAPIError(f"Login request failed: {e}") from e

        code = str(body.get("code", ""))
        msg  = body.get("message", "unknown error")
        _LOGGER.warning(
            "EcoFlow login response: HTTP=%s code=%s msg=%s",
            resp.status_code, code, msg
        )

        if code != "0":
            raise EcoFlowAPIError(f"Login failed: {msg}")

        data = body.get("data", {})
        user = data.get("user", data)
        self._token   = data.get("token", "")
        self._user_id = str(user.get("userId", user.get("id", "")))
        _LOGGER.warning(
            "EcoFlow login SUCCESS: userId=%s token=%s…",
            self._user_id, self._token[:12]
        )
        return data

    def _make_client_id(self) -> str:
        """
        ClientID format observed from STROMDAO tool:
          ANDROID_520200810_1584935350613467137
          = ANDROID_{8-char random hex/digits}_{userId as decimal string}

        The userId is appended as a plain decimal number (not hex-encoded).
        """
        import time as _time
        # 8-char timestamp-based prefix (matches observed pattern like "520200810")
        random_part = str(int(_time.time()))[-8:]
        return f"ANDROID_{random_part}_{self._user_id}"

    def get_mqtt_credentials(self) -> dict[str, Any]:
        """
        Login then fetch MQTT credentials from /iot-auth/app/certification.
        Returns dict compatible with Open API /certification response shape.
        """
        self._login()

        _LOGGER.warning(
            "EcoFlow cert request: userId=%s token=%s…", self._user_id, self._token[:12]
        )
        try:
            resp = self._s.get(
                PRIVATE_CERT_URL,
                params={"userId": self._user_id},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15,
            )
            body = resp.json()
        except requests.RequestException as e:
            raise EcoFlowAPIError(f"MQTT cert request failed: {e}") from e

        _LOGGER.warning("EcoFlow cert response: HTTP=%s code=%s data=%s",
                        resp.status_code, body.get("code"), body.get("data"))

        if str(body.get("code")) != "0":
            raise EcoFlowAPIError(
                f"MQTT cert failed: {body.get('message', 'unknown')}")

        cert = body.get("data", {})
        client_id = self._make_client_id()
        _LOGGER.warning(
            "EcoFlow MQTT creds: host=%s user=%s clientId=%s",
            cert.get("url"), cert.get("certificateAccount"), client_id
        )
        return {
            "certificateAccount":  cert.get("certificateAccount", ""),
            "certificatePassword": cert.get("certificatePassword", ""),
            "url":      cert.get("url", "mqtt-e.ecoflow.com"),
            "port":     cert.get("port", "8883"),
            "protocol": cert.get("protocol", "mqtts"),
            # Extra fields used by __init__.py for topic/clientid construction
            "_private_api": True,
            "_user_id":     self._user_id,
            "_client_id":   client_id,
        }

    def get_device_list(self) -> list[dict]:
        """Fetch device list using app Bearer token (private API endpoint)."""
        if not self._token:
            self._login()
        try:
            r = self._s.get(
                "https://api.ecoflow.com/iot-open/sign/device/list",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15,
            )
            body = r.json()
            _LOGGER.warning("Private device list response: code=%s data=%s",
                            body.get("code"), str(body.get("data", ""))[:200])
            data = body.get("data", [])
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("list", data.get("devices", []))
            return []
        except Exception as e:
            _LOGGER.warning("Private API device list failed: %s", e)
            return []

    def get_all_quota(self) -> dict[str, Any]:
        """Private API does not support REST quota — MQTT push only."""
        return {}

    @property
    def rest_quota_unavailable(self) -> bool:
        """Private API never has REST quota — always True."""
        return True
