"""Pydantic schemas package initialization."""

from app.schemas.auth import Token, TokenPayload, LoginRequest
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserRead
from app.schemas.warning import ExtractionWarningRead
from app.schemas.answer_key import AnswerKeyBase, AnswerKeyCreate, AnswerKeyRead
from app.schemas.question import (
    QuestionOptionBase,
    QuestionOptionCreate,
    QuestionOptionRead,
    QuestionBase,
    QuestionCreate,
    QuestionRead,
    QuestionDetailRead,
)
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentRead,
    DocumentRelationshipCreate,
    DocumentRelationshipRead,
)

__all__ = [
    "Token",
    "TokenPayload",
    "LoginRequest",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "ExtractionWarningRead",
    "AnswerKeyBase",
    "AnswerKeyCreate",
    "AnswerKeyRead",
    "QuestionOptionBase",
    "QuestionOptionCreate",
    "QuestionOptionRead",
    "QuestionBase",
    "QuestionCreate",
    "QuestionRead",
    "QuestionDetailRead",
    "DocumentUploadResponse",
    "DocumentStatusResponse",
    "DocumentRead",
    "DocumentRelationshipCreate",
    "DocumentRelationshipRead",
]
