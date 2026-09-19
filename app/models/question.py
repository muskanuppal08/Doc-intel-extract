"""Question model storing extracted structured examination questions."""

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import QuestionType, ReviewStatus


class Question(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "questions"

    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_number = Column(String(64), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(
        SQLEnum(QuestionType, native_enum=False, length=50),
        default=QuestionType.MULTIPLE_CHOICE,
        nullable=False,
    )

    # Source tracking: allows multi-page spans (e.g. [1, 2]) and coordinates
    source_pages = Column(JSON, nullable=False, default=list)
    bounding_boxes = Column(JSON, nullable=True, default=list)
    diagram_paths = Column(JSON, nullable=True, default=list)

    # Confidence and Quality Assessment
    confidence_score = Column(Float, nullable=False, default=1.0)
    review_status = Column(
        SQLEnum(ReviewStatus, native_enum=False, length=50),
        default=ReviewStatus.CONFIDENT,
        nullable=False,
        index=True,
    )
    raw_extraction = Column(JSON, nullable=True, default=dict)

    # Relationships
    document = relationship("Document", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order_index",
    )
    answer_key = relationship(
        "AnswerKey",
        back_populates="question",
        uselist=False,
    )
    warnings = relationship(
        "ExtractionWarning",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Question id={self.id} num={self.question_number} "
            f"type={self.question_type} conf={self.confidence_score}>"
        )
