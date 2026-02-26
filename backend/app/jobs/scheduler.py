import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    from app.jobs.pull_google import pull_google_ads_all
    from app.jobs.pull_meta import pull_meta_ads_all
    from app.jobs.compute_comparison import compute_comparison_all

    scheduler.add_job(
        pull_google_ads_all,
        CronTrigger(hour=3, minute=0),
        id="pull_google",
        replace_existing=True,
    )
    scheduler.add_job(
        pull_meta_ads_all,
        CronTrigger(hour=3, minute=15),
        id="pull_meta",
        replace_existing=True,
    )
    scheduler.add_job(
        compute_comparison_all,
        CronTrigger(hour=4, minute=0),
        id="compute_comparison",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 3 daily jobs")
