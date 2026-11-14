# Spacious 3-Tier System Architecture Figure (Figure 5.2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Figure 5.2 (`fig:seq_diagram`) in `Report/chapters/implementation.tex` into a spacious, publication-grade 3-tier architecture diagram that completely eliminates crowding, overlaps, and label collisions while fitting cleanly on Page 30 and preserving the 39-page thesis budget.

**Architecture:** Restructure the single horizontal 5-box row into a balanced 3-tier layout:
- **Tier 1 (Top Controller Layer):** `User Input` (-5.5cm) $\longrightarrow$ `Streamlit UI` (0cm, width 6.8cm) $\longrightarrow$ `Output View` (+5.5cm) with 1.8cm clearance for "Config & Tickers" and "3. Renders Views".
- **Tier 2 (Ingestion & Feature Kernel):** 3 wide cards (`DataFetcher`, `FinancialParser`, `RatioEngine`) centered at -5.2cm, 0.0cm, +5.2cm (width 3.6cm each) with generous 1.6cm inter-card gaps for inline `[Raw DF]` and `[Parsed DF]` badges.
- **Tier 3 (Anomaly & Benchmarking Kernel):** 2 centered wide cards (`OutlierEngine`, `BenchmarkCore`) at -2.6cm, +2.6cm (width 4.0cm each) with a 1.2cm gap for inline `[Outlier Mask]` badge.
- **Card Styling:** Distinct header-banner cards with darker-tinted header rectangles and clean, spaced bullet bodies without awkward dividing lines.
- **Connectors:** Closed feedback loop (`UI` $\to$ `DataFetcher` $\to$ `FinancialParser` $\to$ `RatioEngine` $\to$ `OutlierEngine` $\to$ `BenchmarkCore` $\to$ `UI` $\to$ `Output View`).
- **Data Tags:** Inline masked badges (`fill=white, draw=lavenderborder, inner sep=2.5pt`) centered seamlessly along the arrow paths.
- **Geometry & Budget:** Scaled via `\resizebox{0.95\textwidth}{!}` to fit vertically within the 305 pt available on Page 30, strictly preserving the 39-page document budget.

**Tech Stack:** LaTeX, TikZ (`positioning`, `calc`, `arrows.meta`, `shapes.geometric`), pdfLaTeX, Python (PyMuPDF `fitz`, `pytest`).

## Global Constraints
- Preserve exact 39-page document budget (Figure 5.2 must fit cleanly on Page 30 below Section 5.3 text; Chapter 6 begins cleanly on Page 31).
- 0 fatal LaTeX errors, 0 undefined references, 0 undefined citations in `Report/main.log`.
- Color palette: `peachbg` (`RGB{253, 238, 226}`), `lavenderbg` (`RGB{238, 240, 252}`), `lavenderhead` (`RGB{220, 225, 248}`), `boxborder` (`RGB{40, 45, 55}`).
- Arrowheads: `>={Stealth[length=6pt, width=4pt]}`, `thick`, `draw=boxborder`.
- No raw unpadded `\rule` lines cutting through text.
- Do NOT run `git diff` without pathspec on `Report/main.pdf` directly.

---

### Task 1: Re-architect Figure 5.2 to Spacious 3-Tier Layout in `Report/chapters/implementation.tex` & Update Unit Tests

**Files:**
- Modify: `Report/chapters/implementation.tex:120-250`
- Modify: `tests/test_system_architecture_figure.py`

**Interfaces:**
- Consumes: Specifications from `/grill-me` alignment.
- Produces: 3-tier spacious TikZ diagram in `Report/chapters/implementation.tex` and updated test suite in `tests/test_system_architecture_figure.py`.

- [ ] **Step 1: Update unit tests in `tests/test_system_architecture_figure.py`**
  Verify:
  - 3-tier structure presence: `DataFetcher`, `FinancialParser`, `RatioEngine` in Tier 2; `OutlierEngine`, `BenchmarkCore` in Tier 3.
  - Presence of inline badges: `Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask` with `fill=white`.
  - Header styling: `lavenderhead` or distinct header banner styling.
  - Closed-loop orchestration flows: `1. Dispatches`, `2. Delivers`, `3. Renders`.

- [ ] **Step 2: Run pytest to verify test fails on current 2-tier structure**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: FAIL.

- [ ] **Step 3: Implement 3-tier TikZ architecture in `Report/chapters/implementation.tex`**
  - Define local colors: `peachbg`, `peachborder`, `lavenderbg`, `lavenderborder`, `lavenderhead` (`RGB{218, 224, 250}`), `boxborder`, `darktext`.
  - Set 3-tier coordinate layout:
    - **Tier 1 (Top, y=3.2):**
      - `user` at (-5.5, 3.2), width 3.2cm, height 1.1cm
      - `app` at (0.0, 3.2), width 6.6cm, height 1.1cm
      - `output` at (5.5, 3.2), width 3.2cm, height 1.1cm
    - **Tier 2 (Middle, y=0.5):**
      - `fetcher` at (-5.2, 0.5), width 3.6cm, height 2.2cm
      - `parser` at (0.0, 0.5), width 3.6cm, height 2.2cm
      - `ratio` at (5.2, 0.5), width 3.6cm, height 2.2cm
    - **Tier 3 (Bottom, y=-2.4):**
      - `outlier` at (-2.6, -2.4), width 4.0cm, height 2.2cm
      - `core` at (2.6, -2.4), width 4.0cm, height 2.2cm
  - Style each card with header banner:
    - Bold centered header banner at top of card.
    - Spacious, padded bullet points in body area.
  - Draw clean non-crossing connectors:
    - `(user.east) -- node[above, font=\scriptsize\bfseries] {Config \& Tickers} (app.west)`
    - `(app.south -| fetcher.north) -- node[left, font=\scriptsize\bfseries, align=right] {1. Dispatches\\Fetch Job} (fetcher.north)`
    - `(fetcher.east) -- node[midway, tag] {Raw DF} (parser.west)`
    - `(parser.east) -- node[midway, tag] {Parsed DF} (ratio.west)`
    - `(ratio.south) |- node[pos=0.6, tag] {30+ Ratios} (outlier.east)` (or clean orthogonal corner with tag)
    - `(outlier.east) -- node[midway, tag] {Outlier Mask} (core.west)`
    - `(core.north) -- node[right, font=\scriptsize\bfseries, align=left] {2. Delivers Scores\\\& Peer Baselines} (app.south -| core.north)`
    - `(app.east) -- node[above, font=\scriptsize\bfseries] {3. Renders Views} (output.west)`
  - Scale with `\resizebox{0.96\textwidth}{!}{% ... }` to fit standard margin without overflow.

- [ ] **Step 4: Run pytest to verify unit tests pass**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: PASS.

- [ ] **Step 5: Commit changes**
  ```bash
  git add Report/chapters/implementation.tex tests/test_system_architecture_figure.py
  git commit -m "feat(report): restructure Figure 5.2 into spacious 3-tier architecture with header cards and inline badges"
  ```

---

### Task 2: Multi-Pass PDF Compilation & Page 30 Layout Verification

**Files:**
- Modify: `Report/main.pdf`, `Report/main.log`
- Modify: `tests/test_system_architecture_figure.py`

**Interfaces:**
- Consumes: Updated `Report/chapters/implementation.tex`
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
  Run Python validation:
  - Verify `Report/main.log` has 0 fatal errors, 0 undefined references, 0 undefined citations.
  - Verify `Report/main.pdf` has total page count of exactly 39 pages.
  - Verify Figure 5.2 is cleanly located on Page 30 (0-indexed 29) below Section 5.3 text.
  - Verify text elements from Figure 5.2 are cleanly extracted (`DataFetcher`, `FinancialParser`, `RatioEngine`, `OutlierEngine`, `BenchmarkCore`, `Streamlit UI`, `Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask`).
  - Verify Chapter 6 begins cleanly on Page 31.

- [ ] **Step 3: Commit updated compiled PDF and build log**
  ```bash
  git add Report/main.pdf Report/main.log tests/test_system_architecture_figure.py
  git commit -m "docs(report): recompile thesis PDF with spacious 3-tier Figure 5.2"
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
  Expected: All 21 tests PASS.

- [ ] **Step 2: Verify git status is clean**
  Run:
  ```bash
  git status
  ```
  Expected: Working tree clean.
