from celery import Celery

from app.core.config import settings
from app.core.logging import setup_logging
from app.workers.celery_beat_config import CELERY_BEAT_SCHEDULE


setup_logging()
celery_app = Celery(
    "moreach",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "celery"}}

# Use tier-based schedule from celery_beat_config
# Runs poll_reddit_scheduled every hour, which checks user tiers
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
