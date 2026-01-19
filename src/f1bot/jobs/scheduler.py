"""Job scheduler."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from f1bot.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    """Setup and start scheduler."""
    from f1bot.jobs.pre_race import pre_race_job
    from f1bot.jobs.post_race import post_race_job
    
    # Check for pre-race content every 10 minutes
    scheduler.add_job(
        pre_race_job,
        IntervalTrigger(minutes=10),
        id="pre_race_check",
        replace_existing=True,
    )
    
    # Check for post-race content every 30 minutes
    scheduler.add_job(
        post_race_job,
        IntervalTrigger(minutes=30),
        id="post_race_check",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler shut down")
