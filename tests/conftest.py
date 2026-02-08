"""Shared fixtures and test configuration for pytest."""

import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock

import aiohttp

from kospel_cmi.controller.api import HeaterController
from kospel_cmi.controller.registry import SETTINGS_REGISTRY
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend


@pytest.fixture
def api_base_url() -> str:
    """Standard API base URL fixture."""
    return "http://192.168.1.100/api/dev/65"


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock aiohttp ClientSession fixture."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.get = AsyncMock()
    session.post = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


@pytest.fixture
def mock_state_file(tmp_path: Path) -> Path:
    """Temporary mock state file fixture."""
    state_file = tmp_path / "heater_mock_state.yaml"
    return state_file


@pytest.fixture
def sample_registers() -> Dict[str, str]:
    """Sample register data covering various settings and edge cases."""
    return {
        # Register 0b55 - Contains heater mode and flags
        # Bit 3=1 (summer mode), Bit 4=0 (water heater disabled), Bit 5=0, Bit 9=1 (manual enabled)
        # Value: 0x0208 = 0b0000001000001000 (bits 3 and 9 set)
        "0b55": "0802",
        # Register 0b51 - Status register (pumps and valve)
        # Bit 0=1 (pump CO running), Bit 1=0, Bit 2=1 (valve CO position)
        # Value: 0x0005 = 0b0000000000000101 (bits 0 and 2 set)
        "0b51": "0500",
        # Register 0b8d - Manual temperature (215 = 21.5°C)
        "0b8d": "d700",
        # Register 0b68 - Room temperature economy (200 = 20.0°C)
        "0b68": "c800",
        # Register 0b6a - Room temperature comfort (220 = 22.0°C)
        "0b6a": "dc00",
        # Register 0b6b - Room temperature comfort plus (230 = 23.0°C)
        "0b6b": "e600",
        # Register 0b69 - Room temperature comfort minus (210 = 21.0°C)
        "0b69": "d200",
        # Register 0b66 - CWU temperature economy (400 = 40.0°C)
        "0b66": "9001",
        # Register 0b67 - CWU temperature comfort (450 = 45.0°C)
        "0b67": "c201",
        # Register 0b8a - Pressure (5000 = 50.0)
        "0b8a": "8813",
        # Additional registers with edge cases
        "0b00": "0000",  # Zero value
        "0b01": "ff7f",  # 32767 (max positive)
        "0b02": "0080",  # -32768 (min negative)
        "0b03": "0100",  # 1
        "0b04": "ff00",  # 255
        # Register for winter mode test (bit 5=1, bit 3=0)
        # Value: 0x0020 = 0b0000000000100000 (bit 5 set)
        "0b56": "2000",
        # Register for OFF mode test (bits 3=0, 5=0)
        "0b57": "0000",
    }


@pytest.fixture
def sample_registers_empty() -> Dict[str, str]:
    """Empty register data for testing default handling."""
    return {}


@pytest.fixture
def sample_registers_invalid() -> Dict[str, str]:
    """Invalid/malformed register data for error handling tests."""
    return {
        "0b00": "invalid",  # Non-hex string
        "0b01": "123",  # Too short
        "0b02": "12345",  # Too long
        "0b03": "",  # Empty string
        "0b04": "gggg",  # Invalid hex characters
    }


@pytest.fixture
def sample_registers_winter_mode() -> Dict[str, str]:
    """Sample registers with winter mode enabled."""
    return {
        # Register 0b55 - Winter mode (bit 5=1, bit 3=0)
        # Value: 0x0020 = 0b0000000000100000 (bit 5 set)
        "0b55": "2000",
        "0b51": "0500",
        "0b8d": "d700",
        "0b68": "c800",
    }


@pytest.fixture
def sample_registers_off_mode() -> Dict[str, str]:
    """Sample registers with heater off (both bits 3 and 5 cleared)."""
    return {
        # Register 0b55 - OFF mode (bit 3=0, bit 5=0)
        "0b55": "0000",
        "0b51": "0500",
        "0b8d": "d700",
    }


@pytest.fixture
def yaml_backend_state_file(tmp_path: Path) -> Path:
    """Path to a temporary YAML state file for YamlRegisterBackend tests."""
    state_file = tmp_path / "state.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    return state_file


@pytest.fixture
async def heater_controller(
    mock_session: AsyncMock, api_base_url: str
) -> HeaterController:
    """HeaterController instance fixture (HTTP backend)."""
    backend = HttpRegisterBackend(mock_session, api_base_url)
    return HeaterController(backend=backend, registry=SETTINGS_REGISTRY)


@pytest.fixture
async def heater_controller_with_registers(
    mock_session: AsyncMock,
    api_base_url: str,
    sample_registers: Dict[str, str],
) -> HeaterController:
    """HeaterController instance with pre-loaded register data."""
    backend = HttpRegisterBackend(mock_session, api_base_url)
    controller = HeaterController(backend=backend, registry=SETTINGS_REGISTRY)
    controller.from_registers(sample_registers)
    return controller


@pytest.fixture
async def heater_controller_yaml(
    yaml_backend_state_file: Path,
) -> HeaterController:
    """HeaterController instance with YAML backend (for development/mock tests)."""
    backend = YamlRegisterBackend(state_file=str(yaml_backend_state_file))
    return HeaterController(backend=backend, registry=SETTINGS_REGISTRY)
