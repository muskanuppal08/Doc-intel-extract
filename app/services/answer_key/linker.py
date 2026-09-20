"""Question and answer key association engine with fuzzy matching and validation."""

import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.enums import AnswerMatchStatus, WarningSeverity, RelationshipType
from app.services.extractor.base import (
    ExtractedAnswerDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)
from app.models.document import Document
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.relationship import DocumentRelationship
from app.models.extraction_warning import ExtractionWarning


class AnswerKeyLinker:
    @staticmethod
    def clean_identifier(qid: Optional[str]) -> str:
        """
        Normalize question identifiers for fuzzy matching.
        e.g., 'Q1.' -> '1', 'Question 2(b)' -> '2(B)', '12)' -> '12'
        """
        if not qid:
            return ""
        clean = re.sub(r"^(?:Question|Q)\.?\s*", "", qid.strip(), flags=re.IGNORECASE)
        clean = clean.strip(".:)= \t")
        return clean.upper()

    @staticmethod
    def link_answers(
        questions: List[ExtractedQuestionDTO],
        answers: List[ExtractedAnswerDTO],
    ) -> Tuple[List[ExtractedQuestionDTO], List[ExtractedAnswerDTO], List[ExtractionWarningDTO]]:
        """
        Associate parsed answers to extracted questions by matching normalized identifiers.
        Performs validation against available options to prevent silent mismatches.
        """
        warnings: List[ExtractionWarningDTO] = []
        q_map: Dict[str, ExtractedQuestionDTO] = {}

        # Index questions by normalized identifier
        for q in questions:
            norm_id = AnswerKeyLinker.clean_identifier(q.question_number)
            if norm_id:
                q_map[norm_id] = q

        matched_answer_qids = set()

        for ans in answers:
            ans_norm_id = AnswerKeyLinker.clean_identifier(ans.question_identifier)
            target_question = q_map.get(ans_norm_id)

            if not target_question:
                # Answer without a matching question in the paper
                ans.match_status = AnswerMatchStatus.UNMATCHED
                warnings.append(
                    ExtractionWarningDTO(
                        warning_code="UNMATCHED_ANSWER_KEY",
                        message=(
                            f"Answer key found for Question '{ans.question_identifier}' "
                            f"({ans.normalized_answer}), but no corresponding question was extracted."
                        ),
                        severity=WarningSeverity.INFO,
                        source_page=ans.source_page,
                        question_identifier=ans.question_identifier,
                    )
                )
                continue

            # Question found: validate whether answer is plausible
            valid_keys = [o.key.upper() for o in target_question.options]

            if valid_keys and ans.normalized_answer not in valid_keys:
                # E.g. Answer key says 'E', but question only has choices A, B, C, D
                ans.match_status = AnswerMatchStatus.AMBIGUOUS
                warnings.append(
                    ExtractionWarningDTO(
                        warning_code="CONFLICTING_ANSWER",
                        message=(
                            f"Question '{target_question.question_number}' has options {valid_keys}, "
                            f"but answer key specifies '{ans.normalized_answer}'."
                        ),
                        severity=WarningSeverity.WARNING,
                        source_page=ans.source_page,
                        question_identifier=target_question.question_number,
                    )
                )
            else:
                ans.match_status = AnswerMatchStatus.MATCHED
                matched_answer_qids.add(ans_norm_id)

        # Identify questions missing answers
        for norm_id, q in q_map.items():
            if norm_id not in matched_answer_qids and q.options:
                warnings.append(
                    ExtractionWarningDTO(
                        warning_code="MISSING_ANSWER_KEY",
                        message=f"No answer key found for multiple choice Question '{q.question_number}'.",
                        severity=WarningSeverity.INFO,
                        source_page=q.source_pages[0] if q.source_pages else None,
                        question_identifier=q.question_number,
                    )
                )

        return questions, answers, warnings

    @staticmethod
    def link_documents_in_db(
        db: Session,
        question_doc_id: str,
        answer_doc_id: str,
        relationship_type: RelationshipType = RelationshipType.ANSWER_KEY_FOR,
    ) -> int:
        """
        Perform cross-document association between a question paper and separate answer key document.
        Links Question records to AnswerKey records in PostgreSQL.
        Returns: number of matched answers.
        """
        # 1. Create or get DocumentRelationship
        existing_rel = (
            db.query(DocumentRelationship)
            .filter(
                DocumentRelationship.source_document_id == question_doc_id,
                DocumentRelationship.target_document_id == answer_doc_id,
            )
            .first()
        )
        if not existing_rel:
            rel = DocumentRelationship(
                source_document_id=question_doc_id,
                target_document_id=answer_doc_id,
                relationship_type=relationship_type,
            )
            db.add(rel)

        # 2. Match questions and answers
        questions = db.query(Question).filter(Question.document_id == question_doc_id).all()
        answers = db.query(AnswerKey).filter(AnswerKey.source_document_id == answer_doc_id).all()

        q_map: Dict[str, Question] = {
            AnswerKeyLinker.clean_identifier(q.question_number): q
            for q in questions
            if q.question_number
        }

        matched_count = 0
        for ans in answers:
            ans_clean = AnswerKeyLinker.clean_identifier(ans.question_identifier)
            matched_q = q_map.get(ans_clean)

            if matched_q:
                ans.question_id = matched_q.id
                ans.match_status = AnswerMatchStatus.MATCHED
                matched_count += 1
            else:
                ans.match_status = AnswerMatchStatus.UNMATCHED

        db.commit()
        return matched_count


answer_linker = AnswerKeyLinker()
