"""Climate entity for Kospel integration."""

import asyncio
import logging
from typing import Final, TypedDict, Unpack

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import PRESET_NONE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    get_device_info,
    get_device_identifier,
    get_refresh_delay_after_set,
)
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi import KospelError
from kospel_cmi.registers.enums import HeaterMode, HeatingStatus
from kospel_cmi.controller.device import EkcoM3

_LOGGER = logging.getLogger(__name__)

_AUTO_HEATER_MODES: Final[frozenset[HeaterMode]] = frozenset(
    {
        HeaterMode.SUMMER,
        HeaterMode.WINTER,
        HeaterMode.PARTY,
        HeaterMode.VACATION,
    }
)


class _ClimateSetTemperatureKwargs(TypedDict, total=False):
    """Keyword arguments Home Assistant may pass to async_set_temperature."""

    temperature: float


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
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_preset_modes = [
        PRESET_NONE,
        HeaterMode.WINTER.value,
        HeaterMode.SUMMER.value,
        HeaterMode.PARTY.value,
        HeaterMode.VACATION.value,
    ]

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(coordinator.entry)
        self._attr_unique_id = f"{device_id}_climate"
        self._attr_device_info = get_device_info(coordinator.entry)

    @property
    def _heater_mode(self) -> HeaterMode:
        """Current heater mode from the controller."""
        controller: EkcoM3 = self.coordinator.data
        return controller.heater_mode or HeaterMode.OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        controller: EkcoM3 = self.coordinator.data
        return controller.room_temperature

    @property
    def supported_features(self) -> int:
        """Return supported features.

        Target temperature is always advertised so the room setpoint stays visible
        in every HVAC mode. Changing it still only applies in Heat (manual) mode;
        see ``async_set_temperature``.
        """
        return (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TARGET_TEMPERATURE
        )

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature (room setpoint from the controller)."""
        controller: EkcoM3 = self.coordinator.data
        return controller.room_setpoint

    @property
    def hvac_mode(self) -> HVACMode:
        """Map device heater mode to Home Assistant HVAC modes."""
        mode = self._heater_mode
        if mode == HeaterMode.OFF:
            return HVACMode.OFF
        if mode == HeaterMode.MANUAL:
            return HVACMode.HEAT
        return HVACMode.AUTO

    @property
    def hvac_action(self) -> HVACAction:
        """HVAC action is based on whether CO heating circuit is active."""
        controller: EkcoM3 = self.coordinator.data
        co_status = controller.co_heating_status
        return (
            HVACAction.HEATING
            if co_status == HeatingStatus.RUNNING
            else HVACAction.OFF
        )

    @property
    def preset_mode(self) -> str | None:
        """Return the active auto program preset, or ``none`` when not applicable."""
        mode = self._heater_mode
        if mode in (HeaterMode.OFF, HeaterMode.MANUAL):
            return PRESET_NONE
        if mode in _AUTO_HEATER_MODES:
            return mode.value
        return PRESET_NONE

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    async def async_turn_on(self) -> None:
        """Turn the heater on using automatic (winter) heating.

        Uses AUTO HVAC mode with the device's default winter program so existing
        automations that only turn the entity on keep prior seasonal behaviour.
        """
        await self.async_set_hvac_mode(HVACMode.AUTO)

    async def async_turn_off(self) -> None:
        """Turn heater off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode on the device.

        Args:
            hvac_mode: Target mode. OFF turns the heater off, HEAT selects manual
                room control, AUTO selects automatic programs (default winter when
                only the mode is changed without a preset).
        """
        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)
        controller: EkcoM3 = self.coordinator.data

        if hvac_mode == HVACMode.OFF:
            mode = HeaterMode.OFF
        elif hvac_mode == HVACMode.HEAT:
            mode = HeaterMode.MANUAL
        elif hvac_mode == HVACMode.AUTO:
            mode = HeaterMode.WINTER
        else:
            raise HomeAssistantError(f"Unsupported HVAC mode: {hvac_mode}")

        try:
            await controller.set_heater_mode(mode)
        except KospelError as err:
            _LOGGER.error("Failed to set heater mode: %s", err)
            raise HomeAssistantError(f"Failed to set heater mode: {err}") from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Unpack[_ClimateSetTemperatureKwargs]) -> None:
        """Set the manual heating target temperature.

        Raises:
            HomeAssistantError: If the device is not in manual (heat) mode or the
                write fails.
        """
        if self._heater_mode != HeaterMode.MANUAL:
            raise HomeAssistantError(
                "Target temperature can only be set in Heat (manual) mode. "
                "Switch HVAC mode to Heat first."
            )
        controller: EkcoM3 = self.coordinator.data
        temperature = kwargs.get("temperature")
        if temperature is not None:
            try:
                await controller.set_manual_heating(temperature)
            except KospelError as err:
                _LOGGER.error("Failed to set manual heating: %s", err)
                raise HomeAssistantError(
                    f"Failed to set manual heating: {err}"
                ) from err
            self.async_write_ha_state()
            await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the automatic program (winter, summer, party, vacation).

        Args:
            preset_mode: Program preset, or ``none`` for a no-op when already idle.

        Raises:
            HomeAssistantError: If the preset is unknown or the device rejects the change.
        """
        _LOGGER.debug("Setting preset mode to %s", preset_mode)
        if preset_mode == PRESET_NONE:
            return

        if preset_mode not in self._attr_preset_modes:
            raise HomeAssistantError(f"Unsupported preset mode: {preset_mode}")

        controller: EkcoM3 = self.coordinator.data
        try:
            await controller.set_heater_mode(HeaterMode(preset_mode.lower()))
        except KospelError as err:
            _LOGGER.error("Failed to set preset mode: %s", err)
            raise HomeAssistantError(f"Failed to set preset mode: {err}") from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
