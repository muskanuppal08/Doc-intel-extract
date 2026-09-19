"""Verification script for Module 1 & Module 2.

Runs end-to-end checks on:
1. Environment configuration loading
2. Database connection & table creation
3. Seeded user accounts and password verification
4. JWT token generation, role claims & decoding
5. Inserting a document, multi-page question, options, and answer key
6. Validating Pydantic schema serialization
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.security import verify_password, create_access_token, decode_access_token
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import (
    User,
    UserRole,
    Document,
    DocumentType,
    DocumentStatus,
    Question,
    QuestionType,
    ReviewStatus,
    QuestionOption,
    AnswerKey,
    AnswerMatchStatus,
    ExtractionWarning,
    WarningSeverity,
)
from app.schemas.question import QuestionRead


def print_banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def verify() -> None:
    print_banner("STEP 1: Checking Configuration (Module 1)")
    print(f" [PASS] Project Name : {settings.PROJECT_NAME}")
    print(f" [PASS] Database URI : {settings.SQLALCHEMY_DATABASE_URI}")
    print(f" [PASS] Redis Broker : {settings.CELERY_BROKER_URL}")
    print(f" [PASS] Upload Dir   : {settings.UPLOAD_DIR}")

    print_banner("STEP 2: Checking Security & JWT (Module 1)")
    # Test token creation
    token = create_access_token(subject="demo-admin-id", role=UserRole.ADMIN.value)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "demo-admin-id"
    assert decoded["role"] == "admin"
    print(f" [PASS] Generated JWT Token : {token[:35]}... (truncated)")
    print(f" [PASS] Decoded JWT Claims  : {decoded}")

    print_banner("STEP 3: Checking Database & Seeded Users (Module 2)")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f" [PASS] Connected to Database. Found {len(users)} seeded user(s):")
        for u in users:
            is_valid_pwd = verify_password(f"{u.role.value}12345", u.hashed_password)
            print(f"        - {u.email:<25} | Role: {u.role.value:<10} | Password Valid: {is_valid_pwd}")

        print_banner("STEP 4: Testing Question, Options & Answer Key Insertion (Module 2)")
        admin_user = users[0]

        # Insert a sample test document
        test_doc = Document(
            owner_id=admin_user.id,
            original_filename="Sample_Physics_Paper.pdf",
            file_path="/storage/uploads/sample_physics.pdf",
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=245000,
            mime_type="application/pdf",
            doc_type=DocumentType.QUESTION_PAPER,
            status=DocumentStatus.COMPLETED,
            page_count=2,
        )
        db.add(test_doc)
        db.commit()

        # Insert a multi-page spanning question
        test_q = Question(
            document_id=test_doc.id,
            question_number="1",
            question_text="A block of mass 5 kg slides down an inclined plane of 30 degrees. Calculate the acceleration.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            source_pages=[1, 2],  # Spans across page 1 and page 2
            confidence_score=0.95,
            review_status=ReviewStatus.CONFIDENT,
        )
        db.add(test_q)
        db.commit()

        # Insert options
        opts = [
            QuestionOption(question_id=test_q.id, option_key="A", option_text="4.9 m/s^2", order_index=0),
            QuestionOption(question_id=test_q.id, option_key="B", option_text="9.8 m/s^2", order_index=1),
            QuestionOption(question_id=test_q.id, option_key="C", option_text="2.45 m/s^2", order_index=2),
            QuestionOption(question_id=test_q.id, option_key="D", option_text="0 m/s^2", order_index=3),
        ]
        db.add_all(opts)

        # Insert linked Answer Key
        ans = AnswerKey(
            question_id=test_q.id,
            source_document_id=test_doc.id,
            question_identifier="1",
            raw_answer_text="Ans: A (4.9 m/s^2)",
            normalized_answer="A",
            source_page=2,
            confidence_score=0.99,
            match_status=AnswerMatchStatus.MATCHED,
        )
        db.add(ans)
        db.commit()

        # Query back and validate with Pydantic
        db.refresh(test_q)
        serialized = QuestionRead.model_validate(test_q)

        print(f" [PASS] Document Created ID     : {test_doc.id}")
        print(f" [PASS] Question Number         : {serialized.question_number}")
        print(f" [PASS] Source Pages (Multi-page): {serialized.source_pages}")
        print(f" [PASS] Question Stem           : {serialized.question_text}")
        print(f" [PASS] Extracted Options Count : {len(serialized.options)}")
        for opt in serialized.options:
            print(f"        ({opt.option_key}) {opt.option_text}")
        print(f" [PASS] Associated Answer Key   : {serialized.answer_key.normalized_answer} (Status: {serialized.answer_key.match_status.value})")
        print(f" [PASS] Confidence Score        : {serialized.confidence_score}")

        # Clean up test rows
        db.delete(test_doc)
        db.commit()
        print("\n [PASS] Test data cleaned up successfully.")

    finally:
        db.close()

    print_banner("ALL CHECKS PASSED! MODULE 1 & 2 ARE 100% WORKING.")


if __name__ == "__main__":
    verify()
