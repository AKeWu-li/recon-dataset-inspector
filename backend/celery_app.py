from celery import Celery

from backend.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery_app = Celery(
    "recon_dataset_inspector",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)