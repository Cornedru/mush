import math
from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data
from tools.logger import log, WARN, ERROR
from tools.conf import YOSHI_URL


def f(x: float) -> float:
    """
    Returns a float in the range [0.0, 1.0].
    """
    if x <= 5:
        return 1.0
    elif x >= 50:
        return 0.0
    else:
        return math.exp(-(math.log(2) / 25) * (x - 5))

class LowAttendanceFlag(IFlag):
    @property
    def name(self) -> str:
        return "LOW_ATTENDANCE"

    @property
    def threshold(self) -> float:
        return 0.5

    @property
    def sufficient(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Detects corrections performed when school attendance is low"

    def calculate(self, correction_id: str) -> Optional[float]:
        try:
            # Fetch active sessions from Yoshi API
            active_sessions_data = get_data(f"{YOSHI_URL}/active-sessions")

            if not isinstance(active_sessions_data, list):
                log(WARN, "LowAttendanceFlag", "Active sessions data is not a list")
                return None

            active_sessions = len(active_sessions_data)
            self.details = f"{active_sessions} students logged in."

            return f(active_sessions)

        except Exception as e:
            log(ERROR, "LowAttendanceFlag", f"Error calculating low attendance flag: {e}")
            return None
