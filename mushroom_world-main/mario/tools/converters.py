from typing import Optional
from datetime import datetime


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse ISO format timestamp string to datetime.

    Args:
        timestamp_str: ISO format timestamp (e.g., "2024-01-25T14:30:00Z")

    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None

    try:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None