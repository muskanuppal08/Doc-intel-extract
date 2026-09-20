"""Deterministic fixture-based extractor for reliable offline testing and demonstrations."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from app.models.enums import QuestionType, ReviewStatus, WarningSeverity
from app.services.extractor.base import (
    BaseExtractor,
    ExtractionResultDTO,
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)
from app.services.preprocessing.preprocessor import preprocessor


class MockExtractor(BaseExtractor):
    """
    Simulates high-fidelity extraction for standard test cases and offline evaluation.
    Guarantees reproducible extraction for all 10 demo requirements.
    """

    def extract(self, file_path: Path, **kwargs) -> ExtractionResultDTO:
        path = Path(file_path)
        name = path.name.lower()
        inspection = preprocessor.inspect_document(path)
        page_count = inspection.page_count

        questions: List[ExtractedQuestionDTO] = []
        answers: List[ExtractedAnswerDTO] = []
        warnings: List[ExtractionWarningDTO] = []

        # Scenario 1 & 4: Multi-question exam paper
        q1 = ExtractedQuestionDTO(
            question_number="1",
            question_text="What is the time complexity of searching in a balanced Binary Search Tree (BST)?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[
                ExtractedOptionDTO(key="A", text="O(1)", order_index=0),
                ExtractedOptionDTO(key="B", text="O(log n)", order_index=1),
                ExtractedOptionDTO(key="C", text="O(n)", order_index=2),
                ExtractedOptionDTO(key="D", text="O(n log n)", order_index=3),
            ],
            source_pages=[1],
            confidence_score=0.98,
            review_status=ReviewStatus.CONFIDENT,
        )
        questions.append(q1)

        # Scenario 5: Question spanning multiple pages (Pages 1 and 2)
        q2 = ExtractedQuestionDTO(
            question_number="2",
            question_text=(
                "Consider a relational database table with attributes (A, B, C, D) and functional dependencies "
                "{A -> B, B -> C, C -> D}. Decompose the relation into Boyce-Codd Normal Form (BCNF) "
                "and evaluate dependency preservation."
            ),
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[
                ExtractedOptionDTO(key="A", text="The decomposition is in BCNF and preserves all dependencies", order_index=0),
                ExtractedOptionDTO(key="B", text="The decomposition is in BCNF but does not preserve dependencies", order_index=1),
                ExtractedOptionDTO(key="C", text="The decomposition violates 3NF", order_index=2),
                ExtractedOptionDTO(key="D", text="None of the above", order_index=3),
            ],
            source_pages=[1, 2] if page_count > 1 else [1],
            confidence_score=0.91,
            review_status=ReviewStatus.CONFIDENT,
        )
        questions.append(q2)

        # Scenario 8: Low-confidence question requiring human review
        if "blurry" in name or "scan" in name or "low_quality" in name or "imperfect" in name:
            q_review = ExtractedQuestionDTO(
                question_number="3",
                question_text="Calcul... the electric field at point P due to charge Q = 5uC at distance ... [unreadable]",
                question_type=QuestionType.UNKNOWN,
                options=[
                    ExtractedOptionDTO(key="A", text="1.5 x 10^4 N/C", order_index=0),
                    ExtractedOptionDTO(key="B", text="[blurred text]", order_index=1),
                ],
                source_pages=[1],
                confidence_score=0.52,  # Low confidence < 0.80
                review_status=ReviewStatus.NEEDS_REVIEW,
            )
            questions.append(q_review)
            warnings.append(
                ExtractionWarningDTO(
                    warning_code="LOW_CONFIDENCE",
                    message="Question 3 has low OCR confidence (0.52) due to degraded scan quality.",
                    severity=WarningSeverity.WARNING,
                    source_page=1,
                    question_identifier="3",
                )
            )

        # Scenario 7: Answer Key Detection
        answers.append(
            ExtractedAnswerDTO(
                question_identifier="1",
                raw_answer_text="1. B (O(log n))",
                normalized_answer="B",
                source_page=page_count,
                confidence_score=0.99,
            )
        )
        answers.append(
            ExtractedAnswerDTO(
                question_identifier="2",
                raw_answer_text="2. A",
                normalized_answer="A",
                source_page=page_count,
                confidence_score=0.95,
            )
        )

        return ExtractionResultDTO(
            questions=questions,
            answers=answers,
            warnings=warnings,
            page_count=page_count,
            extraction_engine="mock_engine",
            metadata={"simulated": True},
        )


mock_extractor = MockExtractor()
