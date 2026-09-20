"""Human review queue API endpoints for auditing low-confidence and imperfect extractions."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.question import Question
from app.models.enums import ReviewStatus, UserRole
from app.schemas.question import QuestionDetailRead

router = APIRouter(prefix="/review-queue", tags=["Review Queue"])


@router.get("", response_model=List[QuestionDetailRead])
def get_review_queue(
    document_id: Optional[str] = Query(None, description="Optional document filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve all questions requiring human review (NEEDS_REVIEW or PARTIAL_EXTRACTION).
    Enables reviewers to audit low-confidence stems, ambiguous options, and orphan answers.
    """
    query = db.query(Question).filter(
        Question.review_status.in_([ReviewStatus.NEEDS_REVIEW, ReviewStatus.PARTIAL_EXTRACTION])
    )

    # Scoping: standard users only see their own questions, reviewers/admins see all
    if current_user.role == UserRole.USER:
        query = query.join(Question.document).filter(Question.document.has(owner_id=current_user.id))

    if document_id:
        query = query.filter(Question.document_id == document_id)

    flagged_questions = query.offset(skip).limit(limit).all()
    return flagged_questions
