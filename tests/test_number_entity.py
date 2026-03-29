"""Tests for Kospel room preset number entities."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

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
_entity_cat = MagicMock()
_entity_cat.CONFIG = "config"
sys.modules["homeassistant.helpers.entity"].EntityCategory = _entity_cat


class _CoordinatorEntityBase:
    """Minimal CoordinatorEntity stand-in for testing."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def async_write_ha_state(self) -> None:
        """No-op: real HA schedules state write."""

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class _NumberEntityBase:
    """Minimal NumberEntity stand-in for testing."""

    @property
    def native_min_value(self) -> float:
        """Mirror HA NumberEntity: read from _attr_native_min_value."""
        return self._attr_native_min_value

    @property
    def native_max_value(self) -> float:
        """Mirror HA NumberEntity: read from _attr_native_max_value."""
        return self._attr_native_max_value

    @property
    def native_step(self) -> float:
        """Mirror HA NumberEntity: read from _attr_native_step."""
        return self._attr_native_step


number_mock = MagicMock()
number_mock.NumberEntity = _NumberEntityBase
number_mock.NumberDeviceClass = MagicMock()
number_mock.NumberDeviceClass.TEMPERATURE = "temperature"
sys.modules["homeassistant.components.number"] = number_mock

sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)

from custom_components.kospel.number import (  # noqa: E402
    KospelRoomPresetNumberEntity,
    ROOM_PRESET_TEMP_MAX,
    ROOM_PRESET_TEMP_MIN,
    ROOM_PRESET_TEMP_STEP,
)


@pytest.fixture
def mock_entry():
    """Config entry with stable entry_id for unique_id."""
    entry = MagicMock()
    entry.data = {}
    entry.entry_id = "test-entry-id"
    entry.options = {}
    return entry


@pytest.fixture
def mock_coordinator(mock_entry):
    """Mock coordinator with configurable controller data."""
    coordinator = MagicMock()
    coordinator.entry = mock_entry
    coordinator.last_update_success = True
    return coordinator


class TestKospelRoomPresetNumberEntity:
    """Tests for native value, bounds, and async_set_native_value."""

    def test_native_value_reads_controller_property(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value returns the Ekco_M3 property matching translation_key."""
        mock_controller = MagicMock()
        mock_controller.room_temperature_economy = 20.5
        mock_coordinator.data = mock_controller

        entity = KospelRoomPresetNumberEntity(
            mock_coordinator,
            mock_entry,
            "room_temperature_economy",
            "set_room_temperature_economy",
        )

        assert entity.native_value == 20.5

    def test_native_value_returns_none_when_property_missing(
        self, mock_coordinator, mock_entry
    ) -> None:
        """native_value returns None when controller has no such attribute."""
        mock_controller = object()
        mock_coordinator.data = mock_controller

        entity = KospelRoomPresetNumberEntity(
            mock_coordinator,
            mock_entry,
            "room_temperature_economy",
            "set_room_temperature_economy",
        )

        assert entity.native_value is None

    def test_temperature_bounds_and_step(self, mock_coordinator, mock_entry) -> None:
        """Entity exposes 10–25 °C range and 0.1 step (matches module constants)."""
        entity = KospelRoomPresetNumberEntity(
            mock_coordinator,
            mock_entry,
            "room_temperature_comfort",
            "set_room_temperature_comfort",
        )

        assert entity.native_min_value == ROOM_PRESET_TEMP_MIN == 10.0
        assert entity.native_max_value == ROOM_PRESET_TEMP_MAX == 25.0
        assert entity.native_step == ROOM_PRESET_TEMP_STEP == 0.1

    def test_entity_category_is_config(self, mock_coordinator, mock_entry) -> None:
        """Room presets appear under device Configuration (with max boiler power)."""
        entity = KospelRoomPresetNumberEntity(
            mock_coordinator,
            mock_entry,
            "room_temperature_economy",
            "set_room_temperature_economy",
        )
        assert entity._attr_entity_category == "config"

    @pytest.mark.asyncio
    async def test_async_set_native_value_calls_setter_and_refreshes(
        self, mock_coordinator, mock_entry
    ) -> None:
        """Setter on controller is awaited; coordinator refresh runs after delay."""
        mock_controller = MagicMock()
        mock_controller.room_temperature_economy = 20.0
        mock_controller.set_room_temperature_economy = AsyncMock(return_value=True)
        mock_coordinator.data = mock_controller
        mock_coordinator.async_request_refresh = AsyncMock()

        entity = KospelRoomPresetNumberEntity(
            mock_coordinator,
            mock_entry,
            "room_temperature_economy",
            "set_room_temperature_economy",
        )

        with patch(
            "custom_components.kospel.number.asyncio.sleep", new_callable=AsyncMock
        ):
            await entity.async_set_native_value(21.5)

        mock_controller.set_room_temperature_economy.assert_awaited_once_with(21.5)
        mock_coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("translation_key", "setter_name"),
        [
            ("room_temperature_economy", "set_room_temperature_economy"),
            ("room_temperature_comfort", "set_room_temperature_comfort"),
            ("room_temperature_comfort_plus", "set_room_temperature_comfort_plus"),
            ("room_temperature_comfort_minus", "set_room_temperature_comfort_minus"),
        ],
    )
    async def test_each_preset_uses_matching_setter(
        self,
        mock_coordinator,
        mock_entry,
        translation_key: str,
        setter_name: str,
    ) -> None:
        """Each preset entity calls its corresponding Ekco_M3 setter."""
        mock_controller = MagicMock()
        for _key, _setter in [
            ("room_temperature_economy", "set_room_temperature_economy"),
            ("room_temperature_comfort", "set_room_temperature_comfort"),
            ("room_temperature_comfort_plus", "set_room_temperature_comfort_plus"),
            ("room_temperature_comfort_minus", "set_room_temperature_comfort_minus"),
        ]:
            setattr(mock_controller, _setter, AsyncMock(return_value=True))
        mock_coordinator.data = mock_controller
        mock_coordinator.async_request_refresh = AsyncMock()

        entity = KospelRoomPresetNumberEntity(
            mock_coordinator, mock_entry, translation_key, setter_name
        )

        with patch(
            "custom_components.kospel.number.asyncio.sleep", new_callable=AsyncMock
        ):
            await entity.async_set_native_value(22.0)

        called = getattr(mock_controller, setter_name)
        called.assert_awaited_once_with(22.0)
