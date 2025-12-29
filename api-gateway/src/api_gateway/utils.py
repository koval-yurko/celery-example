from typing import Optional
from datetime import datetime

def parse_date_done(date_done) -> Optional[datetime]:
    """
    Parse date_done field which can be ISO string or numeric timestamp.

    Args:
        date_done: ISO format string, numeric timestamp, or None

    Returns:
        datetime object or None
    """
    if not date_done:
        return None

    if isinstance(date_done, (int, float)):
        return datetime.fromtimestamp(date_done)

    if isinstance(date_done, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_done.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try as numeric string
                return datetime.fromtimestamp(float(date_done))
            except ValueError:
                return None

    return None
