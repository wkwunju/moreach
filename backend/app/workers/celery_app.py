from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.core.logging import setup_logging


setup_logging()
celery_app = Celery(
    "moreach",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "celery"}}

# Configure Celery Beat for periodic tasks
celery_app.conf.beat_schedule = {
    # Reddit Lead Generation: Poll every 6 hours
    "poll-reddit-leads": {
        "task": "app.workers.tasks.poll_reddit_leads",
        "schedule": 3600 * 6,  # 6 hours in seconds
    },
    # Alternative: Use crontab for specific times
    # "poll-reddit-leads": {
    #     "task": "app.workers.tasks.poll_reddit_leads",
    #     "schedule": crontab(hour="*/6", minute=0),  # Every 6 hours on the hour
    # },
}
