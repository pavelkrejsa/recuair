"""Unit tests for the Recuair shared coordinator and entity platforms."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock


def _install_stubs() -> None:
    """Install lightweight Home Assistant, aiohttp, and bs4 stubs when absent."""
    if "aiohttp" not in sys.modules:
        aiohttp_mod = types.ModuleType("aiohttp")

        class ClientError(Exception):
            pass

        class ClientTimeout:
            def __init__(self, total=None):
                self.total = total

        class ClientSession:
            pass

        aiohttp_mod.ClientError = ClientError
        aiohttp_mod.ClientTimeout = ClientTimeout
        aiohttp_mod.ClientSession = ClientSession
        sys.modules["aiohttp"] = aiohttp_mod

    if "bs4" not in sys.modules:
        bs4_mod = types.ModuleType("bs4")

        class BeautifulSoup:
            def __init__(self, html, parser):
                self.html = html

        bs4_mod.BeautifulSoup = BeautifulSoup
        sys.modules["bs4"] = bs4_mod

    if "homeassistant" in sys.modules:
        return

    def _pkg(name: str) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
        return mod

    _pkg("homeassistant")
    _pkg("homeassistant.components")
    _pkg("homeassistant.helpers")
    _pkg("homeassistant.util")

    const_mod = types.ModuleType("homeassistant.const")
    const_mod.CONF_HOST = "host"
    const_mod.CONF_SCAN_INTERVAL = "scan_interval"
    sys.modules["homeassistant.const"] = const_mod

    core_mod = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        def __init__(self):
            self.data = {}
            self.config_entries = types.SimpleNamespace(
                async_forward_entry_setups=AsyncMock(return_value=None),
                async_unload_platforms=AsyncMock(return_value=True),
                async_reload=AsyncMock(return_value=None),
            )

    core_mod.HomeAssistant = HomeAssistant
    sys.modules["homeassistant.core"] = core_mod

    ce_mod = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        def __init__(
            self,
            entry_id="entry_1",
            unique_id="recuair_bedroom",
            title="Bedroom",
            data=None,
            options=None,
        ):
            self.entry_id = entry_id
            self.unique_id = unique_id
            self.title = title
            self.data = data or {}
            self.options = options or {}
            self._unloaders = []

        def async_on_unload(self, func):
            self._unloaders.append(func)

        def add_update_listener(self, listener):
            return listener

    ce_mod.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = ce_mod

    exc_mod = types.ModuleType("homeassistant.exceptions")

    class HomeAssistantError(Exception):
        pass

    exc_mod.HomeAssistantError = HomeAssistantError
    sys.modules["homeassistant.exceptions"] = exc_mod

    aio_helper = types.ModuleType("homeassistant.helpers.aiohttp_client")
    aio_helper.async_get_clientsession = lambda hass: object()
    sys.modules["homeassistant.helpers.aiohttp_client"] = aio_helper

    entity_mod = types.ModuleType("homeassistant.helpers.entity")

    class DeviceInfo(dict):
        pass

    entity_mod.DeviceInfo = DeviceInfo
    sys.modules["homeassistant.helpers.entity"] = entity_mod

    ep_mod = types.ModuleType("homeassistant.helpers.entity_platform")
    ep_mod.AddEntitiesCallback = object
    sys.modules["homeassistant.helpers.entity_platform"] = ep_mod

    uc_mod = types.ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, *, name, update_interval=None, update_method=None):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self._update_method = update_method
            self.data = None
            self.update_notifications = 0

        async def _async_update_data(self):
            if self._update_method is not None:
                return await self._update_method()
            raise NotImplementedError

        async def async_config_entry_first_refresh(self):
            self.data = await self._async_update_data()

        def async_set_updated_data(self, data):
            self.data = data
            self.update_notifications += 1

    class CoordinatorEntity:
        _attr_should_poll = False

        def __class_getitem__(cls, item):
            return cls

        def __init__(self, coordinator):
            self.coordinator = coordinator

        @property
        def should_poll(self) -> bool:
            return self._attr_should_poll

    uc_mod.DataUpdateCoordinator = DataUpdateCoordinator
    uc_mod.CoordinatorEntity = CoordinatorEntity
    uc_mod.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = uc_mod

    dt_mod = types.ModuleType("homeassistant.util.dt")
    dt_mod.utcnow = lambda: datetime(2026, 11, 25, 10, 0, 0, tzinfo=timezone.utc)
    sys.modules["homeassistant.util.dt"] = dt_mod

    color_mod = types.ModuleType("homeassistant.util.color")
    color_mod.color_hs_to_RGB = lambda h, s: (10, 20, 30)
    sys.modules["homeassistant.util.color"] = color_mod

    sensor_mod = types.ModuleType("homeassistant.components.sensor")

    class SensorDeviceClass(str, Enum):
        CO2 = "carbon_dioxide"
        TEMPERATURE = "temperature"
        HUMIDITY = "humidity"
        TIMESTAMP = "timestamp"

    @dataclass(frozen=True)
    class SensorEntityDescription:
        key: str
        name: str | None = None
        device_class: SensorDeviceClass | None = None
        native_unit_of_measurement: str | None = None
        icon: str | None = None
        entity_registry_enabled_default: bool = True

    class SensorEntity:
        pass

    sensor_mod.SensorDeviceClass = SensorDeviceClass
    sensor_mod.SensorEntityDescription = SensorEntityDescription
    sensor_mod.SensorEntity = SensorEntity
    sys.modules["homeassistant.components.sensor"] = sensor_mod

    select_mod = types.ModuleType("homeassistant.components.select")

    class SelectEntity:
        pass

    select_mod.SelectEntity = SelectEntity
    sys.modules["homeassistant.components.select"] = select_mod

    number_mod = types.ModuleType("homeassistant.components.number")

    class NumberMode(str, Enum):
        SLIDER = "slider"

    class NumberEntity:
        pass

    number_mod.NumberEntity = NumberEntity
    number_mod.NumberMode = NumberMode
    sys.modules["homeassistant.components.number"] = number_mod

    light_mod = types.ModuleType("homeassistant.components.light")

    class ColorMode(str, Enum):
        RGB = "rgb"

    class LightEntity:
        pass

    light_mod.ATTR_BRIGHTNESS = "brightness"
    light_mod.ATTR_HS_COLOR = "hs_color"
    light_mod.ATTR_RGB_COLOR = "rgb_color"
    light_mod.ColorMode = ColorMode
    light_mod.LightEntity = LightEntity
    sys.modules["homeassistant.components.light"] = light_mod


_install_stubs()

from homeassistant.config_entries import ConfigEntry  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.exceptions import HomeAssistantError  # noqa: E402
from homeassistant.helpers.update_coordinator import UpdateFailed  # noqa: E402

recuair_init = importlib.import_module("recuair")
recuair_api = importlib.import_module("recuair.api")
recuair_coord = importlib.import_module("recuair.coordinator")
recuair_light = importlib.import_module("recuair.light")
recuair_number = importlib.import_module("recuair.number")
recuair_select = importlib.import_module("recuair.select")
recuair_sensor = importlib.import_module("recuair.sensor")


def _sample_payload() -> dict:
    return {
        "device_name": "Bedroom",
        "room_temperature": 22,
        "humidity": 48,
        "outside_temperature": 5,
        "co2": 650,
        "filter_status": 80,
        "ventilation_intensity": 40,
        "mode": "Mode: AUTO",
        "light_intensity": 3,
        "light_rgb": (100, 150, 200),
        "firmware_version": "1.2.3",
    }


class TestRecuairCoordinatorAndEntities(unittest.IsolatedAsyncioTestCase):
    """Verify shared coordinator polling and entity synchronization."""

    def setUp(self) -> None:
        self.hass = HomeAssistant()
        self.entry = ConfigEntry(
            entry_id="entry_bedroom",
            unique_id="Bedroom",
            title="Bedroom",
            data={CONF_HOST: "192.168.2.11", CONF_SCAN_INTERVAL: 60},
            options={CONF_HOST: "192.168.2.11", CONF_SCAN_INTERVAL: 90},
        )
        self.api = types.SimpleNamespace(
            get_data=AsyncMock(return_value=_sample_payload()),
            async_set_mode=AsyncMock(return_value=None),
            async_set_light=AsyncMock(return_value=None),
            async_light_off=AsyncMock(return_value=None),
        )

    async def test_shared_coordinator_fetches_once_for_all_platforms(self) -> None:
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        self.assertEqual(coordinator.update_interval, timedelta(seconds=90))
        self.assertEqual(
            coordinator.device_info["configuration_url"], "http://192.168.2.11"
        )

        await coordinator.async_config_entry_first_refresh()
        self.hass.data.setdefault("recuair", {})[self.entry.entry_id] = coordinator

        added = []
        await recuair_sensor.async_setup_entry(self.hass, self.entry, added.extend)
        await recuair_select.async_setup_entry(self.hass, self.entry, added.extend)
        await recuair_number.async_setup_entry(self.hass, self.entry, added.extend)
        await recuair_light.async_setup_entry(self.hass, self.entry, added.extend)

        # Exactly one HTTP fetch across all 4 platforms
        self.assertEqual(self.api.get_data.await_count, 1)
        self.assertIn("last_successful_update", coordinator.data)

        # No entity enables independent polling
        for entity in added:
            self.assertFalse(entity.should_poll)

    async def test_coordinator_raises_update_failed_when_api_returns_none(self) -> None:
        self.api.get_data = AsyncMock(return_value=None)
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        with self.assertRaises(UpdateFailed):
            await coordinator.async_config_entry_first_refresh()

    async def test_unique_ids_preserved_for_backwards_compatibility(self) -> None:
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        await coordinator.async_config_entry_first_refresh()
        self.hass.data.setdefault("recuair", {})[self.entry.entry_id] = coordinator

        sensors, selects, numbers, lights = [], [], [], []
        await recuair_sensor.async_setup_entry(self.hass, self.entry, sensors.extend)
        await recuair_select.async_setup_entry(self.hass, self.entry, selects.extend)
        await recuair_number.async_setup_entry(self.hass, self.entry, numbers.extend)
        await recuair_light.async_setup_entry(self.hass, self.entry, lights.extend)

        expected_sensor_uid = f"{coordinator.device_info['identifiers']}_co2"
        self.assertIn(expected_sensor_uid, [s._attr_unique_id for s in sensors])
        self.assertEqual(selects[0]._attr_unique_id, "entry_bedroom_mode")
        self.assertEqual(
            numbers[0]._attr_unique_id, "entry_bedroom_light_intensity_control"
        )
        self.assertEqual(lights[0]._attr_unique_id, "entry_bedroom_light")

    async def test_select_updates_shared_state_and_wraps_api_error(self) -> None:
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        await coordinator.async_config_entry_first_refresh()

        select_entity = recuair_select.RecuairModeSelect(coordinator, self.entry)
        mode_sensor = recuair_sensor.RecuairSensor(
            coordinator,
            next(d for d in recuair_sensor.SENSOR_TYPES if d.key == "mode"),
        )
        self.assertEqual(select_entity.current_option, "auto")

        await select_entity.async_select_option("bypass")
        self.api.async_set_mode.assert_awaited_once_with("bypass")
        self.assertEqual(select_entity.current_option, "bypass")
        self.assertEqual(mode_sensor.native_value, "bypass")

        self.api.async_set_mode = AsyncMock(side_effect=recuair_api.RecuairApiError("boom"))
        with self.assertRaises(HomeAssistantError):
            await select_entity.async_select_option("off")

    async def test_number_preserves_rgb_and_syncs_light(self) -> None:
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        await coordinator.async_config_entry_first_refresh()

        number_entity = recuair_number.RecuairLightIntensityNumber(coordinator, self.entry)
        light_entity = recuair_light.RecuairLight(coordinator, self.entry)

        self.assertEqual(number_entity.native_value, 3)
        self.assertEqual(light_entity.rgb_color, (100, 150, 200))

        await number_entity.async_set_native_value(5)
        self.api.async_set_light.assert_awaited_once_with(
            intensity=5, red=100, green=150, blue=200
        )
        self.assertEqual(number_entity.native_value, 5)
        self.assertTrue(light_entity.is_on)
        self.assertEqual(light_entity.brightness, 255)
        self.assertEqual(light_entity.rgb_color, (100, 150, 200))

    async def test_light_turn_on_and_off_syncs_number(self) -> None:
        coordinator = recuair_coord.RecuairDataUpdateCoordinator(
            self.hass, self.entry, self.api
        )
        await coordinator.async_config_entry_first_refresh()

        light_entity = recuair_light.RecuairLight(coordinator, self.entry)
        number_entity = recuair_number.RecuairLightIntensityNumber(coordinator, self.entry)

        await light_entity.async_turn_on(brightness=102, rgb_color=(10, 20, 30))
        self.api.async_set_light.assert_awaited_once_with(
            intensity=2, red=10, green=20, blue=30
        )
        self.assertEqual(number_entity.native_value, 2)
        self.assertEqual(light_entity.rgb_color, (10, 20, 30))

        await light_entity.async_turn_off()
        self.api.async_light_off.assert_awaited_once()
        self.assertFalse(light_entity.is_on)
        self.assertEqual(number_entity.native_value, 0)

    def test_normalize_mode(self) -> None:
        self.assertEqual(recuair_select._normalize_mode("AUTO"), "auto")
        self.assertEqual(recuair_select._normalize_mode("Speed 3"), "3")
        self.assertEqual(recuair_select._normalize_mode("Holiday mode"), "holiday")
        self.assertIsNone(recuair_select._normalize_mode("unknown"))


if __name__ == "__main__":
    unittest.main()
