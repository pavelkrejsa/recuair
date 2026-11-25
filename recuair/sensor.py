"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RecuairDataUpdateCoordinator

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
    coordinator: RecuairDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RecuairSensor(coordinator, description)
        for description in SENSOR_TYPES
        if coordinator.data and description.key in coordinator.data
    ]
    async_add_entities(entities)


class RecuairSensor(CoordinatorEntity[RecuairDataUpdateCoordinator], SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: RecuairDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.device_info['identifiers']}_{description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None
