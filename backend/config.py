import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TASK_QUEUE_MODE = os.getenv("TASK_QUEUE_MODE", "background")

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)

CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1"
)