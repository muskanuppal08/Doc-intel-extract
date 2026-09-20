"""Hybrid extractor orchestrator dynamically routing between digital and vision pipelines."""

from pathlib import Path
from typing import Any, Dict, Optional
from app.core.config import settings
from app.services.extractor.base import BaseExtractor, ExtractionResultDTO
from app.services.extractor.digital import digital_extractor
from app.services.extractor.mock import mock_extractor
from app.services.extractor.vision import vision_extractor
from app.services.preprocessing.preprocessor import preprocessor


class HybridExtractor(BaseExtractor):
    """
    Intelligent extraction orchestrator:
    1. Digital Fast Path: Born-digital PDFs are extracted directly via PyMuPDF (0ms API cost).
    2. Vision Fallback: Scanned documents, rotated images, or low-confidence pages route to Multimodal Vision AI.
    3. Mock Fallback: Configurable offline provider for CI/CD and zero-cost local demonstrations.
    """

    def extract(self, file_path: Path, **kwargs) -> ExtractionResultDTO:
        path = Path(file_path)
        engine_choice = settings.OCR_ENGINE.lower()

        # Direct override via settings
        if engine_choice == "mock":
            return mock_extractor.extract(path, **kwargs)
        if engine_choice == "digital":
            return digital_extractor.extract(path, **kwargs)
        if engine_choice == "vision_ai":
            return vision_extractor.extract(path, **kwargs)

        # Hybrid routing based on document inspection
        inspection = preprocessor.inspect_document(path)

        if inspection.is_digital_pdf:
            # Attempt digital extraction
            result = digital_extractor.extract(path, **kwargs)
            if len(result.questions) > 0:
                result.extraction_engine = "hybrid_digital"
                return result

        # If scanned PDF or single image:
        if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
            result = vision_extractor.extract(path, **kwargs)
            result.extraction_engine = "hybrid_vision"
            return result

        # Fallback to mock if no cloud credentials
        result = mock_extractor.extract(path, **kwargs)
        result.extraction_engine = "hybrid_mock_fallback"
        return result


hybrid_extractor = HybridExtractor()
