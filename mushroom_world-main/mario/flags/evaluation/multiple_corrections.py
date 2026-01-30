from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data
from tools.conf import YOSHI_URL
from tools.converters import parse_timestamp

class MultipleCorrectionsFlag(IFlag):
    """
    Detects multiple corrections happening at the same time or close together.

    This flag identifies cases where a corrector performs multiple evaluations
    simultaneously or very close together, which may indicate rushed or
    inattentive corrections.

    Algorithm:
    1. Compare current correction timestamp with all other corrections for same push
    2. Return 1.0 if exact match (same timestamp)
    3. Return 0.5 if within ±15 minutes
    4. Return 0.0 otherwise

    Returns:
        1.0: At least one correction at exact same time
        0.5: At least one correction within ±15 minutes
        0.0: No corrections close in time
    """

    @property
    def name(self) -> str:
        return "MULTIPLE_CORRECTIONS"

    @property
    def threshold(self) -> float:
        return 0.5

    @property
    def sufficient(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Detects multiple corrections happening at the same time"

    def calculate(self, correction_id: str) -> Optional[float]:
        # Fetch current correction
        correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
        if not correction:
            return None

        current_begin_at = correction.get("begin_at")
        current_time = parse_timestamp(current_begin_at)
        if not current_time:
            return None

        # Fetch push corrections
        push_id = correction.get("push", {}).get("id")
        if not push_id:
            return None

        push_corrections = get_data(f"{YOSHI_URL}/corrections/by_push/{push_id}")
        if not isinstance(push_corrections, list) or len(push_corrections) <= 1:
            return 0.0

        close_match = False

        for corr in push_corrections:
            # Skip the current correction itself
            if corr.get("id") == correction.get("id"):
                continue

            other_begin_at = corr.get("begin_at")
            if not other_begin_at:
                continue

            # Check for exact match
            if other_begin_at == current_begin_at:
                self.details = "At least one correction begins at the same time"
                return 1.0

            # Check for ±15 minute match
            else:
                other_time = parse_timestamp(other_begin_at)
                if other_time:
                    time_diff = abs((current_time - other_time).total_seconds())
                    if time_diff <= 15 * 60:
                        close_match = True

        if close_match:
            self.details = "At least one correction begins within ±15 minutes of this one."
            return 0.5
        else:
            return 0.0
