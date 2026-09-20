"""Extraction validation and review flag evaluation rules."""

import re
from typing import List, Tuple
from app.core.config import settings
from app.models.enums import QuestionType, ReviewStatus, WarningSeverity
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)
from app.services.scoring.calculator import confidence_calculator


class ExtractionValidator:
    """
    Evaluates extracted questions against quality benchmarks,
    assigns review status, and attaches actionable reviewer warning items.
    """

    @staticmethod
    def validate_and_score_questions(
        questions: List[ExtractedQuestionDTO],
        answers: List[ExtractedAnswerDTO],
    ) -> Tuple[List[ExtractedQuestionDTO], List[ExtractionWarningDTO]]:
        """
        Calculates composite confidence for each question,
        assigns ReviewStatus, and creates audit warnings for human review.
        """
        all_warnings: List[ExtractionWarningDTO] = []
        ans_map = {a.question_identifier.strip().upper(): a for a in answers}

        for q in questions:
            qid = (q.question_number or "").strip().upper()
            matched_ans = ans_map.get(qid)
            has_matched = matched_ans is not None and matched_ans.match_status.value == "matched"

            # 1. Compute composite score
            score = confidence_calculator.compute_question_confidence(
                stem=q.question_text,
                options=q.options,
                question_type=q.question_type,
                source_pages=q.source_pages,
                has_matched_answer=has_matched,
            )
            q.confidence_score = score

            # Check for degraded scan markers
            has_artifacts = bool(
                re.search(r"\[unreadable\]|\[blurred\]", q.question_text, re.IGNORECASE)
            )

            # 2. Check for partial extraction
            is_mcq = q.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT)
            if is_mcq and len(q.options) < 2:
                q.review_status = ReviewStatus.PARTIAL_EXTRACTION
                all_warnings.append(
                    ExtractionWarningDTO(
                        warning_code="MISSING_OPTIONS",
                        message=f"Question '{q.question_number}' has only {len(q.options)} option(s) parsed.",
                        severity=WarningSeverity.WARNING,
                        source_page=q.source_pages[0] if q.source_pages else None,
                        question_identifier=q.question_number,
                    )
                )
            elif len(q.question_text.strip()) < 10 or q.question_text.rstrip().endswith("..."):
                q.review_status = ReviewStatus.PARTIAL_EXTRACTION
                all_warnings.append(
                    ExtractionWarningDTO(
                        warning_code="TRUNCATED_STEM",
                        message=f"Question '{q.question_number}' stem appears truncated or incomplete.",
                        severity=WarningSeverity.WARNING,
                        source_page=q.source_pages[0] if q.source_pages else None,
                        question_identifier=q.question_number,
                    )
                )
            # 3. Check for low confidence or degraded quality review
            elif score < settings.CONFIDENCE_THRESHOLD_REVIEW or has_artifacts:
                q.review_status = ReviewStatus.NEEDS_REVIEW
                warning_code = "DEGRADED_TEXT" if has_artifacts else "LOW_CONFIDENCE"
                all_warnings.append(
                    ExtractionWarningDTO(
                        warning_code=warning_code,
                        message=(
                            f"Question '{q.question_number}' requires human review "
                            f"(confidence: {score:.2f}, degraded_artifacts: {has_artifacts})."
                        ),
                        severity=WarningSeverity.WARNING,
                        source_page=q.source_pages[0] if q.source_pages else None,
                        question_identifier=q.question_number,
                    )
                )
            else:
                q.review_status = ReviewStatus.CONFIDENT

        return questions, all_warnings


extraction_validator = ExtractionValidator()
