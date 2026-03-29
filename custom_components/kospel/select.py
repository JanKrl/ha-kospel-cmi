"""Select entities for Kospel integration (boiler max power index)."""

import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kospel_cmi.controller.device import Ekco_M3
from kospel_cmi.registers.enums import BoilerMaxPowerIndex

from .const import DOMAIN, get_device_info, get_device_identifier, get_refresh_delay_after_set
from .coordinator import KospelDataUpdateCoordinator

# Stable order 0..3 for HA options (do not rely on Enum iteration order).
_BOILER_MAX_POWER_ORDER: tuple[BoilerMaxPowerIndex, ...] = (
    BoilerMaxPowerIndex.KW_2,
    BoilerMaxPowerIndex.KW_4,
    BoilerMaxPowerIndex.KW_6,
    BoilerMaxPowerIndex.KW_8,
)

_OPTION_FOR_INDEX: dict[BoilerMaxPowerIndex, str] = {
    BoilerMaxPowerIndex.KW_2: "kw_2",
    BoilerMaxPowerIndex.KW_4: "kw_4",
    BoilerMaxPowerIndex.KW_6: "kw_6",
    BoilerMaxPowerIndex.KW_8: "kw_8",
}

_INDEX_FOR_OPTION: dict[str, BoilerMaxPowerIndex] = {
    v: k for k, v in _OPTION_FOR_INDEX.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel select entities."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KospelBoilerMaxPowerSelectEntity(coordinator, entry)])


class KospelBoilerMaxPowerSelectEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], SelectEntity
):
    """Boiler maximum power step (register 0b62); firmware updates kW display separately."""

    _attr_has_entity_name = True
    _attr_translation_key = "boiler_max_power"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = [_OPTION_FOR_INDEX[idx] for idx in _BOILER_MAX_POWER_ORDER]

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the boiler max power select.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry (device info and refresh delay options).
        """
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_boiler_max_power"
        self._attr_device_info = get_device_info(entry)

    @property
    def current_option(self) -> str | None:
        """Return the selected option slug, or None if the device index is unknown."""
        controller: Ekco_M3 = self.coordinator.data
        index = controller.boiler_max_power_index
        if index is None:
            return None
        return _OPTION_FOR_INDEX.get(index)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Write the selected power step to the heater and refresh coordinator data."""
        chosen = _INDEX_FOR_OPTION.get(option)
        if chosen is None:
            raise ValueError(f"Invalid option: {option}")

        controller: Ekco_M3 = self.coordinator.data
        await controller.set_boiler_max_power_index(chosen)
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
