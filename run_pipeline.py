from pathlib import Path
import argparse
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="三维重建数据预处理与 COLMAP/3DGS 准备流程总控脚本")

    parser.add_argument(
        "--input",
        default=None,
        help="输入图片文件夹路径。第一阶段必须提供，例如 dataset/images"
    )

    parser.add_argument(
        "--output",
        default="output",
        help="输出结果文件夹路径，默认 output"
    )

    parser.add_argument(
        "--blur-threshold",
        type=float,
        default=100,
        help="模糊检测阈值，默认 100"
    )

    parser.add_argument(
        "--after-colmap",
        action="store_true",
        help="COLMAP 运行完成后，执行结果解析、readiness 检查和 3DGS scene 导出"
    )

    parser.add_argument(
        "--scene-name",
        default="gaussian_splatting_scene",
        help="导出的 3DGS scene 文件夹名称"
    )

    parser.add_argument(
        "--skip-scene-export",
        action="store_true",
        help="跳过 3DGS scene 导出"
    )

    parser.add_argument(
        "--gaussian-repo",
        default=None,
        help="官方 3D Gaussian Splatting 仓库路径。暂时可不填，后续需要生成训练脚本时再填"
    )

    parser.add_argument(
        "--conda-env",
        default="gaussian_splatting",
        help="3DGS 训练环境名称，默认 gaussian_splatting"
    )

    return parser.parse_args()


def check_script_exists(project_root, script_name):
    script_path = project_root / script_name

    if not script_path.exists():
        print(f"缺少脚本文件：{script_path}")
        sys.exit(1)

    return script_path


def run_command(description, command, cwd):
    print("\n" + "=" * 80)
    print(description)
    print("执行命令：")
    print(" ".join(str(item) for item in command))
    print("=" * 80 + "\n")

    result = subprocess.run(command, cwd=cwd)

    if result.returncode != 0:
        print(f"步骤失败：{description}")
        print(f"返回码：{result.returncode}")
        sys.exit(result.returncode)


def run_pre_colmap_stage(args, project_root):
    if args.input is None:
        print("第一阶段必须提供 --input，例如：")
        print("python run_pipeline.py --input dataset/images --output output --blur-threshold 50")
        sys.exit(1)

    check_script_exists(project_root, "image_dataset_checker.py")

    command = [
        sys.executable,
        "image_dataset_checker.py",
        "--input",
        args.input,
        "--output",
        args.output,
        "--blur-threshold",
        str(args.blur_threshold)
    ]

    run_command(
        description="阶段 1：图片检查、数据清洗、clean_images 导出、COLMAP 脚本生成",
        command=command,
        cwd=project_root
    )

    output_folder = project_root / args.output
    colmap_bat = output_folder / "run_colmap.bat"

    print("\n第一阶段完成。")
    print(f"输出目录：{output_folder}")

    if colmap_bat.exists():
        print("\n下一步请运行 COLMAP 脚本：")
        print(colmap_bat)
        print("\n例如在 PowerShell 中运行：")
        print(f"{args.output}\\run_colmap.bat")
    else:
        print("\n未找到 run_colmap.bat，请检查 image_dataset_checker.py 是否生成了 COLMAP 脚本。")

    print("\nCOLMAP 运行完成后，再执行：")
    print(f"python run_pipeline.py --output {args.output} --after-colmap")


def run_after_colmap_stage(args, project_root):
    output_folder = project_root / args.output

    if not output_folder.exists():
        print(f"输出目录不存在：{output_folder}")
        print("请先运行第一阶段：")
        print("python run_pipeline.py --input dataset/images --output output --blur-threshold 50")
        sys.exit(1)

    check_script_exists(project_root, "colmap_report_parser.py")
    check_script_exists(project_root, "reconstruction_readiness_checker.py")

    command_report = [
        sys.executable,
        "colmap_report_parser.py",
        "--output",
        args.output
    ]

    run_command(
        description="阶段 2.1：解析 COLMAP 结果并生成 reconstruction_report.md",
        command=command_report,
        cwd=project_root
    )

    command_readiness = [
        sys.executable,
        "reconstruction_readiness_checker.py",
        "--output",
        args.output
    ]

    run_command(
        description="阶段 2.2：检查是否具备进入后续 3DGS / 三维重建实验的条件",
        command=command_readiness,
        cwd=project_root
    )

    if not args.skip_scene_export:
        check_script_exists(project_root, "gaussian_scene_exporter.py")

        command_scene = [
            sys.executable,
            "gaussian_scene_exporter.py",
            "--output",
            args.output,
            "--scene-name",
            args.scene_name
        ]

        if args.gaussian_repo is not None:
            command_scene.extend([
                "--gaussian-repo",
                args.gaussian_repo,
                "--conda-env",
                args.conda_env
            ])

        run_command(
            description="阶段 2.3：导出标准 3D Gaussian Splatting scene 目录",
            command=command_scene,
            cwd=project_root
        )
    else:
        print("已跳过 3DGS scene 导出。")

    print("\n第二阶段完成。")
    print(f"最终报告：{output_folder / 'reconstruction_report.md'}")
    print(f"数据准备检查报告：{output_folder / 'training_data_readiness_report.md'}")

    if not args.skip_scene_export:
        print(f"3DGS scene 目录：{output_folder / args.scene_name}")


def main():
    args = parse_args()

    project_root = Path(__file__).resolve().parent

    if args.after_colmap:
        run_after_colmap_stage(args, project_root)
    else:
        run_pre_colmap_stage(args, project_root)


if __name__ == "__main__":
    main()