"""Individual question endpoints for inspection and reviewer resolution."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.question import Question
from app.models.enums import ReviewStatus, UserRole
from app.schemas.question import QuestionDetailRead

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/{question_id}", response_model=QuestionDetailRead)
def get_question_detail(
    question_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve complete question details including diagram crops, raw extraction, and warnings."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    # Verify authorization through document ownership or reviewer role
    if question.document.owner_id != current_user.id and current_user.role.value not in ("admin", "reviewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return question


@router.post("/{question_id}/resolve", response_model=QuestionDetailRead)
def resolve_question_review(
    question_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: Session = Depends(get_db),
):
    """Mark a flagged question as reviewed and resolved by an authorized reviewer/admin."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    question.review_status = ReviewStatus.RESOLVED

    # Mark associated warnings as dismissed
    for w in question.warnings:
        w.is_dismissed = True

    db.commit()
    db.refresh(question)
    return question
