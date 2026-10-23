"""Request and response bodies for the REST API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    provider: str
    embedding_provider: str
    database: str
    model: str | None = None


class Citation(BaseModel):
    label: int
    chunk_index: int
    text: str
    score: float


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    file_size: int
    summary: str
    key_points: list[str]
    chunk_count: int
    provider: str
    embedding_provider: str
    created_at: datetime


class DocumentDetail(DocumentSummary):
    extracted_text: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    message_id: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: list[Citation]
    created_at: datetime
