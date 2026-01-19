"""Language selection handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from f1bot.logging import get_logger
from f1bot.storage.repositories import UserRepo
from f1bot.bot.handlers.menu import show_main_menu

logger = get_logger(__name__)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    lang = query.data.split(":")[1]  # lang:ru or lang:en

    # Save language
    user_repo = UserRepo()
    user_repo.create_or_update(user_id, lang=lang)

    logger.info(f"User {user_id} selected language: {lang}")

    # Show menu
    await show_main_menu(update, context)


def register_language_handlers(application) -> None:
    """Register language handlers."""
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang:"))
