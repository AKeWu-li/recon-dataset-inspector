from pathlib import Path
import argparse
import shutil


def parse_args():
    parser = argparse.ArgumentParser(description="导出标准 3D Gaussian Splatting scene 目录")

    parser.add_argument(
        "--output",
        default="output",
        help="项目输出目录"
    )

    parser.add_argument(
        "--scene-name",
        default="gaussian_splatting_scene",
        help="导出的 scene 文件夹名称"
    )

    parser.add_argument(
        "--gaussian-repo",
        default=None,
        help="官方 3D Gaussian Splatting 仓库路径；如果不提供，则只导出 scene，不生成训练脚本"
    )

    parser.add_argument(
        "--conda-env",
        default="gaussian_splatting",
        help="3DGS 使用的 conda 环境名称"
    )

    return parser.parse_args()


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

    candidate_dirs = sorted(candidate_dirs, key=lambda x: x.name)

    return candidate_dirs[0]


def copy_folder_files(src_folder, dst_folder):
    dst_folder.mkdir(parents=True, exist_ok=True)

    copied_count = 0

    for file in src_folder.iterdir():
        if not file.is_file():
            continue

        shutil.copy2(file, dst_folder / file.name)
        copied_count += 1

    return copied_count


def export_gaussian_scene(output_folder, scene_name):
    output_folder = Path(output_folder)

    clean_images_folder = output_folder / "clean_images"
    colmap_workspace = output_folder / "colmap_workspace"

    sparse_model_dir = find_sparse_model_dir(colmap_workspace)

    scene_folder = output_folder / scene_name
    scene_images_folder = scene_folder / "images"
    scene_sparse_folder = scene_folder / "sparse" / "0"

    if not output_folder.exists():
        print(f"输出目录不存在：{output_folder}")
        return

    if not clean_images_folder.exists():
        print(f"clean_images 目录不存在：{clean_images_folder}")
        return

    if sparse_model_dir is None:
        print(f"未找到 COLMAP sparse 模型目录：{colmap_workspace / 'sparse'}")
        return

    if scene_folder.exists():
        shutil.rmtree(scene_folder)

    scene_images_folder.mkdir(parents=True, exist_ok=True)
    scene_sparse_folder.mkdir(parents=True, exist_ok=True)

    image_count = copy_folder_files(clean_images_folder, scene_images_folder)

    required_sparse_files = [
        "cameras.bin",
        "images.bin",
        "points3D.bin"
    ]

    for filename in required_sparse_files:
        src_file = sparse_model_dir / filename
        dst_file = scene_sparse_folder / filename

        if not src_file.exists():
            print(f"缺少 COLMAP 文件：{src_file}")
            return

        shutil.copy2(src_file, dst_file)

    report_path = scene_folder / "scene_export_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Gaussian Splatting Scene Export Report\n\n")

        f.write("## 1. 导出结果\n\n")
        f.write(f"- Scene 目录：`{scene_folder}`\n")
        f.write(f"- 图片目录：`{scene_images_folder}`\n")
        f.write(f"- COLMAP sparse 目录：`{scene_sparse_folder}`\n")
        f.write(f"- 图片数量：{image_count}\n\n")

        f.write("## 2. 目录结构\n\n")
        f.write("```text\n")
        f.write(f"{scene_name}/\n")
        f.write("├── images/\n")
        f.write("└── sparse/\n")
        f.write("    └── 0/\n")
        f.write("        ├── cameras.bin\n")
        f.write("        ├── images.bin\n")
        f.write("        └── points3D.bin\n")
        f.write("```\n\n")

        f.write("## 3. 后续使用\n\n")
        f.write("如果使用官方 3D Gaussian Splatting 项目，可以尝试：\n\n")
        f.write("```bash\n")
        f.write(f"python train.py -s {scene_folder}\n")
        f.write("```\n\n")

        f.write("注意：不同 3DGS 项目的训练命令可能略有差异，请根据对应项目 README 调整。\n")

    print("标准 Gaussian Splatting scene 已导出。")
    print(f"Scene 目录：{scene_folder}")
    print(f"图片数量：{image_count}")
    print(f"导出报告：{report_path}")

    return scene_folder

# 生成 3DGS 训练命令脚本
def generate_3dgs_train_bat(scene_folder, output_folder, gaussian_repo_path, conda_env="gaussian_splatting"):
    script_path = output_folder / "run_3dgs_train.bat"
    model_output_path = output_folder / "3dgs_output"

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("echo Running 3D Gaussian Splatting training...\n\n")

        f.write(f"set \"GAUSSIAN_REPO={gaussian_repo_path}\"\n")
        f.write(f"set \"SCENE_PATH={scene_folder}\"\n")
        f.write(f"set \"MODEL_OUTPUT={model_output_path}\"\n\n")

        f.write("if not exist \"%GAUSSIAN_REPO%\" (\n")
        f.write("  echo Gaussian Splatting repo not found: %GAUSSIAN_REPO%\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("if not exist \"%SCENE_PATH%\" (\n")
        f.write("  echo Scene path not found: %SCENE_PATH%\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("if not exist \"%MODEL_OUTPUT%\" mkdir \"%MODEL_OUTPUT%\"\n\n")

        f.write(f"call conda activate {conda_env}\n")
        f.write("if errorlevel 1 (\n")
        f.write("  echo Failed to activate conda environment.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("cd /d \"%GAUSSIAN_REPO%\"\n\n")

        f.write("python train.py ^\n")
        f.write("  -s \"%SCENE_PATH%\" ^\n")
        f.write("  -m \"%MODEL_OUTPUT%\"\n\n")

        f.write("if errorlevel 1 (\n")
        f.write("  echo 3DGS training failed.\n")
        f.write("  pause\n")
        f.write("  exit /b 1\n")
        f.write(")\n\n")

        f.write("echo 3DGS training finished.\n")
        f.write("echo Model output: %MODEL_OUTPUT%\n")
        f.write("pause\n")

    print(f"3DGS 训练脚本已生成：{script_path}")

def main():
    args = parse_args()

    scene_folder = export_gaussian_scene(args.output, args.scene_name)

    if scene_folder is None:
        return

    if args.gaussian_repo is not None:
        generate_3dgs_train_bat(
            scene_folder=scene_folder,
            output_folder=Path(args.output),
            gaussian_repo_path=Path(args.gaussian_repo),
            conda_env=args.conda_env
        )
    else:
        print("未提供 --gaussian-repo，仅导出标准 3DGS scene 目录，不生成训练脚本。")


if __name__ == "__main__":
    main()