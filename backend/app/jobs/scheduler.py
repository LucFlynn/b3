import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    from app.jobs.pull_google import pull_google_ads_all
    from app.jobs.pull_meta import pull_meta_ads_all
    from app.jobs.compute_comparison import compute_comparison_all

    # Pull ad data every 6 hours (3am, 9am, 3pm, 9pm UTC)
    scheduler.add_job(
        pull_google_ads_all,
        CronTrigger(hour="3,9,15,21", minute=0),
        id="pull_google",
        replace_existing=True,
    )
    scheduler.add_job(
        pull_meta_ads_all,
        CronTrigger(hour="3,9,15,21", minute=15),
        id="pull_meta",
        replace_existing=True,
    )
    # Compute comparisons 30 min after each pull cycle
    scheduler.add_job(
        compute_comparison_all,
        CronTrigger(hour="3,9,15,21", minute=45),
        id="compute_comparison",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — ad sync every 6h (3am/9am/3pm/9pm UTC)")
