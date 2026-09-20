"""Question extraction module initialization."""

from app.services.extractor.base import (
    BaseExtractor,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
    ExtractedAnswerDTO,
    ExtractionWarningDTO,
    ExtractionResultDTO,
)
from app.services.extractor.segmenter import QuestionSegmenter, segmenter
from app.services.extractor.digital import DigitalPDFExtractor, digital_extractor
from app.services.extractor.vision import VisionAIExtractor, vision_extractor
from app.services.extractor.mock import MockExtractor, mock_extractor
from app.services.extractor.hybrid import HybridExtractor, hybrid_extractor

__all__ = [
    "BaseExtractor",
    "ExtractedOptionDTO",
    "ExtractedQuestionDTO",
    "ExtractedAnswerDTO",
    "ExtractionWarningDTO",
    "ExtractionResultDTO",
    "QuestionSegmenter",
    "segmenter",
    "DigitalPDFExtractor",
    "digital_extractor",
    "VisionAIExtractor",
    "vision_extractor",
    "MockExtractor",
    "mock_extractor",
    "HybridExtractor",
    "hybrid_extractor",
]
