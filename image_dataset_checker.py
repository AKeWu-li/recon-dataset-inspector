# 检查图片是否合法、统计格式、分辨率和模糊程度
import shutil
from pathlib import Path
from PIL import Image
import csv
import matplotlib.pyplot as plt
import argparse

from blur_detector import calculate_blur_score

# 命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="三维重建图像数据集质量检测工具")

    parser.add_argument("--input", required=True, help="输入图片文件夹路径")
    parser.add_argument("--output", default="output", help="输出结果文件夹路径")
    parser.add_argument("--blur-threshold", type=float, default=100, help="模糊检测阈值")

    return parser.parse_args()

# 写入数据到csv
def write_csv(image_infos, csv_path):
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "filename",
            "suffix",
            "width",
            "height",
            "pixels",
            "blur_score",
            "is_blurry"
        ])

        for img_info in image_infos:
            writer.writerow([
                img_info["name"],
                img_info["suffix"],
                img_info["width"],
                img_info["height"],
                img_info["pixels"],
                img_info["blur_score"],
                img_info["is_blurry"]
            ])

# 绘制分辨率折线图
def plot_resolution_distribution(image_infos, output_path):
    if len(image_infos) == 0:
        print("没有有效图片，无法生成分辨率分布图")
        return

    pixel_values = [img_info["pixels"] for img_info in image_infos]

    plt.figure(figsize=(10, 5))
    plt.plot(range(len(pixel_values)), pixel_values, marker="o")

    plt.title("Image Resolution Distribution")
    plt.xlabel("Image Index")
    plt.ylabel("Pixels")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"分辨率分布图已保存到：{output_path}")


# 生成总结文档
def write_summary(summary_path, img_path, stats):
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# 三维重建图像数据集检查报告\n\n")

        f.write(f"扫描文件夹：`{img_path}`\n\n")

        f.write("## 1. 图片数量统计\n\n")
        f.write("| 类型 | 数量 |\n")
        f.write("|---|---:|\n")
        f.write(f"| 图片总数 | {stats['count']} |\n")
        f.write(f"| jpg 图片 | {stats['count_jpg']} |\n")
        f.write(f"| png 图片 | {stats['count_png']} |\n")
        f.write(f"| jpeg 图片 | {stats['count_jpeg']} |\n")
        f.write(f"| 其他图片 | {stats['count_other']} |\n\n")

        f.write("## 2. 分辨率统计\n\n")

        if stats["count"] > 0:
            max_image = stats["max_image"]
            min_image = stats["min_image"]

            f.write(f"- 最大分辨率：`{max_image['name']}`，{max_image['width']}x{max_image['height']}\n")
            f.write(f"- 最小分辨率：`{min_image['name']}`，{min_image['width']}x{min_image['height']}\n")
            f.write(f"- 平均分辨率：{stats['average_width']:.0f}x{stats['average_height']:.0f}\n\n")
        else:
            f.write("没有找到有效图片。\n\n")

        f.write("## 3. 模糊图片检测\n\n")
        f.write(f"- 模糊度阈值：{stats['blur_threshold']}\n")
        f.write(f"- 可能模糊图片数量：{stats['count_blurry']}\n")
        f.write(f"- 模糊图片输出目录：`{stats['blur_folder']}`\n\n")

        f.write("## 4. 建议\n\n")
        f.write("1. 建议人工检查 `blurry_images` 文件夹中的图片。\n")
        f.write("2. 如果模糊图片较多，建议重新采集数据。\n")
        f.write("3. 三维重建任务中应尽量保证图像清晰、视角连续、重叠区域充足。\n\n")

        f.write("## 5. 分辨率分布图\n\n")
        f.write("![分辨率分布图](resolution_distribution.png)\n")

# 将清晰图片放进clean_images，增加clean_immages_mapping.csv
def export_clean_images(image_infos, clean_folder, mapping_csv_path):
    index = 1

    with open(mapping_csv_path, mode="w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "new_name",
            "original_name",
            "original_path",
            "width",
            "height",
            "blur_score"
        ])

        for img_info in image_infos:
            if img_info["is_blurry"]:
                continue

            suffix = img_info["suffix"]
            new_image_name = f"{index:06d}{suffix}"
            new_image_path = clean_folder / new_image_name

            shutil.copy2(img_info["path"], new_image_path)

            writer.writerow([
                new_image_name,
                img_info["name"],
                str(img_info["path"]),
                img_info["width"],
                img_info["height"],
                img_info["blur_score"]
            ])

            index += 1

    print(f"清洗后的图片已保存到：{clean_folder}")
    print(f"重命名映射表已保存到：{mapping_csv_path}")


def scan_images(folder, blur_threshold, blur_folder):
    # 各类图片数量
    count = 0
    count_jpg = 0
    count_png = 0
    count_jpeg = 0
    count_other = 0
    count_blurry = 0

    # 图片列表
    image_files = []
    image_infos = []

    # 图片宽高
    count_width = 0
    count_height = 0

    for file in folder.iterdir():
        if not file.is_file():
            continue

        try:
            with Image.open(file) as img:
                img.verify()

            with Image.open(file) as img:
                width, height = img.size

            count += 1
            image_files.append(file)

            suffix = file.suffix.lower()

            if suffix == ".jpg":
                count_jpg += 1
            elif suffix == ".png":
                count_png += 1
            elif suffix == ".jpeg":
                count_jpeg += 1
            else:
                count_other += 1

            blur_score = calculate_blur_score(file)
            is_blurry = blur_score is not None and blur_score < blur_threshold

            if is_blurry:
                count_blurry += 1
                shutil.copy2(file, blur_folder / file.name)

            image_infos.append({
                "name": file.name,
                "path":file,
                "suffix": suffix,
                "width": width,
                "height": height,
                "pixels": width * height,
                "blur_score": blur_score,
                "is_blurry": is_blurry
            })

            count_width += width
            count_height += height


        except Exception as e:

            print(f"{file} 不是有效图片，原因：{e}")

    max_image = None
    min_image = None
    average_width = 0
    average_height = 0

    if count > 0:
        max_image = max(image_infos, key=lambda x: x["pixels"])
        min_image = min(image_infos, key=lambda x: x["pixels"])
        average_width = count_width / count
        average_height = count_height / count

    stats = {
        "count": count,
        "count_jpg": count_jpg,
        "count_png": count_png,
        "count_jpeg": count_jpeg,
        "count_other": count_other,
        "count_blurry": count_blurry,
        "blur_threshold": blur_threshold,
        "blur_folder": blur_folder,
        "max_image": max_image,
        "min_image": min_image,
        "average_width": average_width,
        "average_height": average_height
    }

    return image_infos, image_files, stats

# 生成colmap批处理脚本
def generate_colmap_bat(clean_folder, output_folder):
    colmap_workspace = output_folder / "colmap_workspace"
    colmap_workspace.mkdir(parents=True, exist_ok=True)

    sparse_folder = colmap_workspace / "sparse"
    sparse_folder.mkdir(parents=True, exist_ok=True)

    script_path = output_folder / "run_colmap.bat"

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("echo Running COLMAP reconstruction...\n\n")

        f.write("set \"SCRIPT_DIR=%~dp0\"\n")
        f.write("set \"IMAGE_PATH=%SCRIPT_DIR%clean_images\"\n")
        f.write("set \"WORKSPACE_PATH=%SCRIPT_DIR%colmap_workspace\"\n")
        f.write("set \"DATABASE_PATH=%WORKSPACE_PATH%\\database.db\"\n")
        f.write("set \"SPARSE_PATH=%WORKSPACE_PATH%\\sparse\"\n")
        f.write("set \"MODEL_PATH=%SPARSE_PATH%\\0\"\n")
        f.write("set \"TXT_PATH=%WORKSPACE_PATH%\\sparse_txt\"\n")
        f.write("set \"PLY_PATH=%WORKSPACE_PATH%\\sparse.ply\"\n")
        f.write("set \"REPORT_PATH=%WORKSPACE_PATH%\\model_report.txt\"\n\n")

        f.write("if exist \"%WORKSPACE_PATH%\" rmdir /s /q \"%WORKSPACE_PATH%\"\n")
        f.write("mkdir \"%WORKSPACE_PATH%\"\n")
        f.write("mkdir \"%SPARSE_PATH%\"\n")
        f.write("mkdir \"%TXT_PATH%\"\n\n")

        f.write("colmap feature_extractor ^\n")
        f.write("  --database_path \"%DATABASE_PATH%\" ^\n")
        f.write("  --image_path \"%IMAGE_PATH%\"\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo feature_extractor failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("colmap exhaustive_matcher ^\n")
        f.write("  --database_path \"%DATABASE_PATH%\"\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo exhaustive_matcher failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("colmap mapper ^\n")
        f.write("  --database_path \"%DATABASE_PATH%\" ^\n")
        f.write("  --image_path \"%IMAGE_PATH%\" ^\n")
        f.write("  --output_path \"%SPARSE_PATH%\"\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo mapper failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("echo Exporting COLMAP model...\n\n")

        f.write("if not exist \"%MODEL_PATH%\" (\n")
        f.write("  echo COLMAP model folder not found: %MODEL_PATH%\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("colmap model_analyzer ^\n")
        f.write("  --path \"%MODEL_PATH%\" > \"%REPORT_PATH%\"\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo model_analyzer failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("colmap model_converter ^\n")
        f.write("  --input_path \"%MODEL_PATH%\" ^\n")
        f.write("  --output_path \"%TXT_PATH%\" ^\n")
        f.write("  --output_type TXT\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo model_converter TXT failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("colmap model_converter ^\n")
        f.write("  --input_path \"%MODEL_PATH%\" ^\n")
        f.write("  --output_path \"%PLY_PATH%\" ^\n")
        f.write("  --output_type PLY\n\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo model_converter PLY failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("echo COLMAP reconstruction and export finished.\n")
        f.write("pause\n")

    print(f"COLMAP 脚本已生成：{script_path}")


def main():

    args = parse_args()

    # 图片数据文件夹
    img_path = args.input
    folder = Path(img_path)

    if not folder.exists():
        print(f"图片文件夹不存在：{folder}")
        exit()

    if not folder.is_dir():
        print(f"输入路径不是文件夹：{folder}")
        exit()

    # 输出文件夹
    out_folder = Path(args.output)
    out_folder.mkdir(parents=True, exist_ok=True)

    # 模糊图片文件夹
    blur_folder = out_folder / "blurry_images"

    if blur_folder.exists():
        shutil.rmtree(blur_folder)

    blur_folder.mkdir(parents=True, exist_ok=True)

    # 清晰图片文件夹
    clean_folder = out_folder / "clean_images"

    if clean_folder.exists():
        shutil.rmtree(clean_folder)

    clean_folder.mkdir(parents=True, exist_ok=True)

    clean_mapping_csv_path = out_folder / "clean_images_mapping.csv"

    # 总结文件
    # summary_path = out_folder / "summary.md"

    image_infos_csv_path = out_folder / "image_infos.csv"

    # 模糊度阈值
    blur_threshold = args.blur_threshold


    image_infos, image_files, stats = scan_images(folder, blur_threshold, blur_folder)

    print(f"当前扫描文件夹：{img_path}")
    print(f"图片总数：{stats['count']}")
    print(f"jpg 图片数量：{stats['count_jpg']}")
    print(f"png 图片数量：{stats['count_png']}")
    print(f"jpeg 图片数量：{stats['count_jpeg']}")
    print(f"其他图片数量：{stats['count_other']}")
    print(f"可能模糊图片数量：{stats['count_blurry']}")

    print("前 5 张图片：")
    for file in image_files[:5]:
        print(file.name)

    if stats["count"] > 0:
        max_image = stats["max_image"]
        min_image = stats["min_image"]

        print(f"最大分辨率：{max_image['name']}，{max_image['width']}x{max_image['height']}")
        print(f"最小分辨率：{min_image['name']}，{min_image['width']}x{min_image['height']}")
        print(f"平均分辨率：{stats['average_width']:.0f}x{stats['average_height']:.0f}")
    else:
        print("没有找到有效图片")

    write_csv(image_infos, image_infos_csv_path)

    export_clean_images(image_infos , clean_folder , clean_mapping_csv_path)

    generate_colmap_bat(clean_folder, out_folder)

    print(f"CSV 文件已保存到：{image_infos_csv_path}")

    resolution_plot_path = out_folder / "resolution_distribution.png"
    plot_resolution_distribution(image_infos, resolution_plot_path)

    # write_summary(summary_path, img_path, stats)
    # print(f"总结报告已保存到：{summary_path}")

if __name__ == "__main__":
    main()