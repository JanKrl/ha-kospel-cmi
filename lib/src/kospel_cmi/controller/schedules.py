from dataclasses import dataclass
from typing import Optional


class ScheduleValidationError(ValueError):
    """Exception raised for invalid schedule configurations."""
    pass


@dataclass
class ScheduleTimeSlot:
    """A time slot in a daily program."""

    start_minute: int
    stop_minute: int
    preset_id: Optional[int] = None

    @property
    def is_empty(self) -> bool:
        """Check if the slot is marked as empty (-1 or 65535)."""
        return self.start_minute in (-1, 65535) and self.stop_minute in (-1, 65535)


@dataclass
class DailyProgram:
    """A full daily program containing up to 5 time slots."""

    slots: list[ScheduleTimeSlot]


@dataclass
class WeekdaySchedule:
    """Mapping of days of the week to DailyProgram IDs (1-8)."""

    monday: int
    tuesday: int
    wednesday: int
    thursday: int
    friday: int
    saturday: int
    sunday: int


def validate_program(program: DailyProgram) -> None:
    """
    Validate a daily program.

    Rules:
    - Maximum of 5 time slots
    - Stop time must be strictly greater than start time for each slot
    - Slots must not overlap
    """
    if len(program.slots) > 5:
        raise ScheduleValidationError("A daily program can have a maximum of 5 time slots")

    valid_slots = [slot for slot in program.slots if not slot.is_empty]

    for slot in valid_slots:
        if slot.stop_minute <= slot.start_minute:
            raise ScheduleValidationError(
                f"Invalid slot: stop time ({slot.stop_minute}) must be strictly greater "
                f"than start time ({slot.start_minute})"
            )

    sorted_slots = sorted(valid_slots, key=lambda x: x.start_minute)

    for i in range(len(sorted_slots) - 1):
        current_slot = sorted_slots[i]
        next_slot = sorted_slots[i + 1]

        if next_slot.start_minute < current_slot.stop_minute:
            raise ScheduleValidationError(
                f"Overlapping slots: ({current_slot.start_minute}-{current_slot.stop_minute}) "
                f"and ({next_slot.start_minute}-{next_slot.stop_minute})"
            )
