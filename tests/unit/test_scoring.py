"""Unit tests for confidence scoring and review classification rules."""

import pytest
from app.models.enums import QuestionType, ReviewStatus, AnswerMatchStatus
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
)
from app.services.scoring.calculator import confidence_calculator
from app.services.scoring.validator import extraction_validator


def test_confidence_calculator_high_quality_mcq():
    options = [
        ExtractedOptionDTO(key="A", text="Option A"),
        ExtractedOptionDTO(key="B", text="Option B"),
        ExtractedOptionDTO(key="C", text="Option C"),
        ExtractedOptionDTO(key="D", text="Option D"),
    ]
    score = confidence_calculator.compute_question_confidence(
        stem="What is the unit of electrical resistance in SI system?",
        options=options,
        question_type=QuestionType.MULTIPLE_CHOICE,
        source_pages=[1],
        has_matched_answer=True,
    )
    assert score >= 0.90


def test_confidence_calculator_degraded_question():
    options = [
        ExtractedOptionDTO(key="A", text="5 N"),
    ]
    score = confidence_calculator.compute_question_confidence(
        stem="Find force at... [unreadable]",
        options=options,
        question_type=QuestionType.MULTIPLE_CHOICE,
        source_pages=[1],
        has_matched_answer=False,
    )
    assert score < 0.60


def test_validator_assigns_statuses():
    # 1. High quality question -> CONFIDENT
    q_good = ExtractedQuestionDTO(
        question_number="1",
        question_text="Which planet is known as the Red Planet in our solar system?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[
            ExtractedOptionDTO(key="A", text="Venus"),
            ExtractedOptionDTO(key="B", text="Mars"),
            ExtractedOptionDTO(key="C", text="Jupiter"),
            ExtractedOptionDTO(key="D", text="Saturn"),
        ],
        source_pages=[1],
    )

    # 2. Missing options -> PARTIAL_EXTRACTION
    q_partial = ExtractedQuestionDTO(
        question_number="2",
        question_text="Which of the following is an inert gas?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[ExtractedOptionDTO(key="A", text="Helium")],  # Only 1 option!
        source_pages=[1],
    )

    # 3. Degraded scan text with low confidence -> NEEDS_REVIEW
    q_review = ExtractedQuestionDTO(
        question_number="3",
        question_text="Calculate the magnetic field at center of loop [blurred] with current I.",
        question_type=QuestionType.SUBJECTIVE,
        options=[],
        source_pages=[1],
    )

    # Answer for question 1
    ans1 = ExtractedAnswerDTO(
        question_identifier="1",
        raw_answer_text="1. B",
        normalized_answer="B",
        match_status=AnswerMatchStatus.MATCHED,
    )

    questions, warnings = extraction_validator.validate_and_score_questions(
        [q_good, q_partial, q_review], [ans1]
    )

    assert q_good.review_status == ReviewStatus.CONFIDENT
    assert q_partial.review_status == ReviewStatus.PARTIAL_EXTRACTION
    assert q_review.review_status == ReviewStatus.NEEDS_REVIEW

    # Check warnings
    warning_codes = [w.warning_code for w in warnings]
    assert "MISSING_OPTIONS" in warning_codes
    assert "DEGRADED_TEXT" in warning_codes
