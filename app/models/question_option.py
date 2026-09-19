"""Question option model representing choices for multiple choice / select questions."""

from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin


class QuestionOption(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "question_options"

    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_key = Column(String(32), nullable=False)  # e.g., 'A', 'B', '1', '(iv)'
    option_text = Column(Text, nullable=False)
    diagram_path = Column(String(1024), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    extra_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    question = relationship("Question", back_populates="options")

    def __repr__(self) -> str:
        return f"<QuestionOption id={self.id} key={self.option_key}>"
