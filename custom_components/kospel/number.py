"""Number entities for Kospel integration (room and DHW preset temperatures)."""

import asyncio
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kospel_cmi import KospelError
from kospel_cmi.controller.device import EkcoM3

from .const import DOMAIN, get_device_info, get_device_identifier, get_refresh_delay_after_set
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

ROOM_PRESET_TEMP_MIN = 10.0
ROOM_PRESET_TEMP_MAX = 25.0
DHW_PRESET_TEMP_MIN = 30.0
DHW_PRESET_TEMP_MAX = 80.0
OUTSIDE_THRESHOLD_MIN = 0
OUTSIDE_THRESHOLD_MAX = 30
PRESET_TEMP_STEP = 0.1

# (translation_key / controller property name / async setter name / min temp / max temp)
_PRESET_ENTITIES: list[tuple[str, str, str, float, float]] = [
    (
        "room_temperature_economy",
        "room_temperature_economy",
        "set_room_temperature_economy",
        ROOM_PRESET_TEMP_MIN,
        ROOM_PRESET_TEMP_MAX,
    ),
    (
        "room_temperature_comfort",
        "room_temperature_comfort",
        "set_room_temperature_comfort",
        ROOM_PRESET_TEMP_MIN,
        ROOM_PRESET_TEMP_MAX,
    ),
    (
        "room_temperature_comfort_plus",
        "room_temperature_comfort_plus",
        "set_room_temperature_comfort_plus",
        ROOM_PRESET_TEMP_MIN,
        ROOM_PRESET_TEMP_MAX,
    ),
    (
        "room_temperature_comfort_minus",
        "room_temperature_comfort_minus",
        "set_room_temperature_comfort_minus",
        ROOM_PRESET_TEMP_MIN,
        ROOM_PRESET_TEMP_MAX,
    ),
    (
        "dhw_temperature_economy",
        "cwu_temperature_economy",
        "set_water_economy_temperature",
        DHW_PRESET_TEMP_MIN,
        DHW_PRESET_TEMP_MAX,
    ),
    (
        "dhw_temperature_comfort",
        "cwu_temperature_comfort",
        "set_water_comfort_temperature",
        DHW_PRESET_TEMP_MIN,
        DHW_PRESET_TEMP_MAX,
    ),
    (
        "outside_temperature_off",
        "outside_temperature_off",
        "set_outside_temperature_off",
        OUTSIDE_THRESHOLD_MIN,
        OUTSIDE_THRESHOLD_MAX,
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel number entities."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = [
        KospelPresetNumberEntity(
            coordinator,
            entry,
            translation_key,
            value_attr,
            setter_name,
            min_temp,
            max_temp,
        )
        for translation_key, value_attr, setter_name, min_temp, max_temp in _PRESET_ENTITIES
    ]
    async_add_entities(entities)


class KospelPresetNumberEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], NumberEntity
):
    """Preset temperature (room / DHW) as a read/write number.

    Shown under device **Configuration** with other system-style setpoints
    (e.g. max boiler power select).
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = PRESET_TEMP_STEP
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
        translation_key: str,
        value_attr: str,
        setter_name: str,
        min_temp: float,
        max_temp: float,
        step: float = PRESET_TEMP_STEP,
    ) -> None:
        """Initialize the preset temperature number entity.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry (device info and refresh delay options).
            translation_key: Translation key used for human-friendly entity naming.
            value_attr: EkcoM3 property name to read from the controller.
            setter_name: Name of the async setter on EkcoM3.
            min_temp: Minimum supported temperature for this preset.
            max_temp: Maximum supported temperature for this preset.
            step: Supported step size for this preset.
        """
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_{value_attr}"
        self._attr_translation_key = translation_key
        self._attr_device_info = get_device_info(entry)
        self._attr_native_min_value = min_temp
        self._attr_native_max_value = max_temp
        self._attr_native_step = step
        self._value_attr = value_attr
        self._setter_name = setter_name

    @property
    def native_value(self) -> float | None:
        """Return the current preset temperature from the controller."""
        controller: EkcoM3 = self.coordinator.data
        return getattr(controller, self._value_attr, None)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    async def async_set_native_value(self, value: float) -> None:
        """Write preset temperature to the heater and refresh coordinator data."""
        controller: EkcoM3 = self.coordinator.data
        setter = getattr(controller, self._setter_name)
        try:
            await setter(value)
        except KospelError as err:
            _LOGGER.error("Failed to set %s: %s", self._setter_name, err)
            raise HomeAssistantError(
                f"Failed to set room preset ({self._setter_name}): {err}"
            ) from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
