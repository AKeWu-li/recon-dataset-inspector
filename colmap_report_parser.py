from pathlib import Path
import argparse
import csv
import numpy as np
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(description="生成三维重建报告")

    parser.add_argument(
        "--output",
        default="output",
        help="项目输出目录"
    )

    return parser.parse_args()


def count_files_in_folder(folder):
    if not folder.exists():
        return 0

    return len([file for file in folder.iterdir() if file.is_file()])


def read_text_if_exists(path):
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")

    return None


def get_image_dataset_stats(image_infos_csv):
    if not image_infos_csv.exists():
        return None

    image_infos = []

    with open(image_infos_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            image_infos.append(row)

    if len(image_infos) == 0:
        return {
            "total": 0,
            "blurry": 0,
            "max_pixels_image": None,
            "min_pixels_image": None
        }

    blurry_count = 0

    for info in image_infos:
        if info["is_blurry"] == "True":
            blurry_count += 1

    max_pixels_image = max(image_infos, key=lambda x: int(x["pixels"]))
    min_pixels_image = min(image_infos, key=lambda x: int(x["pixels"]))

    return {
        "total": len(image_infos),
        "blurry": blurry_count,
        "max_pixels_image": max_pixels_image,
        "min_pixels_image": min_pixels_image
    }


def generate_reconstruction_report(output_folder):
    output_folder = Path(output_folder)

    image_infos_csv = output_folder / "image_infos.csv"
    clean_mapping_csv = output_folder / "clean_images_mapping.csv"
    resolution_plot = output_folder / "resolution_distribution.png"

    clean_folder = output_folder / "clean_images"
    blurry_folder = output_folder / "blurry_images"

    colmap_workspace = output_folder / "colmap_workspace"
    model_report_path = colmap_workspace / "model_report.txt"
    sparse_ply_path = colmap_workspace / "sparse.ply"
    sparse_txt_path = colmap_workspace / "sparse_txt"
    images_txt_path = sparse_txt_path / "images.txt"
    camera_trajectory_path = colmap_workspace / "camera_trajectory.png"

    colmap_txt_stats = parse_colmap_txt_model(sparse_txt_path)

    reconstruction_report_path = output_folder / "reconstruction_report.md"

    dataset_stats = get_image_dataset_stats(image_infos_csv)
    model_report_content = read_text_if_exists(model_report_path)

    clean_image_count = count_files_in_folder(clean_folder)
    blurry_image_count = count_files_in_folder(blurry_folder)

    camera_centers = parse_camera_centers(images_txt_path)
    plot_camera_trajectory(camera_centers, camera_trajectory_path)

    quality_result = evaluate_reconstruction_quality(
        clean_image_count,
        colmap_txt_stats,
        sparse_ply_path.exists()
    )

    with open(reconstruction_report_path, "w", encoding="utf-8") as f:
        f.write("# 三维重建数据集与 COLMAP 重建报告\n\n")

        f.write("## 1. 输出目录\n\n")
        f.write(f"- 输出目录：`{output_folder}`\n")
        f.write(f"- COLMAP 工作目录：`{colmap_workspace}`\n\n")

        f.write("## 2. 数据集检查结果\n\n")

        if dataset_stats is None:
            f.write("未找到 `image_infos.csv`，请先运行 `image_dataset_checker.py`。\n\n")
        else:
            f.write(f"- 有效图片数量：{dataset_stats['total']}\n")
            f.write(f"- 疑似模糊图片数量：{dataset_stats['blurry']}\n")
            f.write(f"- clean_images 图片数量：{clean_image_count}\n")
            f.write(f"- blurry_images 图片数量：{blurry_image_count}\n")

            if dataset_stats["max_pixels_image"] is not None:
                max_img = dataset_stats["max_pixels_image"]
                min_img = dataset_stats["min_pixels_image"]

                f.write(
                    f"- 最大分辨率图片：`{max_img['filename']}`，"
                    f"{max_img['width']}x{max_img['height']}\n"
                )
                f.write(
                    f"- 最小分辨率图片：`{min_img['filename']}`，"
                    f"{min_img['width']}x{min_img['height']}\n"
                )

            f.write("\n")

        f.write("## 3. 数据清洗输出文件\n\n")
        f.write(f"- `image_infos.csv`：{'存在' if image_infos_csv.exists() else '不存在'}\n")
        f.write(f"- `clean_images_mapping.csv`：{'存在' if clean_mapping_csv.exists() else '不存在'}\n")
        f.write(f"- `clean_images/`：{'存在' if clean_folder.exists() else '不存在'}\n")
        f.write(f"- `blurry_images/`：{'存在' if blurry_folder.exists() else '不存在'}\n\n")

        f.write("## 4. 分辨率分布图\n\n")

        if resolution_plot.exists():
            f.write("![分辨率分布图](resolution_distribution.png)\n\n")
        else:
            f.write("未找到 `resolution_distribution.png`。\n\n")

        f.write("## 5. COLMAP 输出文件检查\n\n")
        f.write(f"- `model_report.txt`：{'存在' if model_report_path.exists() else '不存在'}\n")
        f.write(f"- `sparse.ply`：{'存在' if sparse_ply_path.exists() else '不存在'}\n")
        f.write(f"- `sparse_txt/`：{'存在' if sparse_txt_path.exists() else '不存在'}\n\n")

        f.write("## 6. COLMAP 模型分析结果\n\n")

        if model_report_content is not None:
            f.write("```text\n")
            f.write(model_report_content)
            f.write("\n```\n\n")
        else:
            f.write("未找到 `model_report.txt`，请先运行 `run_colmap.bat`。\n\n")

        f.write("## 7.COLMAP 重建统计\n\n")

        if sparse_txt_path.exists():
            f.write(f"- 相机数量：{colmap_txt_stats['camera_count']}\n")
            f.write(f"- 成功注册图片数量：{colmap_txt_stats['registered_image_count']}\n")
            f.write(f"- 稀疏 3D 点数量：{colmap_txt_stats['point3d_count']}\n\n")
        else:
            f.write("未找到 `sparse_txt/`，请先运行 COLMAP 并导出 TXT 模型。\n\n")

        f.write("## 8.相机轨迹可视化\n\n")

        if camera_trajectory_path.exists():
            f.write("![相机轨迹](colmap_workspace/camera_trajectory.png)\n\n")
        else:
            f.write("未生成相机轨迹图。\n\n")

        f.write("## 9.重建质量诊断\n\n")
        f.write(f"- 综合评分：{quality_result['score']} / 100\n")
        f.write(f"- 重建质量：{quality_result['quality']}\n")
        f.write(f"- 注册图片比例：{quality_result['registered_ratio'] * 100:.2f}%\n\n")

        f.write("### 诊断结果\n\n")
        for item in quality_result["warnings"]:
            f.write(f"- {item}\n")

        f.write("\n### 建议\n\n")
        for item in quality_result["suggestions"]:
            f.write(f"- {item}\n")

        f.write("\n")

        f.write("## 10. 建议\n\n")
        f.write("1. 如果 COLMAP 注册图片数量较少，建议增加图片数量，并保证相邻图片有足够重叠。\n")
        f.write("2. 如果稀疏点数量较少，建议检查场景纹理、模糊图片和拍摄视角覆盖情况。\n")
        f.write("3. 如果重投影误差较高，建议检查低质量图片，或重新采集更清晰、重叠更充分的数据。\n")

    print(f"最终重建报告已生成：{reconstruction_report_path}")

def count_registered_images(images_txt_path):
    if not images_txt_path.exists():
        return 0

    count = 0
    expect_image_line = True

    with open(images_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            if line.startswith("#"):
                continue

            if expect_image_line:
                if not line:
                    continue

                parts = line.split()

                # IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME
                if len(parts) >= 10:
                    count += 1
                    expect_image_line = False
            else:
                # 消费 POINTS2D 那一行，不管它是不是空行
                expect_image_line = True

    return count

def parse_colmap_txt_model(sparse_txt_path):
    cameras_txt = sparse_txt_path / "cameras.txt"
    images_txt = sparse_txt_path / "images.txt"
    points3d_txt = sparse_txt_path / "points3D.txt"

    stats = {
        "camera_count": 0,
        "registered_image_count": 0,
        "point3d_count": 0
    }

    if cameras_txt.exists():
        with open(cameras_txt, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    stats["camera_count"] += 1

    if images_txt.exists():
        stats["registered_image_count"] = count_registered_images(images_txt)

    if points3d_txt.exists():
        with open(points3d_txt, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    stats["point3d_count"] += 1

    return stats

# 把 COLMAP 给的四元数 QW QX QY QZ 转成旋转矩阵 R
def qvec_to_rotmat(qvec):
    qw, qx, qy, qz = qvec

    return np.array([
        [
            1 - 2 * qy * qy - 2 * qz * qz,
            2 * qx * qy - 2 * qw * qz,
            2 * qz * qx + 2 * qw * qy
        ],
        [
            2 * qx * qy + 2 * qw * qz,
            1 - 2 * qx * qx - 2 * qz * qz,
            2 * qy * qz - 2 * qw * qx
        ],
        [
            2 * qz * qx - 2 * qw * qy,
            2 * qy * qz + 2 * qw * qx,
            1 - 2 * qx * qx - 2 * qy * qy
        ]
    ])

# 解析images.txt
def parse_camera_centers(images_txt_path):
    images_txt_path = Path(images_txt_path)

    camera_centers = []

    if not images_txt_path.exists():
        print(f"images.txt 不存在：{images_txt_path}")
        return camera_centers

    expect_image_line = True

    with open(images_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            if line.startswith("#"):
                continue

            if expect_image_line:
                if not line:
                    continue

                parts = line.split()

                if len(parts) < 10:
                    continue

                image_id = int(parts[0])

                qw = float(parts[1])
                qx = float(parts[2])
                qy = float(parts[3])
                qz = float(parts[4])

                tx = float(parts[5])
                ty = float(parts[6])
                tz = float(parts[7])

                camera_id = int(parts[8])

                # 比 parts[9] 更稳，如果图片名里有空格也不会丢
                image_name = " ".join(parts[9:])

                qvec = np.array([qw, qx, qy, qz])
                tvec = np.array([tx, ty, tz])

                R = qvec_to_rotmat(qvec)

                camera_center = -R.T @ tvec

                camera_centers.append({
                    "image_id": image_id,
                    "camera_id": camera_id,
                    "name": image_name,
                    "x": float(camera_center[0]),
                    "y": float(camera_center[1]),
                    "z": float(camera_center[2])
                })

                expect_image_line = False

            else:
                # 不管 POINTS2D 行是不是空，都把它消费掉
                expect_image_line = True

    return camera_centers


# 画相机轨迹图
def plot_camera_trajectory(camera_centers, output_path):
    if len(camera_centers) == 0:
        print("没有相机中心数据，无法生成相机轨迹图")
        return

    xs = [camera["x"] for camera in camera_centers]
    zs = [camera["z"] for camera in camera_centers]

    plt.figure(figsize=(8, 6))

    plt.scatter(xs, zs, label="Camera Centers")
    plt.plot(xs, zs, linestyle="--", label="Camera Path")

    for i, camera in enumerate(camera_centers):
        plt.text(camera["x"], camera["z"], str(i + 1), fontsize=8)

    plt.title("COLMAP Camera Trajectory")
    plt.xlabel("X")
    plt.ylabel("Z")
    plt.legend()
    plt.axis("equal")
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()

    print(f"相机轨迹图已保存到：{output_path}")

def evaluate_reconstruction_quality(clean_image_count, colmap_stats, sparse_ply_exists):
    score = 0
    warnings = []
    suggestions = []

    registered_count = colmap_stats["registered_image_count"]
    point3d_count = colmap_stats["point3d_count"]

    if clean_image_count > 0:
        registered_ratio = registered_count / clean_image_count
    else:
        registered_ratio = 0

    # 1. 注册率评分
    if registered_ratio >= 0.8:
        score += 35
        warnings.append("注册图片比例较高，说明图像之间重叠关系较好。")
    elif registered_ratio >= 0.5:
        score += 20
        warnings.append("注册图片比例一般，部分图片可能没有成功参与重建。")
        suggestions.append("建议检查未注册图片是否存在模糊、弱纹理或视角跳跃问题。")
    else:
        score += 5
        warnings.append("注册图片比例较低，重建结果可能不稳定。")
        suggestions.append("建议重新采集更多具有连续重叠的图片。")

    # 2. 稀疏点数量评分
    if point3d_count >= 5000:
        score += 35
        warnings.append("稀疏 3D 点数量较充足。")
    elif point3d_count >= 1000:
        score += 20
        warnings.append("稀疏 3D 点数量一般。")
        suggestions.append("建议增加纹理丰富区域的拍摄视角。")
    else:
        score += 5
        warnings.append("稀疏 3D 点数量较少。")
        suggestions.append("建议选择纹理更丰富的场景，避免白墙、纯色桌面等弱纹理区域。")

    # 3. PLY 文件评分
    if sparse_ply_exists:
        score += 20
        warnings.append("已成功导出 sparse.ply 文件。")
    else:
        warnings.append("未找到 sparse.ply 文件，COLMAP 模型导出可能失败。")
        suggestions.append("请检查 run_colmap.bat 是否完整运行成功。")

    # 4. 基础数量评分
    if clean_image_count >= 20:
        score += 10
    else:
        suggestions.append("clean_images 数量偏少，建议至少准备 20 张以上具有重叠的图片。")

    if score >= 80:
        quality = "较好"
    elif score >= 50:
        quality = "一般"
    else:
        quality = "较差"

    return {
        "score": score,
        "quality": quality,
        "registered_ratio": registered_ratio,
        "warnings": warnings,
        "suggestions": suggestions
    }

def main():
    args = parse_args()
    generate_reconstruction_report(args.output)


if __name__ == "__main__":
    main()