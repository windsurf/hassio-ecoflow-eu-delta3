"""EcoFlow API clients.

Three authentication / control modes:

  1. PUBLIC API (Open API) — read + write via Developer API
     - Credentials: Access Key + Secret Key from developer-eu.ecoflow.com
     - Read:  GET /iot-open/sign/device/quota/all (fails with 1006 on Delta 3)
     - Write: PUT /iot-open/sign/device/quota (confirmed working for Delta 3)
     - MQTT:  /open/{certificateAccount}/{sn}/quota

  2. PRIVATE API (App credentials) — read via MQTT, no REST write
     - Credentials: EcoFlow app email + password
     - Read:  MQTT push /app/device/property/{sn} (works for ALL devices)
     - Write: MQTT /set topic (Delta 3 ignores JSON, needs protobuf)
     - ClientID: ANDROID_{uuid}_{userId_hex}

  3. HYBRID MODE (recommended for Delta 3) — MQTT read + REST write
     - MQTT telemetry via Private API (email + password)
     - SET commands via Developer API (Access Key + Secret Key)
     - Best of both worlds: real-time data + reliable control

HMAC signing spec (confirmed 19 March 2026):
  GET:  HMAC-SHA256("accessKey=...&nonce=...&timestamp=...", secretKey)
  PUT:  HMAC-SHA256("flat_body_sorted&accessKey=...&nonce=...&timestamp=...", secretKey)
        Nested params flattened with dot notation (params.enabled=0).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import random
import time
from typing import Any

import requests

from .const import API_HOST_DEFAULT

_LOGGER = logging.getLogger(__name__)

# ── Developer API paths ──────────────────────────────────────────────────
PATH_MQTT        = "/iot-open/sign/certification"
PATH_QUOTA       = "/iot-open/sign/device/quota/all"
PATH_QUOTA_SET   = "/iot-open/sign/device/quota"
PATH_DEVICE_LIST = "/iot-open/sign/device/list"

# ── Private API URLs ──────────────────────────────────────────────────────
PRIVATE_LOGIN_URL = "https://api.ecoflow.com/auth/login"
PRIVATE_CERT_URL  = "https://api.ecoflow.com/iot-auth/app/certification"


def _nonce() -> str:
    return str(random.randint(100_000, 999_999))

def _ts() -> str:
    return str(int(time.time() * 1000))

def _flatten(obj: dict, prefix: str = "") -> dict[str, str]:
    """Recursively flatten nested dict with dot notation for signing.

    Example: {"sn": "X", "params": {"enabled": 0}}
          -> {"sn": "X", "params.enabled": "0"}
    """
    result: dict[str, str] = {}
    for k, v in obj.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(_flatten(v, full_key))
        else:
            result[full_key] = str(v)
    return result

def _sign_get(ak: str, sk: str) -> dict[str, str]:
    """Build signed headers for GET requests.

    GET signing: HMAC-SHA256("accessKey=...&nonce=...&timestamp=...", secretKey)
    Request params (sn, etc.) are NOT part of the signature.
    """
    nc  = _nonce()
    ts  = _ts()
    msg = f"accessKey={ak}&nonce={nc}&timestamp={ts}"
    sig = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return {"accessKey": ak, "timestamp": ts, "nonce": nc, "sign": sig,
            "Content-Type": "application/json"}

def _sign_put(body: dict, ak: str, sk: str) -> dict[str, str]:
    """Build signed headers for PUT requests.

    PUT signing:
      1. Flatten body params with dot notation (params.enabled=0)
      2. Sort flattened params by key (ASCII order)
      3. Append accessKey=...&nonce=...&timestamp=...
      4. HMAC-SHA256 the entire string
    """
    nc   = _nonce()
    ts   = _ts()
    flat = _flatten(body)
    ps   = "&".join(f"{k}={v}" for k, v in sorted(flat.items()))
    auth = f"accessKey={ak}&nonce={nc}&timestamp={ts}"
    msg  = f"{ps}&{auth}" if ps else auth
    sig  = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    _LOGGER.debug("sign_put input: %s", msg[:120])
    return {"accessKey": ak, "timestamp": ts, "nonce": nc, "sign": sig,
            "Content-Type": "application/json"}


class EcoFlowAPIError(Exception):
    pass


# ── Developer API client ──────────────────────────────────────────────────

class EcoFlowAPI:
    """REST client for the EcoFlow Developer (Open) API.

    Used for:
      - Authentication + MQTT credential retrieval (GET, auth-only signing)
      - Device listing (GET, auth-only signing)
      - Quota reading (GET, auth-only signing) — returns 1006 for Delta 3
      - SET commands (PUT, body-param signing) — confirmed working for Delta 3
    """

    def __init__(self, access_key: str, secret_key: str,
                 device_sn: str, api_host: str = API_HOST_DEFAULT) -> None:
        self._ak   = access_key.strip()
        self._sk   = secret_key.strip()
        self._sn   = device_sn.strip()
        self._host = api_host.rstrip("/")
        self._s    = requests.Session()
        self._s.headers.update({"User-Agent": "HomeAssistant/EcoFlowCloud"})

    def _get(self, path: str, url_params: dict | None = None) -> dict:
        """GET request with auth-only signing (no request params in signature)."""
        url  = f"{self._host}{path}"
        hdrs = _sign_get(self._ak, self._sk)
        try:
            r    = self._s.get(url, headers=hdrs, params=url_params, timeout=15)
            r.raise_for_status()
            body = r.json()
        except requests.RequestException as e:
            raise EcoFlowAPIError(f"GET {path} failed: {e}") from e
        _LOGGER.debug("GET %s: %s", path, str(body)[:300])
        if str(body.get("code")) != "0":
            raise EcoFlowAPIError(
                f"API error {body.get('code')}: {body.get('message', 'unknown')}")
        return body.get("data") or {}

    def _put(self, path: str, body: dict) -> dict:
        """PUT request with body-param signing (flatten + sort + auth)."""
        url  = f"{self._host}{path}"
        hdrs = _sign_put(body, self._ak, self._sk)
        try:
            r    = self._s.put(url, headers=hdrs, json=body, timeout=15)
            r.raise_for_status()
            resp = r.json()
        except requests.RequestException as e:
            raise EcoFlowAPIError(f"PUT {path} failed: {e}") from e
        _LOGGER.debug("PUT %s: %s", path, str(resp)[:300])
        code = str(resp.get("code", ""))
        if code != "0":
            raise EcoFlowAPIError(
                f"SET error {code}: {resp.get('message', 'unknown')}")
        return resp.get("data") or {}

    def get_mqtt_credentials(self) -> dict[str, Any]:
        return self._get(PATH_MQTT)

    def get_device_list(self) -> list[dict]:
        data = self._get(PATH_DEVICE_LIST)
        if isinstance(data, list):
            return data
        return data.get("list", [])

    def get_all_quota(self) -> dict[str, Any]:
        """Returns empty dict on 1006/8521 — not fatal, MQTT is primary."""
        try:
            raw = self._get(PATH_QUOTA, url_params={"sn": self._sn})
            return self._normalise(raw)
        except EcoFlowAPIError as e:
            if "1006" in str(e) or "8521" in str(e):
                _LOGGER.warning(
                    "Quota REST failed for %s (%s) — will rely on MQTT push", self._sn, e)
                self.rest_quota_unavailable = True
                return {}
            raise

    def set_quota(self, module_type: int, operate_type: str,
                  params: dict) -> dict:
        """Send a SET command via REST API PUT.

        This is the primary control path for Delta 3 (D361) devices.
        The Developer API accepts JSON commands that the MQTT /set topic ignores.

        Args:
            module_type: EcoFlow module (1=PD, 2=BMS, 3=INV, 5=MPPT)
            operate_type: Command name (e.g. "acOutCfg", "quietMode")
            params: Command parameters (e.g. {"enabled": 1})

        Returns:
            Response data dict (usually empty on success)

        Raises:
            EcoFlowAPIError: On signing failure (8521), device offline (1006),
                             or other API errors.
        """
        body = {
            "sn":          self._sn,
            "moduleType":  module_type,
            "operateType": operate_type,
            "params":      params,
        }
        _LOGGER.info(
            "EcoFlow REST SET: sn=%s module=%d operate=%s params=%s",
            self._sn, module_type, operate_type, params,
        )
        return self._put(PATH_QUOTA_SET, body)

    def set_quota_cmdcode(self, cmd_code: str, params: dict) -> dict:
        """Send a cmdCode-based SET command via REST API PUT.

        This is the control path for Delta Pro Ultra (DGEB) devices.
        DPU uses cmdCode strings (YJ751_PD_*) instead of moduleType/operateType.

        Args:
            cmd_code: Command code string (e.g. "YJ751_PD_AC_DSG_SET")
            params: Command parameters (e.g. {"enable": 1, "xboost": 1, "outFreq": 50})

        Returns:
            Response data dict (usually empty on success)

        Raises:
            EcoFlowAPIError: On signing failure (8521), device offline (1006),
                             or other API errors.
        """
        body = {
            "sn":       self._sn,
            "cmdCode":  cmd_code,
            "params":   params,
        }
        _LOGGER.info(
            "EcoFlow REST SET cmdCode: sn=%s cmdCode=%s params=%s",
            self._sn, cmd_code, params,
        )
        return self._put(PATH_QUOTA_SET, body)

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
        _LOGGER.info(
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
        _LOGGER.info(
            "EcoFlow login response: HTTP=%s code=%s msg=%s",
            resp.status_code, code, msg
        )

        if code != "0":
            raise EcoFlowAPIError(f"Login failed: {msg}")

        data = body.get("data", {})
        user = data.get("user", data)
        self._token   = data.get("token", "")
        self._user_id = str(user.get("userId", user.get("id", "")))
        _LOGGER.info(
            "EcoFlow login SUCCESS: userId=%s token=%s…",
            self._user_id, self._token[:12]
        )
        return data

    def _make_client_id(self) -> str:
        """
        The EcoFlow MQTT broker authenticates the client ID and requires the
        ANDROID_ prefix — other prefixes result in rc=5 (Not Authorized).

        Format: ANDROID_{8-digit timestamp}_{userId}

        NOTE: When the EcoFlow mobile app is also connected it uses the same
        prefix with a different random part, so both sessions can coexist on
        the broker. The root cause of commands being ignored must be sought
        elsewhere (payload format, topic, or app-side exclusive lock).
        """
        import time as _time
        random_part = str(int(_time.time()))[-8:]
        return f"ANDROID_{random_part}_{self._user_id}"

    def get_mqtt_credentials(self) -> dict[str, Any]:
        """
        Login then fetch MQTT credentials from /iot-auth/app/certification.
        Returns dict compatible with Open API /certification response shape.
        """
        self._login()

        _LOGGER.info(
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

        _LOGGER.info("EcoFlow cert response: HTTP=%s code=%s data=%s",
                        resp.status_code, body.get("code"), body.get("data"))

        if str(body.get("code")) != "0":
            raise EcoFlowAPIError(
                f"MQTT cert failed: {body.get('message', 'unknown')}")

        cert = body.get("data", {})
        client_id = self._make_client_id()
        _LOGGER.info(
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

    # ── Hybrid mode: optional Developer API for SET commands ─────────────
    _developer_api: EcoFlowAPI | None = None

    def attach_developer_api(self, dev_api: EcoFlowAPI) -> None:
        """Attach a Developer API client for REST SET commands.

        When attached, set_quota() delegates to the Developer API.
        This enables hybrid mode: MQTT read (Private) + REST write (Developer).
        """
        self._developer_api = dev_api
        _LOGGER.info(
            "EcoFlow: Developer API attached for REST SET (sn=%s host=%s)",
            self._sn, dev_api._host,
        )

    @property
    def has_developer_api(self) -> bool:
        """True if a Developer API client is attached for REST SET."""
        return self._developer_api is not None

    def set_quota(self, module_type: int, operate_type: str,
                  params: dict) -> dict:
        """Send SET command via Developer API (if attached).

        In hybrid mode, delegates to EcoFlowAPI.set_quota().
        Without Developer API, raises EcoFlowAPIError.
        """
        if self._developer_api is None:
            raise EcoFlowAPIError(
                "No Developer API configured — cannot send REST SET. "
                "Add Developer API credentials in integration options."
            )
        return self._developer_api.set_quota(module_type, operate_type, params)

    def set_quota_cmdcode(self, cmd_code: str, params: dict) -> dict:
        """Send cmdCode-based SET via Developer API (if attached).

        Used by Delta Pro Ultra (DGEB) devices.
        """
        if self._developer_api is None:
            raise EcoFlowAPIError(
                "No Developer API configured — cannot send REST SET cmdCode. "
                "Add Developer API credentials in integration options."
            )
        return self._developer_api.set_quota_cmdcode(cmd_code, params)
