"""Document inspection and high-resolution page rasterization service."""

import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
from pydantic import BaseModel
import pymupdf
from app.services.preprocessing.normalizer import normalizer


class PageMetadata(BaseModel):
    page_number: int  # 1-indexed
    width: float
    height: float
    has_text_layer: bool
    char_count: int
    image_count: int


class DocumentInspectionResult(BaseModel):
    is_pdf: bool
    page_count: int
    is_digital_pdf: bool  # True if native text layer exists across pages
    is_scanned: bool       # True if mostly image-based without selectable text
    pages: List[PageMetadata]


class DocumentPreprocessor:
    @staticmethod
    def inspect_document(file_path: Union[str, Path]) -> DocumentInspectionResult:
        """Analyze document structure, page count, and determine digital vs scanned nature."""
        path = Path(file_path)
        is_pdf = path.suffix.lower() == ".pdf"

        if is_pdf:
            try:
                doc = pymupdf.open(str(path))
                total_pages = len(doc)
                pages_meta = []
                total_chars = 0

                for i in range(total_pages):
                    page = doc[i]
                    text = page.get_text().strip()
                    char_count = len(text)
                    total_chars += char_count
                    images = page.get_images()

                    pages_meta.append(
                        PageMetadata(
                            page_number=i + 1,
                            width=page.rect.width,
                            height=page.rect.height,
                            has_text_layer=char_count > 40,
                            char_count=char_count,
                            image_count=len(images),
                        )
                    )

                avg_chars = total_chars / total_pages if total_pages > 0 else 0
                is_digital = avg_chars >= 50 or any(p.has_text_layer for p in pages_meta)
                is_scanned = not is_digital

                doc.close()
                return DocumentInspectionResult(
                    is_pdf=True,
                    page_count=total_pages,
                    is_digital_pdf=is_digital,
                    is_scanned=is_scanned,
                    pages=pages_meta,
                )
            except Exception:
                # Handle damaged or minimal mock PDF structures
                return DocumentInspectionResult(
                    is_pdf=True,
                    page_count=1,
                    is_digital_pdf=False,
                    is_scanned=True,
                    pages=[
                        PageMetadata(
                            page_number=1,
                            width=595.0,
                            height=842.0,
                            has_text_layer=False,
                            char_count=0,
                            image_count=0,
                        )
                    ],
                )

        # Single image file (PNG, JPG)
        with Image.open(str(path)) as img:
            w, h = img.size
            return DocumentInspectionResult(
                is_pdf=False,
                page_count=1,
                is_digital_pdf=False,
                is_scanned=True,
                pages=[
                    PageMetadata(
                        page_number=1,
                        width=float(w),
                        height=float(h),
                        has_text_layer=False,
                        char_count=0,
                        image_count=1,
                    )
                ],
            )

    @staticmethod
    def rasterize_page(
        file_path: Union[str, Path],
        page_number: int = 1,
        dpi: int = 200,
        enhance: bool = True,
    ) -> Image.Image:
        """
        Render a PDF page to a high-resolution PIL Image.
        If the file is already an image, load it directly.
        Optionally enhances contrast and orientation.
        """
        path = Path(file_path)
        if path.suffix.lower() != ".pdf":
            img = Image.open(str(path))
            if enhance:
                img = normalizer.enhance_for_ocr(img)
            return img

        doc = pymupdf.open(str(path))
        page_idx = max(0, min(page_number - 1, len(doc) - 1))
        page = doc[page_idx]

        # PyMuPDF zoom factor from default 72 DPI
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        if enhance:
            img = normalizer.fix_orientation(img)

        return img


preprocessor = DocumentPreprocessor()
