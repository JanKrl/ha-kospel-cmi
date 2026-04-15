"""Config flow for Kospel integration."""

import asyncio
import logging
from ipaddress import ip_interface
from ipaddress import ip_network
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from kospel_cmi import discover_devices, probe_device

from .const import (
    DOMAIN,
    CONF_BACKEND_TYPE,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    CONF_REFRESH_DELAY_AFTER_SET,
    CONF_SERIAL_NUMBER,
    CONF_SIMULATION_MODE,
    DEFAULT_REFRESH_DELAY_AFTER_SET,
    KOSPEL_MAC_PREFIXES,
    BACKEND_TYPE_HTTP,
    BACKEND_TYPE_YAML,
    REFRESH_DELAY_MAX,
    REFRESH_DELAY_MIN,
    make_unique_id,
)

LOGGER = logging.getLogger(__name__)
DISCOVERY_TIMEOUT_SECONDS = 90.0
MAX_NETWORK_SCAN_HOSTS = 1024


class CannotConnect(Exception):
    """Raised when connection to heater fails."""


_DHCP_CANDIDATE_HOSTS: set[str] = set()


def _normalize_mac(mac: str | None) -> str | None:
    """Return lowercase hex-only MAC string or None for invalid values."""
    if not mac:
        return None
    normalized = "".join(char for char in mac.lower() if char in "0123456789abcdef")
    return normalized if len(normalized) >= 9 else None


def _is_kospel_mac(mac: str | None) -> bool:
    """Return True when MAC belongs to known Kospel vendor prefixes."""
    normalized = _normalize_mac(mac)
    if normalized is None:
        return False
    return any(normalized.startswith(prefix) for prefix in KOSPEL_MAC_PREFIXES)


async def _discover_by_kospel_mac(
    session: aiohttp.ClientSession,
) -> list[tuple[Any, int]]:
    """Discover devices from DHCP auto-discovered Kospel candidates."""
    if not _DHCP_CANDIDATE_HOSTS:
        LOGGER.debug("Auto discovery has no DHCP candidate hosts")
        return []

    LOGGER.debug(
        "Auto discovery probing DHCP candidates: %s",
        sorted(_DHCP_CANDIDATE_HOSTS),
    )
    probe_results = await asyncio.gather(
        *[probe_device(session, host) for host in sorted(_DHCP_CANDIDATE_HOSTS)],
        return_exceptions=True,
    )

    discovered: list[tuple[Any, int]] = []
    for result in probe_results:
        if isinstance(result, Exception) or result is None:
            continue
        for device_id in result.device_ids:
            discovered.append((result, device_id))
    LOGGER.debug("Auto discovery found %s device candidates", len(discovered))
    return discovered


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
    """Get subnets to scan from enabled IPv4 adapters."""
    try:
        adapters = await network.async_get_adapters(hass)
    except Exception:
        LOGGER.exception("Could not read network adapters for subnet scan")
        return []

    subnets: set[str] = set()
    for adapter in adapters:
        if not adapter.get("enabled"):
            continue
        for ipv4 in adapter.get("ipv4", []):
            try:
                iface = ip_interface(f"{ipv4['address']}/{ipv4['network_prefix']}")
                subnets.add(str(iface.network))
            except (ValueError, KeyError):
                continue

    result = sorted(subnets)
    LOGGER.debug("Network scan subnets resolved: %s", result)
    return result


async def _discover_by_network_scan(
    hass: HomeAssistant, session: aiohttp.ClientSession
) -> list[tuple[Any, int]]:
    """Discover devices by scanning all IPv4 subnets from network adapters."""
    subnets = await _get_subnets_to_scan(hass)
    if not subnets:
        LOGGER.warning("Network scan has no enabled IPv4 subnets to scan")
        return []

    discovered: list[tuple[Any, int]] = []
    for subnet in subnets:
        try:
            network_obj = ip_network(subnet, strict=False)
            host_count = max(0, int(network_obj.num_addresses) - 2)
        except ValueError:
            LOGGER.warning("Skipping invalid subnet from adapter list: %s", subnet)
            continue

        if host_count > MAX_NETWORK_SCAN_HOSTS:
            LOGGER.warning(
                "Skipping large subnet %s (%s hosts > limit %s)",
                subnet,
                host_count,
                MAX_NETWORK_SCAN_HOSTS,
            )
            continue

        LOGGER.info("Network scan probing subnet=%s", subnet)
        devices = await discover_devices(
            session, subnet, timeout=3.0, concurrency_limit=20
        )
        for info in devices:
            for device_id in info.device_ids:
                discovered.append((info, device_id))
    LOGGER.debug("Network scan found %s device candidates", len(discovered))
    return discovered


class KospelConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self._backend_type: str | None = None
        self._discovered_devices: list[
            tuple[Any, int]
        ] = []  # (KospelDeviceInfo, device_id)
        self._discovery_method: str = "auto_discovery"
        self._discover_task: asyncio.Task[None] | None = None

    async def async_step_dhcp(self, discovery_info: dict[str, Any]) -> FlowResult:
        """Handle discovery from Home Assistant DHCP integration."""
        mac_address = discovery_info.get("macaddress")
        if not _is_kospel_mac(mac_address):
            LOGGER.debug(
                "Ignoring DHCP discovery with non-Kospel MAC: %s",
                mac_address,
            )
            return self.async_abort(reason="not_kospel_device")

        host = discovery_info.get("ip")
        if not isinstance(host, str):
            LOGGER.warning("DHCP discovery missing IP field: %s", discovery_info)
            return self.async_abort(reason="unknown")

        _DHCP_CANDIDATE_HOSTS.add(host)
        LOGGER.info(
            "Stored DHCP discovery candidate host=%s (total_candidates=%s)",
            host,
            len(_DHCP_CANDIDATE_HOSTS),
        )

        async with aiohttp.ClientSession() as session:
            info = await probe_device(session, host)
        if info is None or not info.device_ids:
            LOGGER.warning("DHCP candidate probe failed for host=%s", host)
            return self.async_abort(reason="cannot_connect")

        if len(info.device_ids) == 1:
            device_id = info.device_ids[0]
            unique_id = make_unique_id(info.serial_number, device_id)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            heater_ip = info.host.split(":")[0] if ":" in info.host else info.host
            LOGGER.info(
                "DHCP discovery created entry host=%s device_id=%s",
                heater_ip,
                device_id,
            )
            return self.async_create_entry(
                title=f"Kospel Heater {heater_ip} (device {device_id})",
                data={
                    CONF_BACKEND_TYPE: BACKEND_TYPE_HTTP,
                    CONF_HEATER_IP: heater_ip,
                    CONF_DEVICE_ID: device_id,
                    CONF_SERIAL_NUMBER: info.serial_number,
                },
            )

        self._discovered_devices = [(info, device_id) for device_id in info.device_ids]
        LOGGER.info(
            "DHCP discovery found multiple device IDs at host=%s: %s",
            host,
            info.device_ids,
        )
        return await self.async_step_discover_result()

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

        # HTTP: show connection method choice.
        return self.async_show_form(
            step_id="http_method",
            data_schema=vol.Schema(
                {
                    vol.Required("http_method", default="auto_discovery"): vol.In(
                        {
                            "auto_discovery": "option_auto_discovery",
                            "network_scan": "option_network_scan",
                            "manual": "option_manual",
                        }
                    ),
                }
            ),
        )

    async def async_step_http_method(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle HTTP connection method selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="http_method",
                data_schema=vol.Schema(
                    {
                        vol.Required("http_method", default="auto_discovery"): vol.In(
                            {
                                "auto_discovery": "option_auto_discovery",
                                "network_scan": "option_network_scan",
                                "manual": "option_manual",
                            }
                        ),
                    }
                ),
            )

        method = user_input["http_method"]
        if method in {"auto_discovery", "network_scan"}:
            self._discover_task = None
            self._discovery_method = method
            LOGGER.info("HTTP discovery method selected: %s", method)
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

    async def _async_run_discovery(self) -> None:
        """Run discovery task and store results for discover_result step."""
        try:
            LOGGER.info("Starting discovery run via method=%s", self._discovery_method)
            all_devices: list[tuple[Any, int]] = []

            async with aiohttp.ClientSession() as session:
                if self._discovery_method == "network_scan":
                    all_devices = await asyncio.wait_for(
                        _discover_by_network_scan(self.hass, session),
                        timeout=DISCOVERY_TIMEOUT_SECONDS,
                    )
                else:
                    all_devices = await asyncio.wait_for(
                        _discover_by_kospel_mac(session),
                        timeout=DISCOVERY_TIMEOUT_SECONDS,
                    )

            self._discovered_devices = all_devices
            LOGGER.debug(
                "Discovery completed via method=%s found_devices=%s",
                self._discovery_method,
                len(self._discovered_devices),
            )
        except asyncio.TimeoutError:
            LOGGER.warning(
                "Discovery timed out after %s seconds via method=%s",
                DISCOVERY_TIMEOUT_SECONDS,
                self._discovery_method,
            )
            self._discovered_devices = []
        except Exception:
            LOGGER.exception("Discovery failed via method=%s", self._discovery_method)
            self._discovered_devices = []

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Scan network for Kospel devices."""
        LOGGER.warning(
            "Discovery UI step entered (method=%s)",
            self._discovery_method,
        )
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

        # Avoid progress-step edge cases when auto discovery has no DHCP candidates.
        if (
            self._discovery_method == "auto_discovery"
            and not _DHCP_CANDIDATE_HOSTS
            and self._discover_task is None
        ):
            LOGGER.info(
                "Auto discovery has no DHCP candidates, showing result directly"
            )
            self._discovered_devices = []
            return await self.async_step_discover_result()

        if self._discover_task is None:
            LOGGER.debug("Creating new discovery progress task")
            self._discover_task = self.hass.async_create_task(self._async_run_discovery())
        elif not self._discover_task.done():
            LOGGER.debug("Reusing running discovery progress task")
        else:
            LOGGER.debug("Discovery progress task is done, moving to result step")
            self._discover_task = None
            return self.async_show_progress_done(next_step_id="discover_result")
        return self.async_show_progress(
            step_id="discover",
            progress_action="discover",
            progress_task=self._discover_task,
        )

    async def async_step_discover_result(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle discovery result: show device list or retry form."""
        # Clear cached task only after progress step transitions to result.
        self._discover_task = None
        if not self._discovered_devices:
            LOGGER.debug(
                "Discovery result empty for method=%s",
                self._discovery_method,
            )
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
        LOGGER.debug("Discovery result offers %s selectable devices", len(options))

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "KospelOptionsFlowHandler":
        """Get the options flow for this handler."""
        return KospelOptionsFlowHandler(config_entry)


class KospelOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle Kospel integration options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        default_delay = self.options.get(
            CONF_REFRESH_DELAY_AFTER_SET, DEFAULT_REFRESH_DELAY_AFTER_SET
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REFRESH_DELAY_AFTER_SET,
                        default=default_delay,
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=REFRESH_DELAY_MIN, max=REFRESH_DELAY_MAX),
                    ),
                }
            ),
        )
