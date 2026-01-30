"""
Statistical Pair Analysis Flag for detecting suspicious correction frequency patterns.

This flag uses statistical significance testing to identify correction pairs
where the observed frequency is significantly higher than expected by chance.
"""

from mario_types.IFlag import IFlag
from typing import Optional, Dict, Tuple
from collections import defaultdict
from tools.handle_requests import get_data
from tools.conf import YOSHI_URL
from scipy import stats
import math


class StatisticalPairFlag(IFlag):
    """
    Detects statistically significant over-representation of correction pairs.

    Algorithm:
    1. Build a correction graph from all corrections in the system
    2. Calculate observed frequency: How many times A corrected B
    3. Calculate expected frequency: (Corrections by A × Corrections received by B) / Total
    4. Use binomial test to determine if observed >> expected

    The flag uses statistical significance (p-value) rather than arbitrary thresholds,
    making it scalable and self-adjusting as the dataset grows.

    Returns:
        Float in [0, 1]: 1 - p_value (higher = more suspicious)
        None: If insufficient data for statistical analysis
    """

    MIN_OBSERVATIONS = 3  # Minimum corrections between pair to analyze
    MIN_TOTAL_CORRECTIONS = 50  # Minimum total corrections in system
    P_VALUE_THRESHOLD = 0.01  # Statistical significance level

    @property
    def name(self) -> str:
        return "STATISTICAL_PAIR"

    @property
    def threshold(self) -> float:
        # 1 - p_value threshold of 0.01 = 0.99
        return 0.99

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects statistically significant over-representation of correction pairs using binomial testing"

    def _build_correction_graph(self) -> Tuple[
        Dict[Tuple[int, int], int],  # edge_weights: (corrector_id, corrected_id) -> count
        Dict[int, int],  # corrector_totals: corrector_id -> total corrections given
        Dict[int, int],  # corrected_totals: corrected_id -> total corrections received
        int  # total_corrections
    ]:
        """
        Build a directed graph of all corrections in the system.

        Returns:
            Tuple of (edge_weights, corrector_totals, corrected_totals, total_corrections)
        """
        edge_weights: Dict[Tuple[int, int], int] = defaultdict(int)
        corrector_totals: Dict[int, int] = defaultdict(int)
        corrected_totals: Dict[int, int] = defaultdict(int)
        total_corrections = 0

        all_corrections = get_data(f"{YOSHI_URL}/corrections/")
        if not isinstance(all_corrections, list):
            return edge_weights, corrector_totals, corrected_totals, total_corrections

        for correction in all_corrections:
            corrector = correction.get("corrector")
            if not corrector or not corrector.get("id"):
                continue

            corrector_id = corrector["id"]
            correcteds = correction.get("push", {}).get("correcteds", [])

            for corrected in correcteds:
                corrected_id = corrected.get("id")
                if not corrected_id:
                    continue

                edge_weights[(corrector_id, corrected_id)] += 1
                corrector_totals[corrector_id] += 1
                corrected_totals[corrected_id] += 1
                total_corrections += 1

        return edge_weights, corrector_totals, corrected_totals, total_corrections

    def _calculate_expected(
        self,
        corrector_id: int,
        corrected_id: int,
        corrector_totals: Dict[int, int],
        corrected_totals: Dict[int, int],
        total_corrections: int
    ) -> float:
        """
        Calculate expected correction frequency using the formula:
        Expected(A→B) = (Total corrections by A × Total corrections received by B) / Total corrections
        """
        if total_corrections == 0:
            return 0.0

        corrections_by_a = corrector_totals.get(corrector_id, 0)
        corrections_to_b = corrected_totals.get(corrected_id, 0)

        return (corrections_by_a * corrections_to_b) / total_corrections

    def _binomial_test(
        self,
        observed: int,
        total_by_corrector: int,
        expected_probability: float
    ) -> float:
        """
        Perform a one-sided binomial test.

        H0: The probability of correcting this specific student equals expected_probability
        H1: The probability is greater than expected (over-representation)

        Returns:
            p-value for the one-sided test
        """
        if total_by_corrector == 0 or expected_probability <= 0:
            return 1.0

        expected_probability = min(expected_probability, 1.0)

        result = stats.binomtest(
            k=observed,
            n=total_by_corrector,
            p=expected_probability,
            alternative='greater'
        )

        return result.pvalue

    def calculate(self, correction_id: str) -> Optional[float]:
        # Fetch current correction
        correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
        if not correction:
            return None

        corrector = correction.get("corrector")
        if not corrector or not corrector.get("id"):
            return None

        corrector_id = corrector["id"]
        correcteds = correction.get("push", {}).get("correcteds", [])
        if not correcteds:
            return None

        # Build the full correction graph
        edge_weights, corrector_totals, corrected_totals, total_corrections = (
            self._build_correction_graph()
        )

        # Check minimum data requirements
        if total_corrections < self.MIN_TOTAL_CORRECTIONS:
            return None

        # Analyze each corrected student and take the most suspicious result
        min_p_value = 1.0
        most_suspicious_pair = None
        pair_details = []

        for corrected in correcteds:
            corrected_id = corrected.get("id")
            if not corrected_id:
                continue

            observed = edge_weights.get((corrector_id, corrected_id), 0)

            # Skip if insufficient observations
            if observed < self.MIN_OBSERVATIONS:
                continue

            # Calculate expected frequency
            expected = self._calculate_expected(
                corrector_id,
                corrected_id,
                corrector_totals,
                corrected_totals,
                total_corrections
            )

            if expected <= 0:
                continue

            # Calculate expected probability for binomial test
            total_by_corrector = corrector_totals.get(corrector_id, 0)
            if total_by_corrector == 0:
                continue

            expected_probability = corrected_totals.get(corrected_id, 0) / total_corrections

            # Perform binomial test
            p_value = self._binomial_test(observed, total_by_corrector, expected_probability)

            pair_details.append({
                'corrected_login': corrected.get('login', 'unknown'),
                'observed': observed,
                'expected': expected,
                'p_value': p_value,
            })

            if p_value < min_p_value:
                min_p_value = p_value
                most_suspicious_pair = {
                    'corrected_login': corrected.get('login', 'unknown'),
                    'observed': observed,
                    'expected': expected,
                    'p_value': p_value,
                }

        if most_suspicious_pair is None:
            return None

        corrector_login = corrector.get('login', 'unknown')
        details_parts = []

        for detail in pair_details:
            if detail['p_value'] < self.P_VALUE_THRESHOLD:
                details_parts.append(
                    f"{corrector_login} -> {detail['corrected_login']}: "
                    f"{detail['observed']}x (expected: {detail['expected']:.1f}, "
                    f"p={detail['p_value']:.4f})"
                )

        if details_parts:
            self.details = "; ".join(details_parts)

        if min_p_value > 0 and min_p_value < 1:
            log_score = -math.log10(min_p_value) / 5
            score = min(1.0, log_score)
        else:
            score = 1.0 - min_p_value

        return max(0.0, min(1.0, score))
