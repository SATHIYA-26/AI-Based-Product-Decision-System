from celery import Celery
from typing import Any

from review_clustering.services.pipeline_service import PipelineService

# basic Celery app; the broker URL should be configured via environment
celery_app = Celery(
    "backend_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# you can configure additional settings here or in a separate config file


@celery_app.task(bind=True)
def process_reviews(self, raw_items: Any) -> dict:
    """Wrapper around PipelineService.run_pipeline so it can be executed
    as a background job. ``raw_items`` has the same shape expected by the
    pipeline (list of strings or dicts with text/timestamp).
    """
    # in a real app you'd probably validate/transform the input and handle
    # exceptions more gracefully, maybe using retries.
    return PipelineService.run_pipeline(raw_items)
