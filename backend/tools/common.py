from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Job


@contextmanager
def tool_db_session():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_job_or_error(
    db: Session,
    job_id: int
) -> Tuple[Optional[Job], Optional[Dict[str, Any]]]:
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        return None, {
            "error": "Job not found",
            "job_id": job_id
        }

    return job, None


def serialize_job(job: Job) -> Dict[str, Any]:
    return {
        "id": job.id,
        "input_path": job.input_path,
        "output_path": job.output_path,
        "blur_threshold": job.blur_threshold,
        "status": job.status,
        "message": job.message,
        "celery_task_id": job.celery_task_id,
        "created_at": str(job.created_at),
        "updated_at": str(job.updated_at)
    }