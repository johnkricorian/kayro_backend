import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from app.services.prediction_batch import generate_prediction_batch
from app.core.logger import create_logger

logger = create_logger(__name__)

NEW_YORK_TZ = ZoneInfo("America/New_York")

scheduler = BackgroundScheduler(
    timezone=NEW_YORK_TZ
)

def run_daily_prediction_batch() -> None:
    logger.info(
        "🚀 Starting daily Qeyro prediction batch"
    )

    result = generate_prediction_batch(
        force_refresh=True
    )

    logger.info(
        "✅ Daily Qeyro batch completed: "
        "%s generated, %s errors",
        result["generated"],
        result["errors_count"],
    )


def start_scheduler() -> None:
    scheduler_enabled = (
        os.getenv(
            "QEYRO_SCHEDULER_ENABLED",
            "false",
        ).lower()
        == "true"
    )

    if not scheduler_enabled:
        logger.info(
            "⏸️ Qeyro scheduler disabled"
        )
        return

    scheduler.add_job(
        run_daily_prediction_batch,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=16,
            minute=30,
            timezone=NEW_YORK_TZ,
        ),
        id="qeyro_daily_prediction_batch",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900,
    )

    scheduler.start()

    logger.info(
        "⏰ Qeyro scheduler started "
        "(Mon-Fri 16:30 America/New_York)"
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(
            wait=False
        )
