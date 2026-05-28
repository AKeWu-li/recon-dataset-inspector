from typing import Dict, Any

from backend.tools.common import tool_db_session, get_job_or_error
from backend.services.diagnosis_service import diagnose_job
from backend.services.agent_graph import run_agent_graph


def diagnose_job_tool(job_id: int) -> Dict[str, Any]:
    """
    只读工具：运行规则诊断。
    """
    with tool_db_session() as db:
        job, error = get_job_or_error(db, job_id)

        if error:
            return error

        return diagnose_job(job)


def run_agent_graph_debug_tool(
    job_id: int,
    question: str,
    use_context: bool = True,
    include_logs: bool = False,
    use_retrieval: bool = True
) -> Dict[str, Any]:
    """
    只读工具：运行 LangGraph debug 流程。
    不调用 LLM，不消耗 token。
    """
    with tool_db_session() as db:
        job, error = get_job_or_error(db, job_id)

        if error:
            return error

        graph_result = run_agent_graph(
            job=job,
            question=question,
            use_context=use_context,
            include_logs=include_logs,
            use_retrieval=use_retrieval,
            skip_llm=True
        )

        text_context = graph_result.get("text_context") or {}
        retrieved_sections = text_context.get(
            "retrieved_report_sections",
            []
        )

        return {
            "job_id": job.id,
            "question": question,
            "answer_source": graph_result.get("answer_source"),
            "planned_context": graph_result.get("planned_context"),
            "auto_include_logs": graph_result.get("auto_include_logs", False),
            "auto_use_retrieval": graph_result.get("auto_use_retrieval", False),
            "context_keys": list(text_context.keys()),
            "retrieved_sections": retrieved_sections,
            "debug_steps": graph_result.get("debug_steps", []),
            "evidence": graph_result.get("evidence", {})
        }