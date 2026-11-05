"""Shared data coordinator for Recuair entities."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import RecuairApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RecuairCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
    """Coordinate one status-page poll for all Recuair entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: RecuairApi,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator and shared device API."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Fetch the current device state once for all platforms."""
        device_data = await self.api.get_data()
        if device_data:
            device_data["last_successful_update"] = dt_util.utcnow()
        return device_data
