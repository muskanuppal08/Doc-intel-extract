"""Answer key parser handling list, table, and explanation formats."""

import re
from typing import Dict, List, Optional, Tuple
from app.models.enums import AnswerMatchStatus
from app.services.extractor.base import ExtractedAnswerDTO

# Regex for standard answer key lines:
# e.g., "1. A", "1. (B)", "Q1: C", "Question 1 = D", "1 - True", "1) False"
ANSWER_LINE_RE = re.compile(
    r"(?:^|\n)\s*(?:Q(?:uestion)?\.?\s*)?(\d+[a-zA-Z]?)\s*[\.\:\-\=\)]\s*\(?([A-Da-d]|[1-4]|True|False)\)?(?:\s*[\-\–\:]\s*(.+))?",
    re.IGNORECASE,
)

# Regex for grid/table rows:
# e.g., "1 | A | 2 | B | 3 | C" or "1: A   2: B   3: C"
GRID_PAIR_RE = re.compile(
    r"(?:^|\s+|\|)(?:Q)?(\d+[a-zA-Z]?)\s*[\:\.\-\|\s]\s*\(?([A-Da-d]|[1-4]|True|False)\)?",
    re.IGNORECASE,
)


class AnswerKeyParser:
    @staticmethod
    def normalize_answer_value(raw_val: str) -> str:
        """Normalize answer values: (b) -> B, true -> TRUE."""
        val = raw_val.strip().strip("()").strip(".")
        val_upper = val.upper()
        if val_upper in ("TRUE", "FALSE"):
            return val_upper
        return val_upper

    @staticmethod
    def parse_from_text(
        text: str,
        source_page: Optional[int] = None,
    ) -> List[ExtractedAnswerDTO]:
        """
        Parse answer keys from text content.
        Supports:
        1. Numbered lists with optional explanations
        2. Horizontal grid tables (e.g. 1|A|2|B|3|C)
        """
        answers: List[ExtractedAnswerDTO] = []
        seen_qids = set()

        # 1. Try standard numbered lines with possible explanations
        for match in ANSWER_LINE_RE.finditer(text):
            qid = match.group(1).strip()
            raw_val = match.group(2).strip()
            explanation = match.group(3).strip() if match.group(3) else None

            if qid not in seen_qids:
                seen_qids.add(qid)
                norm = AnswerKeyParser.normalize_answer_value(raw_val)
                answers.append(
                    ExtractedAnswerDTO(
                        question_identifier=qid,
                        raw_answer_text=match.group(0).strip(),
                        normalized_answer=norm,
                        explanation=explanation,
                        source_page=source_page,
                        confidence_score=0.98 if explanation else 0.95,
                        match_status=AnswerMatchStatus.UNMATCHED,
                    )
                )

        # 2. If standard line parser found few/no answers, attempt grid pattern
        if len(answers) < 2:
            grid_answers: List[ExtractedAnswerDTO] = []
            for match in GRID_PAIR_RE.finditer(text):
                qid = match.group(1).strip()
                raw_val = match.group(2).strip()
                if qid not in seen_qids:
                    seen_qids.add(qid)
                    norm = AnswerKeyParser.normalize_answer_value(raw_val)
                    grid_answers.append(
                        ExtractedAnswerDTO(
                            question_identifier=qid,
                            raw_answer_text=match.group(0).strip(),
                            normalized_answer=norm,
                            source_page=source_page,
                            confidence_score=0.92,
                            match_status=AnswerMatchStatus.UNMATCHED,
                        )
                    )
            if len(grid_answers) > len(answers):
                answers = grid_answers

        return answers


answer_parser = AnswerKeyParser()
