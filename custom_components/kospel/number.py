"""Number entities for Kospel integration (room preset temperatures)."""

import asyncio

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kospel_cmi.controller.device import Ekco_M3

from .const import DOMAIN, get_device_info, get_device_identifier, get_refresh_delay_after_set
from .coordinator import KospelDataUpdateCoordinator

ROOM_PRESET_TEMP_MIN = 10.0
ROOM_PRESET_TEMP_MAX = 25.0
ROOM_PRESET_TEMP_STEP = 0.1

# (translation_key / unique_id suffix / Ekco_M3 property name, async setter name)
_ROOM_PRESET_ENTITIES: list[tuple[str, str]] = [
    ("room_temperature_economy", "set_room_temperature_economy"),
    ("room_temperature_comfort", "set_room_temperature_comfort"),
    ("room_temperature_comfort_plus", "set_room_temperature_comfort_plus"),
    ("room_temperature_comfort_minus", "set_room_temperature_comfort_minus"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel number entities."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = [
        KospelRoomPresetNumberEntity(coordinator, entry, prop_key, setter_name)
        for prop_key, setter_name in _ROOM_PRESET_ENTITIES
    ]
    async_add_entities(entities)


class KospelRoomPresetNumberEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], NumberEntity
):
    """Room preset temperature (economy / comfort / ±) as a read/write number."""

    _attr_has_entity_name = True
    _attr_native_min_value = ROOM_PRESET_TEMP_MIN
    _attr_native_max_value = ROOM_PRESET_TEMP_MAX
    _attr_native_step = ROOM_PRESET_TEMP_STEP
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
        value_attr: str,
        setter_name: str,
    ) -> None:
        """Initialize the room preset number entity.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry (device info and refresh delay options).
            value_attr: Ekco_M3 property name (same as translation_key / unique suffix).
            setter_name: Name of the async setter on Ekco_M3 (e.g. set_room_temperature_economy).
        """
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_{value_attr}"
        self._attr_translation_key = value_attr
        self._attr_device_info = get_device_info(entry)
        self._value_attr = value_attr
        self._setter_name = setter_name

    @property
    def native_value(self) -> float | None:
        """Return the current preset temperature from the controller."""
        controller: Ekco_M3 = self.coordinator.data
        return getattr(controller, self._value_attr, None)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_native_value(self, value: float) -> None:
        """Write preset temperature to the heater and refresh coordinator data."""
        controller: Ekco_M3 = self.coordinator.data
        setter = getattr(controller, self._setter_name)
        await setter(value)
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
