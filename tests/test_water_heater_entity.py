"""Tests for Kospel water heater entity (target_temperature, current_operation)."""

import sys
from unittest.mock import MagicMock

import pytest

from kospel_cmi.registers.enums import CwuMode


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


class _WaterHeaterEntityBase:
    """Minimal WaterHeaterEntity stand-in for testing."""

    pass


sys.modules[
    "homeassistant.helpers.update_coordinator"
].CoordinatorEntity = _CoordinatorEntityBase
sys.modules[
    "homeassistant.components.water_heater"
].WaterHeaterEntity = _WaterHeaterEntityBase

from custom_components.kospel.water_heater import (
    KospelWaterHeaterEntity,
    STATE_ECO,
    STATE_OFF,
    STATE_PERFORMANCE,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with configurable controller data."""
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    coordinator.entry.data = {}
    coordinator.entry.options = {}
    coordinator.entry.entry_id = "test-entry-id"
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def water_heater_entity(mock_coordinator):
    """Create KospelWaterHeaterEntity with mocked coordinator."""
    return KospelWaterHeaterEntity(mock_coordinator)


class TestWaterHeaterTargetTemperature:
    """Tests for target_temperature (mode-dependent setpoints)."""

    def test_target_temperature_returns_economy_setpoint_when_economy_mode(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns cwu_temperature_economy when cwu_mode is economy."""
        mock_controller = MagicMock()
        mock_controller.cwu_mode = CwuMode.ECONOMY
        mock_controller.cwu_temperature_economy = 40.0
        mock_controller.cwu_temperature_comfort = 45.0
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature == 40.0

    def test_target_temperature_returns_comfort_setpoint_when_comfort_mode(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns cwu_temperature_comfort when cwu_mode is comfort."""
        mock_controller = MagicMock()
        mock_controller.cwu_mode = CwuMode.COMFORT
        mock_controller.cwu_temperature_economy = 40.0
        mock_controller.cwu_temperature_comfort = 45.0
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature == 45.0

    def test_target_temperature_returns_economy_setpoint_when_anti_freeze_mode(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns cwu_temperature_economy when cwu_mode is anti-freeze."""
        mock_controller = MagicMock()
        mock_controller.cwu_mode = CwuMode.ANTI_FREEZE
        mock_controller.cwu_temperature_economy = 40.0
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature == 40.0

    def test_target_temperature_returns_none_when_setpoint_missing(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns None when setpoint not in controller."""
        mock_controller = MagicMock(spec=[])  # No cwu_temperature_* attributes
        mock_coordinator.data = mock_controller

        result = water_heater_entity.target_temperature
        assert result is None


class TestWaterHeaterCurrentOperation:
    """Tests for current_operation (from cwu_mode)."""

    def test_current_operation_eco_when_cwu_mode_economy(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """current_operation returns eco when cwu_mode is economy."""
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        mock_controller.cwu_mode = CwuMode.ECONOMY
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_ECO

    def test_current_operation_off_when_water_heater_disabled(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """current_operation returns off when water heater is disabled."""
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.DISABLED
        mock_controller.cwu_mode = CwuMode.ECONOMY
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_OFF

    def test_current_operation_performance_when_cwu_mode_comfort(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """current_operation returns performance when cwu_mode is comfort."""
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        mock_controller.cwu_mode = CwuMode.COMFORT
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_PERFORMANCE
