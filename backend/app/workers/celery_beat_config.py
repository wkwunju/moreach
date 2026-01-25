"""
Celery Beat Configuration for Periodic Tasks

To enable automated Reddit polling, add this to your celery_app.py:

from celery.schedules import crontab
from app.workers.celery_beat_config import CELERY_BEAT_SCHEDULE

app = Celery(...)
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
"""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Poll Reddit every 6 hours
    "poll-reddit-leads": {
        "task": "app.workers.tasks.poll_reddit_leads",
        "schedule": 3600 * 6,  # 6 hours in seconds
    },
    
    # Alternative: Use crontab for more control
    # Run at 00:00, 06:00, 12:00, 18:00 every day
    # "poll-reddit-leads": {
    #     "task": "app.workers.tasks.poll_reddit_leads",
    #     "schedule": crontab(hour="*/6", minute=0),
    # },
}

