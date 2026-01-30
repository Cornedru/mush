from tools.logger import log, ERROR

# Import all flags
from flags.pair.correction_network import CorrectionNetworkFlag
from flags.pair.favoritism import FavoritismFlag
from flags.pair.friendship import FriendshipFlag
from flags.pair.statistical_pair import StatisticalPairFlag
from flags.evaluation.multiple_corrections import MultipleCorrectionsFlag
from flags.evaluation.low_attendance import LowAttendanceFlag
from flags.evaluation.time_until_correction import TimeUntilCorrectionFlag
from flags.evaluation.time_from_slot_creation_to_booking import TimeFromSlotCreationToBookingFlag
from flags.corrector.corrector_not_logged_in import CorrectorNotLoggedInFlag
from flags.correcteds.correcteds_not_logged_in import CorrectedsNotLoggedInFlag

# All registered flags
FLAGS = [
    CorrectionNetworkFlag(),
    FavoritismFlag(),
    FriendshipFlag(),
    StatisticalPairFlag(),
    MultipleCorrectionsFlag(),
    LowAttendanceFlag(),
    TimeUntilCorrectionFlag(),
    TimeFromSlotCreationToBookingFlag(),
    CorrectorNotLoggedInFlag(),
    CorrectedsNotLoggedInFlag(),
]


def calculate_flags(correction_id):
    """
    Calculate all flags for a given correction.

    Each flag fetches its own data from Yoshi API and performs its calculation.

    Args:
        correction_id: ID of the correction to analyze

    Returns:
        Dict mapping flag names to {value, is_triggered, sufficient, description, details}
    """
    result = {}

    for flag in FLAGS:
        try:
            value = flag.calculate(correction_id)

            if value is not None:
                flag.validate_result(value)
                flag.result = value
                result[flag.name] = {
                    "value": value,
                    "threshold": flag.threshold,
                    "is_triggered": flag.is_triggered(),
                    "sufficient": flag.sufficient,
                    "description": flag.description,
                    "details": flag.details
                }
        except Exception as e:
            log(ERROR, "Flags", f"Error calculating flag {flag.name}: {e}")
            continue

    return result
