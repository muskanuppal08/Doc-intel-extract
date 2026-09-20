"""Generator for synthetic sample test documents matching all 10 demonstration criteria."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf


def generate_all_samples(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Demo 1: Clean Digital PDF
    p1 = output_dir / "demo_1_digital.pdf"
    doc1 = pymupdf.open()
    page1 = doc1.new_page()
    page1.insert_text(
        (50, 72),
        "COMPUTER SCIENCE MIDTERM EXAMINATION\n\n"
        "1. What is the time complexity of quicksort in the average case?\n"
        "(A) O(n log n)\n"
        "(B) O(n^2)\n"
        "(C) O(n)\n"
        "(D) O(1)\n"
    )
    doc1.save(str(p1))
    doc1.close()

    # 2. Demo 2: Single Question Image (PNG)
    p2 = output_dir / "demo_2_image.png"
    img = Image.new("RGB", (800, 300), color="white")
    draw = ImageDraw.Draw(img)
    text = (
        "Question 1: Which data structure uses FIFO (First In First Out)?\n"
        "(A) Stack\n"
        "(B) Queue\n"
        "(C) Tree\n"
        "(D) Graph"
    )
    draw.text((30, 40), text, fill="black")
    img.save(str(p2))

    # 3. Demo 3: Scanned / Low-Quality Degraded PDF
    p3 = output_dir / "demo_3_scanned_low_quality.pdf"
    doc3 = pymupdf.open()
    page3 = doc3.new_page()
    page3.insert_text(
        (50, 72),
        "CHEMISTRY SCAN - LOW RESOLUTION\n\n"
        "1. Identify the oxidation state of Chromium in K2Cr2O7 [blurred].\n"
        "(A) +6\n"
        "(B) +3\n"
        "(C) +2\n"
        "(D) 0\n"
    )
    doc3.save(str(p3))
    doc3.close()

    # 4. Demo 4: Multi-Question Paper (MCQs + Subjective)
    p4 = output_dir / "demo_4_multi_questions.pdf"
    doc4 = pymupdf.open()
    page4 = doc4.new_page()
    page4.insert_text(
        (50, 72),
        "MATHEMATICS & PHYSICS COMPREHENSIVE\n\n"
        "1. Evaluate the integral of e^(2x) dx.\n"
        "(A) (1/2) e^(2x) + C\n"
        "(B) 2 e^(2x) + C\n"
        "(C) e^(2x) + C\n"
        "(D) (1/4) e^(2x) + C\n\n"
        "2. State Heisenberg's uncertainty principle."
    )
    doc4.save(str(p4))
    doc4.close()

    # 5. Demo 5: Question Spanning Multiple Pages (Pages 1 & 2)
    p5 = output_dir / "demo_5_multipage_span.pdf"
    doc5 = pymupdf.open()
    # Page 1 has Question 1 complete, and Question 2 starting at bottom
    page5_1 = doc5.new_page()
    page5_1.insert_text(
        (50, 72),
        "EXAM SECTION A\n\n"
        "1. What is the derivative of cos(x)?\n"
        "(A) -sin(x)\n"
        "(B) sin(x)\n"
        "(C) tan(x)\n"
        "(D) -cos(x)\n\n"
        "2. Consider an ideal Carnot engine operating between temperatures T1 and T2"
    )
    # Page 2 has the options for Question 2
    page5_2 = doc5.new_page()
    page5_2.insert_text(
        (50, 72),
        "(A) Efficiency depends only on T1 and T2\n"
        "(B) Efficiency is always 100%\n"
        "(C) Efficiency is independent of working substance\n"
        "(D) Both A and C\n\n"
        "3. Define entropy in statistical mechanics."
    )
    doc5.save(str(p5))
    doc5.close()

    # 6. Demo 6: Standard Options Exam (A, B, C, D)
    p6 = output_dir / "demo_6_options_exam.pdf"
    doc6 = pymupdf.open()
    page6 = doc6.new_page()
    page6.insert_text(
        (50, 72),
        "BIOLOGY GENERAL\n\n"
        "1. Which organelle is responsible for cellular respiration?\n"
        "(A) Mitochondria\n"
        "(B) Ribosome\n"
        "(C) Golgi apparatus\n"
        "(D) Chloroplast\n"
    )
    doc6.save(str(p6))
    doc6.close()

    # 7. Demo 7: Paper with Inline Answer Key
    p7 = output_dir / "demo_7_inline_answer_key.pdf"
    doc7 = pymupdf.open()
    page7 = doc7.new_page()
    page7.insert_text(
        (50, 72),
        "ASTRONOMY TEST WITH ANSWERS\n\n"
        "1. What is the closest star to Earth?\n"
        "(A) Proxima Centauri\n"
        "(B) The Sun\n"
        "(C) Sirius\n"
        "(D) Betelgeuse\n\n"
        "ANSWERS:\n"
        "1. B - The Sun is at an average distance of 149.6 million km.\n"
    )
    doc7.save(str(p7))
    doc7.close()

    # 8. Demo 8: Low-Confidence Question Requiring Review
    p8 = output_dir / "demo_8_uncertain_review.pdf"
    doc8 = pymupdf.open()
    page8 = doc8.new_page()
    page8.insert_text(
        (50, 72),
        "ENGINEERING MECHANICS\n\n"
        "1. Determine force vector F in member BC [unreadable] when load is 10 kN ...\n"
        "(A) 12.5 kN\n"
        "(B) [blurred]\n"
    )
    doc8.save(str(p8))
    doc8.close()

    # 9. Demo 9: Final Structured Output (Question + Options + Answers)
    p9 = output_dir / "demo_9_structured_output.pdf"
    doc9 = pymupdf.open()
    page9 = doc9.new_page()
    page9.insert_text(
        (50, 72),
        "PHYSICS GENERAL FINAL\n\n"
        "1. What is the unit of electric power?\n"
        "(A) Watt\n"
        "(B) Joule\n"
        "(C) Ampere\n"
        "(D) Volt\n\n"
        "2. State Ohm's law.\n\n"
        "ANSWER KEY:\n"
        "1. A\n"
    )
    doc9.save(str(p9))
    doc9.close()

    # 10. Demo 10: Invalid File Format (Rejection)
    p10 = output_dir / "demo_10_invalid.sh"
    p10.write_text("#!/bin/bash\necho 'Unsupported format'")

    print(f"Successfully generated 10 sample demo files in: {output_dir}")


if __name__ == "__main__":
    generate_all_samples(Path(__file__).resolve().parent)
