from pathlib import Path
import sys
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from backend.tools.job_tools import get_job_status_tool
from backend.tools.agent_tools import (
    diagnose_job_tool,
    run_agent_graph_debug_tool
)
from backend.tools.report_tools import (
    search_report_sections_tool,
    get_context_preview_tool
)


mcp = FastMCP(
    "Recon Dataset Inspector MCP",
    json_response=True
)


@mcp.tool()
def get_job_status(job_id: int) -> Dict[str, Any]:
    """
    Get basic status information for a reconstruction job.
    Read-only tool.
    """
    return get_job_status_tool(job_id)


@mcp.tool()
def diagnose_job(job_id: int) -> Dict[str, Any]:
    """
    Run rule-based diagnosis for a reconstruction job.
    Read-only tool.
    """
    return diagnose_job_tool(job_id)


@mcp.tool()
def search_report_sections(
    job_id: int,
    question: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Search reconstruction/readiness report sections related to a question.
    Read-only tool.
    """
    return search_report_sections_tool(
        job_id=job_id,
        question=question,
        top_k=top_k
    )


@mcp.tool()
def get_context_preview(job_id: int) -> Dict[str, Any]:
    """
    Get preview of report/log context used by the Agent.
    Read-only tool.
    """
    return get_context_preview_tool(job_id)


@mcp.tool()
def run_agent_graph_debug(
    job_id: int,
    question: str,
    use_context: bool = True,
    include_logs: bool = False,
    use_retrieval: bool = True
) -> Dict[str, Any]:
    """
    Run LangGraph debug workflow without calling LLM.
    Read-only tool.
    """
    return run_agent_graph_debug_tool(
        job_id=job_id,
        question=question,
        use_context=use_context,
        include_logs=include_logs,
        use_retrieval=use_retrieval
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()