"""Number entities for Kospel integration (room, DHW, and profile preset temperatures)."""

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

from kospel_cmi import KospelError, Ppe4
from kospel_cmi.controller.device import EkcoM3

from .const import (
    DOMAIN,
    get_device_identifier,
    get_device_info,
    get_refresh_delay_after_set,
)
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

ROOM_PRESET_TEMP_MIN = 10.0
ROOM_PRESET_TEMP_MAX = 25.0
DHW_PRESET_TEMP_MIN = 30.0
DHW_PRESET_TEMP_MAX = 80.0
OUTSIDE_THRESHOLD_MIN = 0
OUTSIDE_THRESHOLD_MAX = 30
PRESET_TEMP_STEP = 0.1

# (unique_id_suffix / controller property name & translation key / async setter name / min temp / max temp)
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
        # Keep old cwu_ unique_id to preserve existing HA entity registry entries
        "cwu_temperature_economy",
        "dhw_temperature_economy",
        "set_water_economy_temperature",
        DHW_PRESET_TEMP_MIN,
        DHW_PRESET_TEMP_MAX,
    ),
    (
        # Keep old cwu_ unique_id to preserve existing HA entity registry entries
        "cwu_temperature_comfort",
        "dhw_temperature_comfort",
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
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel number entities."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if hasattr(coordinator.data, "get_profile_temperature"):
        entities: list[NumberEntity] = [
            ProfileNumberEntity(coordinator, entry, profile)
            for profile in (1, 2, 3)
        ]
    else:
        entities = [
            PresetNumberEntity(
                coordinator,
                entry,
                unique_id_suffix,
                value_attr,
                setter_name,
                min_temp,
                max_temp,
            )
            for unique_id_suffix, value_attr, setter_name, min_temp, max_temp in _PRESET_ENTITIES
        ]
    async_add_entities(entities)


class PresetNumberEntity(
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
        unique_id_suffix: str,
        value_attr: str,
        setter_name: str,
        min_temp: float,
        max_temp: float,
        step: float = PRESET_TEMP_STEP,
    ) -> None:
        """Initialize the preset temperature number entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_{unique_id_suffix}"
        self._attr_translation_key = value_attr
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


class ProfileNumberEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], NumberEntity
):
    """Profile temperature preset (PPE.4 profiles 1..3)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
        profile: int,
    ) -> None:
        """Initialize the profile temperature number entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        key = f"profile_{profile}_temperature"
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = get_device_info(entry)
        self._profile = profile
        controller: Ppe4 = coordinator.data
        self._attr_native_min_value = getattr(controller, "water_min_temperature", 20.0)
        self._attr_native_max_value = getattr(controller, "water_max_temperature", 55.0)

    @property
    def native_max_value(self) -> float:
        """Return dynamic max temperature from the controller."""
        controller: Ppe4 = self.coordinator.data
        val = getattr(controller, "water_max_temperature", 55.0)
        return val if val is not None else 55.0

    @property
    def native_value(self) -> float | None:
        """Return the current profile temperature from the controller."""
        controller: Ppe4 = self.coordinator.data
        return controller.get_profile_temperature(self._profile)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    async def async_set_native_value(self, value: float) -> None:
        """Write profile temperature to the heater and refresh coordinator data."""
        controller: Ppe4 = self.coordinator.data
        try:
            await controller.set_profile_temperature(self._profile, value)
        except KospelError as err:
            _LOGGER.error("Failed to set profile %d temperature: %s", self._profile, err)
            raise HomeAssistantError(
                f"Failed to set profile {self._profile} temperature: {err}"
            ) from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
