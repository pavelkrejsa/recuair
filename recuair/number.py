"""Number platform for Recuair controls."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RecuairApiError
from .const import DOMAIN
from .coordinator import RecuairDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair number entities from config entry."""
    coordinator: RecuairDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RecuairLightIntensityNumber(coordinator, entry)])


class RecuairLightIntensityNumber(
    CoordinatorEntity[RecuairDataUpdateCoordinator], NumberEntity
):
    """Number entity for Recuair light intensity."""

    _attr_has_entity_name = True
    _attr_name = "Light Intensity"
    _attr_native_min_value = 0
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: RecuairDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize light intensity number."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{entry.entry_id}_light_intensity_control"

    @property
    def native_value(self) -> int:
        """Return current light intensity from shared coordinator data."""
        value = (self.coordinator.data or {}).get("light_intensity")
        if isinstance(value, int):
            return value
        return 0

    async def async_set_native_value(self, value: float) -> None:
        """Set device light intensity while preserving current RGB color.

        Recuair expects full RGB payload for light updates.
        """
        intensity = int(value)
        rgb = (self.coordinator.data or {}).get("light_rgb")
        if (
            isinstance(rgb, tuple)
            and len(rgb) == 3
            and all(isinstance(channel, int) for channel in rgb)
        ):
            red, green, blue = rgb
        else:
            red, green, blue = (255, 255, 255)

        try:
            await self.coordinator.api.async_set_light(
                intensity=intensity, red=red, green=green, blue=blue
            )
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err

        self.coordinator.async_update_local_state(
            {"light_intensity": intensity, "light_rgb": (red, green, blue)}
        )
