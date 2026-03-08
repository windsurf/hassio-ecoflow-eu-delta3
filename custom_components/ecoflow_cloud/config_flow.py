"""Config flow + options flow for EcoFlow Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, INTEGRATION_VERSION,
    CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_DEVICE_SN, CONF_API_HOST,
    CONF_AUTH_MODE, CONF_EMAIL, CONF_PASSWORD,
    AUTH_MODE_PUBLIC, AUTH_MODE_PRIVATE, AUTH_MODE_AUTO,
    API_HOST_EU, API_HOST_US, API_HOST_GLOBAL,
    PRIVATE_API_SN_PREFIXES,
)
from .api_client import EcoFlowAPI, EcoFlowPrivateAPI, EcoFlowAPIError


def _resolve_auth_mode(auth_mode: str, sn: str) -> str:
    """Resolve AUTH_MODE_AUTO to public or private based on SN prefix."""
    if auth_mode != AUTH_MODE_AUTO:
        return auth_mode
    sn_upper = sn.upper()
    if any(sn_upper.startswith(pfx) for pfx in PRIVATE_API_SN_PREFIXES):
        return AUTH_MODE_PRIVATE
    return AUTH_MODE_PUBLIC

_LOGGER = logging.getLogger(__name__)


async def _test_public(hass, ak, sk, sn) -> tuple[str | None, dict]:
    working = None
    results = {}
    for host in [API_HOST_EU, API_HOST_US, API_HOST_GLOBAL]:
        try:
            api     = EcoFlowAPI(ak, sk, sn, host)
            mqtt    = await hass.async_add_executor_job(api.get_mqtt_credentials)
            if not mqtt:
                results[host] = "❌ empty response"
                continue
            devices = await hass.async_add_executor_job(api.get_device_list)
            sns     = [d.get("sn", "") for d in devices]
            if sn in sns:
                name = next((d.get("deviceName") or d.get("productName", "?")
                             for d in devices if d.get("sn") == sn), "?")
                results[host] = f"✅ OK — {name}"
                working = working or host
            elif sns:
                results[host] = f"⚠️ Auth OK, SN not found (account has: {', '.join(sns)})"
                working = working or host
            else:
                results[host] = "⚠️ Auth OK, no devices on account"
                working = working or host
        except EcoFlowAPIError as e:
            results[host] = f"❌ {e}"
        except Exception as e:
            results[host] = f"❌ {e}"
    return working, results


async def _test_private(hass, email, password, sn) -> tuple[bool, str]:
    try:
        api     = EcoFlowPrivateAPI(email, password, sn)
        mqtt    = await hass.async_add_executor_job(api.get_mqtt_credentials)
        if not mqtt:
            return False, "❌ empty response after login"
        devices = await hass.async_add_executor_job(api.get_device_list)
        sns     = [d.get("sn", "") for d in devices]
        if sn in sns:
            name = next((d.get("deviceName") or d.get("productName", "?")
                         for d in devices if d.get("sn") == sn), "?")
            return True, f"✅ Login OK — found {name} ({sn})"
        elif sns:
            return True, f"⚠️ Login OK, SN not found. Account has: {', '.join(sns)}"
        return True, "⚠️ Login OK, no devices on account"
    except EcoFlowAPIError as e:
        return False, f"❌ {e}"
    except Exception as e:
        return False, f"❌ {e}"


# ── Initial setup flow ────────────────────────────────────────────────────

class EcoFlowCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}
        self._working_host: str | None = None
        self._private_ok: bool = False

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Step 1: choose auth mode."""
        if user_input is not None:
            sn        = user_input[CONF_DEVICE_SN].strip().upper()
            raw_mode  = user_input[CONF_AUTH_MODE]
            resolved  = _resolve_auth_mode(raw_mode, sn)
            self._data[CONF_DEVICE_SN]  = sn
            self._data[CONF_AUTH_MODE]  = resolved   # store resolved mode
            if resolved == AUTH_MODE_PRIVATE:
                return await self.async_step_private_creds()
            return await self.async_step_public_creds()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_SN): cv.string,
                vol.Required(CONF_AUTH_MODE, default=AUTH_MODE_AUTO): vol.In({
                    AUTH_MODE_AUTO:    "Auto-detect (recommended — detects from serial number)",
                    AUTH_MODE_PRIVATE: "App Login (Email + Password) — Delta 3, newer devices",
                    AUTH_MODE_PUBLIC:  "Developer API (Access Key + Secret Key)",
                }),
            }),
            description_placeholders={"version": INTEGRATION_VERSION},
        )

    async def async_step_public_creds(self, user_input=None) -> FlowResult:
        if user_input is not None:
            self._data.update({
                CONF_ACCESS_KEY: user_input[CONF_ACCESS_KEY].strip(),
                CONF_SECRET_KEY: user_input[CONF_SECRET_KEY].strip(),
            })
            return await self.async_step_test()

        return self.async_show_form(
            step_id="public_creds",
            data_schema=vol.Schema({
                vol.Required(CONF_ACCESS_KEY): cv.string,
                vol.Required(CONF_SECRET_KEY): cv.string,
            }),
            description_placeholders={
                "version": INTEGRATION_VERSION,
                "hint": "Get your keys at: developer-eu.ecoflow.com",
            },
        )

    async def async_step_private_creds(self, user_input=None) -> FlowResult:
        if user_input is not None:
            self._data.update({
                CONF_EMAIL:    user_input[CONF_EMAIL].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            })
            return await self.async_step_test()

        return self.async_show_form(
            step_id="private_creds",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL):    cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }),
            description_placeholders={
                "version": INTEGRATION_VERSION,
                "hint": "Use your EcoFlow app email and password. Recommended for Delta 3.",
            },
        )

    async def async_step_test(self, user_input=None) -> FlowResult:
        if user_input is None:
            sn   = self._data[CONF_DEVICE_SN]
            mode = self._data[CONF_AUTH_MODE]

            if mode == AUTH_MODE_PRIVATE:
                ok, result = await _test_private(
                    self.hass, self._data[CONF_EMAIL],
                    self._data[CONF_PASSWORD], sn
                )
                self._private_ok = ok
                _LOGGER.warning("EcoFlow private API test: %s", result)
                hint = (f"✅ Will connect — click Submit to finish."
                        if ok else
                        "❌ Login failed — click Submit to re-enter credentials.")
                return self.async_show_form(
                    step_id="test",
                    data_schema=vol.Schema({}),
                    description_placeholders={
                        "version": INTEGRATION_VERSION,
                        "eu":   f"App Login: {result}",
                        "us":   "",
                        "glob": "",
                        "hint": hint,
                    },
                )
            else:
                self._working_host, results = await _test_public(
                    self.hass, self._data[CONF_ACCESS_KEY],
                    self._data[CONF_SECRET_KEY], sn
                )
                _LOGGER.warning("EcoFlow public API test: EU=%s US=%s Global=%s",
                    results.get(API_HOST_EU), results.get(API_HOST_US),
                    results.get(API_HOST_GLOBAL))
                hint = (f"✅ Will use: {self._working_host} — click Submit."
                        if self._working_host else
                        "❌ No server worked — click Submit to re-enter credentials.")
                return self.async_show_form(
                    step_id="test",
                    data_schema=vol.Schema({}),
                    description_placeholders={
                        "version": INTEGRATION_VERSION,
                        "eu":   f"EU:     {results.get(API_HOST_EU, '—')}",
                        "us":   f"US:     {results.get(API_HOST_US, '—')}",
                        "glob": f"Global: {results.get(API_HOST_GLOBAL, '—')}",
                        "hint": hint,
                    },
                )

        # Submit pressed
        sn   = self._data[CONF_DEVICE_SN]
        mode = self._data[CONF_AUTH_MODE]

        if mode == AUTH_MODE_PRIVATE and not self._private_ok:
            return await self.async_step_private_creds()
        if mode == AUTH_MODE_PUBLIC and not self._working_host:
            return await self.async_step_public_creds()

        if mode == AUTH_MODE_PUBLIC:
            self._data[CONF_API_HOST] = self._working_host

        await self.async_set_unique_id(sn)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"EcoFlow ({sn})",
            data=self._data,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EcoFlowOptionsFlow(config_entry)


# ── Options flow ──────────────────────────────────────────────────────────

class EcoFlowOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        current = self._entry.data
        mode    = current.get(CONF_AUTH_MODE, AUTH_MODE_PUBLIC)

        if mode == AUTH_MODE_PRIVATE:
            schema = vol.Schema({
                vol.Required(CONF_EMAIL,    default=current.get(CONF_EMAIL, "")): cv.string,
                vol.Required(CONF_PASSWORD, default=""): cv.string,
                vol.Required(CONF_DEVICE_SN, default=current.get(CONF_DEVICE_SN, "")): cv.string,
            })
        else:
            schema = vol.Schema({
                vol.Required(CONF_ACCESS_KEY, default=current.get(CONF_ACCESS_KEY, "")): cv.string,
                vol.Required(CONF_SECRET_KEY, default=current.get(CONF_SECRET_KEY, "")): cv.string,
                vol.Required(CONF_DEVICE_SN,  default=current.get(CONF_DEVICE_SN, "")): cv.string,
                vol.Required(CONF_API_HOST,   default=current.get(CONF_API_HOST, API_HOST_EU)):
                    vol.In([API_HOST_EU, API_HOST_US, API_HOST_GLOBAL]),
            })

        if user_input is not None:
            new_data = {**current, **{k: v.strip() if isinstance(v, str) else v
                                      for k, v in user_input.items()}}
            self.hass.config_entries.async_update_entry(self._entry, data=new_data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "version":      INTEGRATION_VERSION,
                "current_host": current.get(CONF_API_HOST, API_HOST_EU),
                "mode":         mode,
            },
        )
