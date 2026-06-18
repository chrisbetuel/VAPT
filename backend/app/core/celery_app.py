from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "vapt",
    broker=settings.CELERY_BROKER_URL or settings.redis_url.replace(f"/{settings.REDIS_DB}", "/1"),
    backend=settings.CELERY_RESULT_BACKEND or settings.redis_url.replace(f"/{settings.REDIS_DB}", "/2"),
    include=[
        "app.tasks.scan_tasks",
        "app.tasks.report_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_track_started=True,
    task_publish_retry=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "cleanup-old-scans": {
            "task": "app.tasks.scan_tasks.cleanup_old_scans",
            "schedule": 86400.0,
        },
        "send-scheduled-reports": {
            "task": "app.tasks.report_tasks.send_scheduled_reports",
            "schedule": 3600.0,
        },
    },
)
