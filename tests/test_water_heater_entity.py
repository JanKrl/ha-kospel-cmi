"""Tests for Kospel water heater entity (target_temperature uses supply_setpoint)."""

import sys
from unittest.mock import MagicMock

import pytest

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


sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)
sys.modules["homeassistant.components.water_heater"].WaterHeaterEntity = (
    _WaterHeaterEntityBase
)

from custom_components.kospel.water_heater import KospelWaterHeaterEntity


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
def water_heater_entity(mock_coordinator):
    """Create KospelWaterHeaterEntity with mocked coordinator."""
    return KospelWaterHeaterEntity(mock_coordinator)


class TestWaterHeaterTargetTemperature:
    """Tests for target_temperature (supply_setpoint for CWU)."""

    def test_target_temperature_returns_supply_setpoint(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns supply_setpoint from controller."""
        mock_controller = MagicMock()
        mock_controller.supply_setpoint = 45.0
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature == 45.0

    def test_target_temperature_returns_none_when_supply_setpoint_missing(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns None when supply_setpoint not in controller."""
        mock_controller = MagicMock(spec=[])  # No supply_setpoint
        mock_coordinator.data = mock_controller

        result = water_heater_entity.target_temperature
        assert result is None
