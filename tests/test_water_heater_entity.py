"""Tests for unified Kospel WaterHeaterEntity (read-only EKCO.M3 and writable PPE.4)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kospel_cmi.registers.enums import DhwMode


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


class _CoordinatorEntityBase:
    """Minimal CoordinatorEntity stand-in for testing."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def async_write_ha_state(self) -> None:
        pass

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

from custom_components.kospel.water_heater import (  # noqa: E402
    PROFILE_OPTIONS,
    STATE_ECO,
    STATE_OFF,
    STATE_PERFORMANCE,
    WaterHeaterEntity,
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
    coordinator.communication_ok = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def water_heater_entity(mock_coordinator):
    """Create WaterHeaterEntity with mocked coordinator."""
    return WaterHeaterEntity(mock_coordinator)


class TestWaterHeaterTargetTemperature:
    """Tests for target_temperature (live supply setpoint)."""

    def test_target_temperature_returns_supply_setpoint(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns supply_setpoint regardless of dhw_mode."""
        mock_controller = MagicMock()
        mock_controller.supply_setpoint = 15.0
        mock_controller.dhw_mode = DhwMode.ANTI_FREEZE
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature == 15.0

    def test_target_temperature_returns_none_when_supply_setpoint_missing(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        """target_temperature returns None when supply_setpoint is unavailable."""
        mock_controller = MagicMock()
        mock_controller.supply_setpoint = None
        mock_coordinator.data = mock_controller

        assert water_heater_entity.target_temperature is None


class TestReadOnlyWaterHeaterBehavior:
    """Tests for read-only controller (water_heater_writable = False, e.g. EkcoM3)."""

    def test_current_operation_eco_when_dhw_mode_economy(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.water_heater_writable = False
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        mock_controller.dhw_mode = DhwMode.ECONOMY
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_ECO

    def test_current_operation_off_when_water_heater_disabled(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.water_heater_writable = False
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.DISABLED
        mock_controller.dhw_mode = DhwMode.ECONOMY
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_OFF

    def test_current_operation_performance_when_dhw_mode_comfort(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        from kospel_cmi.registers.enums import WaterHeaterEnabled

        mock_controller = MagicMock()
        mock_controller.water_heater_writable = False
        mock_controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        mock_controller.dhw_mode = DhwMode.COMFORT
        mock_coordinator.data = mock_controller

        assert water_heater_entity.current_operation == STATE_PERFORMANCE

    @pytest.mark.asyncio
    async def test_writes_ignored_when_not_writable(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        mock_controller = MagicMock()
        mock_controller.water_heater_writable = False
        mock_controller.set_manual_heating = AsyncMock()
        mock_controller.set_active_profile = AsyncMock()
        mock_coordinator.data = mock_controller

        await water_heater_entity.async_set_temperature(temperature=45.0)
        await water_heater_entity.async_set_operation_mode(STATE_PERFORMANCE)

        mock_controller.set_manual_heating.assert_not_awaited()
        mock_controller.set_active_profile.assert_not_awaited()


class TestWritableWaterHeaterBehavior:
    """Tests for writable controller (water_heater_writable = True, e.g. Ppe4)."""

    def test_operation_list_and_current_operation_use_profiles(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        mock_controller = MagicMock()
        mock_controller.water_heater_writable = True
        mock_controller.active_profile = 2
        mock_controller.water_min_temperature = 20.0
        mock_controller.water_max_temperature = 55.0
        mock_coordinator.data = mock_controller

        assert water_heater_entity.operation_list == PROFILE_OPTIONS
        assert water_heater_entity.current_operation == "profile_2"
        assert water_heater_entity.min_temp == 20.0
        assert water_heater_entity.max_temp == 55.0

    @pytest.mark.asyncio
    async def test_set_temperature_writes_manual_heating_and_refreshes(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        mock_controller = MagicMock()
        mock_controller.water_heater_writable = True
        mock_controller.set_manual_heating = AsyncMock()
        mock_coordinator.data = mock_controller

        with patch(
            "custom_components.kospel.water_heater.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await water_heater_entity.async_set_temperature(temperature=44.0)

        mock_controller.set_manual_heating.assert_awaited_once_with(44.0)
        mock_coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_operation_mode_writes_active_profile_and_refreshes(
        self, water_heater_entity, mock_coordinator
    ) -> None:
        mock_controller = MagicMock()
        mock_controller.water_heater_writable = True
        mock_controller.set_active_profile = AsyncMock()
        mock_coordinator.data = mock_controller

        with patch(
            "custom_components.kospel.water_heater.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await water_heater_entity.async_set_operation_mode("profile_3")

        mock_controller.set_active_profile.assert_awaited_once_with(3)
        mock_coordinator.async_request_refresh.assert_awaited_once()
