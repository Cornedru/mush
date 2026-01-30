from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data, get_data_or_none
from tools.logger import log, WARN, ERROR
from tools.conf import YOSHI_URL


class CorrectorNotLoggedInFlag(IFlag):
    @property
    def name(self) -> str:
        return "CORRECTOR_NOT_LOGGED_IN"

    @property
    def threshold(self) -> float:
        return 0.5

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects when a correction is assigned to a corrector who is not logged in"

    def calculate(self, correction_id: str) -> Optional[float]:
        try:
            # Fetch correction data
            correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
            if not correction:
                log(WARN, "CorrectorNotLoggedInFlag", "Could not fetch correction data")
                return None

            # Get corrector login
            corrector = correction.get("corrector")
            if not corrector:
                log(WARN, "CorrectorNotLoggedInFlag", "No corrector data in correction")
                return None

            corrector_login = corrector.get("login")
            if not corrector_login:
                log(WARN, "CorrectorNotLoggedInFlag", "No corrector login found")
                return None

            # Use get_data_or_none since 404 means "not logged in" (expected case)
            active_session = get_data_or_none(f"{YOSHI_URL}/active-sessions/by-login/{corrector_login}")

            if active_session and active_session.get("login"):
                return 0.0
            else:
                self.details = f"Corrector {corrector_login} was not logged in at the time of correction subscription"
                return 1.0

        except Exception as e:
            log(ERROR, "CorrectorNotLoggedInFlag", f"Error calculating flag: {e}")
            return None
