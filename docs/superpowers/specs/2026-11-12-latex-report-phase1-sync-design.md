# Design Specification: FinMetrics Suite LaTeX Report Synchronization

## 1. Overview and Objective
This document outlines the exact architectural modifications required to update the LaTeX document `Report/main.tex` and its associated chapter files (`Report/chapters/*.tex`) to produce the updated `Report/main.pdf`.

The primary objective is to synchronize the academic report with the refactored codebase (post-commits `86ac9be` and `3c1144d`), cleanly excising the removed Phase 2 subsystems (TallySync ERP double-entry ingestion, client comparison, and K-Means archetype clustering) while aligning all front matter, diagrams, algorithms, and empirical results with the active Phase 1 public listed equity engine.

---

## 2. File-by-File Changes

### 2.1 `Report/main.tex` (Root Document & Front Matter)
- **PDF Metadata (`\hypersetup`):**
  - Update `pdftitle` to `FinMetrics Suite: An AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, and Strategic Benchmarking System`.
  - Update `pdfkeywords` to remove `ERP Integration, TallySync, K-Means Clustering`.
- **Title Page:**
  - Subtitle: Change to `{\large An AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, \\ and Strategic Benchmarking System \par}`.
  - Date: Change `MAY 2026` to `NOVEMBER 2026`.
- **University Certificate Page:**
  - Academic year: Retain `2026-27`.
  - Date / Examination placeholder: Retained in standard format.
- **Abstract:**
  - Revise paragraph 2: Remove references to TallySync ERP bridge, journal streaming in 50,000 row chunks, trial balance balancing to $10^{-6}$ INR, and private SME manager workflows.
  - Emphasize automated public financial statement fetching via Yahoo Finance API, 60-field alias mapping dictionary, robust statistical filtering (Tukey IQR, MAD Modified Z-score, Isolation Forest), bounded 0-100 Sigmoid benchmark scoring across 5 operational pillars, and Gemini-powered dynamic sector discovery.
- **List of Abbreviations:**
  - Remove `ERP` (Enterprise Resource Planning) and `JV` (Journal Voucher).
  - Retain all other standard financial/ML abbreviations (`API`, `CAGR`, `COGS`, `EBIT`, `EBITDA`, `EPS`, `FP&A`, `IQR`, `MAD`, `ML`, `OCF`, `QoQ`, `ROA`, `ROCE`, `ROE`, `TTL`, `UML`, `YoY`).

---

### 2.2 `Report/chapters/introduction.tex` (Chapter 1)
- **Problem Statement (Section 1.2):**
  - Remove Item 3 (`The Public-Private Benchmarking Divide`).
  - Keep the problem focused on the two core computational bottlenecks:
    1. *Nomenclature Disparity* in financial statements.
    2. *Outlier & Baseline Distortion* across noisy sector peer groups.
- **Figure 1.1 (Bottlenecks):**
  - Update TikZ diagram from 3 boxes to 2 boxes (`Reporting Nomenclature` $\to$ `Data Integrity Risks / Outlier Distortion`).
- **Objectives (Section 1.3):**
  - Remove bullet 5 (`Double-Entry ERP Synchronization`).
- **Scope (Section 1.4):**
  - Remove bullet on Tally ERP journal voucher ingestion and SME manager audience.
- **Motivation (Section 1.5):**
  - Tighten text: remove private enterprise Tally file upload narrative; emphasize democratization of institutional-grade cross-sectional equity analytics and anomaly detection.

---

### 2.3 `Report/chapters/literature_survey.tex` (Chapter 2)
- **Existing Methodologies (Section 2.1):**
  - In Proprietary Terminals, remove references to uploading double-entry Tally ERP ledger data.
- **K-Means Clustering & Corporate Archetypes (Section 2.3):**
  - Remove Section 2.3.
- **Figure 2.2 (Multi-layered Outlier & Clustering Pipeline):**
  - Update the TikZ flowchart to end at the Clean Masked Dataset and Robust Baselines / Scoring, removing the K-Means and Archetypes steps.
- **Research Gaps (Section 2.4):**
  - Remove Item 3 (`Lack of ERP Double-Entry Integration`).

---

### 2.4 `Report/chapters/system_design.tex` (Chapter 3)
- **System Architecture (Section 3.1):**
  - Remove `tally_bridge.py` and `client_comparator.py` from the Analytical Kernel Layer description.
- **System Workflow (Section 3.2):**
  - Remove Subsection 3.2.2 (`Phase 2: Private Enterprise Client Benchmarking`).
  - Reframe Section 3.2 as a single end-to-end pipeline:
    1. Scope definition (pre-mapped sector or Gemini AI search).
    2. Statement harvesting & Parquet caching.
    3. Synonym resolution via 60-field alias dictionary.
    4. Financial ratio calculation.
    5. Outlier detection (IQR, MAD Z-Score, Isolation Forest).
    6. Cell-level masking and baseline computation.
    7. Sigmoid scoring and percentile ranking.
    8. Reporting and interactive AI diagnostics.
- **Figure 3.1 (Platform Architecture & Workflow):**
  - Replace dual-column split-bus diagram with a single-track modular architecture matching `SYSTEM_LOGICS_AND_BLUEPRINT.md`: Streamlit UI $\to$ Data Fetcher $\to$ Financial Parser $\to$ Ratio Engine $\to$ Outlier Engine $\to$ Benchmark Core $\to$ Visualization & Excel Exporter.
- **Figure 3.2 & 3.3 (Data Flow Diagrams):**
  - DFD Level 0: Clean up I/O labels.
  - DFD Level 1: Update input arrow into Process 1.0 from "ERP / Manual" to "Sector / Ticker Selection".
- **Module Descriptions (Section 3.4):**
  - Remove `tally_bridge.py` and `client_comparator.py`.
  - Detail active modules: `sector_loader.py`, `data_fetcher.py`, `financial_parser.py`, `ratio_engine.py`, `outlier_engine.py`, `benchmark_core.py`, `benchmark_classifier.py`, `report_generator.py`, `ai_handler.py`.

---

### 2.5 `Report/chapters/algorithms.tex` (Chapter 4)
- **Section Removals:**
  - Remove Section 4.4 (`K-Means Clustering for Peer Archetypes`) and Table 4.3 (`glossary_kmeans`).
  - Remove Section 4.5 (`TallySync Double-Entry Bridge Ingestion`).
  - Remove Subsection 4.6.2 (`TallySync ERP Double-Entry Journal Aggregator`) and Algorithm 2 (`ProcessTally`).
- **Retained & Refined Content:**
  - Section 4.1: Tukey Fences (IQR).
  - Section 4.2: Robust Modified Z-Score (MAD).
  - Section 4.3: Isolation Forest.
  - Table 4.2 (Pseudocode mathematical symbols): Remove $\text{dr}, \text{cr}$ and $\mathbf{P}$.
  - Algorithm 1: `DetectOutliers` (Univariate Outlier Detection and Baseline Masking).

---

### 2.6 `Report/chapters/implementation.tex` (Chapter 5)
- **Tools & Libraries (Section 5.2):**
  - Remove `KMeans` from Scikit-Learn description, focusing on `RobustScaler` and `IsolationForest`.
  - Remove Tally ledger mapping from Pandas description.
- **Figure 5.1 (Development Workflow):**
  - Remove step 4 (`ERP Synchronization Bridge`), streamlining the lifecycle across 5 stages: Planning, Ingestion & Normalization, Anomaly Engines, Scoring & Baselines, Release & Reporting.
- **Code Structure Explanation (Section 5.4):**
  - Update folder tree to remove `tally_bridge.py` and `client_comparator.py`.
- **Module Implementation Details (Section 5.5):**
  - Remove Subsection 5.5.3 (`Tally Bridge Streamer`).
- **Section 5.6 & Figure 5.2 (System Component Integration):**
  - Replace the Phase 2 orchestration figure with the Phase 1 Orchestration Pipeline:
    Streamlit UI ($app.py$) $\leftrightarrow$ `DataFetcher` $\to$ `FinancialParser` $\to$ `RatioEngine` $\to$ `OutlierEngine` $\to$ `BenchmarkCore`.

---

### 2.7 `Report/chapters/results.tex` (Chapter 6)
- **Experimental Setup (Section 6.1):**
  - State evaluation was conducted across 13 public market sectors using real NSE equity filings.
- **Results Analysis & Outlier Evaluation (Sections 6.2 & 6.3):**
  - Remove Tally balancing metrics ($590M$ debit/credit balance).
  - Retain Table 6.1 (*Impact of Outlier Masking on Peer Group Statistics*), demonstrating that outlier masking restores sector standard deviation from $39.54\%$ to $1.28\%$.
- **Section 6.4: Case Study — Maruti Suzuki India Limited (`MARUTI.NS`):**
  - Evaluate `MARUTI.NS` in the Automobile Sector benchmark (9 peers: Maruti, M&M, Bajaj Auto, Hero MotoCorp, Eicher Motors, Ashok Leyland, TVS Motor, Balkrishna Industries, Motherson).
  - Solvency: Debt-to-Equity of $0.001$, Interest Coverage of $68.38\times$ (Ranked *Elite*, Above Benchmark).
  - Efficiency: Asset Turnover of $0.346$, Inventory Turnover of $4.56$ (Ranked *Elite*).
  - Profitability: Operating Margin of $9.68\%$ (Ranked *Weak* / Near Benchmark Low against high-margin peers like Eicher Motors at $32.83\%$).
- **Figure 6.2 (Scorecard):**
  - Update TikZ bar chart to display Maruti Suzuki's percentile profile (Solvency/Turnover in the 90th+ percentile vs. Operating Margin in the 25th percentile).
- **Performance Analysis (Table 6.2):**
  - Remove Tally ERP Aggregation and K-Means Clustering rows. Retain Data Harvesting (14.50s), Data Ingestion (1.20s), Outlier Detection & Scoring (0.45s), and Excel Report Generation (1.10s).

---

### 2.8 `Report/chapters/conclusion.tex` (Chapter 7)
- **Final Outcomes & Contributions (Sections 7.1 & 7.2):**
  - Remove Tally ERP translation layer and K-Means archetype segmentation.
  - Summarize 3 core contributions:
    1. *Automated Financial Standardization*: 60-field synonym resolution dictionary.
    2. *Outlier-Resistant Statistical Engine*: Cell-level masking with Tukey Fences and MAD Modified Z-Scores.
    3. *Bounded Multi-Pillar Scoring Architecture*: Transparent 0-100 Sigmoid scoring and Gemini-driven qualitative diagnostics.
- **Future Scope (Section 7.3):**
  - Remove ERP direct database connectors. Focus on automated SEC/MCA regulatory filing parsers, real-time outlier alerting, predictive ratio time-series forecasting, and international equity market expansions.

---

### 2.9 `Report/chapters/appendices.tex` (Appendices)
- **Appendix Structure:**
  - Retain Appendix A (`Core Source Code`) with `Outlier Filtering Logic`.
  - Remove Chapter B (`Tally ERP Ingestion Formats`) and its subsections (`Ledger Master CSV Format`, `Journal Voucher CSV Format`).

---

## 3. Verification & Compilation Criteria
1. Recompile using:
   ```bash
   pdflatex -interaction=nonstopmode main.tex
   bibtex main
   pdflatex -interaction=nonstopmode main.tex
   pdflatex -interaction=nonstopmode main.tex
   ```
2. Verify zero LaTeX fatal errors, zero broken references (`??`), and zero undefined citations.
3. Verify output PDF page count, bookmarks, and visual layout.
