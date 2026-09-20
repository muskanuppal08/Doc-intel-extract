"""Digital PDF extractor using PyMuPDF for fast, native text and layout parsing."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf
from app.services.extractor.base import (
    BaseExtractor,
    ExtractionResultDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)
from app.services.extractor.segmenter import segmenter
from app.services.preprocessing.cropper import region_cropper
from app.storage.service import storage_service


class DigitalPDFExtractor(BaseExtractor):
    """Extracts questions and options directly from born-digital PDF text blocks."""

    def extract(self, file_path: Path, **kwargs) -> ExtractionResultDTO:
        path = Path(file_path)
        doc = pymupdf.open(str(path))
        page_count = len(doc)

        pages_content: List[Tuple[int, str]] = []
        diagram_map: Dict[int, List[str]] = {}

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Extract text
            page_text = page.get_text("text")
            pages_content.append((page_num, page_text))

            # 2. Extract any embedded diagrams
            try:
                embedded = region_cropper.extract_pdf_embedded_images(page)
                for img, _ in embedded:
                    crop_path = storage_service.save_crop_image(
                        img,
                        filename_prefix=f"p{page_num}_fig",
                    )
                    diagram_map.setdefault(page_num, []).append(crop_path)
            except Exception:
                pass

        doc.close()

        # Run multi-page stitching & option parsing
        questions, answers, warnings = segmenter.stitch_multipage_questions(pages_content)

        # Associate diagrams to questions on the same page
        for q in questions:
            for p in q.source_pages:
                if p in diagram_map and diagram_map[p]:
                    q.diagram_paths = diagram_map[p]

        return ExtractionResultDTO(
            questions=questions,
            answers=answers,
            warnings=warnings,
            page_count=page_count,
            extraction_engine="digital_pdf",
            metadata={"total_text_blocks": len(pages_content)},
        )


digital_extractor = DigitalPDFExtractor()
