"""Base classes and typed Data Transfer Objects (DTOs) for question extraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.enums import QuestionType, ReviewStatus, WarningSeverity, AnswerMatchStatus


class ExtractedOptionDTO(BaseModel):
    key: str  # e.g., "A", "B", "1", "(i)"
    text: str
    diagram_path: Optional[str] = None
    order_index: int = 0
    confidence_score: float = 1.0


class ExtractedQuestionDTO(BaseModel):
    question_number: Optional[str] = None
    question_text: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: List[ExtractedOptionDTO] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    confidence_score: float = 1.0
    review_status: ReviewStatus = ReviewStatus.CONFIDENT
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    diagram_paths: Optional[List[str]] = None
    raw_text: Optional[str] = None


class ExtractedAnswerDTO(BaseModel):
    question_identifier: str
    raw_answer_text: str
    normalized_answer: str
    explanation: Optional[str] = None
    source_page: Optional[int] = None
    confidence_score: float = 1.0
    match_status: AnswerMatchStatus = AnswerMatchStatus.UNMATCHED


class ExtractionWarningDTO(BaseModel):
    warning_code: str
    message: str
    severity: WarningSeverity = WarningSeverity.WARNING
    source_page: Optional[int] = None
    question_identifier: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ExtractionResultDTO(BaseModel):
    questions: List[ExtractedQuestionDTO] = Field(default_factory=list)
    answers: List[ExtractedAnswerDTO] = Field(default_factory=list)
    warnings: List[ExtractionWarningDTO] = Field(default_factory=list)
    page_count: int = 0
    extraction_engine: str = "base"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseExtractor(ABC):
    """Abstract interface for all document extraction engines."""

    @abstractmethod
    def extract(self, file_path: Path, **kwargs) -> ExtractionResultDTO:
        """Extract structured questions, options, and answers from a document."""
        pass
