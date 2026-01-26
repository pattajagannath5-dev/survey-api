"""Celery application configuration for async task processing."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "survey_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Rate limiting
    task_default_rate_limit="100/m",
    # Result expiration
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.send_survey_notification": {"queue": "notifications"},
    "app.tasks.process_survey_analytics": {"queue": "analytics"},
    "app.tasks.export_survey_results": {"queue": "exports"},
}
