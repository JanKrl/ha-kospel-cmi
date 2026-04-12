"""Tests for Kospel climate entity (target_temperature, supported_features, async_set_temperature)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kospel_cmi.registers.enums import HeaterMode, HeatingStatus

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
climate_mock.HVACMode.HEAT = "heat"
climate_mock.HVACMode.OFF = "off"
climate_mock.HVACAction = MagicMock()
sys.modules["homeassistant.components.climate"] = climate_mock

# Import after mocks
from custom_components.kospel.climate import KospelClimateEntity

ClimateEntityFeature = _ClimateEntityFeature
HVACAction = climate_mock.HVACAction
HVACMode = climate_mock.HVACMode


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with configurable controller data."""
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    coordinator.entry.data = {}
    coordinator.entry.options = {}
    coordinator.entry.entry_id = "test-entry-id"
    coordinator.last_update_success = True
    coordinator.communication_ok = True
    return coordinator


@pytest.fixture
def climate_entity(mock_coordinator):
    """Create KospelClimateEntity with mocked coordinator."""
    return KospelClimateEntity(mock_coordinator)


class TestClimateTargetTemperature:
    """Tests for target_temperature (always room_setpoint)."""

    def test_target_temperature_returns_room_setpoint(
        self, climate_entity, mock_coordinator
    ) -> None:
        """target_temperature always returns room_setpoint from controller."""
        mock_controller = MagicMock()
        mock_controller.room_setpoint = 22.0
        mock_coordinator.data = mock_controller

        assert climate_entity.target_temperature == 22.0

    def test_target_temperature_returns_none_when_room_setpoint_missing(
        self, climate_entity, mock_coordinator
    ) -> None:
        """target_temperature returns None when room_setpoint not in controller."""
        mock_controller = MagicMock()
        mock_controller.room_setpoint = None
        mock_coordinator.data = mock_controller

        result = climate_entity.target_temperature
        assert result is None


class TestClimateSupportedFeatures:
    """Tests for supported_features (TARGET_TEMPERATURE always shown for display)."""

    def test_supported_features_includes_target_temp_always(
        self, climate_entity, mock_coordinator
    ) -> None:
        """TARGET_TEMPERATURE always included so target is displayed and settable."""
        for mode in (HeaterMode.WINTER, HeaterMode.MANUAL):
            mock_controller = MagicMock()
            mock_controller.heater_mode = mode
            mock_coordinator.data = mock_controller

            features = climate_entity.supported_features
            assert (features & ClimateEntityFeature.TARGET_TEMPERATURE) != 0


class TestClimateSetTemperature:
    """Tests for async_set_temperature (delegates to set_manual_heating on the device)."""

    @pytest.mark.asyncio
    async def test_set_temperature_calls_set_manual_heating_from_winter_mode(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature calls set_manual_heating even when not already in MANUAL."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.WINTER
        mock_controller.set_manual_heating = AsyncMock(return_value=True)
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_temperature(temperature=25.0)

        mock_controller.set_manual_heating.assert_called_once_with(25.0)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_temperature_calls_set_manual_heating_when_already_manual(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature still calls set_manual_heating when already in MANUAL."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.MANUAL
        mock_controller.set_manual_heating = AsyncMock(return_value=True)
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_temperature(temperature=25.0)

        mock_controller.set_manual_heating.assert_called_once_with(25.0)
        mock_coordinator.async_request_refresh.assert_called_once()


class TestClimateHvacAction:
    """Tests for hvac_action (heating indicator based on co_heating_status)."""

    def test_hvac_action_heating_when_co_heating_status_running(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns HEATING when co_heating_status is RUNNING."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.RUNNING
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.HEATING

    def test_hvac_action_off_when_co_heating_status_idle(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns OFF when co_heating_status is IDLE."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.IDLE
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.OFF

    def test_hvac_action_off_when_co_heating_status_disabled(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns OFF when co_heating_status is DISABLED."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.DISABLED
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.OFF


class TestClimateTurnOnOff:
    """Tests for async_turn_on and async_turn_off (delegate to async_set_hvac_mode)."""

    @pytest.mark.asyncio
    async def test_turn_on_calls_set_hvac_mode_heat(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_turn_on delegates to async_set_hvac_mode(HVACMode.HEAT)."""
        climate_entity.async_set_hvac_mode = AsyncMock()
        await climate_entity.async_turn_on()
        climate_entity.async_set_hvac_mode.assert_called_once_with(HVACMode.HEAT)

    @pytest.mark.asyncio
    async def test_turn_off_calls_set_hvac_mode_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_turn_off delegates to async_set_hvac_mode(HVACMode.OFF)."""
        climate_entity.async_set_hvac_mode = AsyncMock()
        await climate_entity.async_turn_off()
        climate_entity.async_set_hvac_mode.assert_called_once_with(HVACMode.OFF)
