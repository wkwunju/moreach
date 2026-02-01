"""
Celery Beat Configuration for Periodic Tasks

To enable automated Reddit polling, add this to your celery_app.py:

from celery.schedules import crontab
from app.workers.celery_beat_config import CELERY_BEAT_SCHEDULE

app = Celery(...)
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

Polling Schedule (based on subscription tier):
- Starter plans: 2x/day at UTC 07:00 (Europe 8am CET) and 16:00 (US West 8am PST)
- Growth/Pro plans: 4x/day at UTC 07:00, 11:00, 16:00, 22:00

The task runs every hour and checks which users should be polled at that hour.
"""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Run the tier-based scheduled polling every hour
    # The task will check which users should be polled based on their tier
    "poll-reddit-scheduled": {
        "task": "app.workers.tasks.poll_reddit_scheduled",
        "schedule": crontab(minute=0),  # Every hour at :00
    },

    # Legacy: Poll all active (kept for backward compatibility, disabled by default)
    # "poll-reddit-leads": {
    #     "task": "app.workers.tasks.poll_reddit_leads",
    #     "schedule": 3600 * 6,  # 6 hours in seconds
    # },
}

