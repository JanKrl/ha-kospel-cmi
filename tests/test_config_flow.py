"""Tests for config flow and related helpers.

Uses sys.modules mocking to avoid requiring homeassistant at test runtime,
since homeassistant has strict dependency constraints that conflict with
the project's aiohttp version.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

# Mock homeassistant before importing integration modules.
# homeassistant must be a module (have __path__) for "from homeassistant.x import y" to work.
class _HAModule:
    __path__ = []
    __file__ = ""
    __name__ = "homeassistant"


_ha = _HAModule()
sys.modules["homeassistant"] = _ha


class _ConfigFlowBase:
    """Minimal ConfigFlow stand-in (required by KospelConfigFlowHandler)."""

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Accept domain= and other kwargs from HA ConfigFlow pattern."""
        super().__init_subclass__()


class _OptionsFlowWithConfigEntryBase:
    """Minimal OptionsFlowWithConfigEntry stand-in for options flow tests."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = config_entry.options if config_entry.options is not None else {}

    def async_create_entry(self, title, data):
        return {"type": "create_entry", "data": data}

    def async_show_form(self, step_id, data_schema):
        return {"type": "show_form", "step_id": step_id, "data_schema": data_schema}


_config_entries_mock = MagicMock()
_config_entries_mock.ConfigFlow = _ConfigFlowBase
_config_entries_mock.OptionsFlowWithConfigEntry = _OptionsFlowWithConfigEntryBase
sys.modules["homeassistant.config_entries"] = _config_entries_mock
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.network"] = MagicMock()
sys.modules["homeassistant.components.climate"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.switch"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
_ha_core_mock = MagicMock()
# Real identity decorator so @callback on async_get_options_flow is not a MagicMock.
_ha_core_mock.callback = lambda f: f
sys.modules["homeassistant.core"] = _ha_core_mock
sys.modules["homeassistant.data_entry_flow"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

# DeviceInfo is typically a TypedDict - use a simple dict-like
def _device_info(**kwargs):
    return kwargs


sys.modules["homeassistant.helpers.entity"].DeviceInfo = _device_info

from custom_components.kospel.const import (
    CONF_DEVICE_ID,
    CONF_REFRESH_DELAY_AFTER_SET,
    CONF_SERIAL_NUMBER,
    DEFAULT_REFRESH_DELAY_AFTER_SET,
    REFRESH_DELAY_MAX,
    REFRESH_DELAY_MIN,
    make_unique_id,
    get_device_identifier,
    get_device_info,
)
from custom_components.kospel.config_flow import (
    CannotConnect,
    KospelConfigFlowHandler,
    KospelOptionsFlowHandler,
    validate_http_input,
    _DHCP_CANDIDATE_HOSTS,
    _discover_by_kospel_mac,
    _discover_by_network_scan,
    _get_subnets_to_scan,
    _is_kospel_mac,
    _normalize_mac,
)


class TestMakeUniqueId:
    """Tests for make_unique_id."""

    def test_returns_serial_and_device_id(self) -> None:
        """make_unique_id combines serial_number and device_id."""
        assert make_unique_id("mi01_00006047", 65) == "mi01_00006047_65"

    def test_handles_different_device_ids(self) -> None:
        """make_unique_id works for various device IDs."""
        assert make_unique_id("sn123", 1) == "sn123_1"
        assert make_unique_id("sn123", 255) == "sn123_255"


class TestGetDeviceIdentifier:
    """Tests for get_device_identifier."""

    def test_uses_serial_and_device_id_when_available(self) -> None:
        """get_device_identifier uses make_unique_id when serial in entry."""
        entry = MagicMock()
        entry.data = {CONF_SERIAL_NUMBER: "mi01_001", CONF_DEVICE_ID: 65}
        entry.entry_id = "abc-123"
        assert get_device_identifier(entry) == "mi01_001_65"

    def test_fallback_to_entry_id_when_no_serial(self) -> None:
        """get_device_identifier falls back to entry_id for legacy entries."""
        entry = MagicMock()
        entry.data = {CONF_DEVICE_ID: 65}
        entry.entry_id = "legacy-uuid"
        assert get_device_identifier(entry) == "legacy-uuid"

    def test_fallback_when_device_id_missing(self) -> None:
        """get_device_identifier falls back when device_id missing."""
        entry = MagicMock()
        entry.data = {CONF_SERIAL_NUMBER: "sn"}
        entry.entry_id = "uuid"
        assert get_device_identifier(entry) == "uuid"


class TestGetDeviceInfo:
    """Tests for get_device_info."""

    def test_identifiers_use_unique_id_when_serial_present(self) -> None:
        """DeviceInfo.identifiers uses make_unique_id when serial available."""
        entry = MagicMock()
        entry.data = {CONF_SERIAL_NUMBER: "mi01_001", CONF_DEVICE_ID: 65}
        entry.entry_id = "abc"
        info = get_device_info(entry)
        assert ("kospel", "mi01_001_65") in info["identifiers"]

    def test_identifiers_use_entry_id_for_legacy(self) -> None:
        """DeviceInfo.identifiers uses entry_id for legacy entries."""
        entry = MagicMock()
        entry.data = {}
        entry.entry_id = "legacy-uuid"
        info = get_device_info(entry)
        assert ("kospel", "legacy-uuid") in info["identifiers"]


class TestValidateHttpInput:
    """Tests for validate_http_input."""

    @pytest.mark.asyncio
    async def test_returns_title_and_serial_on_success(self) -> None:
        """validate_http_input returns title and serial_number when probe succeeds."""
        mock_info = MagicMock()
        mock_info.device_ids = [65]
        mock_info.serial_number = "mi01_00006047"

        with patch(
            "custom_components.kospel.config_flow.probe_device",
            new_callable=AsyncMock,
            return_value=mock_info,
        ):
            result = await validate_http_input(
                MagicMock(),
                {"heater_ip": "192.168.1.100", "device_id": 65},
            )
        assert result["title"] == "Kospel Heater 192.168.1.100 (device 65)"
        assert result["serial_number"] == "mi01_00006047"

    @pytest.mark.asyncio
    async def test_raises_cannot_connect_when_probe_returns_none(self) -> None:
        """validate_http_input raises CannotConnect when probe returns None."""
        with patch(
            "custom_components.kospel.config_flow.probe_device",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(CannotConnect):
                await validate_http_input(
                    MagicMock(),
                    {"heater_ip": "192.168.1.100", "device_id": 65},
                )

    @pytest.mark.asyncio
    async def test_raises_cannot_connect_when_device_id_not_in_module(
        self,
    ) -> None:
        """validate_http_input raises CannotConnect when device_id not in device_ids."""
        mock_info = MagicMock()
        mock_info.device_ids = [66, 67]
        mock_info.serial_number = "mi01_001"

        with patch(
            "custom_components.kospel.config_flow.probe_device",
            new_callable=AsyncMock,
            return_value=mock_info,
        ):
            with pytest.raises(CannotConnect):
                await validate_http_input(
                    MagicMock(),
                    {"heater_ip": "192.168.1.100", "device_id": 65},
                )


class TestGetSubnetsToScan:
    """Tests for _get_subnets_to_scan."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_network_fails(self) -> None:
        """_get_subnets_to_scan returns empty when network raises."""
        hass = MagicMock()
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            side_effect=Exception("Network not loaded"),
        ):
            result = await _get_subnets_to_scan(hass)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_subnets_from_adapters(self) -> None:
        """_get_subnets_to_scan builds subnets from Network adapters."""
        hass = MagicMock()
        adapters = [
            {
                "enabled": True,
                "ipv4": [
                    {"address": "192.168.1.100", "network_prefix": 24},
                ],
            },
        ]
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            return_value=adapters,
        ):
            result = await _get_subnets_to_scan(hass)
        assert "192.168.1.0/24" in result

    @pytest.mark.asyncio
    async def test_skips_disabled_adapters(self) -> None:
        """_get_subnets_to_scan skips disabled adapters."""
        hass = MagicMock()
        adapters = [
            {"enabled": False, "ipv4": [{"address": "10.0.0.1", "network_prefix": 24}]},
        ]
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            return_value=adapters,
        ):
            result = await _get_subnets_to_scan(hass)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_ipv4(self) -> None:
        """_get_subnets_to_scan returns empty when no IPv4 addresses."""
        hass = MagicMock()
        adapters = [{"enabled": True, "ipv4": []}]
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            return_value=adapters,
        ):
            result = await _get_subnets_to_scan(hass)
        assert result == []


class TestMacFilteringHelpers:
    """Tests for MAC normalization and Kospel MAC filtering."""

    def test_normalize_mac_removes_separators_and_lowercases(self) -> None:
        """_normalize_mac returns lowercase hex string without separators."""
        assert _normalize_mac("70:B3:D5:24:9A:BC") == "70b3d5249abc"

    def test_is_kospel_mac_matches_registered_prefix(self) -> None:
        """_is_kospel_mac returns True for known Kospel vendor prefix."""
        assert _is_kospel_mac("70-B3-D5-24-9F-00")

    def test_is_kospel_mac_rejects_other_vendors(self) -> None:
        """_is_kospel_mac returns False for non-Kospel prefixes."""
        assert not _is_kospel_mac("AA:BB:CC:DD:EE:FF")

class TestDiscoverByKospelMac:
    """Tests for discovery path using DHCP candidate hosts."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_dhcp_candidates(self) -> None:
        """_discover_by_kospel_mac returns empty when no DHCP candidates exist."""
        _DHCP_CANDIDATE_HOSTS.clear()
        result = await _discover_by_kospel_mac(MagicMock())
        assert result == []

    @pytest.mark.asyncio
    async def test_discovers_from_dhcp_candidate_hosts(self) -> None:
        """_discover_by_kospel_mac probes DHCP hosts and expands device IDs."""
        _DHCP_CANDIDATE_HOSTS.clear()
        _DHCP_CANDIDATE_HOSTS.update({"192.168.1.10"})
        session = MagicMock()
        discovered = MagicMock()
        discovered.device_ids = [65, 66]

        with patch(
            "custom_components.kospel.config_flow.probe_device",
            new_callable=AsyncMock,
            return_value=discovered,
        ) as mock_probe:
            result = await _discover_by_kospel_mac(session)

        mock_probe.assert_awaited_once_with(session, "192.168.1.10")
        assert result == [(discovered, 65), (discovered, 66)]


class TestConfigFlowDiscoveryFallback:
    """Tests for config flow fallback behavior in discovery."""

    @pytest.mark.asyncio
    async def test_run_discovery_falls_back_to_subnet_scan(self) -> None:
        """_async_run_discovery uses network scan when method is network_scan."""
        handler = KospelConfigFlowHandler()
        handler.hass = MagicMock()
        handler._discovery_method = "network_scan"
        handler.async_show_progress_done = lambda next_step_id: {
            "type": "progress_done",
            "next_step_id": next_step_id,
        }

        found = MagicMock()
        found.device_ids = [65]

        with patch(
            "custom_components.kospel.config_flow._discover_by_network_scan",
            new_callable=AsyncMock,
            return_value=[(found, 65)],
        ) as mock_discover:
            result = await handler._async_run_discovery()

        mock_discover.assert_awaited_once()
        assert handler._discovered_devices == [(found, 65)]
        assert result is None

    @pytest.mark.asyncio
    async def test_discover_step_transitions_when_task_done(self) -> None:
        """async_step_discover returns progress_done when task already finished."""
        handler = KospelConfigFlowHandler()
        handler.hass = MagicMock()
        handler._discover_task = MagicMock()
        handler._discover_task.done.return_value = True
        handler.async_show_progress_done = lambda next_step_id: {
            "type": "progress_done",
            "next_step_id": next_step_id,
        }

        result = await handler.async_step_discover()

        assert result == {"type": "progress_done", "next_step_id": "discover_result"}
        assert handler._discover_task is None

    @pytest.mark.asyncio
    async def test_discover_result_with_no_devices_shows_manual_retry(self) -> None:
        """async_step_discover_result shows no-devices form with manual/retry choices."""
        handler = KospelConfigFlowHandler()
        handler._discovered_devices = []
        handler.async_show_form = lambda step_id, data_schema, errors=None: {
            "type": "show_form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors,
        }

        result = await handler.async_step_discover_result()

        assert result["type"] == "show_form"
        assert result["step_id"] == "discover"
        assert result["errors"] == {"base": "no_devices_found"}

    @pytest.mark.asyncio
    async def test_run_discovery_uses_auto_discovery_by_default(self) -> None:
        """_async_run_discovery uses MAC candidate auto discovery by default."""
        handler = KospelConfigFlowHandler()
        handler.hass = MagicMock()
        handler.async_show_progress_done = lambda next_step_id: {
            "type": "progress_done",
            "next_step_id": next_step_id,
        }
        found = MagicMock()
        found.device_ids = [65]

        with patch(
            "custom_components.kospel.config_flow._discover_by_kospel_mac",
            new_callable=AsyncMock,
            return_value=[(found, 65)],
        ) as mock_auto:
            await handler._async_run_discovery()

        mock_auto.assert_awaited_once()


class TestDhcpDiscoveryStep:
    """Tests for Home Assistant DHCP discovery flow step."""

    @pytest.mark.asyncio
    async def test_dhcp_ignores_non_kospel_mac(self) -> None:
        """async_step_dhcp aborts for non-Kospel MAC addresses."""
        handler = KospelConfigFlowHandler()
        handler.async_abort = lambda reason: {"type": "abort", "reason": reason}
        result = await handler.async_step_dhcp(
            {"ip": "192.168.1.10", "macaddress": "AA:BB:CC:DD:EE:FF"}
        )
        assert result == {"type": "abort", "reason": "not_kospel_device"}

    @pytest.mark.asyncio
    async def test_dhcp_creates_entry_for_single_device(self) -> None:
        """async_step_dhcp probes host and creates entry for single device ID."""
        handler = KospelConfigFlowHandler()
        _DHCP_CANDIDATE_HOSTS.clear()
        info = MagicMock()
        info.device_ids = [65]
        info.serial_number = "mi01_123"
        info.host = "192.168.1.10"
        handler.async_create_entry = lambda title, data: {
            "type": "create_entry",
            "title": title,
            "data": data,
        }
        handler.async_set_unique_id = AsyncMock()
        handler._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.kospel.config_flow.probe_device",
            new_callable=AsyncMock,
            return_value=info,
        ):
            result = await handler.async_step_dhcp(
                {"ip": "192.168.1.10", "macaddress": "70:B3:D5:24:9A:CC"}
            )

        assert "192.168.1.10" in _DHCP_CANDIDATE_HOSTS
        assert result["type"] == "create_entry"


class TestDiscoverByNetworkScan:
    """Tests for adapter-subnet network scan discovery."""

    @pytest.mark.asyncio
    async def test_returns_empty_without_subnets(self) -> None:
        """_discover_by_network_scan returns empty when no adapter subnets exist."""
        with patch(
            "custom_components.kospel.config_flow._get_subnets_to_scan",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await _discover_by_network_scan(MagicMock(), MagicMock())
        assert result == []

    @pytest.mark.asyncio
    async def test_scans_all_subnets_and_expands_device_ids(self) -> None:
        """_discover_by_network_scan scans all subnets from adapters."""
        info = MagicMock()
        info.device_ids = [65, 66]
        with patch(
            "custom_components.kospel.config_flow._get_subnets_to_scan",
            new_callable=AsyncMock,
            return_value=["192.168.1.0/24", "10.0.0.0/24"],
        ), patch(
            "custom_components.kospel.config_flow.discover_devices",
            new_callable=AsyncMock,
            side_effect=[[info], []],
        ) as mock_discover:
            result = await _discover_by_network_scan(MagicMock(), MagicMock())
        assert mock_discover.await_count == 2
        assert result == [(info, 65), (info, 66)]


class TestHttpMethodSelection:
    """Tests for explicit HTTP connection method selection."""

    @pytest.mark.asyncio
    async def test_http_method_selects_auto_discovery(self) -> None:
        """Selecting auto_discovery stores method and continues to discover step."""
        handler = KospelConfigFlowHandler()
        with patch.object(
            handler,
            "async_step_discover",
            new_callable=AsyncMock,
            return_value={"type": "discover"},
        ) as mock_step:
            result = await handler.async_step_http_method(
                {"http_method": "auto_discovery"}
            )
        assert handler._discovery_method == "auto_discovery"
        mock_step.assert_awaited_once()
        assert result == {"type": "discover"}

    @pytest.mark.asyncio
    async def test_http_method_selects_network_scan(self) -> None:
        """Selecting network_scan stores method and continues to discover step."""
        handler = KospelConfigFlowHandler()
        with patch.object(
            handler,
            "async_step_discover",
            new_callable=AsyncMock,
            return_value={"type": "discover"},
        ) as mock_step:
            result = await handler.async_step_http_method(
                {"http_method": "network_scan"}
            )
        assert handler._discovery_method == "network_scan"
        mock_step.assert_awaited_once()
        assert result == {"type": "discover"}


class TestKospelOptionsFlowHandler:
    """Tests for KospelOptionsFlowHandler (options flow for refresh delay)."""

    @pytest.mark.asyncio
    async def test_init_form_shows_default_delay(self) -> None:
        """async_step_init with no user_input shows form with default delay."""
        config_entry = MagicMock()
        config_entry.options = {}
        handler = KospelOptionsFlowHandler(config_entry)

        result = await handler.async_step_init(user_input=None)

        assert result["type"] == "show_form"
        assert result["step_id"] == "init"
        assert CONF_REFRESH_DELAY_AFTER_SET in result["data_schema"].schema
        # Default when options empty is DEFAULT_REFRESH_DELAY_AFTER_SET
        assert handler.options.get(CONF_REFRESH_DELAY_AFTER_SET) is None

    @pytest.mark.asyncio
    async def test_init_form_saves_user_input(self) -> None:
        """async_step_init with user_input saves and returns create_entry."""
        config_entry = MagicMock()
        config_entry.options = {}
        handler = KospelOptionsFlowHandler(config_entry)
        user_input = {CONF_REFRESH_DELAY_AFTER_SET: 2.0}

        result = await handler.async_step_init(user_input=user_input)

        assert result["type"] == "create_entry"
        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_init_form_uses_existing_option_as_default(self) -> None:
        """async_step_init shows form when existing options present."""
        config_entry = MagicMock()
        config_entry.options = {CONF_REFRESH_DELAY_AFTER_SET: 2.5}
        handler = KospelOptionsFlowHandler(config_entry)

        result = await handler.async_step_init(user_input=None)

        assert result["type"] == "show_form"
        assert result["step_id"] == "init"
        assert handler.options.get(CONF_REFRESH_DELAY_AFTER_SET) == 2.5

    def test_async_get_options_flow_returns_handler(self) -> None:
        """async_get_options_flow returns KospelOptionsFlowHandler instance."""
        config_entry = MagicMock()
        result = KospelConfigFlowHandler.async_get_options_flow(config_entry)
        assert isinstance(result, KospelOptionsFlowHandler)
        assert result.config_entry is config_entry

    def test_validation_rejects_out_of_range(self) -> None:
        """vol.Range rejects values outside 0.5 to 5.0."""
        schema = vol.Schema(
            {
                vol.Required(CONF_REFRESH_DELAY_AFTER_SET): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=REFRESH_DELAY_MIN, max=REFRESH_DELAY_MAX),
                ),
            }
        )
        schema({CONF_REFRESH_DELAY_AFTER_SET: 2.0})  # Valid
        with pytest.raises(vol.Invalid):
            schema({CONF_REFRESH_DELAY_AFTER_SET: 0.1})
        with pytest.raises(vol.Invalid):
            schema({CONF_REFRESH_DELAY_AFTER_SET: 10.0})
