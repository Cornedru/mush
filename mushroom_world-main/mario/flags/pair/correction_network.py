from mario_types.IFlag import IFlag
from typing import Optional, Set
from tools.handle_requests import get_data
from tools.conf import YOSHI_URL


class CorrectionNetworkFlag(IFlag):
    """
    Detects if corrector shares a correction community with the corrected student(s)
    using Jaccard Similarity between their correction networks.

    Algorithm:
    1. Build corrector's network (students they've corrected + who corrected them)
    2. Build corrected students' combined network
    3. Calculate Jaccard similarity: |A ∩ B| / |A ∪ B|
    4. High similarity indicates they're part of the same correction community

    Returns:
        Float in [0, 1]: Jaccard similarity score
        None: If networks are too small for meaningful comparison
        0: If no shared correction partners
    """

    MIN_NETWORK_SIZE = 3

    @property
    def name(self) -> str:
        return "CORRECTION_NETWORK"

    @property
    def threshold(self) -> float:
        return 0.25

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects if corrector and corrected share a significant correction community"

    def _get_correction_network(self, user_id: int) -> Set[int]:
        """Build the correction network for a user (people they've corrected + who corrected them)."""
        network: Set[int] = set()

        # People who corrected this user
        as_corrected = get_data(f"{YOSHI_URL}/corrections/by_corrected/{user_id}")
        if isinstance(as_corrected, list):
            for corr in as_corrected:
                corrector = corr.get("corrector")
                if corrector and corrector.get("id"):
                    network.add(corrector["id"])

        # People this user has corrected
        as_corrector = get_data(f"{YOSHI_URL}/corrections/by_corrector/{user_id}")
        if isinstance(as_corrector, list):
            for corr in as_corrector:
                push = corr.get("push")
                if push:
                    for student in push.get("correcteds", []):
                        if student and student.get("id"):
                            network.add(student["id"])

        return network

    def calculate(self, correction_id: str) -> Optional[float]:
        correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
        if not correction:
            return None

        corrector = correction.get("corrector")
        if not corrector or not corrector.get("id"):
            return None

        corrector_id = corrector["id"]
        push = correction.get("push")
        correcteds = push.get("correcteds", []) if push else []
        if not correcteds:
            return None

        # Build corrector's network (excluding current correcteds)
        corrector_network = self._get_correction_network(corrector_id)
        corrector_network.discard(corrector_id)  # Remove self
        for c in correcteds:
            corrector_network.discard(c.get("id"))  # Exclude current correcteds

        # Build combined network of all corrected students
        corrected_network: Set[int] = set()
        for corrected in correcteds:
            if corrected.get("id"):
                network = self._get_correction_network(corrected["id"])
                network.discard(corrected["id"])  # Remove self
                network.discard(corrector_id)  # Exclude current corrector
                corrected_network.update(network)

        # Check minimum network sizes
        if len(corrector_network) < self.MIN_NETWORK_SIZE or len(corrected_network) < self.MIN_NETWORK_SIZE:
            return None

        # Calculate Jaccard similarity
        intersection = corrector_network & corrected_network
        union = corrector_network | corrected_network

        if len(union) == 0:
            return 0.0

        jaccard = len(intersection) / len(union)

        if len(intersection) > 0:
            self.details = f"Shared {len(intersection)} correction partners out of {len(union)} total"

        return jaccard
