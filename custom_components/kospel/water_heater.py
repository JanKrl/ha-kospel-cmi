"""Water heater entity for Kospel integration (DHW)."""

import asyncio
import logging
from typing import TypedDict, Unpack

from homeassistant.components.water_heater import (
    WaterHeaterEntity as HaWaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kospel_cmi import KospelError, WaterHeaterController
from kospel_cmi.registers.enums import DhwMode, WaterHeaterEnabled

from .const import (
    DOMAIN,
    get_device_identifier,
    get_device_info,
    get_refresh_delay_after_set,
)
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# HA water_heater operation modes (from homeassistant.const)
STATE_ECO = "eco"
STATE_PERFORMANCE = "performance"
STATE_OFF = "off"

OPERATION_LIST = [STATE_ECO, STATE_PERFORMANCE, STATE_OFF]
PROFILE_OPTIONS = ["manual", "profile_1", "profile_2", "profile_3"]

# DhwMode (0=economy, 1=anti-freeze, 2=comfort) to HA operation mode
_DHW_MODE_TO_HA: dict[int, str] = {
    DhwMode.ECONOMY: STATE_ECO,
    DhwMode.ANTI_FREEZE: STATE_OFF,
    DhwMode.COMFORT: STATE_PERFORMANCE,
}


class _WaterHeaterSetTemperatureKwargs(TypedDict, total=False):
    """Keyword arguments Home Assistant may pass to async_set_temperature."""

    temperature: float
    operation_mode: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel water heater platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WaterHeaterEntity(coordinator)])


class WaterHeaterEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], HaWaterHeaterEntity
):
    """Representation of a Kospel domestic hot water (DHW) entity.

    Adapts behavior via ``controller.water_heater_writable``:
    - Read-only controllers (e.g. EKCO.M3): displays current temperature, target
      temperature, and operation mode; write actions are no-ops.
    - Writable controllers (e.g. PPE.4): exposes manual/profile operation modes
      and writes target temperature / active profile to the device.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "dhw"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = PRECISION_WHOLE
    _attr_supported_features = (
        WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.TARGET_TEMPERATURE
    )

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(coordinator.entry)
        self._attr_unique_id = f"{device_id}_water_heater"
        self._attr_device_info = get_device_info(coordinator.entry)

    def _get_controller(self) -> WaterHeaterController:
        """Return the device controller from coordinator data."""
        return self.coordinator.data  # type: ignore[return-value]

    @property
    def min_temp(self) -> float:
        """Return the minimum target temperature."""
        controller = self._get_controller()
        return getattr(controller, "water_min_temperature", 30.0)

    @property
    def max_temp(self) -> float:
        """Return the maximum target temperature."""
        controller = self._get_controller()
        val = getattr(controller, "water_max_temperature", 65.0)
        return val if val is not None else 55.0

    @property
    def operation_list(self) -> list[str]:
        """Return the list of available operation modes."""
        controller = self._get_controller()
        if getattr(controller, "water_heater_writable", False):
            return PROFILE_OPTIONS
        return OPERATION_LIST

    async def async_set_temperature(
        self, **kwargs: Unpack[_WaterHeaterSetTemperatureKwargs]
    ) -> None:
        """Set target temperature when controller supports water heater writes."""
        controller = self._get_controller()
        if not getattr(controller, "water_heater_writable", False):
            _LOGGER.debug("Ignoring set_temperature on read-only DHW entity")
            return

        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        try:
            await controller.set_manual_heating(float(temperature))  # type: ignore[attr-defined]
        except KospelError as err:
            _LOGGER.error("Failed to set water heater temperature: %s", err)
            raise HomeAssistantError(
                f"Failed to set water heater temperature: {err}"
            ) from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set operation mode (active profile) when controller supports writes."""
        controller = self._get_controller()
        if not getattr(controller, "water_heater_writable", False):
            _LOGGER.debug(
                "Ignoring set_operation_mode on read-only DHW entity (mode=%s)",
                operation_mode,
            )
            return

        try:
            profile_index = PROFILE_OPTIONS.index(operation_mode)
        except ValueError as err:
            raise HomeAssistantError(
                f"Unsupported operation mode: {operation_mode}"
            ) from err

        try:
            await controller.set_active_profile(profile_index)  # type: ignore[attr-defined]
        except KospelError as err:
            _LOGGER.error("Failed to set water heater profile: %s", err)
            raise HomeAssistantError(
                f"Failed to set water heater profile: {err}"
            ) from err
        self.async_write_ha_state()
        await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
        await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float | None:
        """Return the current water temperature."""
        controller = self._get_controller()
        return controller.water_current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the live DHW supply setpoint from the device."""
        controller = self._get_controller()
        return controller.supply_setpoint

    @property
    def current_operation(self) -> str:
        """Return the current operation mode."""
        controller = self._get_controller()
        if getattr(controller, "water_heater_writable", False):
            active = getattr(controller, "active_profile", 0) or 0
            if 0 <= active < len(PROFILE_OPTIONS):
                return PROFILE_OPTIONS[active]
            return PROFILE_OPTIONS[0]

        if getattr(controller, "is_water_heater_enabled", None) != WaterHeaterEnabled.ENABLED:
            return STATE_OFF
        dhw_mode = getattr(controller, "dhw_mode", 0)
        return _DHW_MODE_TO_HA.get(dhw_mode or 0, STATE_ECO)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
