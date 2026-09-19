"""Unit tests for storage service, magic byte checking, and file sanitization."""

import io
from pathlib import Path
import pytest
from fastapi import HTTPException
from PIL import Image

from app.storage.validators import sanitize_filename, validate_file_content_and_type
from app.storage.service import StorageService


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("..\\windows\\system32\\exam.png") == "exam.png"
    assert sanitize_filename("my exam paper (1).pdf") == "my exam paper (1).pdf"
    assert sanitize_filename("") == "unnamed_document"


def test_validate_pdf_magic_bytes():
    valid_pdf = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj..."
    mime = validate_file_content_and_type(valid_pdf[:64], "exam.pdf", len(valid_pdf))
    assert mime == "application/pdf"


def test_validate_png_magic_bytes():
    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
    mime = validate_file_content_and_type(valid_png[:64], "scan.png", len(valid_png))
    assert mime == "image/png"


def test_validate_jpeg_magic_bytes():
    valid_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF..."
    mime = validate_file_content_and_type(valid_jpg[:64], "photo.jpg", len(valid_jpg))
    assert mime == "image/jpeg"


def test_reject_spoofed_file():
    # A shell script named as .pdf
    fake_pdf = b"#!/bin/bash\necho 'malicious'"
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content_and_type(fake_pdf, "evil.pdf", len(fake_pdf))
    assert exc_info.value.status_code == 415


def test_reject_empty_file():
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content_and_type(b"", "empty.pdf", 0)
    assert exc_info.value.status_code == 400


def test_storage_service_save_and_crop(tmp_path):
    storage = StorageService(upload_dir=tmp_path / "uploads", crops_dir=tmp_path / "crops")

    # Save upload
    pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n10\n%%EOF"
    file_stream = io.BytesIO(pdf_content)
    file_path, file_hash, size, mime = storage.save_upload(
        file_stream, "test_paper.pdf", user_id="user123"
    )

    assert Path(file_path).exists()
    assert size == len(pdf_content)
    assert mime == "application/pdf"
    assert len(file_hash) == 64

    # Save crop
    img = Image.new("RGB", (100, 100), color="blue")
    crop_path = storage.save_crop_image(img, "diag_q1")
    assert Path(crop_path).exists()

    # Clean up
    assert storage.delete_file(file_path) is True
    assert not Path(file_path).exists()
