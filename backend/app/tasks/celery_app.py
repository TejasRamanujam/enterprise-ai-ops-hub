from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_ops_hub",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.agent_tasks",
        "app.tasks.sync_tasks",
        "app.tasks.scheduled_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    result_expires=3600,
    beat_schedule={
        "sync-all-integrations": {
            "task": "app.tasks.scheduled_tasks.sync_all_integrations",
            "schedule": 3600.0,
        },
        "generate-daily-health-reports": {
            "task": "app.tasks.scheduled_tasks.generate_daily_health_reports",
            "schedule": 86400.0,
        },
        "cleanup-expired-approvals": {
            "task": "app.tasks.scheduled_tasks.cleanup_expired_approvals",
            "schedule": 3600.0,
        },
    },
)
