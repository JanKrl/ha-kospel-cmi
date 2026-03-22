"""DataUpdateCoordinator for Kospel integration."""

import logging

from kospel_cmi.controller.device import Ekco_M3

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class KospelDataUpdateCoordinator(DataUpdateCoordinator[Ekco_M3]):
    """Class to manage fetching data from the Kospel heater."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        heater_controller: Ekco_M3,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            entry: Config entry for this integration.
            heater_controller: Ekco_M3 device (backed by HTTP or YAML backend).
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=True,
        )
        self.entry = entry
        self.heater_controller = heater_controller

    async def _async_update_data(self) -> Ekco_M3:
        """Fetch data from the heater controller.

        Returns:
            Ekco_M3 instance (entities access settings via coordinator.data).
        """
        try:
            await self.heater_controller.refresh()
            return self.heater_controller
        except Exception as err:
            _LOGGER.error("Error fetching heater data: %s", err)
            raise UpdateFailed(f"Error communicating with heater: {err}") from err
