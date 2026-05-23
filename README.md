# 3D Reconstruction Image Dataset Inspector

面向三维重建任务的图像数据集质量检查工具，支持图片有效性检测、格式统计、分辨率统计、模糊图片检测、CSV 明细导出、Markdown 总结报告生成和分辨率分布图绘制。

## 功能

- 检查文件夹中的有效图片
- 统计 jpg / png / jpeg / 其他图片数量
- 统计最大、最小、平均分辨率
- 使用 Laplacian 方差检测疑似模糊图片
- 将疑似模糊图片复制到单独文件夹
- 导出 `image_infos.csv`
- 生成 `summary.md`
- 生成 `resolution_distribution.png`

## 项目结构

```text
.
├── image_dataset_checker.py
├── blur_detector.py
├── requirements.txt
├── README.md
├── dataset/
│   └── images/
└── output/
    ├── image_infos.csv
    ├── summary.md
    ├── resolution_distribution.png
    └── blurry_images/

```

## 安装依赖

pip install -r requirements.txt

## 使用方法

python image_dataset_checker.py --input dataset/images --output output --blur-threshold 100

### 参数说明

--input             输入图片文件夹路径
--output            输出结果文件夹路径，默认 output
--blur-threshold    模糊检测阈值，默认 100