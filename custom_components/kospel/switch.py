"""Switch entities for Kospel integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.registers.enums import ManualMode, WaterHeaterEnabled
from kospel_cmi.controller.api import HeaterController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel switch platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        KospelManualModeSwitch(coordinator, entry.entry_id),
        KospelWaterHeaterSwitch(coordinator, entry.entry_id),
    ]

    async_add_entities(entities)


class KospelSwitchEntity(CoordinatorEntity[KospelDataUpdateCoordinator], SwitchEntity):
    """Base class for Kospel switch entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
        unique_id_suffix: str,
        translation_key: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{unique_id_suffix}"
        self._attr_translation_key = translation_key
        self._attr_device_info = get_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class KospelManualModeSwitch(KospelSwitchEntity):
    """Representation of a Kospel manual mode switch."""

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the manual mode switch."""
        super().__init__(coordinator, entry_id, "manual_mode", "manual_mode")

    @property
    def is_on(self) -> bool:
        """Return if manual mode is enabled."""
        controller: HeaterController = self.coordinator.data
        manual_mode = getattr(controller, "is_manual_mode_enabled", None)
        if manual_mode is None:
            return False
        # ManualMode is an enum, check if it's ENABLED
        return manual_mode == ManualMode.ENABLED

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn manual mode on."""
        controller: HeaterController = self.coordinator.data
        controller.is_manual_mode_enabled = ManualMode.ENABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn manual mode off."""
        controller: HeaterController = self.coordinator.data
        controller.is_manual_mode_enabled = ManualMode.DISABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelWaterHeaterSwitch(KospelSwitchEntity):
    """Representation of a Kospel water heater switch."""

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the water heater switch."""
        super().__init__(coordinator, entry_id, "water_heater", "water_heater")

    @property
    def is_on(self) -> bool:
        """Return if water heater is enabled."""
        controller: HeaterController = self.coordinator.data
        water_heater = getattr(controller, "is_water_heater_enabled", None)
        if water_heater is None:
            return False
        # WaterHeaterEnabled is an enum, check if it's ENABLED
        return water_heater == WaterHeaterEnabled.ENABLED

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn water heater on."""
        controller: HeaterController = self.coordinator.data
        controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn water heater off."""
        controller: HeaterController = self.coordinator.data
        controller.is_water_heater_enabled = WaterHeaterEnabled.DISABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
