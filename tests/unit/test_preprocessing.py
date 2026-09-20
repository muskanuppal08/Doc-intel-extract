"""Unit tests for document preprocessing, rasterization, and image enhancement."""

from pathlib import Path
import pytest
from PIL import Image
import pymupdf

from app.services.preprocessing.cropper import region_cropper
from app.services.preprocessing.normalizer import normalizer
from app.services.preprocessing.preprocessor import preprocessor


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Create a minimal 2-page PDF file with text for testing."""
    pdf_path = tmp_path / "sample_two_pages.pdf"
    doc = pymupdf.open()

    page1 = doc.new_page()
    page1.insert_text((50, 72), "Sample Exam Page 1 Content with sufficient characters to pass the heuristic test.")

    page2 = doc.new_page()
    page2.insert_text((50, 72), "Sample Exam Page 2 Content continuing the examination questions clearly.")

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_image_normalizer_enhance():
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    enhanced = normalizer.enhance_for_ocr(img)
    assert enhanced.mode == "L"
    assert enhanced.size == (200, 200)

    binarized = normalizer.binarize_adaptive(enhanced)
    assert binarized.size == (200, 200)


def test_region_cropper():
    img = Image.new("RGB", (300, 400), color="white")
    cropped = region_cropper.crop_box(img, [10, 20, 110, 120])
    assert cropped.size == (100, 100)

    # Test out-of-bounds clamping
    clamped = region_cropper.crop_box(img, [-50, -50, 500, 600])
    assert clamped.size == (300, 400)


def test_document_preprocessor_inspect_and_rasterize(sample_pdf):
    inspection = preprocessor.inspect_document(sample_pdf)
    assert inspection.is_pdf is True
    assert inspection.page_count == 2
    assert inspection.is_digital_pdf is True

    # Rasterize page 1
    raster_img = preprocessor.rasterize_page(sample_pdf, page_number=1, dpi=100)
    assert isinstance(raster_img, Image.Image)
    assert raster_img.width > 0
    assert raster_img.height > 0
