"""Main entry point for the F1 Bot."""

import asyncio

from f1bot.bot.app import create_application
from f1bot.logging import setup_logging, get_logger
from f1bot.storage.db import init_db
from f1bot.jobs.scheduler import setup_scheduler, shutdown_scheduler

logger = get_logger(__name__)


def main() -> None:
    """Start the bot."""
    setup_logging()
    logger.info("Starting F1 Bot...")

    # Initialize database
    init_db()

    # Setup scheduler
    setup_scheduler()

    # Create application
    application = create_application()

    try:
        # Run polling (python-telegram-bot manages event loop)
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    finally:
        shutdown_scheduler()


if __name__ == "__main__":
    main()
