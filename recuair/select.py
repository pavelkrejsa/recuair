"""Select platform for Recuair controls."""
from __future__ import annotations

import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RecuairApiError
from .const import DOMAIN, MODE_AUTO, MODE_OPTIONS
from .coordinator import RecuairDataUpdateCoordinator


def _normalize_mode(mode: str) -> str | None:
    """Normalize mode value from Recuair UI to integration option values."""
    normalized = mode.strip().lower()
    if normalized in MODE_OPTIONS:
        return normalized

    if "auto" in normalized:
        return "auto"
    if "off" in normalized:
        return "off"
    if "holiday" in normalized:
        return "holiday"
    if "bypass" in normalized:
        return "bypass"

    match = re.search(r"\b([1-4])\b", normalized)
    if match:
        return match.group(1)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair select entities from config entry."""
    coordinator: RecuairDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RecuairModeSelect(coordinator, entry)])


class RecuairModeSelect(CoordinatorEntity[RecuairDataUpdateCoordinator], SelectEntity):
    """Select entity for Recuair operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_options = MODE_OPTIONS

    def __init__(
        self,
        coordinator: RecuairDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the mode select entity."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{entry.entry_id}_mode"

    @property
    def current_option(self) -> str:
        """Return the current normalized mode from shared coordinator data."""
        mode = (self.coordinator.data or {}).get("mode")
        if isinstance(mode, str):
            normalized = _normalize_mode(mode)
            if normalized is not None:
                return normalized
        return MODE_AUTO

    async def async_select_option(self, option: str) -> None:
        """Select a new device mode."""
        try:
            await self.coordinator.api.async_set_mode(option)
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err
        self.coordinator.async_update_local_state({"mode": option})
