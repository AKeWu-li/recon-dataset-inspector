from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import Job, AgentConversation
from backend.schemas import (
    AgentDiagnoseRequest,
    AgentDiagnoseResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentConversationResponse,
    LLMStatusResponse,
    AgentContextPreviewResponse
)
from backend.services.diagnosis_service import diagnose_job
from backend.services.llm_service import generate_llm_answer, get_llm_status
from backend.services.context_service import collect_job_text_context, get_context_preview


router = APIRouter(
    prefix="/api/v1/agent",
    tags=["agent"]
)


@router.post("/diagnose", response_model=AgentDiagnoseResponse)
def diagnose_reconstruction_job(
    request: AgentDiagnoseRequest,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == request.job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result = diagnose_job(job)

    return result

@router.post("/chat", response_model=AgentChatResponse)
def chat_with_reconstruction_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == request.job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    diagnose_result = diagnose_job(job)

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

    rule_answer = "\n".join(answer_lines)

    if request.use_context:
        text_context = collect_job_text_context(
            job,
            include_logs=request.include_logs
        )
    else:
        text_context = None

    llm_answer, llm_error, llm_provider, llm_model = generate_llm_answer(
        question=request.question,
        diagnose_result=diagnose_result,
        rule_answer=rule_answer,
        text_context=text_context
    )

    if llm_answer is not None:
        answer = llm_answer
        answer_source = f"llm:{llm_provider}"
    else:
        answer = rule_answer

        if llm_error:
            answer += f"\n\n注意：大模型回答生成失败，当前返回规则版诊断结果。错误信息：{llm_error}"
            answer_source = f"rule_based_fallback:{llm_provider}"
        else:
            answer_source = "rule_based"

    conversation = AgentConversation(
        job_id=job.id,
        question=request.question,
        answer=answer,
        answer_source=answer_source,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_error=llm_error,
        created_at=datetime.now()
    )

    db.add(conversation)
    db.commit()

    return {
        "job_id": job.id,
        "question": request.question,
        "answer": answer,
        "answer_source": answer_source,
        "context_used": request.use_context,
        "logs_included": request.include_logs,
        "evidence": evidence
    }

@router.get(
    "/jobs/{job_id}/conversations",
    response_model=list[AgentConversationResponse]
)
def list_job_conversations(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    conversations = (
        db.query(AgentConversation)
        .filter(AgentConversation.job_id == job_id)
        .order_by(AgentConversation.id.desc())
        .all()
    )

    return conversations

@router.get("/llm-status", response_model=LLMStatusResponse)
def check_llm_status():
    return get_llm_status()

@router.get("/jobs/{job_id}/context-preview",response_model=AgentContextPreviewResponse)
def preview_agent_context(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    files = get_context_preview(job)

    return {
        "job_id": job.id,
        "files": files
    }