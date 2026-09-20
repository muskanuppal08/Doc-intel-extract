"""Confidence scoring calculator applying multi-factor reliability heuristics."""

import re
from typing import List, Optional
from app.models.enums import QuestionType
from app.services.extractor.base import ExtractedOptionDTO


class ConfidenceCalculator:
    """
    Computes a composite extraction confidence score between 0.0 and 1.0
    based on stem completeness, option validity, layout consistency, and answer-key correlation.
    """

    @staticmethod
    def calculate_stem_score(stem: str) -> float:
        clean = stem.strip()
        if not clean:
            return 0.0

        length = len(clean)
        # Length score
        if length >= 25:
            len_score = 1.0
        elif length >= 15:
            len_score = 0.80
        else:
            len_score = 0.40

        # Punctuation check
        ends_properly = clean.endswith(("?", ".", ":", "!"))
        punct_score = 1.0 if ends_properly else 0.60

        # OCR Artifact / Truncation check
        has_artifacts = bool(
            re.search(r"\[unreadable\]|\[blurred\]|\.\.\.$", clean, re.IGNORECASE)
        )
        artifact_score = 0.40 if has_artifacts else 1.0

        return (len_score * 0.4) + (punct_score * 0.3) + (artifact_score * 0.3)

    @staticmethod
    def calculate_options_score(options: List[ExtractedOptionDTO], q_type: QuestionType) -> float:
        if q_type in (QuestionType.SUBJECTIVE, QuestionType.FILL_IN_THE_BLANK):
            return 1.0

        if q_type == QuestionType.TRUE_FALSE:
            if len(options) >= 2:
                return 1.0
            return 0.50 if len(options) == 1 else 0.10

        # Multiple choice / multiple select
        count = len(options)
        if count >= 4:
            base_score = 1.0
        elif count == 3:
            base_score = 0.80
        elif count == 2:
            base_score = 0.60
        elif count == 1:
            base_score = 0.20
        else:
            base_score = 0.0

        # Check option keys diversity (e.g. distinct A, B, C, D)
        keys = [o.key.upper() for o in options]
        is_distinct = len(keys) == len(set(keys))
        diversity_factor = 1.0 if is_distinct else 0.70

        return base_score * diversity_factor

    @staticmethod
    def calculate_layout_score(source_pages: List[int]) -> float:
        if not source_pages:
            return 0.50
        if len(source_pages) == 1:
            return 1.0
        # Multi-page question span
        return 0.90

    @classmethod
    def compute_question_confidence(
        cls,
        stem: str,
        options: List[ExtractedOptionDTO],
        question_type: QuestionType,
        source_pages: List[int],
        has_matched_answer: bool = False,
    ) -> float:
        """
        Weighted composite calculation:
        - 35% Question stem clarity and grammar
        - 35% Options count and consistency
        - 15% Layout and page provenance
        - 15% Answer-key verification
        """
        s_stem = cls.calculate_stem_score(stem)
        s_opt = cls.calculate_options_score(options, question_type)
        s_layout = cls.calculate_layout_score(source_pages)

        if has_matched_answer:
            s_ans = 1.0
        elif question_type in (QuestionType.SUBJECTIVE, QuestionType.FILL_IN_THE_BLANK):
            s_ans = 0.85
        else:
            s_ans = 0.40

        composite = (
            (0.35 * s_stem)
            + (0.35 * s_opt)
            + (0.15 * s_layout)
            + (0.15 * s_ans)
        )

        return round(max(0.10, min(1.0, composite)), 2)


confidence_calculator = ConfidenceCalculator()
