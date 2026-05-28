from backend.celery_app import celery_app
from backend.services.pipeline_service import run_pipeline_job, run_after_colmap_job


@celery_app.task(name="backend.tasks.run_pipeline_task")
def run_pipeline_task(job_id, input_path, output_path, blur_threshold):
    run_pipeline_job(
        job_id=job_id,
        input_path=input_path,
        output_path=output_path,
        blur_threshold=blur_threshold
    )

    return {
        "job_id": job_id,
        "task": "run_pipeline_task",
        "status": "finished"
    }


@celery_app.task(name="backend.tasks.run_after_colmap_task")
def run_after_colmap_task(job_id, output_path):
    run_after_colmap_job(
        job_id=job_id,
        output_path=output_path
    )

    return {
        "job_id": job_id,
        "task": "run_after_colmap_task",
        "status": "finished"
    }