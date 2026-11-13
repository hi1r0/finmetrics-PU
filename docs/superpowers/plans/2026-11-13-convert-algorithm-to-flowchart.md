# Convert Outlier Algorithm to Flowchart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Algorithm 1 ("Univariate Outlier Detection and Baselines") in Chapter 4 (`Report/chapters/algorithms.tex`) into a professional LaTeX TikZ flowchart figure, rename Section 4.4 to "Algorithmic Workflow & Flowchart", and recompile `Report/main.pdf` with synchronized TOC, zero compilation errors, and no orphan layout breaks.

**Architecture:** Replace the `\begin{algorithm}[H]` pseudocode environment in `Report/chapters/algorithms.tex` with a native TikZ flowchart (`Figure 4.1`) styled in an academic soft pastel palette with rounded process rectangles, decision diamonds, and terminal capsules. Recompile `Report/main.pdf` with multi-pass pdfLaTeX, ensuring clean pagination without orphan spills.

**Tech Stack:** LaTeX, TikZ (`shapes.geometric`, `arrows.meta`, `positioning`, `calc`), pdfTeX (MiKTeX 25.12), Python 3.10+, PyMuPDF (`fitz`), pytest.

## Global Constraints
- Target PDF output: `Report/main.pdf`
- Root LaTeX source: `Report/main.tex`
- Chapter 4 source: `Report/chapters/algorithms.tex`
- Section Title: `Algorithmic Workflow \& Flowchart` (Section 4.4)
- Subsection Title: `Univariate Outlier Detection Process` (Subsection 4.4.1)
- Figure Caption: `Figure 4.1: Univariate Outlier Detection and Baseline Masking Flowchart` (`\label{fig:outlier_flowchart}`)
- Flowchart Nodes: Pure conceptual labels matching user specification:
  - `START` (Terminal capsule)
  - `Select Ratio Column` (Process rectangle)
  - `Remove Missing Values` (Process rectangle)
  - `Enough Data?` (Decision diamond)
  - `Skip Column` (Process rectangle)
  - `Calculate IQR` (Process rectangle)
  - `Calculate Z-score` (Process rectangle)
  - `Is it an Outlier?` (Decision diamond)
  - `Mask Value` (Process rectangle)
  - `Keep Value` (Process rectangle)
  - `END` (Terminal capsule)
- Color Palette: Academic Soft Pastel theme (soft green/teal terminals, soft blue process boxes, soft amber decision diamonds, thick stealth connectors, bold Yes/No path annotations).
- Zero fatal compilation errors (`! LaTeX Error`), zero undefined references (`??`), zero undefined citations. Total page count remains compact without orphan spills.

---

### Task 1: Replace Algorithm 1 with TikZ Flowchart in `Report/chapters/algorithms.tex`

**Files:**
- Modify: `Report/chapters/algorithms.tex`
- Test: `tests/test_outlier_flowchart.py`

**Interfaces:**
- Consumes: User-approved conceptual flowchart structure
- Produces: Updated `Report/chapters/algorithms.tex` with TikZ flowchart

- [ ] **Step 1: Write test for flowchart environment and section updates**
  Create `tests/test_outlier_flowchart.py`:
  ```python
  import os

  def test_flowchart_environment_and_labels():
      algo_path = "Report/chapters/algorithms.tex"
      assert os.path.exists(algo_path), "algorithms.tex must exist"
      with open(algo_path, "r", encoding="utf-8") as f:
          content = f.read()

      # Section and subsection titles
      assert "\\section{Algorithmic Workflow \\& Flowchart}" in content
      assert "\\subsection{Univariate Outlier Detection Process}" in content

      # Figure and label
      assert "\\begin{figure}" in content
      assert "\\label{fig:outlier_flowchart}" in content
      assert "Univariate Outlier Detection and Baseline Masking Flowchart" in content

      # Flowchart nodes
      assert "Select Ratio Column" in content
      assert "Remove Missing Values" in content
      assert "Enough Data?" in content
      assert "Skip Column" in content
      assert "Calculate IQR" in content
      assert "Calculate Z-score" in content
      assert "Is it an Outlier?" in content
      assert "Mask Value" in content
      assert "Keep Value" in content

      # Pseudocode block must be removed
      assert "\\begin{algorithmic}" not in content
      assert "\\begin{algorithm}" not in content
      assert "\\Procedure{DetectOutliers}" not in content
  ```

- [ ] **Step 2: Run test to confirm it fails before modifying `algorithms.tex`**
  Run: `python -m pytest tests/test_outlier_flowchart.py -v`
  Expected: FAIL with `AssertionError`.

- [ ] **Step 3: Update `Report/chapters/algorithms.tex`**
  - Update Section 4.4 title to `\section{Algorithmic Workflow \& Flowchart}`.
  - Update Subsection 4.4.1 to `\subsection{Univariate Outlier Detection Process}`.
  - Update in-text reference to `Figure~\ref{fig:outlier_flowchart}`.
  - Replace `\begin{algorithm}[H] ... \end{algorithm}` with the native TikZ flowchart `\begin{figure}[htbp] ... \end{figure}`.

- [ ] **Step 4: Run test to confirm it passes**
  Run: `python -m pytest tests/test_outlier_flowchart.py -v`
  Expected: PASS (1/1).

- [ ] **Step 5: Commit changes**
  Run:
  ```bash
  git add tests/test_outlier_flowchart.py Report/chapters/algorithms.tex
  git commit -m "feat(report): convert outlier detection algorithm into TikZ flowchart"
  ```

---

### Task 2: Multi-Pass PDF Compilation & Layout Verification

**Files:**
- Modify: `Report/main.pdf`, `Report/main.log`

**Interfaces:**
- Consumes: Updated `Report/chapters/algorithms.tex`
- Produces: Updated `Report/main.pdf` with flowchart rendered and TOC synchronized

- [ ] **Step 1: Multi-pass compilation of `Report/main.tex`**
  Run:
  ```bash
  cd "D:\Python\PYCHARM\Projects\finmetrics\Report"
  pdflatex -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex
  ```
  Expected: Returncode 0, 0 fatal errors.

- [ ] **Step 2: Automated verification of PDF layout and bookmarks**
  Run Python validation script:
  - Verify `Report/main.log` has 0 fatal errors, 0 undefined references, 0 undefined citations.
  - Verify `Report/main.pdf` TOC contains `4.4 Algorithmic Workflow & Flowchart`.
  - Verify flowchart text extraction on Chapter 4 pages contains `Select Ratio Column`, `Calculate IQR`, `Is it an Outlier?`, `Mask Value`.
  - Verify total page count is compact and clean (no orphan spills).

- [ ] **Step 3: Commit updated compiled PDF and build log**
  Run:
  ```bash
  git add Report/main.pdf Report/main.log
  git commit -m "docs(report): recompile thesis PDF with outlier detection flowchart"
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
  python -m pytest tests/
  ```
  Expected: All 18 tests PASS.

- [ ] **Step 2: Verify git status is clean**
  Run:
  ```bash
  git status
  ```
  Expected: Working tree clean.
