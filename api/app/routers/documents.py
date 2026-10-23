"""Upload a document, read it back, and ask questions about it."""

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.schemas import ChatRequest, ChatResponse, DocumentDetail, DocumentSummary, MessageOut
from app.services.documents import (
    DocumentServiceError,
    ask,
    create_document,
    delete_document,
    get_document,
    list_documents,
    list_messages,
    to_detail,
    to_summary,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db(request: Request):
    session: Session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _service_error(exc: DocumentServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@router.post("", response_model=DocumentDetail, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    try:
        document = create_document(
            db,
            request.app.state.settings,
            request.app.state.provider,
            filename=file.filename or "upload",
            content_type=file.content_type or "",
            data=data,
        )
    except DocumentServiceError as exc:
        return _service_error(exc)
    return to_detail(db, document)


@router.get("", response_model=list[DocumentSummary])
def get_documents(db: Session = Depends(get_db)) -> list[DocumentSummary]:
    return [to_summary(db, document) for document in list_documents(db)]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_one(document_id: str, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"detail": "Document not found."})
    return to_detail(db, document)


@router.delete("/{document_id}", status_code=204)
def remove(document_id: str, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"detail": "Document not found."})
    delete_document(db, document)
    return Response(status_code=204)


@router.get("/{document_id}/messages", response_model=list[MessageOut])
def get_messages(document_id: str, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"detail": "Document not found."})
    return list_messages(document)


@router.post("/{document_id}/chat", response_model=ChatResponse)
def chat(document_id: str, body: ChatRequest, request: Request, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"detail": "Document not found."})
    try:
        answer, citations, message_id = ask(
            db,
            request.app.state.settings,
            request.app.state.provider,
            document,
            body.question,
        )
    except DocumentServiceError as exc:
        return _service_error(exc)
    return ChatResponse(answer=answer, citations=citations, message_id=message_id)
