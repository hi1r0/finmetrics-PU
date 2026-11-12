# FinMetrics Suite LaTeX Report Phase 1 Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `Report/main.tex` and its associated chapter files (`Report/chapters/*.tex`) to synchronize the academic thesis with the refactored codebase, removing all references to TallySync ERP, private client benchmarking, and K-Means clustering while featuring real NSE listed sector benchmarks (Maruti Suzuki case study) and ensuring a clean compilation to `Report/main.pdf`.

**Architecture:** Systematic file-by-file refactor across all 8 chapters/appendices, removing dead architectural constructs and updating TikZ diagrams, mathematical glossaries, pseudocode algorithms, and empirical tables. Each task ends with a LaTeX compilation check to guarantee that no syntax or formatting regressions occur.

**Tech Stack:** LaTeX, pdfTeX (MiKTeX 25.12), BibTeX, TikZ / PGF, booktabs, algorithmicx.

## Global Constraints
- Target PDF output: `D:\Python\PYCHARM\Projects\finmetrics\Report\main.pdf`
- Root LaTeX source: `D:\Python\PYCHARM\Projects\finmetrics\Report\main.tex`
- Chapter files: `D:\Python\PYCHARM\Projects\finmetrics\Report\chapters\*.tex`
- Submission Date: `NOVEMBER 2026`
- Academic Year: `2026-27`
- Student Name: `N Rohit Vedhanandh`, Reg No: `25MSQUFPY0002`
- Title: `FinMetrics Suite`
- Subtitle: `An AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, and Strategic Benchmarking System`
- Zero fatal compilation errors and zero broken references (`??`) allowed in final build.

---

### Task 1: Update Root Document, Metadata, and Front Matter

**Files:**
- Modify: `Report/main.tex`

**Interfaces:**
- Consumes: Existing preamble, layout configurations, and styling.
- Produces: Updated `\hypersetup`, title page, abstract, and abbreviations table.

- [ ] **Step 1: Edit `Report/main.tex`**
  - Update `\hypersetup` with:
    - `pdftitle={FinMetrics Suite: An AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, and Strategic Benchmarking System}`
    - `pdfkeywords={Financial Analysis, Anomaly Detection, Outlier Screening, Robust Statistics, Modified Z-Score, Isolation Forest, Pillar Scoring, Strategic Benchmarking, NSE Equities}`
  - On title page:
    - Update subtitle: `{\large An AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, \\ and Strategic Benchmarking System \par}`
    - Update submission date: `\textbf{\large NOVEMBER 2026}`
  - On Abstract page:
    - Revise paragraph 2 to remove TallySync ERP, 50,000-row chunk streaming, and $10^{-6}$ INR trial balance balancing.
    - Highlight the 5-pillar composite scoring model (0-100 bounded Sigmoid transformation), dynamic Gemini AI sector discovery, and interactive visual dashboards.
  - In List of Abbreviations table:
    - Remove `\textbf{ERP} & Enterprise Resource Planning \\`
    - Remove `\textbf{JV} & Journal Voucher \\`

- [ ] **Step 2: Compile `main.tex` to verify syntax**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation of front matter with no fatal errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/main.tex
  git commit -m "docs(report): update metadata, title page, abstract, and abbreviations in main.tex"
  ```

---

### Task 2: Update Introduction (Chapter 1)

**Files:**
- Modify: `Report/chapters/introduction.tex`

**Interfaces:**
- Consumes: `Report/main.tex` include statement.
- Produces: Chapter 1 text without Public-Private divide, with a streamlined 2-box bottleneck diagram.

- [ ] **Step 1: Edit `Report/chapters/introduction.tex`**
  - Section 1.1 (Background): In paragraph 2, update the final sentence to remove "and integrate private enterprise records against public industry benchmarks in real time", replacing it with "and benchmark company financial health objectively against robust industry baselines in real time."
  - Section 1.2 (Problem Statement):
    - Remove item 3: `\item \textbf{The Public-Private Benchmarking Divide}: ...`
    - Update introductory sentence to: `Automated cross-sectional financial analysis is constrained by two primary technical bottlenecks:`
  - Figure 1.1 (`fig:bottlenecks`):
    - Update TikZ figure to contain 2 boxes instead of 3:
      `\node (box1) [block] {\textbf{Reporting Nomenclature}\\Companies report identical metrics under arbitrary names; breaks automated scrapers.};`
      `\node (box2) [block, right=of box1] {\textbf{Data Integrity Risks}\\Outliers, data errors, or extreme structures distort peer baselines.};`
      `\draw [arrow] (box1) -- (box2);`
  - Section 1.3 (Objectives):
    - Remove bullet: `\item \textbf{Double-Entry ERP Synchronization}: ...`
    - Retain: Automated Financial Harvesting, Standardized Alias Processing, Robust Anomaly Scanning, Weighted Pillar Scoring, and Strategic Benchmarking Diagnostics.
  - Section 1.4 (Scope):
    - Remove bullet: `\item Ingestion support for double-entry Tally ERP journal voucher/ledger master logs...`
    - In audience sentence, remove `and SME managers`.
  - Section 1.5 (Motivation):
    - Remove references to local business owners uploading raw Tally files.
    - Emphasize providing institutional-grade competitive intelligence and anomaly detection for equity analysts and financial researchers.

- [ ] **Step 2: Compile to verify Chapter 1**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/introduction.tex
  git commit -m "docs(report): remove public-private divide and ERP scope from introduction.tex"
  ```

---

### Task 3: Update Literature Survey (Chapter 2)

**Files:**
- Modify: `Report/chapters/literature_survey.tex`

**Interfaces:**
- Consumes: Citations in `Report/references.bib`.
- Produces: Chapter 2 literature review focused on robust statistics and isolation forest without K-Means archetypes or ERP gaps.

- [ ] **Step 1: Edit `Report/chapters/literature_survey.tex`**
  - Section 2.1 (Existing Methodologies): In bullet 2 (`Proprietary Financial Terminals`), revise the closing sentence to state: "However, their high annual licensing fees (\$24,000+ per user) and closed database architectures prevent independent researchers from easily integrating custom statistical outlier screening models."
  - Remove Section 2.3 (`K-Means Clustering & Corporate Archetypes`) including lines 48-53.
  - Update Figure 2.2 (`fig:outlier_cluster_pipeline`):
    - In TikZ diagram, remove Level 4 (K-Means Clustering) and Level 5 (Corporate Archetypes).
    - End the pipeline cleanly at Level 3 (Clean Masked Dataset & Robust Baselines).
    - Update caption to: `\caption{Multi-layered Robust Outlier Masking and Baseline Generation Pipeline}`.
  - Section 2.4 (Research Gaps):
    - Update introductory sentence: `Two critical research gaps remain in current financial intelligence frameworks:`
    - Remove item 3: `\item \textbf{Lack of ERP Double-Entry Integration}: ...`

- [ ] **Step 2: Compile to verify Chapter 2**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/literature_survey.tex
  git commit -m "docs(report): remove K-Means clustering and ERP research gap from literature_survey.tex"
  ```

---

### Task 4: Update System Analysis and Design (Chapter 3)

**Files:**
- Modify: `Report/chapters/system_design.tex`

**Interfaces:**
- Consumes: Module definitions in `modules/*.py`.
- Produces: Chapter 3 describing the single-track Phase 1 architecture, DFDs, and active modules.

- [ ] **Step 1: Edit `Report/chapters/system_design.tex`**
  - Section 3.1 (System Architecture): In Analytical Kernel Layer, remove `Tally Bridge` and `Client Comparator`.
  - Section 3.2 (System Workflow):
    - Change heading to: `\section{System Workflow and Execution Pipeline}`
    - Remove Subsection 3.2.2 (`Phase 2: Private Enterprise Client Benchmarking`).
    - Convert Subsection 3.2.1 into the primary end-to-end numbered workflow:
      1. Scope definition (pre-mapped Sector, Industry, or Gemini AI Search).
      2. Environment check & API key configuration.
      3. AI ticker discovery via Gemini (appending exchange suffixes like `.NS`).
      4. Statement harvesting via `data_fetcher.py` and local Parquet caching.
      5. Canonical synonym resolution via `financial_parser.py` (60-field alias map).
      6. Ratio calculation via `ratio_engine.py` (5 core pillars).
      7. Multi-tier outlier detection via `outlier_engine.py` (IQR, MAD Z-score, Isolation Forest).
      8. Cell-level outlier masking and baseline generation via `benchmark_core.py`.
      9. Sigmoid scoring (0-100), pillar aggregation, and percentile ranking via `benchmark_classifier.py`.
      10. Output generation: interactive Streamlit tabs, styled multi-sheet Excel reports, and Gemini diagnostic commentary.
  - Figure 3.1 (`fig:workflow_flowchart`):
    - Replace the dual-phase split diagram with a clean vertical modular pipeline matching `SYSTEM_LOGICS_AND_BLUEPRINT.md`:
      `Streamlit UI` $\to$ `Data Ingestion (Data Fetcher & Financial Parser)` $\to$ `Ratio Engine` $\to$ `Outlier Engine` $\to$ `Benchmark Core` $\to$ `Visualization & Report Generator`.
    - Update caption to: `\caption{End-to-End System Architecture and Processing Pipeline}`.
  - Section 3.3 (Data Flow Diagrams):
    - DFD Level 0 (Figure 3.2): In the left arrows between User and Suite, replace `Ingest / Config` with `Scope / Config`.
    - DFD Level 1 (Figure 3.3): Update label on the input arrow from `User` to `1.0` from `ERP / Manual` to `Sector / Scope`.
  - Section 3.4 (Module Descriptions):
    - Remove bullet: `\textbf{tally\_bridge.py}: ...`
    - Remove bullet: `\textbf{client\_comparator.py}: ...`
    - Add/retain: `benchmark_store.py` (Persists and retrieves precomputed sector benchmark matrices in Parquet format).

- [ ] **Step 2: Compile to verify Chapter 3**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/system_design.tex
  git commit -m "docs(report): update architecture diagram, workflow, and modules in system_design.tex"
  ```

---

### Task 5: Update Algorithms and Methodology (Chapter 4)

**Files:**
- Modify: `Report/chapters/algorithms.tex`

**Interfaces:**
- Consumes: Math formulations from `modules/outlier_engine.py` and `modules/benchmark_core.py`.
- Produces: Chapter 4 presenting univariate and multivariate outlier methods without K-Means or Tally.

- [ ] **Step 1: Edit `Report/chapters/algorithms.tex`**
  - Remove Section 4.4 (`K-Means Clustering for Peer Archetypes`) including lines 194-235 (equations, centroid profiles, and Table 4.3).
  - Remove Section 4.5 (`TallySync Double-Entry Bridge Ingestion`) lines 236-241.
  - Section 4.6 (Algorithms Pseudocode):
    - Update introductory text: remove references to TallySync double-entry journal processing.
    - In Table 4.4 (`tab:glossary_pseudocode`), remove:
      `$\text{dr}, \text{cr}$ & Debit and credit ledger transaction amounts from streamed journal lines. \\`
      `$\mathbf{P}$ & Hash-map storing aggregated double-entry balances for financial pillars. \\`
    - Retain Subsection 4.6.1 (`Univariate Outlier Detection and Baseline Masking`) and Algorithm 1 (`alg:outliers`).
    - Remove Subsection 4.6.2 (`TallySync ERP Double-Entry Journal Aggregator`) and Algorithm 2 (`alg:tally`).

- [ ] **Step 2: Compile to verify Chapter 4**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/algorithms.tex
  git commit -m "docs(report): remove K-Means and Tally pseudocode from algorithms.tex"
  ```

---

### Task 6: Update Implementation (Chapter 5)

**Files:**
- Modify: `Report/chapters/implementation.tex`

**Interfaces:**
- Consumes: Codebase directory structure and active module implementations.
- Produces: Chapter 5 with updated development lifecycle, directory tree, and Phase 1 orchestration diagram.

- [ ] **Step 1: Edit `Report/chapters/implementation.tex`**
  - Section 5.2 (Tools and Libraries):
    - Under `Pandas`, remove: `mapping Tally ERP ledgers, and streaming journal logs in chunks.`
    - Under `Scikit-Learn`, revise to: `Powers the machine learning engines: RobustScaler for median-based scaling and IsolationForest for multi-dimensional anomaly detection.`
  - Figure 5.1 (`fig:dev_workflow`):
    - In TikZ flowchart, remove step 4 (`4. ERP Synchronization Bridge`).
    - Re-index steps to 5 clear phases:
      1. `1. Planning & Scoping` (30+ financial ratios, 5-pillar composite structure).
      2. `2. Data Ingestion & Normalization` (yfinance harvester and 60-field synonym parser).
      3. `3. Mathematical & Anomaly Engines` (RatioEngine, outlier filters IQR/Z/IF).
      4. `4. Benchmarking & Scoring Pipeline` (outlier masking, robust scaling, sigmoid scoring, Gemini integration).
      5. `5. Application Release & Reporting` (Streamlit control dashboard, Excel exporter).
  - Section 5.4 (Code Structure Explanation):
    - Remove `tally_bridge.py` and `client_comparator.py` from the file listing.
    - Add `benchmark_store.py` (Local benchmark cache persistence).
  - Section 5.5 (Module-wise Implementation Details):
    - Remove Subsection 5.5.3 (`Tally Bridge Streamer (tally_bridge.py)`).
  - Section 5.6 (System Component Integration) & Figure 5.2:
    - Replace text and Figure 5.2 with the Phase 1 Orchestration Pipeline:
      - Core Controller: Streamlit UI (`app.py`).
      - Coordinated modules: `DataFetcher` $\to$ `FinancialParser` $\to$ `RatioEngine` $\to$ `OutlierEngine` $\to$ `BenchmarkCore`.
      - Output: Interactive Heatmaps, Scorecards, Styled Excel Reports.
    - Update caption to: `\caption{System Architecture and Orchestration Pipeline of the Benchmarking Engine}`.

- [ ] **Step 2: Compile to verify Chapter 5**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/implementation.tex
  git commit -m "docs(report): update workflow, code tree, and orchestration pipeline in implementation.tex"
  ```

---

### Task 7: Update Results and Discussion (Chapter 6)

**Files:**
- Modify: `Report/chapters/results.tex`

**Interfaces:**
- Consumes: Precomputed benchmark values for Automobile sector from `data/benchmarks/automobile/`.
- Produces: Chapter 6 with Maruti Suzuki case study and clean pipeline performance timings.

- [ ] **Step 1: Edit `Report/chapters/results.tex`**
  - Section 6.1 (Experimental Setup):
    - Revise to state testing was conducted on 13 public market sectors using real NSE equity filings, evaluating peer groups ranging from 5 to 29 companies. Remove the private Tally ERP testing protocol.
  - Section 6.2 (Results Analysis):
    - Remove Tally ledger aggregation metrics ($590M$ debit/credit balance, $10^{-6}$ INR rounding limit).
    - Introduce the Cross-Sectional Sector Ingestion Results: describe automated normalization across NSE Automobile sector constituents, verifying zero schema breaks across differing filing terminologies.
  - Section 6.3 (Outlier Masking Evaluation):
    - Retain Table 6.1 (`tab:outlier_impact`) and its analytical discussion (masking restores standard deviation from $39.54\%$ to $1.28\%$).
  - Section 6.4 (Benchmarking Case Study: Listed Enterprise Evaluation):
    - Title: `\section{Benchmarking Case Study: Listed Enterprise Evaluation}`
    - Text: Evaluate Maruti Suzuki India Limited (`MARUTI.NS`) against the 9-peer Automobile sector baseline:
      - Solvency & Liquidity: Debt-to-Equity of $0.001$, Interest Coverage of $68.38\times$ (Ranked *Elite*, Above Benchmark).
      - Asset & Inventory Velocity: Asset Turnover of $0.346$, Inventory Turnover of $4.56$ (Ranked *Elite*).
      - Profitability: Operating Margin of $9.68\%$ (Ranked *Weak* / Near Benchmark Low relative to premium niche peers like Eicher Motors at $32.83\%$ and Bajaj Auto at $27.36\%$).
    - Subsection 6.4.1 (`Strategic Diagnostic Insights`):
      - Replace SME inventory actions with strategic analysis: Maruti's fortress zero-debt balance sheet and rapid asset velocity provide defensive resilience, but competitive margins face margin compression from rising raw material input costs and EV capital expenditures.
  - Figure 6.2 (`fig:client_scorecard`):
    - Update TikZ bar chart to display:
      1. Solvency (Debt-to-Equity / Interest Coverage): 95th Percentile (*Elite*).
      2. Asset Efficiency (Asset Turnover): 90th Percentile (*Elite*).
      3. Profitability (Operating Margin): 25th Percentile (*Weak* / Moderate).
    - Update caption to: `\caption{Maruti Suzuki India Limited: Financial Health Scorecard (Percentile Rankings)}`.
  - Section 6.5 (Performance Analysis) & Table 6.2:
    - Remove row: `Tally ERP Aggregation (100k rows) & 4.20 s \\`
    - Remove row: `UML/K-Means Clustering & 0.25 s \\`
    - Retain: Data Harvesting (14.50 s), Data Ingestion cached (1.20 s), Outlier Detection & Core Scoring (0.45 s), Excel Report Generation (1.10 s).

- [ ] **Step 2: Compile to verify Chapter 6**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 3: Commit changes**
  Run:
  ```bash
  git add Report/chapters/results.tex
  git commit -m "docs(report): replace client results with Maruti Suzuki case study in results.tex"
  ```

---

### Task 8: Update Conclusion and Appendices (Chapter 7 & Appendices)

**Files:**
- Modify: `Report/chapters/conclusion.tex`
- Modify: `Report/chapters/appendices.tex`

**Interfaces:**
- Consumes: System outcomes and core source code listing.
- Produces: Chapter 7 and Appendix A without Tally or K-Means.

- [ ] **Step 1: Edit `Report/chapters/conclusion.tex`**
  - Section 7.1 (Final Outcomes):
    - Remove bullet 3 (TallySync bridge).
    - In bullet 4, remove archetype clustering and business owner narrative; focus on 5-pillar scoring and Gemini-driven interactive diagnostics for equity analysts.
  - Section 7.2 (Contributions):
    - Replace Contribution 1 with: `\item \textbf{Standardized Financial Parsing Engine}: Implemented a 60-field synonym resolution dictionary resolving reporting nomenclature disparities across listed public corporate filings.`
    - Retain Contribution 2: Outlier-Resistant Benchmarks.
    - Replace Contribution 3 with: `\item \textbf{Bounded Multi-Pillar Scoring Architecture}: Designed a transparent 0-100 Sigmoid scoring model and contribution matrix aggregating 5 operational pillars.`
  - Section 7.3 (Future Scope):
    - Remove multi-year ERP trend analysis and direct ERP database connectors.
    - Include: automated regulatory filing scraping (SEC / MCA EDGAR parsers), real-time outlier alerting, predictive ratio time-series forecasting (ARIMA/Prophet), and cross-market international exchange coverage.

- [ ] **Step 2: Edit `Report/chapters/appendices.tex`**
  - Retain Chapter A (`Core Source Code`) with `Outlier Filtering Logic`.
  - Remove Chapter B (`Tally ERP Ingestion Formats`) and its subsections (`Ledger Master CSV Format`, `Journal Voucher CSV Format`).

- [ ] **Step 3: Compile to verify Chapter 7 & Appendices**
  Run: `cd "D:\Python\PYCHARM\Projects\finmetrics\Report"; pdflatex -interaction=nonstopmode main.tex`
  Expected: Successful compilation with 0 errors.

- [ ] **Step 4: Commit changes**
  Run:
  ```bash
  git add Report/chapters/conclusion.tex Report/chapters/appendices.tex
  git commit -m "docs(report): align conclusion and remove Tally Appendix from appendices.tex"
  ```

---

### Task 9: Full Multi-Pass Compilation, Bibliography, and Visual Quality Verification

**Files:**
- Output: `Report/main.pdf`

**Interfaces:**
- Consumes: `Report/main.tex`, all chapter `.tex` files, and `Report/references.bib`.
- Produces: Fully compiled, verified `Report/main.pdf`.

- [ ] **Step 1: Run full multi-pass compilation pipeline**
  Run:
  ```bash
  cd "D:\Python\PYCHARM\Projects\finmetrics\Report"
  pdflatex -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex
  ```
  Expected: Exit code 0 on all passes.

- [ ] **Step 2: Verify log for errors and warnings**
  Check `Report/main.log` to confirm:
  - Zero fatal errors (`! LaTeX Error`).
  - Zero undefined references (`LaTeX Warning: Reference ... undefined`).
  - Zero undefined citations (`LaTeX Warning: Citation ... undefined`).
  - Check page count and ensure bookmarks build cleanly.

- [ ] **Step 3: Commit final compiled PDF and log**
  Run:
  ```bash
  git add Report/main.pdf Report/main.log
  git commit -m "build(report): compile final synchronized thesis PDF"
  ```
