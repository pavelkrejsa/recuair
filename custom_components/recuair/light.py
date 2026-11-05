"""Light platform for Recuair controls."""
from __future__ import annotations

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import color_hs_to_RGB

from .api import RecuairApiError
from .const import DOMAIN, MODEL
from .coordinator import RecuairCoordinator
from .identity import mac_connection


def _intensity_to_brightness(intensity: int) -> int:
    """Convert Recuair intensity (0-5) to HA brightness (0-255)."""
    return round((max(0, min(5, intensity)) * 255) / 5)


def _brightness_to_intensity(brightness: int) -> int:
    """Convert HA brightness (0-255) to Recuair intensity (0-5)."""
    return round((max(0, min(255, brightness)) * 5) / 255)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair light entities from config entry."""
    coordinator: RecuairCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        connections=mac_connection(entry),
        name=entry.title,
        manufacturer="Recuair",
        model=MODEL,
        configuration_url=coordinator.api.configuration_url,
    )
    async_add_entities([RecuairLight(coordinator, entry, device_info)])


class RecuairLight(CoordinatorEntity, LightEntity):
    """Native Home Assistant light entity for Recuair."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        coordinator: RecuairCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._intensity = 0
        self._rgb = (255, 255, 255)
        self._update_from_coordinator()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._intensity > 0

    @property
    def brightness(self) -> int:
        """Return brightness in HA scale."""
        return _intensity_to_brightness(self._intensity)

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return current RGB color."""
        return self._rgb

    @callback
    def _update_from_coordinator(self) -> None:
        """Apply light values from the shared device poll."""
        data = self.coordinator.data
        if not data:
            return

        intensity = data.get("light_intensity")
        if isinstance(intensity, int):
            self._intensity = intensity

        rgb = data.get("light_rgb")
        if (
            isinstance(rgb, tuple)
            and len(rgb) == 3
            and all(isinstance(value, int) for value in rgb)
        ):
            self._rgb = rgb

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update light state when the shared device poll completes."""
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on light with optional brightness and RGB values."""
        rgb = kwargs.get(ATTR_RGB_COLOR, self._rgb)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is None:
            intensity = self._intensity if self._intensity > 0 else 5
        else:
            intensity = _brightness_to_intensity(int(brightness))
            if intensity == 0:
                intensity = 1

        if (
            hs_color is not None
            and isinstance(hs_color, (tuple, list))
            and len(hs_color) == 2
        ):
            rgb = color_hs_to_RGB(float(hs_color[0]), float(hs_color[1]))

        if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
            rgb = self._rgb

        red, green, blue = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

        try:
            await self.coordinator.api.async_set_light(
                intensity=intensity, red=red, green=green, blue=blue
            )
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err

        self._intensity = intensity
        self._rgb = (red, green, blue)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off light."""
        try:
            await self.coordinator.api.async_light_off()
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err

        self._intensity = 0
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
