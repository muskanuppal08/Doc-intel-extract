"""Question boundary segmenter, option parser, and multi-page stitching engine."""

import re
from typing import Dict, List, Optional, Tuple
from app.models.enums import QuestionType, ReviewStatus, WarningSeverity
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)

# Question number regex matching patterns:
# "1.", "Q1.", "Q.1", "Question 1:", "1)", "[1]", "12(a)"
QUESTION_NUM_RE = re.compile(
    r"(?:^|\n)\s*(?:Q(?:uestion)?\.?\s*(\d+[a-zA-Z]?)|(\d+[a-zA-Z]?)[\.\)\:-]|\[(\d+[a-zA-Z]?)\])\s*",
    re.IGNORECASE,
)

# Option patterns:
# (A) text, (B) text, A. text, a) text, (i) text
OPTION_MARKER_RE = re.compile(
    r"(?:^|\n|\s+)(?:\(([A-Da-d]|[1-4]|(?:[ivx]+))\)|([A-Da-d]|[1-4]|(?:[ivx]+))[\.\)])\s+",
    re.IGNORECASE,
)

# Inline Answer Key Section patterns
ANSWER_SECTION_RE = re.compile(
    r"(?:^|\n)\s*(?:ANSWER\s*KEY|ANSWERS|SOLUTIONS)\s*[:\n]",
    re.IGNORECASE,
)

ANSWER_PAIR_RE = re.compile(
    r"(?:Q(?:uestion)?\.?\s*)?(\d+[a-zA-Z]?)\s*[\.\:\-\=]\s*\(?([A-Da-d]|[1-4]|True|False)\)?",
    re.IGNORECASE,
)


class QuestionSegmenter:
    @staticmethod
    def classify_question_type(stem: str, options: List[ExtractedOptionDTO]) -> QuestionType:
        """Heuristic classification of examination question types."""
        stem_lower = stem.lower()

        if len(options) >= 2:
            opt_texts = [o.text.strip().lower() for o in options]
            if set(opt_texts) == {"true", "false"}:
                return QuestionType.TRUE_FALSE
            return QuestionType.MULTIPLE_CHOICE

        if "fill in the blank" in stem_lower or "____" in stem:
            return QuestionType.FILL_IN_THE_BLANK

        if "match the following" in stem_lower or ("column a" in stem_lower and "column b" in stem_lower):
            return QuestionType.MATCH_FOLLOWING

        return QuestionType.SUBJECTIVE

    @staticmethod
    def parse_options(text: str) -> Tuple[str, List[ExtractedOptionDTO]]:
        """
        Extract options from a question block using marker positions.
        Returns: (cleaned_stem, list_of_options)
        """
        matches = list(OPTION_MARKER_RE.finditer(text))
        if not matches:
            return text.strip(), []

        # Filter out false positives (e.g. single isolated letter in prose)
        first_key = (matches[0].group(1) or matches[0].group(2)).upper()
        if len(matches) < 2 and first_key not in ("A", "1"):
            return text.strip(), []

        first_match_start = matches[0].start()
        stem = text[:first_match_start].strip()

        options: List[ExtractedOptionDTO] = []
        for idx, m in enumerate(matches):
            key = (m.group(1) or m.group(2)).upper()
            start_pos = m.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            opt_text = text[start_pos:end_pos].strip()

            options.append(
                ExtractedOptionDTO(
                    key=key,
                    text=opt_text,
                    order_index=idx,
                    confidence_score=1.0,
                )
            )

        return stem, options

    @staticmethod
    def parse_answers_from_text(
        text: str,
        source_page: Optional[int] = None,
    ) -> List[ExtractedAnswerDTO]:
        """Parse standalone answer keys formatted as '1. A', 'Q2: B', '3 - C'."""
        answers: List[ExtractedAnswerDTO] = []
        for match in ANSWER_PAIR_RE.finditer(text):
            q_id = match.group(1)
            ans = match.group(2).upper()
            answers.append(
                ExtractedAnswerDTO(
                    question_identifier=q_id,
                    raw_answer_text=match.group(0).strip(),
                    normalized_answer=ans,
                    source_page=source_page,
                    confidence_score=0.95,
                )
            )
        return answers

    @staticmethod
    def segment_page_text(
        text: str,
        page_num: int,
    ) -> Tuple[List[ExtractedQuestionDTO], List[ExtractedAnswerDTO], Optional[str]]:
        """
        Segments text of a single page into questions.
        If an answer key section is found on the page, splits and extracts answers.
        Returns: (questions, answers, trailing_unclosed_question_text)
        """
        questions: List[ExtractedQuestionDTO] = []
        answers: List[ExtractedAnswerDTO] = []

        # Check if page contains an Answer Key section
        ans_match = ANSWER_SECTION_RE.search(text)
        if ans_match:
            body_text = text[:ans_match.start()]
            ans_text = text[ans_match.start():]
            answers.extend(QuestionSegmenter.parse_answers_from_text(ans_text, source_page=page_num))
        else:
            body_text = text

        # Find question boundaries
        matches = list(QUESTION_NUM_RE.finditer(body_text))
        if not matches:
            # Entire page might be a continuation of previous question
            return [], answers, body_text.strip()

        trailing_text = None
        for i, match in enumerate(matches):
            q_num = match.group(1) or match.group(2) or match.group(3)
            start_idx = match.end()
            end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)

            q_raw = body_text[start_idx:end_idx].strip()
            stem, options = QuestionSegmenter.parse_options(q_raw)
            q_type = QuestionSegmenter.classify_question_type(stem, options)

            # Heuristic: If last question on page has no options and ends abruptly without period,
            # it might span across to the next page
            if i == len(matches) - 1:
                is_incomplete = (
                    not options
                    and len(stem) > 10
                    and not stem.rstrip().endswith((".", "?", "!", ":"))
                )
                if is_incomplete:
                    trailing_text = f"__Q_START__{q_num}__ {stem}"
                    continue

            questions.append(
                ExtractedQuestionDTO(
                    question_number=q_num,
                    question_text=stem,
                    question_type=q_type,
                    options=options,
                    source_pages=[page_num],
                    confidence_score=0.92 if options or q_type == QuestionType.SUBJECTIVE else 0.75,
                    review_status=ReviewStatus.CONFIDENT if options or q_type == QuestionType.SUBJECTIVE else ReviewStatus.NEEDS_REVIEW,
                    raw_text=q_raw,
                )
            )

        return questions, answers, trailing_text

    @staticmethod
    def stitch_multipage_questions(
        pages_content: List[Tuple[int, str]],
    ) -> Tuple[List[ExtractedQuestionDTO], List[ExtractedAnswerDTO], List[ExtractionWarningDTO]]:
        """
        Stitch questions across pages when a question is split across page boundaries.
        Preserves source_pages=[N, N+1] for spanning questions.
        """
        all_questions: List[ExtractedQuestionDTO] = []
        all_answers: List[ExtractedAnswerDTO] = []
        warnings: List[ExtractionWarningDTO] = []

        pending_question: Optional[ExtractedQuestionDTO] = None

        for page_num, text in pages_content:
            if not text.strip():
                continue

            page_questions, page_answers, trailing = QuestionSegmenter.segment_page_text(text, page_num)
            all_answers.extend(page_answers)

            # If there was a pending question from previous page, resolve continuation
            if pending_question:
                # If first block of this page has options or text before the first new question
                first_match = QUESTION_NUM_RE.search(text)
                if first_match:
                    continuation_text = text[:first_match.start()].strip()
                else:
                    continuation_text = text.strip()

                if continuation_text:
                    # Check if continuation adds options or completes stem
                    cont_stem, cont_options = QuestionSegmenter.parse_options(continuation_text)
                    if cont_stem:
                        pending_question.question_text += " " + cont_stem
                    if cont_options:
                        pending_question.options.extend(cont_options)

                    pending_question.source_pages.append(page_num)
                    pending_question.question_type = QuestionSegmenter.classify_question_type(
                        pending_question.question_text,
                        pending_question.options,
                    )
                    pending_question.confidence_score = 0.90
                    pending_question.review_status = ReviewStatus.CONFIDENT

                    warnings.append(
                        ExtractionWarningDTO(
                            warning_code="QUESTION_SPAN_PAGES",
                            message=(
                                f"Question {pending_question.question_number} spans multiple pages: "
                                f"{pending_question.source_pages}"
                            ),
                            severity=WarningSeverity.INFO,
                            source_page=page_num,
                            question_identifier=pending_question.question_number,
                        )
                    )

                all_questions.append(pending_question)
                pending_question = None

            # Check if trailing text signals an incomplete question spanning to next page
            if trailing and trailing.startswith("__Q_START__"):
                match = re.match(r"__Q_START__(\d+[a-zA-Z]?)__\s*(.+)", trailing)
                if match:
                    q_num = match.group(1)
                    stem = match.group(2)
                    pending_question = ExtractedQuestionDTO(
                        question_number=q_num,
                        question_text=stem,
                        question_type=QuestionType.UNKNOWN,
                        options=[],
                        source_pages=[page_num],
                        confidence_score=0.70,
                        review_status=ReviewStatus.NEEDS_REVIEW,
                    )
            elif trailing:
                # General trailing text
                pass

            all_questions.extend(page_questions)

        if pending_question:
            # Trailing at the very end of document
            all_questions.append(pending_question)

        return all_questions, all_answers, warnings


segmenter = QuestionSegmenter()
