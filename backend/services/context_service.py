from pathlib import Path
from typing import Dict

from backend.models import Job
from backend.utils.path_utils import resolve_project_path


def read_text_smart(path: Path, max_chars: int = 8000) -> str:
    """
    智能读取文本文件。

    如果文件较短：完整读取。
    如果文件较长：保留开头和结尾，中间截断。

    这样做的原因：
    - 报告开头通常有总体信息；
    - 日志结尾通常有错误或最终结果；
    - 避免把超长文件全部塞给 LLM，浪费 token。
    """
    if not path.exists() or not path.is_file():
        return ""

    content = path.read_text(encoding="utf-8", errors="ignore")

    if len(content) <= max_chars:
        return content

    head_chars = max_chars // 4
    tail_chars = max_chars - head_chars

    return (
        content[:head_chars]
        + "\n\n[中间内容过长，已截断]\n\n"
        + content[-tail_chars:]
    )


"""
收集某个任务的文本上下文，供 LLM Agent 使用。

注意：
- reconstruction_report.md 和 readiness_report 是总结报告，给较大上下文；
- backend_job.log 和 backend_after_colmap.log 可能很长，所以限制更严格；
- 真正的核心判断仍然应该依赖 diagnose_job() 生成的结构化 evidence。
"""
def collect_job_text_context(job: Job, include_logs: bool = False) -> Dict[str, str]:
    output_path = resolve_project_path(job.output_path)

    reconstruction_report = output_path / "reconstruction_report.md"
    readiness_report = output_path / "training_data_readiness_report.md"
    backend_job_log = output_path / "backend_job.log"
    after_colmap_log = output_path / "backend_after_colmap.log"

    context = {
        "reconstruction_report": read_text_smart(
            reconstruction_report,
            max_chars=12000
        ),
        "readiness_report": read_text_smart(
            readiness_report,
            max_chars=8000
        ),
    }

    if include_logs:
        context["backend_job_log"] = read_text_smart(
            backend_job_log,
            max_chars=6000
        )
        context["after_colmap_log"] = read_text_smart(
            after_colmap_log,
            max_chars=6000
        )

    return context

def get_context_preview(job: Job, preview_chars: int = 500, include_logs: bool = True):
    output_path = resolve_project_path(job.output_path)

    context = collect_job_text_context(job, include_logs=include_logs)

    result = []

    for name, content in context.items():
        if content:
            preview = content[:preview_chars]
            exists = True
            char_count = len(content)
        else:
            preview = ""
            exists = False
            char_count = 0

        result.append({
            "name": name,
            "exists": exists,
            "char_count": char_count,
            "preview": preview
        })

    return result