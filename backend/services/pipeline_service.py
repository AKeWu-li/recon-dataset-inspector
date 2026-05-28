from pathlib import Path
from datetime import datetime
import subprocess
import sys
import shutil
import locale
import os

from backend.database import SessionLocal
from backend.models import Job


def clean_stale_outputs(output_folder):
    stale_files = [
        "reconstruction_report.md",
        "training_data_readiness_report.md"
    ]

    stale_folders = [
        "colmap_workspace",
        "gaussian_splatting_scene"
    ]

    for filename in stale_files:
        path = output_folder / filename
        if path.exists():
            path.unlink()

    for foldername in stale_folders:
        path = output_folder / foldername
        if path.exists():
            shutil.rmtree(path)


def update_job_status(job_id, status, message):
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is None:
            return

        job.status = status
        job.message = message
        job.updated_at = datetime.now()

        db.commit()

    finally:
        db.close()


def run_pipeline_job(job_id, input_path, output_path, blur_threshold):
    project_root = Path(__file__).resolve().parents[2]

    output_folder = project_root / output_path
    output_folder.mkdir(parents=True, exist_ok=True)

    clean_stale_outputs(output_folder)

    log_path = output_folder / "backend_job.log"

    update_job_status(
        job_id=job_id,
        status="running",
        message="Job is running."
    )

    command = [
        sys.executable,
        "run_pipeline.py",
        "--input",
        input_path,
        "--output",
        output_path,
        "--blur-threshold",
        str(blur_threshold)
    ]

    try:
        result = run_subprocess_with_log(command, project_root)

        log_content = ""
        log_content += "COMMAND:\n"
        log_content += " ".join(command)
        log_content += "\n\nSTDOUT:\n"
        log_content += result.stdout
        log_content += "\n\nSTDERR:\n"
        log_content += result.stderr

        log_path.write_text(log_content, encoding="utf-8")

        if result.returncode == 0:
            update_job_status(
                job_id=job_id,
                status="success",
                message=f"Job finished successfully. Log saved to {log_path}"
            )
        else:
            update_job_status(
                job_id=job_id,
                status="failed",
                message=f"Job failed with return code {result.returncode}. Log saved to {log_path}"
            )

    except Exception as e:
        error_message = f"Job failed with exception: {e}"

        log_path.write_text(error_message, encoding="utf-8")

        update_job_status(
            job_id=job_id,
            status="failed",
            message=error_message
        )

def run_after_colmap_job(job_id, output_path):
    project_root = Path(__file__).resolve().parents[2]

    output_folder = project_root / output_path
    output_folder.mkdir(parents=True, exist_ok=True)

    log_path = output_folder / "backend_after_colmap.log"

    update_job_status(
        job_id=job_id,
        status="after_colmap_running",
        message="After-COLMAP post-processing is running."
    )

    command = [
        sys.executable,
        "run_pipeline.py",
        "--output",
        output_path,
        "--after-colmap"
    ]

    try:
        result = run_subprocess_with_log(command, project_root)

        log_content = ""
        log_content += "COMMAND:\n"
        log_content += " ".join(command)
        log_content += "\n\nSTDOUT:\n"
        log_content += result.stdout
        log_content += "\n\nSTDERR:\n"
        log_content += result.stderr

        log_path.write_text(log_content, encoding="utf-8")

        if result.returncode == 0:
            update_job_status(
                job_id=job_id,
                status="after_colmap_success",
                message=f"After-COLMAP post-processing finished successfully. Log saved to {log_path}"
            )
        else:
            update_job_status(
                job_id=job_id,
                status="after_colmap_failed",
                message=f"After-COLMAP post-processing failed with return code {result.returncode}. Log saved to {log_path}"
            )

    except Exception as e:
        error_message = f"After-COLMAP post-processing failed with exception: {e}"

        log_path.write_text(error_message, encoding="utf-8")

        update_job_status(
            job_id=job_id,
            status="after_colmap_failed",
            message=error_message
        )

def run_subprocess_with_log(command, cwd):
    """
    运行子进程并尽量正确处理 Windows 中文输出编码。
    """
    system_encoding = locale.getpreferredencoding(False)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

        # 如果 utf-8 解码后出现大量替换字符，尝试用系统编码重新跑一次
        if "�" in result.stdout or "�" in result.stderr:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding=system_encoding,
                errors="replace",
                env=os.environ.copy()
            )

        return result

    except UnicodeDecodeError:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding=system_encoding,
            errors="replace"
        )