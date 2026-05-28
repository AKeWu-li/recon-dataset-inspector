# Recon Dataset Inspector Backend

面向三维重建任务的数据处理与智能诊断后端系统。

本项目最初用于三维重建图像数据集质量检查，后续逐步扩展为一个基于 **FastAPI** 的后端服务，支持通过 REST API 创建数据处理任务，自动执行图像质量检测、数据清洗、COLMAP 辅助流程、重建结果解析、3DGS scene 导出，并结合 **LLM Agent** 对重建结果进行智能诊断。

---

## 1. 项目定位

本项目定位为：

```text
面向三维重建与 3DGS 实验的数据处理、任务管理与智能诊断后端系统
```

核心目标：

* 将原始图像数据集自动清洗成适合三维重建实验的数据
* 管理长耗时数据处理任务
* 解析 COLMAP 稀疏重建结果
* 生成重建质量报告和数据准备报告
* 导出标准 3D Gaussian Splatting scene 目录
* 通过 LLM Agent 自动分析重建质量并给出下一步建议
* 体现 Python 后端开发中的 API 设计、数据库、异步任务、文件管理和 AI Agent 集成能力

---

## 2. 技术栈

### 后端与工程

```text
Python
FastAPI
Pydantic
SQLAlchemy
SQLite
Uvicorn
BackgroundTasks
Celery
Redis
```

### 图像处理与三维重建辅助

```text
Pillow
OpenCV
NumPy
Matplotlib
COLMAP
3D Gaussian Splatting scene export
```

### AI Agent

```text
DeepSeek API / OpenAI-compatible API
LLM Agent
规则诊断
报告上下文增强
对话历史持久化
失败降级机制
```

### 可选工程化组件

```text
Docker / Docker Compose
Redis / Celery Worker
.env environment configuration
```

说明：当前项目默认使用 `BackgroundTasks` 运行后台任务；已预留 `Celery + Redis` 任务队列模式，可通过环境变量切换。Docker / Redis 部署可根据本地环境后续启用。

---

## 3. 核心功能

### 3.1 数据集检查与清洗

支持：

* 检查图片文件是否合法
* 统计图片格式、分辨率和像素数量
* 使用 Laplacian 方差检测疑似模糊图片
* 将清晰图片复制到 `clean_images/`
* 将疑似模糊图片复制到 `blurry_images/`
* 生成图片信息 CSV
* 生成 clean image 文件名映射表
* 绘制分辨率分布图

输出示例：

```text
output/job_001/
├── clean_images/
├── blurry_images/
├── image_infos.csv
├── clean_images_mapping.csv
├── resolution_distribution.png
└── run_colmap.bat
```

---

### 3.2 COLMAP 辅助流程

第一阶段会自动生成：

```text
run_colmap.bat
```

用户运行该脚本后，会生成 COLMAP 工作目录：

```text
output/job_001/colmap_workspace/
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
├── model_report.txt
└── camera_trajectory.png
```

---

### 3.3 重建结果解析与报告生成

系统可以解析 COLMAP 导出的 TXT 模型，并生成：

```text
reconstruction_report.md
training_data_readiness_report.md
```

报告内容包括：

* 有效图片数量
* 模糊图片数量
* clean images 数量
* COLMAP 注册图片数量
* 注册图片比例
* 稀疏 3D 点数量
* 关键文件完整性
* 相机轨迹可视化
* 重建质量评分
* 后续建议

---

### 3.4 3D Gaussian Splatting scene 导出

支持导出标准 3DGS scene 目录：

```text
gaussian_splatting_scene/
├── images/
└── sparse/
    └── 0/
        ├── cameras.bin
        ├── images.bin
        └── points3D.bin
```

该目录可作为后续 3D Gaussian Splatting 训练输入。

---

### 3.5 后端任务管理

通过 FastAPI 提供任务创建、状态查询、日志查看、报告查看和文件下载接口。

支持任务状态：

```text
pending
running
success
failed
after_colmap_pending
after_colmap_running
after_colmap_success
after_colmap_failed
queued
queue_failed
```

任务信息保存在 SQLite 数据库中。

---

### 3.6 LLM Agent 智能诊断

Agent 支持：

* 读取任务状态
* 读取结构化 evidence
* 读取 reconstruction report
* 读取 readiness report
* 可选读取日志上下文
* 使用规则诊断生成基础判断
* 调用 DeepSeek / OpenAI-compatible LLM 生成自然语言回答
* LLM 调用失败时自动降级为规则回答
* 保存 Agent 问答历史
* 查询 LLM 当前配置状态
* 查询实际传给 LLM 的上下文预览

示例问题：

```text
这次重建结果怎么样？
这次结果有没有潜在风险？
为什么这个任务没有生成报告？
下一步我该做什么？
这个数据集适合继续做 3DGS 吗？
```

示例回答来源：

```json
{
  "answer_source": "llm:deepseek"
}
```

如果 LLM 不可用：

```json
{
  "answer_source": "rule_based_fallback:deepseek"
}
```

---

## 4. 项目结构

```text
recon-dataset-inspector/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── celery_app.py
│   ├── tasks.py
│   ├── routers/
│   │   ├── jobs.py
│   │   └── agent.py
│   ├── services/
│   │   ├── pipeline_service.py
│   │   ├── diagnosis_service.py
│   │   ├── context_service.py
│   │   └── llm_service.py
│   └── utils/
│       └── path_utils.py
├── image_dataset_checker.py
├── blur_detector.py
├── colmap_report_parser.py
├── reconstruction_readiness_checker.py
├── gaussian_scene_exporter.py
├── run_pipeline.py
├── requirements.txt
├── .env.example
├── README.md
├── dataset/
│   └── images/
├── output/
└── docs/
```

---

## 5. 环境准备

建议使用 Python 3.9 或以上版本。

安装依赖：

```bash
pip install -r requirements.txt
```

`requirements.txt` 示例：

```text
fastapi
uvicorn
sqlalchemy
pydantic
Pillow
opencv-python
matplotlib
numpy
openai
celery
redis
```

如果需要运行 COLMAP，请提前安装 COLMAP，并确保命令行中可以直接调用：

```bash
colmap
```

---

## 6. 环境变量配置

项目根目录可创建 `.env` 文件，也可以直接使用系统环境变量。

建议提供 `.env.example`：

```env
# Task queue mode: background or celery
TASK_QUEUE_MODE=background

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LLM provider
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_api_key_here
```

注意：

```text
不要把真实 .env 文件提交到 GitHub
不要把真实 LLM_API_KEY 写进 README 或代码
```

建议 `.gitignore` 中加入：

```text
.env
recon_jobs.db
dataset/
output/
__pycache__/
*.pyc
```

---

## 7. 启动后端服务

默认使用 BackgroundTasks，不依赖 Redis。

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

访问健康检查接口：

```text
http://127.0.0.1:8000/health
```

访问 API 文档：

```text
http://127.0.0.1:8000/docs
```

---

## 8. 任务运行流程

### 8.1 创建数据处理任务

接口：

```text
POST /api/v1/jobs/
```

请求示例：

```json
{
  "input_path": "dataset/images",
  "output_path": "output/job_001",
  "blur_threshold": 50,
  "auto_run": true
}
```

说明：

* `input_path`：原始图片目录
* `output_path`：任务输出目录
* `blur_threshold`：Laplacian 模糊检测阈值
* `auto_run`：

  * `true`：创建任务后自动执行第一阶段 pipeline
  * `false`：只注册已有 output 目录，不重新运行 pipeline

---

### 8.2 查询任务状态

```text
GET /api/v1/jobs/{job_id}
```

返回示例：

```json
{
  "id": 3,
  "input_path": "dataset/images",
  "output_path": "output/job_001",
  "blur_threshold": 50,
  "status": "success",
  "message": "Job finished successfully.",
  "celery_task_id": null,
  "created_at": "2026-05-27T20:00:00",
  "updated_at": "2026-05-27T20:05:00"
}
```

---

### 8.3 运行 COLMAP

第一阶段完成后，手动运行该任务目录下生成的脚本：

```bash
output/job_001/run_colmap.bat
```

成功后会生成：

```text
output/job_001/colmap_workspace/
```

---

### 8.4 触发 after-colmap 后处理

COLMAP 运行完成后，调用：

```text
POST /api/v1/jobs/{job_id}/after-colmap
```

该阶段会执行：

```bash
python run_pipeline.py --output output/job_001 --after-colmap
```

并生成：

```text
reconstruction_report.md
training_data_readiness_report.md
gaussian_splatting_scene/
```

---

## 9. API 列表

### 9.1 Job API

```text
GET  /health
POST /api/v1/jobs/
GET  /api/v1/jobs/
GET  /api/v1/jobs/{job_id}
GET  /api/v1/jobs/{job_id}/outputs
GET  /api/v1/jobs/{job_id}/log
GET  /api/v1/jobs/{job_id}/report
POST /api/v1/jobs/{job_id}/after-colmap
GET  /api/v1/jobs/{job_id}/download/{file_path}
```

功能说明：

| API                                              | 功能            |
| ------------------------------------------------ | ------------- |
| `POST /api/v1/jobs/`                             | 创建数据处理任务      |
| `GET /api/v1/jobs/`                              | 查询任务列表        |
| `GET /api/v1/jobs/{job_id}`                      | 查询单个任务状态      |
| `GET /api/v1/jobs/{job_id}/outputs`              | 查看任务输出文件      |
| `GET /api/v1/jobs/{job_id}/log`                  | 查看任务运行日志      |
| `GET /api/v1/jobs/{job_id}/report`               | 查看重建报告        |
| `POST /api/v1/jobs/{job_id}/after-colmap`        | 触发 COLMAP 后处理 |
| `GET /api/v1/jobs/{job_id}/download/{file_path}` | 下载任务输出文件      |

---

### 9.2 Agent API

```text
POST /api/v1/agent/diagnose
POST /api/v1/agent/chat
GET  /api/v1/agent/jobs/{job_id}/conversations
GET  /api/v1/agent/llm-status
GET  /api/v1/agent/jobs/{job_id}/context-preview
```

功能说明：

| API                                               | 功能                 |
| ------------------------------------------------- | ------------------ |
| `POST /api/v1/agent/diagnose`                     | 返回结构化诊断结果          |
| `POST /api/v1/agent/chat`                         | 与 LLM Agent 对话     |
| `GET /api/v1/agent/jobs/{job_id}/conversations`   | 查询某个任务的 Agent 对话历史 |
| `GET /api/v1/agent/llm-status`                    | 查询当前 LLM 配置状态      |
| `GET /api/v1/agent/jobs/{job_id}/context-preview` | 查看传给 LLM 的上下文预览    |

---

## 10. Agent 使用示例

### 10.1 结构化诊断

接口：

```text
POST /api/v1/agent/diagnose
```

请求：

```json
{
  "job_id": 3
}
```

返回示例：

```json
{
  "job_id": 3,
  "job_status": "success",
  "quality": "较好",
  "main_problems": [
    "未发现明显问题。"
  ],
  "suggestions": [
    "当前任务结果较完整，可以继续进行 3DGS scene 导出或后续训练准备。"
  ],
  "next_actions": [
    "GET /api/v1/jobs/3/report"
  ],
  "evidence": {
    "valid_image_count": 318,
    "blurry_image_count": 0,
    "quality_score": 100,
    "registered_ratio": 100
  }
}
```

---

### 10.2 LLM Agent 对话

接口：

```text
POST /api/v1/agent/chat
```

请求：

```json
{
  "job_id": 3,
  "question": "这次重建结果怎么样？",
  "use_context": true,
  "include_logs": false
}
```

返回示例：

```json
{
  "job_id": 3,
  "question": "这次重建结果怎么样？",
  "answer": "根据系统提供的诊断结果和报告，这次重建任务结果较好...",
  "answer_source": "llm:deepseek",
  "context_used": true,
  "logs_included": false,
  "evidence": {
    "valid_image_count": 318,
    "blurry_image_count": 0,
    "quality_score": 100,
    "registered_ratio": 100
  }
}
```

参数说明：

| 参数              | 说明                                                      |
| --------------- | ------------------------------------------------------- |
| `use_context`   | 是否将报告内容加入 LLM 上下文                                       |
| `include_logs`  | 是否将日志内容加入 LLM 上下文                                       |
| `answer_source` | 回答来源，例如 `llm:deepseek` 或 `rule_based_fallback:deepseek` |

---

## 11. LLM 配置

当前项目支持 OpenAI-compatible API，因此可以使用 DeepSeek 等模型服务。

示例环境变量：

```env
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_api_key_here
```

检查当前 LLM 配置：

```text
GET /api/v1/agent/llm-status
```

返回示例：

```json
{
  "provider": "deepseek",
  "model": "deepseek-v4-flash",
  "base_url": "https://api.deepseek.com",
  "api_key_configured": true
}
```

如果 LLM 调用失败，系统会自动返回规则诊断结果，不会导致接口整体失败。

---

## 12. 任务队列模式

当前支持两种任务执行方式。

### 12.1 BackgroundTasks 模式

默认模式：

```env
TASK_QUEUE_MODE=background
```

特点：

* 不依赖 Redis
* 适合本地开发和演示
* FastAPI 进程内后台执行任务

启动：

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

---

### 12.2 Celery + Redis 模式

可选模式：

```env
TASK_QUEUE_MODE=celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

启动 Celery Worker：

```bash
celery -A backend.celery_app:celery_app worker --loglevel=info --pool=solo
```

说明：

* Windows 本地开发建议使用 `--pool=solo`
* 该模式需要本地或远程 Redis 服务
* 如果未启动 Redis，Celery Worker 会连接失败
* Docker Compose 部署 Redis 可在支持 Docker 的环境中启用

架构：

```text
FastAPI API
    ↓
Redis Broker
    ↓
Celery Worker
    ↓
Pipeline Service
    ↓
SQLite 状态更新
```

---

## 13. 文件下载接口安全设计

文件下载接口：

```text
GET /api/v1/jobs/{job_id}/download/{file_path}
```

后端会将任务输出目录解析为绝对路径，并使用路径校验防止路径穿越。

例如禁止访问：

```text
../../backend/database.py
```

只允许下载当前任务输出目录下的文件。

---

## 14. 当前系统架构

```text
用户 / Swagger / 前端
        ↓
FastAPI REST API
        ↓
Job Router / Agent Router
        ↓
Service Layer
├── Pipeline Service
│   ├── image_dataset_checker.py
│   ├── run_pipeline.py
│   ├── colmap_report_parser.py
│   ├── reconstruction_readiness_checker.py
│   └── gaussian_scene_exporter.py
│
├── Diagnosis Service
│   └── 规则诊断 / evidence 提取
│
├── Context Service
│   └── 读取报告 / 日志上下文
│
└── LLM Service
    └── DeepSeek / OpenAI-compatible API

        ↓
SQLite
├── jobs
└── agent_conversations
```

可选异步任务架构：

```text
FastAPI
  ↓
Redis
  ↓
Celery Worker
  ↓
Pipeline Service
```

---

## 15. 典型使用流程

### 方式一：完整新任务流程

```text
1. POST /api/v1/jobs/
2. 等待任务状态变为 success
3. 运行 output/job_001/run_colmap.bat
4. POST /api/v1/jobs/{job_id}/after-colmap
5. GET /api/v1/jobs/{job_id}/report
6. POST /api/v1/agent/chat
```

---

### 方式二：注册已有 output 目录

如果已经存在：

```text
output/job_001/
```

并且不想重新运行 pipeline，可以创建任务时传：

```json
{
  "input_path": "dataset/images",
  "output_path": "output/job_001",
  "blur_threshold": 50,
  "auto_run": false
}
```

这样系统只会注册已有目录，不会覆盖旧结果。

---

## 16. 常见问题

### 16.1 Docker 无法使用怎么办？

Docker 不是必须的。

项目默认使用：

```env
TASK_QUEUE_MODE=background
```

该模式不依赖 Docker 或 Redis。

如果系统支持 Docker，可以后续使用 Docker Compose 启动 Redis，并切换到 Celery 模式。

---

### 16.2 Celery Worker 连接 Redis 失败

如果看到：

```text
Cannot connect to redis://localhost:6379/0
```

说明 Redis 没有启动，或者 6379 端口没有服务监听。

可以检查：

```powershell
Test-NetConnection localhost -Port 6379
```

如果返回 `False`，说明 Redis 不可用。

---

### 16.3 ChatGPT Plus 是否包含 API 额度？

不包含。

LLM API 调用需要单独配置对应平台的 API Key 和额度。当前项目支持 DeepSeek 等 OpenAI-compatible API。

---

### 16.4 为什么 Agent 有时会返回规则诊断？

如果 LLM API 不可用、额度不足、网络错误或 API Key 未配置，系统会自动降级到规则诊断结果。

这属于设计内的 fallback 机制。

---

## 17. 当前项目亮点

* 基于 FastAPI 实现三维重建任务后端服务
* 使用 SQLAlchemy + SQLite 管理任务状态和 Agent 对话历史
* 支持后台执行长耗时图像处理 pipeline
* 支持 Celery + Redis 可选任务队列架构
* 封装图像质量检测、COLMAP 后处理和 3DGS scene 导出流程
* 集成 DeepSeek LLM Agent，根据重建报告和结构化 evidence 生成诊断建议
* 支持 LLM 调用失败降级，提升系统鲁棒性
* 支持日志查询、报告查询、文件下载和上下文预览
* 支持注册已有 output 目录，便于实验结果复用

---

## 18. 后续计划

后续可以继续扩展：

* 完整跑通 Celery + Redis 生产式任务队列
* Docker Compose 管理 API、Worker、Redis
* 增加前端任务管理页面
* 支持 WebSocket 实时推送任务日志
* 接入向量数据库，实现报告和日志 RAG 检索
* 支持多数据集批处理
* 支持 3DGS 训练日志解析
* 支持 PSNR / SSIM / LPIPS 指标统计
* 支持 PostgreSQL 替换 SQLite
* 使用 Alembic 管理数据库迁移

---


## 19. License

This project is for research, learning, and portfolio demonstration purposes.
