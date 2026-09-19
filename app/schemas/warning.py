"""Extraction warning and review item schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import WarningSeverity


class ExtractionWarningRead(BaseModel):
    id: str
    document_id: str
    question_id: Optional[str] = None
    warning_code: str
    message: str
    severity: WarningSeverity
    source_page: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    is_dismissed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
