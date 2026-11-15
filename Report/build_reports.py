#!/usr/bin/env python3
"""
Build script to compile both Color and Greyscale versions of the FinMetrics Suite Report.
- Color: main.pdf and main_color.pdf
- Greyscale: main_greyscale.pdf (Chapter 1 Introduction to Appendix in pure vector grayscale, Front Matter in full color)
"""
import os
import shutil
import subprocess
import fitz

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_pass(tex_file, base_name):
    print(f"=== Compiling {tex_file} ===")
    for cmd in [
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["bibtex", base_name],
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["pdflatex", "-interaction=nonstopmode", tex_file]
    ]:
        res = subprocess.run(cmd, cwd=REPORT_DIR, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error running {cmd}:")
            print(res.stdout[-1000:])
            raise RuntimeError(f"Command {' '.join(cmd)} failed with returncode {res.returncode}")
        print(f"  Passed: {' '.join(cmd)}")

def main():
    # 1. Compile Color version
    run_pass("main.tex", "main")
    color_pdf = os.path.join(REPORT_DIR, "main.pdf")
    color_copy = os.path.join(REPORT_DIR, "main_color.pdf")
    shutil.copyfile(color_pdf, color_copy)
    print(f"Color build completed: {color_pdf} -> {color_copy}")

    # 2. Compile Greyscale version
    run_pass("main_greyscale.tex", "main_greyscale")
    gray_pdf = os.path.join(REPORT_DIR, "main_greyscale.pdf")
    print(f"Greyscale build completed: {gray_pdf}")

    # 3. Verify page counts
    doc_color = fitz.open(color_pdf)
    doc_gray = fitz.open(gray_pdf)
    print(f"Color pages: {len(doc_color)}")
    print(f"Greyscale pages: {len(doc_gray)}")
    assert len(doc_color) == 43, f"Expected 43 pages, got {len(doc_color)}"
    assert len(doc_gray) == 43, f"Expected 43 pages, got {len(doc_gray)}"
    print("ALL BUILDS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
