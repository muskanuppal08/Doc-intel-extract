"""Enums used across database models and API schemas."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    USER = "user"


class DocumentType(str, Enum):
    QUESTION_PAPER = "question_paper"
    ANSWER_KEY = "answer_key"
    COMBINED = "combined"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    EXTRACTING = "extracting"
    ASSOCIATING_ANSWERS = "associating_answers"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    SUBJECTIVE = "subjective"
    MATCH_FOLLOWING = "match_following"
    UNKNOWN = "unknown"


class ReviewStatus(str, Enum):
    CONFIDENT = "confident"
    NEEDS_REVIEW = "needs_review"
    PARTIAL_EXTRACTION = "partial_extraction"
    RESOLVED = "resolved"


class AnswerMatchStatus(str, Enum):
    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNMATCHED = "unmatched"


class RelationshipType(str, Enum):
    ANSWER_KEY_FOR = "answer_key_for"
    SUPPLEMENTARY_TO = "supplementary_to"
    SAME_EXAM = "same_exam"


class WarningSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
