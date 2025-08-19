"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .api import RecuairApi

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="co2",
        name="CO2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement="ppm",
    ),
    SensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
    ),
    SensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement="%",
    ),
    SensorEntityDescription(
        key="filter_status",
        name="Filter Status",
        native_unit_of_measurement="%",
    ),
    SensorEntityDescription(
        key="ventilation_intensity",
        name="Ventilation Intensity",
        native_unit_of_measurement="%",
    ),
    SensorEntityDescription(
        key="mode",
        name="Mode",
    ),
    SensorEntityDescription(
        key="light_intensity",
        name="Light Intensity",
        icon="mdi:brightness-5",
    ),
    SensorEntityDescription(
        key="last_successful_update",
        name="Last Successful Update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    api: RecuairApi = hass.data[DOMAIN][entry.entry_id]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 60)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            data = await api.get_data()
            if data:
                data["last_successful_update"] = dt_util.utcnow()
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="recuair_sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        name=entry.title,
        manufacturer="Recuair",
        model="DC40",
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    entities = [
        RecuairSensor(coordinator, description, device_info)
        for description in SENSOR_TYPES
        if coordinator.data and description.key in coordinator.data
    ]
    async_add_entities(entities)


class RecuairSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{device_info['identifiers']}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None