"""DataUpdateCoordinator for EcoFlow Cloud."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api_client import EcoFlowAPI, EcoFlowAPIError
from .const import DOMAIN, COORDINATOR_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Top-level MQTT keys that are never data fields
_META_KEYS = {"id", "version", "timestamp", "moduleType", "operateType",
              "cmdFunc", "cmdId", "deviceSn", "need_reply", "seq", "random"}


class EcoflowCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """
    Central data hub for one EcoFlow device.

    Strategy:
    - REST polling every 30s as an optional fallback.
    - If REST returns 1006 or 8521 on the first try, polling is permanently
      disabled to avoid log spam. MQTT push is then the sole data source.
    - MQTT push via update_from_mqtt() is always the primary real-time source.
    - Entities are available as soon as their key appears in self.data.
    """

    def __init__(self, hass: HomeAssistant, api: EcoFlowAPI) -> None:
        super().__init__(
            hass, _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=COORDINATOR_UPDATE_INTERVAL),
        )
        self._api = api
        self._rest_disabled = False
        self.data: dict[str, Any] = {}

    def disable_rest_polling(self) -> None:
        """Permanently stop REST polling — used when device returns 1006/8521."""
        if not self._rest_disabled:
            self._rest_disabled = True
            _LOGGER.info(
                "REST polling disabled — device does not support quota endpoint. "
                "All data will come from MQTT push."
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Periodic REST poll. Skipped when disabled. Never raises."""
        if self._rest_disabled:
            return self.data or {}
        try:
            fresh = await self.hass.async_add_executor_job(self._api.get_all_quota)
            if fresh:
                _LOGGER.debug("REST poll: %d keys", len(fresh))
                return {**(self.data or {}), **fresh}
        except EcoFlowAPIError as exc:
            _LOGGER.debug("REST poll error (non-fatal, will retry next interval): %s", exc)
        except Exception as exc:
            _LOGGER.debug("REST poll unexpected error (non-fatal): %s", exc)
        return self.data or {}

    @callback
    def update_from_mqtt(self, payload: dict[str, Any]) -> None:
        """
        Parse an MQTT push message and merge into coordinator data.
        Must be called via hass.loop.call_soon_threadsafe() from paho thread.

        Handles all known EcoFlow Open API payload shapes:

        Shape A – typeCode + params dict (most common):
            {"typeCode": "bms_bmsStatus", "params": {"soc": 80, "vol": 12600}}
            → {"bms_bmsStatus.soc": 80, "bms_bmsStatus.vol": 12600}

        Shape B – typeCode + data dict (some firmware versions):
            {"typeCode": "bms_bmsStatus", "data": {"soc": 80}}
            → {"bms_bmsStatus.soc": 80}

        Shape C – params with pre-dotted keys (Open API v2):
            {"params": {"bms_bmsStatus.soc": 80, "inv.outputWatts": 0}}
            → {"bms_bmsStatus.soc": 80, "inv.outputWatts": 0}

        Shape D – param dict:
            {"param": {"bms_bmsStatus.soc": 80}}
            → {"bms_bmsStatus.soc": 80}

        Shape E – flat top-level keys:
            {"bms_bmsStatus.soc": 80, "inv.outputWatts": 0}
            → stored as-is
        """
        if not isinstance(payload, dict):
            return

        _LOGGER.debug("MQTT raw payload: %s", str(payload)[:400])

        new_data: dict[str, Any] = {}
        type_code = payload.get("typeCode", "")
        params    = payload.get("params")
        param     = payload.get("param")
        data_dict = payload.get("data")

        if type_code and isinstance(params, dict):
            for k, v in params.items():
                new_data[f"{type_code}.{k}"] = v
        elif type_code and isinstance(data_dict, dict):
            for k, v in data_dict.items():
                new_data[f"{type_code}.{k}"] = v
        elif isinstance(params, dict):
            new_data = dict(params)
        elif isinstance(param, dict):
            new_data = dict(param)
        elif isinstance(data_dict, dict) and not type_code:
            new_data = dict(data_dict)
        else:
            new_data = {k: v for k, v in payload.items() if k not in _META_KEYS}

        if not new_data:
            _LOGGER.debug("MQTT payload yielded no data: %s", str(payload)[:200])
            return

        _LOGGER.warning(
            "MQTT data received: %d keys — all keys: %s",
            len(new_data), sorted(new_data.keys())
        )
        self.async_set_updated_data({**(self.data or {}), **new_data})
