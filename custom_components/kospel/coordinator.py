"""DataUpdateCoordinator for Kospel integration."""

from __future__ import annotations

import logging

from kospel_cmi import (
    IncompleteRegisterRefreshError,
    KospelConnectionError,
    KospelError,
    RegisterReadError,
)
from kospel_cmi.controller.device import EkcoM3

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COMMUNICATION_FAILURE_THRESHOLD, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class KospelDataUpdateCoordinator(DataUpdateCoordinator[EkcoM3]):
    """Class to manage fetching data from the Kospel heater."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        heater_controller: EkcoM3,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            entry: Config entry for this integration.
            heater_controller: EkcoM3 device (backed by HTTP or YAML backend).
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=True,
        )
        self.entry = entry
        self.heater_controller = heater_controller
        self._failure_streak: int = 0

    @property
    def communication_ok(self) -> bool:
        """True if communication is OK (debounced; see ``COMMUNICATION_FAILURE_THRESHOLD``)."""
        return self._failure_streak < COMMUNICATION_FAILURE_THRESHOLD

    @callback
    def _async_refresh_finished(self) -> None:
        """Track consecutive failures for debounced availability."""
        if self.last_update_success:
            self._failure_streak = 0
        else:
            self._failure_streak += 1

    async def _async_update_data(self) -> EkcoM3:
        """Fetch data from the heater controller.

        Uses the library strict refresh (see ``EkcoM3(..., strict_refresh=True)``):
        incomplete batches raise ``IncompleteRegisterRefreshError`` without mutating cache.

        Returns:
            EkcoM3 instance (entities access settings via coordinator.data).

        Raises:
            UpdateFailed: On transport/read errors or incomplete strict refresh.
        """
        try:
            await self.heater_controller.refresh()
        except IncompleteRegisterRefreshError as err:
            _LOGGER.warning(
                "Incomplete heater register batch (strict): missing %s",
                ", ".join(sorted(err.missing_registers)),
            )
            raise UpdateFailed(f"Incomplete heater data: {err}") from err
        except (KospelConnectionError, RegisterReadError) as err:
            _LOGGER.debug("Heater read failed: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with heater: {err}") from err
        except KospelError as err:
            _LOGGER.error("Unexpected Kospel error during refresh: %s", err)
            raise UpdateFailed(f"Error communicating with heater: {err}") from err

        return self.heater_controller
