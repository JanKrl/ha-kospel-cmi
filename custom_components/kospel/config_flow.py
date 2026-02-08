"""Config flow for Kospel integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_BACKEND_TYPE,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    CONF_SIMULATION_MODE,
    BACKEND_TYPE_HTTP,
    BACKEND_TYPE_YAML,
)


async def validate_http_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate HTTP backend input (heater IP and device ID).

    Returns:
        Dict with "title" for the config entry title.
    """
    # Basic validation: IP format and device ID range could be added here
    heater_ip = data[CONF_HEATER_IP]
    device_id = data[CONF_DEVICE_ID]
    return {"title": f"Kospel Heater {heater_ip} (device {device_id})"}


class KospelConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self._backend_type: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: choose backend type (HTTP or YAML)."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_BACKEND_TYPE,
                            default=BACKEND_TYPE_HTTP,
                        ): vol.In(
                            {
                                BACKEND_TYPE_HTTP: "option_http",
                                BACKEND_TYPE_YAML: "option_yaml",
                            }
                        ),
                    }
                ),
                description_placeholders={
                    "yaml_path": "custom_components/kospel/data/state.yaml",
                },
            )

        self._backend_type = user_input[CONF_BACKEND_TYPE]

        if self._backend_type == BACKEND_TYPE_YAML:
            return self.async_create_entry(
                title="Kospel Heater (YAML / development)",
                data={
                    CONF_BACKEND_TYPE: BACKEND_TYPE_YAML,
                },
            )

        # HTTP: show connection details step
        return self.async_show_form(
            step_id="http",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HEATER_IP): str,
                    vol.Required(CONF_DEVICE_ID, default=65): int,
                }
            ),
        )

    async def async_step_http(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle HTTP backend connection details."""
        if user_input is None:
            return self.async_show_form(
                step_id="http",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HEATER_IP): str,
                        vol.Required(CONF_DEVICE_ID, default=65): int,
                    }
                ),
            )

        errors: dict[str, str] = {}
        heater_ip = user_input[CONF_HEATER_IP].strip()
        device_id = user_input[CONF_DEVICE_ID]

        if device_id < 1 or device_id > 255:
            errors["base"] = "invalid_device_id"

        if not errors:
            try:
                info = await validate_http_input(
                    self.hass,
                    {
                        CONF_HEATER_IP: heater_ip,
                        CONF_DEVICE_ID: device_id,
                    },
                )
            except Exception:
                errors["base"] = "unknown"
                info = {}

        if errors:
            return self.async_show_form(
                step_id="http",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HEATER_IP, default=heater_ip): str,
                        vol.Required(CONF_DEVICE_ID, default=device_id): int,
                    }
                ),
                errors=errors,
            )

        return self.async_create_entry(
            title=info.get("title", f"Kospel Heater {heater_ip}"),
            data={
                CONF_BACKEND_TYPE: BACKEND_TYPE_HTTP,
                CONF_HEATER_IP: heater_ip,
                CONF_DEVICE_ID: device_id,
            },
        )

    async def async_migrate_entry(
        self, hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> bool:
        """Migrate config entry from version 1 to 2 (backend_type instead of simulation_mode)."""
        if entry.version >= 2:
            return True

        data = dict(entry.data)
        if CONF_BACKEND_TYPE not in data:
            data[CONF_BACKEND_TYPE] = (
                BACKEND_TYPE_YAML
                if data.get(CONF_SIMULATION_MODE, False)
                else BACKEND_TYPE_HTTP
            )
            if CONF_SIMULATION_MODE in data:
                del data[CONF_SIMULATION_MODE]

        hass.config_entries.async_update_entry(entry, data=data, version=2)
        return True
