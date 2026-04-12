"""Tests for Kospel temperature sensor (native_value via value getter)."""

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
const_mock = MagicMock()
const_mock.UnitOfTemperature = MagicMock()
const_mock.UnitOfTemperature.CELSIUS = "°C"
const_mock.UnitOfPressure = MagicMock()
const_mock.UnitOfPower = MagicMock()
const_mock.UnitOfPower.WATT = "W"
sys.modules["homeassistant.const"] = const_mock
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()


def _device_info(**kwargs):
    return kwargs


sys.modules["homeassistant.helpers.entity"].DeviceInfo = _device_info
_ec = MagicMock()
_ec.CONFIG = "config"
_ec.DIAGNOSTIC = "diagnostic"
sys.modules["homeassistant.helpers.entity"].EntityCategory = _ec


class _CoordinatorEntityBase:
    """Minimal CoordinatorEntity stand-in for testing."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class _SensorEntityBase:
    """Minimal SensorEntity stand-in for testing."""

    pass


sensor_mock = MagicMock()
sensor_mock.SensorEntity = _SensorEntityBase
sensor_mock.SensorDeviceClass = MagicMock()
sensor_mock.SensorDeviceClass.TEMPERATURE = "temperature"
sensor_mock.SensorDeviceClass.POWER = "power"
sensor_mock.SensorStateClass = MagicMock()
sensor_mock.SensorStateClass.MEASUREMENT = "measurement"
sys.modules["homeassistant.components.sensor"] = sensor_mock

sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)

from custom_components.kospel.sensor import (  # noqa: E402
    KospelMaxPowerLimitSensor,
    KospelTemperatureSensor,
)


@pytest.fixture
def mock_entry():
    """Config entry with stable entry_id for unique_id."""
    entry = MagicMock()
    entry.data = {}
    entry.entry_id = "test-entry-id"
    return entry


@pytest.fixture
def mock_coordinator(mock_entry):
    """Mock coordinator with configurable controller data."""
    coordinator = MagicMock()
    coordinator.entry = mock_entry
    coordinator.last_update_success = True
    coordinator.communication_ok = True
    return coordinator


class TestKospelTemperatureSensorNativeValue:
    """Tests for native_value reading controller attributes via getter."""

    def test_native_value_returns_float_from_controller_attribute(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value returns the float from the bound EkcoM3 attribute."""
        mock_controller = MagicMock()
        mock_controller.room_setpoint = 22.5
        mock_coordinator.data = mock_controller

        entity = KospelTemperatureSensor(
            mock_coordinator,
            mock_entry,
            "room_setpoint",
            lambda c, name="room_setpoint": getattr(c, name, None),
        )

        assert entity.native_value == 22.5

    def test_native_value_returns_none_when_attribute_missing(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value returns None when attribute is absent."""
        mock_controller = object()
        mock_coordinator.data = mock_controller

        entity = KospelTemperatureSensor(
            mock_coordinator,
            mock_entry,
            "room_setpoint",
            lambda c, name="room_setpoint": getattr(c, name, None),
        )

        assert entity.native_value is None


class TestKospelMaxPowerLimitSensorNativeValue:
    """Tests for max power limit sensor (kW to W)."""

    def test_native_value_converts_kw_to_w(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is boiler_max_power_kw * 1000."""
        mock_controller = MagicMock()
        mock_controller.boiler_max_power_kw = 4.0
        mock_coordinator.data = mock_controller

        entity = KospelMaxPowerLimitSensor(mock_coordinator, mock_entry)
        assert entity.native_value == 4000.0

    def test_native_value_none_when_missing(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is None when boiler_max_power_kw is None."""
        mock_controller = MagicMock()
        mock_controller.boiler_max_power_kw = None
        mock_coordinator.data = mock_controller

        entity = KospelMaxPowerLimitSensor(mock_coordinator, mock_entry)
        assert entity.native_value is None
