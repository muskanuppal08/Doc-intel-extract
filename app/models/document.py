"""Document entity representing uploaded exam papers and answer keys."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import DocumentStatus, DocumentType


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    owner_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=False)

    doc_type = Column(
        SQLEnum(DocumentType, native_enum=False, length=50),
        default=DocumentType.UNKNOWN,
        nullable=False,
    )
    status = Column(
        SQLEnum(DocumentStatus, native_enum=False, length=50),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True,
    )

    page_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    owner = relationship("User", back_populates="documents")
    questions = relationship(
        "Question",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Question.question_number",
    )
    answer_keys = relationship(
        "AnswerKey",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    warnings = relationship(
        "ExtractionWarning",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.original_filename} status={self.status}>"
