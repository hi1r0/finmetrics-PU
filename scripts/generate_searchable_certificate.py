#!/usr/bin/env python3
"""
Generate a dual-layer searchable A4 PDF from the high-resolution scanned
corporate internship certificate image.

The resulting PDF contains:
1. The authentic 600 DPI full-color scanned artwork across the entire page.
2. An invisible OCR text layer (render_mode=3) precisely aligned with the visual text,
   enabling search, copy/paste, and accessibility compliance.
"""

import argparse
import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF

DEFAULT_SOURCE_IMAGE = r"E:\Rohit Documents\intern\IMG_20261113_0001.jpg.jpeg"
DEFAULT_OUTPUT_IMAGE = "Report/internship_certificate.jpg"
DEFAULT_OUTPUT_PDF = "Report/internship_certificate.pdf"

# Standard A4 dimensions in points (72 points per inch)
A4_WIDTH = 595.32
A4_HEIGHT = 841.92

# Text elements to inject as invisible OCR layer (render_mode=3)
# (Point(x, baseline_y), text, fontsize)
TEXT_ELEMENTS = [
    (fitz.Point(438, 65), "IQBA", 14),
    (fitz.Point(438, 80), "IQ Business Advisors", 10),
    (fitz.Point(235, 155), "Certificate", 36),
    (fitz.Point(280, 190), "OF INTERNSHIP", 14),
    (fitz.Point(260, 290), "This certificate is proudly presented to", 11),
    (fitz.Point(210, 350), "N. Rohit Vedhanandh", 24),
    (
        fitz.Point(208, 420),
        "has successfully completed a 2-month internship at IQ Business Advisors",
        9,
    ),
    (
        fitz.Point(208, 435),
        "from 06th May, 2026 to 10th July, 2026. During this",
        9,
    ),
    (
        fitz.Point(208, 450),
        "period, he actively contributed to tasks related to Financial Analyst",
        9,
    ),
    (
        fitz.Point(208, 465),
        "and Process Re-engineering, demonstrating a strong willingness",
        9,
    ),
    (
        fitz.Point(208, 480),
        "to learn and a professional attitude. His contributions were",
        9,
    ),
    (
        fitz.Point(208, 495),
        "appreciated by the team, and he consistently showed initiative and",
        9,
    ),
    (
        fitz.Point(208, 510),
        "responsibility in the assigned work. We thank for his time and",
        9,
    ),
    (
        fitz.Point(208, 525),
        "efforts and wish his success in future endeavors.",
        9,
    ),
    (fitz.Point(285, 565), "Issue Date : 10/07/2026", 10),
    (fitz.Point(285, 580), "Certificate No : IQBA/2026/013", 10),
    (fitz.Point(430, 665), "N NAGA ARJUN", 11),
    (fitz.Point(430, 685), "Managing Partner", 10),
]


def generate_searchable_certificate(
    source_img_path: str = DEFAULT_SOURCE_IMAGE,
    output_img_path: str = DEFAULT_OUTPUT_IMAGE,
    output_pdf_path: str = DEFAULT_OUTPUT_PDF,
) -> None:
    source = Path(source_img_path)
    if not source.exists():
        raise FileNotFoundError(f"Source certificate image not found at: {source}")

    out_img = Path(output_img_path)
    out_img.parent.mkdir(parents=True, exist_ok=True)
    out_pdf = Path(output_pdf_path)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # 1. Copy source image to repository location if different
    if source.resolve() != out_img.resolve():
        print(f"Copying {source} -> {out_img}...")
        shutil.copy2(source, out_img)

    # 2. Build dual-layer A4 PDF
    print(f"Creating dual-layer searchable PDF: {out_pdf}...")
    doc = fitz.open()
    page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)

    # Layer 1: High-resolution raster image covering entire A4 page
    page.insert_image(page.rect, filename=str(out_img))

    # Layer 2: Invisible OCR text overlay (render_mode=3: neither fill nor stroke)
    for point, text, font_size in TEXT_ELEMENTS:
        page.insert_text(
            point,
            text,
            fontsize=font_size,
            fontname="helv",
            render_mode=3,
        )

    # 3. Save PDF
    doc.save(str(out_pdf))
    doc.close()
    print(f"Successfully generated searchable certificate PDF at: {out_pdf}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate searchable dual-layer internship certificate PDF."
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE_IMAGE,
        help="Path to source 600 DPI certificate image.",
    )
    parser.add_argument(
        "--output-img",
        default=DEFAULT_OUTPUT_IMAGE,
        help="Path to copy image within repository.",
    )
    parser.add_argument(
        "--output-pdf",
        default=DEFAULT_OUTPUT_PDF,
        help="Path for target searchable PDF.",
    )
    args = parser.parse_args()

    generate_searchable_certificate(
        source_img_path=args.source,
        output_img_path=args.output_img,
        output_pdf_path=args.output_pdf,
    )


if __name__ == "__main__":
    main()
