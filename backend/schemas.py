from pydantic import BaseModel, Field
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
    use_retrieval: bool = True

class AgentChatResponse(BaseModel):
    job_id: int
    question: str
    answer: str
    answer_source: str
    context_used: bool
    logs_included: bool
    retrieval_used: bool
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

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class RetrievedSection(BaseModel):
    source: str
    title: str
    score: float
    content: str


class RetrievalPreviewResponse(BaseModel):
    job_id: int
    question: str
    sections: List[RetrievedSection]

class AgentGraphDebugResponse(BaseModel):
    job_id: int
    question: str
    answer_source: str
    planned_context: Optional[str]
    auto_include_logs: bool
    auto_use_retrieval: bool
    context_keys: List[str]
    retrieved_sections: List[RetrievedSection]
    debug_steps: List[str]
    evidence: Dict[str, Any]


