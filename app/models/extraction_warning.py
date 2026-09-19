"""Extraction warning and review flag model."""

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import WarningSeverity


class ExtractionWarning(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "extraction_warnings"

    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    warning_code = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(
        SQLEnum(WarningSeverity, native_enum=False, length=50),
        default=WarningSeverity.WARNING,
        nullable=False,
        index=True,
    )
    source_page = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True, default=dict)
    is_dismissed = Column(Boolean, default=False, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="warnings")
    question = relationship("Question", back_populates="warnings")

    def __repr__(self) -> str:
        return f"<ExtractionWarning code={self.warning_code} severity={self.severity}>"
