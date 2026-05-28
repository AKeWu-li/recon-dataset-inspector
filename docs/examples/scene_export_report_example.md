# Gaussian Splatting Scene Export Report

## 1. 导出结果

- Scene 目录：`output\job_001\gaussian_splatting_scene`
- 图片目录：`output\job_001\gaussian_splatting_scene\images`
- COLMAP sparse 目录：`output\job_001\gaussian_splatting_scene\sparse\0`
- 图片数量：318

## 2. 目录结构

```text
gaussian_splatting_scene/
├── images/
└── sparse/
    └── 0/
        ├── cameras.bin
        ├── images.bin
        └── points3D.bin
```

## 3. 后续使用

如果使用官方 3D Gaussian Splatting 项目，可以尝试：

```bash
python train.py -s output\job_001\gaussian_splatting_scene
```

注意：不同 3DGS 项目的训练命令可能略有差异，请根据对应项目 README 调整。
