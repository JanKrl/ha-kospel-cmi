"""Water heater entity for Kospel integration (CWU / DHW)."""

import logging
from typing import TypedDict, Unpack

from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info, get_device_identifier
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.registers.enums import CwuMode, WaterHeaterEnabled
from kospel_cmi.controller.device import EkcoM3

_LOGGER = logging.getLogger(__name__)

# HA water_heater operation modes (from homeassistant.const)
STATE_ECO = "eco"
STATE_PERFORMANCE = "performance"
STATE_OFF = "off"

OPERATION_LIST = [STATE_ECO, STATE_PERFORMANCE, STATE_OFF]

# CwuMode (0=economy, 1=anti-freeze, 2=comfort) to HA operation mode
_CWU_MODE_TO_HA: dict[int, str] = {
    CwuMode.ECONOMY: STATE_ECO,
    CwuMode.ANTI_FREEZE: STATE_OFF,
    CwuMode.COMFORT: STATE_PERFORMANCE,
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
    async_add_entities([KospelWaterHeaterEntity(coordinator)])


class KospelWaterHeaterEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], WaterHeaterEntity
):
    """Representation of a Kospel domestic hot water (CWU/DHW) entity.

    Read-only for writes: displays current temperature, target temperature, and
    operation mode. Target/operation controls on this entity are intentionally
    no-ops; DHW/CWU setpoints and modes follow the device and the climate entity
    (HVAC / auto programs), not the water heater card.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "dhw"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_LIST
    _attr_min_temp = 30.0
    _attr_max_temp = 65.0
    # OPERATION_MODE and TARGET_TEMPERATURE are declared so Home Assistant shows
    # current operation and temperatures in the UI. Writes are ignored here by design:
    # DHW/CWU behaviour is driven by the device and by the climate entity (HVAC mode
    # and auto presets; see climate.async_set_*).
    _attr_supported_features = (
        WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.TARGET_TEMPERATURE
    )

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(coordinator.entry)
        self._attr_unique_id = f"{device_id}_water_heater"
        self._attr_device_info = get_device_info(coordinator.entry)

    def _get_controller(self) -> EkcoM3:
        """Return the device controller from coordinator data."""
        return self.coordinator.data

    async def async_set_temperature(
        self, **kwargs: Unpack[_WaterHeaterSetTemperatureKwargs]
    ) -> None:
        """Ignore temperature writes; DHW setpoints are changed on the device or via climate."""
        _LOGGER.debug("Ignoring set_temperature on read-only DHW entity")

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Ignore operation mode writes; CWU mode is not controlled here."""
        _LOGGER.debug(
            "Ignoring set_operation_mode on read-only DHW entity (mode=%s)",
            operation_mode,
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current water temperature."""
        controller = self._get_controller()
        return controller.water_current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the live CWU supply setpoint from the device (register 0b2f).

        Reflects firmware output including daily programs; not derived from
        static economy/comfort preset registers. ``None`` if the value is
        unavailable (no substitution).
        """
        controller = self._get_controller()
        return controller.supply_setpoint

    @property
    def current_operation(self) -> str:
        """Return the current operation mode from device cwu_mode."""
        controller = self._get_controller()
        if controller.is_water_heater_enabled != WaterHeaterEnabled.ENABLED:
            return STATE_OFF
        cwu_mode = controller.cwu_mode
        return _CWU_MODE_TO_HA.get(cwu_mode or 0, STATE_ECO)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.communication_ok

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
