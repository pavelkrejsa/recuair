"""Select platform for Recuair controls."""
from __future__ import annotations

import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RecuairApiError
from .const import DOMAIN, MODEL, MODE_AUTO, MODE_OPTIONS
from .coordinator import RecuairCoordinator
from .identity import mac_connection


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
    coordinator: RecuairCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        connections=mac_connection(entry),
        name=entry.title,
        manufacturer="Recuair",
        model=MODEL,
        configuration_url=coordinator.api.configuration_url,
    )
    async_add_entities([RecuairModeSelect(coordinator, entry, device_info)])


class RecuairModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for Recuair operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_options = MODE_OPTIONS

    def __init__(
        self,
        coordinator: RecuairCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the mode select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_mode"
        self._attr_current_option = MODE_AUTO
        self._update_from_coordinator()

    @callback
    def _update_from_coordinator(self) -> None:
        """Apply the reported operating mode from the shared poll."""
        data = self.coordinator.data
        mode = (data or {}).get("mode")
        if isinstance(mode, str):
            normalized = _normalize_mode(mode)
            if normalized is not None:
                self._attr_current_option = normalized

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the mode when the shared poll completes."""
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Select a new device mode."""
        try:
            await self.coordinator.api.async_set_mode(option)
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
