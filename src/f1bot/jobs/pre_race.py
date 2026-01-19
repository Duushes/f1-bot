"""Pre-race content generation job."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from f1bot.logging import get_logger
from f1bot.config import settings
from f1bot.storage.repositories import RaceRepo, ContentRepo
from f1bot.services.calendar import get_next_race
from f1bot.services.news import fetch_news
from f1bot.services.llm import generate_pre_race
from f1bot.bot.app import create_application

logger = get_logger(__name__)


async def pre_race_job() -> None:
    """Generate pre-race content 2 hours before race start."""
    logger.info("Pre-race job triggered")
    
    # Get next race
    race_repo = RaceRepo()
    race = race_repo.get_next_race()
    
    if not race:
        logger.info("No upcoming race found")
        return
    
    race_id = race["race_id"]
    start_time = datetime.fromisoformat(race["start_time_utc"].replace("Z", "+00:00")) if isinstance(race["start_time_utc"], str) else race["start_time_utc"]
    now = datetime.now(ZoneInfo(settings.timezone))
    
    # Check if it's 2 hours before race (with 10 minute window)
    time_diff = (start_time - now).total_seconds() / 3600
    if not (1.8 <= time_diff <= 2.2):
        logger.info(f"Not yet time for pre-race generation. Time diff: {time_diff:.2f} hours")
        return
    
    # Check if content already exists
    content_repo = ContentRepo()
    ru_content = content_repo.fetch_by_race_type_lang(race_id, "pre_race", "ru")
    en_content = content_repo.fetch_by_race_type_lang(race_id, "pre_race", "en")
    
    if ru_content and ru_content["status"] != "draft":
        logger.info("Pre-race content already generated")
        return
    
    # Fetch news
    news = fetch_news(limit=10)
    
    # Generate content for both languages
    for lang in ["ru", "en"]:
        existing = content_repo.fetch_by_race_type_lang(race_id, "pre_race", lang)
        if existing and existing["status"] != "draft":
            continue
        
        text = generate_pre_race(race, news, lang)
        content_repo.save_draft(race_id, "pre_race", lang, text)
        content_repo.mark_pending(race_id, "pre_race", lang)
        
        logger.info(f"Generated pre-race content for {race_id} in {lang}")
    
    # Notify admins
    await notify_admins_pre_race(race_id)


async def notify_admins_pre_race(race_id: str) -> None:
    """Notify admins about pending pre-race content."""
    try:
        application = create_application()
        content_repo = ContentRepo()
        
        for lang in ["ru", "en"]:
            content = content_repo.fetch_by_race_type_lang(race_id, "pre_race", lang)
            if not content or content["status"] != "pending_admin":
                continue
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            text = f"📋 Pre-Race Content ({lang.upper()})\n\n{content['text']}"
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin:approve:pre_race:{race_id}:{lang}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"admin:cancel:pre_race:{race_id}:{lang}"),
                ]
            ])
            
            for admin_id in settings.admin_ids:
                try:
                    await application.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=keyboard,
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Error notifying admins: {e}")
