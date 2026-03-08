"""Tests for config flow and related helpers.

Uses sys.modules mocking to avoid requiring homeassistant at test runtime,
since homeassistant has strict dependency constraints that conflict with
the project's aiohttp version.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock homeassistant before importing integration modules.
# homeassistant must be a module (have __path__) for "from homeassistant.x import y" to work.
class _HAModule:
    __path__ = []
    __file__ = ""
    __name__ = "homeassistant"


_ha = _HAModule()
sys.modules["homeassistant"] = _ha
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.network"] = MagicMock()
sys.modules["homeassistant.components.climate"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.switch"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
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
    CONF_SERIAL_NUMBER,
    DEFAULT_SUBNETS,
    make_unique_id,
    get_device_identifier,
    get_device_info,
)
from custom_components.kospel.config_flow import (
    CannotConnect,
    validate_http_input,
    _get_subnets_to_scan,
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
    async def test_returns_default_subnets_when_network_fails(self) -> None:
        """_get_subnets_to_scan returns DEFAULT_SUBNETS when network raises."""
        hass = MagicMock()
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            side_effect=Exception("Network not loaded"),
        ):
            result = await _get_subnets_to_scan(hass)
        assert result == DEFAULT_SUBNETS

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
        assert result == DEFAULT_SUBNETS

    @pytest.mark.asyncio
    async def test_returns_default_when_no_ipv4(self) -> None:
        """_get_subnets_to_scan returns DEFAULT_SUBNETS when no IPv4 addresses."""
        hass = MagicMock()
        adapters = [{"enabled": True, "ipv4": []}]
        with patch(
            "custom_components.kospel.config_flow.network.async_get_adapters",
            new_callable=AsyncMock,
            return_value=adapters,
        ):
            result = await _get_subnets_to_scan(hass)
        assert result == DEFAULT_SUBNETS
