"""Sensor entities for Kospel integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info
from .coordinator import KospelDataUpdateCoordinator

from .controller.api import HeaterController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel sensor platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Temperature sensors: (unique_id_suffix, translation_key, setting_name)
    temperature_sensors = [
        ("room_temperature_economy", "room_temperature_economy"),
        ("room_temperature_comfort", "room_temperature_comfort"),
        ("room_temperature_comfort_plus", "room_temperature_comfort_plus"),
        ("room_temperature_comfort_minus", "room_temperature_comfort_minus"),
        ("cwu_temperature_economy", "cwu_temperature_economy"),
        ("cwu_temperature_comfort", "cwu_temperature_comfort"),
        ("manual_temperature", "manual_temperature"),
    ]

    for unique_id_suffix, setting_name in temperature_sensors:
        entities.append(
            KospelTemperatureSensor(
                coordinator, entry.entry_id, unique_id_suffix, setting_name
            )
        )

    # Pressure sensor
    entities.append(KospelPressureSensor(coordinator, entry.entry_id))

    # Status sensors: (unique_id_suffix, translation_key, setting_name)
    entities.append(
        KospelPumpStatusSensor(
            coordinator, entry.entry_id, "pump_co", "is_pump_co_running"
        )
    )
    entities.append(
        KospelPumpStatusSensor(
            coordinator, entry.entry_id, "pump_circulation", "is_pump_circulation_running"
        )
    )
    entities.append(KospelValvePositionSensor(coordinator, entry.entry_id))

    async_add_entities(entities)


class KospelSensorEntity(CoordinatorEntity[KospelDataUpdateCoordinator], SensorEntity):
    """Base class for Kospel sensor entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
        unique_id_suffix: str,
        translation_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{unique_id_suffix}"
        self._attr_translation_key = translation_key
        self._attr_device_info = get_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class KospelTemperatureSensor(KospelSensorEntity):
    """Representation of a Kospel temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
        unique_id_suffix: str,
        setting_name: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, entry_id, unique_id_suffix, unique_id_suffix)
        self._setting_name = setting_name

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        controller: HeaterController = self.coordinator.data
        return getattr(controller, self._setting_name, None)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelPressureSensor(KospelSensorEntity):
    """Representation of a Kospel pressure sensor."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_native_unit_of_measurement = UnitOfPressure.BAR
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the pressure sensor."""
        super().__init__(coordinator, entry_id, "pressure", "pressure")

    @property
    def native_value(self) -> float | None:
        """Return the pressure value."""
        controller: HeaterController = self.coordinator.data
        return getattr(controller, "pressure", None)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelPumpStatusSensor(KospelSensorEntity):
    """Representation of a Kospel pump status sensor."""

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
        unique_id_suffix: str,
        setting_name: str,
    ) -> None:
        """Initialize the pump status sensor."""
        super().__init__(coordinator, entry_id, unique_id_suffix, unique_id_suffix)
        self._setting_name = setting_name

    @property
    def native_value(self) -> str | None:
        """Return the pump status."""
        controller: HeaterController = self.coordinator.data
        status = getattr(controller, self._setting_name, None)
        if status is None:
            return None
        if hasattr(status, "value"):
            return status.value
        return str(status)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelValvePositionSensor(KospelSensorEntity):
    """Representation of a Kospel valve position sensor."""

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the valve position sensor."""
        super().__init__(coordinator, entry_id, "valve_position", "valve_position")

    @property
    def native_value(self) -> str | None:
        """Return the valve position."""
        controller: HeaterController = self.coordinator.data
        position = getattr(controller, "valve_position", None)
        if position is None:
            return None
        if hasattr(position, "value"):
            return position.value
        return str(position)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
