"""Unit tests for database models, relationships, and schema validations."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import (
    User,
    UserRole,
    Document,
    DocumentType,
    DocumentStatus,
    DocumentRelationship,
    RelationshipType,
    Question,
    QuestionType,
    ReviewStatus,
    QuestionOption,
    AnswerKey,
    AnswerMatchStatus,
    ExtractionWarning,
    WarningSeverity,
)
from app.schemas.question import QuestionRead
from app.schemas.document import DocumentRead


@pytest.fixture
def db_session():
    """In-memory SQLite database session for fast, isolated unit testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_user_creation(db_session):
    user = User(
        email="examiner@example.com",
        hashed_password="fakehashedpassword",
        full_name="Exam Creator",
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "examiner@example.com"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None


def test_document_and_questions_with_multipage_and_options(db_session):
    user = User(email="test@example.com", hashed_password="pwd", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    # Create Document
    doc = Document(
        owner_id=user.id,
        original_filename="Physics_Final_Exam.pdf",
        file_path="/storage/uploads/physics.pdf",
        file_hash="a"*64,
        file_size_bytes=1048576,
        mime_type="application/pdf",
        doc_type=DocumentType.QUESTION_PAPER,
        status=DocumentStatus.COMPLETED,
        page_count=5,
    )
    db_session.add(doc)
    db_session.commit()

    # Create Question spanning pages 1 and 2
    question = Question(
        document_id=doc.id,
        question_number="12",
        question_text="A projectile is launched from ground level at an angle of 45 degrees. Which of the following is true?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        source_pages=[1, 2],  # Question split across page 1 and page 2
        confidence_score=0.92,
        review_status=ReviewStatus.CONFIDENT,
    )
    db_session.add(question)
    db_session.commit()

    # Add Options
    opt_a = QuestionOption(
        question_id=question.id,
        option_key="A",
        option_text="Horizontal velocity remains constant in absence of air resistance",
        order_index=0,
    )
    opt_b = QuestionOption(
        question_id=question.id,
        option_key="B",
        option_text="Vertical acceleration changes sign at peak height",
        order_index=1,
    )
    db_session.add_all([opt_a, opt_b])
    db_session.commit()

    # Add associated Answer Key
    answer = AnswerKey(
        question_id=question.id,
        source_document_id=doc.id,
        question_identifier="12",
        raw_answer_text="Ans: A (Horizontal velocity remains constant)",
        normalized_answer="A",
        source_page=5,
        confidence_score=0.98,
        match_status=AnswerMatchStatus.MATCHED,
    )
    db_session.add(answer)
    db_session.commit()

    # Verify relationships
    db_session.refresh(doc)
    db_session.refresh(question)

    assert len(doc.questions) == 1
    assert question.source_pages == [1, 2]
    assert len(question.options) == 2
    assert question.options[0].option_key == "A"
    assert question.answer_key is not None
    assert question.answer_key.normalized_answer == "A"
    assert question.answer_key.match_status == AnswerMatchStatus.MATCHED

    # Test Pydantic serialization
    q_schema = QuestionRead.model_validate(question)
    assert q_schema.id == question.id
    assert q_schema.source_pages == [1, 2]
    assert len(q_schema.options) == 2
    assert q_schema.answer_key is not None
    assert q_schema.answer_key.normalized_answer == "A"


def test_document_relationship_linking(db_session):
    user = User(email="rel_user@example.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    doc_paper = Document(
        owner_id=user.id,
        original_filename="Question_Paper.pdf",
        file_path="/path/qp.pdf",
        file_hash="b"*64,
        file_size_bytes=500000,
        mime_type="application/pdf",
        doc_type=DocumentType.QUESTION_PAPER,
    )
    doc_key = Document(
        owner_id=user.id,
        original_filename="Answer_Key.pdf",
        file_path="/path/ak.pdf",
        file_hash="c"*64,
        file_size_bytes=200000,
        mime_type="application/pdf",
        doc_type=DocumentType.ANSWER_KEY,
    )
    db_session.add_all([doc_paper, doc_key])
    db_session.commit()

    rel = DocumentRelationship(
        source_document_id=doc_paper.id,
        target_document_id=doc_key.id,
        relationship_type=RelationshipType.ANSWER_KEY_FOR,
    )
    db_session.add(rel)
    db_session.commit()

    assert rel.id is not None
    assert rel.source_document.original_filename == "Question_Paper.pdf"
    assert rel.target_document.original_filename == "Answer_Key.pdf"
    assert rel.relationship_type == RelationshipType.ANSWER_KEY_FOR


def test_extraction_warning_and_review_flag(db_session):
    user = User(email="warning_test@example.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    doc = Document(
        owner_id=user.id,
        original_filename="Scanned_Exam.png",
        file_path="/path/scan.png",
        file_hash="d"*64,
        file_size_bytes=100000,
        mime_type="image/png",
        doc_type=DocumentType.QUESTION_PAPER,
        status=DocumentStatus.NEEDS_REVIEW,
    )
    db_session.add(doc)
    db_session.commit()

    question = Question(
        document_id=doc.id,
        question_number="5",
        question_text="Blurry stem text missing ending...",
        question_type=QuestionType.UNKNOWN,
        source_pages=[1],
        confidence_score=0.45,
        review_status=ReviewStatus.NEEDS_REVIEW,
    )
    db_session.add(question)
    db_session.commit()

    warning = ExtractionWarning(
        document_id=doc.id,
        question_id=question.id,
        warning_code="LOW_CONFIDENCE",
        message="Question stem has OCR confidence below 0.50 due to blur",
        severity=WarningSeverity.WARNING,
        source_page=1,
    )
    db_session.add(warning)
    db_session.commit()

    db_session.refresh(question)
    assert len(question.warnings) == 1
    assert question.warnings[0].warning_code == "LOW_CONFIDENCE"
    assert question.review_status == ReviewStatus.NEEDS_REVIEW
    assert question.confidence_score == 0.45
