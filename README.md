# Recon Dataset Inspector

面向三维重建任务的图像数据集检查、清洗、COLMAP 稀疏重建辅助与 3DGS 数据准备工具。

本项目用于将原始图片数据集整理为更适合三维重建实验的输入数据，支持图片有效性检查、模糊图片检测、清洗后图片导出、COLMAP 脚本生成、COLMAP 重建结果解析、相机轨迹可视化、重建质量诊断，以及标准 3D Gaussian Splatting scene 目录导出。

---

## 1. 项目功能

当前项目支持：

- 检查图片文件是否合法
- 统计图片格式数量
- 统计图片分辨率信息
- 使用 Laplacian 方差检测疑似模糊图片
- 将疑似模糊图片复制到 `blurry_images/`
- 将清晰图片复制到 `clean_images/` 并统一重命名
- 生成 `clean_images_mapping.csv`，保存原始文件名与新文件名映射关系
- 生成 `image_infos.csv`，保存每张图片的详细信息
- 绘制图片分辨率分布图
- 自动生成 `run_colmap.bat`
- 运行 COLMAP 后导出：
  - `model_report.txt`
  - `sparse.ply`
  - `sparse_txt/`
- 解析 COLMAP TXT 模型结果
- 统计注册图片数量、3D 点数量、观测信息
- 生成相机轨迹可视化图
- 生成最终重建报告 `reconstruction_report.md`
- 生成数据准备检查报告 `training_data_readiness_report.md`
- 导出标准 3D Gaussian Splatting scene 目录

---

## 2. 项目结构

```text
recon-dataset-inspector/
├── image_dataset_checker.py              # 图片检查、清洗、COLMAP 脚本生成
├── blur_detector.py                      # 模糊检测函数
├── colmap_report_parser.py               # COLMAP 结果解析与报告生成
├── reconstruction_readiness_checker.py   # 3DGS / 后续实验数据准备检查
├── gaussian_scene_exporter.py            # 标准 3DGS scene 目录导出
├── run_pipeline.py                       # 总控流程脚本
├── requirements.txt
├── README.md
├── dataset/
│   └── images/                           # 原始输入图片，不建议上传 GitHub
├── docs/                                 # 示例结果图片，可选
└── output/                               # 程序输出结果，不建议上传 GitHub
```

---

## 3. 环境依赖

建议使用 Python 3.9 或以上版本。

安装依赖：

```bash
pip install -r requirements.txt
```

`requirements.txt` 示例：

```text
Pillow
opencv-python
matplotlib
numpy
```

如果需要运行 COLMAP，请提前安装 COLMAP，并确保命令行中可以直接调用：

```bash
colmap
```

如果终端能够正确显示 COLMAP 帮助信息，说明环境变量配置基本正常。

---

## 4. 快速开始

### 4.1 第一阶段：图片检查、清洗与 COLMAP 脚本生成

运行：

```bash
python run_pipeline.py --input dataset/images --output output --blur-threshold 50
```

该阶段会完成：

```text
原始图片
→ 有效图片检查
→ 模糊图片检测
→ clean_images 导出
→ 分辨率统计
→ run_colmap.bat 生成
```

生成结果包括：

```text
output/
├── clean_images/
├── blurry_images/
├── image_infos.csv
├── clean_images_mapping.csv
├── resolution_distribution.png
└── run_colmap.bat
```

---

### 4.2 第二阶段：运行 COLMAP

第一阶段完成后，运行：

```bash
output/run_colmap.bat
```

该脚本会自动执行：

```text
COLMAP feature_extractor
COLMAP exhaustive_matcher
COLMAP mapper
COLMAP model_analyzer
COLMAP model_converter
```

成功后会生成：

```text
output/colmap_workspace/
├── database.db
├── sparse/
│   └── 0/
│       ├── cameras.bin
│       ├── images.bin
│       └── points3D.bin
├── sparse_txt/
│   ├── cameras.txt
│   ├── images.txt
│   └── points3D.txt
├── sparse.ply
└── model_report.txt
```

---

### 4.3 第三阶段：COLMAP 结果解析、报告生成与 3DGS scene 导出

COLMAP 运行完成后，执行：

```bash
python run_pipeline.py --output output --after-colmap
```

该阶段会完成：

```text
COLMAP 结果解析
→ reconstruction_report.md 生成
→ 相机轨迹可视化
→ 重建质量诊断
→ 数据准备检查
→ 标准 3DGS scene 导出
```

生成结果包括：

```text
output/
├── reconstruction_report.md
├── training_data_readiness_report.md
├── gaussian_splatting_scene/
│   ├── images/
│   └── sparse/
│       └── 0/
│           ├── cameras.bin
│           ├── images.bin
│           └── points3D.bin
└── colmap_workspace/
    ├── camera_trajectory.png
    ├── sparse.ply
    ├── model_report.txt
    └── sparse_txt/
```

---

## 5. 完整运行流程

推荐完整流程如下：

```bash
python run_pipeline.py --input dataset/images --output output --blur-threshold 50
```

然后运行：

```bash
output/run_colmap.bat
```

最后运行：

```bash
python run_pipeline.py --output output --after-colmap
```

---

## 6. 单独运行各个模块

除了使用 `run_pipeline.py`，也可以单独运行各个脚本。

### 6.1 图片检查与清洗

```bash
python image_dataset_checker.py --input dataset/images --output output --blur-threshold 50
```

### 6.2 COLMAP 结果报告生成

```bash
python colmap_report_parser.py --output output
```

### 6.3 数据准备检查

```bash
python reconstruction_readiness_checker.py --output output
```

### 6.4 导出标准 3DGS scene

```bash
python gaussian_scene_exporter.py --output output
```

导出结果：

```text
output/gaussian_splatting_scene/
├── images/
└── sparse/
    └── 0/
        ├── cameras.bin
        ├── images.bin
        └── points3D.bin
```

---

## 7. 生成 3DGS 训练脚本

如果已经下载了官方 3D Gaussian Splatting 仓库，并配置好了对应环境，可以额外传入 `--gaussian-repo` 参数。

示例：

```bash
python gaussian_scene_exporter.py ^
  --output output ^
  --scene-name gaussian_splatting_scene ^
  --gaussian-repo D:\PythonProject\gaussian-splatting ^
  --conda-env gaussian_splatting
```

这会额外生成：

```text
output/run_3dgs_train.bat
```

如果不提供 `--gaussian-repo`，则只导出标准 scene 目录，不生成训练脚本。

---

## 8. 输出文件说明

### 8.1 图片检查阶段输出

```text
output/image_infos.csv
```

保存每张有效图片的信息，包括：

```text
filename
suffix
width
height
pixels
blur_score
is_blurry
```

---

```text
output/clean_images/
```

保存清洗后的图片，图片会被重新命名为：

```text
000001.jpg
000002.jpg
000003.jpg
...
```

---

```text
output/clean_images_mapping.csv
```

保存清洗后文件名和原始文件名的映射关系。

---

```text
output/blurry_images/
```

保存疑似模糊图片，方便人工检查。

---

```text
output/resolution_distribution.png
```

图片分辨率分布图，用于观察数据集中是否存在异常低分辨率图片。

---

### 8.2 COLMAP 阶段输出

```text
output/colmap_workspace/sparse/0/
```

保存 COLMAP 稀疏重建结果：

```text
cameras.bin
images.bin
points3D.bin
```

---

```text
output/colmap_workspace/sparse_txt/
```

保存转换后的 TXT 模型：

```text
cameras.txt
images.txt
points3D.txt
```

---

```text
output/colmap_workspace/sparse.ply
```

稀疏点云文件，可以使用 MeshLab、CloudCompare、Open3D 等工具查看。

---

```text
output/colmap_workspace/model_report.txt
```

COLMAP 模型分析结果。

---

```text
output/colmap_workspace/camera_trajectory.png
```

相机轨迹可视化结果。

---

### 8.3 最终报告输出

```text
output/reconstruction_report.md
```

最终三维重建报告，包括：

- 数据集检查结果
- 清洗结果
- COLMAP 输出文件检查
- COLMAP 模型统计
- 相机轨迹图
- 重建质量诊断
- 后续建议

---

```text
output/training_data_readiness_report.md
```

检查当前数据是否具备进入 3DGS / 后续三维重建实验的基础条件。

---

## 9. 示例结果

如果项目中包含 `docs/` 示例图片，可以在这里展示。

### 9.1 分辨率分布图

![Resolution Distribution](docs/resolution_distribution.png)

### 9.2 相机轨迹图

![Camera Trajectory](docs/camera_trajectory.png)

---

## 10. 模糊检测方法

本项目使用 OpenCV 计算灰度图的 Laplacian 方差作为清晰度指标。

核心代码：

```python
blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
```

一般来说：

```text
Laplacian 方差越大 → 图像边缘和纹理越丰富 → 图片通常越清晰
Laplacian 方差越小 → 图像边缘和纹理越弱 → 图片可能越模糊
```

当：

```text
blur_score < blur_threshold
```

时，图片会被标记为疑似模糊图片，并复制到：

```text
output/blurry_images/
```

---

## 11. COLMAP 常见问题

### 11.1 `No images with matches`

如果运行 COLMAP 时出现：

```text
No images with matches
Failed to create any sparse model
```

通常说明图片之间没有足够匹配关系。

可能原因：

- 图片数量太少
- 图片不是同一场景
- 相邻图片重叠率太低
- 场景纹理太弱
- 图片过于模糊
- 拍摄视角跳跃太大
- 模糊阈值太高，导致关键图片被过滤

建议：

- 准备 20 张以上图片
- 保证相邻图片有 60% 以上重叠
- 拍摄纹理丰富的物体或场景
- 降低 `--blur-threshold`，例如使用 30 或 50
- 避免纯白墙、纯色桌面等弱纹理区域

---

### 11.2 `colmap` 不是内部或外部命令

说明 COLMAP 没有加入系统环境变量。

解决方法：

- 确认已经安装 COLMAP
- 将 COLMAP 可执行文件所在目录加入系统 PATH
- 重新打开终端后再运行

---

### 11.3 旧的 COLMAP 结果影响新结果

`run_colmap.bat` 会在运行前自动清理旧的：

```text
output/colmap_workspace/
```

避免旧的 `database.db`、旧的匹配结果或旧模型污染当前实验。

---

## 12. 标准 3DGS scene 目录

导出的标准 3DGS scene 目录结构为：

```text
gaussian_splatting_scene/
├── images/
│   ├── 000001.jpg
│   ├── 000002.jpg
│   └── ...
└── sparse/
    └── 0/
        ├── cameras.bin
        ├── images.bin
        └── points3D.bin
```

该结构可作为后续 3D Gaussian Splatting 训练前的数据基础。

如果使用官方 3DGS 仓库，后续训练命令通常类似：

```bash
python train.py -s path/to/gaussian_splatting_scene
```

不同 3DGS 项目的具体命令可能略有区别，请根据对应项目 README 调整。

---

## 13. 推荐数据采集方式

为了获得更稳定的 COLMAP / 3DGS 结果，建议：

- 图片数量不少于 20 张
- 相邻图片保持较高重叠率
- 围绕目标场景缓慢移动拍摄
- 避免大幅跳跃视角
- 避免大面积纯色或弱纹理区域
- 保持图片清晰
- 避免强反光、运动模糊和曝光剧烈变化
- 尽量使用相同焦距和相机设置

---

## 14. 当前项目定位

本项目当前定位为：

```text
三维重建图像数据集质量检查、COLMAP 稀疏重建辅助与 3DGS 数据准备工具
```

适合用于：

- 三维重建实验前的数据预处理
- COLMAP 重建前的数据质量检查
- COLMAP 重建结果分析
- 3D Gaussian Splatting 数据准备
- 三维重建实验报告生成

---

## 15. 后续计划

后续可继续扩展：

- 自动运行 COLMAP
- 生成 3DGS 训练脚本
- 解析 3DGS 训练日志
- 统计训练时间、显存占用和渲染指标
- 支持 PSNR / SSIM / LPIPS 指标整理
- 支持多组实验对比
- 支持将结果导出为更完整的实验报告
- 支持更多三维重建数据格式

---

## 16. Git 忽略建议

建议 `.gitignore` 中忽略：

```text
__pycache__/
*.pyc

.venv/
venv/
.env

dataset/
output/
```

其中：

- `dataset/` 通常包含原始图片，可能较大，不建议上传
- `output/` 是程序输出结果，可以本地生成，不建议上传
- `docs/` 可以上传，用于展示示例图片和报告

---

## 17. License

This project is for research and learning purposes.