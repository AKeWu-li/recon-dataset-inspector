from pathlib import Path
import argparse
import csv


def parse_args():
    parser = argparse.ArgumentParser(description="检查三维重建 / 3DGS 数据准备状态")

    parser.add_argument(
        "--output",
        default="output",
        help="项目输出目录"
    )

    return parser.parse_args()


def count_files(folder):
    if not folder.exists() or not folder.is_dir():
        return 0

    return len([file for file in folder.iterdir() if file.is_file()])


def count_csv_rows(csv_path):
    if not csv_path.exists():
        return 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


def is_int_string(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def count_registered_images(images_txt_path):
    if not images_txt_path.exists():
        return 0

    count = 0

    with open(images_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            # COLMAP images.txt 中图片位姿行格式通常是：
            # IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME
            # POINTS2D 行第一个通常是浮点数，不会是整数 IMAGE_ID
            if len(parts) >= 10 and is_int_string(parts[0]) and is_int_string(parts[8]):
                count += 1

    return count


def count_points3d(points3d_txt_path):
    if not points3d_txt_path.exists():
        return 0

    count = 0

    with open(points3d_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if line and not line.startswith("#"):
                count += 1

    return count


def find_sparse_model_dir(colmap_workspace):
    sparse_root = colmap_workspace / "sparse"

    if not sparse_root.exists():
        return None

    candidate_dirs = []

    for item in sparse_root.iterdir():
        if not item.is_dir():
            continue

        cameras_bin = item / "cameras.bin"
        images_bin = item / "images.bin"
        points3d_bin = item / "points3D.bin"

        if cameras_bin.exists() and images_bin.exists() and points3d_bin.exists():
            candidate_dirs.append(item)

    if len(candidate_dirs) == 0:
        return None

    # 通常 COLMAP 第一个成功模型在 sparse/0
    candidate_dirs = sorted(candidate_dirs, key=lambda x: x.name)

    return candidate_dirs[0]


def check_readiness(output_folder):
    output_folder = Path(output_folder)

    clean_images_folder = output_folder / "clean_images"
    blurry_images_folder = output_folder / "blurry_images"

    image_infos_csv = output_folder / "image_infos.csv"
    clean_mapping_csv = output_folder / "clean_images_mapping.csv"
    reconstruction_report = output_folder / "reconstruction_report.md"
    resolution_plot = output_folder / "resolution_distribution.png"

    colmap_workspace = output_folder / "colmap_workspace"
    sparse_model_dir = find_sparse_model_dir(colmap_workspace)

    sparse_txt_dir = colmap_workspace / "sparse_txt"
    cameras_txt = sparse_txt_dir / "cameras.txt"
    images_txt = sparse_txt_dir / "images.txt"
    points3d_txt = sparse_txt_dir / "points3D.txt"

    sparse_ply = colmap_workspace / "sparse.ply"
    model_report = colmap_workspace / "model_report.txt"
    camera_trajectory = colmap_workspace / "camera_trajectory.png"

    clean_image_count = count_files(clean_images_folder)
    blurry_image_count = count_files(blurry_images_folder)
    clean_mapping_count = count_csv_rows(clean_mapping_csv)

    registered_image_count = count_registered_images(images_txt)
    point3d_count = count_points3d(points3d_txt)

    checks = {
        "output_folder_exists": output_folder.exists(),
        "clean_images_exists": clean_images_folder.exists(),
        "clean_mapping_exists": clean_mapping_csv.exists(),
        "image_infos_exists": image_infos_csv.exists(),
        "colmap_workspace_exists": colmap_workspace.exists(),
        "sparse_model_exists": sparse_model_dir is not None,
        "sparse_txt_exists": sparse_txt_dir.exists(),
        "cameras_txt_exists": cameras_txt.exists(),
        "images_txt_exists": images_txt.exists(),
        "points3d_txt_exists": points3d_txt.exists(),
        "sparse_ply_exists": sparse_ply.exists(),
        "model_report_exists": model_report.exists(),
        "camera_trajectory_exists": camera_trajectory.exists(),
        "reconstruction_report_exists": reconstruction_report.exists(),
        "resolution_plot_exists": resolution_plot.exists()
    }

    warnings = []
    suggestions = []

    if clean_image_count == 0:
        warnings.append("clean_images 目录中没有图片，无法进入 3DGS / 后续重建流程。")
        suggestions.append("请先运行 image_dataset_checker.py，并确认 clean_images 正常生成。")

    if clean_image_count < 20:
        warnings.append("clean_images 图片数量偏少，后续 COLMAP / 3DGS 结果可能不稳定。")
        suggestions.append("建议准备至少 20 张以上具有连续重叠的图片。")

    if clean_mapping_count != clean_image_count:
        warnings.append("clean_images_mapping.csv 的记录数量与 clean_images 图片数量不一致。")
        suggestions.append("建议重新运行 image_dataset_checker.py 生成 clean_images 和映射表。")

    if sparse_model_dir is None:
        warnings.append("未找到 COLMAP sparse 模型目录，例如 sparse/0。")
        suggestions.append("请先运行 run_colmap.bat，并确认 COLMAP mapper 成功完成。")

    if registered_image_count == 0:
        warnings.append("未从 images.txt 中解析到注册图片。")
        suggestions.append("请检查 COLMAP 是否成功生成 sparse_txt/images.txt。")

    if clean_image_count > 0 and registered_image_count > 0:
        registered_ratio = registered_image_count / clean_image_count
    else:
        registered_ratio = 0

    if registered_ratio < 0.5:
        warnings.append("COLMAP 注册图片比例较低。")
        suggestions.append("建议检查图片重叠率、模糊图片、弱纹理区域或拍摄视角跳跃问题。")
    elif registered_ratio < 0.8:
        warnings.append("COLMAP 注册图片比例一般。")
        suggestions.append("后续可以尝试增加图片数量或提升相邻图片重叠率。")

    if point3d_count < 1000:
        warnings.append("稀疏 3D 点数量较少。")
        suggestions.append("建议使用纹理更丰富的场景，避免大面积白墙、纯色桌面等弱纹理区域。")

    critical_ready = (
        clean_image_count > 0
        and sparse_model_dir is not None
        and checks["sparse_ply_exists"]
        and registered_image_count > 0
    )

    if critical_ready and len(warnings) == 0:
        status = "READY"
        conclusion = "当前数据已具备进入 3DGS / 后续三维重建实验的基础条件。"
    elif critical_ready:
        status = "READY_WITH_WARNINGS"
        conclusion = "当前数据基本具备进入 3DGS / 后续三维重建实验的条件，但仍有一些质量风险需要注意。"
    else:
        status = "NOT_READY"
        conclusion = "当前数据暂不建议进入 3DGS / 后续三维重建实验，需要先补齐关键文件或重新运行 COLMAP。"

    return {
        "output_folder": output_folder,
        "clean_images_folder": clean_images_folder,
        "blurry_images_folder": blurry_images_folder,
        "clean_image_count": clean_image_count,
        "blurry_image_count": blurry_image_count,
        "clean_mapping_count": clean_mapping_count,
        "colmap_workspace": colmap_workspace,
        "sparse_model_dir": sparse_model_dir,
        "registered_image_count": registered_image_count,
        "registered_ratio": registered_ratio,
        "point3d_count": point3d_count,
        "checks": checks,
        "warnings": warnings,
        "suggestions": suggestions,
        "status": status,
        "conclusion": conclusion
    }


def write_readiness_report(result, report_path):
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 三维重建 / 3DGS 数据准备检查报告\n\n")

        f.write("## 1. 总体结论\n\n")
        f.write(f"- 状态：`{result['status']}`\n")
        f.write(f"- 结论：{result['conclusion']}\n\n")

        f.write("## 2. 数据集清洗结果\n\n")
        f.write(f"- clean_images 目录：`{result['clean_images_folder']}`\n")
        f.write(f"- clean_images 图片数量：{result['clean_image_count']}\n")
        f.write(f"- blurry_images 图片数量：{result['blurry_image_count']}\n")
        f.write(f"- clean_images_mapping.csv 记录数量：{result['clean_mapping_count']}\n\n")

        f.write("## 3. COLMAP 重建结果\n\n")
        f.write(f"- COLMAP 工作目录：`{result['colmap_workspace']}`\n")
        f.write(f"- sparse 模型目录：`{result['sparse_model_dir']}`\n")
        f.write(f"- 注册图片数量：{result['registered_image_count']}\n")
        f.write(f"- 注册图片比例：{result['registered_ratio'] * 100:.2f}%\n")
        f.write(f"- 稀疏 3D 点数量：{result['point3d_count']}\n\n")

        f.write("## 4. 关键文件检查\n\n")
        f.write("| 文件 / 目录 | 状态 |\n")
        f.write("|---|---|\n")

        for name, exists in result["checks"].items():
            status_text = "存在" if exists else "缺失"
            f.write(f"| {name} | {status_text} |\n")

        f.write("\n")

        f.write("## 5. 风险提示\n\n")
        if len(result["warnings"]) == 0:
            f.write("未发现明显风险。\n\n")
        else:
            for warning in result["warnings"]:
                f.write(f"- {warning}\n")
            f.write("\n")

        f.write("## 6. 建议\n\n")
        if len(result["suggestions"]) == 0:
            f.write("- 当前结果较完整，可以继续进行 3DGS / 后续三维重建实验。\n")
        else:
            for suggestion in result["suggestions"]:
                f.write(f"- {suggestion}\n")

    print(f"数据准备检查报告已生成：{report_path}")


def main():
    args = parse_args()

    output_folder = Path(args.output)
    report_path = output_folder / "training_data_readiness_report.md"

    result = check_readiness(output_folder)
    write_readiness_report(result, report_path)


if __name__ == "__main__":
    main()