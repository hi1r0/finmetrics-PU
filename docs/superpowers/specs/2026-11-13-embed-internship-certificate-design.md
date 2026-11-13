# Design Specification: OCR-Friendly Internship Certificate Embedding

## 1. Overview and Objective
This document defines the implementation details for embedding the scanned corporate internship certificate into the LaTeX thesis `Report/main.tex` to produce an updated `Report/main.pdf`.

The certificate was awarded to **N. Rohit Vedhanandh** by **IQ Business Advisors** for completing a 2-month internship as **Financial Analyst and Process Re-engineering** (06th May, 2026 to 10th July, 2026), under Certificate No: `IQBA/2026/013`.

The primary requirements:
1. **OCR-Friendly**: The embedded certificate must possess an invisible, selectable, searchable OCR text layer (`render_mode=3`) precisely aligned with the text, allowing PDF readers and scanners to search (`Ctrl+F`), select, and copy text with 100% accuracy.
2. **Visual Authenticity**: Retain the original uncompressed 600 DPI full-color artwork (green borders, gold ribbon, blue circular seal, and signature).
3. **Seamless Integration**: Replace the blank `\mbox{}` placeholder on page iii of `Report/main.tex` via `\includepdf`, displaying the centered roman page number (`ii`) and keeping the entry in the Table of Contents.

---

## 2. File and Asset Architecture

### 2.1 Asset Copy & Generation
- **Source Image:** `E:\Rohit Documents\intern\IMG_20261113_0001.jpg.jpeg` (4960 $\times$ 7015 pixels, 600 DPI).
- **Target Image:** `Report/internship_certificate.jpg` copied directly into the repository.
- **Searchable PDF Generator Script:** `scripts/generate_searchable_certificate.py`
  - Uses `fitz` (PyMuPDF) to construct an A4 page (`595.32 x 841.92` points).
  - Inserts the original 600 DPI image across the full page rectangle.
  - Injects invisible text (`render_mode=3`) at exact visual coordinates matching:
    - `"IQBA Business Advisors"`
    - `"Certificate"`
    - `"OF INTERNSHIP"`
    - `"This certificate is proudly presented to"`
    - `"N. Rohit Vedhanandh"`
    - Completion text paragraph (8 lines)
    - `"Issue Date : 10/07/2026"`
    - `"Certificate No : IQBA/2026/013"`
    - `"N NAGA ARJUN"`
    - `"Managing Partner"`
  - Outputs `Report/internship_certificate.pdf`.

### 2.2 LaTeX Document Updates (`Report/main.tex`)
- In preamble (line 21):
  Add `\usepackage{pdfpages}`.
- Replace placeholder lines 184–189:
  ```latex
  % =========================================================
  % INTERNSHIP COMPLETION CERTIFICATE
  % =========================================================
  \includepdf[pages=1,pagecommand={\thispagestyle{plain}\phantomsection\addcontentsline{toc}{chapter}{Internship Certificate}}]{internship_certificate.pdf}
  ```
- All other chapters, figures, equations, and front matter remain untouched.

---

## 3. Verification & Acceptance Criteria
1. `Report/internship_certificate.pdf` contains searchable text readable by PyMuPDF text extraction.
2. `pdflatex` compiles `Report/main.tex` with exit code 0, 0 fatal errors, and 0 undefined references.
3. `Report/main.pdf` contains the colored certificate on page 3 (roman numeral `ii` at bottom center).
4. Text on page 3 of `Report/main.pdf` can be selected and searched.
5. Table of Contents retains `Internship Certificate` pointing to page iii.
6. Overall page count remains 40 pages.
