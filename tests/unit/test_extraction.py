"""Unit tests for question extraction, option parsing, and multi-page question stitching."""

from pathlib import Path
import pytest
from PIL import Image
import pymupdf
from app.models.enums import QuestionType, ReviewStatus
from app.services.extractor.segmenter import segmenter
from app.services.extractor.mock import mock_extractor
from app.services.extractor.hybrid import hybrid_extractor


def test_parse_options():
    text = (
        "What is the chemical formula for water?\n"
        "(A) H2O\n"
        "(B) CO2\n"
        "(C) NaCl\n"
        "(D) CH4"
    )
    stem, options = segmenter.parse_options(text)
    assert stem == "What is the chemical formula for water?"
    assert len(options) == 4
    assert options[0].key == "A"
    assert options[0].text == "H2O"
    assert options[1].key == "B"
    assert options[1].text == "CO2"


def test_classify_question_types():
    # MCQ
    _, mcq_opts = segmenter.parse_options("(A) One (B) Two (C) Three")
    assert segmenter.classify_question_type("Choose the number", mcq_opts) == QuestionType.MULTIPLE_CHOICE

    # True / False
    _, tf_opts = segmenter.parse_options("(A) True (B) False")
    assert segmenter.classify_question_type("Earth is flat", tf_opts) == QuestionType.TRUE_FALSE

    # Fill in the blank
    assert segmenter.classify_question_type("The speed of light in vacuum is _____ m/s.", []) == QuestionType.FILL_IN_THE_BLANK

    # Subjective
    assert segmenter.classify_question_type("Explain the working principle of a transformer.", []) == QuestionType.SUBJECTIVE


def test_multipage_question_stitching():
    """
    Test scenario where Question 1 is fully on Page 1, but Question 2 begins on Page 1
    and its options are located on Page 2.
    """
    page1_text = (
        "1. What is the derivative of sin(x)?\n"
        "(A) cos(x)\n"
        "(B) -cos(x)\n"
        "(C) tan(x)\n"
        "(D) sec(x)\n\n"
        "2. Consider a directed acyclic graph (DAG) with V vertices and E edges"
    )

    page2_text = (
        "(A) Topological sorting can be computed in O(V + E) time\n"
        "(B) Topological sorting requires O(V^2) time\n"
        "(C) DAGs cannot be topologically sorted\n"
        "(D) None of the above\n\n"
        "3. Define a Turing machine."
    )

    pages = [(1, page1_text), (2, page2_text)]
    questions, answers, warnings = segmenter.stitch_multipage_questions(pages)

    assert len(questions) == 3

    # Question 1: Single page (page 1)
    assert questions[0].question_number == "1"
    assert questions[0].source_pages == [1]
    assert len(questions[0].options) == 4

    # Question 2: Stitched across page 1 and page 2
    assert questions[1].question_number == "2"
    assert questions[1].source_pages == [1, 2]
    assert len(questions[1].options) == 4
    assert questions[1].options[0].key == "A"
    assert "Topological sorting can be computed" in questions[1].options[0].text
    assert "Consider a directed acyclic graph" in questions[1].question_text

    # Question 3: Single page (page 2, subjective)
    assert questions[2].question_number == "3"
    assert questions[2].source_pages == [2]
    assert questions[2].question_type == QuestionType.SUBJECTIVE

    # Verify warning about multi-page span was recorded for review
    span_warnings = [w for w in warnings if w.warning_code == "QUESTION_SPAN_PAGES"]
    assert len(span_warnings) == 1
    assert span_warnings[0].question_identifier == "2"


def test_mock_extractor(tmp_path):
    fake_file = tmp_path / "sample_exam.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(fake_file))
    doc.close()

    res = mock_extractor.extract(fake_file)
    assert len(res.questions) >= 2
    assert res.questions[0].question_number == "1"
    assert len(res.questions[0].options) == 4
    assert len(res.answers) >= 2


def test_hybrid_extractor(tmp_path):
    fake_file = tmp_path / "scanned_blurry_exam.png"
    # Create valid 1x1 PNG image
    img = Image.new("RGB", (10, 10), color="white")
    img.save(str(fake_file))

    res = hybrid_extractor.extract(fake_file)
    assert len(res.questions) >= 2
    # Should include low confidence item flagged for review
    assert any(q.review_status == ReviewStatus.NEEDS_REVIEW for q in res.questions)
