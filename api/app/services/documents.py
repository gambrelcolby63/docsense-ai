"""Create documents and answer questions grounded in their chunks."""

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import ChatMessage, Chunk, Document
from app.schemas import Citation, DocumentDetail, DocumentSummary, MessageOut
from app.services.chunking import chunk_text
from app.services.extraction import ExtractionError, UnsupportedFileError, extract_text
from app.services.llm import (
    LLMError,
    LLMProvider,
    answer_question,
    embed_passages,
    embed_query,
    summarize_document,
)
from app.services.rag import retrieve

MAX_TEXT_CHARS = 200_000
MAX_CHUNKS = 400


class DocumentServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def create_document(
    db: Session,
    settings: Settings,
    provider: LLMProvider,
    *,
    filename: str,
    content_type: str,
    data: bytes,
) -> Document:
    safe_name = Path(filename or "upload").name[:255] or "upload"
    if len(data) > settings.max_upload_bytes:
        limit_mb = settings.max_upload_bytes // (1024 * 1024)
        raise DocumentServiceError(413, f"That file is larger than the {limit_mb} MB limit.")
    try:
        text = extract_text(safe_name, content_type or "", data)
    except UnsupportedFileError as exc:
        raise DocumentServiceError(415, str(exc)) from exc
    except ExtractionError as exc:
        raise DocumentServiceError(422, str(exc)) from exc

    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS]
    pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)[:MAX_CHUNKS]
    if not pieces:
        raise DocumentServiceError(422, "No text could be read from this file.")

    try:
        embedding_mode, vectors = embed_passages(provider, settings, pieces)
        summary, key_points = summarize_document(provider, text)
    except LLMError as exc:
        raise DocumentServiceError(502, str(exc)) from exc

    document = Document(
        id=str(uuid.uuid4()),
        filename=safe_name,
        content_type=(content_type or "application/octet-stream").split(";")[0][:127],
        file_size=len(data),
        extracted_text=text,
        summary=summary,
        key_points=key_points,
        provider=_provider_label(provider),
        embedding_provider=embedding_mode,
    )
    document.chunks = [
        Chunk(position=index, text=piece, embedding=vector)
        for index, (piece, vector) in enumerate(zip(pieces, vectors, strict=True))
    ]
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(statement))


def get_document(db: Session, document_id: str) -> Document | None:
    return db.get(Document, document_id)


def delete_document(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()


def list_messages(document: Document) -> list[MessageOut]:
    return [_message_out(message) for message in document.messages]


def ask(
    db: Session,
    settings: Settings,
    provider: LLMProvider,
    document: Document,
    question: str,
) -> tuple[str, list[Citation], int]:
    question = question.strip()
    if not question:
        raise DocumentServiceError(422, "Ask a question about the document.")
    try:
        query_vector = embed_query(provider, document.embedding_provider, question)
    except LLMError as exc:
        raise DocumentServiceError(502, str(exc)) from exc

    ranked = retrieve(document.chunks, query_vector, settings.retrieval_k)
    # A zero score means the passage shares no terms with the question.
    # Keep it only when nothing was actually similar, so the UI can show
    # the nearest passage on a miss without padding a good answer.
    matched = [item for item in ranked if item[1] > 0]
    ranked = matched or ranked[:1]
    passages: list[tuple[int, int, str, float]] = []
    citations: list[Citation] = []
    for label, (chunk, score) in enumerate(ranked, start=1):
        passages.append((label, chunk.position, chunk.text, score))
        citations.append(
            Citation(
                label=label,
                chunk_index=chunk.position,
                text=chunk.text,
                score=round(score, 4),
            )
        )

    history = [(message.role, message.content) for message in document.messages]
    try:
        answer = answer_question(provider, question, passages, history)
    except LLMError as exc:
        raise DocumentServiceError(502, str(exc)) from exc

    db.add(ChatMessage(document_id=document.id, role="user", content=question, citations=[]))
    assistant = ChatMessage(
        document_id=document.id,
        role="assistant",
        content=answer,
        citations=[citation.model_dump() for citation in citations],
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return answer, citations, assistant.id


def _provider_label(provider: LLMProvider) -> str:
    if provider.name == "mock":
        return "mock"
    return str(getattr(provider, "model", provider.name))[:128]


def to_summary(db: Session, document: Document) -> DocumentSummary:
    count = db.scalar(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == document.id)
    )
    return DocumentSummary(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        summary=document.summary,
        key_points=list(document.key_points or []),
        chunk_count=int(count or 0),
        provider=document.provider,
        embedding_provider=document.embedding_provider,
        created_at=document.created_at,
    )


def to_detail(db: Session, document: Document) -> DocumentDetail:
    summary = to_summary(db, document)
    return DocumentDetail(**summary.model_dump(), extracted_text=document.extracted_text)


def _message_out(message: ChatMessage) -> MessageOut:
    raw = message.citations or []
    citations = [Citation.model_validate(item) for item in raw]
    return MessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=citations,
        created_at=message.created_at,
    )
