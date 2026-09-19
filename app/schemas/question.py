"""Question and Option schemas conforming to platform-independent structure."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import QuestionType, ReviewStatus
from app.schemas.answer_key import AnswerKeyRead
from app.schemas.warning import ExtractionWarningRead


class QuestionOptionBase(BaseModel):
    option_key: str = Field(..., description="Option identifier e.g. A, B, C, D or (i)")
    option_text: str = Field(..., description="Text content of the option")
    diagram_path: Optional[str] = Field(None, description="Path or URL to option diagram crop")
    order_index: int = Field(0, description="Visual order of the option")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionRead(QuestionOptionBase):
    id: str
    question_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_number: Optional[str] = Field(None, description="Extracted question numbering e.g. '1', 'Q2'")
    question_text: str = Field(..., description="Question stem text (Markdown / LaTeX math supported)")
    question_type: QuestionType = Field(QuestionType.MULTIPLE_CHOICE, description="Classified question type")
    source_pages: List[int] = Field(default_factory=list, description="Page numbers originating this question")
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(default=None, description="Coordinates per page")
    diagram_paths: Optional[List[str]] = Field(default=None, description="Paths to cropped question figures/tables")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Calculated extraction reliability score")
    review_status: ReviewStatus = Field(ReviewStatus.CONFIDENT, description="Review classification state")


class QuestionCreate(QuestionBase):
    document_id: str
    options: List[QuestionOptionCreate] = Field(default_factory=list)


class QuestionRead(QuestionBase):
    """Structured question format consumable by any downstream assessment platform."""
    id: str
    document_id: str
    options: List[QuestionOptionRead] = Field(default_factory=list)
    answer_key: Optional[AnswerKeyRead] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionDetailRead(QuestionRead):
    """Detailed question response including reviewer warnings and raw extraction audit metadata."""
    warnings: List[ExtractionWarningRead] = Field(default_factory=list)
    raw_extraction: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
