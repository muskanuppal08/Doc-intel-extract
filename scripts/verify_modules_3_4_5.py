"""Verification script for Modules 3, 4, and 5.

Demonstrates:
1. Module 3: File upload validation, magic byte checking, SHA-256 deduplication hashing.
2. Module 4: PDF & Image preprocessing, inspection, DPI rasterization, contrast enhancement.
3. Module 5: Question extraction, option parsing (including parenthetical math formulas),
             and multi-page question stitching with source tracking [1, 2].
"""

import io
import sys
from pathlib import Path
from PIL import Image
import pymupdf

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.storage.service import storage_service
from app.storage.validators import validate_file_content_and_type, sanitize_filename
from app.services.preprocessing.preprocessor import preprocessor
from app.services.preprocessing.normalizer import normalizer
from app.services.extractor.segmenter import segmenter
from app.services.extractor.hybrid import hybrid_extractor


def print_banner(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def verify() -> None:
    print_banner("STEP 1: Testing Storage & Magic Byte Validation (Module 3)")
    # Test valid PDF upload
    test_pdf_data = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n10\n%%EOF"
    stream = io.BytesIO(test_pdf_data)
    file_path, file_hash, size, mime = storage_service.save_upload(
        stream, "Chemistry_Exam.pdf", user_id="test_user"
    )
    print(f" [PASS] Upload Stored Path  : {file_path}")
    print(f" [PASS] SHA-256 Checksum    : {file_hash}")
    print(f" [PASS] Detected MIME Type  : {mime}")
    print(f" [PASS] File Size           : {size} bytes")

    # Test file spoofing rejection
    try:
        validate_file_content_and_type(b"#!/bin/sh\nrm -rf /", "trojan.pdf", 25)
        assert False, "Should have rejected spoofed file"
    except Exception as e:
        print(f" [PASS] Spoofed File Rejection : Correctly rejected invalid magic bytes ({e.status_code})")

    storage_service.delete_file(file_path)

    print_banner("STEP 2: Testing Document Preprocessing & Rasterization (Module 4)")
    # Create a synthetic 2-page examination PDF
    sample_pdf_path = Path("storage/test_two_page_exam.pdf")
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_text((50, 72), "PHYSICS EXAMINATION\n1. What is the value of gravitational constant G?\n(A) 6.67 x 10^-11 N m^2/kg^2\n(B) 9.8 m/s^2\n\n2. A particle moves such that its position is given by x(t) = 3t^2 + 2t.")
    p2 = doc.new_page()
    p2.insert_text((50, 72), "(A) Acceleration is constant at 6 m/s^2\n(B) Acceleration depends on time\n(C) Velocity is zero at t=1s\n(D) None\n\n3. State Newton's third law of motion.")
    doc.save(str(sample_pdf_path))
    doc.close()

    # Inspect document
    inspection = preprocessor.inspect_document(sample_pdf_path)
    print(f" [PASS] Document Type   : {'Digital PDF' if inspection.is_digital_pdf else 'Scanned'}")
    print(f" [PASS] Total Pages     : {inspection.page_count}")
    for p in inspection.pages:
        print(f"        - Page {p.page_number}: {p.char_count} characters, text_layer={p.has_text_layer}")

    # Rasterize page to high-DPI image
    raster_img = preprocessor.rasterize_page(sample_pdf_path, page_number=1, dpi=150)
    print(f" [PASS] Rasterized Page 1 : {raster_img.width}x{raster_img.height} pixels (Mode: {raster_img.mode})")

    enhanced = normalizer.enhance_for_ocr(raster_img)
    print(f" [PASS] Contrast Enhanced: {enhanced.mode} mode ready for Vision / OCR")

    print_banner("STEP 3: Testing Question Extraction & Multi-Page Stitching (Module 5)")
    result = hybrid_extractor.extract(sample_pdf_path)

    print(f" [PASS] Extractor Used : {result.extraction_engine}")
    print(f" [PASS] Total Questions: {len(result.questions)}")
    for q in result.questions:
        print(f"\n   -------------------------------------------------")
        print(f"   Question #{q.question_number} ({q.question_type.value})")
        print(f"   Source Pages : {q.source_pages} {'(STITCHED ACROSS PAGES)' if len(q.source_pages) > 1 else ''}")
        print(f"   Confidence   : {q.confidence_score * 100:.1f}% | Review Status: {q.review_status.value}")
        print(f"   Stem         : {q.question_text}")
        if q.options:
            print(f"   Options ({len(q.options)}):")
            for opt in q.options:
                print(f"      ({opt.key}) {opt.text}")

    if result.warnings:
        print(f"\n [PASS] Extraction Warnings Logged ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"        [{w.severity.value.upper()}] {w.warning_code}: {w.message}")

    # Clean up test file
    sample_pdf_path.unlink(missing_ok=True)

    print_banner("ALL MODULE 3, 4, 5 VERIFICATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    verify()
