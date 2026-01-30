from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data, get_data_or_none
from tools.logger import log, WARN, ERROR
from tools.conf import YOSHI_URL


class CorrectedsNotLoggedInFlag(IFlag):
    @property
    def name(self) -> str:
        return "CORRECTEDS_NOT_LOGGED_IN"

    @property
    def threshold(self) -> float:
        return 0.5

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects when corrected students are not logged in at the time of correction booking"

    def calculate(self, correction_id: str) -> Optional[float]:
        try:
            # Fetch correction data
            correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
            if not correction:
                log(WARN, "CorrectedsNotLoggedInFlag", "Could not fetch correction data")
                return None

            # Get push data to access corrected students
            push = correction.get("push")
            if not push:
                log(WARN, "CorrectedsNotLoggedInFlag", "No push data in correction")
                return None

            correcteds = push.get("correcteds", [])
            if not correcteds or len(correcteds) == 0:
                log(WARN, "CorrectedsNotLoggedInFlag", "No corrected students found")
                return None

            # Count how many corrected students are not logged in
            total_correcteds = len(correcteds)
            not_logged_in_count = 0
            not_logged_in_logins = []

            for corrected in correcteds:
                login = corrected.get("login")
                if not login:
                    continue

                # Use get_data_or_none since 404 means "not logged in" (expected case)
                active_session = get_data_or_none(f"{YOSHI_URL}/active-sessions/by-login/{login}")

                if not active_session or not active_session.get("login"):
                    not_logged_in_count += 1
                    not_logged_in_logins.append(login)

            ratio = not_logged_in_count / total_correcteds

            if not_logged_in_count > 0:
                self.details = f"{not_logged_in_count} of {total_correcteds} corrected student(s) not logged in: {', '.join(not_logged_in_logins)}."

            return ratio

        except Exception as e:
            log(ERROR, "CorrectedsNotLoggedInFlag", f"Error calculating flag: {e}")
            return None
