"""Answer key entity for storing answer information and association status."""

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import AnswerMatchStatus


class AnswerKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answer_keys"

    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_identifier = Column(String(64), nullable=False, index=True)
    raw_answer_text = Column(Text, nullable=False)
    normalized_answer = Column(String(256), nullable=False)
    explanation = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    match_status = Column(
        SQLEnum(AnswerMatchStatus, native_enum=False, length=50),
        default=AnswerMatchStatus.UNMATCHED,
        nullable=False,
        index=True,
    )
    extra_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    question = relationship("Question", back_populates="answer_key")
    source_document = relationship("Document", back_populates="answer_keys")

    def __repr__(self) -> str:
        return (
            f"<AnswerKey id={self.id} q_id={self.question_identifier} "
            f"norm={self.normalized_answer} status={self.match_status}>"
        )
