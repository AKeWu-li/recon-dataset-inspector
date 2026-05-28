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
    AgentContextPreviewResponse,
    RetrievalPreviewResponse,
    AgentGraphDebugResponse
)
from backend.services.diagnosis_service import diagnose_job
from backend.services.diagnosis_service import diagnose_job
from backend.services.llm_service import get_llm_status
from backend.services.context_service import get_context_preview
from backend.services.retrieval_service import search_job_reports
from backend.services.agent_graph import run_agent_graph
from backend.security import get_current_user


router = APIRouter(
    prefix="/api/v1/agent",
    tags=["agent"],
    dependencies=[Depends(get_current_user)]
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

    graph_result = run_agent_graph(
        job=job,
        question=request.question,
        use_context=request.use_context,
        include_logs=request.include_logs,
        use_retrieval=request.use_retrieval
    )

    answer = graph_result["answer"]
    answer_source = graph_result["answer_source"]
    evidence = graph_result["evidence"]

    conversation = AgentConversation(
        job_id=job.id,
        question=request.question,
        answer=answer,
        answer_source=answer_source,
        llm_provider=graph_result.get("llm_provider"),
        llm_model=graph_result.get("llm_model"),
        llm_error=graph_result.get("llm_error"),
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
        "retrieval_used": request.use_retrieval,
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

@router.get(
    "/jobs/{job_id}/retrieval-preview",
    response_model=RetrievalPreviewResponse
)
def preview_report_retrieval(
    job_id: int,
    question: str,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    sections = search_job_reports(
        job=job,
        question=question,
        top_k=top_k
    )

    return {
        "job_id": job.id,
        "question": question,
        "sections": sections
    }

@router.post("/graph-debug", response_model=AgentGraphDebugResponse)
def debug_agent_graph(
    request: AgentChatRequest,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == request.job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    graph_result = run_agent_graph(
        job=job,
        question=request.question,
        use_context=request.use_context,
        include_logs=request.include_logs,
        use_retrieval=request.use_retrieval,
        skip_llm=True
    )

    text_context = graph_result.get("text_context") or {}

    retrieved_sections = text_context.get(
        "retrieved_report_sections",
        []
    )

    return {
        "job_id": job.id,
        "question": request.question,
        "answer_source": graph_result.get("answer_source"),
        "planned_context": graph_result.get("planned_context"),
        "auto_include_logs": graph_result.get("auto_include_logs", False),
        "auto_use_retrieval": graph_result.get("auto_use_retrieval", False),
        "context_keys": list(text_context.keys()),
        "retrieved_sections": retrieved_sections,
        "debug_steps": graph_result.get("debug_steps", []),
        "evidence": graph_result.get("evidence", {})
    }