"""Document upload, status, and relationship schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import DocumentStatus, DocumentType, RelationshipType


class DocumentUploadResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    doc_type: DocumentType
    status: DocumentStatus
    message: str = "Document uploaded successfully and queued for processing"
    tracking_url: str


class DocumentStatusResponse(BaseModel):
    id: str
    original_filename: str
    doc_type: DocumentType
    status: DocumentStatus
    page_count: Optional[int] = None
    questions_extracted: int = 0
    answer_keys_found: int = 0
    warnings_count: int = 0
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime


class DocumentRead(BaseModel):
    id: str
    owner_id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    doc_type: DocumentType
    status: DocumentStatus
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRelationshipCreate(BaseModel):
    source_document_id: str = Field(..., description="ID of primary document (e.g. Question Paper)")
    target_document_id: str = Field(..., description="ID of associated document (e.g. Answer Key)")
    relationship_type: RelationshipType = Field(
        RelationshipType.ANSWER_KEY_FOR,
        description="Type of association between documents",
    )
    extra_metadata: Optional[Dict[str, Any]] = None


class DocumentRelationshipRead(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    relationship_type: RelationshipType
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
