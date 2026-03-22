"""Climate entity for Kospel integration."""

import asyncio
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    get_device_info,
    get_device_identifier,
    get_refresh_delay_after_set,
)
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.registers.enums import HeaterMode, HeatingStatus
from kospel_cmi.controller.device import Ekco_M3

_LOGGER = logging.getLogger(__name__)


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
    """Representation of a Kospel heater climate entity (main device entity)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "heater"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = [mode.value for mode in HeaterMode]

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(coordinator.entry)
        self._attr_unique_id = f"{device_id}_climate"
        self._attr_device_info = get_device_info(coordinator.entry)

        self._preset_mode = self._attr_preset_modes[0]

    @property
    def _heater_mode(self) -> HeaterMode:
        """Current heater mode from the controller."""
        controller: Ekco_M3 = self.coordinator.data
        return controller.heater_mode or HeaterMode.OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        controller: Ekco_M3 = self.coordinator.data
        return controller.room_temperature

    @property
    def _is_manual_mode(self) -> bool:
        """Return True if manual mode is enabled."""
        return self._heater_mode == HeaterMode.MANUAL

    @property
    def supported_features(self) -> int:
        """Return supported features; target temperature always shown, but only settable in manual mode."""
        return (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TARGET_TEMPERATURE
        )

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature (always room_setpoint)."""
        controller: Ekco_M3 = self.coordinator.data
        return controller.room_setpoint

    @property
    def hvac_mode(self) -> HVACMode:
        """Current HVAC mode is based on the heater mode (represented in preset)."""
        return HVACMode.HEAT if self._heater_mode != HeaterMode.OFF else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """HVAC action is based on whether CO heating circuit is active."""
        controller: Ekco_M3 = self.coordinator.data
        co_status = getattr(controller, "co_heating_status", HeatingStatus.IDLE)
        return (
            HVACAction.HEATING
            if co_status == HeatingStatus.RUNNING
            else HVACAction.OFF
        )

    @property
    def preset_mode(self) -> str | None:
        """Current preset mode (heater_mode value)."""
        return self._heater_mode.value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_turn_on(self) -> None:
        """Turn heater on (set to HEAT mode)."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn heater off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)
        controller: Ekco_M3 = self.coordinator.data

        mode = HeaterMode.OFF if hvac_mode == HVACMode.OFF else HeaterMode.WINTER
        await controller.set_heater_mode(mode)
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature (only when manual mode is on)."""
        if not self._is_manual_mode:
            _LOGGER.debug("Ignoring set_temperature: manual mode is off")
            return
        controller: Ekco_M3 = self.coordinator.data
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await controller.set_manual_heating(temperature)
            self.async_write_ha_state()
            await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("Setting preset mode to %s", preset_mode)
        controller: Ekco_M3 = self.coordinator.data
        await controller.set_heater_mode(HeaterMode(preset_mode.lower()))
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
