# Rectify System Architecture and Orchestration Figure (Figure 5.2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rectify Figure 5.2 (`fig:seq_diagram`) in `Report/chapters/implementation.tex` to eliminate extreme horizontal crowding, overlapping text/borders, and colliding arrow labels by introducing an anti-collision geometry with 1.4cm inter-engine spacing, pill-badge data labels, balanced controller widths, a closed-loop orchestration flow, and responsive scaling via `\resizebox{\textwidth}{!}`, preserving the 39-page document budget.

**Architecture:** Re-architect the 2-tier TikZ layout into a balanced coordinate grid:
- Top Tier: `User Input` (-8.8cm), `Streamlit UI` (0cm, width 10cm), and `Output View` (+8.8cm) with generous 2.1cm clearance.
- Bottom Tier: 5 Engine Cards (`DataFetcher`, `FinancialParser`, `RatioEngine`, `OutlierEngine`, `BenchmarkCore`) spaced with 1.4cm gaps between boxes.
- Connector Flow: Closed orchestration feedback loop (User -> Streamlit UI -> DataFetcher -> ... -> BenchmarkCore -> Streamlit UI -> Output View).
- Inter-stage Data Labels: Elevated on pill badge nodes with solid white backgrounds (`Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask`) with zero border or text collisions.
- Scaling: `\resizebox{\textwidth}{!}` ensures full width utilization without margin overflow or page spillover.

**Tech Stack:** LaTeX, TikZ (`positioning`, `calc`, `arrows.meta`, `shapes.geometric`), pdfLaTeX, Python (PyMuPDF `fitz`, `pytest`).

## Global Constraints
- Preserve exact 39-page document budget (Figure 5.2 must fit cleanly on Page 30 below Section 5.3 text; Chapter 6 begins cleanly on Page 31).
- 0 fatal LaTeX errors, 0 undefined references, 0 undefined citations in `Report/main.log`.
- Color palette: `peachbg` (`RGB{253, 238, 226}`) for controller, `lavenderbg` (`RGB{238, 240, 252}`) for engines, `boxborder` (`RGB{40, 45, 55}`).
- Arrowheads: `>={Stealth[length=6pt, width=4pt]}`, `thick`, `draw=boxborder`.
- No raw `\rule` lines cutting through node text or colliding with arrows.
- Do NOT run `git diff` without pathspec on `Report/main.pdf` directly.

---

### Task 1: Re-architect Figure 5.2 in `Report/chapters/implementation.tex` & Create Unit Tests

**Files:**
- Modify: `Report/chapters/implementation.tex:120-254`
- Create: `tests/test_system_architecture_figure.py`

**Interfaces:**
- Consumes: Architectural specifications from `/grill-me` alignment.
- Produces: Clean, anti-collision TikZ diagram in `Report/chapters/implementation.tex` and pytest verification suite.

- [ ] **Step 1: Write failing test in `tests/test_system_architecture_figure.py`**
  Verify:
  - `Report/chapters/implementation.tex` contains `\resizebox{\textwidth}{!}`.
  - Figure 5.2 contains pill badge node tags: `fill=white`, `Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask`.
  - Top row nodes (`User Input`, `Streamlit UI`, `Output View`) have non-colliding widths (`minimum width` $\le 10.5\text{cm}$ for controller).
  - Removal of ugly unpadded `\rule{1.9cm}{0.4pt}` cutting across engine text.
  - Presence of closed loop orchestration steps: `1. Dispatches`, `2. Delivers`, `3. Renders`.

- [ ] **Step 2: Run pytest to verify test fails**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: FAIL (missing new styling and structure).

- [ ] **Step 3: Implement rectified TikZ code in `Report/chapters/implementation.tex`**
  - Define local colors: `peachbg`, `peachborder`, `lavenderbg`, `lavenderborder`, `boxborder`, `darktext`.
  - Wrap in `\resizebox{\textwidth}{!}{% \begin{tikzpicture}[...] ... \end{tikzpicture}}`.
  - Set balanced node widths:
    - `orchestrator`: width 10.0cm, height 1.1cm.
    - `io_box`: width 3.2cm, height 1.2cm, `text width=3.0cm`.
    - `engine`: width 3.0cm, height 2.6cm, `text width=2.85cm`.
    - `tag`: `fill=white, draw=lavenderborder, rounded corners=3pt, inner sep=2pt, font=\scriptsize\bfseries`.
  - Position bottom engines with 1.4cm gaps:
    - `fetcher` at $(-8.8, -1.5)$
    - `parser` at $(-4.4, -1.5)$
    - `ratio` at $(0.0, -1.5)$
    - `outlier` at $(4.4, -1.5)$
    - `core` at $(8.8, -1.5)$
  - Position top row:
    - `user` at $(-8.8, 2.8)$
    - `app` at $(0.0, 2.8)$
    - `output` at $(8.8, 2.8)$
  - Draw clean closed-loop arrows:
    - `(user) -- node[above, font=\scriptsize\bfseries] {Config \& Tickers} (app.west)`
    - `($(app.south -| fetcher.north)$) -- node[left, font=\scriptsize\bfseries, align=right] {1. Dispatches\\Fetch Job} ($(fetcher.north)$)`
    - Intermediate pipeline arrows with centered pill badges (`Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask`).
    - `($(core.north)$) -- node[right, font=\scriptsize\bfseries, align=left] {2. Delivers Scores\\\& Peer Baselines} ($(app.south -| core.north)$)`
    - `(app.east) -- node[above, font=\scriptsize\bfseries] {3. Renders Views} (output.west)`

- [ ] **Step 4: Run pytest to verify test passes**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: PASS.

- [ ] **Step 5: Commit changes**
  ```bash
  git add Report/chapters/implementation.tex tests/test_system_architecture_figure.py
  git commit -m "feat(report): rectify Figure 5.2 architecture with anti-collision layout and closed loop orchestration"
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
  - Verify Figure 5.2 is cleanly located on Page 30 (0-indexed 29).
  - Verify text elements from Figure 5.2 are cleanly extracted (`DataFetcher`, `FinancialParser`, `RatioEngine`, `OutlierEngine`, `BenchmarkCore`, `Streamlit UI`, `Raw DF`, `Parsed DF`, `30+ Ratios`, `Outlier Mask`).
  - Verify Chapter 6 begins cleanly on Page 31.

- [ ] **Step 3: Commit updated compiled PDF and build log**
  ```bash
  git add Report/main.pdf Report/main.log tests/test_system_architecture_figure.py
  git commit -m "docs(report): recompile thesis PDF with rectified Figure 5.2"
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
  Expected: All 20 tests PASS.

- [ ] **Step 2: Verify git status is clean**
  Run:
  ```bash
  git status
  ```
  Expected: Working tree clean.
