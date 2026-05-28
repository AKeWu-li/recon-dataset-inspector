from typing import Dict, Any

from backend.tools.common import (
    tool_db_session,
    get_job_or_error,
    serialize_job
)


def get_job_status_tool(job_id: int) -> Dict[str, Any]:
    """
    只读工具：查询任务基础状态。
    可被 FastAPI / LangGraph / MCP Server 复用。
    """
    with tool_db_session() as db:
        job, error = get_job_or_error(db, job_id)

        if error:
            return error

        return serialize_job(job)