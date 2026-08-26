import asyncio
import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError

from kospel_cmi.controller.schedules import (
    DailyProgram,
    ScheduleTimeSlot,
    WeekdaySchedule,
    validate_program,
    ScheduleValidationError,
)
from kospel_cmi.registers.enums import ScheduleType
from kospel_cmi import KospelError

from .const import DOMAIN, get_refresh_delay_after_set

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_PROGRAM = "set_program"
SERVICE_SET_WEEKDAY_SCHEDULE = "set_weekday_schedule"
SERVICE_GET_PROGRAM = "get_program"
SERVICE_GET_WEEKDAY_SCHEDULE = "get_weekday_schedule"

# Schema definitions
SLOT_SCHEMA = vol.Schema(
    {
        vol.Required("start_minute"): cv.positive_int,
        vol.Required("stop_minute"): cv.positive_int,
        vol.Optional("preset_id"): cv.positive_int,
    }
)

SET_PROGRAM_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id", default=""): cv.string,
        vol.Required("schedule_type"): vol.In(["ch", "dhw", "circulation"]),
        vol.Required("program_id"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("slots"): vol.All(cv.ensure_list, [SLOT_SCHEMA]),
    }
)

SET_WEEKDAY_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id", default=""): cv.string,
        vol.Required("schedule_type"): vol.In(["ch", "dhw", "circulation"]),
        vol.Required("monday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("tuesday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("wednesday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("thursday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("friday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("saturday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("sunday"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
    }
)

GET_PROGRAM_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id", default=""): cv.string,
        vol.Required("schedule_type"): vol.In(["ch", "dhw", "circulation"]),
        vol.Required("program_id"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
    }
)

GET_WEEKDAY_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id", default=""): cv.string,
        vol.Required("schedule_type"): vol.In(["ch", "dhw", "circulation"]),
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Kospel services."""

    def _get_coordinator_from_device_id(device_id: str):
        coordinators = hass.data.get(DOMAIN, {})
        active_coordinators = {
            k: v for k, v in coordinators.items() if not str(k).startswith("_")
        }

        if not active_coordinators:
            raise HomeAssistantError("No active Kospel integration instances found")

        if device_id:
            # 1. Device Registry ID
            device_registry = dr.async_get(hass)
            if device := device_registry.async_get(device_id):
                for config_entry_id in device.config_entries:
                    if coordinator := active_coordinators.get(config_entry_id):
                        return coordinator

            # 2. Entity ID (e.g. climate.heater)
            entity_registry = er.async_get(hass)
            if entity := entity_registry.async_get(device_id):
                if entity.config_entry_id and (
                    coordinator := active_coordinators.get(entity.config_entry_id)
                ):
                    return coordinator

            # 3. Config Entry ID directly
            if coordinator := active_coordinators.get(device_id):
                return coordinator

            # 4. Search by numeric device_id / IP or identifier
            for coordinator in active_coordinators.values():
                entry_data = coordinator.entry.data
                if (
                    str(entry_data.get("device_id")) == str(device_id)
                    or entry_data.get("heater_ip") == str(device_id)
                ):
                    return coordinator

        # Fallback: if only 1 active coordinator exists, auto-select it!
        if len(active_coordinators) == 1:
            return next(iter(active_coordinators.values()))

        raise HomeAssistantError(f"Kospel integration instance not found for device: {device_id}")

    async def async_handle_set_program(call: ServiceCall) -> None:
        """Handle set_program service call."""
        device_id = call.data["device_id"]
        schedule_type_str = call.data["schedule_type"]
        program_id = call.data["program_id"]
        slots_data = call.data["slots"]

        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid schedule_type: {schedule_type_str}") from err

        slots = []
        for slot in slots_data:
            slots.append(
                ScheduleTimeSlot(
                    start_minute=slot["start_minute"],
                    stop_minute=slot["stop_minute"],
                    preset_id=slot.get("preset_id")
                )
            )

        program = DailyProgram(slots=slots)

        try:
            validate_program(program)
        except ScheduleValidationError as err:
            raise HomeAssistantError(f"Validation failed: {err}") from err

        coordinator = _get_coordinator_from_device_id(device_id)
        controller = coordinator.heater_controller

        try:
            await controller.set_program(schedule_type, program_id, program)
        except KospelError as err:
            _LOGGER.error("Failed to set program: %s", err)
            raise HomeAssistantError(f"Failed to set program: {err}") from err

        await asyncio.sleep(get_refresh_delay_after_set(coordinator.entry))
        await coordinator.async_request_refresh()

    async def async_handle_set_weekday_schedule(call: ServiceCall) -> None:
        """Handle set_weekday_schedule service call."""
        device_id = call.data["device_id"]
        schedule_type_str = call.data["schedule_type"]
        
        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid schedule_type: {schedule_type_str}") from err

        schedule = WeekdaySchedule(
            monday=call.data["monday"],
            tuesday=call.data["tuesday"],
            wednesday=call.data["wednesday"],
            thursday=call.data["thursday"],
            friday=call.data["friday"],
            saturday=call.data["saturday"],
            sunday=call.data["sunday"],
        )

        coordinator = _get_coordinator_from_device_id(device_id)
        controller = coordinator.heater_controller

        try:
            await controller.set_weekday_schedule(schedule_type, schedule)
        except KospelError as err:
            _LOGGER.error("Failed to set weekday schedule: %s", err)
            raise HomeAssistantError(f"Failed to set weekday schedule: {err}") from err

        await asyncio.sleep(get_refresh_delay_after_set(coordinator.entry))
        await coordinator.async_request_refresh()

    async def async_handle_get_program(call: ServiceCall) -> ServiceResponse:
        """Handle get_program service call."""
        device_id = call.data["device_id"]
        schedule_type_str = call.data["schedule_type"]
        program_id = call.data["program_id"]

        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid schedule_type: {schedule_type_str}") from err

        coordinator = _get_coordinator_from_device_id(device_id)
        controller = coordinator.heater_controller

        try:
            program = await controller.get_program(schedule_type, program_id)
        except KospelError as err:
            _LOGGER.error("Failed to get program: %s", err)
            raise HomeAssistantError(f"Failed to get program: {err}") from err

        slots = []
        for slot in program.slots:
            if getattr(slot, "is_empty", False):
                continue
            if slot.start_minute in (-1, 65535) or slot.stop_minute in (-1, 65535):
                continue
            if slot.stop_minute <= slot.start_minute:
                continue
            slot_data = {
                "start_minute": slot.start_minute,
                "stop_minute": slot.stop_minute,
            }
            if slot.preset_id is not None:
                slot_data["preset_id"] = slot.preset_id
            slots.append(slot_data)

        return {"slots": slots}

    async def async_handle_get_weekday_schedule(call: ServiceCall) -> ServiceResponse:
        """Handle get_weekday_schedule service call."""
        device_id = call.data["device_id"]
        schedule_type_str = call.data["schedule_type"]

        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid schedule_type: {schedule_type_str}") from err

        coordinator = _get_coordinator_from_device_id(device_id)
        controller = coordinator.heater_controller

        try:
            schedule = await controller.get_weekday_schedule(schedule_type)
        except KospelError as err:
            _LOGGER.error("Failed to get weekday schedule: %s", err)
            raise HomeAssistantError(f"Failed to get weekday schedule: {err}") from err

        return {
            "monday": schedule.monday,
            "tuesday": schedule.tuesday,
            "wednesday": schedule.wednesday,
            "thursday": schedule.thursday,
            "friday": schedule.friday,
            "saturday": schedule.saturday,
            "sunday": schedule.sunday,
        }

    # Avoid registering multiple times if multiple config entries are added
    if hass.services.has_service(DOMAIN, SERVICE_SET_PROGRAM):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PROGRAM,
        async_handle_set_program,
        schema=SET_PROGRAM_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WEEKDAY_SCHEDULE,
        async_handle_set_weekday_schedule,
        schema=SET_WEEKDAY_SCHEDULE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PROGRAM,
        async_handle_get_program,
        schema=GET_PROGRAM_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_WEEKDAY_SCHEDULE,
        async_handle_get_weekday_schedule,
        schema=GET_WEEKDAY_SCHEDULE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
