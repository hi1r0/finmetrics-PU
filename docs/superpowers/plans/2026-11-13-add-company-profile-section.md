# Company Profile Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a formal "Host Organization Profile: IQ Business Advisors" section (Section 1.2) into Chapter 1 (`Report/chapters/introduction.tex`) of the thesis report and recompile `Report/main.pdf` with full TOC synchronization and zero compilation errors.

**Architecture:** Inject three structured, formal prose paragraphs into `Report/chapters/introduction.tex` between Section 1.1 (*Background*) and Section 1.3 (*Problem Statement*), describing IQBA's corporate identity, leadership (Naga Arjun and Rajesh Kannan, Founders and Managing Partners), advisory scope, and the direct catalyst connecting the internship role to the *FinMetrics Suite*. Recompile `Report/main.pdf` through multi-pass pdfLaTeX with updated bookmarks and pagination.

**Tech Stack:** LaTeX, pdfTeX (MiKTeX 25.12), Python 3.10+, PyMuPDF (`fitz`), pytest.

## Global Constraints
- Target PDF output: `Report/main.pdf`
- Root LaTeX source: `Report/main.tex`
- Chapter 1 source: `Report/chapters/introduction.tex`
- Section Title: `Host Organization Profile: IQ Business Advisors`
- Placement: Section 1.2 in Chapter 1 (immediately after Section 1.1 Background)
- Key facts:
  - Organization: IQ Business Advisors (IQBA)
  - Founded: December 2024
  - Headquarters: Kavundanpalayam, Puducherry – 605009
  - Founders: Naga Arjun and Rajesh Kannan (both designated as Founders and Managing Partners)
  - Combined Experience: Over 10+ years
  - Operating Footprint: Puducherry, Tamil Nadu (Chennai, Coimbatore), pan-India
  - Core Domains: Financial advisory, management consulting, stock auditing, internal audit assurance, regulatory tax compliance for SMEs, manufacturing, retail, and trading enterprises
  - Internship Context: Financial Analyst and Process Re-engineering Intern (Certificate No: IQBA/2026/013, May 2026 to July 2026)
  - Synergy: Bridge corporate advisory observations (nomenclature disparities, outlier-distorted peer benchmarks) to the design of the *FinMetrics Suite*
- Strict Exclusions: No mission statement, no core value propositions, no "DRIVE SMART" framework, no summary table, no TikZ diagram. Pure narrative prose paragraphs.
- Zero fatal compilation errors (`! LaTeX Error`), zero undefined references, zero undefined citations. Natural expansion allowed ($\approx 41\text{--}42$ pages).

---

### Task 1: Add Section 1.2 to `Report/chapters/introduction.tex`

**Files:**
- Modify: `Report/chapters/introduction.tex`
- Test: `tests/test_company_profile.py`

**Interfaces:**
- Consumes: Verified corporate profile details from `https://iqba.in/`
- Produces: Updated `Report/chapters/introduction.tex` with Section 1.2

- [ ] **Step 1: Write test for Company Profile section in `Report/chapters/introduction.tex`**
  Create `tests/test_company_profile.py`:
  ```python
  import os

  def test_company_profile_section_content():
      intro_path = "Report/chapters/introduction.tex"
      assert os.path.exists(intro_path), "introduction.tex must exist"
      with open(intro_path, "r", encoding="utf-8") as f:
          content = f.read()

      # Section header
      assert "\\section{Host Organization Profile: IQ Business Advisors}" in content

      # Leadership and titles
      assert "Naga Arjun" in content
      assert "Rajesh Kannan" in content
      assert "Founders and Managing Partners" in content

      # Corporate facts
      assert "Kavundanpalayam" in content
      assert "Puducherry" in content
      assert "December 2024" in content
      assert "Financial Analyst and Process Re-engineering" in content
      assert "IQBA/2026/013" in content
      assert "FinMetrics Suite" in content

      # Exclusions
      assert "DRIVE SMART" not in content
      assert "Mission Statement" not in content
      assert "Dynamic Stock Audit" not in content
  ```

- [ ] **Step 2: Run test to confirm it fails before modifying `introduction.tex`**
  Run: `python -m pytest tests/test_company_profile.py -v`
  Expected: FAIL with `AssertionError`.

- [ ] **Step 3: Update `Report/chapters/introduction.tex`**
  Insert `\section{Host Organization Profile: IQ Business Advisors}` with the three agreed prose paragraphs directly between Section 1.1 `\section{Background}` and `\section{Problem Statement}`.

- [ ] **Step 4: Run test to confirm it passes**
  Run: `python -m pytest tests/test_company_profile.py -v`
  Expected: PASS (1/1).

- [ ] **Step 5: Commit changes**
  Run:
  ```bash
  git add tests/test_company_profile.py Report/chapters/introduction.tex
  git commit -m "feat(report): add host organization profile section for IQ Business Advisors"
  ```

---

### Task 2: Multi-Pass PDF Compilation & Document Layout Verification

**Files:**
- Modify: `Report/main.pdf`, `Report/main.log`

**Interfaces:**
- Consumes: Updated `Report/chapters/introduction.tex`
- Produces: Updated `Report/main.pdf` with synchronized TOC and PDF bookmarks

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
  - Verify `Report/main.pdf` TOC contains `1.2 Host Organization Profile: IQ Business Advisors`.
  - Verify page text extraction on Chapter 1 pages contains all key terms.
  - Verify total page count expands cleanly without broken layout.

- [ ] **Step 3: Commit updated compiled PDF and build log**
  Run:
  ```bash
  git add Report/main.pdf Report/main.log
  git commit -m "docs(report): recompile thesis PDF with synchronized company profile TOC"
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
  Expected: All 17 tests PASS.

- [ ] **Step 2: Verify git status is clean**
  Run:
  ```bash
  git status
  ```
  Expected: Working tree clean.
