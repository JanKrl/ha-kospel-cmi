"""Tests for Kospel climate entity (target_temperature, supported_features, async_set_temperature)."""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from kospel_cmi.registers.enums import HeaterMode

# Mock homeassistant before importing integration modules.
class _HAModule:
    __path__ = []
    __file__ = ""
    __name__ = "homeassistant"
    __spec__ = None


_ha = _HAModule()
sys.modules["homeassistant"] = _ha
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.climate"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.switch"] = MagicMock()
sys.modules["homeassistant.components.water_heater"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()


def _device_info(**kwargs):
    return kwargs


sys.modules["homeassistant.helpers.entity"].DeviceInfo = _device_info

# Create minimal base classes to avoid metaclass conflicts
class _CoordinatorEntityBase:
    """Minimal CoordinatorEntity stand-in for testing."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class _ClimateEntityBase:
    """Minimal ClimateEntity stand-in for testing."""

    pass


class _ClimateEntityFeature:
    """Minimal ClimateEntityFeature stand-in for testing (distinct bit flags)."""

    TARGET_TEMPERATURE = 1
    PRESET_MODE = 2
    TURN_ON = 4
    TURN_OFF = 8


sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)
climate_mock = MagicMock()
climate_mock.ClimateEntity = _ClimateEntityBase
climate_mock.ClimateEntityFeature = _ClimateEntityFeature
climate_mock.HVACMode = MagicMock()
climate_mock.HVACAction = MagicMock()
sys.modules["homeassistant.components.climate"] = climate_mock

# Import after mocks
from custom_components.kospel.climate import KospelClimateEntity

ClimateEntityFeature = _ClimateEntityFeature


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with configurable controller data."""
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    coordinator.entry.data = {}
    coordinator.entry.entry_id = "test-entry-id"
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def climate_entity(mock_coordinator):
    """Create KospelClimateEntity with mocked coordinator."""
    return KospelClimateEntity(mock_coordinator)


class TestClimateTargetTemperature:
    """Tests for target_temperature (room_setpoint)."""

    def test_target_temperature_returns_room_setpoint(
        self, climate_entity, mock_coordinator
    ) -> None:
        """target_temperature returns room_setpoint from controller."""
        mock_controller = MagicMock()
        mock_controller.room_setpoint = 22.0
        mock_coordinator.data = mock_controller

        assert climate_entity.target_temperature == 22.0

    def test_target_temperature_returns_none_when_room_setpoint_missing(
        self, climate_entity, mock_coordinator
    ) -> None:
        """target_temperature returns None when room_setpoint not in controller."""
        mock_controller = MagicMock(spec=[])  # No room_setpoint
        mock_coordinator.data = mock_controller

        result = climate_entity.target_temperature
        assert result is None


class TestClimateSupportedFeatures:
    """Tests for supported_features (TARGET_TEMPERATURE only when manual mode)."""

    def test_supported_features_includes_target_temp_when_manual_mode_on(
        self, climate_entity, mock_coordinator
    ) -> None:
        """TARGET_TEMPERATURE included when manual mode is enabled."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.MANUAL
        mock_coordinator.data = mock_controller

        features = climate_entity.supported_features
        assert (features & ClimateEntityFeature.TARGET_TEMPERATURE) != 0

    def test_supported_features_excludes_target_temp_when_manual_mode_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """TARGET_TEMPERATURE excluded when manual mode is disabled."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.WINTER
        mock_coordinator.data = mock_controller

        features = climate_entity.supported_features
        assert (features & ClimateEntityFeature.TARGET_TEMPERATURE) == 0


class TestClimateSetTemperature:
    """Tests for async_set_temperature (no-op when manual mode off)."""

    @pytest.mark.asyncio
    async def test_set_temperature_no_op_when_manual_mode_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature does nothing when manual mode is off."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.WINTER
        mock_controller.save = AsyncMock()
        mock_coordinator.data = mock_controller

        await climate_entity.async_set_temperature(temperature=25.0)

        mock_controller.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_temperature_writes_when_manual_mode_on(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature writes manual_temperature when manual mode is on."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.MANUAL
        mock_controller.save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        await climate_entity.async_set_temperature(temperature=25.0)

        assert mock_controller.manual_temperature == 25.0
        mock_controller.save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()
