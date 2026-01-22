"""F1 calendar service."""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import httpx

from f1bot.config import settings
from f1bot.domain.models import Race
from f1bot.logging import get_logger

logger = get_logger(__name__)


def get_next_race(now: Optional[datetime] = None, tz: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get the next upcoming race."""
    if now is None:
        now = datetime.now(ZoneInfo(tz or settings.timezone))
    
    if not settings.f1_calendar_source:
        logger.debug("No F1 calendar source configured")
        return None
    
    try:
        races = _fetch_calendar()
        if not races:
            return None
        
        # Find next race
        for race in races:
            start_time = _parse_race_time(race)
            if start_time and start_time > now:
                return {
                    "race_id": race.get("id", race.get("raceId", "")),
                    "name": race.get("name", race.get("raceName", "")),
                    "start_time_utc": start_time,
                    "status": "upcoming",
                    "meta_json": {
                        "track": race.get("track", race.get("circuit", {}).get("name", "")),
                        "location": race.get("location", race.get("circuit", {}).get("location", "")),
                        "country": race.get("country", race.get("circuit", {}).get("country", "")),
                    }
                }
    except Exception as e:
        logger.error(f"Error fetching calendar: {e}")
    
    return None


def _fetch_calendar() -> list:
    """Fetch calendar from configured source."""
    if not settings.f1_calendar_source:
        return []
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(settings.f1_calendar_source)
            response.raise_for_status()
            
            # Try JSON first
            try:
                data = response.json()
                return _parse_json_calendar(data)
            except (json.JSONDecodeError, ValueError):
                # Try ICS format (basic parsing)
                return _parse_ics_calendar(response.text)
    except Exception as e:
        logger.error(f"Error fetching calendar from {settings.f1_calendar_source}: {e}")
        return []


def _parse_json_calendar(data: dict) -> list:
    """Parse JSON calendar format."""
    races = []
    
    # Try common JSON structures
    if isinstance(data, list):
        races = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ["races", "events", "calendar", "schedule", "data"]:
            if key in data and isinstance(data[key], list):
                races = data[key]
                break
        # If no list found, try root level
        if not races and "race" in data:
            races = [data["race"]] if isinstance(data["race"], dict) else data["race"]
    
    return races


def _parse_ics_calendar(ics_content: str) -> list:
    """Basic ICS calendar parsing."""
    races = []
    
    try:
        import re
        # Extract VEVENT blocks
        events = re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', ics_content, re.DOTALL)
        
        for event in events:
            race = {}
            # Extract DTSTART
            dtstart_match = re.search(r'DTSTART[^:]*:(.*)', event)
            if dtstart_match:
                race["start_time"] = dtstart_match.group(1).strip()
            # Extract SUMMARY
            summary_match = re.search(r'SUMMARY:(.*)', event)
            if summary_match:
                race["name"] = summary_match.group(1).strip()
            # Extract LOCATION
            location_match = re.search(r'LOCATION:(.*)', event)
            if location_match:
                race["location"] = location_match.group(1).strip()
            
            if race:
                races.append(race)
    except Exception as e:
        logger.error(f"Error parsing ICS calendar: {e}")
    
    return races


def _parse_race_time(race: dict) -> Optional[datetime]:
    """Parse race start time from race data."""
    # Try different time formats
    time_str = race.get("start_time", race.get("date", race.get("startDate", "")))
    if not time_str:
        return None
    
    try:
        # Try ISO format
        if "T" in time_str or "Z" in time_str:
            time_str = time_str.replace("Z", "+00:00")
            return datetime.fromisoformat(time_str)
        # Try other formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y %H:%M"]:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
    except Exception as e:
        logger.error(f"Error parsing race time {time_str}: {e}")
    
    return None


def is_race_weekend(now: Optional[datetime] = None) -> bool:
    """Check if current time is during a race weekend."""
    if now is None:
        now = datetime.now(ZoneInfo(settings.timezone))
    
    try:
        races = _fetch_calendar()
        for race in races:
            start_time = _parse_race_time(race)
            if start_time:
                # Check if within 3 days of race
                days_diff = (start_time - now).days
                if -1 <= days_diff <= 1:
                    return True
    except Exception as e:
        logger.error(f"Error checking race weekend: {e}")
    
    return False
