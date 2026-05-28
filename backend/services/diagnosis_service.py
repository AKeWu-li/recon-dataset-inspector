from pathlib import Path
import csv
import re

from backend.models import Job
from backend.utils.path_utils import resolve_project_path


def read_text_if_exists(path: Path) -> str:
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def get_image_stats(image_infos_csv: Path):
    if not image_infos_csv.exists():
        return {
            "valid_image_count": 0,
            "blurry_image_count": 0,
            "blurry_ratio": 0.0,
            "has_image_infos": False
        }

    valid_count = 0
    blurry_count = 0

    with open(image_infos_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            valid_count += 1

            if row.get("is_blurry") == "True":
                blurry_count += 1

    blurry_ratio = blurry_count / valid_count if valid_count > 0 else 0.0

    return {
        "valid_image_count": valid_count,
        "blurry_image_count": blurry_count,
        "blurry_ratio": blurry_ratio,
        "has_image_infos": True
    }


def extract_reconstruction_quality(report_content: str):
    score = None
    quality = "unknown"
    registered_ratio = None

    score_match = re.search(r"综合评分：\s*(\d+)", report_content)
    if score_match:
        score = int(score_match.group(1))

    quality_match = re.search(r"重建质量：\s*([^\n\r]+)", report_content)
    if quality_match:
        quality = quality_match.group(1).strip()

    ratio_match = re.search(r"注册图片比例：\s*([\d.]+)%", report_content)
    if ratio_match:
        registered_ratio = float(ratio_match.group(1))

    return {
        "quality_score": score,
        "quality_level": quality,
        "registered_ratio": registered_ratio
    }


def diagnose_job(job: Job):
    output_path = resolve_project_path(job.output_path)

    image_infos_csv = output_path / "image_infos.csv"
    reconstruction_report = output_path / "reconstruction_report.md"
    readiness_report = output_path / "training_data_readiness_report.md"
    backend_log = output_path / "backend_job.log"
    after_colmap_log = output_path / "backend_after_colmap.log"

    run_colmap_bat = output_path / "run_colmap.bat"
    colmap_workspace = output_path / "colmap_workspace"
    sparse_ply = colmap_workspace / "sparse.ply"
    sparse_txt = colmap_workspace / "sparse_txt"

    image_stats = get_image_stats(image_infos_csv)

    reconstruction_content = read_text_if_exists(reconstruction_report)
    readiness_content = read_text_if_exists(readiness_report)
    backend_log_content = read_text_if_exists(backend_log)
    after_colmap_log_content = read_text_if_exists(after_colmap_log)

    reconstruction_quality = extract_reconstruction_quality(reconstruction_content)

    main_problems = []
    suggestions = []
    next_actions = []

    if job.status in ["failed", "after_colmap_failed"]:
        main_problems.append("任务执行失败。")
        suggestions.append("建议先查看 backend_job.log 或 backend_after_colmap.log，定位具体错误。")
        next_actions.append(f"GET /api/v1/jobs/{job.id}/log")

    if not image_infos_csv.exists():
        main_problems.append("未找到 image_infos.csv，说明图片检查阶段可能没有成功完成。")
        suggestions.append("建议重新创建任务，检查 input_path 是否正确。")

    if image_stats["valid_image_count"] == 0:
        main_problems.append("有效图片数量为 0。")
        suggestions.append("请检查输入目录是否存在图片，或图片格式是否能被 PIL 正常读取。")

    if image_stats["blurry_ratio"] > 0.3:
        main_problems.append("疑似模糊图片比例较高。")
        suggestions.append("建议检查 blurry_images 目录，必要时重新采集更清晰的数据。")

    if run_colmap_bat.exists() and not colmap_workspace.exists():
        main_problems.append("已生成 run_colmap.bat，但尚未发现 COLMAP 输出目录。")
        suggestions.append("请先运行该任务目录下的 run_colmap.bat。")
        next_actions.append(str(run_colmap_bat))

    if colmap_workspace.exists() and not reconstruction_report.exists():
        main_problems.append("已发现 COLMAP 工作目录，但尚未生成 reconstruction_report.md。")
        suggestions.append("请调用 after-colmap 接口生成重建报告。")
        next_actions.append(f"POST /api/v1/jobs/{job.id}/after-colmap")

    if reconstruction_report.exists():
        quality_level = reconstruction_quality["quality_level"]
        quality_score = reconstruction_quality["quality_score"]

        if quality_level in ["较差", "一般"]:
            main_problems.append(f"重建质量为：{quality_level}。")
            suggestions.append("建议检查注册图片比例、稀疏点数量、相机轨迹和模糊图片比例。")

        if quality_score is not None and quality_score < 60:
            main_problems.append("综合评分偏低。")
            suggestions.append("建议增加图片数量、提高相邻图片重叠率，并避免弱纹理场景。")

    if readiness_report.exists():
        if "NOT_READY" in readiness_content:
            main_problems.append("数据准备检查结果为 NOT_READY。")
            suggestions.append("请根据 training_data_readiness_report.md 中的风险提示补齐关键文件或重新运行 COLMAP。")
        elif "READY_WITH_WARNINGS" in readiness_content:
            main_problems.append("数据准备检查结果存在警告。")
            suggestions.append("可以继续后续实验，但建议先查看 readiness report 中的风险项。")

    if "No images with matches" in backend_log_content or "No images with matches" in after_colmap_log_content:
        main_problems.append("COLMAP 没有找到可匹配图片对。")
        suggestions.append("建议提高相邻图片重叠率，避免纯色/弱纹理场景，并降低 blur-threshold 后重新尝试。")

    if not main_problems:
        main_problems.append("未发现明显问题。")

    if not suggestions:
        suggestions.append("当前任务结果较完整，可以继续进行 3DGS scene 导出或后续训练准备。")

    if not next_actions:
        if reconstruction_report.exists():
            next_actions.append(f"GET /api/v1/jobs/{job.id}/report")
        elif run_colmap_bat.exists():
            next_actions.append(str(run_colmap_bat))

    if reconstruction_report.exists():
        quality = reconstruction_quality["quality_level"]
    elif job.status == "success":
        quality = "待运行 COLMAP"
    elif job.status == "after_colmap_success":
        quality = "已完成后处理"
    else:
        quality = "unknown"

    evidence = {
        "output_path": job.output_path,
        "image_infos_exists": image_infos_csv.exists(),
        "valid_image_count": image_stats["valid_image_count"],
        "blurry_image_count": image_stats["blurry_image_count"],
        "blurry_ratio": image_stats["blurry_ratio"],
        "run_colmap_bat_exists": run_colmap_bat.exists(),
        "colmap_workspace_exists": colmap_workspace.exists(),
        "sparse_ply_exists": sparse_ply.exists(),
        "sparse_txt_exists": sparse_txt.exists(),
        "reconstruction_report_exists": reconstruction_report.exists(),
        "readiness_report_exists": readiness_report.exists(),
        "quality_score": reconstruction_quality["quality_score"],
        "quality_level": reconstruction_quality["quality_level"],
        "registered_ratio": reconstruction_quality["registered_ratio"]
    }

    return {
        "job_id": job.id,
        "job_status": job.status,
        "quality": quality,
        "main_problems": main_problems,
        "suggestions": suggestions,
        "next_actions": next_actions,
        "evidence": evidence
    }