"""Start command handler."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from f1bot.logging import get_logger
from f1bot.storage.repositories import UserRepo

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")

    # Check if user exists and has language set
    user_repo = UserRepo()
    user = user_repo.get(user_id)

    if user and user.get("lang"):
        # User already has language, show menu
        from f1bot.bot.handlers.menu import show_main_menu
        await show_main_menu(update, context)
    else:
        # Show language selection
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            ]
        ])
        await update.message.reply_text(
            "Выберите язык / Choose language:",
            reply_markup=keyboard,
        )


def register_start_handler(application) -> None:
    """Register start handler."""
    application.add_handler(CommandHandler("start", start_command))
