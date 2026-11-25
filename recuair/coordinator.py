"""Shared DataUpdateCoordinator for the Recuair integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import RecuairApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RecuairDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data fetching across all Recuair entity platforms."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: RecuairApi,
    ) -> None:
        """Initialize the Recuair coordinator."""
        self.api = api
        self.entry = entry
        host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, 60),
        )
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Recuair",
            model="DC40",
            configuration_url=f"http://{host}",
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.title}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest state from the Recuair unit once per scan interval."""
        try:
            data = await self.api.get_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Recuair API: {err}") from err

        if not data:
            raise UpdateFailed("Failed to fetch data from Recuair unit")

        data["last_successful_update"] = dt_util.utcnow()
        return data

    def async_update_local_state(self, updates: dict[str, Any]) -> None:
        """Apply optimistic state updates to cached coordinator data."""
        merged = dict(self.data or {})
        merged.update(updates)
        self.async_set_updated_data(merged)
