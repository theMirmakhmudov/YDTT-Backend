"""Tasks module initialization."""
from app.tasks.celery_tasks import celery_app

__all__ = ["celery_app"]
