"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL
from .coordinator import RecuairCoordinator
from .identity import mac_connection

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
    coordinator: RecuairCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        connections=mac_connection(entry),
        name=entry.title,
        manufacturer="Recuair",
        model=MODEL,
        configuration_url=coordinator.api.configuration_url,
    )

    entities = [
        RecuairSensor(coordinator, entry, description, device_info)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class RecuairSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: RecuairCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None
