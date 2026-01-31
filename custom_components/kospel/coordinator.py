"""DataUpdateCoordinator for Kospel integration."""

import logging

import aiohttp

from .controller.api import HeaterController
from .kospel.simulator import is_simulation_mode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL, CONF_SIMULATION_MODE

_LOGGER = logging.getLogger(__name__)


class KospelDataUpdateCoordinator(DataUpdateCoordinator[HeaterController]):
    """Class to manage fetching data from the Kospel heater."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: aiohttp.ClientSession,
        heater_controller: HeaterController,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=True,
        )
        self.entry = entry
        self.session = session
        self.heater_controller = heater_controller
        self._simulation_mode = entry.data.get(
            CONF_SIMULATION_MODE, is_simulation_mode()
        )

    # async def _async_setup(self) -> None:
    #     """Setup the coordinator."""
    #     await self.heater_controller.refresh()
    #     return self.heater_controller

    async def _async_update_data(self) -> HeaterController:
        """Fetch data from the heater controller.

        Returns:
            HeaterController instance (entities access settings via coordinator.data.property_name)
        """
        try:
            await self.heater_controller.refresh()
            return self.heater_controller
        except Exception as err:
            _LOGGER.error("Error fetching heater data: %s", err)
            raise UpdateFailed(f"Error communicating with heater: {err}") from err
