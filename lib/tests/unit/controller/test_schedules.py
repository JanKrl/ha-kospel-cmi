import pytest

from kospel_cmi.controller.schedules import (
    DailyProgram,
    ScheduleTimeSlot,
    ScheduleValidationError,
    WeekdaySchedule,
    validate_program,
)
from kospel_cmi.registers.enums import ChPreset


def test_schedule_time_slot():
    slot = ScheduleTimeSlot(start_minute=480, stop_minute=600, preset_id=ChPreset.COMFORT)
    assert slot.start_minute == 480
    assert slot.stop_minute == 600
    assert slot.preset_id == ChPreset.COMFORT
    assert not slot.is_empty


def test_empty_schedule_time_slot():
    slot = ScheduleTimeSlot(start_minute=-1, stop_minute=-1, preset_id=-1)
    assert slot.is_empty


def test_validate_program_valid():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(0, 120, ChPreset.COMFORT),
            ScheduleTimeSlot(120, 240, ChPreset.ANTIFREEZE),
        ]
    )
    # Should not raise
    validate_program(program)


def test_validate_program_overlap():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(0, 120, ChPreset.COMFORT),
            ScheduleTimeSlot(60, 240, ChPreset.ANTIFREEZE),
        ]
    )
    with pytest.raises(ScheduleValidationError, match="(?i)overlap"):
        validate_program(program)


def test_validate_program_overlap_exact_start():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(0, 120, ChPreset.COMFORT),
            ScheduleTimeSlot(0, 60, ChPreset.ANTIFREEZE),
        ]
    )
    with pytest.raises(ScheduleValidationError, match="(?i)overlap"):
        validate_program(program)


def test_validate_program_invalid_duration():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(120, 120, ChPreset.COMFORT),
        ]
    )
    with pytest.raises(ScheduleValidationError, match="(?i)strictly greater"):
        validate_program(program)


def test_validate_program_inverted_duration():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(120, 60, ChPreset.COMFORT),
        ]
    )
    with pytest.raises(ScheduleValidationError, match="(?i)strictly greater"):
        validate_program(program)


def test_validate_program_with_empty_slots():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(0, 120, ChPreset.COMFORT),
            ScheduleTimeSlot(-1, -1, -1),
            ScheduleTimeSlot(180, 240, ChPreset.COMFORT),
        ]
    )
    # Should not raise
    validate_program(program)


def test_validate_program_too_many_slots():
    program = DailyProgram(
        slots=[
            ScheduleTimeSlot(0, 60, 1),
            ScheduleTimeSlot(60, 120, 1),
            ScheduleTimeSlot(120, 180, 1),
            ScheduleTimeSlot(180, 240, 1),
            ScheduleTimeSlot(240, 300, 1),
            ScheduleTimeSlot(300, 360, 1),
        ]
    )
    with pytest.raises(ScheduleValidationError, match="maximum of 5"):
        validate_program(program)


def test_weekday_schedule():
    schedule = WeekdaySchedule(
        monday=1,
        tuesday=2,
        wednesday=3,
        thursday=4,
        friday=5,
        saturday=6,
        sunday=7,
    )
    assert schedule.monday == 1
    assert schedule.sunday == 7
