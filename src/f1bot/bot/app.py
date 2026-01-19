"""Application setup for python-telegram-bot."""

from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from f1bot.config import settings
from f1bot.logging import get_logger
from f1bot.bot.handlers import register_handlers

logger = get_logger(__name__)


async def error_handler(update: object, context: Exception) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context}", exc_info=context)

    # Send user-friendly message if update is available
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception:
            pass


def create_application() -> Application:
    """Create and configure the Telegram application."""
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Register handlers
    register_handlers(application)

    # Register error handler
    application.add_error_handler(error_handler)

    logger.info("Application created successfully")
    return application
