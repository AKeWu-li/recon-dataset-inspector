from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path

from backend.database import get_db
from backend.models import Job
from backend.utils.path_utils import resolve_project_path, ensure_path_inside
from backend.services.pipeline_service import run_pipeline_job, run_after_colmap_job
from backend.schemas import (
    JobCreate,
    JobResponse,
    JobOutputsResponse,
    JobLogResponse,
    JobReportResponse
)
from backend.config import TASK_QUEUE_MODE
from backend.tasks import run_pipeline_task, run_after_colmap_task
from backend.security import get_current_user



router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=JobResponse)
def create_job(
    job_create: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if job_create.auto_run:
        if TASK_QUEUE_MODE == "celery":
            status = "queued"
            message = "Job queued, waiting for Celery worker."
        else:
            status = "pending"
            message = "Job created, waiting to run with BackgroundTasks."
    else:
        status, message = infer_job_status_from_output(job_create.output_path)

    job = Job(
        input_path=job_create.input_path,
        output_path=job_create.output_path,
        blur_threshold=job_create.blur_threshold,
        status=status,
        message=message,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    if job_create.auto_run:
        if TASK_QUEUE_MODE == "celery":
            try:
                async_result = run_pipeline_task.delay(
                    job.id,
                    job.input_path,
                    job.output_path,
                    job.blur_threshold
                )

                job.celery_task_id = async_result.id
                job.message = f"Job queued to Celery. task_id={async_result.id}"
                job.updated_at = datetime.now()

                db.commit()
                db.refresh(job)

            except Exception as e:
                job.status = "queue_failed"
                job.message = f"Failed to enqueue Celery task: {e}"
                job.updated_at = datetime.now()
                db.commit()
                db.refresh(job)

                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to enqueue Celery task: {e}"
                )
        else:
            background_tasks.add_task(
                run_pipeline_job,
                job.id,
                job.input_path,
                job.output_path,
                job.blur_threshold
            )

    return job


@router.get("/", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.id.desc()).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

@router.get("/{job_id}/outputs", response_model=JobOutputsResponse)
def get_job_outputs(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    output_path = Path(job.output_path)

    if not output_path.exists():
        return {
            "job_id": job.id,
            "output_path": job.output_path,
            "exists": False,
            "files": [],
            "folders": []
        }

    files = []
    folders = []

    for item in output_path.iterdir():
        if item.is_file():
            files.append(item.name)
        elif item.is_dir():
            folders.append(item.name)

    return {
        "job_id": job.id,
        "output_path": job.output_path,
        "exists": True,
        "files": files,
        "folders": folders
    }

@router.get("/{job_id}/log", response_model=JobLogResponse)
def get_job_log(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    output_path = Path(job.output_path)
    log_path = output_path / "backend_job.log"

    if not log_path.exists():
        return {
            "job_id": job.id,
            "log_path": str(log_path),
            "exists": False,
            "content": ""
        }

    content = log_path.read_text(encoding="utf-8", errors="ignore")

    return {
        "job_id": job.id,
        "log_path": str(log_path),
        "exists": True,
        "content": content
    }

@router.get("/{job_id}/report", response_model=JobReportResponse)
def get_job_report(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    output_path = Path(job.output_path)

    reconstruction_report_path = output_path / "reconstruction_report.md"
    readiness_report_path = output_path / "training_data_readiness_report.md"

    if reconstruction_report_path.exists():
        content = reconstruction_report_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        return {
            "job_id": job.id,
            "report_type": "reconstruction_report",
            "report_path": str(reconstruction_report_path),
            "exists": True,
            "content": content
        }

    if readiness_report_path.exists():
        content = readiness_report_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        return {
            "job_id": job.id,
            "report_type": "training_data_readiness_report",
            "report_path": str(readiness_report_path),
            "exists": True,
            "content": content
        }

    return {
        "job_id": job.id,
        "report_type": "none",
        "report_path": "",
        "exists": False,
        "content": ""
    }

@router.post("/{job_id}/after-colmap", response_model=JobResponse)
def run_after_colmap(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    output_path = Path(job.output_path)

    if not output_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Output path does not exist: {job.output_path}"
        )

    colmap_workspace = output_path / "colmap_workspace"
    sparse_folder = colmap_workspace / "sparse"

    if not colmap_workspace.exists() or not sparse_folder.exists():
        raise HTTPException(
            status_code=400,
            detail="COLMAP result not found. Please run run_colmap.bat before after-colmap post-processing."
        )

    if TASK_QUEUE_MODE == "celery":
        job.status = "after_colmap_queued"
        job.message = "After-COLMAP post-processing queued, waiting for Celery worker."
    else:
        job.status = "after_colmap_pending"
        job.message = "After-COLMAP post-processing task created, waiting to run with BackgroundTasks."

    job.updated_at = datetime.now()

    db.commit()
    db.refresh(job)

    if TASK_QUEUE_MODE == "celery":
        try:
            async_result = run_after_colmap_task.delay(
                job.id,
                job.output_path
            )

            job.celery_task_id = async_result.id
            job.message = f"After-COLMAP task queued to Celery. task_id={async_result.id}"
            job.updated_at = datetime.now()

            db.commit()
            db.refresh(job)

        except Exception as e:
            job.status = "after_colmap_queue_failed"
            job.message = f"Failed to enqueue After-COLMAP task: {e}"
            job.updated_at = datetime.now()
            db.commit()
            db.refresh(job)

            raise HTTPException(
                status_code=500,
                detail=f"Failed to enqueue After-COLMAP task: {e}"
            )
    else:
        background_tasks.add_task(
            run_after_colmap_job,
            job.id,
            job.output_path
        )

    return job

@router.get("/{job_id}/download/{file_path:path}")
def download_job_file(
    job_id: int,
    file_path: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    output_path = resolve_project_path(job.output_path)
    target_path = (output_path / file_path).resolve()

    ensure_path_inside(output_path, target_path)

    if not target_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    if not target_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="Target path is not a file"
        )

    return FileResponse(
        path=target_path,
        filename=target_path.name,
        media_type="application/octet-stream"
    )

def infer_job_status_from_output(output_path_str: str):
    output_path = resolve_project_path(output_path_str)

    reconstruction_report = output_path / "reconstruction_report.md"
    readiness_report = output_path / "training_data_readiness_report.md"
    colmap_workspace = output_path / "colmap_workspace"
    run_colmap_bat = output_path / "run_colmap.bat"

    if reconstruction_report.exists() or readiness_report.exists():
        return (
            "after_colmap_success",
            "Existing output directory registered. After-COLMAP reports were found."
        )

    if colmap_workspace.exists():
        return (
            "colmap_finished",
            "Existing output directory registered. COLMAP workspace was found, but reports were not found."
        )

    if run_colmap_bat.exists():
        return (
            "success",
            "Existing output directory registered. First-stage outputs were found."
        )

    if output_path.exists():
        return (
            "registered",
            "Existing output directory registered, but no known pipeline outputs were found."
        )

    return (
        "registered",
        "Job registered without running pipeline. Output directory does not exist yet."
    )