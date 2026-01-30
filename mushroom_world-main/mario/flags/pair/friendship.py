from mario_types.IFlag import IFlag
from typing import Optional
from tools.handle_requests import get_data
from tools.conf import YOSHI_URL


class FriendshipFlag(IFlag):
    """
    Detects corrections between project teammates.

    This flag identifies cases where a corrector evaluates students they have
    previously worked with on group projects, which may indicate bias.

    Algorithm:
    1. Find all group projects the corrector participated in
    2. Count how many shared group projects exist with each corrected student
    3. Normalize by total group projects corrector participated in
    4. Return highest friendship ratio among corrected students

    Returns:
        Float in [0, 1]: Ratio of shared projects to total group projects
        None: If no significant friendship detected or no group projects
    """

    @property
    def name(self) -> str:
        return "FRIENDSHIP"

    @property
    def threshold(self) -> float:
        return 0.3

    @property
    def sufficient(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Detects corrections between project teammates"

    def calculate(self, correction_id: str) -> Optional[float]:
        # Fetch current correction
        correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
        if not correction:
            return None

        corrector = correction.get("corrector", {}).get("login")
        if not corrector:
            return None

        correcteds = [c["login"] for c in correction.get("push", {}).get("correcteds", [])]

        # Fetch all pushes
        all_pushes = get_data(f"{YOSHI_URL}/pushes")
        if not isinstance(all_pushes, list):
            return None

        counts = {}
        corrector_group_projects = []

        for push in all_pushes:
            push_correcteds = [c["login"] for c in push.get("correcteds", [])]
            project_id = push.get("project", {}).get("id")

            if corrector not in push_correcteds or not project_id:
                continue

            if len(push_correcteds) > 1:
                if project_id not in corrector_group_projects:
                    corrector_group_projects.append(project_id)
                for corrected in push_correcteds:
                    if corrected in correcteds:
                        if corrected not in counts:
                            counts[corrected] = []
                        if project_id not in counts[corrected]:
                            counts[corrected].append(project_id)

        worse_friendship = max([0] + [len(counts[key]) for key in counts])
        min_group_correction = 2

        if worse_friendship >= min_group_correction and len(corrector_group_projects) > 0:
            return worse_friendship / len(corrector_group_projects)
        return None
