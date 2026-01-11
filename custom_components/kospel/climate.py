"""Climate entity for Kospel integration."""

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator

from .registers.enums import HeaterMode
from .controller.api import HeaterController


def _map_heater_mode_to_hvac_mode(heater_mode: HeaterMode) -> HVACMode:
    """Map HeaterMode enum to HVACMode."""
    mapping = {
        HeaterMode.OFF: HVACMode.OFF,
        HeaterMode.WINTER: HVACMode.HEAT,
        HeaterMode.SUMMER: HVACMode.HEAT,  # Summer mode still provides heat (water only)
    }
    return mapping.get(heater_mode, HVACMode.OFF)


def _map_hvac_mode_to_heater_mode(hvac_mode: HVACMode) -> HeaterMode:
    """Map HVACMode to HeaterMode enum."""
    if hvac_mode == HVACMode.OFF:
        return HeaterMode.OFF
    # Default to WINTER for HEAT mode (preset can override)
    return HeaterMode.WINTER


def _map_heater_mode_to_preset(heater_mode: HeaterMode) -> str:
    """Map HeaterMode enum to preset mode string."""
    mapping = {
        HeaterMode.OFF: "off",
        HeaterMode.WINTER: "winter",
        HeaterMode.SUMMER: "summer",
    }
    return mapping.get(heater_mode, "off")


def _map_preset_to_heater_mode(preset: str) -> HeaterMode:
    """Map preset mode string to HeaterMode enum."""
    mapping = {
        "off": HeaterMode.OFF,
        "winter": HeaterMode.WINTER,
        "summer": HeaterMode.SUMMER,
    }
    return mapping.get(preset, HeaterMode.OFF)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel climate platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KospelClimateEntity(coordinator)])


class KospelClimateEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], ClimateEntity
):
    """Representation of a Kospel heater climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["winter", "summer", "off"]

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_climate"
        self._attr_name = "Kospel Heater"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        controller: HeaterController = self.coordinator.data
        # Use room temperature comfort as current temperature
        return getattr(controller, "room_temperature_comfort", None)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        controller: HeaterController = self.coordinator.data
        return getattr(controller, "manual_temperature", None)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        controller: HeaterController = self.coordinator.data
        heater_mode = getattr(controller, "heater_mode", None)
        if heater_mode is None:
            return HVACMode.OFF
        return _map_heater_mode_to_hvac_mode(heater_mode)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        controller: HeaterController = self.coordinator.data
        heater_mode = getattr(controller, "heater_mode", None)
        if heater_mode is None:
            return "off"
        return _map_heater_mode_to_preset(heater_mode)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        controller: HeaterController = self.coordinator.data
        temperature = kwargs.get("temperature")
        if temperature is not None:
            controller.manual_temperature = temperature
            await controller.save()
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        controller: HeaterController = self.coordinator.data
        heater_mode = _map_hvac_mode_to_heater_mode(hvac_mode)
        controller.heater_mode = heater_mode
        await controller.save()
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        controller: HeaterController = self.coordinator.data
        heater_mode = _map_preset_to_heater_mode(preset_mode)
        controller.heater_mode = heater_mode
        await controller.save()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
