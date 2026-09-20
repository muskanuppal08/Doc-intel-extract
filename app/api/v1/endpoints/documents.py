"""Document management, upload, status polling, and question retrieval endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks, status, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.extraction_warning import ExtractionWarning
from app.models.relationship import DocumentRelationship
from app.models.enums import DocumentStatus, DocumentType, QuestionType, ReviewStatus
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentRead,
    DocumentRelationshipCreate,
    DocumentRelationshipRead,
)
from app.schemas.question import QuestionRead
from app.schemas.answer_key import AnswerKeyRead
from app.schemas.warning import ExtractionWarningRead
from app.storage.service import storage_service
from app.services.answer_key.linker import answer_linker
from app.workers.tasks import dispatch_processing_job

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF or image examination file"),
    doc_type: DocumentType = Form(DocumentType.QUESTION_PAPER, description="Type of document"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or image document (digitally generated, scanned, PNG, JPG).
    The file is validated for binary magic bytes, saved with SHA-256 deduplication,
    and queued asynchronously for question extraction.
    """
    file_path, file_hash, file_size, mime_type = storage_service.save_upload(
        file_obj=file.file,
        filename=file.filename or "upload.pdf",
        user_id=current_user.id,
    )

    # Check for existing document by hash for this user
    existing_doc = (
        db.query(Document)
        .filter(Document.owner_id == current_user.id, Document.file_hash == file_hash)
        .first()
    )
    if existing_doc and existing_doc.status == DocumentStatus.COMPLETED:
        return DocumentUploadResponse(
            id=existing_doc.id,
            original_filename=existing_doc.original_filename,
            file_size_bytes=existing_doc.file_size_bytes,
            mime_type=existing_doc.mime_type,
            doc_type=existing_doc.doc_type,
            status=existing_doc.status,
            message="Document already processed (deduplicated via SHA-256)",
            tracking_url=f"{settings.API_V1_STR}/documents/{existing_doc.id}/status",
        )

    # Create new document record
    doc = Document(
        owner_id=current_user.id,
        original_filename=file.filename or "unnamed_document",
        file_path=file_path,
        file_hash=file_hash,
        file_size_bytes=file_size,
        mime_type=mime_type,
        doc_type=doc_type,
        status=DocumentStatus.UPLOADED,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Dispatch asynchronous extraction pipeline
    dispatch_processing_job(document_id=doc.id, background_tasks=background_tasks)

    return DocumentUploadResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        doc_type=doc.doc_type,
        status=doc.status,
        message="Document uploaded successfully and queued for processing",
        tracking_url=f"{settings.API_V1_STR}/documents/{doc.id}/status",
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Poll processing status of an uploaded document.
    Returns lifecycle state: UPLOADED -> PREPROCESSING -> EXTRACTING -> ASSOCIATING_ANSWERS -> COMPLETED.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # User isolation check (admin/reviewer can access all)
    if doc.owner_id != current_user.id and current_user.role.value not in ("admin", "reviewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    q_count = db.query(Question).filter(Question.document_id == doc.id).count()
    a_count = db.query(AnswerKey).filter(AnswerKey.source_document_id == doc.id).count()
    w_count = db.query(ExtractionWarning).filter(ExtractionWarning.document_id == doc.id).count()

    return DocumentStatusResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        doc_type=doc.doc_type,
        status=doc.status,
        page_count=doc.page_count,
        questions_extracted=q_count,
        answer_keys_found=a_count,
        warnings_count=w_count,
        error_message=doc.error_message,
        processing_started_at=doc.processing_started_at,
        processing_completed_at=doc.processing_completed_at,
        created_at=doc.created_at,
    )


@router.get("/{document_id}/questions", response_model=List[QuestionRead])
def get_document_questions(
    document_id: str,
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    review_status: Optional[ReviewStatus] = Query(None, description="Filter by review status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve structured, machine-readable questions extracted from a document.
    Includes question stems, options, associated answers, confidence scores, and source pages.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.owner_id != current_user.id and current_user.role.value not in ("admin", "reviewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(Question).filter(Question.document_id == doc.id)
    if question_type:
        query = query.filter(Question.question_type == question_type)
    if review_status:
        query = query.filter(Question.review_status == review_status)

    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/{document_id}/answers", response_model=List[AnswerKeyRead])
def get_document_answers(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve all answer keys parsed from the document or linked to its questions."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.owner_id != current_user.id and current_user.role.value not in ("admin", "reviewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    answers = db.query(AnswerKey).filter(AnswerKey.source_document_id == doc.id).all()
    return answers


@router.get("/{document_id}/warnings", response_model=List[ExtractionWarningRead])
def get_document_warnings(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve extraction warnings and items requiring human review."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.owner_id != current_user.id and current_user.role.value not in ("admin", "reviewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    warnings = db.query(ExtractionWarning).filter(ExtractionWarning.document_id == doc.id).all()
    return warnings


@router.post("/link", response_model=DocumentRelationshipRead, status_code=status.HTTP_201_CREATED)
def link_related_documents(
    payload: DocumentRelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Associate two related documents (e.g. Question Paper <-> Separate Answer Key).
    Automatically matches answer keys from the answer document to questions in the paper document.
    """
    doc_src = db.query(Document).filter(Document.id == payload.source_document_id).first()
    doc_tgt = db.query(Document).filter(Document.id == payload.target_document_id).first()

    if not doc_src or not doc_tgt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both documents not found")

    # Link in DB and match answers
    answer_linker.link_documents_in_db(
        db=db,
        question_doc_id=payload.source_document_id,
        answer_doc_id=payload.target_document_id,
        relationship_type=payload.relationship_type,
    )

    rel = (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.source_document_id == payload.source_document_id,
            DocumentRelationship.target_document_id == payload.target_document_id,
        )
        .first()
    )
    return rel
