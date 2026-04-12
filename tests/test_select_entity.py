"""Tests for Kospel boiler max power select entity."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kospel_cmi.registers.enums import BoilerMaxPowerIndex

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
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
entity_mod = sys.modules["homeassistant.helpers.entity"]
entity_mod.EntityCategory = MagicMock()
entity_mod.EntityCategory.CONFIG = "config"
entity_mod.DeviceInfo = lambda **kwargs: kwargs
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()


class _CoordinatorEntityBase:
    """Minimal CoordinatorEntity stand-in for testing."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def async_write_ha_state(self) -> None:
        """No-op: real HA schedules state write."""

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class _SelectEntityBase:
    """Minimal SelectEntity stand-in for testing."""

    @property
    def options(self) -> list[str]:
        """Mirror HA SelectEntity."""
        return self._attr_options


select_mock = MagicMock()
select_mock.SelectEntity = _SelectEntityBase
sys.modules["homeassistant.components.select"] = select_mock

sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = (
    _CoordinatorEntityBase
)

from custom_components.kospel.select import (  # noqa: E402
    KospelBoilerMaxPowerSelectEntity,
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
    coordinator.communication_ok = True
    return coordinator


class TestKospelBoilerMaxPowerSelectEntity:
    """Tests for options, current_option, and async_select_option."""

    def test_options_order_and_numeric_strings(self, mock_coordinator, mock_entry) -> None:
        """Entity exposes four kW options in index order 0..3."""
        entity = KospelBoilerMaxPowerSelectEntity(mock_coordinator, mock_entry)
        assert entity.options == ["2", "4", "6", "8"]

    def test_current_option_maps_enum(
        self, mock_coordinator, mock_entry
    ) -> None:
        """current_option returns kW string for controller.boiler_max_power_index."""
        mock_controller = MagicMock()
        mock_controller.boiler_max_power_index = BoilerMaxPowerIndex.KW_6
        mock_coordinator.data = mock_controller

        entity = KospelBoilerMaxPowerSelectEntity(mock_coordinator, mock_entry)
        assert entity.current_option == "6"

    def test_current_option_none_when_unknown(
        self, mock_coordinator, mock_entry
    ) -> None:
        """current_option is None when library reports unknown index."""
        mock_controller = MagicMock()
        mock_controller.boiler_max_power_index = None
        mock_coordinator.data = mock_controller

        entity = KospelBoilerMaxPowerSelectEntity(mock_coordinator, mock_entry)
        assert entity.current_option is None

    @pytest.mark.asyncio
    async def test_async_select_option_calls_setter_and_refreshes(
        self, mock_coordinator, mock_entry
    ) -> None:
        """set_boiler_max_power_index is awaited; coordinator refresh runs."""
        mock_controller = MagicMock()
        mock_controller.set_boiler_max_power_index = AsyncMock(return_value=True)
        mock_coordinator.data = mock_controller
        mock_coordinator.async_request_refresh = AsyncMock()

        entity = KospelBoilerMaxPowerSelectEntity(mock_coordinator, mock_entry)

        with patch(
            "custom_components.kospel.select.asyncio.sleep", new_callable=AsyncMock
        ):
            await entity.async_select_option("4")

        mock_controller.set_boiler_max_power_index.assert_awaited_once()
        call_arg = mock_controller.set_boiler_max_power_index.await_args[0][0]
        assert call_arg == BoilerMaxPowerIndex.KW_4
        mock_coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_select_option_invalid_raises(
        self, mock_coordinator, mock_entry
    ) -> None:
        """Invalid option string raises ValueError."""
        mock_controller = MagicMock()
        mock_coordinator.data = mock_controller

        entity = KospelBoilerMaxPowerSelectEntity(mock_coordinator, mock_entry)

        with pytest.raises(ValueError, match="Invalid option"):
            await entity.async_select_option("not_a_step")
