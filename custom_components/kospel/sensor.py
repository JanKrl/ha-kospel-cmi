"""Sensor entities for Kospel integration."""

from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info, get_device_identifier
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.controller.device import Ekco_M3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel sensor platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    temperature_sensors = [
        ("room_setpoint", "room_setpoint"),
        ("supply_setpoint", "supply_setpoint"),
    ]

    for unique_id_suffix, attr_name in temperature_sensors:
        entities.append(
            KospelTemperatureSensor(
                coordinator,
                entry,
                unique_id_suffix,
                lambda c, name=attr_name: getattr(c, name, None),
            )
        )

    # Pressure sensor
    entities.append(KospelPressureSensor(coordinator, entry))

    # Power sensor
    entities.append(KospelPowerSensor(coordinator, entry))

    # Configured max boiler power limit (kW from device, exposed as W)
    entities.append(KospelMaxPowerLimitSensor(coordinator, entry))

    # Heating status sensors: (unique_id_suffix, setting_name)
    entities.append(
        KospelHeatingStatusSensor(coordinator, entry, "co_heating", "co_heating_status")
    )
    entities.append(
        KospelHeatingStatusSensor(
            coordinator, entry, "cwu_heating", "cwu_heating_status"
        )
    )
    entities.append(KospelValvePositionSensor(coordinator, entry))

    async_add_entities(entities)


class KospelSensorEntity(CoordinatorEntity[KospelDataUpdateCoordinator], SensorEntity):
    """Base class for Kospel sensor entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
        unique_id_suffix: str,
        translation_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_{unique_id_suffix}"
        self._attr_translation_key = translation_key
        self._attr_device_info = get_device_info(entry)

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
        entry: ConfigEntry,
        unique_id_suffix: str,
        value_getter: Callable[[Ekco_M3], float | None],
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, entry, unique_id_suffix, unique_id_suffix)
        self._value_getter = value_getter

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        controller: Ekco_M3 = self.coordinator.data
        return self._value_getter(controller)

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
        entry: ConfigEntry,
    ) -> None:
        """Initialize the pressure sensor."""
        super().__init__(coordinator, entry, "pressure", "pressure")

    @property
    def native_value(self) -> float | None:
        """Return the pressure value."""
        controller: Ekco_M3 = self.coordinator.data
        return controller.pressure

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelPowerSensor(KospelSensorEntity):
    """Representation of instantaneous power in watts.

    The library reports power in kW; this sensor exposes native W for the
    Energy dashboard and long-term statistics.
    """

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator, entry, "power", "power")

    @property
    def native_value(self) -> float | None:
        """Return the power value in W (device reports kW)."""
        controller: Ekco_M3 = self.coordinator.data
        power_kw = controller.power
        if power_kw is None:
            return None
        return power_kw * 1000.0

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelMaxPowerLimitSensor(KospelSensorEntity):
    """Configured maximum boiler power in watts.

    Reads kW from register 0b34 and exposes W (same idea as ``KospelPowerSensor``).
    Uses ``EntityCategory.DIAGNOSTIC`` because Home Assistant rejects CONFIG on
    sensor entities; the max-power *select* remains CONFIG.
    """

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the max power limit sensor."""
        super().__init__(coordinator, entry, "max_power_limit", "max_power_limit")

    @property
    def native_value(self) -> float | None:
        """Return the configured max power in W (register 0b34, kW × 1000)."""
        controller: Ekco_M3 = self.coordinator.data
        limit_kw = controller.boiler_max_power_kw
        if limit_kw is None:
            return None
        return float(limit_kw) * 1000.0

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelHeatingStatusSensor(KospelSensorEntity):
    """Representation of a Kospel heating status sensor (CO or CWU circuit)."""

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
        unique_id_suffix: str,
        setting_name: str,
    ) -> None:
        """Initialize the heating status sensor."""
        super().__init__(coordinator, entry, unique_id_suffix, unique_id_suffix)
        self._setting_name = setting_name

    @property
    def native_value(self) -> str | None:
        """Return the heating status (RUNNING, IDLE, DISABLED)."""
        controller: Ekco_M3 = self.coordinator.data
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
        entry: ConfigEntry,
    ) -> None:
        """Initialize the valve position sensor."""
        super().__init__(coordinator, entry, "valve_position", "valve_position")

    @property
    def native_value(self) -> str | None:
        """Return the valve position."""
        controller: Ekco_M3 = self.coordinator.data
        position = controller.valve_position
        if position is None:
            return None
        if hasattr(position, "value"):
            return position.value
        return str(position)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
