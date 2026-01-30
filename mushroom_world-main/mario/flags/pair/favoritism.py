from mario_types.IFlag import IFlag
from typing import Optional
import math
from tools.handle_requests import get_data
from tools.conf import YOSHI_URL


class FavoritismFlag(IFlag):
    """
    Detects grade-based favoritism in corrections.

    This flag identifies cases where a corrector gives significantly higher
    grades to specific students compared to their average grading pattern.

    Algorithm:
    1. Collect grades given to corrected students vs. all others
    2. Calculate mean grade for corrected students vs. all corrections
    3. Compare the difference using arctan normalization
    4. Require minimum correction threshold to avoid false positives

    Returns:
        Float in [0, 1]: atan-normalized favoritism score
        None: If corrector has fewer than minimum corrections
        0: If no favoritism detected
    """

    _ALL = "ALL"

    @property
    def name(self) -> str:
        return "FAVORITISM"

    @property
    def threshold(self) -> float:
        # Threshold applied to atan-normalized values
        return math.atan(0.3)

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects grade-based favoritism in corrections"

    def calculate(self, correction_id: str) -> Optional[float]:
        # Fetch current correction
        correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
        if not correction:
            return None

        corrector_id = correction.get("corrector", {}).get("id")
        if not corrector_id:
            return None

        correcteds = [c["login"] for c in correction.get("push", {}).get("correcteds", [])]

        # Fetch corrector's corrections
        corrector_corrections = get_data(f"{YOSHI_URL}/corrections/by_corrector/{corrector_id}")
        if not isinstance(corrector_corrections, list):
            return None

        marks = {
            self._ALL: []
        }

        for corrected in correcteds:
            for corr in corrector_corrections:
                mark = corr.get("mark")
                if mark is None:
                    continue
                corr_correcteds = [c["login"] for c in corr.get("push", {}).get("correcteds", [])]
                if corrected in corr_correcteds:
                    if corrected not in marks:
                        marks[corrected] = []
                    marks[corrected].append(mark)
                else:
                    marks[self._ALL].append(mark)

        min_corrections = 5

        if len(marks[self._ALL]) < min_corrections:
            return None

        if len(marks[self._ALL]) == 0:
            return None

        mean_all = sum(marks[self._ALL]) / len(marks[self._ALL])
        mean_cor = 0
        for key in marks:
            if key == self._ALL:
                continue
            if len(marks[key]) == 0:
                continue
            current_mean = sum(marks[key]) / len(marks[key])
            if mean_cor < current_mean:
                mean_cor = current_mean

        if mean_all >= mean_cor:
            return 0

        if mean_all == 0:
            if mean_cor != 0:
                return 1
            return 0
        return math.atan(mean_cor / mean_all - 1)
