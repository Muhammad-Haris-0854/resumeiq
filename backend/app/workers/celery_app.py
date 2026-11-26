"""Celery application.

Two queues keep slow AI work away from uploads; Premium traffic gets its own priority queue.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "resumeiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    task_routes={
        "resumeiq.extract_resume": {"queue": "default"},
        "resumeiq.export_resume": {"queue": "default"},
        "resumeiq.analyse_resume": {"queue": "ai"},
        "resumeiq.match_job": {"queue": "ai"},
    },
    task_annotations={
        "resumeiq.analyse_resume": {"time_limit": 180, "soft_time_limit": 160},
        "resumeiq.extract_resume": {"time_limit": 120, "soft_time_limit": 110},
        "resumeiq.export_resume": {"time_limit": 90, "soft_time_limit": 80},
    },
    broker_connection_retry_on_startup=True,
)

if settings.celery_eager:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
