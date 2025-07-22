from celery import Celery
import os

# Load environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery instance
celery_app = Celery(
    "doc_analyser",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.worker.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours
    task_soft_time_limit=6900,  # 1 hour 55 min buffer
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    worker_concurrency=2,
    task_acks_late=True,
    worker_lost_wait=60,
)

# Configure task routing
celery_app.conf.task_routes = {
    "analyze_repository": {"queue": "analysis"},
    "execute_use_case": {"queue": "execution"},
}