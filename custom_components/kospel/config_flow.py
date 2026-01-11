"""Config flow for Kospel integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    CONF_SIMULATION_MODE,
)
from .kospel.simulator import is_simulation_mode


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # In simulation mode, validation is skipped
    simulation_mode = data.get(CONF_SIMULATION_MODE, False)
    if simulation_mode:
        return {"title": "Kospel Heater (Simulation Mode)"}

    # Future: Validate real connection here
    # For now, just return success
    return {"title": f"Kospel Heater {data[CONF_HEATER_IP]}"}


class KospelConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            # Initial form display - default simulation mode to env var state
            simulation_mode_default = is_simulation_mode()
            data_schema = vol.Schema(
                {
                    vol.Optional(
                        CONF_SIMULATION_MODE, default=simulation_mode_default
                    ): bool,
                    vol.Optional(CONF_HEATER_IP, default=""): str,
                    vol.Optional(CONF_DEVICE_ID, default=""): int,
                }
                if simulation_mode_default
                else {
                    vol.Optional(CONF_SIMULATION_MODE, default=False): bool,
                    vol.Required(CONF_HEATER_IP): str,
                    vol.Required(CONF_DEVICE_ID, default=65): int,
                }
            )

            return self.async_show_form(
                step_id="user",
                data_schema=data_schema,
                description_placeholders={
                    "simulation_note": "Simulation mode is active. No actual heater connection will be made."
                    if simulation_mode_default
                    else ""
                },
            )

        errors = {}

        # Get simulation mode from user input (checkbox value)
        simulation_mode = user_input.get(CONF_SIMULATION_MODE, False)

        # In simulation mode, use placeholder values if not provided
        if simulation_mode:
            heater_ip = user_input.get(CONF_HEATER_IP, "127.0.0.1")
            device_id = user_input.get(CONF_DEVICE_ID, 65)
        else:
            heater_ip = user_input[CONF_HEATER_IP]
            device_id = user_input[CONF_DEVICE_ID]
            # Future: Validate IP format and device ID range

        try:
            info = await validate_input(
                self.hass,
                {
                    CONF_HEATER_IP: heater_ip,
                    CONF_DEVICE_ID: device_id,
                    CONF_SIMULATION_MODE: simulation_mode,
                },
            )
        except Exception:
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_SIMULATION_MODE, default=simulation_mode
                        ): bool,
                        vol.Optional(CONF_HEATER_IP, default=heater_ip): str,
                        vol.Optional(CONF_DEVICE_ID, default=device_id): int,
                    }
                    if simulation_mode
                    else {
                        vol.Optional(CONF_SIMULATION_MODE, default=False): bool,
                        vol.Required(CONF_HEATER_IP, default=heater_ip): str,
                        vol.Required(CONF_DEVICE_ID, default=device_id): int,
                    }
                ),
                errors=errors,
            )

        # Store simulation mode status in config entry data
        return self.async_create_entry(
            title=info["title"],
            data={
                CONF_HEATER_IP: heater_ip,
                CONF_DEVICE_ID: device_id,
                CONF_SIMULATION_MODE: simulation_mode,
            },
        )
