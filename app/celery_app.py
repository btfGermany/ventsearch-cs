"""
Celery Application Configuration

Celery worker configuration for background tasks.
"""

from celery import Celery
from celery.schedules import crontab


# Create Celery app
celery_app = Celery('company_intel')

# Configure from environment or defaults
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Import tasks to register them
from app.tasks import ingestion_tasks  # noqa
from app.tasks import indexing_tasks  # noqa