"""Tests for Kospel services."""

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Mock homeassistant before importing integration modules.
class _HAModule:
    __path__ = []
    __file__ = ""
    __name__ = "homeassistant"
    __spec__ = None

_ha = _HAModule()
if "homeassistant" not in sys.modules:
    sys.modules["homeassistant"] = _ha
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()

def dummy_callback(func):
    return func

core_mock = MagicMock()
core_mock.callback = dummy_callback
sys.modules["homeassistant.core"] = core_mock

class _FakeHomeAssistantError(Exception):
    """Stand-in for HomeAssistantError in tests."""

sys.modules["homeassistant.exceptions"] = SimpleNamespace(
    HomeAssistantError=_FakeHomeAssistantError,
    ConfigEntryNotReady=Exception,
)
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.config_validation"] = MagicMock()
sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

from custom_components.kospel.services import (
    async_setup_services,
    SERVICE_SET_PROGRAM,
    SERVICE_SET_WEEKDAY_SCHEDULE,
)
from custom_components.kospel.const import DOMAIN
from kospel_cmi.registers.enums import ScheduleType

HomeAssistantError = _FakeHomeAssistantError

@pytest.fixture
def hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock()
    hass.services.has_service.return_value = False
    hass.data = {DOMAIN: {}}
    return hass


def test_async_setup_services_registers_services(hass):
    """Test that services are registered."""
    async_setup_services(hass)
    assert hass.services.async_register.call_count == 4
    calls = hass.services.async_register.call_args_list
    assert calls[0][0][1] == SERVICE_SET_PROGRAM
    assert calls[1][0][1] == SERVICE_SET_WEEKDAY_SCHEDULE


@pytest.mark.asyncio
async def test_set_program_service(hass):
    """Test successful set_program service call."""
    async_setup_services(hass)
    handle_set_program = hass.services.async_register.call_args_list[0][0][2]

    # Mock device registry
    device_registry = MagicMock()
    device = MagicMock()
    device.config_entries = ["test-entry-id"]
    device_registry.async_get.return_value = device
    
    # Mock coordinator and controller
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    controller = MagicMock()
    controller.set_program = AsyncMock()
    coordinator.heater_controller = controller
    coordinator.async_request_refresh = AsyncMock()
    hass.data[DOMAIN]["test-entry-id"] = coordinator

    with patch("custom_components.kospel.services.dr.async_get", return_value=device_registry), \
         patch("custom_components.kospel.services.asyncio.sleep", new_callable=AsyncMock):
        
        call = MagicMock()
        call.data = {
            "device_id": "test_device_id",
            "schedule_type": "ch",
            "program_id": 1,
            "slots": [
                {"start_minute": 0, "stop_minute": 60}
            ]
        }
        
        await handle_set_program(call)
        
        controller.set_program.assert_called_once()
        args, _ = controller.set_program.call_args
        assert args[0] == ScheduleType.CH
        assert args[1] == 1
        assert len(args[2].slots) == 1
        assert args[2].slots[0].start_minute == 0
        assert args[2].slots[0].stop_minute == 60


@pytest.mark.asyncio
async def test_set_program_validation_error(hass):
    """Test set_program with validation failure."""
    async_setup_services(hass)
    handle_set_program = hass.services.async_register.call_args_list[0][0][2]

    with pytest.raises(Exception, match="Validation failed"):
        call = MagicMock()
        call.data = {
            "device_id": "test_device_id",
            "schedule_type": "ch",
            "program_id": 1,
            "slots": [
                {"start_minute": 100, "stop_minute": 50}  # Invalid: stop before start
            ]
        }
        await handle_set_program(call)


@pytest.mark.asyncio
async def test_set_weekday_schedule_service(hass):
    """Test successful set_weekday_schedule service call."""
    async_setup_services(hass)
    handle_set_weekday_schedule = hass.services.async_register.call_args_list[1][0][2]

    # Mock device registry
    device_registry = MagicMock()
    device = MagicMock()
    device.config_entries = ["test-entry-id"]
    device_registry.async_get.return_value = device
    
    # Mock coordinator and controller
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    controller = MagicMock()
    controller.set_weekday_schedule = AsyncMock()
    coordinator.heater_controller = controller
    coordinator.async_request_refresh = AsyncMock()
    hass.data[DOMAIN]["test-entry-id"] = coordinator

    with patch("custom_components.kospel.services.dr.async_get", return_value=device_registry), \
         patch("custom_components.kospel.services.asyncio.sleep", new_callable=AsyncMock):
        
        call = MagicMock()
        call.data = {
            "device_id": "test_device_id",
            "schedule_type": "dhw",
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6,
            "sunday": 7
        }
        
        await handle_set_weekday_schedule(call)
        
        controller.set_weekday_schedule.assert_called_once()
        args, _ = controller.set_weekday_schedule.call_args
        assert args[0] == ScheduleType.DHW
        schedule = args[1]
        assert schedule.monday == 1
        assert schedule.tuesday == 2
        assert schedule.sunday == 7

@pytest.mark.asyncio
async def test_get_program_service(hass):
    """Test getting a program schedule."""
    async_setup_services(hass)
    handle_get_program = hass.services.async_register.call_args_list[2][0][2]

    # Mock device registry
    device_registry = MagicMock()
    device = MagicMock()
    device.config_entries = ["test-entry-id"]
    device_registry.async_get.return_value = device
    
    # Mock coordinator and controller
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    controller = MagicMock()
    
    from kospel_cmi.controller.schedules import DailyProgram, ScheduleTimeSlot
    from kospel_cmi.registers.enums import ScheduleType
    
    mock_program = DailyProgram(slots=[
        ScheduleTimeSlot(start_minute=100, stop_minute=200, preset_id=1),
        ScheduleTimeSlot(start_minute=300, stop_minute=400, preset_id=None),
    ])
    controller.get_program.return_value = mock_program
    coordinator.heater_controller = controller
    hass.data[DOMAIN]["test-entry-id"] = coordinator

    with patch("custom_components.kospel.services.dr.async_get", return_value=device_registry):
        call = MagicMock()
        call.data = {
            "device_id": "test_device_id",
            "schedule_type": "ch",
            "program_id": 2,
        }
        
        response = await handle_get_program(call)
        
        controller.get_program.assert_called_once_with(ScheduleType.CH, 2)
        assert response == {
            "slots": [
                {"start_minute": 100, "stop_minute": 200, "preset_id": 1},
                {"start_minute": 300, "stop_minute": 400},
            ]
        }


@pytest.mark.asyncio
async def test_get_weekday_schedule_service(hass):
    """Test getting a weekday schedule."""
    async_setup_services(hass)
    handle_get_weekday_schedule = hass.services.async_register.call_args_list[3][0][2]

    # Mock device registry
    device_registry = MagicMock()
    device = MagicMock()
    device.config_entries = ["test-entry-id"]
    device_registry.async_get.return_value = device
    
    # Mock coordinator and controller
    coordinator = MagicMock()
    coordinator.entry = MagicMock()
    controller = MagicMock()
    
    from kospel_cmi.controller.schedules import WeekdaySchedule
    from kospel_cmi.registers.enums import ScheduleType
    
    mock_schedule = WeekdaySchedule(
        monday=1, tuesday=2, wednesday=3, thursday=4, friday=5, saturday=6, sunday=7
    )
    controller.get_weekday_schedule.return_value = mock_schedule
    coordinator.heater_controller = controller
    hass.data[DOMAIN]["test-entry-id"] = coordinator

    with patch("custom_components.kospel.services.dr.async_get", return_value=device_registry):
        call = MagicMock()
        call.data = {
            "device_id": "test_device_id",
            "schedule_type": "dhw",
        }
        
        response = await handle_get_weekday_schedule(call)
        
        controller.get_weekday_schedule.assert_called_once_with(ScheduleType.DHW)
        assert response == {
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6,
            "sunday": 7,
        }
