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
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import color_hs_to_RGB

from .api import RecuairApiError
from .const import DOMAIN
from .coordinator import RecuairDataUpdateCoordinator


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
    coordinator: RecuairDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RecuairLight(coordinator, entry)])


class RecuairLight(CoordinatorEntity[RecuairDataUpdateCoordinator], LightEntity):
    """Native Home Assistant light entity for Recuair."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        coordinator: RecuairDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{entry.entry_id}_light"

    @property
    def _intensity(self) -> int:
        """Return current Recuair intensity (0-5) from coordinator data."""
        value = (self.coordinator.data or {}).get("light_intensity")
        if isinstance(value, int):
            return value
        return 0

    @property
    def _rgb(self) -> tuple[int, int, int]:
        """Return current RGB color from coordinator data."""
        rgb = (self.coordinator.data or {}).get("light_rgb")
        if (
            isinstance(rgb, tuple)
            and len(rgb) == 3
            and all(isinstance(value, int) for value in rgb)
        ):
            return rgb
        return (255, 255, 255)

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

        if hs_color is not None and isinstance(hs_color, (tuple, list)) and len(hs_color) == 2:
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

        self.coordinator.async_update_local_state(
            {"light_intensity": intensity, "light_rgb": (red, green, blue)}
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off light."""
        try:
            await self.coordinator.api.async_light_off()
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err

        self.coordinator.async_update_local_state({"light_intensity": 0})
