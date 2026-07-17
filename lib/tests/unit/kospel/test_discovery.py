"""Unit tests for kospel.discovery (probe_device, discover_devices)."""

import aiohttp
import pytest
from aioresponses import aioresponses

from kospel_cmi.kospel.discovery import (
    DeviceDetail,
    KospelDeviceInfo,
    MODEL_NAMES,
    discover_devices,
    probe_device,
)


class TestProbeDevice:
    """Tests for probe_device."""

    @pytest.mark.asyncio
    async def test_probe_device_returns_info_on_valid_response(self) -> None:
        """probe_device returns KospelDeviceInfo when host is C.MI device."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "0", "sn": "mi01_00006047", "devs": ["65"]},
                )
                m.get(
                    "http://192.168.101.49/api/dev/65/info",
                    payload={
                        "status": "0",
                        "info": {"id": 19, "moduleID": "65"},
                    },
                )
                result = await probe_device(session, "192.168.101.49")
        assert result is not None
        assert isinstance(result, KospelDeviceInfo)
        assert result.host == "192.168.101.49"
        assert result.device_ids == [65]
        assert result.serial_number == "mi01_00006047"
        assert result.api_base_url == "http://192.168.101.49/api/dev/65"
        assert result.device_id == 65
        assert len(result.devices) == 1
        assert result.devices[0].device_id == 65
        assert result.devices[0].model_id == 19
        assert result.devices[0].model_name == "EKCO.M3"
        assert result.devices[0].module_id == "65"

    @pytest.mark.asyncio
    async def test_probe_device_returns_none_on_http_error(self) -> None:
        """probe_device returns None when request fails."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get("http://192.168.101.49/api/dev", status=404)
                result = await probe_device(session, "192.168.101.49")
        assert result is None

    @pytest.mark.asyncio
    async def test_probe_device_returns_none_when_missing_devs(self) -> None:
        """probe_device returns None when response lacks devs."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "0", "sn": "mi01_xyz"},
                )
                result = await probe_device(session, "192.168.101.49")
        assert result is None

    @pytest.mark.asyncio
    async def test_probe_device_returns_none_when_missing_sn(self) -> None:
        """probe_device returns None when response lacks sn."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "0", "devs": ["65"]},
                )
                result = await probe_device(session, "192.168.101.49")
        assert result is None

    @pytest.mark.asyncio
    async def test_probe_device_returns_none_when_status_not_zero(self) -> None:
        """probe_device returns None when status is not '0'."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "1", "sn": "mi01_xyz", "devs": ["65"]},
                )
                result = await probe_device(session, "192.168.101.49")
        assert result is None

    @pytest.mark.asyncio
    async def test_probe_device_model_mapping(self) -> None:
        """probe_device maps model_id to correct model_name."""
        model_cases = [
            (18, "EKD.M3"),
            (19, "EKCO.M3"),
            (65, "C.MG3"),
            (81, "C.MW3"),
        ]
        for model_id, expected_name in model_cases:
            async with aiohttp.ClientSession() as session:
                with aioresponses() as m:
                    m.get(
                        "http://host/api/dev",
                        payload={"status": "0", "sn": "x", "devs": ["65"]},
                    )
                    m.get(
                        "http://host/api/dev/65/info",
                        payload={"status": "0", "info": {"id": model_id, "moduleID": "65"}},
                    )
                    result = await probe_device(session, "http://host")
            assert result is not None
            assert result.devices[0].model_id == model_id
            assert result.devices[0].model_name == expected_name

    @pytest.mark.asyncio
    async def test_probe_device_multiple_devices(self) -> None:
        """probe_device handles devs with multiple device IDs."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.1.1/api/dev",
                    payload={"status": "0", "sn": "mi01_abc", "devs": ["65", "66"]},
                )
                m.get(
                    "http://192.168.1.1/api/dev/65/info",
                    payload={"status": "0", "info": {"id": 19, "moduleID": "65"}},
                )
                m.get(
                    "http://192.168.1.1/api/dev/66/info",
                    payload={"status": "0", "info": {"id": 65, "moduleID": "66"}},
                )
                result = await probe_device(session, "192.168.1.1")
        assert result is not None
        assert result.device_ids == [65, 66]
        assert result.device_id == 65
        assert len(result.devices) == 2
        assert result.devices[0].model_name == "EKCO.M3"
        assert result.devices[1].model_name == "C.MG3"


class TestModelNames:
    """Tests for MODEL_NAMES constant."""

    def test_model_names_contains_expected_mappings(self) -> None:
        """MODEL_NAMES has mappings for known device types."""
        assert MODEL_NAMES[18] == "EKD.M3"
        assert MODEL_NAMES[19] == "EKCO.M3"
        assert MODEL_NAMES[65] == "C.MG3"
        assert MODEL_NAMES[81] == "C.MW3"


class TestDiscoverDevices:
    """Tests for discover_devices."""

    @pytest.mark.asyncio
    async def test_discover_devices_returns_list(self) -> None:
        """discover_devices returns list of KospelDeviceInfo."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "0", "sn": "mi01_001", "devs": ["65"]},
                )
                m.get(
                    "http://192.168.101.49/api/dev/65/info",
                    payload={"status": "0", "info": {"id": 19, "moduleID": "65"}},
                )
                result = await discover_devices(
                    session, "192.168.101.49/32", timeout=1.0
                )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].host == "192.168.101.49"
        assert result[0].serial_number == "mi01_001"

    @pytest.mark.asyncio
    async def test_discover_devices_invalid_subnet_returns_empty(self) -> None:
        """discover_devices returns empty list for invalid subnet."""
        async with aiohttp.ClientSession() as session:
            result = await discover_devices(session, "not-a-subnet")
        assert result == []

    @pytest.mark.asyncio
    async def test_discover_devices_handles_probe_exceptions(self) -> None:
        """discover_devices returns successful results when some probes raise."""
        async with aiohttp.ClientSession() as session:
            with aioresponses() as m:
                m.get(
                    "http://192.168.101.49/api/dev",
                    payload={"status": "0", "sn": "mi01_ok", "devs": ["65"]},
                )
                m.get(
                    "http://192.168.101.49/api/dev/65/info",
                    payload={"status": "0", "info": {"id": 19, "moduleID": "65"}},
                )
                m.get("http://192.168.101.50/api/dev", exception=ConnectionError("unreachable"))
                result = await discover_devices(
                    session, "192.168.101.48/30", timeout=1.0
                )
        assert len(result) == 1
        assert result[0].host == "192.168.101.49"
        assert result[0].serial_number == "mi01_ok"
