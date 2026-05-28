from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime

from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=False)
    blur_threshold = Column(Float, default=100)

    status = Column(String, default="pending")
    message = Column(Text, default="")
    celery_task_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, index=True)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    answer_source = Column(String, default="rule_based")
    llm_provider = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    llm_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)