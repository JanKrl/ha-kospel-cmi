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
    KospelHeatingModeSensor,
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

    def test_native_value_room_temperature(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value reads room_temperature from controller."""
        mock_controller = MagicMock()
        mock_controller.room_temperature = 21.0
        mock_coordinator.data = mock_controller

        entity = KospelTemperatureSensor(
            mock_coordinator,
            mock_entry,
            "room_temperature",
            lambda c, name="room_temperature": getattr(c, name, None),
        )

        assert entity.native_value == 21.0

    def test_native_value_water_temperature_reads_water_current_temperature(
        self, mock_coordinator, mock_entry
    ) -> None:
        """Water sensor uses translation id water_temperature; value from water_current_temperature."""
        mock_controller = MagicMock()
        mock_controller.water_current_temperature = 42.0
        mock_coordinator.data = mock_controller

        entity = KospelTemperatureSensor(
            mock_coordinator,
            mock_entry,
            "water_temperature",
            lambda c, name="water_current_temperature": getattr(c, name, None),
        )

        assert entity.native_value == 42.0

    def test_native_value_water_temperature_none_when_attr_missing(
        self, mock_coordinator, mock_entry
    ) -> None:
        """Water temperature sensor returns None without water_current_temperature."""
        mock_controller = object()
        mock_coordinator.data = mock_controller

        entity = KospelTemperatureSensor(
            mock_coordinator,
            mock_entry,
            "water_temperature",
            lambda c, name="water_current_temperature": getattr(c, name, None),
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


class TestKospelHeatingModeSensorNativeValue:
    """Tests for combined heating mode sensor."""

    def test_heating_mode_ch_running(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is 'ch' when CH is running."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = "running"
        mock_controller.cwu_heating_status = "idle"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "ch"

    def test_heating_mode_dwh_running(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is 'dwh' when DHW is running."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = "idle"
        mock_controller.cwu_heating_status = "running"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "dwh"

    def test_heating_mode_both_idle(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is 'idle' when both are idle."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = "idle"
        mock_controller.cwu_heating_status = "idle"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "idle"

    def test_heating_mode_ch_idle_dwh_disabled(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is 'idle' when CH is idle and DHW disabled."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = "idle"
        mock_controller.cwu_heating_status = "disabled"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "idle"

    def test_heating_mode_both_disabled(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is 'off' when both are disabled."""
        mock_controller = MagicMock()
        mock_controller.co_heating_status = "disabled"
        mock_controller.cwu_heating_status = "disabled"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "off"

    def test_heating_mode_with_enum_values(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value works with enum-like objects that have .value attribute."""
        mock_controller = MagicMock()
        mock_ch_status = MagicMock()
        mock_ch_status.value = "RUNNING"
        mock_dwh_status = MagicMock()
        mock_dwh_status.value = "IDLE"
        mock_controller.co_heating_status = mock_ch_status
        mock_controller.cwu_heating_status = mock_dwh_status
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value == "ch"

    def test_heating_mode_none_when_missing_ch(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is None when CH status is missing."""
        mock_controller = MagicMock(spec=[])
        mock_controller.cwu_heating_status = "idle"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value is None

    def test_heating_mode_none_when_missing_dwh(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value is None when DHW status is missing."""
        mock_controller = MagicMock(spec=[])
        mock_controller.co_heating_status = "idle"
        mock_coordinator.data = mock_controller

        entity = KospelHeatingModeSensor(mock_coordinator, mock_entry)
        assert entity.native_value is None
