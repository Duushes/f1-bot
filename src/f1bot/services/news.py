"""F1 news service."""

import json
from typing import List, Dict
from datetime import datetime
import httpx

from f1bot.config import settings
from f1bot.logging import get_logger

logger = get_logger(__name__)


def fetch_news(limit: int = 10) -> List[Dict[str, str]]:
    """Fetch F1 news from sources."""
    if not settings.news_sources:
        logger.debug("No news sources configured")
        return []
    
    sources = [s.strip() for s in settings.news_sources.split(",") if s.strip()]
    if not sources:
        return []
    
    all_news = []
    
    for source_url in sources[:5]:  # Limit to 5 sources
        try:
            news_items = _fetch_from_source(source_url, limit)
            all_news.extend(news_items)
        except Exception as e:
            logger.error(f"Error fetching news from {source_url}: {e}")
            continue
    
    # Sort by published_at if available, limit results
    all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return all_news[:limit]


def _fetch_from_source(url: str, limit: int) -> List[Dict[str, str]]:
    """Fetch news from a single source."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
            # Try to parse as JSON first
            try:
                data = response.json()
                return _parse_json_news(data, limit)
            except (json.JSONDecodeError, ValueError):
                # Try to parse as RSS/XML (basic parsing)
                return _parse_rss_news(response.text, limit)
    except Exception as e:
        logger.error(f"Error fetching from {url}: {e}")
        return []


def _parse_json_news(data: dict, limit: int) -> List[Dict[str, str]]:
    """Parse JSON news format."""
    news_items = []
    
    # Try common JSON structures
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ["items", "articles", "news", "results", "data"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
    
    for item in items[:limit]:
        if isinstance(item, dict):
            news_items.append({
                "title": item.get("title", item.get("headline", "")),
                "source": item.get("source", item.get("site", "")),
                "published_at": item.get("published_at", item.get("date", item.get("time", ""))),
                "url": item.get("url", item.get("link", "")),
            })
    
    return news_items


def _parse_rss_news(xml_content: str, limit: int) -> List[Dict[str, str]]:
    """Basic RSS/XML parsing."""
    news_items = []
    
    # Very basic RSS parsing (for MVP)
    # In production, use feedparser library
    try:
        import re
        # Extract title tags
        titles = re.findall(r'<title>(.*?)</title>', xml_content, re.DOTALL)
        links = re.findall(r'<link>(.*?)</link>', xml_content, re.DOTALL)
        
        for i, title in enumerate(titles[:limit]):
            if i < len(links):
                news_items.append({
                    "title": re.sub(r'<[^>]+>', '', title).strip(),
                    "source": "RSS Feed",
                    "published_at": "",
                    "url": links[i].strip(),
                })
    except Exception as e:
        logger.error(f"Error parsing RSS: {e}")
    
    return news_items
