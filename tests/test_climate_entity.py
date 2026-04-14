"""Tests for Kospel climate entity (HVAC modes, presets, target temperature)."""

import sys
from types import SimpleNamespace
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


class _FakeHomeAssistantError(Exception):
    """Stand-in for HomeAssistantError in tests."""


class _FakeConfigEntryNotReady(_FakeHomeAssistantError):
    """Stand-in for ConfigEntryNotReady (package __init__ imports it)."""


sys.modules["homeassistant.exceptions"] = SimpleNamespace(
    HomeAssistantError=_FakeHomeAssistantError,
    ConfigEntryNotReady=_FakeConfigEntryNotReady,
)
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


climate_const_mock = SimpleNamespace(PRESET_NONE="none")
sys.modules["homeassistant.components.climate.const"] = climate_const_mock

sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)
climate_mock = MagicMock()
climate_mock.ClimateEntity = _ClimateEntityBase
climate_mock.ClimateEntityFeature = _ClimateEntityFeature
climate_mock.HVACMode = MagicMock()
climate_mock.HVACMode.HEAT = "heat"
climate_mock.HVACMode.OFF = "off"
climate_mock.HVACMode.AUTO = "auto"
climate_mock.HVACAction = MagicMock()
sys.modules["homeassistant.components.climate"] = climate_mock

# Import after mocks
from custom_components.kospel.climate import KospelClimateEntity

ClimateEntityFeature = _ClimateEntityFeature
HVACAction = climate_mock.HVACAction
HVACMode = climate_mock.HVACMode
PRESET_NONE = climate_const_mock.PRESET_NONE
HomeAssistantError = _FakeHomeAssistantError


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
    """Tests for supported_features (TARGET_TEMPERATURE always on for visibility)."""

    def test_supported_features_includes_target_temp_in_manual_and_auto(
        self, climate_entity, mock_coordinator
    ) -> None:
        """TARGET_TEMPERATURE is always set so the UI can show the room setpoint."""
        for mode in (HeaterMode.WINTER, HeaterMode.MANUAL):
            mock_controller = MagicMock()
            mock_controller.heater_mode = mode
            mock_coordinator.data = mock_controller

            features = climate_entity.supported_features
            assert (features & ClimateEntityFeature.TARGET_TEMPERATURE) != 0


class TestClimateHvacModeAndPreset:
    """Tests for hvac_mode and preset_mode mapping."""

    def test_hvac_off_preset_none_when_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """OFF maps to HVAC off and preset none."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.OFF
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_mode == HVACMode.OFF
        assert climate_entity.preset_mode == PRESET_NONE

    def test_hvac_heat_preset_none_when_manual(
        self, climate_entity, mock_coordinator
    ) -> None:
        """MANUAL maps to Heat and preset none."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.MANUAL
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_mode == HVACMode.HEAT
        assert climate_entity.preset_mode == PRESET_NONE

    def test_hvac_auto_preset_winter(
        self, climate_entity, mock_coordinator
    ) -> None:
        """WINTER maps to Auto with winter preset."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.WINTER
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_mode == HVACMode.AUTO
        assert climate_entity.preset_mode == HeaterMode.WINTER.value

    def test_hvac_auto_preset_summer(
        self, climate_entity, mock_coordinator
    ) -> None:
        """SUMMER maps to Auto with summer preset."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.SUMMER
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_mode == HVACMode.AUTO
        assert climate_entity.preset_mode == HeaterMode.SUMMER.value


class TestClimateSetTemperature:
    """Tests for async_set_temperature (delegates to set_manual_heating on the device)."""

    @pytest.mark.asyncio
    async def test_set_temperature_raises_when_not_manual(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature raises when the device is not in MANUAL."""
        mock_controller = MagicMock()
        mock_controller.heater_mode = HeaterMode.WINTER
        mock_controller.set_manual_heating = AsyncMock(return_value=True)
        mock_coordinator.data = mock_controller

        with pytest.raises(HomeAssistantError, match="Heat \\(manual\\)"):
            await climate_entity.async_set_temperature(temperature=25.0)

        mock_controller.set_manual_heating.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_temperature_calls_set_manual_heating_when_manual(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_set_temperature calls set_manual_heating when in MANUAL."""
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


class TestClimateSetHvacMode:
    """Tests for async_set_hvac_mode device mapping."""

    @pytest.mark.asyncio
    async def test_set_hvac_off_sets_heater_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """HVAC OFF sets HeaterMode.OFF."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_hvac_mode(HVACMode.OFF)

        mock_controller.set_heater_mode.assert_called_once_with(HeaterMode.OFF)

    @pytest.mark.asyncio
    async def test_set_hvac_heat_sets_manual(
        self, climate_entity, mock_coordinator
    ) -> None:
        """HVAC HEAT sets HeaterMode.MANUAL."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_hvac_mode(HVACMode.HEAT)

        mock_controller.set_heater_mode.assert_called_once_with(HeaterMode.MANUAL)

    @pytest.mark.asyncio
    async def test_set_hvac_auto_sets_winter_default(
        self, climate_entity, mock_coordinator
    ) -> None:
        """HVAC AUTO defaults to HeaterMode.WINTER."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_hvac_mode(HVACMode.AUTO)

        mock_controller.set_heater_mode.assert_called_once_with(HeaterMode.WINTER)


class TestClimateSetPresetMode:
    """Tests for async_set_preset_mode."""

    @pytest.mark.asyncio
    async def test_set_preset_none_is_noop(
        self, climate_entity, mock_coordinator
    ) -> None:
        """Preset 'none' does not call the controller."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.data = mock_controller

        await climate_entity.async_set_preset_mode(PRESET_NONE)

        mock_controller.set_heater_mode.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_preset_summer_calls_controller(
        self, climate_entity, mock_coordinator
    ) -> None:
        """Setting summer preset writes HeaterMode.SUMMER."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_coordinator.data = mock_controller
        climate_entity.async_write_ha_state = MagicMock()

        with patch("custom_components.kospel.climate.asyncio.sleep", new_callable=AsyncMock):
            await climate_entity.async_set_preset_mode(HeaterMode.SUMMER.value)

        mock_controller.set_heater_mode.assert_called_once_with(HeaterMode.SUMMER)

    @pytest.mark.asyncio
    async def test_set_preset_invalid_raises(
        self, climate_entity, mock_coordinator
    ) -> None:
        """Unknown preset raises HomeAssistantError."""
        mock_controller = MagicMock()
        mock_controller.set_heater_mode = AsyncMock()
        mock_coordinator.data = mock_controller

        with pytest.raises(HomeAssistantError, match="Unsupported preset"):
            await climate_entity.async_set_preset_mode("not_a_mode")

        mock_controller.set_heater_mode.assert_not_called()


class TestClimateHvacAction:
    """Tests for hvac_action (heating indicator based on CH status)."""

    def test_hvac_action_heating_when_ch_status_running(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns HEATING when CH status is RUNNING."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.RUNNING
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.HEATING

    def test_hvac_action_off_when_ch_status_idle(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns OFF when CH status is IDLE."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.IDLE
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.OFF

    def test_hvac_action_off_when_ch_status_disabled(
        self, climate_entity, mock_coordinator
    ) -> None:
        """hvac_action returns OFF when CH status is DISABLED."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = HeatingStatus.DISABLED
        mock_coordinator.data = mock_controller

        assert climate_entity.hvac_action == HVACAction.OFF


class TestClimateTurnOnOff:
    """Tests for async_turn_on and async_turn_off (delegate to async_set_hvac_mode)."""

    @pytest.mark.asyncio
    async def test_turn_on_calls_set_hvac_mode_auto(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_turn_on delegates to async_set_hvac_mode(AUTO) for seasonal default."""
        climate_entity.async_set_hvac_mode = AsyncMock()
        await climate_entity.async_turn_on()
        climate_entity.async_set_hvac_mode.assert_called_once_with(HVACMode.AUTO)

    @pytest.mark.asyncio
    async def test_turn_off_calls_set_hvac_mode_off(
        self, climate_entity, mock_coordinator
    ) -> None:
        """async_turn_off delegates to async_set_hvac_mode(HVACMode.OFF)."""
        climate_entity.async_set_hvac_mode = AsyncMock()
        await climate_entity.async_turn_off()
        climate_entity.async_set_hvac_mode.assert_called_once_with(HVACMode.OFF)
