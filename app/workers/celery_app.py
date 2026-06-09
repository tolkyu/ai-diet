from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_diet",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.notifications",
        "app.workers.tasks.analytics",
        "app.workers.tasks.cleanup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
)

celery_app.conf.beat_schedule = {
    "daily-morning-coaching": {
        "task": "app.workers.tasks.notifications.send_morning_coaching",
        "schedule": 3600.0 * 24,  # Daily — actual hour handled in task
        "options": {"expires": 3600},
    },
    "evening-progress-check": {
        "task": "app.workers.tasks.notifications.send_evening_check",
        "schedule": 3600.0 * 24,
        "options": {"expires": 3600},
    },
    "weekly-analytics": {
        "task": "app.workers.tasks.analytics.generate_weekly_reports",
        "schedule": 3600.0 * 24 * 7,
        "options": {"expires": 3600 * 6},
    },
    "daily-cleanup": {
        "task": "app.workers.tasks.cleanup.cleanup_old_data",
        "schedule": 3600.0 * 24,
    },
}
