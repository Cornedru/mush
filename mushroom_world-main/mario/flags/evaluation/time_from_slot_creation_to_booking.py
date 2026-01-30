import math

from flask.sansio.scaffold import F
from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data
from tools.logger import log, WARN, ERROR
from tools.conf import YOSHI_URL
from tools.converters import parse_timestamp
from datetime import datetime, timezone


def f(m: float) -> float:
    if m < 0:
        return 1.0
    if m >= 30:
        return 0.0

    k = math.log(2) / 10
    score = math.exp(-k * m)

    if m <= 7:
        score = max(score, 0.8)

    return max(0.0, min(1.0, score))

class TimeFromSlotCreationToBookingFlag(IFlag):
    @property
    def name(self) -> str:
        return "TIME_FROM_SLOT_CREATION_TO_BOOKING"

    @property
    def threshold(self) -> float:
        return 0.8

    @property
    def sufficient(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Measures the time difference between slot creation and correction booking."

    def calculate(self, correction_id: str) -> Optional[float]:
        try:
            # Fetch correction data
            correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
            if not correction:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "Could not fetch correction data")
                return None

            corrector = correction.get("corrector")
            if not corrector:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "No corrector data in correction")
                return None

            corrector_id = corrector.get("id")
            if not corrector_id:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "No corrector ID found")
                return None

            begin_at_str = correction.get("begin_at")
            if not begin_at_str:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "No begin_at timestamp in correction")
                return None

            begin_at = parse_timestamp(begin_at_str)
            if not begin_at:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "Could not parse begin_at timestamp")
                return None

            all_slots = get_data(f"{YOSHI_URL}/slots")
            if not isinstance(all_slots, list):
                log(WARN, "TimeFromSlotCreationToBookingFlag", "Could not fetch slots data")
                return None

            matching_slot = None
            for slot in all_slots:
                slot_student_id = slot.get("student_id")
                slot_begin_at_str = slot.get("begin_at")

                if slot_student_id == corrector_id and slot_begin_at_str == begin_at_str:
                    matching_slot = slot
                    break

            if not matching_slot:
                log(WARN, "TimeFromSlotCreationToBookingFlag",
                    f"Could not find slot for corrector {corrector_id} at {begin_at_str}")
                return None

            slot_created_at_str = matching_slot.get("created_at")
            if not slot_created_at_str:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "No created_at in slot")
                return None

            slot_created_at = parse_timestamp(slot_created_at_str)
            if not slot_created_at:
                log(WARN, "TimeFromSlotCreationToBookingFlag", "Could not parse slot created_at")
                return None

            current_time = datetime.now(timezone.utc)

            time_diff_seconds = abs((current_time - slot_created_at).total_seconds())
            minutes, secs = divmod(int(time_diff_seconds), 60)

            score = f(minutes)

            if score > 0.0:
                self.details = f"The correction was booked about {minutes}m{secs:02d}s after slot creation"
            return score

        except Exception as e:
            log(ERROR, "TimeFromSlotCreationToBookingFlag", f"Error calculating flag: {e}")
            return None
