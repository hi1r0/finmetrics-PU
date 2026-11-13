# Enlarge Outlier Detection Flowchart to Full-Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enlarge the univariate outlier detection flowchart in `Report/chapters/algorithms.tex` into a prominent, full-page visual diagram top-aligned directly under the running header on Page 25, utilizing the thesis-standard pastel color palette (`greenbg`, `lavenderbg`, `peachbg`, `boxborder`), while preserving the exact 39-page document budget.

**Architecture:** Replace the compact 0.92x scaled flowchart with a top-snapped, full-page vector TikZ architecture with enlarged node dimensions (~5.2cm width, ~1.1cm height), expanded vertical node distances (~1.0cm - 1.2cm), larger typography (`\small` / `\bfseries\small`), larger stealth arrowheads, and the established thesis color palette matching Chapter 2, 3, and 5 diagrams. Multi-pass pdfLaTeX compilation and PyMuPDF geometry verification ensure zero page overflow and pristine visual hierarchy.

**Tech Stack:** LaTeX, TikZ (`shapes.geometric`, `arrows.meta`, `positioning`, `calc`), pdfLaTeX, BibTeX, Python (PyMuPDF `fitz`, `pytest`).

## Global Constraints
- Preserve exact thesis page budget at 39 pages (Page 25 dedicated to the full-page flowchart; Chapter 5 begins cleanly on Page 26).
- 0 fatal LaTeX errors, 0 undefined references, 0 undefined citations in `Report/main.log`.
- Color palette: `greenbg` (`RGB{228, 248, 232}`), `lavenderbg` (`RGB{238, 240, 252}`), `peachbg` (`RGB{253, 238, 226}`), `boxborder` (`RGB{40, 45, 55}`).
- Arrow style: `thick`, `draw=boxborder`, `>={Stealth[length=6.5pt, width=4.5pt]}`.
- Font styling: `\rmfamily\small` with `\bfseries` for terminals, decision diamonds, and branch labels.
- Do NOT run `git diff` without pathspec on `Report/main.pdf` directly.

---

### Task 1: Update Flowchart Geometry, Sizing, and Styling in `Report/chapters/algorithms.tex`

**Files:**
- Modify: `Report/chapters/algorithms.tex:225-300`
- Modify: `tests/test_outlier_flowchart.py`

**Interfaces:**
- Consumes: User ASCII architecture (`START`, `Select Ratio Column`, `Remove Missing Values`, `Enough Data?`, `Skip Column`, `Calculate IQR`, `Calculate Z-score`, `Is it an Outlier?`, `Mask Value`, `Keep Value`, `END`).
- Produces: Updated TikZ flowchart in `Report/chapters/algorithms.tex` using the thesis pastel palette and full-page layout, with updated automated tests.

- [ ] **Step 1: Update automated test suite in `tests/test_outlier_flowchart.py`**
  Add assertions checking:
  - Colors: `greenbg`, `lavenderbg`, `peachbg`, `boxborder`.
  - Node dimensions and styles: `minimum width=5.2cm`, `minimum height=1.1cm`, `font=\rmfamily\small`.
  - Top-alignment placement: `\clearpage` preceding the figure and `\begin{figure}[t!]`.

- [ ] **Step 2: Run pytest to observe test failure**
  Run:
  ```bash
  python -m pytest tests/test_outlier_flowchart.py
  ```
  Expected: FAIL due to missing updated color definitions and dimensions.

- [ ] **Step 3: Update `Report/chapters/algorithms.tex` with enlarged, top-aligned flowchart**
  - Add `\clearpage` before `\begin{figure}[t!]`.
  - Define:
    ```latex
    \definecolor{peachbg}{RGB}{253, 238, 226}
    \definecolor{lavenderbg}{RGB}{238, 240, 252}
    \definecolor{greenbg}{RGB}{228, 248, 232}
    \definecolor{boxborder}{RGB}{40, 45, 55}
    ```
  - Define enlarged styles:
    - `terminal`: `draw=boxborder, rounded corners=12pt, fill=greenbg, minimum width=3.8cm, minimum height=1.0cm, align=center, thick, font=\bfseries\small`
    - `process`: `draw=boxborder, rounded corners=4pt, fill=lavenderbg, minimum width=5.2cm, minimum height=1.1cm, align=center, thick, font=\small`
    - `decision`: `draw=boxborder, diamond, aspect=2.1, fill=peachbg, inner sep=4pt, align=center, thick, font=\bfseries\small`
    - `arrow`: `thick, ->, draw=boxborder, >={Stealth[length=6.5pt, width=4.5pt]}`
    - `node distance=1.1cm and 2.0cm`
  - Position nodes:
    - Central spine: `start`, `select`, `clean`, `enough`, `iqr`, `zscore`, `outlier`, `finish`.
    - `skip`: `right=1.8cm of enough`.
    - `mask`: `below left=0.9cm and 0.6cm of outlier`.
    - `keep`: `below right=0.9cm and 0.6cm of outlier`.
    - `finish`: `below=2.3cm of outlier`.
  - Orthogonal routing from `skip` to `finish` and `mask`/`keep` to `finish`.

- [ ] **Step 4: Run pytest to verify test passes**
  Run:
  ```bash
  python -m pytest tests/test_outlier_flowchart.py
  ```
  Expected: PASS (tex source assertions).

- [ ] **Step 5: Commit changes**
  ```bash
  git add Report/chapters/algorithms.tex tests/test_outlier_flowchart.py
  git commit -m "feat(report): enlarge outlier flowchart to full page with thesis pastel palette"
  ```

---

### Task 2: Multi-Pass PDF Compilation & Layout Verification

**Files:**
- Modify: `Report/main.pdf`, `Report/main.log`

**Interfaces:**
- Consumes: Updated `Report/chapters/algorithms.tex`
- Produces: Recompiled `Report/main.pdf` and updated `Report/main.log`

- [ ] **Step 1: Multi-pass compilation of `Report/main.tex`**
  Run from `Report/` directory:
  ```bash
  pdflatex -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex
  ```
  Expected: Return code 0, 0 fatal errors.

- [ ] **Step 2: Automated verification of PDF layout and bookmarks**
  Run Python validation script:
  - Verify `Report/main.log` has 0 fatal errors, 0 undefined references, 0 undefined citations.
  - Verify `Report/main.pdf` TOC contains `4.4 Algorithmic Workflow & Flowchart` targeting Page 24.
  - Verify Page 25 contains the flowchart and caption `Figure 4.2: Univariate Outlier Detection and Baseline Masking Flowchart`.
  - Verify flowchart starts in the upper quadrant of Page 25 (top < 150 pt from the running header) and extends towards the bottom margin.
  - Verify total page count remains exactly 39 pages without orphan page breaks.

- [ ] **Step 3: Commit updated compiled PDF and build log**
  ```bash
  git add Report/main.pdf Report/main.log tests/test_outlier_flowchart.py
  git commit -m "docs(report): recompile thesis PDF with enlarged full-page flowchart"
  ```

---

### Task 3: Comprehensive Document Integrity and Whole-Branch Verification

**Files:**
- Verify: Full repository integrity and all test suites

**Interfaces:**
- Consumes: Repository state
- Produces: Final verification report

- [ ] **Step 1: Run full automated test suite**
  Run:
  ```bash
  python -m pytest
  ```
  Expected: All 19 tests PASS.

- [ ] **Step 2: Verify git status is clean**
  Run:
  ```bash
  git status
  ```
  Expected: Working tree clean.
