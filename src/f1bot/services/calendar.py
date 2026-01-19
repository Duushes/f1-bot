"""F1 calendar service."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from f1bot.config import settings
from f1bot.domain.models import Race


def get_next_race(now: Optional[datetime] = None, tz: Optional[str] = None) -> Optional[Race]:
    """Get the next upcoming race."""
    if now is None:
        now = datetime.now(ZoneInfo(tz or settings.timezone))
    
    # TODO: Implement calendar fetching
    # For MVP, return None or mock data
    return None


def is_race_weekend(now: Optional[datetime] = None) -> bool:
    """Check if current time is during a race weekend."""
    # TODO: Implement
    return False
