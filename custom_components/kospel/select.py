"""Select entities for Kospel integration (boiler max power index)."""

import asyncio
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
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
    def options(self) -> list[str]:
        """Return a set of selectable options dynamically from the heater."""
        controller: EkcoM3 = self.coordinator.data
        return [str(int(kw)) for kw in controller.available_boiler_max_power_settings]

    @property
    def current_option(self) -> str | None:
        """Return the selected kW step as a string (e.g. '4'), or None if unknown."""
        controller: EkcoM3 = self.coordinator.data
        index = controller.boiler_max_power_index
        if index is None:
            return None
        available = controller.available_boiler_max_power_settings
        if index < len(available):
            return str(int(available[index]))
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    async def async_select_option(self, option: str) -> None:
        """Write the selected power step to the heater and refresh coordinator data."""
        controller: EkcoM3 = self.coordinator.data
        available_strs = [str(int(kw)) for kw in controller.available_boiler_max_power_settings]
        
        try:
            chosen = available_strs.index(option)
        except ValueError:
            raise ValueError(f"Invalid option: {option}")

        try:
            await controller.set_boiler_max_power_index(chosen)
        except KospelError as err:
            _LOGGER.error("Failed to set boiler max power: %s", err)
            raise HomeAssistantError(
                f"Failed to set boiler max power: {err}"
            ) from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
