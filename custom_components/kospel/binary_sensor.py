"""Binary sensor entities for Kospel integration (connectivity)."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info, get_device_identifier
from .coordinator import KospelDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel binary sensor entities."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KospelConnectivityBinarySensor(coordinator, entry)])


class KospelConnectivityBinarySensor(
    CoordinatorEntity[KospelDataUpdateCoordinator], BinarySensorEntity
):
    """Hub connectivity: on when communication is OK (debounced failed polls)."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the connectivity binary sensor."""
        super().__init__(coordinator)
        device_id = get_device_identifier(entry)
        self._attr_unique_id = f"{device_id}_connectivity"
        self._attr_device_info = get_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        """Return True when the heater is reachable within debounce threshold."""
        return self.coordinator.communication_ok

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
