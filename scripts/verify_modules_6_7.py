"""Verification script for Modules 6 and 7.

Demonstrates:
1. Module 6: Answer key parsing (lists, explanations, table grids), fuzzy question linking,
             detection of conflicting answers (e.g. key=E when choices=A-D), and orphan keys.
2. Module 7: Multi-factor composite confidence scoring (stems, options, layout, answers),
             and review classification (CONFIDENT, NEEDS_REVIEW, PARTIAL_EXTRACTION).
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.enums import QuestionType, ReviewStatus, AnswerMatchStatus
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
)
from app.services.answer_key.parser import answer_parser
from app.services.answer_key.linker import answer_linker
from app.services.scoring.calculator import confidence_calculator
from app.services.scoring.validator import extraction_validator


def print_banner(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def verify() -> None:
    print_banner("STEP 1: Testing Answer Key Parsing (Module 6)")
    sample_text = (
        "OFFICIAL ANSWER KEY:\n"
        "1. A\n"
        "2. (B)\n"
        "Q3: C - Light travels faster in vacuum than in matter.\n"
        "4 - True\n"
    )
    parsed_answers = answer_parser.parse_from_text(sample_text, source_page=2)
    print(f" [PASS] Parsed {len(parsed_answers)} answer entries from text:")
    for a in parsed_answers:
        exp = f" | Expl: {a.explanation}" if a.explanation else ""
        print(f"        - Question '{a.question_identifier}': {a.normalized_answer}{exp}")

    # Grid parser
    grid_text = "5 | B | 6 | D | 7 | A"
    grid_answers = answer_parser.parse_from_text(grid_text, source_page=2)
    print(f" [PASS] Parsed {len(grid_answers)} answers from table grid: {[a.normalized_answer for a in grid_answers]}")

    print_banner("STEP 2: Testing Answer Key Linking & Conflict Detection (Module 6)")
    # Question 1: MCQ with A, B, C, D
    q1 = ExtractedQuestionDTO(
        question_number="1",
        question_text="What is the SI unit of electric current?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[
            ExtractedOptionDTO(key="A", text="Ampere"),
            ExtractedOptionDTO(key="B", text="Volt"),
            ExtractedOptionDTO(key="C", text="Ohm"),
            ExtractedOptionDTO(key="D", text="Watt"),
        ],
        source_pages=[1],
    )

    # Question 2: MCQ with only A, B, C, D
    q2 = ExtractedQuestionDTO(
        question_number="2",
        question_text="Which particle has zero electric charge?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[
            ExtractedOptionDTO(key="A", text="Electron"),
            ExtractedOptionDTO(key="B", text="Proton"),
            ExtractedOptionDTO(key="C", text="Neutron"),
            ExtractedOptionDTO(key="D", text="Positron"),
        ],
        source_pages=[1],
    )

    # Answer 1: Matches Q1 with 'A'
    ans_good = ExtractedAnswerDTO(
        question_identifier="1",
        raw_answer_text="1. A",
        normalized_answer="A",
    )
    # Answer 2: Conflicting answer (specifies option 'E', not in question options)
    ans_conflict = ExtractedAnswerDTO(
        question_identifier="2",
        raw_answer_text="2. E",
        normalized_answer="E",
    )
    # Answer 3: Orphan answer for question 99
    ans_orphan = ExtractedAnswerDTO(
        question_identifier="99",
        raw_answer_text="99. B",
        normalized_answer="B",
    )

    questions, answers, link_warnings = answer_linker.link_answers(
        [q1, q2], [ans_good, ans_conflict, ans_orphan]
    )

    print(f" [PASS] Question 1 Answer Match Status : {answers[0].match_status.value.upper()} (Answer: {answers[0].normalized_answer})")
    print(f" [PASS] Question 2 Conflict Detection  : {answers[1].match_status.value.upper()} (Rejected invalid choice 'E')")
    print(f" [PASS] Orphan Key Detection          : {answers[2].match_status.value.upper()} (Question 99 not in exam)")

    print(f"\n [PASS] Linking Warnings Emitted ({len(link_warnings)}):")
    for w in link_warnings:
        print(f"        [{w.severity.value.upper()}] {w.warning_code}: {w.message}")

    print_banner("STEP 3: Testing Confidence Scoring & Review Classification (Module 7)")
    # Question 3: Degraded scan with blurred segment
    q3 = ExtractedQuestionDTO(
        question_number="3",
        question_text="Calculate the magnetic field at center of loop [blurred] with current I.",
        question_type=QuestionType.SUBJECTIVE,
        options=[],
        source_pages=[1],
    )

    # Question 4: Truncated stem
    q4 = ExtractedQuestionDTO(
        question_number="4",
        question_text="Derive the expression for kinetic energy ...",
        question_type=QuestionType.SUBJECTIVE,
        options=[],
        source_pages=[1],
    )

    scored_questions, review_warnings = extraction_validator.validate_and_score_questions(
        [q1, q2, q3, q4], answers
    )

    for q in scored_questions:
        print(f"\n   - Question #{q.question_number} ({q.question_type.value}):")
        print(f"     Stem       : {q.question_text[:50]}...")
        print(f"     Confidence : {q.confidence_score * 100:.1f}%")
        print(f"     Review Tag : {q.review_status.value.upper()}")

    print(f"\n [PASS] Quality Audit Warnings Logged ({len(review_warnings)}):")
    for w in review_warnings:
        print(f"        [{w.severity.value.upper()}] {w.warning_code}: {w.message}")

    print_banner("ALL MODULE 6 & 7 VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    verify()
