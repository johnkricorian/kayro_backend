from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.generate_opportunities import generate
from app.services.prediction_batch import generate_prediction_batch
from app.core.logger import create_logger

scheduler = BackgroundScheduler(timezone="UTC")

scheduler.add_job(
    generate,
    trigger="interval",
    minutes=15,
    id="opportunities_refresh",
    replace_existing=True,
    max_instances=1,
    coalesce=True
)

logger = create_logger(__name__)

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
    scheduler.add_job(
        run_daily_prediction_batch,
        trigger="cron",
        hour=22,
        minute=30,
        id="qeyro_daily_prediction_batch",
        replace_existing=True,
    )

    scheduler.start()

    logger.info(
        "⏰ Qeyro scheduler started"
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
