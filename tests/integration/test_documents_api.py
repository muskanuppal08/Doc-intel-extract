"""Integration tests for Documents, Questions, Reviews, and Multi-Document APIs."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import pymupdf

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enums import UserRole, DocumentType

client = TestClient(app)


@pytest.fixture
def auth_tokens():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        user = db.query(User).filter(User.role == UserRole.USER).first()
        reviewer = db.query(User).filter(User.role == UserRole.REVIEWER).first()

        return {
            "admin": create_access_token(admin.id, role="admin"),
            "user": create_access_token(user.id, role="user"),
            "reviewer": create_access_token(reviewer.id, role="reviewer"),
        }
    finally:
        db.close()


@pytest.fixture
def sample_pdf_bytes():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "GENERAL SCIENCE EXAMINATION\n\n"
        "1. What is the acceleration due to gravity on Earth?\n"
        "(A) 9.8 m/s^2\n"
        "(B) 1.6 m/s^2\n"
        "(C) 0 m/s^2\n"
        "(D) 25 m/s^2\n\n"
        "ANSWERS:\n"
        "1. A\n"
    )
    bytes_data = doc.tobytes()
    doc.close()
    return bytes_data


def test_upload_and_extract_flow(auth_tokens, sample_pdf_bytes):
    headers = {"Authorization": f"Bearer {auth_tokens['user']}"}

    # 1. Upload Document
    files = {"file": ("physics_exam.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    data = {"doc_type": "question_paper"}
    response = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)

    assert response.status_code == 202
    upload_res = response.json()
    assert "id" in upload_res
    doc_id = upload_res["id"]
    assert "tracking_url" in upload_res

    # 2. Check Status
    status_res = client.get(f"/api/v1/documents/{doc_id}/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] in ("completed", "needs_review", "extracting", "associating_answers")
    assert status_data["page_count"] >= 1

    # 3. Retrieve Questions
    q_res = client.get(f"/api/v1/documents/{doc_id}/questions", headers=headers)
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) >= 1
    assert questions[0]["question_number"] == "1"
    assert len(questions[0]["options"]) == 4

    # 4. Check Answer Key
    a_res = client.get(f"/api/v1/documents/{doc_id}/answers", headers=headers)
    assert a_res.status_code == 200
    answers = a_res.json()
    assert len(answers) >= 1
    assert answers[0]["normalized_answer"] == "A"


def test_upload_invalid_file(auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['user']}"}
    fake_file = io.BytesIO(b"#!/bin/sh\nrm -rf /")
    files = {"file": ("malicious.sh", fake_file, "text/plain")}

    response = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert response.status_code in (400, 415)


def test_review_queue_and_resolution(auth_tokens, sample_pdf_bytes):
    headers_user = {"Authorization": f"Bearer {auth_tokens['user']}"}
    headers_reviewer = {"Authorization": f"Bearer {auth_tokens['reviewer']}"}

    # Upload document
    files = {"file": ("review_test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/documents/upload", headers=headers_user, files=files)
    doc_id = res.json()["id"]

    # Query questions
    q_res = client.get(f"/api/v1/documents/{doc_id}/questions", headers=headers_user)
    question_id = q_res.json()[0]["id"]

    # Access single question detail
    detail_res = client.get(f"/api/v1/questions/{question_id}", headers=headers_user)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == question_id

    # Reviewer marks question as resolved
    resolve_res = client.post(f"/api/v1/questions/{question_id}/resolve", headers=headers_reviewer)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["review_status"] == "resolved"


def test_link_related_documents(auth_tokens, sample_pdf_bytes):
    headers = {"Authorization": f"Bearer {auth_tokens['user']}"}

    # Upload Doc 1: Question Paper
    files1 = {"file": ("paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res1 = client.post("/api/v1/documents/upload", headers=headers, files=files1, data={"doc_type": "question_paper"})
    doc1_id = res1.json()["id"]

    # Upload Doc 2: Answer Key
    files2 = {"file": ("key.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res2 = client.post("/api/v1/documents/upload", headers=headers, files=files2, data={"doc_type": "answer_key"})
    doc2_id = res2.json()["id"]

    # Link Doc 1 and Doc 2
    link_payload = {
        "source_document_id": doc1_id,
        "target_document_id": doc2_id,
        "relationship_type": "answer_key_for",
    }
    link_res = client.post("/api/v1/documents/link", headers=headers, json=link_payload)
    assert link_res.status_code == 201
    assert link_res.json()["source_document_id"] == doc1_id
    assert link_res.json()["target_document_id"] == doc2_id
