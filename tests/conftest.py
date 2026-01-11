"""Shared fixtures and test configuration for pytest."""

import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock

import aiohttp

from custom_components.kospel.controller.api import HeaterController
from custom_components.kospel.controller.registry import SETTINGS_REGISTRY
from custom_components.kospel.kospel.simulator import SimulatorRegisterState


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
def mock_register_state(
    mock_state_file: Path, monkeypatch: pytest.MonkeyPatch
) -> SimulatorRegisterState:
    """SimulatorRegisterState instance fixture with temporary file."""
    # Set environment variable to use the temporary file
    monkeypatch.setenv("SIMULATION_STATE_FILE", mock_state_file.name)
    # Create a temporary data directory
    data_dir = mock_state_file.parent / "data"
    data_dir.mkdir(exist_ok=True)
    state_file_path = str(data_dir / mock_state_file.name)

    # Patch the SimulatorRegisterState to use our temp file
    state = SimulatorRegisterState(state_file=state_file_path)
    return state


@pytest.fixture
async def heater_controller(
    mock_session: AsyncMock, api_base_url: str
) -> HeaterController:
    """HeaterController instance fixture."""
    return HeaterController(mock_session, api_base_url, registry=SETTINGS_REGISTRY)


@pytest.fixture
async def heater_controller_with_registers(
    mock_session: AsyncMock,
    api_base_url: str,
    sample_registers: Dict[str, str],
) -> HeaterController:
    """HeaterController instance with pre-loaded register data."""
    controller = HeaterController(
        mock_session, api_base_url, registry=SETTINGS_REGISTRY
    )
    controller.from_registers(sample_registers)
    return controller


@pytest.fixture(autouse=True)
def reset_simulation_mode(monkeypatch: pytest.MonkeyPatch):
    """Reset simulation mode to disabled before each test."""
    monkeypatch.delenv("SIMULATION_MODE", raising=False)


@pytest.fixture
def enable_simulation_mode(monkeypatch: pytest.MonkeyPatch):
    """Enable simulation mode for a test."""
    monkeypatch.setenv("SIMULATION_MODE", "1")
    return True


@pytest.fixture
def disable_simulation_mode(monkeypatch: pytest.MonkeyPatch):
    """Disable simulation mode for a test."""
    monkeypatch.delenv("SIMULATION_MODE", raising=False)
    return False


@pytest.fixture
def enable_mock_mode(monkeypatch: pytest.MonkeyPatch):
    """Alias for enable_simulation_mode for backward compatibility in tests."""
    monkeypatch.setenv("SIMULATION_MODE", "1")
    return True
