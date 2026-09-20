"""Generate Comprehensive Master Examination PDF with all test cases:
1. MCQs with choices (A, B, C, D)
2. Mathematical formulas and calculus integrals
3. Visual diagrams (Mechanics incline & Geometry inscribed circle)
4. Multi-page question spanning across page 1 and page 2
5. Degraded/blurry question triggering low-confidence review queue
6. Formatted answer keys with explanations & grid
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf

OUTPUT_DIR = Path("demo_assets")
OUTPUT_DIR.mkdir(exist_ok=True)
PDF_PATH = OUTPUT_DIR / "comprehensive_master_exam.pdf"

# 1. Create Diagram 1: Inclined Plane Mechanics
def create_inclined_plane_diagram():
    img = Image.new("RGB", (600, 320), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Ground and Triangle
    draw.line([(50, 270), (550, 270)], fill=(0, 0, 0), width=3) # Ground
    draw.polygon([(100, 270), (500, 270), (500, 80)], outline=(0, 51, 102), fill=(240, 245, 255), width=3) # Incline
    
    # Angle arc and text
    draw.arc([(140, 240), (200, 300)], start=200, end=360, fill=(204, 0, 0), width=2)
    draw.text((210, 245), "theta = 30 deg", fill=(204, 0, 0))
    
    # Block on Incline
    # Incline hypotenuse runs from (100, 270) to (500, 80)
    # Midpoint roughly (300, 175)
    block_points = [(270, 185), (330, 156), (360, 219), (300, 248)]
    draw.polygon(block_points, outline=(0, 102, 204), fill=(179, 217, 255), width=2)
    draw.text((290, 200), "m = 10 kg", fill=(0, 0, 128))
    
    # Force Vector F parallel to incline
    draw.line([(330, 156), (420, 113)], fill=(0, 153, 76), width=3)
    draw.polygon([(420, 113), (405, 125), (412, 110)], fill=(0, 153, 76))
    draw.text((370, 115), "F = 50 N", fill=(0, 153, 76))
    
    # Gravity Vector mg downwards
    draw.line([(315, 210), (315, 265)], fill=(153, 0, 0), width=3)
    draw.polygon([(315, 265), (310, 255), (320, 255)], fill=(153, 0, 0))
    draw.text((325, 240), "W = mg", fill=(153, 0, 0))

    diag_path = OUTPUT_DIR / "diagram_mechanics_incline.png"
    img.save(diag_path)
    return diag_path

# 2. Create Diagram 2: Inscribed Circle in Right-Angled Triangle
def create_geometry_diagram():
    img = Image.new("RGB", (600, 340), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Triangle vertices: (100, 280), (450, 280), (100, 50)
    # Right angle at (100, 280)
    p_right = (100, 280)
    p_bottom = (460, 280)
    p_top = (100, 60)
    
    # Fill Triangle
    draw.polygon([p_right, p_bottom, p_top], outline=(0, 51, 102), fill=(245, 245, 245), width=3)
    
    # Right angle marker
    draw.rectangle([(100, 260), (120, 280)], outline=(0, 0, 0), width=2)
    
    # Inscribed circle: radius r = (a + b - c)/2 = (15 + 20 - 25)/2 = 5
    # Center = (100 + 5*scale, 280 - 5*scale)
    # scale approx 10 px per cm -> r = 50 px, center = (180, 200)
    cx, cy, r = 185, 195, 80
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(204, 0, 0), fill=(255, 230, 230), width=3)
    draw.line([(cx, cy), (cx + r, cy)], fill=(204, 0, 0), width=2) # Radius line
    draw.text((cx + 20, cy - 15), "r = 5 cm", fill=(204, 0, 0))
    
    # Dimensions
    draw.text((250, 290), "Base b = 20 cm", fill=(0, 51, 102))
    draw.text((20, 160), "Height a = 15 cm", fill=(0, 51, 102))
    draw.text((310, 140), "Hypotenuse c = 25 cm", fill=(0, 51, 102))

    diag_path = OUTPUT_DIR / "diagram_geometry_inscribed.png"
    img.save(diag_path)
    return diag_path

diag1_path = create_inclined_plane_diagram()
diag2_path = create_geometry_diagram()

# 3. Create Multi-page PDF using PyMuPDF
doc = pymupdf.open()

# ================= PAGE 1 =================
p1 = doc.new_page(width=595, height=842) # A4 size

header_text = (
    "PBNC CENTRAL BOARD OF EXAMINATION\n"
    "ADVANCED APPLIED SCIENCES & MATHEMATICS - EXAM PAPER 2026\n"
    "Course Code: PBNC-CSE-2026 | Time: 3.0 Hours | Max Marks: 100\n"
    "--------------------------------------------------------------------------------------------------"
)
p1.insert_text((40, 45), header_text, fontsize=10, fontname="helv", color=(0.1, 0.1, 0.3))

# Question 1 (Diagram-based Mechanics)
q1_text = (
    "1. A block of mass m = 10 kg is placed on an inclined plane with an inclination angle of\n"
    "   theta = 30 degrees. A constant force F = 50 N is applied parallel to the incline as shown\n"
    "   in Figure 1. Taking g = 9.8 m/s^2, determine the resulting acceleration of the block:\n"
    "   (A) a = 0.0 m/s^2 (The block remains in equilibrium)\n"
    "   (B) a = 4.9 m/s^2 down the incline\n"
    "   (C) a = 2.45 m/s^2 up the incline\n"
    "   (D) a = 9.8 m/s^2 downwards"
)
p1.insert_text((40, 110), q1_text, fontsize=10, fontname="helv")

# Insert Diagram 1 into Page 1
rect_diag1 = pymupdf.Rect(120, 220, 480, 360)
p1.insert_image(rect_diag1, filename=str(diag1_path))
p1.insert_text((230, 370), "[Figure 1: Inclined Plane Free Body Diagram]", fontsize=8, color=(0.3, 0.3, 0.3))

# Question 2 (Calculus & Trigonometry)
q2_text = (
    "2. Evaluate the definite definite trigonometric integral:\n"
    "   I = \\int_{0}^{\\pi/2} \\frac{\\sin^3(x)}{\\sin^3(x) + \\cos^3(x)} dx\n"
    "   Which of the following values correctly represents the solution to I?\n"
    "   (A) \\pi / 4\n"
    "   (B) \\pi / 2\n"
    "   (C) 1 / \\sqrt{2}\n"
    "   (D) \\ln(2)"
)
p1.insert_text((40, 400), q2_text, fontsize=10, fontname="helv")

# Question 3 (Multi-Page Continuity Split - Part 1 on Page 1)
q3_text_part1 = (
    "3. An electrical AC circuit consists of a pure resistance R = 50 Ohms, an inductance\n"
    "   L = 0.318 H, and a capacitance C = 63.6 microfarads connected in series across an\n"
    "   alternating voltage supply V(t) = 220 * sqrt(2) * sin(100 * pi * t) Volts.\n"
    "   Calculate the total circuit impedance Z and resonant power factor cos(phi):\n"
    "   (A) Z = 50 Ohms, cos(phi) = 1.0 (Purely resistive at resonance)\n"
    "   (B) Z = 100 Ohms, cos(phi) = 0.5"
)
p1.insert_text((40, 540), q3_text_part1, fontsize=10, fontname="helv")

footer_p1 = "[Turn Over: Question 3 Options continue on Page 2 | PBNC Confidential Examination]"
p1.insert_text((80, 800), footer_p1, fontsize=9, color=(0.5, 0.5, 0.5))


# ================= PAGE 2 =================
p2 = doc.new_page(width=595, height=842) # A4 size

p2.insert_text((40, 45), "PBNC CENTRAL BOARD OF EXAMINATION - PAGE 2 OF 2", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.3))

# Question 3 (Continued from Page 1: choices C and D)
q3_continuation = (
    "(Question 3 Continued from Page 1):\n"
    "   (C) Z = 70.7 Ohms, cos(phi) = 0.707\n"
    "   (D) Z = 125 Ohms, cos(phi) = 0.8"
)
p2.insert_text((40, 75), q3_continuation, fontsize=10, fontname="helv")

# Question 4 (Geometry & Calculus with Diagram 2)
q4_text = (
    "4. A circle of radius r = 5 cm is inscribed inside a right-angled triangle with perpendicular\n"
    "   legs a = 15 cm and b = 20 cm as illustrated in Figure 2 below.\n"
    "   Determine the shaded boundary area enclosed between the triangle and the circle:\n"
    "   (A) 71.46 cm^2\n"
    "   (B) 150.00 cm^2\n"
    "   (C) 78.54 cm^2\n"
    "   (D) 25.13 cm^2"
)
p2.insert_text((40, 140), q4_text, fontsize=10, fontname="helv")

# Insert Diagram 2 into Page 2
rect_diag2 = pymupdf.Rect(120, 245, 480, 395)
p2.insert_image(rect_diag2, filename=str(diag2_path))
p2.insert_text((220, 405), "[Figure 2: Inscribed Circle in Right Triangle]", fontsize=8, color=(0.3, 0.3, 0.3))

# Question 5 (Degraded/Low-Confidence to trigger Review Queue)
q5_text = (
    "5. Explain the mathematical formulation of Heisenberg Uncertainty Principle:\n"
    "   Delta x * Delta p >= h_bar / 2. [blurred_text: experimental measurement noise ... scan illegible]\n"
    "   (A) Simultaneous measurement precision of conjugate variables is physically bounded\n"
    "   (B) Momentum is indeterminate only in macroscopic thermodynamic systems"
)
p2.insert_text((40, 435), q5_text, fontsize=10, fontname="helv")

# Section B: Official Answer Key with Grid and Explanations
answers_text = (
    "SECTION B: OFFICIAL ANSWER KEY & DETAILED EXPLANATIONS\n"
    "==================================================================================================\n"
    "Answer Key Grid:   Q1: A  |  Q2: A  |  Q3: A  |  Q4: A\n\n"
    "Explanations:\n"
    "1. (A) - Net force parallel to plane: F - m*g*sin(30) = 50 - 10*9.8*0.5 = 1 N, held by static friction.\n"
    "2. (A) - Applying King's rule \\int_0^a f(x)dx = \\int_0^a f(a-x)dx yields 2*I = \\pi/2, hence I = \\pi/4.\n"
    "3. (A) - At frequency 50Hz, X_L = 2*pi*f*L = 100 Ohms, X_C = 1/(2*pi*f*C) = 100 Ohms, Z = R = 50 Ohms.\n"
    "4. (A) - Area of triangle = (15 * 20)/2 = 150 cm^2; Area of circle = pi * 5^2 = 78.54 cm^2; Area = 71.46 cm^2."
)
p2.insert_text((40, 560), answers_text, fontsize=9, fontname="helv", color=(0.05, 0.2, 0.05))

doc.save(PDF_PATH)
doc.close()
print(f"Master Exam PDF successfully generated at: {PDF_PATH}")
