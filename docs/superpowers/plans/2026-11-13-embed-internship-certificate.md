# OCR-Friendly Internship Certificate Embedding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed the scanned corporate internship certificate into `Report/main.tex` on page iii with an invisible, selectable, searchable OCR text layer (`render_mode=3`) while preserving the authentic 600 DPI full-color artwork, producing an updated `Report/main.pdf`.

**Architecture:** A standalone Python generation script (`scripts/generate_searchable_certificate.py`) constructs a dual-layer A4 PDF (`Report/internship_certificate.pdf`) containing the original uncompressed 600 DPI image and an invisible OCR text layer matching exact visual coordinates. `Report/main.tex` embeds this PDF via `pdfpages` on page iii with centered roman page number (`ii`) and TOC registration.

**Tech Stack:** Python 3.10+, PyMuPDF (`fitz`), LaTeX, pdfTeX (MiKTeX 25.12), `pdfpages`.

## Global Constraints
- Target PDF output: `D:\Python\PYCHARM\Projects\finmetrics\Report\main.pdf`
- Root LaTeX source: `D:\Python\PYCHARM\Projects\finmetrics\Report\main.tex`
- Certificate source image: `E:\Rohit Documents\intern\IMG_20261113_0001.jpg.jpeg`
- Repository image copy: `D:\Python\PYCHARM\Projects\finmetrics\Report\internship_certificate.jpg`
- Searchable certificate PDF: `D:\Python\PYCHARM\Projects\finmetrics\Report\internship_certificate.pdf`
- Certificate Details:
  - Candidate: N. Rohit Vedhanandh
  - Company: IQ Business Advisors
  - Role: Financial Analyst and Process Re-engineering
  - Duration: 06th May, 2026 to 10th July, 2026
  - Certificate No: IQBA/2026/013
  - Issue Date: 10/07/2026
  - Signatory: N Naga Arjun, Managing Partner
- Placement: Page iii (roman numeral `ii` at bottom center)
- Zero fatal compilation errors, zero broken references (`??`), and total page count remains 40 pages.

---

### Task 1: Generate Searchable Dual-Layer Certificate PDF

**Files:**
- Create: `scripts/generate_searchable_certificate.py`
- Test: `tests/test_certificate_pdf.py`
- Output: `Report/internship_certificate.jpg`, `Report/internship_certificate.pdf`

**Interfaces:**
- Consumes: `E:\Rohit Documents\intern\IMG_20261113_0001.jpg.jpeg`
- Produces: `Report/internship_certificate.pdf` with selectable, searchable text layer.

- [ ] **Step 1: Write test to verify certificate PDF properties and OCR text layer**
  Create `tests/test_certificate_pdf.py`:
  ```python
  import fitz
  import os

  def test_searchable_certificate_exists_and_has_text():
      pdf_path = "Report/internship_certificate.pdf"
      img_path = "Report/internship_certificate.jpg"
      assert os.path.exists(pdf_path), "Certificate PDF must exist"
      assert os.path.exists(img_path), "Local certificate image copy must exist"

      doc = fitz.open(pdf_path)
      assert len(doc) == 1, "Must be exactly 1 page"
      page = doc[0]

      # Verify A4 dimensions (595.32 x 841.92 pt within 1 pt tolerance)
      rect = page.rect
      assert abs(rect.width - 595.32) < 2.0
      assert abs(rect.height - 841.92) < 2.0

      # Verify text is extractable and contains all mandatory keywords
      text = page.get_text()
      assert "Rohit" in text
      assert "IQ Business Advisors" in text or "IQBA" in text
      assert "OF INTERNSHIP" in text
      assert "Financial Analyst" in text
      assert "Process Re-engineering" in text
      assert "IQBA/2026/013" in text
      assert "N NAGA ARJUN" in text
      assert "10/07/2026" in text
  ```

- [ ] **Step 2: Run test to confirm it fails before generation**
  Run: `pytest tests/test_certificate_pdf.py -v`
  Expected: FAIL with `AssertionError: Certificate PDF must exist`.

- [ ] **Step 3: Implement `scripts/generate_searchable_certificate.py`**
  Write the script using `fitz` and `shutil`:
  - Copy `E:\Rohit Documents\intern\IMG_20261113_0001.jpg.jpeg` to `Report/internship_certificate.jpg`.
  - Create A4 page (`595.32 x 841.92`).
  - Insert image over full page.
  - Insert invisible text (`render_mode=3`) matching all text positions.
  - Save to `Report/internship_certificate.pdf`.

- [ ] **Step 4: Execute generator and run tests to verify pass**
  Run:
  ```bash
  python scripts/generate_searchable_certificate.py
  pytest tests/test_certificate_pdf.py -v
  ```
  Expected: PASS (1/1 tests passing, text fully searchable).

- [ ] **Step 5: Commit generator script and test**
  Run:
  ```bash
  git add scripts/generate_searchable_certificate.py tests/test_certificate_pdf.py Report/internship_certificate.jpg Report/internship_certificate.pdf
  git commit -m "feat(report): generate dual-layer searchable internship certificate PDF"
  ```

---

### Task 2: Embed Searchable Certificate into `Report/main.tex` and Compile `Report/main.pdf`

**Files:**
- Modify: `Report/main.tex`
- Output: `Report/main.pdf`, `Report/main.log`

**Interfaces:**
- Consumes: `Report/internship_certificate.pdf`
- Produces: Updated `Report/main.pdf` with the certificate embedded at page 3.

- [ ] **Step 1: Edit `Report/main.tex`**
  - In preamble: ensure `\usepackage{pdfpages}` is included.
  - Replace lines 184–189 (the blank `\mbox{}` placeholder):
    ```latex
    % =========================================================
    % INTERNSHIP COMPLETION CERTIFICATE
    % =========================================================
    \includepdf[pages=1,pagecommand={\thispagestyle{plain}\phantomsection\addcontentsline{toc}{chapter}{Internship Certificate}}]{internship_certificate.pdf}
    ```

- [ ] **Step 2: Multi-pass compilation**
  Run:
  ```bash
  cd "D:\Python\PYCHARM\Projects\finmetrics\Report"
  pdflatex -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex
  ```
  Expected: Exit code 0 on all passes, 0 fatal errors, 0 undefined citations/references.

- [ ] **Step 3: Verify document structure and text layer**
  Run Python validation:
  ```python
  import fitz
  doc = fitz.open("Report/main.pdf")
  assert len(doc) == 40, f"Expected 40 pages, got {len(doc)}"
  # Page 3 (index 2) must contain the certificate text and roman numeral 'ii'
  page3_text = doc[2].get_text()
  assert "N. Rohit Vedhanandh" in page3_text
  assert "IQ Business Advisors" in page3_text
  assert "ii" in page3_text
  print("Document verification successful!")
  ```

- [ ] **Step 4: Commit changes**
  Run:
  ```bash
  git add Report/main.tex Report/main.pdf Report/main.log
  git commit -m "docs(report): embed searchable internship certificate into thesis page iii"
  ```

---

### Task 3: Full Document Integrity and Visual Quality Verification

**Files:**
- Output: `Report/main.pdf`

**Interfaces:**
- Consumes: `Report/main.pdf`
- Produces: Final verification report.

- [ ] **Step 1: Check `Report/main.log` for warnings and errors**
  Verify:
  - Fatal errors (`! LaTeX Error`): 0
  - Undefined references: 0
  - Undefined citations: 0

- [ ] **Step 2: Check Table of Contents and bookmark outlines**
  Verify that bookmark index points to "Internship Certificate" on page 3.

- [ ] **Step 3: Verification commit (if needed) or final readiness sign-off**
  Confirm working tree is clean.
