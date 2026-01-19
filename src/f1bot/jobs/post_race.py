"""Post-race content generation job."""

from datetime import datetime
from zoneinfo import ZoneInfo

from f1bot.logging import get_logger
from f1bot.config import settings
from f1bot.storage.repositories import RaceRepo, ContentRepo
from f1bot.services.news import fetch_news
from f1bot.services.llm import generate_post_race
from f1bot.bot.app import create_application

logger = get_logger(__name__)


async def post_race_job() -> None:
    """Generate post-race content after race finish."""
    logger.info("Post-race job triggered")
    
    # Get last finished race
    race_repo = RaceRepo()
    race = race_repo.get_last_race()
    
    if not race:
        logger.info("No finished race found")
        return
    
    race_id = race["race_id"]
    
    # Check if content already exists
    content_repo = ContentRepo()
    ru_content = content_repo.fetch_by_race_type_lang(race_id, "post_race", "ru")
    en_content = content_repo.fetch_by_race_type_lang(race_id, "post_race", "en")
    
    if ru_content and ru_content["status"] != "draft":
        logger.info("Post-race content already generated")
        return
    
    # Fetch news
    news = fetch_news(limit=10)
    
    # Generate content for both languages
    for lang in ["ru", "en"]:
        existing = content_repo.fetch_by_race_type_lang(race_id, "post_race", lang)
        if existing and existing["status"] != "draft":
            continue
        
        text = generate_post_race(race, news, lang)
        content_repo.save_draft(race_id, "post_race", lang, text)
        content_repo.mark_pending(race_id, "post_race", lang)
        
        logger.info(f"Generated post-race content for {race_id} in {lang}")
    
    # Notify admins
    await notify_admins_post_race(race_id)


async def notify_admins_post_race(race_id: str) -> None:
    """Notify admins about pending post-race content."""
    try:
        application = create_application()
        content_repo = ContentRepo()
        
        for lang in ["ru", "en"]:
            content = content_repo.fetch_by_race_type_lang(race_id, "post_race", lang)
            if not content or content["status"] != "pending_admin":
                continue
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            text = f"🏁 Post-Race Content ({lang.upper()})\n\n{content['text']}"
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin:approve:post_race:{race_id}:{lang}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"admin:cancel:post_race:{race_id}:{lang}"),
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
