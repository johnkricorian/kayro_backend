from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.generate_opportunities import generate

scheduler = BackgroundScheduler(
    timezone="UTC"
)

scheduler.add_job(
    generate,
    trigger="interval",
    minutes=15,
    id="opportunities_refresh",
    replace_existing=True,
    max_instances=1,
    coalesce=True
)
