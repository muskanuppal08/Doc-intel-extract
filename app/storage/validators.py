"""File validation utilities inspecting magic bytes and size limits."""

import os
from typing import Tuple
from fastapi import HTTPException, status
from app.core.config import settings

# Magic byte signatures
MAGIC_NUMBERS = {
    "application/pdf": [b"%PDF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
}


def sanitize_filename(filename: str) -> str:
    """Strip path traversal characters and return clean basename."""
    clean = filename.replace("\\", "/")
    clean = os.path.basename(clean)
    clean = clean.replace("\x00", "")
    return clean or "unnamed_document"


def validate_file_content_and_type(header_bytes: bytes, filename: str, file_size: int) -> str:
    """
    Validate file size and detect genuine MIME type using magic bytes.
    Prevents file spoofing attacks (e.g. malicious executable renamed to .pdf).
    """
    # 1. Size check
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)",
        )

    # 2. Magic byte check
    detected_mime = None
    for mime_type, signatures in MAGIC_NUMBERS.items():
        for sig in signatures:
            if header_bytes.startswith(sig):
                detected_mime = mime_type
                break
        if detected_mime:
            break

    if not detected_mime:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported or corrupted file type. Supported formats: PDF, PNG, JPG/JPEG.",
        )

    # 3. Check extension alignment
    clean_name = sanitize_filename(filename).lower()
    ext = clean_name.split(".")[-1] if "." in clean_name else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '.{ext}' is not permitted. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    return detected_mime
