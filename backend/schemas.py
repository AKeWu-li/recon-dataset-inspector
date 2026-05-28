from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class JobCreate(BaseModel):
    input_path: str
    output_path: str = "output"
    blur_threshold: float = 100
    auto_run: bool = True


class JobResponse(BaseModel):
    id: int
    input_path: str
    output_path: str
    blur_threshold: float
    status: str
    message: Optional[str]
    celery_task_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobOutputsResponse(BaseModel):
    job_id: int
    output_path: str
    exists: bool
    files: List[str]
    folders: List[str]

class JobLogResponse(BaseModel):
    job_id: int
    log_path: str
    exists: bool
    content: str

class JobReportResponse(BaseModel):
    job_id: int
    report_type: str
    report_path: str
    exists: bool
    content: str

class AgentDiagnoseRequest(BaseModel):
    job_id: int


class AgentDiagnoseResponse(BaseModel):
    job_id: int
    job_status: str
    quality: str
    main_problems: List[str]
    suggestions: List[str]
    next_actions: List[str]
    evidence: Dict[str, Any]

class AgentChatRequest(BaseModel):
    job_id: int
    question: str
    use_context: bool = True
    include_logs: bool = False


class AgentChatResponse(BaseModel):
    job_id: int
    question: str
    answer: str
    answer_source: str
    context_used: bool
    logs_included: bool
    evidence: Dict[str, Any]

class AgentConversationResponse(BaseModel):
    id: int
    job_id: int
    question: str
    answer: str
    answer_source: str
    llm_provider: Optional[str]
    llm_model: Optional[str]
    llm_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LLMStatusResponse(BaseModel):
    provider: str
    model: str
    base_url: Optional[str]
    api_key_configured: bool

class ContextFilePreview(BaseModel):
    name: str
    exists: bool
    char_count: int
    preview: str


class AgentContextPreviewResponse(BaseModel):
    job_id: int
    files: List[ContextFilePreview]

