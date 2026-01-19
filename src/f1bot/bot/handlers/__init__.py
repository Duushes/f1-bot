"""Handlers registration."""

from telegram.ext import Application

from f1bot.bot.handlers.start import register_start_handler
from f1bot.bot.handlers.language import register_language_handlers
from f1bot.bot.handlers.menu import register_menu_handlers
from f1bot.bot.handlers.bingo import register_bingo_handlers
from f1bot.bot.handlers.admin import register_admin_handlers


def register_handlers(application: Application) -> None:
    """Register all handlers."""
    register_start_handler(application)
    register_language_handlers(application)
    register_menu_handlers(application)
    register_bingo_handlers(application)
    register_admin_handlers(application)
