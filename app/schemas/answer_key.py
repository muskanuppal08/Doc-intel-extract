"""Answer key schemas for extraction and verification."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import AnswerMatchStatus


class AnswerKeyBase(BaseModel):
    question_identifier: str
    raw_answer_text: str
    normalized_answer: str
    explanation: Optional[str] = None
    source_page: Optional[int] = None
    confidence_score: float = 1.0
    match_status: AnswerMatchStatus = AnswerMatchStatus.UNMATCHED
    extra_metadata: Optional[Dict[str, Any]] = None


class AnswerKeyCreate(AnswerKeyBase):
    source_document_id: str
    question_id: Optional[str] = None


class AnswerKeyRead(AnswerKeyBase):
    id: str
    source_document_id: str
    question_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
