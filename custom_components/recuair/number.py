"""Number platform for Recuair controls."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RecuairApiError
from .const import DOMAIN, MODEL
from .coordinator import RecuairCoordinator
from .identity import mac_connection


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair number entities from config entry."""
    coordinator: RecuairCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        connections=mac_connection(entry),
        name=entry.title,
        manufacturer="Recuair",
        model=MODEL,
        configuration_url=coordinator.api.configuration_url,
    )
    async_add_entities([RecuairLightIntensityNumber(coordinator, entry, device_info)])


class RecuairLightIntensityNumber(CoordinatorEntity, NumberEntity):
    """Number entity for Recuair light intensity."""

    _attr_has_entity_name = True
    _attr_name = "Light Intensity"
    _attr_native_min_value = 0
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: RecuairCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize light intensity number."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_light_intensity_control"
        self._attr_native_value = 0
        self._update_from_coordinator()

    @callback
    def _update_from_coordinator(self) -> None:
        """Apply light intensity from the shared device poll."""
        data = self.coordinator.data
        value = (data or {}).get("light_intensity")
        if isinstance(value, int):
            self._attr_native_value = value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the number when the shared poll completes."""
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_set_native_value(self, value: float) -> None:
        """Set device light intensity.

        Recuair expects full RGB payload for light updates.
        """
        intensity = int(value)
        try:
            await self.coordinator.api.async_set_light(
                intensity=intensity, red=255, green=255, blue=255
            )
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_native_value = intensity
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
