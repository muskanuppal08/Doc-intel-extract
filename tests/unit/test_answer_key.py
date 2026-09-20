"""Unit tests for answer key parsing, normalization, and question linking."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import (
    User,
    Document,
    Question,
    QuestionOption,
    AnswerKey,
    AnswerMatchStatus,
    DocumentRelationship,
    RelationshipType,
    QuestionType,
    ReviewStatus,
)
from app.services.answer_key.parser import answer_parser
from app.services.answer_key.linker import answer_linker
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
)


def test_answer_parser_standard_list():
    raw_text = (
        "ANSWERS:\n"
        "1. A\n"
        "2. (B)\n"
        "3 - C\n"
        "Q4: D - Because kinetic energy is proportional to velocity squared.\n"
        "5. True\n"
    )
    answers = answer_parser.parse_from_text(raw_text, source_page=3)

    assert len(answers) == 5
    assert answers[0].question_identifier == "1"
    assert answers[0].normalized_answer == "A"

    assert answers[1].question_identifier == "2"
    assert answers[1].normalized_answer == "B"

    assert answers[2].question_identifier == "3"
    assert answers[2].normalized_answer == "C"

    assert answers[3].question_identifier == "4"
    assert answers[3].normalized_answer == "D"
    assert "kinetic energy" in answers[3].explanation

    assert answers[4].question_identifier == "5"
    assert answers[4].normalized_answer == "TRUE"


def test_answer_parser_grid_format():
    grid_text = "1 | A | 2 | B | 3 | C | 4 | D"
    answers = answer_parser.parse_from_text(grid_text, source_page=1)

    assert len(answers) == 4
    assert [a.normalized_answer for a in answers] == ["A", "B", "C", "D"]


def test_answer_linker_matching_and_conflicts():
    # Question 1 has options A, B, C, D
    q1 = ExtractedQuestionDTO(
        question_number="1",
        question_text="Sample question 1?",
        options=[
            ExtractedOptionDTO(key="A", text="Option A"),
            ExtractedOptionDTO(key="B", text="Option B"),
            ExtractedOptionDTO(key="C", text="Option C"),
            ExtractedOptionDTO(key="D", text="Option D"),
        ],
    )

    # Question 2 has options A, B, C, D
    q2 = ExtractedQuestionDTO(
        question_number="Q2",
        question_text="Sample question 2?",
        options=[
            ExtractedOptionDTO(key="A", text="Option A"),
            ExtractedOptionDTO(key="B", text="Option B"),
        ],
    )

    # Answer 1 matches q1
    a1 = ExtractedAnswerDTO(
        question_identifier="1",
        raw_answer_text="1. B",
        normalized_answer="B",
    )

    # Answer 2 specifies option 'E', which does not exist in q2
    a2 = ExtractedAnswerDTO(
        question_identifier="2",
        raw_answer_text="2. E",
        normalized_answer="E",
    )

    # Answer 3 is an orphan answer (no Question 3)
    a3 = ExtractedAnswerDTO(
        question_identifier="99",
        raw_answer_text="99. A",
        normalized_answer="A",
    )

    questions, answers, warnings = answer_linker.link_answers([q1, q2], [a1, a2, a3])

    assert a1.match_status == AnswerMatchStatus.MATCHED
    assert a2.match_status == AnswerMatchStatus.AMBIGUOUS  # Option E doesn't exist
    assert a3.match_status == AnswerMatchStatus.UNMATCHED  # Question 99 missing

    warning_codes = [w.warning_code for w in warnings]
    assert "CONFLICTING_ANSWER" in warning_codes
    assert "UNMATCHED_ANSWER_KEY" in warning_codes


def test_database_cross_document_linking():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        user = User(email="test@pbnc.internal", hashed_password="pwd")
        db.add(user)
        db.commit()

        # Document 1: Question Paper
        doc_paper = Document(
            owner_id=user.id,
            original_filename="Exam_Paper.pdf",
            file_path="/uploads/exam.pdf",
            file_hash="1"*64,
            file_size_bytes=1000,
            mime_type="application/pdf",
        )
        # Document 2: Separate Answer Key
        doc_key = Document(
            owner_id=user.id,
            original_filename="Official_Key.pdf",
            file_path="/uploads/key.pdf",
            file_hash="2"*64,
            file_size_bytes=500,
            mime_type="application/pdf",
        )
        db.add_all([doc_paper, doc_key])
        db.commit()

        # Add questions to doc_paper
        q1 = Question(
            document_id=doc_paper.id,
            question_number="1",
            question_text="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
        )
        db.add(q1)

        # Add answers to doc_key
        ans1 = AnswerKey(
            source_document_id=doc_key.id,
            question_identifier="Q1",
            raw_answer_text="1. B (4)",
            normalized_answer="B",
        )
        db.add(ans1)
        db.commit()

        # Perform cross-document link
        matched_count = answer_linker.link_documents_in_db(
            db,
            question_doc_id=doc_paper.id,
            answer_doc_id=doc_key.id,
            relationship_type=RelationshipType.ANSWER_KEY_FOR,
        )

        assert matched_count == 1
        db.refresh(ans1)
        assert ans1.question_id == q1.id
        assert ans1.match_status == AnswerMatchStatus.MATCHED

        # Verify DocumentRelationship was recorded
        rel = db.query(DocumentRelationship).filter(
            DocumentRelationship.source_document_id == doc_paper.id,
            DocumentRelationship.target_document_id == doc_key.id,
        ).first()
        assert rel is not None
        assert rel.relationship_type == RelationshipType.ANSWER_KEY_FOR

    finally:
        db.close()
