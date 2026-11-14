# Integrate User-Provided Figure 5.2 LaTeX Snippet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Figure 5.2 in `Report/chapters/implementation.tex` with the user-provided TikZ implementation featuring `\pipebox` modular cards, split top/bottom flow labels (`Raw`/`DF`, `Parsed`/`DF`, etc.), and custom HTML palette, preserving `\label{fig:seq_diagram}` and the 39-page thesis budget.

**Architecture:** Integrate the user's snippet directly into `Report/chapters/implementation.tex` lines 120-250:
- Colors: `uifill` (`#F8E7DA`), `uiborder` (`#8C7365`), `pipefill` (`#E9EDFC`), `pipeborder` (`#99A7D6`), `linegray` (`#333333`).
- Macro: `\providecommand{\pipebox}[5]` for uniform bottom pipeline module formatting.
- Diagram structure: 5 uniform bottom pipeline modules (`DataFetcher`, `FinancialParser`, `RatioEngine`, `OutlierEngine`, `BenchmarkCore`), top controller `Streamlit UI (app.py) [Central Controller]`, perimeter boxes (`User Input`, `Output View`).
- Connector routing: Box-to-box vertical orchestration arrows, top horizontal arrows (`Config & Tickers`, `3. Renders Views`), and bottom pipeline arrows with split top and bottom flow labels (`flowtop` / `flowbot`).
- Label: `\label{fig:seq_diagram}` preserved for cross-referencing.
- Budget: Verified on Page 30 below Section 5.3 text, maintaining 39 pages total.

**Tech Stack:** LaTeX, TikZ (`positioning`, `arrows.meta`), pdfLaTeX, Python (PyMuPDF `fitz`, `pytest`).

## Global Constraints
- Preserve exact 39-page document budget (Figure 5.2 must fit cleanly on Page 30 below Section 5.3 text; Chapter 6 begins cleanly on Page 31).
- 0 fatal LaTeX errors, 0 undefined references, 0 undefined citations in `Report/main.log`.
- Keep `\label{fig:seq_diagram}` so existing in-text cross-references remain valid.
- Do NOT run `git diff` without pathspec on `Report/main.pdf` directly.

---

### Task 1: Replace Figure 5.2 in `Report/chapters/implementation.tex` & Update Unit Tests

**Files:**
- Modify: `Report/chapters/implementation.tex:120-250`
- Modify: `tests/test_system_architecture_figure.py`

**Interfaces:**
- Consumes: User-provided LaTeX snippet verbatim.
- Produces: Updated `Report/chapters/implementation.tex` with the user's snippet and updated unit tests.

- [ ] **Step 1: Update unit tests in `tests/test_system_architecture_figure.py`**
  Add assertions checking:
  - Color definitions: `uifill`, `uiborder`, `pipefill`, `pipeborder`, `linegray`.
  - Helper macro: `\providecommand{\pipebox}` or `\pipebox`.
  - Node styles: `topbox`, `uibox`, `pipe`, `flowtop`, `flowbot`, `toplbl`, `vertlbl`, `arr`.
  - Split labels: `flowtop` (`Raw`, `Parsed`, `30+`, `Outlier`) and `flowbot` (`DF`, `Ratios`, `Mask`).
  - Label: `\label{fig:seq_diagram}`.

- [ ] **Step 2: Run pytest to observe test failure**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: FAIL on new macro and style assertions.

- [ ] **Step 3: Replace Figure 5.2 in `Report/chapters/implementation.tex`**
  Insert the user's snippet with `\providecommand{\pipebox}` and `\label{fig:seq_diagram}`:
  ```latex
  % Custom colors matching the diagram
  \definecolor{uifill}{HTML}{F8E7DA}
  \definecolor{uiborder}{HTML}{8C7365}
  \definecolor{pipefill}{HTML}{E9EDFC}
  \definecolor{pipeborder}{HTML}{99A7D6}
  \definecolor{linegray}{HTML}{333333}

  % Helper macro for uniform bottom pipeline cards (4 single-line bullets each)
  \providecommand{\pipebox}[5]{%
    {\fontsize{9.5}{11}\selectfont\textbf{#1}}\par\vspace{4.5pt}%
    {\fontsize{8}{10.5}\selectfont
      \textbullet~#2\par
      \textbullet~#3\par
      \textbullet~#4\par
      \textbullet~#5\par
    }%
  }

  \begin{figure}[htbp]
  \centering
  \resizebox{\textwidth}{!}{%
  \begin{tikzpicture}[
      font=\rmfamily,
      topbox/.style={
          rectangle,
          rounded corners=4pt,
          draw=linegray,
          line width=0.75pt,
          fill=white,
          align=center,
          text width=2.75cm,
          minimum height=1.35cm,
          inner xsep=5pt,
          inner ysep=6pt,
          font=\fontsize{8.2}{10}\selectfont
      },
      uibox/.style={
          rectangle,
          rounded corners=5pt,
          draw=uiborder,
          line width=0.75pt,
          fill=uifill,
          align=center,
          minimum height=1.05cm,
          inner xsep=16pt,
          inner ysep=9pt,
          font=\fontsize{9.5}{11}\selectfont
      },
      pipe/.style={
          rectangle,
          rounded corners=5pt,
          draw=pipeborder,
          line width=0.75pt,
          fill=pipefill,
          align=left,
          text width=2.75cm,
          minimum height=2.40cm,
          inner xsep=5pt,
          inner ysep=7pt
      },
      flowtop/.style={
          above=2.5pt,
          align=center,
          font=\fontsize{8}{9.5}\selectfont\bfseries,
          text=black
      },
      flowbot/.style={
          below=2.5pt,
          align=center,
          font=\fontsize{8}{9.5}\selectfont\bfseries,
          text=black
      },
      toplbl/.style={
          above=3.5pt,
          align=center,
          font=\fontsize{8}{9.5}\selectfont\bfseries,
          text=black
      },
      vertlbl/.style={
          midway,
          font=\fontsize{8}{9.5}\selectfont\bfseries,
          text=black
      },
      arr/.style={
          -{Stealth[length=2.4mm, width=1.6mm]},
          draw=linegray,
          line width=0.8pt
      }
  ]

  % --- Bottom Row: 5 Uniform Pipeline Modules ---
  \node[pipe] (df) {\pipebox{DataFetcher}{yfinance API}{Parquet Cache}{Market Info}{Async Pulls}};
  \node[pipe, right=1.40cm of df] (fp) {\pipebox{FinancialParser}{60-Field Synonyms}{Canonical Map}{GAAP / Ind-AS}{Type Coercion}};
  \node[pipe, right=1.40cm of fp] (re) {\pipebox{RatioEngine}{30+ Ratios}{5 Core Pillars}{YoY/QoQ Trends}{CAGR Growth}};
  \node[pipe, right=1.40cm of re] (oe) {\pipebox{OutlierEngine}{Tukey IQR Fences}{Robust Z-Scores}{Isolation Forest}{Severity Scores}};
  \node[pipe, right=1.40cm of oe] (bc) {\pipebox{BenchmarkCore}{Outlier Masking}{RobustScaler}{Sigmoid Scoring}{Percentile Ranks}};

  % --- Top Row: Controller & Views ---
  \node[uibox, above=2.25cm of re.north] (ui) {\textbf{Streamlit UI (}\texttt{app.py}\textbf{) [Central Controller]}};
  \node[topbox] (input) at (df.center |- ui.center) {{\fontsize{9.5}{11}\selectfont\textbf{User Input}}\\[2.5pt]Sector/Tickers \&\\Config Controls};
  \node[topbox] (output) at (bc.center |- ui.center) {{\fontsize{9.5}{11}\selectfont\textbf{Output View}}\\[2.5pt]Heatmaps,\\Scorecards\\\& Excel Reports};

  % --- Top Horizontal Arrows ---
  \draw[arr] (input.east) -- node[toplbl] {Config \& Tickers} (ui.west);
  \draw[arr] (ui.east) -- node[toplbl] {3. Renders Views} (output.west);

  % --- Box-to-Box Vertical Orchestration Arrows ---
  \draw[arr] (input.south) -- node[vertlbl, left=6pt, align=right] {1. Dispatches\\Fetch Job} (df.north);
  \draw[arr] (bc.north) -- node[vertlbl, right=6pt, align=left] {2. Delivers Scores\\\& Peer Baselines} (output.south);

  % --- Bottom Pipeline Horizontal Arrows (Split Top & Bottom Labels) ---
  \draw[arr] (df.east) -- node[flowtop] {Raw} node[flowbot] {DF} (fp.west);
  \draw[arr] (fp.east) -- node[flowtop] {Parsed} node[flowbot] {DF} (re.west);
  \draw[arr] (re.east) -- node[flowtop] {30+} node[flowbot] {Ratios} (oe.west);
  \draw[arr] (oe.east) -- node[flowtop] {Outlier} node[flowbot] {Mask} (bc.west);

  \end{tikzpicture}%
  }
  \caption{System Architecture and Orchestration Pipeline of the Benchmarking Engine}
  \label{fig:seq_diagram}
  \end{figure}
  ```

- [ ] **Step 4: Run pytest to verify unit tests pass**
  Run:
  ```bash
  python -m pytest tests/test_system_architecture_figure.py
  ```
  Expected: PASS (unit assertions).

- [ ] **Step 5: Commit changes**
  ```bash
  git add Report/chapters/implementation.tex tests/test_system_architecture_figure.py
  git commit -m "feat(report): integrate user-provided Figure 5.2 snippet with uniform pipeboxes and split flow labels"
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
  - Verify text elements from Figure 5.2 are cleanly extracted (`DataFetcher`, `FinancialParser`, `RatioEngine`, `OutlierEngine`, `BenchmarkCore`, `Streamlit UI`, `Raw`, `DF`, `Parsed`, `30+`, `Ratios`, `Outlier`, `Mask`).
  - Verify Chapter 6 begins cleanly on Page 31.

- [ ] **Step 3: Commit updated compiled PDF and build log**
  ```bash
  git add Report/main.pdf Report/main.log tests/test_system_architecture_figure.py
  git commit -m "docs(report): recompile thesis PDF with integrated user Figure 5.2"
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
