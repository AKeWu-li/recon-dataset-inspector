from typing import Any, Dict, Optional, TypedDict, List

from langgraph.graph import StateGraph, END

from backend.services.diagnosis_service import diagnose_job
from backend.services.context_service import collect_job_text_context
from backend.services.retrieval_service import search_job_reports
from backend.services.llm_service import generate_llm_answer


class AgentState(TypedDict, total=False):
    job: Any
    question: str

    use_context: bool
    include_logs: bool
    use_retrieval: bool
    skip_llm: bool

    diagnose_result: Dict[str, Any]
    evidence: Dict[str, Any]
    rule_answer: str
    text_context: Optional[Dict[str, Any]]

    auto_include_logs: bool
    auto_use_retrieval: bool
    planned_context: str

    llm_answer: Optional[str]
    llm_error: Optional[str]
    llm_provider: Optional[str]
    llm_model: Optional[str]

    answer: str
    answer_source: str

    debug_steps: List[str]


LOG_KEYWORDS = [
    "日志", "log", "报错", "错误", "失败", "failed",
    "error", "exception", "traceback", "崩溃", "异常"
]

REPORT_KEYWORDS = [
    "质量", "风险", "报告", "建议", "重建", "COLMAP",
    "3DGS", "注册", "注册率", "稀疏", "点云", "相机",
    "轨迹", "模糊", "readiness", "reconstruction"
]

STATUS_ONLY_KEYWORDS = [
    "状态", "进度", "现在到哪", "完成了吗", "成功了吗"
]


def append_debug(state: AgentState, message: str) -> List[str]:
    steps = list(state.get("debug_steps", []))
    steps.append(message)
    return steps


def diagnose_node(state: AgentState) -> Dict[str, Any]:
    job = state["job"]
    diagnose_result = diagnose_job(job)

    return {
        "diagnose_result": diagnose_result,
        "evidence": diagnose_result["evidence"],
        "debug_steps": append_debug(
            state,
            f"diagnose_node: job_status={diagnose_result.get('job_status')}, quality={diagnose_result.get('quality')}"
        )
    }


def route_context_node(state: AgentState) -> Dict[str, Any]:
    job = state["job"]
    question = state["question"]

    use_context = state.get("use_context", True)
    include_logs = state.get("include_logs", False)
    use_retrieval = state.get("use_retrieval", True)

    question_lower = question.lower()
    job_status = getattr(job, "status", "") or ""

    asks_logs = any(keyword.lower() in question_lower for keyword in LOG_KEYWORDS)
    job_failed = "failed" in job_status.lower() or "失败" in job_status

    auto_include_logs = include_logs or asks_logs or job_failed

    asks_report = any(keyword.lower() in question_lower for keyword in REPORT_KEYWORDS)
    asks_status_only = any(keyword.lower() in question_lower for keyword in STATUS_ONLY_KEYWORDS)

    if not use_context:
        auto_use_retrieval = False
        planned_context = "no_context"
    elif use_retrieval and asks_report:
        auto_use_retrieval = True
        planned_context = "retrieval"
    elif use_retrieval and not asks_status_only:
        # 默认情况：如果不是单纯问状态，就使用报告检索
        auto_use_retrieval = True
        planned_context = "retrieval"
    else:
        auto_use_retrieval = False
        planned_context = "no_context"

    return {
        "auto_include_logs": auto_include_logs,
        "auto_use_retrieval": auto_use_retrieval,
        "planned_context": planned_context,
        "debug_steps": append_debug(
            state,
            (
                "route_context_node: "
                f"use_context={use_context}, "
                f"auto_use_retrieval={auto_use_retrieval}, "
                f"auto_include_logs={auto_include_logs}, "
                f"planned_context={planned_context}"
            )
        )
    }


def build_rule_answer_node(state: AgentState) -> Dict[str, Any]:
    job = state["job"]
    diagnose_result = state["diagnose_result"]

    quality = diagnose_result["quality"]
    main_problems = diagnose_result["main_problems"]
    suggestions = diagnose_result["suggestions"]
    next_actions = diagnose_result["next_actions"]
    evidence = diagnose_result["evidence"]

    answer_lines = []

    answer_lines.append(f"任务 {job.id} 当前状态是 `{job.status}`。")
    answer_lines.append(f"系统根据当前任务输出判断，重建质量为：`{quality}`。")
    answer_lines.append("")

    answer_lines.append("主要诊断结果：")
    for problem in main_problems:
        answer_lines.append(f"- {problem}")

    answer_lines.append("")
    answer_lines.append("建议：")
    for suggestion in suggestions:
        answer_lines.append(f"- {suggestion}")

    answer_lines.append("")
    answer_lines.append("下一步可以执行：")
    for action in next_actions:
        answer_lines.append(f"- {action}")

    answer_lines.append("")
    answer_lines.append("关键证据：")
    answer_lines.append(f"- 有效图片数量：{evidence.get('valid_image_count')}")
    answer_lines.append(f"- 模糊图片数量：{evidence.get('blurry_image_count')}")
    answer_lines.append(f"- 模糊图片比例：{evidence.get('blurry_ratio')}")
    answer_lines.append(f"- COLMAP 工作目录是否存在：{evidence.get('colmap_workspace_exists')}")
    answer_lines.append(f"- sparse.ply 是否存在：{evidence.get('sparse_ply_exists')}")
    answer_lines.append(f"- sparse_txt 是否存在：{evidence.get('sparse_txt_exists')}")
    answer_lines.append(f"- 重建报告是否存在：{evidence.get('reconstruction_report_exists')}")
    answer_lines.append(f"- readiness 报告是否存在：{evidence.get('readiness_report_exists')}")
    answer_lines.append(f"- 质量评分：{evidence.get('quality_score')}")
    answer_lines.append(f"- 注册图片比例：{evidence.get('registered_ratio')}%")

    return {
        "rule_answer": "\n".join(answer_lines),
        "debug_steps": append_debug(
            state,
            "build_rule_answer_node: rule-based answer generated"
        )
    }


def retrieve_report_node(state: AgentState) -> Dict[str, Any]:
    job = state["job"]
    question = state["question"]

    retrieved_sections = search_job_reports(
        job=job,
        question=question,
        top_k=5
    )

    text_context = {
        "retrieved_report_sections": retrieved_sections
    }

    titles = [
        f"{section.get('source')}::{section.get('title')}"
        for section in retrieved_sections
    ]

    return {
        "text_context": text_context,
        "debug_steps": append_debug(
            state,
            f"retrieve_report_node: retrieved {len(retrieved_sections)} sections: {titles}"
        )
    }


def no_context_node(state: AgentState) -> Dict[str, Any]:
    return {
        "text_context": None,
        "debug_steps": append_debug(
            state,
            "no_context_node: skipped report/log context"
        )
    }


def add_logs_node(state: AgentState) -> Dict[str, Any]:
    job = state["job"]

    text_context = state.get("text_context") or {}

    log_context = collect_job_text_context(
        job,
        include_logs=True
    )

    text_context["backend_job_log"] = log_context.get(
        "backend_job_log",
        ""
    )
    text_context["after_colmap_log"] = log_context.get(
        "after_colmap_log",
        ""
    )

    return {
        "text_context": text_context,
        "debug_steps": append_debug(
            state,
            "add_logs_node: backend_job_log and after_colmap_log added"
        )
    }


def llm_answer_node(state: AgentState) -> Dict[str, Any]:
    if state.get("skip_llm", False):
        return {
            "answer": state["rule_answer"],
            "answer_source": "debug_no_llm",
            "llm_answer": None,
            "llm_error": None,
            "llm_provider": None,
            "llm_model": None,
            "debug_steps": append_debug(
                state,
                "llm_answer_node: skipped LLM call because skip_llm=True"
            )
        }

    llm_answer, llm_error, llm_provider, llm_model = generate_llm_answer(
        question=state["question"],
        diagnose_result=state["diagnose_result"],
        rule_answer=state["rule_answer"],
        text_context=state.get("text_context")
    )

    if llm_answer is not None:
        answer = llm_answer
        answer_source = f"llm:{llm_provider}"
        debug_message = f"llm_answer_node: LLM answer generated by {llm_provider}/{llm_model}"
    else:
        answer = state["rule_answer"]

        if llm_error:
            answer += (
                "\n\n注意：大模型回答生成失败，"
                f"当前返回规则版诊断结果。错误信息：{llm_error}"
            )
            answer_source = f"rule_based_fallback:{llm_provider}"
            debug_message = f"llm_answer_node: LLM failed, fallback used. error={llm_error}"
        else:
            answer_source = "rule_based"
            debug_message = "llm_answer_node: rule-based answer used"

    return {
        "llm_answer": llm_answer,
        "llm_error": llm_error,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "answer": answer,
        "answer_source": answer_source,
        "debug_steps": append_debug(state, debug_message)
    }


def route_after_rule_answer(state: AgentState) -> str:
    planned_context = state.get("planned_context", "retrieval")

    if planned_context == "no_context":
        return "no_context"

    return "retrieve_report"


def route_after_context(state: AgentState) -> str:
    if state.get("auto_include_logs", False):
        return "add_logs"

    return "llm_answer"


def build_agent_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("diagnose", diagnose_node)
    graph_builder.add_node("route_context", route_context_node)
    graph_builder.add_node("build_rule_answer", build_rule_answer_node)
    graph_builder.add_node("retrieve_report", retrieve_report_node)
    graph_builder.add_node("no_context", no_context_node)
    graph_builder.add_node("add_logs", add_logs_node)
    graph_builder.add_node("llm_answer", llm_answer_node)

    graph_builder.set_entry_point("diagnose")

    graph_builder.add_edge("diagnose", "route_context")
    graph_builder.add_edge("route_context", "build_rule_answer")

    graph_builder.add_conditional_edges(
        "build_rule_answer",
        route_after_rule_answer,
        {
            "retrieve_report": "retrieve_report",
            "no_context": "no_context",
        }
    )

    graph_builder.add_conditional_edges(
        "retrieve_report",
        route_after_context,
        {
            "add_logs": "add_logs",
            "llm_answer": "llm_answer",
        }
    )

    graph_builder.add_conditional_edges(
        "no_context",
        route_after_context,
        {
            "add_logs": "add_logs",
            "llm_answer": "llm_answer",
        }
    )

    graph_builder.add_edge("add_logs", "llm_answer")
    graph_builder.add_edge("llm_answer", END)

    return graph_builder.compile()


agent_graph = build_agent_graph()


def run_agent_graph(
    job,
    question: str,
    use_context: bool = True,
    include_logs: bool = False,
    use_retrieval: bool = True,
    skip_llm: bool = False
) -> Dict[str, Any]:
    initial_state = {
        "job": job,
        "question": question,
        "use_context": use_context,
        "include_logs": include_logs,
        "use_retrieval": use_retrieval,
        "skip_llm": skip_llm,
        "debug_steps": []
    }

    result = agent_graph.invoke(initial_state)

    return result