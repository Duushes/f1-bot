"""Main menu handlers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from f1bot.logging import get_logger
from f1bot.storage.repositories import UserRepo
from f1bot.services.i18n import t

logger = get_logger(__name__)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu."""
    user_id = update.effective_user.id
    user_repo = UserRepo()
    user = user_repo.get(user_id)
    lang = user.get("lang", "ru") if user else "ru"

    text = t("menu.welcome", lang)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("menu.pre_race", lang), callback_data="menu:pre_race")],
        [InlineKeyboardButton(t("menu.bingo", lang), callback_data="menu:bingo")],
        [InlineKeyboardButton(t("menu.post_race", lang), callback_data="menu:post_race")],
        [InlineKeyboardButton(t("menu.language", lang), callback_data="menu:language")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu callbacks."""
    query = update.callback_query
    await query.answer()

    action = query.data.split(":")[1]  # menu:pre_race, etc.

    if action == "language":
        # Show language selection
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            ]
        ])
        await query.edit_message_text(
            "Выберите язык / Choose language:",
            reply_markup=keyboard,
        )
    elif action == "pre_race":
        # Show pre-race content
        try:
            from f1bot.storage.repositories import RaceRepo, ContentRepo
            from f1bot.services.calendar import get_next_race as get_calendar_race
            
            user_repo = UserRepo()
            user = user_repo.get(update.effective_user.id)
            lang = user.get("lang", "ru") if user else "ru"
            
            race_repo = RaceRepo()
            race = race_repo.get_next_race()
            
            # If not in database, try to fetch from calendar source
            if not race:
                logger.info("No race in database, trying to fetch from calendar")
                try:
                    calendar_race = get_calendar_race()
                    if calendar_race:
                        # Save to database
                        race_repo.upsert(
                            race_id=calendar_race["race_id"],
                            name=calendar_race["name"],
                            start_time_utc=calendar_race["start_time_utc"],
                            status=calendar_race["status"],
                            meta_json=calendar_race.get("meta_json"),
                        )
                        race = calendar_race
                        logger.info(f"Fetched race from calendar: {race['name']}")
                except Exception as e:
                    logger.error(f"Error fetching from calendar: {e}")
            
            if not race:
                logger.info("No upcoming race found")
                text = t("menu.pre_race_coming_soon", lang)
                if lang == "ru":
                    text += "\n\n💡 Совет: Убедитесь, что F1_CALENDAR_SOURCE настроен в переменных окружения."
                else:
                    text += "\n\n💡 Tip: Make sure F1_CALENDAR_SOURCE is configured in environment variables."
                await query.edit_message_text(text)
                return
            
            content_repo = ContentRepo()
            content = content_repo.fetch_by_race_type_lang(race["race_id"], "pre_race", lang)
            
            if content and content["status"] == "published":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Открыть Bingo Cards" if lang == "ru" else "🎯 Open Bingo Cards", callback_data="menu:bingo")],
                    [InlineKeyboardButton(t("menu.back", lang), callback_data="menu:main")],
                ])
                await query.edit_message_text(content["text"], reply_markup=keyboard)
            else:
                # Show race info even if content is not ready
                race_name = race.get("name", "Unknown Race")
                meta = race.get("meta_json", {})
                track = meta.get("track", "") if isinstance(meta, dict) else ""
                
                if lang == "ru":
                    text = f"🏎️ Гонка: {race_name}\n"
                    if track:
                        text += f"📍 Трасса: {track}\n"
                    text += "\n📋 Превью гонки будет доступно за 2 часа до старта."
                else:
                    text = f"🏎️ Race: {race_name}\n"
                    if track:
                        text += f"📍 Track: {track}\n"
                    text += "\n📋 Race preview will be available 2 hours before start."
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(t("menu.back", lang), callback_data="menu:main")],
                ])
                await query.edit_message_text(text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error showing pre-race content: {e}", exc_info=True)
            user_repo = UserRepo()
            user = user_repo.get(update.effective_user.id)
            lang = user.get("lang", "ru") if user else "ru"
            await query.edit_message_text(t("menu.pre_race_coming_soon", lang))
    elif action == "bingo":
        # Show bingo cards
        from f1bot.bot.handlers.bingo import show_bingo_card
        await show_bingo_card(update, context)
    elif action == "post_race":
        # Show post-race content
        try:
            from f1bot.storage.repositories import RaceRepo, ContentRepo
            user_repo = UserRepo()
            user = user_repo.get(update.effective_user.id)
            lang = user.get("lang", "ru") if user else "ru"
            
            race_repo = RaceRepo()
            race = race_repo.get_last_race()
            
            if not race:
                await query.edit_message_text(t("menu.post_race_coming_soon", lang))
                return
            
            content_repo = ContentRepo()
            content = content_repo.fetch_by_race_type_lang(race["race_id"], "post_race", lang)
            
            if content and content["status"] == "published":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Следующая гонка" if lang == "ru" else "📋 Next Race", callback_data="menu:pre_race")],
                    [InlineKeyboardButton(t("menu.back", lang), callback_data="menu:main")],
                ])
                await query.edit_message_text(content["text"], reply_markup=keyboard)
            else:
                await query.edit_message_text(t("menu.post_race_coming_soon", lang))
        except Exception as e:
            logger.error(f"Error showing post-race content: {e}", exc_info=True)
            user_repo = UserRepo()
            user = user_repo.get(update.effective_user.id)
            lang = user.get("lang", "ru") if user else "ru"
            await query.edit_message_text(t("menu.post_race_coming_soon", lang))
    elif action == "main":
        await show_main_menu(update, context)
    else:
        await show_main_menu(update, context)


def register_menu_handlers(application) -> None:
    """Register menu handlers."""
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
