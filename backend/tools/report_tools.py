from typing import Dict, Any

from backend.tools.common import tool_db_session, get_job_or_error
from backend.services.retrieval_service import search_job_reports
from backend.services.context_service import get_context_preview


def search_report_sections_tool(
    job_id: int,
    question: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    只读工具：根据用户问题检索任务报告中的相关片段。
    """
    with tool_db_session() as db:
        job, error = get_job_or_error(db, job_id)

        if error:
            return error

        sections = search_job_reports(
            job=job,
            question=question,
            top_k=top_k
        )

        return {
            "job_id": job.id,
            "question": question,
            "top_k": top_k,
            "sections": sections
        }


def get_context_preview_tool(job_id: int) -> Dict[str, Any]:
    """
    只读工具：查看 Agent 可用的上下文预览。
    """
    with tool_db_session() as db:
        job, error = get_job_or_error(db, job_id)

        if error:
            return error

        files = get_context_preview(job)

        return {
            "job_id": job.id,
            "files": files
        }