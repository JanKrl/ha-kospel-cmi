"""Config flow for Kospel integration."""

from ipaddress import ip_interface
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from kospel_cmi import discover_devices, probe_device

from .const import (
    DOMAIN,
    CONF_BACKEND_TYPE,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    CONF_SERIAL_NUMBER,
    CONF_SIMULATION_MODE,
    DEFAULT_SUBNETS,
    BACKEND_TYPE_HTTP,
    BACKEND_TYPE_YAML,
    make_unique_id,
)


class CannotConnect(Exception):
    """Raised when connection to heater fails."""


async def validate_http_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate HTTP backend input (heater IP and device ID).

    Probes the device via probe_device to verify connectivity and that
    the device_id exists on the module. Returns title and serial_number on success.

    Returns:
        Dict with "title" and optionally "serial_number" for the config entry.

    Raises:
        CannotConnect: When probe fails or device_id is not found on the module.
    """
    heater_ip = data[CONF_HEATER_IP].strip()
    device_id = data[CONF_DEVICE_ID]

    async with aiohttp.ClientSession() as session:
        info = await probe_device(session, heater_ip)
    if info is None:
        raise CannotConnect()
    if device_id not in info.device_ids:
        raise CannotConnect()

    serial = info.serial_number
    return {
        "title": f"Kospel Heater {heater_ip} (device {device_id})",
        "serial_number": serial,
    }


async def _get_subnets_to_scan(hass: HomeAssistant) -> list[str]:
    """Get subnets to scan from Network integration or fallback to defaults."""
    try:
        adapters = await network.async_get_adapters(hass)
    except Exception:
        return DEFAULT_SUBNETS

    subnets: set[str] = set()
    for adapter in adapters:
        if not adapter.get("enabled"):
            continue
        for ipv4 in adapter.get("ipv4", []):
            try:
                iface = ip_interface(
                    f"{ipv4['address']}/{ipv4['network_prefix']}"
                )
                subnets.add(str(iface.network))
            except (ValueError, KeyError):
                continue

    return list(subnets) if subnets else DEFAULT_SUBNETS


class KospelConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self._backend_type: str | None = None
        self._discovered_devices: list[tuple[Any, int]] = []  # (KospelDeviceInfo, device_id)

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

        # HTTP: show connection method choice (Discover vs Manual)
        return self.async_show_form(
            step_id="http_method",
            data_schema=vol.Schema(
                {
                    vol.Required("http_method", default="discover"): vol.In(
                        {
                            "discover": "option_discover",
                            "manual": "option_manual",
                        }
                    ),
                }
            ),
        )

    async def async_step_http_method(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle HTTP connection method: Discover or Manual."""
        if user_input is None:
            return self.async_show_form(
                step_id="http_method",
                data_schema=vol.Schema(
                    {
                        vol.Required("http_method", default="discover"): vol.In(
                            {
                                "discover": "option_discover",
                                "manual": "option_manual",
                            }
                        ),
                    }
                ),
            )

        if user_input["http_method"] == "discover":
            return await self.async_step_discover()
        return self.async_show_form(
            step_id="http",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HEATER_IP): str,
                    vol.Required(CONF_DEVICE_ID, default=65): int,
                }
            ),
        )

    async def _async_run_discovery(self) -> FlowResult:
        """Run network discovery and return progress_done to transition to result step."""
        try:
            subnets = await _get_subnets_to_scan(self.hass)
            all_devices: list[tuple[Any, int]] = []

            async with aiohttp.ClientSession() as session:
                for subnet in subnets:
                    devices = await discover_devices(
                        session, subnet, timeout=3.0, concurrency_limit=20
                    )
                    for info in devices:
                        for device_id in info.device_ids:
                            all_devices.append((info, device_id))

            self._discovered_devices = all_devices
            return self.async_show_progress_done(next_step_id="discover_result")
        except Exception:
            self._discovered_devices = []
            return self.async_show_progress_done(next_step_id="discover_result")

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Scan network for Kospel devices."""
        if user_input and user_input.get("action") == "manual":
            return self.async_show_form(
                step_id="http",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HEATER_IP): str,
                        vol.Required(CONF_DEVICE_ID, default=65): int,
                    }
                ),
            )

        progress_task = self.hass.async_create_task(self._async_run_discovery())
        return self.async_show_progress(
            step_id="discover",
            progress_action="discover",
            progress_task=progress_task,
        )

    async def async_step_discover_result(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle discovery result: show device list or retry form."""
        if not self._discovered_devices:
            return self.async_show_form(
                step_id="discover",
                data_schema=vol.Schema(
                    {
                        vol.Required("action", default="manual"): vol.In(
                            {
                                "retry": "option_retry",
                                "manual": "option_manual",
                            }
                        ),
                    }
                ),
                errors={"base": "no_devices_found"},
            )

        # Build device selection options
        options: dict[str, str] = {}
        for info, device_id in self._discovered_devices:
            devices = getattr(info, "devices", None) or []
            model = devices[0].model_name if devices else "?"
            unique_id = make_unique_id(info.serial_number, device_id)
            options[unique_id] = (
                f"{info.host} — {info.serial_number} (dev {device_id}, {model})"
            )

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(options),
                }
            ),
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection from discovered list."""
        if user_input is None:
            return self.async_abort(reason="unknown")

        selected_unique_id = user_input["device"]
        info = None
        device_id = None
        for dev_info, dev_id in self._discovered_devices:
            if make_unique_id(dev_info.serial_number, dev_id) == selected_unique_id:
                info = dev_info
                device_id = dev_id
                break

        if info is None or device_id is None:
            return self.async_abort(reason="unknown")

        await self.async_set_unique_id(selected_unique_id)
        self._abort_if_unique_id_configured()

        heater_ip = info.host.split(":")[0] if ":" in info.host else info.host

        return self.async_create_entry(
            title=f"Kospel Heater {heater_ip} (device {device_id})",
            data={
                CONF_BACKEND_TYPE: BACKEND_TYPE_HTTP,
                CONF_HEATER_IP: heater_ip,
                CONF_DEVICE_ID: device_id,
                CONF_SERIAL_NUMBER: info.serial_number,
            },
        )

    async def async_step_http(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle HTTP backend connection details (manual entry)."""
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
            except CannotConnect:
                errors["base"] = "cannot_connect"
                info = {}
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

        serial = info.get("serial_number")
        unique_id = make_unique_id(serial, device_id) if serial else None
        if unique_id:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

        entry_data: dict[str, Any] = {
            CONF_BACKEND_TYPE: BACKEND_TYPE_HTTP,
            CONF_HEATER_IP: heater_ip,
            CONF_DEVICE_ID: device_id,
        }
        if serial is not None:
            entry_data[CONF_SERIAL_NUMBER] = serial

        return self.async_create_entry(
            title=info.get("title", f"Kospel Heater {heater_ip}"),
            data=entry_data,
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
