"""Asynchronous document processing worker tasks and pipeline execution."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import (
    Document,
    DocumentStatus,
    Question,
    QuestionOption,
    AnswerKey,
    ExtractionWarning,
    ReviewStatus,
    AnswerMatchStatus,
)
from app.services.preprocessing.preprocessor import preprocessor
from app.services.extractor.hybrid import hybrid_extractor
from app.services.answer_key.linker import answer_linker
from app.services.scoring.validator import extraction_validator
from app.workers.celery_app import celery_app


def execute_document_pipeline(document_id: str) -> None:
    """
    Executes the full asynchronous document extraction lifecycle:
    1. Preprocessing & structure inspection (page count, digital vs scanned)
    2. Hybrid extraction (PyMuPDF / Multimodal Vision / Segmenter)
    3. Answer key parsing & fuzzy linking
    4. Multi-factor confidence scoring & review flag evaluation
    5. Atomic persistence to PostgreSQL
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # 1. Update status: PREPROCESSING
        doc.status = DocumentStatus.PREPROCESSING
        doc.processing_started_at = datetime.now(timezone.utc)
        db.commit()

        file_path = Path(doc.file_path)
        if not file_path.exists():
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"File not found at storage path: {doc.file_path}"
            db.commit()
            return

        # Inspect document
        inspection = preprocessor.inspect_document(file_path)
        doc.page_count = inspection.page_count
        doc.extra_metadata = {
            "is_digital": inspection.is_digital_pdf,
            "is_scanned": inspection.is_scanned,
        }
        db.commit()

        # 2. Update status: EXTRACTING
        doc.status = DocumentStatus.EXTRACTING
        db.commit()

        extraction_result = hybrid_extractor.extract(file_path)

        # 3. Update status: ASSOCIATING_ANSWERS
        doc.status = DocumentStatus.ASSOCIATING_ANSWERS
        db.commit()

        questions, answers, link_warnings = answer_linker.link_answers(
            extraction_result.questions,
            extraction_result.answers,
        )

        # 4. Run confidence scoring & validation
        scored_questions, review_warnings = extraction_validator.validate_and_score_questions(
            questions,
            answers,
        )

        all_warnings = (
            extraction_result.warnings
            + link_warnings
            + review_warnings
        )

        # 5. Persist extracted questions & options
        has_needs_review = False
        saved_q_map = {}

        for q_dto in scored_questions:
            q_model = Question(
                document_id=doc.id,
                question_number=q_dto.question_number,
                question_text=q_dto.question_text,
                question_type=q_dto.question_type,
                source_pages=q_dto.source_pages,
                bounding_boxes=q_dto.bounding_boxes or [],
                diagram_paths=q_dto.diagram_paths or [],
                confidence_score=q_dto.confidence_score,
                review_status=q_dto.review_status,
                raw_extraction={"raw_text": q_dto.raw_text},
            )
            db.add(q_model)
            db.flush()  # Generate q_model.id

            if q_dto.question_number:
                clean_id = answer_linker.clean_identifier(q_dto.question_number)
                saved_q_map[clean_id] = q_model.id

            if q_dto.review_status in (ReviewStatus.NEEDS_REVIEW, ReviewStatus.PARTIAL_EXTRACTION):
                has_needs_review = True

            # Save options
            for opt_dto in q_dto.options:
                opt_model = QuestionOption(
                    question_id=q_model.id,
                    option_key=opt_dto.key,
                    option_text=opt_dto.text,
                    diagram_path=opt_dto.diagram_path,
                    order_index=opt_dto.order_index,
                    confidence_score=opt_dto.confidence_score,
                )
                db.add(opt_model)

        # 6. Persist answer keys
        for ans_dto in answers:
            clean_ans_id = answer_linker.clean_identifier(ans_dto.question_identifier)
            linked_q_id = saved_q_map.get(clean_ans_id)

            ans_model = AnswerKey(
                source_document_id=doc.id,
                question_id=linked_q_id,
                question_identifier=ans_dto.question_identifier,
                raw_answer_text=ans_dto.raw_answer_text,
                normalized_answer=ans_dto.normalized_answer,
                explanation=ans_dto.explanation,
                source_page=ans_dto.source_page,
                confidence_score=ans_dto.confidence_score,
                match_status=ans_dto.match_status,
            )
            db.add(ans_model)

        # 7. Persist extraction warnings
        for w_dto in all_warnings:
            clean_w_id = answer_linker.clean_identifier(w_dto.question_identifier) if w_dto.question_identifier else None
            w_qid = saved_q_map.get(clean_w_id) if clean_w_id else None

            warn_model = ExtractionWarning(
                document_id=doc.id,
                question_id=w_qid,
                warning_code=w_dto.warning_code,
                message=w_dto.message,
                severity=w_dto.severity,
                source_page=w_dto.source_page,
                details=w_dto.details or {},
            )
            db.add(warn_model)

        # 8. Mark document completed
        doc.status = DocumentStatus.NEEDS_REVIEW if has_needs_review else DocumentStatus.COMPLETED
        doc.processing_completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        # Record failure on document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"Processing failed: {str(exc)}"
            doc.processing_completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@celery_app.task(name="process_document_celery")
def process_document_celery(document_id: str):
    """Celery background task."""
    execute_document_pipeline(document_id)


def dispatch_processing_job(
    document_id: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> None:
    """
    Dual-mode task dispatcher:
    1. If background_tasks is supplied (FastAPI request lifecycle), queue task in-process.
    2. Otherwise attempt Celery/Redis, falling back to in-process execution.
    """
    if background_tasks is not None:
        background_tasks.add_task(execute_document_pipeline, document_id)
        return

    try:
        process_document_celery.delay(document_id)
    except Exception:
        # Fallback if Redis is not running locally
        execute_document_pipeline(document_id)
