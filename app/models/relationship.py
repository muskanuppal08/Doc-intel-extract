"""Document relationship model for multi-document associations."""

from sqlalchemy import Column, String, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import RelationshipType


class DocumentRelationship(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_relationships"

    source_document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type = Column(
        SQLEnum(RelationshipType, native_enum=False, length=50),
        default=RelationshipType.ANSWER_KEY_FOR,
        nullable=False,
    )
    extra_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    source_document = relationship(
        "Document",
        foreign_keys=[source_document_id],
        backref="outgoing_relationships",
    )
    target_document = relationship(
        "Document",
        foreign_keys=[target_document_id],
        backref="incoming_relationships",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "target_document_id",
            "relationship_type",
            name="uq_document_relationship",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentRelationship source={self.source_document_id} "
            f"target={self.target_document_id} type={self.relationship_type}>"
        )
