# Recon Dataset Inspector Backend

面向三维重建任务的数据处理、任务管理与智能诊断后端系统。

本项目最初用于三维重建图像数据集质量检查，后续扩展为一个基于 **FastAPI** 的后端系统。系统支持通过 REST API 管理三维重建数据处理任务，自动执行图像质量检测、数据清洗、COLMAP 结果解析、3D Gaussian Splatting scene 导出，并结合 **Report Retrieval + LangGraph + LLM Agent + MCP Server** 对重建结果进行智能诊断和工具化访问。

---

## 1. 项目简介

本项目面向三维重建与 3D Gaussian Splatting 实验场景，主要解决以下问题：

* 原始图片数据集质量参差不齐，缺少自动化检查工具
* COLMAP 重建结果需要人工查看和分析，流程繁琐
* 3DGS 训练前需要整理标准 scene 目录结构
* 长耗时任务需要统一管理状态、日志和输出文件
* 重建质量判断依赖经验，缺少自动诊断和自然语言解释
* Agent 调用后端能力时需要稳定、可复用的工具层
* 外部 Agent 需要通过标准协议访问后端工具能力

本项目将原本分散的脚本流程封装为后端服务，并进一步引入认证、数据库迁移、自动化测试、Agent 工作流、Tool Layer 和 MCP Server，使其更接近一个完整的 Python 后端工程项目。

---

## 2. 核心功能

### 2.1 数据集检查与清洗

系统可以对原始图片目录进行检查，包括：

* 判断文件是否为有效图片
* 统计图片格式、分辨率和像素数量
* 使用 Laplacian 方差检测疑似模糊图片
* 将清晰图片复制到 `clean_images/`
* 将疑似模糊图片复制到 `blurry_images/`
* 生成图片信息表 `image_infos.csv`
* 生成清洗后图片映射表 `clean_images_mapping.csv`
* 生成分辨率分布图 `resolution_distribution.png`

示例输出结构：

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

### 2.2 COLMAP 辅助流程

第一阶段 pipeline 会生成 COLMAP 执行脚本：

```text
run_colmap.bat
```

用户运行该脚本后，系统会得到 COLMAP 工作目录：

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

### 2.3 COLMAP 结果解析与报告生成

系统可以解析 COLMAP 导出的 TXT 模型文件，并生成：

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
* 关键文件完整性检查
* 相机轨迹可视化
* 重建质量评分
* 数据准备状态
* 后续建议

---

### 2.4 3D Gaussian Splatting scene 导出

系统支持导出标准 3DGS scene 目录：

```text
gaussian_splatting_scene/
├── images/
└── sparse/
    └── 0/
        ├── cameras.bin
        ├── images.bin
        └── points3D.bin
```

该目录可以作为后续 3D Gaussian Splatting 训练输入。

---

### 2.5 任务管理

系统通过 FastAPI 提供任务管理能力，包括：

* 创建任务
* 查询任务列表
* 查询任务状态
* 查看任务输出文件
* 查看任务运行日志
* 查看重建报告
* 下载任务输出文件
* 触发 after-colmap 后处理
* 注册已有 output 目录而不重新运行 pipeline

常见任务状态：

```text
pending
running
success
failed
registered
after_colmap_pending
after_colmap_running
after_colmap_success
after_colmap_failed
queued
queue_failed
```

---

### 2.6 用户认证

系统支持基于 OAuth2 Password Flow 和 JWT 的用户认证。

认证接口：

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

受保护接口需要携带：

```text
Authorization: Bearer <access_token>
```

认证相关技术：

```text
OAuth2 Password Flow
JWT
python-jose
passlib
bcrypt
```

---

### 2.7 智能诊断 Agent

Agent 可以回答类似问题：

```text
这次重建结果怎么样？
这次重建有没有潜在风险？
为什么任务没有生成报告？
这个任务有没有报错？
下一步我应该做什么？
这个数据集适合继续做 3DGS 吗？
```

Agent 结合以下信息进行回答：

```text
规则诊断结果
结构化 evidence
Report Retrieval 检索到的报告片段
可选日志上下文
LangGraph 条件分支工作流
LLM 生成结果
LLM 失败降级结果
Agent 对话历史
```

如果 LLM 调用成功：

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

## 3. 技术栈

### 后端

```text
Python 3.10
FastAPI
Pydantic
SQLAlchemy
SQLite
Alembic
Uvicorn
pytest
GitHub Actions
```

### 认证

```text
OAuth2 Password Flow
JWT
python-jose
passlib
bcrypt
```

### 任务系统

```text
FastAPI BackgroundTasks
Celery-ready architecture
Redis-ready configuration
```

当前默认使用 `BackgroundTasks` 模式，本地运行不依赖 Redis。
项目已预留 `Celery + Redis` 任务队列模式，可通过环境变量切换。

### 图像处理与三维重建辅助

```text
Pillow
OpenCV
NumPy
Matplotlib
COLMAP
3D Gaussian Splatting scene export
```

### Agent 相关

```text
DeepSeek API / OpenAI-compatible API
Report Retrieval
LangGraph
Tool Layer
MCP Server
Rule-based fallback
Conversation persistence
```

### MCP

```text
MCP Python SDK
FastMCP
MCP tools
MCP Server wrapper
```

当前项目已统一使用 Python 3.10 环境，因此主后端、测试、LangGraph 和 MCP Server 可以在同一套环境中运行。

---

## 4. 系统架构

整体架构：

```text
用户 / Swagger / 未来前端 / 外部 Agent
        ↓
FastAPI / MCP Server
        ↓
Auth Router / Job Router / Agent Router / MCP Tools
        ↓
Service Layer
├── Pipeline Service
├── Diagnosis Service
├── Retrieval Service
├── Context Service
├── LLM Service
└── LangGraph Agent Graph
        ↓
Tool Layer
├── Job Tools
├── Report Tools
└── Agent Tools

Database:
SQLite + SQLAlchemy + Alembic
```

Agent 工作流：

```text
用户问题
  ↓
规则诊断
  ↓
上下文路由判断
  ↓
报告检索 / 跳过上下文
  ↓
可选日志上下文
  ↓
LLM 回答 / 规则降级
  ↓
保存对话历史
```

MCP 工具调用链路：

```text
外部 MCP Client / Agent
        ↓
MCP Server
        ↓
Tool Layer
        ↓
任务状态 / 报告检索 / LangGraph Debug / 数据库
```

---

## 5. LangGraph Agent 工作流

本项目使用 LangGraph 将 Agent 流程拆分为多个节点。

```text
StateGraph
├── diagnose_node
├── route_context_node
├── build_rule_answer_node
├── retrieve_report_node
├── no_context_node
├── add_logs_node
└── llm_answer_node
```

工作流会根据用户问题和任务状态自动判断：

* 是否需要检索报告
* 是否需要读取日志
* 是否只用结构化 evidence 即可回答
* LLM 失败时是否使用规则诊断降级

例如：

```text
用户问“这次重建有没有风险？”
→ 检索报告中的风险提示和质量诊断部分

用户问“这个任务有没有报错？”
→ 自动加入日志上下文

用户问“当前任务状态是什么？”
→ 可以只使用结构化 evidence，不读取完整报告
```

---

## 6. Report Retrieval

系统没有简单地把完整报告全部塞给 LLM，而是实现了轻量级 Report Retrieval。

流程：

```text
reconstruction_report.md
training_data_readiness_report.md
        ↓
按 Markdown section 切分
        ↓
关键词 / 领域词打分
        ↓
返回 top-k 相关片段
        ↓
构造 LLM 上下文
```

这样可以：

* 降低 token 消耗
* 减少无关上下文干扰
* 提高回答和问题的相关性
* 保留可解释的检索结果

检索预览接口：

```text
GET /api/v1/agent/jobs/{job_id}/retrieval-preview
```

示例返回：

```json
{
  "job_id": 3,
  "question": "这次重建有没有风险？",
  "sections": [
    {
      "source": "readiness_report",
      "title": "5. 风险提示",
      "score": 16.0,
      "content": "未发现明显风险。"
    }
  ]
}
```

---

## 7. Tool Layer

项目将可复用能力抽象为 Tool Layer：

```text
backend/tools/
├── common.py
├── job_tools.py
├── report_tools.py
└── agent_tools.py
```

目前包含：

```text
get_job_status_tool
diagnose_job_tool
search_report_sections_tool
get_context_preview_tool
run_agent_graph_debug_tool
```

这些工具不依赖 FastAPI Router，可以被多个模块复用：

```text
FastAPI APIs
LangGraph nodes
MCP Server
pytest tests
未来外部 Agent
```

这样可以避免把业务逻辑写死在接口层，也方便后续扩展 MCP Server 或其他 Agent 接入方式。

---

## 8. MCP Server

项目提供了基于 Tool Layer 的 MCP Server。

文件：

```text
backend/mcp_server.py
```

当前暴露的只读 MCP tools：

```text
get_job_status
diagnose_job
search_report_sections
get_context_preview
run_agent_graph_debug
```

为了安全，当前 MCP Server 不暴露以下危险能力：

```text
run_command
delete_file
run_pipeline
run_colmap
download_arbitrary_file
```

MCP Server 可以直接启动：

```bash
python -m backend.mcp_server
```

如果需要使用 MCP Inspector：

```bash
mcp dev backend/mcp_server.py
```

注意：MCP Inspector 依赖 Node.js 环境。如果本地 Node.js 版本较旧，可能需要升级 Node.js 后再使用 `mcp dev`。

---

## 9. 项目结构

```text
recon-dataset-inspector/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   ├── celery_app.py
│   ├── tasks.py
│   ├── mcp_server.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── jobs.py
│   │   └── agent.py
│   ├── services/
│   │   ├── pipeline_service.py
│   │   ├── diagnosis_service.py
│   │   ├── context_service.py
│   │   ├── retrieval_service.py
│   │   ├── llm_service.py
│   │   └── agent_graph.py
│   ├── tools/
│   │   ├── common.py
│   │   ├── job_tools.py
│   │   ├── report_tools.py
│   │   └── agent_tools.py
│   └── utils/
│       └── path_utils.py
├── alembic/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_jobs.py
│   └── test_agent.py
├── .github/
│   └── workflows/
│       └── tests.yml
├── image_dataset_checker.py
├── blur_detector.py
├── colmap_report_parser.py
├── reconstruction_readiness_checker.py
├── gaussian_scene_exporter.py
├── run_pipeline.py
├── requirements.txt
├── alembic.ini
├── pytest.ini
├── .env.example
├── README.md
├── docs/
├── dataset/
└── output/
```

---

## 10. 环境准备

推荐使用 Python 3.10。

创建环境：

```bash
conda create -n recon310 python=3.10 -y
conda activate recon310
```

安装依赖：

```bash
pip install -r requirements.txt
```

如果需要运行 COLMAP，请提前安装 COLMAP，并确保命令行可以调用：

```bash
colmap
```

---

## 11. 环境变量

可以创建 `.env` 文件，也可以使用系统环境变量。

示例 `.env.example`：

```env
# Database
DATABASE_URL=sqlite:///./recon_jobs.db

# Task queue mode: background or celery
TASK_QUEUE_MODE=background

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# JWT
JWT_SECRET_KEY=change_me_to_a_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM provider
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_api_key_here
```

不要提交真实 API Key。

推荐 `.gitignore`：

```text
.env
recon_jobs.db
test_recon_jobs.db
dataset/
output/*
!output/.gitkeep
__pycache__/
*.pyc
.pytest_cache/
```

---

## 12. 数据库迁移

本项目使用 Alembic 管理数据库迁移。

生成迁移文件：

```bash
alembic revision --autogenerate -m "migration message"
```

执行迁移：

```bash
alembic upgrade head
```

典型用途：

* 新增 users 表
* 新增任务字段
* 新增 Agent 对话字段
* 后续切换 PostgreSQL 时管理 schema

---

## 13. 启动后端

启动 FastAPI：

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

健康检查：

```text
http://127.0.0.1:8000/health
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

---

## 14. 启动 MCP Server

启动 MCP Server：

```bash
python -m backend.mcp_server
```

如果需要使用 MCP Inspector：

```bash
mcp dev backend/mcp_server.py
```

如果 `mcp dev` 报 Node.js 版本相关错误，请升级 Node.js 后再试。

---

## 15. 认证流程

### 注册用户

```text
POST /api/v1/auth/register
```

请求：

```json
{
  "username": "admin",
  "password": "test123456"
}
```

返回：

```json
{
  "id": 1,
  "username": "admin",
  "is_active": true,
  "created_at": "2026-05-28T18:21:48"
}
```

### 登录

```text
POST /api/v1/auth/login
```

该接口使用表单数据：

```text
username=admin
password=test123456
```

返回：

```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

在 Swagger 右上角点击 `Authorize`，填入：

```text
Bearer jwt_token_here
```

---

## 16. 任务流程

### 16.1 创建任务

```text
POST /api/v1/jobs/
```

请求：

```json
{
  "input_path": "dataset/images",
  "output_path": "output/job_001",
  "blur_threshold": 50,
  "auto_run": true
}
```

字段说明：

| 字段               | 说明                  |
| ---------------- | ------------------- |
| `input_path`     | 原始图片目录              |
| `output_path`    | 输出目录                |
| `blur_threshold` | 模糊检测阈值              |
| `auto_run`       | 是否自动执行第一阶段 pipeline |

如果 `auto_run=false`，系统只会注册已有 output 目录，不会重新运行 pipeline。

---

### 16.2 查询任务状态

```text
GET /api/v1/jobs/{job_id}
```

---

### 16.3 运行 COLMAP

第一阶段完成后，运行任务目录下生成的：

```bash
output/job_001/run_colmap.bat
```

---

### 16.4 触发 after-colmap 后处理

```text
POST /api/v1/jobs/{job_id}/after-colmap
```

该阶段会生成：

```text
reconstruction_report.md
training_data_readiness_report.md
gaussian_splatting_scene/
```

---

## 17. API 列表

### Auth APIs

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

### Job APIs

```text
POST /api/v1/jobs/
GET  /api/v1/jobs/
GET  /api/v1/jobs/{job_id}
GET  /api/v1/jobs/{job_id}/outputs
GET  /api/v1/jobs/{job_id}/log
GET  /api/v1/jobs/{job_id}/report
POST /api/v1/jobs/{job_id}/after-colmap
GET  /api/v1/jobs/{job_id}/download/{file_path}
```

### Agent APIs

```text
POST /api/v1/agent/diagnose
POST /api/v1/agent/chat
POST /api/v1/agent/graph-debug
GET  /api/v1/agent/jobs/{job_id}/conversations
GET  /api/v1/agent/llm-status
GET  /api/v1/agent/jobs/{job_id}/context-preview
GET  /api/v1/agent/jobs/{job_id}/retrieval-preview
```

---

## 18. Agent 使用示例

### 18.1 Agent Chat

```text
POST /api/v1/agent/chat
```

请求：

```json
{
  "job_id": 3,
  "question": "这次重建有没有潜在风险？",
  "use_context": true,
  "include_logs": false,
  "use_retrieval": true
}
```

返回示例：

```json
{
  "job_id": 3,
  "question": "这次重建有没有潜在风险？",
  "answer": "根据系统提供的诊断结果和报告，本次重建任务没有发现潜在风险...",
  "answer_source": "llm:deepseek",
  "context_used": true,
  "logs_included": false,
  "retrieval_used": true,
  "evidence": {
    "valid_image_count": 318,
    "blurry_image_count": 0,
    "quality_score": 100,
    "registered_ratio": 100
  }
}
```

---

### 18.2 Graph Debug

```text
POST /api/v1/agent/graph-debug
```

请求：

```json
{
  "job_id": 3,
  "question": "这个任务有没有报错？请结合日志分析",
  "use_context": true,
  "include_logs": false,
  "use_retrieval": true
}
```

返回中会包含：

```json
{
  "planned_context": "retrieval",
  "auto_include_logs": true,
  "auto_use_retrieval": true,
  "context_keys": [
    "retrieved_report_sections",
    "backend_job_log",
    "after_colmap_log"
  ],
  "debug_steps": [
    "diagnose_node: job_status=success, quality=较好",
    "route_context_node: use_context=True, auto_use_retrieval=True, auto_include_logs=True, planned_context=retrieval",
    "retrieve_report_node: retrieved 5 sections",
    "add_logs_node: backend_job_log and after_colmap_log added",
    "llm_answer_node: skipped LLM call because skip_llm=True"
  ]
}
```

该接口不会调用 LLM，也不会消耗 token。

---

## 19. MCP 工具示例

当前 MCP Server 暴露以下只读工具：

```text
get_job_status(job_id)
diagnose_job(job_id)
search_report_sections(job_id, question, top_k)
get_context_preview(job_id)
run_agent_graph_debug(job_id, question, use_context, include_logs, use_retrieval)
```

示例用途：

```text
外部 Agent 可以通过 MCP 调用 get_job_status 获取任务状态
外部 Agent 可以通过 MCP 调用 search_report_sections 检索报告相关片段
外部 Agent 可以通过 MCP 调用 run_agent_graph_debug 查看 Agent 工作流路径
```

---

## 20. 任务队列模式

### 20.1 BackgroundTasks 模式

默认模式：

```env
TASK_QUEUE_MODE=background
```

特点：

* 不依赖 Redis
* 适合本地开发
* 由 FastAPI 进程执行后台任务

---

### 20.2 Celery + Redis 模式

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
* 该模式需要 Redis 服务
* 如果 Redis 未启动，Celery Worker 会连接失败
* Docker / Redis 部署可以在兼容环境中后续启用

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

## 21. 测试

本地运行测试：

```bash
python -m pytest -v
```

当前测试覆盖：

* 健康检查
* 用户注册
* 用户登录
* JWT 保护接口
* `auto_run=false` 创建任务
* 任务列表查询
* Agent LLM 状态接口

示例结果：

```text
10 passed
```

项目已配置 GitHub Actions，在 push 和 pull request 时自动运行测试。

配置文件：

```text
.github/workflows/tests.yml
```

---

## 22. output 目录说明

`output/` 是运行时产物目录，可能占用大量磁盘空间。

不建议将完整 `output/` 提交到 GitHub。

推荐策略：

```text
output/*
!output/.gitkeep
```

如果需要保留示例，可以将轻量文件复制到：

```text
docs/examples/
```

建议保留：

```text
reconstruction_report_example.md
training_data_readiness_report_example.md
camera_trajectory.png
scene_export_report_example.md
```

---

## 23. 后续计划

后续可以继续扩展：

* 用户级任务隔离
* PostgreSQL 支持
* 结构化日志
* WebSocket / SSE 实时任务日志推送
* 完整 Celery + Redis 部署
* Docker Compose 支持
* 简单 React 前端
* 向量数据库 / 更高级的报告检索
* MCP Inspector 兼容测试
* 更多 Tool Layer 和 LangGraph 测试

---

## 24. License

This project is for research, learning, and portfolio demonstration purposes.
