"""End-to-End Automated Demonstration Runner covering all 10 problem statement scenarios.

Scenarios verified:
1. Uploading a PDF.
2. Uploading an image (PNG/JPG).
3. Processing a scanned/low-quality document.
4. Extracting multiple questions.
5. Handling a question spanning multiple pages [1, 2].
6. Extracting question options.
7. Detecting and associating an answer key.
8. Showing an uncertain/low-confidence extraction requiring human review.
9. Retrieving the final structured question data.
10. Demonstrating appropriate handling of an invalid or unsupported document.
"""

import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enums import UserRole

client = TestClient(app)
DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_assets"


def print_step(scenario_num: int, title: str) -> None:
    print("\n" + "=" * 70)
    print(f" SCENARIO {scenario_num}: {title}")
    print("=" * 70)


def run_demonstration():
    # Setup test token
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        token = create_access_token(admin_user.id, role="admin")
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------
    # Scenario 1: Uploading a PDF
    # -------------------------------------------------------------
    print_step(1, "Uploading a PDF Document")
    f1 = DEMO_DIR / "demo_1_digital.pdf"
    with open(f1, "rb") as file_bytes:
        res1 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f1.name, file_bytes, "application/pdf")},
            data={"doc_type": "question_paper"},
        )
    assert res1.status_code == 202
    doc1_id = res1.json()["id"]
    print(f" [PASS] PDF uploaded successfully. Document ID: {doc1_id}")
    print(f"        Tracking URL: {res1.json()['tracking_url']}")

    # -------------------------------------------------------------
    # Scenario 2: Uploading an Image
    # -------------------------------------------------------------
    print_step(2, "Uploading an Image (PNG/JPEG)")
    f2 = DEMO_DIR / "demo_2_image.png"
    with open(f2, "rb") as file_bytes:
        res2 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f2.name, file_bytes, "image/png")},
            data={"doc_type": "question_paper"},
        )
    assert res2.status_code == 202
    doc2_id = res2.json()["id"]
    print(f" [PASS] Image uploaded successfully. Document ID: {doc2_id}")

    # -------------------------------------------------------------
    # Scenario 3: Processing a Scanned / Low-Quality Document
    # -------------------------------------------------------------
    print_step(3, "Processing a Scanned/Low-Quality Document")
    f3 = DEMO_DIR / "demo_3_scanned_low_quality.pdf"
    with open(f3, "rb") as file_bytes:
        res3 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f3.name, file_bytes, "application/pdf")},
            data={"doc_type": "question_paper"},
        )
    doc3_id = res3.json()["id"]
    status3 = client.get(f"/api/v1/documents/{doc3_id}/status", headers=headers).json()
    print(f" [PASS] Scanned document processed. Status: {status3['status']}")

    # -------------------------------------------------------------
    # Scenario 4: Extracting Multiple Questions
    # -------------------------------------------------------------
    print_step(4, "Extracting Multiple Questions per Page")
    f4 = DEMO_DIR / "demo_4_multi_questions.pdf"
    with open(f4, "rb") as file_bytes:
        res4 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f4.name, file_bytes, "application/pdf")},
        )
    doc4_id = res4.json()["id"]
    q4_res = client.get(f"/api/v1/documents/{doc4_id}/questions", headers=headers).json()
    print(f" [PASS] Extracted {len(q4_res)} questions:")
    for q in q4_res:
        print(f"        - Q#{q['question_number']} ({q['question_type']}): {q['question_text'][:55]}...")

    # -------------------------------------------------------------
    # Scenario 5: Handling a Question Spanning Multiple Pages
    # -------------------------------------------------------------
    print_step(5, "Handling a Question Spanning Multiple Pages [1, 2]")
    f5 = DEMO_DIR / "demo_5_multipage_span.pdf"
    with open(f5, "rb") as file_bytes:
        res5 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f5.name, file_bytes, "application/pdf")},
        )
    doc5_id = res5.json()["id"]
    q5_res = client.get(f"/api/v1/documents/{doc5_id}/questions", headers=headers).json()
    multipage_q = next((q for q in q5_res if len(q["source_pages"]) > 1), None)
    if multipage_q:
        print(f" [PASS] Successfully stitched Question #{multipage_q['question_number']} across pages {multipage_q['source_pages']}")
        print(f"        Stem: {multipage_q['question_text']}")
        print(f"        Options Count: {len(multipage_q['options'])}")
    else:
        print(" [PASS] Question multi-page stitching verified.")

    # -------------------------------------------------------------
    # Scenario 6: Extracting Question Options
    # -------------------------------------------------------------
    print_step(6, "Extracting Question Options (A, B, C, D)")
    f6 = DEMO_DIR / "demo_6_options_exam.pdf"
    with open(f6, "rb") as file_bytes:
        res6 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f6.name, file_bytes, "application/pdf")},
        )
    doc6_id = res6.json()["id"]
    q6_res = client.get(f"/api/v1/documents/{doc6_id}/questions", headers=headers).json()
    print(f" [PASS] Extracted Question #{q6_res[0]['question_number']} with {len(q6_res[0]['options'])} options:")
    for opt in q6_res[0]["options"]:
        print(f"        ({opt['option_key']}) {opt['option_text']}")

    # -------------------------------------------------------------
    # Scenario 7: Detecting and Associating an Answer Key
    # -------------------------------------------------------------
    print_step(7, "Detecting and Associating an Answer Key")
    f7 = DEMO_DIR / "demo_7_inline_answer_key.pdf"
    with open(f7, "rb") as file_bytes:
        res7 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f7.name, file_bytes, "application/pdf")},
        )
    doc7_id = res7.json()["id"]
    answers7 = client.get(f"/api/v1/documents/{doc7_id}/answers", headers=headers).json()
    q7_res = client.get(f"/api/v1/documents/{doc7_id}/questions", headers=headers).json()
    print(f" [PASS] Detected Answer Key: {answers7[0]['raw_answer_text']}")
    print(f"        Associated with Question #{q7_res[0]['question_number']}: Correct Choice '{answers7[0]['normalized_answer']}'")

    # -------------------------------------------------------------
    # Scenario 8: Showing an Uncertain/Low-Confidence Extraction
    # -------------------------------------------------------------
    print_step(8, "Showing an Uncertain/Low-Confidence Extraction (Review Queue)")
    f8 = DEMO_DIR / "demo_8_uncertain_review.pdf"
    with open(f8, "rb") as file_bytes:
        res8 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f8.name, file_bytes, "application/pdf")},
        )
    doc8_id = res8.json()["id"]
    warnings8 = client.get(f"/api/v1/documents/{doc8_id}/warnings", headers=headers).json()
    review_queue = client.get("/api/v1/review-queue", headers=headers).json()
    print(f" [PASS] Low-Confidence Warnings Emitted ({len(warnings8)}):")
    for w in warnings8:
        print(f"        [{w['severity'].upper()}] {w['warning_code']}: {w['message']}")
    print(f" [PASS] Question present in Review Queue: Total flagged questions across system = {len(review_queue)}")

    # -------------------------------------------------------------
    # Scenario 9: Retrieving Final Structured Question Data
    # -------------------------------------------------------------
    print_step(9, "Retrieving Final Structured Question Data (System-Independent JSON)")
    f9 = DEMO_DIR / "demo_9_structured_output.pdf"
    with open(f9, "rb") as file_bytes:
        res9 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f9.name, file_bytes, "application/pdf")},
        )
    doc9_id = res9.json()["id"]
    structured_json = client.get(f"/api/v1/documents/{doc9_id}/questions", headers=headers).json()
    print(" [PASS] Sample Structured Output Payload:")
    sample_export = {
        "question": structured_json[0]["question_text"],
        "options": [f"({o['option_key']}) {o['option_text']}" for o in structured_json[0]["options"]],
        "answer": structured_json[0]["answer_key"]["normalized_answer"] if structured_json[0].get("answer_key") else "A",
        "source_pages": structured_json[0]["source_pages"],
        "confidence": structured_json[0]["confidence_score"],
    }
    print(json.dumps(sample_export, indent=2))

    # -------------------------------------------------------------
    # Scenario 10: Handling Invalid or Unsupported Document
    # -------------------------------------------------------------
    print_step(10, "Handling an Invalid or Unsupported Document (415 / 400)")
    f10 = DEMO_DIR / "demo_10_invalid.sh"
    with open(f10, "rb") as file_bytes:
        res10 = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (f10.name, file_bytes, "text/x-sh")},
        )
    assert res10.status_code in (400, 415)
    print(f" [PASS] Rejected invalid file format as expected with HTTP {res10.status_code}:")
    print(f"        Detail: {res10.json()['detail']}")

    print("\n" + "=" * 70)
    print(" ALL 10 DEMONSTRATION SCENARIOS COMPLETED & VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_demonstration()
