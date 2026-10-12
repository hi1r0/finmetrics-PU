# FinMetrics: Comprehensive Operational Manual & Architectural Reference

---

## 1. Executive Summary and Value Proposition

Traditional financial analysis suffers from significant friction points: extensive time spent manually collecting accounts, subjective normalization processes, and a lack of standardized benchmarking across sector peers. 

The FinMetrics Suite resolves these inefficiencies by automating the entire pipeline, from raw financial statement collection to deep analytical scoring and outlier detection, executing complex sector workflows in seconds.

### The System Core Pillars:
*   **Automated Ingestion**: Directly fetches quarterly and annual statements for major NSE-listed companies across 13 sectors using Yahoo Finance. Data is normalized instantly via a 60-field alias-mapping engine.
*   **Statistical Outlier Scans**: Implements Tukey Fences (IQR), robust standard deviations (Modified Z-Score / MAD), and multi-variate unsupervised anomalies (Isolation Forest) to isolate erratic accounting cells and ensure data integrity.
*   **Strategic Benchmarking**: Calculates over 30 ratios spanning Liquidity, Profitability, Solvency, Operating Efficiency, Growth, Valuation, and Cash Flow Health. Ratios are scored using robust outlier-resistant scaling techniques.
*   **Composite Solvency & Health Scoring**: Aggregates multi-pillar financial performance into an objective 0–100 composite score, ranking companies within their sector and classifying risk categories.
*   **Institutional Excel Reporting**: Compiles multi-sheet Excel reports with automated statistical explanations, benchmark quartiles, outlier registries, and pillar summaries.

---

## 2. Global Configuration and Sidebar Control

The sidebar acts as the global control center of the FinMetrics Suite. It manages security credentials, performance optimization, and clean memory states. All interface actions adapt instantly to user selections, with the sidebar maintaining persistent configurations across re-runs.

### Sidebar Components and Controls:
1.  **AI Search Integration and API Key Status**: Scans environment variables for a valid API key. A positive status enables natural-language AI searches for public peer tickers.
2.  **Use Data Cache (Toggle)**: A switch to enable or disable local caching to prevent API rate limiting and reduce loading times.
3.  **Clear All Cache (Action Button)**: A critical action button that purges the system, clearing RAM caches and persistent Parquet files.

---

## 3. Core Analytical Workflow

The application operates as an end-to-end sector benchmarking pipeline:

### Step 1: Define Scope
Users navigate to the **Home** tab and choose the analysis unit:
*   **Sector**: Choose an NSE sector (e.g., Automobile, Banking, FMCG, IT, Pharmaceuticals, etc.).
*   **Industry**: Choose a sub-industry within a sector.
*   **AI Search**: Describe an industry in natural language to discover relevant NSE tickers dynamically.

### Step 2: Ticker Override (Optional)
Users can expand the **Ticker Override** section to add, remove, or substitute specific NSE tickers (`.NS` suffix).

### Step 3: Statistical Calibration (Advanced)
Users can fine-tune outlier detection thresholds:
*   **IQR Multiplier**: Multiplier for Tukey fences (default: 1.5).
*   **Z-Score Threshold**: Threshold for Modified Z-score (default: 3.5).
*   **Isolation Forest Contamination (%)**: Expected proportion of structural anomalies (default: 10%).

### Step 4: Build Benchmark
Click **Build Sector Benchmark** to execute statement ingestion, ratio calculation, outlier detection, quartile computation, and composite scoring.

---

## 4. Dashboard Tab-by-Tab Detailed Reference

*   **Home Tab**: The primary command hub featuring scope selectors, calibration sliders, and the benchmark execution button.
*   **Ratio Scorecard Tab**: Displays benchmark scorecards for companies within the peer group, categorizing ratios against the sector baseline (Above, At, Below Benchmark) using horizontal bar charts and data tables.
*   **Outliers Tab**: Highlights extreme financial values across the peer group using scatter plots and univariate/multivariate anomaly data tables.
*   **Peer Benchmark Tab**: Presents sector-wide descriptive statistics (deciles, quartiles, medians, means) via a dense heat map and comprehensive data tables.
*   **Composite Score Tab**: Aggregates and displays weighted financial health scores (0–100) for all companies within the peer group using ranked bar charts and pillar metric breakdowns.
*   **Export Tab**: Compiles the complete analysis into a downloadable multi-sheet Excel workbook with full statistical explanations.

---

## 5. Visual Interface and Visualizations Walkthrough

### Core Analysis Dashboards
1.  **Ratio Scorecard**:
    *   Horizontal metric cards display aggregate counts: Above Benchmark, At Benchmark, Below Benchmark.
    *   Company selector allows switching between individual peer companies.
    *   Visual percentile bars (0 to 100) indicate relative standing per ratio, color-coded green (strong), yellow (neutral), red (weak).
    *   Full scorecard table displays raw value, peer median, quartiles (Q1, Q3), percentiles (P10, P90), percentile rank, position label, and health label.
2.  **Outliers**:
    *   Scatter plot mapping deviation from sector median against severity score.
    *   Univariate outlier table showing triggered ratios, raw values, sector medians, Z-scores, and severity flags.
    *   Multivariate Isolation Forest anomaly scoring identifying structurally atypical firms across the full ratio space.
3.  **Peer Benchmark**:
    *   Dense quartile heatmap showing statistical distributions (P10, Q1, Median, Mean, Q3, P90) across all computed metrics.
    *   Descriptive statistics table detailing medians, standard deviations, peer counts, and excluded outliers.
4.  **Composite Score**:
    *   Ranked horizontal bar chart showing composite scores from highest to lowest.
    *   Pillar breakdown table displaying scores across Profitability, Solvency, Liquidity, Cash Flow, and Efficiency.
5.  **Export**:
    *   One-click generation of institutional Excel workbooks containing Ratio Scorecard, Peer Benchmark, Outliers, Composite Scores, Business Explanations, and Summary sheets.
