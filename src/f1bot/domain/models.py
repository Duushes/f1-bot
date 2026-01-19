"""Domain models."""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """User model."""

    telegram_id: int
    lang: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Race:
    """Race model."""

    race_id: str
    name: str
    start_time_utc: datetime
    status: str  # upcoming, in_progress, finished
    meta_json: Optional[Dict[str, Any]] = None


@dataclass
class Content:
    """Content model (pre-race, post-race)."""

    race_id: str
    content_type: str  # pre_race, post_race
    lang: str
    status: str  # draft, pending_admin, approved, published
    text: str
    created_at: datetime
    updated_at: datetime


@dataclass
class BingoCard:
    """Bingo card template."""

    race_id: str
    lang: str
    cells_json: Dict[str, Any]  # 16 cells
    created_at: datetime


@dataclass
class BingoUserState:
    """User's bingo state for a race."""

    race_id: str
    telegram_id: int
    states_json: Dict[str, str]  # cell_id -> status (empty, checked, verified)
    created_at: datetime
    updated_at: datetime
