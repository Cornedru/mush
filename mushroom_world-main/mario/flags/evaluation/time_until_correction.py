import math
from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data
from tools.logger import log, WARN, ERROR
from tools.conf import YOSHI_URL
from tools.converters import parse_timestamp
from datetime import datetime, timezone


def f(h: float) -> float:
    if h < 4:
        return 0.0

    k = math.log(2) / 2
    return 1.0 - math.exp(-k * (h - 4))

def format_seconds_hhmm(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    return f"{hours}h{minutes:02d}m"

class TimeUntilCorrectionFlag(IFlag):
    @property
    def name(self) -> str:
        return "TIME_UNTIL_CORRECTION"

    @property
    def threshold(self) -> float:
        return 0.8

    @property
    def sufficient(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Measures the time difference between subscription and correction start time."

    def calculate(self, correction_id: str) -> Optional[float]:
        try:
            # Fetch correction data
            correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
            if not correction:
                log(WARN, "TimeUntilCorrectionFlag", "Could not fetch correction data")
                return None

            # Get begin_at timestamp
            begin_at_str = correction.get("begin_at")
            if not begin_at_str:
                log(WARN, "TimeUntilCorrectionFlag", "No begin_at timestamp in correction")
                return None

            begin_at = parse_timestamp(begin_at_str)
            if not begin_at:
                log(WARN, "TimeUntilCorrectionFlag", "Could not parse begin_at timestamp")
                return None

            current_time = datetime.now(timezone.utc)

            time_diff_seconds = abs((begin_at - current_time).total_seconds())

            score = f(time_diff_seconds / 3600)

            if score > 0.0:
                self.details = f"The correction was scheduled {format_seconds_hhmm(time_diff_seconds)} in advance"
                return score
            else:
                return 0.0

        except Exception as e:
            log(ERROR, "TimeUntilCorrectionFlag", f"Error calculating flag: {e}")
            return None
