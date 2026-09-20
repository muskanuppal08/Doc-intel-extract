"""Vision-Language Model (VLM) extractor using multimodal APIs for complex layouts and scans."""

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from PIL import Image

from app.core.config import settings
from app.models.enums import QuestionType, ReviewStatus, WarningSeverity
from app.services.extractor.base import (
    BaseExtractor,
    ExtractionResultDTO,
    ExtractedAnswerDTO,
    ExtractedOptionDTO,
    ExtractedQuestionDTO,
    ExtractionWarningDTO,
)
from app.services.preprocessing.preprocessor import preprocessor


SYSTEM_PROMPT = """You are an expert examination document processing system.
Extract all questions, options, diagrams, and answer keys from the provided document page(s).
Return ONLY a valid JSON object matching this schema:
{
  "questions": [
    {
      "question_number": "1",
      "question_text": "Question text in markdown or LaTeX for math...",
      "question_type": "multiple_choice", // multiple_choice, multiple_select, true_false, fill_in_the_blank, subjective, match_following
      "options": [
        {"key": "A", "text": "Option text..."},
        {"key": "B", "text": "Option text..."}
      ],
      "source_pages": [1],
      "confidence_score": 0.95
    }
  ],
  "answers": [
    {
      "question_identifier": "1",
      "raw_answer_text": "1 - A",
      "normalized_answer": "A",
      "source_page": 1,
      "confidence_score": 0.98
    }
  ],
  "warnings": [
    {
      "warning_code": "LOW_RESOLUTION",
      "message": "Page 1 has slight blur",
      "severity": "warning"
    }
  ]
}
If a question spans across multiple pages, include all pages in "source_pages" (e.g. [1, 2]).
Do not invent answers if missing. If uncertain about a question boundary or text, give confidence < 0.70.
"""


class VisionAIExtractor(BaseExtractor):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY

    def _image_to_base64(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def extract(self, file_path: Path, **kwargs) -> ExtractionResultDTO:
        """Process document images using Multimodal Vision API."""
        inspection = preprocessor.inspect_document(file_path)
        page_count = inspection.page_count

        if not self.api_key:
            # Fallback warning if external API key is not configured
            return ExtractionResultDTO(
                questions=[],
                answers=[],
                warnings=[
                    ExtractionWarningDTO(
                        warning_code="NO_API_KEY",
                        message="Vision AI API key not configured; falling back to offline extraction.",
                        severity=WarningSeverity.WARNING,
                    )
                ],
                page_count=page_count,
                extraction_engine="vision_ai",
            )

        # Call Gemini REST endpoint
        try:
            images_b64 = []
            for p in range(1, page_count + 1):
                page_img = preprocessor.rasterize_page(file_path, page_number=p, dpi=150)
                images_b64.append(self._image_to_base64(page_img))

            parts: List[Dict[str, Any]] = [{"text": SYSTEM_PROMPT}]
            for b64 in images_b64:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64,
                    }
                })

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"response_mime_type": "application/json"},
            }

            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()

            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            questions = [
                ExtractedQuestionDTO(
                    question_number=q.get("question_number"),
                    question_text=q.get("question_text", ""),
                    question_type=QuestionType(q.get("question_type", "multiple_choice")),
                    options=[
                        ExtractedOptionDTO(
                            key=o.get("key", ""),
                            text=o.get("text", ""),
                            order_index=i,
                        )
                        for i, o in enumerate(q.get("options", []))
                    ],
                    source_pages=q.get("source_pages", [1]),
                    confidence_score=float(q.get("confidence_score", 0.9)),
                    review_status=ReviewStatus.CONFIDENT if float(q.get("confidence_score", 0.9)) >= 0.8 else ReviewStatus.NEEDS_REVIEW,
                )
                for q in parsed.get("questions", [])
            ]

            answers = [
                ExtractedAnswerDTO(
                    question_identifier=a.get("question_identifier", ""),
                    raw_answer_text=a.get("raw_answer_text", ""),
                    normalized_answer=a.get("normalized_answer", ""),
                    source_page=a.get("source_page"),
                    confidence_score=float(a.get("confidence_score", 0.95)),
                )
                for a in parsed.get("answers", [])
            ]

            return ExtractionResultDTO(
                questions=questions,
                answers=answers,
                warnings=[],
                page_count=page_count,
                extraction_engine="vision_ai",
            )

        except Exception as e:
            return ExtractionResultDTO(
                questions=[],
                answers=[],
                warnings=[
                    ExtractionWarningDTO(
                        warning_code="VISION_API_ERROR",
                        message=f"External Vision processing error: {str(e)}",
                        severity=WarningSeverity.CRITICAL,
                    )
                ],
                page_count=page_count,
                extraction_engine="vision_ai",
            )


vision_extractor = VisionAIExtractor()
