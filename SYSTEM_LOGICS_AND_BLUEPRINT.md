#  NSE Financial Outlier Detection & Benchmarking System
## Technical Blueprint, Architectural Logic, and Mathematical Foundation

### Table of Contents
1. [Introduction & System Purpose](#1-introduction--system-purpose)
2. [Module Architecture & Global System Flowcharts](#2-module-architecture--global-system-flowcharts)
3. [Data Ingestion & Normalization Engine (yfinance)](#3-data-fetching--normalization-engine-yfinance)
4. [Ratio Calculation Engine](#4-ratio-engine--computational-logic)
5. [Statistical Outlier Detection Engine](#5-statistical-outlier-detection-engine)
6. [Benchmarking Scoring Pipeline](#6-benchmarking-scoring-pipeline)
7. [Reporting & Explanation Engine](#7-reporting--explanation-engine)
8. [Operational Boundaries, Error Handling & Limitations](#8-operational-boundaries-error-handling--limitations)

---

## 1. Introduction & System Purpose

The **NSE Financial Outlier Detection & Benchmarking System** is a robust Python-based quantitative finance platform designed to automate cross-sectional financial analysis, statistical anomaly detection, and strategic benchmarking for companies listed on the National Stock Exchange of India (NSE). 

### 1.1 Core Problems Solved
1. **Parsing Friction**: Financial statements retrieved from raw APIs (like Yahoo Finance) are highly inconsistent, with changing line-item descriptions and shifted timeframes. The system automates ingestion and standardizes reports in under 60 seconds.
2. **Distribution Skewness**: Extreme financial metrics (e.g., a P/E ratio of $5000\times$ or interest coverage of $-400\times$) drag arithmetic averages and standard deviations, rendering normal companies indistinguishable under traditional z-score models. The system addresses this with robust median-based scaling and cell-level outlier masking.
3. **Black-Box Metrics**: Most quantitative models return a health score without auditability. The system generates a detailed **Contribution Matrix** and translates mathematical comparisons into structured statistical explanations and multi-sheet Excel reports.

### 1.2 Target User Personas
*   **Equity Analysts**: Run cross-sectional sector scans to flag undervalued performers or identify companies with deteriorating fundamentals.
*   **Risk Officers**: Scan for extreme statistical outliers that could signify accounting anomalies, operational distress, or aggressive revenue recognition.
*   **Corporate & Portfolio Strategists**: Benchmark sector constituents against robust distribution baselines to assess relative financial health.

---

## 2. Module Architecture & Global System Flowcharts

The platform is designed around a modular pipeline pattern. Each step of the process is handled by a dedicated module with well-defined contracts, ensuring the data pipeline is reliable and easy to audit.

### 2.1 Module Architecture Flowchart
```mermaid
graph TD
    %% Main Entrypoint
    App[app.py Streamlit Dashboard]

    %% Data Ingestion
    loader[sector_loader.py]
    fetcher[data_fetcher.py]
    parser[financial_parser.py]

    %% Computation Engines
    ratio_eng[ratio_engine.py]
    outlier_eng[outlier_engine.py]
    bench_core[benchmark_core.py]
    bench_class[benchmark_classifier.py]
    bench_store[benchmark_store.py]

    %% Outputs & Vis
    vis[visualization.py]
    report_gen[report_generator.py]

    %% Connections
    App --> loader
    App --> fetcher
    fetcher --> parser
    parser --> ratio_eng
    ratio_eng --> outlier_eng
    ratio_eng --> bench_core
    outlier_eng --> bench_core
    
    bench_core --> bench_class
    bench_core --> bench_store
    
    App --> vis
    App --> report_gen
```

### 2.2 End-to-End Ingestion and Analysis Flowchart
```mermaid
sequenceDiagram
    autonumber
    actor User as Analyst / User
    participant UI as app.py (Streamlit)
    participant DF as data_fetcher.py
    participant FP as financial_parser.py
    participant RE as ratio_engine.py
    participant OE as outlier_engine.py
    participant BC as benchmark_core.py
    participant BS as benchmark_store.py

    User->>UI: Select Sector & Configure Thresholds
    UI->>DF: Fetch Financial Statements & Market Info
    Note over DF: Check Local Parquet Cache (24h TTL)
    DF-->>UI: Raw Statement DataFrames
    UI->>FP: Ingest Raw Statements
    Note over FP: Map Aliases & Transpose Matrix
    FP-->>UI: Standardized Income, Balance & Cashflow DataFrames
    UI->>RE: Compute Financial Ratios & YoY Growth
    RE-->>UI: Combined Ratio Matrix (Tickers × Ratios)
    UI->>OE: Execute Outlier Detection Scan
    Note over OE: Run IQR, Robust Z-Score, and Isolation Forest
    OE-->>UI: Outliers Log DataFrame
    UI->>BC: Execute Benchmarking Pipeline
    Note over BC: 1. Mask Outliers<br/>2. Compute Robust Scaling<br/>3. Sigmoid Scoring (0-100)<br/>4. Pillar Aggregation
    BC->>BS: Save Sector Benchmark Profile
    BC-->>UI: Mapped Scores, Rankings & Categories
    UI->>User: Display Dashboards, Heatmaps & Benchmark Reports
```

### 2.3 Core Source Code Index
The codebase consists of the following components:

*   [app.py](file:///D:/Python/PYCHARM/PANDAS/app.py) — The Streamlit graphical entry point. Orchestrates session states, sidebar configuration, UI custom styling (Abyss Teal), and renders the 6 analytical tabs.
*   [modules/sector_loader.py](file:///D:/Python/PYCHARM/PANDAS/modules/sector_loader.py) — Contains structural mappings of NSE sectors (e.g., Automobile, IT, FMCG, Banking) to primary ticker symbols.
*   [modules/data_fetcher.py](file:///D:/Python/PYCHARM/PANDAS/modules/data_fetcher.py) — Collects data from Yahoo Finance (`yfinance`), manages the local caching database, and implements API rate-limiting delays.
*   [modules/financial_parser.py](file:///D:/Python/PYCHARM/PANDAS/modules/financial_parser.py) — Resolves field discrepancies across financial statement versions by mapping raw columns to canonical variables.
*   [modules/ratio_engine.py](file:///D:/Python/PYCHARM/PANDAS/modules/ratio_engine.py) — Computes 30+ quarterly and annual financial metrics with safeguards against division by zero.
*   [modules/outlier_engine.py](file:///D:/Python/PYCHARM/PANDAS/modules/outlier_engine.py) — Houses univariate statistical fences (IQR, Z-Score) and multivariate anomaly detection (Isolation Forest) algorithms.
*   [modules/benchmark_core.py](file:///D:/Python/PYCHARM/PANDAS/modules/benchmark_core.py) — Runs the  benchmarking engine, utilizing robust statistics to rank and score peer groups.
*   [modules/benchmark_classifier.py](file:///D:/Python/PYCHARM/PANDAS/modules/benchmark_classifier.py) — Determines percentile positions, health categorization labels, and signal classes for individual ratios.
*   [modules/benchmark_store.py](file:///D:/Python/PYCHARM/PANDAS/modules/benchmark_store.py) — Handles file persistence (Parquet/JSON) for finalized sector benchmarks.
*   [modules/ai_handler.py](file:///D:/Python/PYCHARM/PANDAS/modules/ai_handler.py) — Connects to the Google Gemini API, manages key rotation, and discovers target tickers for AI Search.
*   [modules/visualization.py](file:///D:/Python/PYCHARM/PANDAS/modules/visualization.py) — Renders interactive charts (radar, sunburst, stacked contribution bars, scatter plots, heatmaps) in Plotly and Seaborn.
*   [modules/report_generator.py](file:///D:/Python/PYCHARM/PANDAS/modules/report_generator.py) — Compiles outputs into multi-sheet Excel workbooks with proper styling and exports statistical explanations.
*   [modules/utils.py](file:///D:/Python/PYCHARM/PANDAS/modules/utils.py) — Implements helpers like `safe_divide()`, exponential backoff decorators, logging config, and numeric converters.

---

## 3. Data Fetching & Normalization Engine (yfinance)

Raw financial filings retrieved via Yahoo Finance contain inconsistent naming conventions across companies, sectors, and historical quarters. The system standardizes this data using the **Parser & Normalization Ingestion pipeline**.

### 3.1 Fetching, Caching, and Retries
*   **Throttling Control**: To prevent Yahoo Finance API rate limits, a configurable time delay (default `0.5s`) is enforced between ticker queries.
*   **Retry Logic**: System API calls are wrapped in a custom `@retry` decorator (located in [utils.py](file:///D:/Python/PYCHARM/PANDAS/modules/utils.py#L54-L72)) implementing up to 3 execution attempts with exponential backoff delays ($Delay = Base \times Attempt$).
*   **Two-Tier Caching Database**:
    1.  **RAM Cache**: Streamlit's `@st.cache_data` caches raw operations locally during a session.
    2.  **File Cache**: Raw data is stored in localized Parquet files under `data/cache/` using MD5 hash naming conventions. The default Cache Time-To-Live (TTL) is set to 24 hours.

### 3.2 Parsing Ingestion Pipeline
1.  **DataFrame Transposition**: Converts the raw `yfinance` field-as-row, date-as-column configuration into a standard row-per-date structure.
2.  **Canonical Alias Resolution**: The engine sweeps raw column names against pre-defined alias sets. If a match is found, the column is renamed to its standardized key.
3.  **Deduplication**: Handles duplicate records that can arise from overlapping quarterly and annual statement ingestion.
4.  **Data Type Alignment**: Enforces a strict `float64` schema across all numeric fields and sorts indices chronologically.

### 3.3 Alias Mapping Configuration
The [financial_parser.py](file:///D:/Python/PYCHARM/PANDAS/modules/financial_parser.py) file maps over 60 naming variants to canonical fields. A summary of key mappings is provided below:

| Canonical Key | Financial Statement | Primary Naming Aliases Mapped |
|:---|:---|:---|
| `total_revenue` | Income Statement | "Total Revenue", "Revenue", "Net Revenue", "Net Sales", "Revenues" |
| `gross_profit` | Income Statement | "Gross Profit", "GrossProfit", "Gross Income" |
| `operating_income` | Income Statement | "Operating Income", "Operating Profit", "EBIT", "OperatingIncome" |
| `net_income` | Income Statement | "Net Income", "Net Profit", "NetIncome", "Net Profit After Tax" |
| `interest_expense` | Income Statement | "Interest Expense", "Interest Expense Paid", "Finance Costs" |
| `ebitda` | Income Statement | "EBITDA", "Normalized EBITDA", "Ebitda" |
| `depreciation_amortization` | Income Statement | "Depreciation & Amortization", "Depreciation And Amortization" |
| `total_assets` | Balance Sheet | "Total Assets", "TotalAssets", "Total Assets Mapped" |
| `total_liabilities` | Balance Sheet | "Total Liabilities", "Total Liabilities Mapped", "Total Liabilities Net Minor Interest" |
| `total_equity` | Balance Sheet | "Total Equity", "Stockholders Equity", "Shareholders Equity", "Net Worth" |
| `current_assets` | Balance Sheet | "Total Current Assets", "Current Assets", "CurrentAssets" |
| `current_liabilities` | Balance Sheet | "Total Current Liabilities", "Current Liabilities", "CurrentLiabilities" |
| `cash_and_equivalents` | Balance Sheet | "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash" |
| `inventory` | Balance Sheet | "Inventory", "Inventories", "Stock In Hand" |
| `accounts_receivable` | Balance Sheet | "Receivables", "Accounts Receivable", "Net Receivables", "Sundry Debtors" |
| `total_debt` | Balance Sheet | "Total Debt", "Long Term Debt + Short Term Debt", "Borrowings" |
| `operating_cashflow` | Cash Flow Statement | "Operating Cash Flow", "Cash Flow From Operating Activities", "Net Cash From Operating Activities" |
| `capital_expenditure` | Cash Flow Statement | "Capital Expenditure", "CapEx", "Purchase Of Property Plant And Equipment" |
| `free_cashflow` | Cash Flow Statement | "Free Cash Flow", "Free Cashflow" |

---

## 4. Ratio Engine & Computational Logic

The [ratio_engine.py](file:///D:/Python/PYCHARM/PANDAS/modules/ratio_engine.py) module extracts values from standardized statements and computes financial ratios.

### 4.1 Liquidity Ratios
Measure a company's ability to cover its short-term obligations using assets that can be quickly converted into cash.

*   **Current Ratio**:
    $$\text{Current Ratio} = \frac{\text{Current Assets}}{\text{Current Liabilities}}$$
*   **Quick Ratio**:
    $$\text{Quick Ratio} = \frac{\text{Current Assets} - \text{Inventory}}{\text{Current Liabilities}}$$
*   **Cash Ratio**:
    $$\text{Cash Ratio} = \frac{\text{Cash \& Equivalents}}{\text{Current Liabilities}}$$

### 4.2 Solvency & Leverage Ratios
Measure a company's long-term capital structure, debt levels, and capacity to service interest payments.

*   **Debt-to-Equity**:
    $$\text{Debt-to-Equity} = \frac{\text{Total Debt}}{\text{Total Equity}}$$
*   **Debt Ratio**:
    $$\text{Debt Ratio} = \frac{\text{Total Liabilities}}{\text{Total Assets}}$$
*   **Interest Coverage**:
    $$\text{Interest Coverage} = \frac{\text{Operating Income}}{|\text{Interest Expense}|}$$
    *(Note: If interest expense is zero, the system returns `NaN` to denote a debt-free capital structure, preventing division-by-zero errors).*

### 4.3 Profitability Ratios
Measure a company's efficiency in generating profits relative to sales, asset base, or equity capital.

*   **Gross Margin (%)**:
    $$\text{Gross Margin} = \left( \frac{\text{Gross Profit}}{\text{Total Revenue}} \right) \times 100$$
*   **Operating Margin (%)**:
    $$\text{Operating Margin} = \left( \frac{\text{Operating Income}}{\text{Total Revenue}} \right) \times 100$$
*   **Net Margin (%)**:
    $$\text{Net Margin} = \left( \frac{\text{Net Income}}{\text{Total Revenue}} \right) \times 100$$
*   **Return on Equity (ROE) (%)**:
    $$\text{ROE} = \left( \frac{\text{Net Income}}{\text{Total Equity}} \right) \times 100$$
*   **Return on Assets (ROA) (%)**:
    $$\text{ROA} = \left( \frac{\text{Net Income}}{\text{Total Assets}} \right) \times 100$$
*   **Return on Capital Employed (ROCE) (%)**:
    $$\text{ROCE} = \left( \frac{\text{Operating Income}}{\text{Total Assets} - \text{Current Liabilities}} \right) \times 100$$

### 4.4 Efficiency Ratios
Measure how effectively a company utilizes its assets to generate sales.

*   **Asset Turnover**:
    $$\text{Asset Turnover} = \frac{\text{Total Revenue}}{\text{Total Assets}}$$
*   **Inventory Turnover**:
    $$\text{Inventory Turnover} = \frac{\text{Total Revenue}}{\text{Inventory}}$$
*   **Receivables Turnover**:
    $$\text{Receivables Turnover} = \frac{\text{Total Revenue}}{\text{Accounts Receivable}}$$

### 4.5 Cash Flow Ratios
Measure the relationship between accounting profits and actual cash generated.

*   **Operating Cash Flow Ratio**:
    $$\text{Operating CF Ratio} = \frac{\text{Operating Cash Flow}}{\text{Current Liabilities}}$$
*   **Free Cash Flow Margin (%)**:
    $$\text{FCF Margin} = \left( \frac{\text{Free Cash Flow}}{\text{Total Revenue}} \right) \times 100$$
*   **Cash Conversion Ratio**:
    $$\text{Cash Conversion} = \frac{\text{Operating Cash Flow}}{\text{Net Income}}$$

### 4.6 Annual Growth Ratios
Growth rates are calculated using year-over-year (YoY) changes from annual reports:

$$\text{Growth Rate (\%)} = \left( \frac{\text{Metric}_{t} - \text{Metric}_{t-1}}{|\text{Metric}_{t-1}|} \right) \times 100$$
Calculated for:
*   `revenue_growth`
*   `net_income_growth`
*   `ebitda_growth`
*   `ocf_growth`

### 4.7 Division-by-Zero Protection
To prevent division errors from breaking the pipeline, the system uses a helper function in [utils.py](file:///D:/Python/PYCHARM/PANDAS/modules/utils.py#L120-L128):

```python
def safe_divide(numerator: float, denominator: float, default: float = np.nan) -> float:
    try:
        if pd.isna(denominator) or denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default
```
Any invalid division returns `NaN`. Downstream metrics are adjusted to handle `NaN` inputs, preventing values like `inf` or `-inf` from affecting the statistical models.

---

## 5. Statistical Outlier Detection Engine

The [outlier_engine.py](file:///D:/Python/PYCHARM/PANDAS/modules/outlier_engine.py) module identifies extreme values within a peer group to prevent them from skewing the sector averages.

```mermaid
graph TD
    A[Raw Ratio Matrix] --> B[Drop Raw Monetary Columns]
    B --> C[For each ratio column...]
    C --> D[Run IQR Tukey Fences]
    C --> E[Run Robust Z-Scores]
    C --> F[Run Multivariate Isolation Forest]
    D & E & F --> G[Compute Anomaly Flag]
    G --> H{Is cell flagged as Outlier?}
    H -- Yes --> I[Compute Severity Score & Set Flag]
    H -- No --> J[Keep Raw Value]
    I --> K[Isolate Cell & Mask as NaN in clean_matrix]
```

### 5.1 Tukey's Interquartile Range (IQR) Method
Because financial ratios are rarely normally distributed, the system uses Tukey's Fences as its primary non-parametric detection method.

1.  **Quartile Mappings**:
    *   $Q_1 = \text{25th Percentile of the peer distribution}$
    *   $Q_3 = \text{75th Percentile of the peer distribution}$
    *   $\text{IQR} = Q_3 - Q_1$
2.  **Fence Computations**:
    $$\text{Lower Fence} = Q_1 - (Multiplier \times \text{IQR})$$
    $$\text{Upper Fence} = Q_3 + (Multiplier \times \text{IQR})$$
    *(The default multiplier is set to $1.5\times$ for standard outliers).*
3.  **Flagging Criteria**: Any ratio value $x$ where $x < \text{Lower Fence}$ or $x > \text{Upper Fence}$ is flagged.

### 5.2 Robust Z-Score Method
Standard Z-Score models use the mean and standard deviation, which are sensitive to outliers. To address this, the system implements a **Robust Z-Score** based on the **Median Absolute Deviation (MAD)**.

1.  **Median Absolute Deviation (MAD)**:
    $$\text{MAD} = \text{median}\left( \left| x_i - \text{median}(X) \right| \right)$$
2.  **Robust Z-Score Formulation**:
    $$Z_i = \frac{0.6745 \times (x_i - \text{median}(X))}{\text{MAD}}$$
    *(The scaling factor $0.6745$ aligns the expected value of MAD to the standard deviation of a normal distribution).*
3.  **Flagging Criteria**: A cell is flagged as an outlier if $|Z_i| > \text{Threshold}$ (default threshold is set to $3.5$).

### 5.3 Isolation Forest (Multivariate Anomaly Detection)
To identify structural anomalies that may not show up in single-variable tests, the system uses scikit-learn's **Isolation Forest** model.
*   **Algorithm**: Sub-samples features and builds isolation trees. The number of splits needed to isolate a sample is a measure of its anomaly status.
*   **Contamination Parameter**: Set to $10\%$, specifying the expected proportion of outliers in the dataset.
*   **Feature Preprocessing**: Missing data is imputed with column medians, followed by scaling with a `RobustScaler` before training.

### 5.4 Outlier Severity & Directional Rules
*   **Composite Severity Score**: To rank anomalies, the system computes a weighted severity index:
    $$\text{Severity Score} = \left( 0.6 \times \text{IQR Deviation Ratio} \right) + \left( 0.4 \times |Z_i| \right)$$
    The score is mapped to categories: **Low** ($<1.0$), **Medium** ($1.0 \le s < 2.0$), **High** ($2.0 \le s < 3.0$), or **Critical** ($\ge 3.0$).
*   **Directional Labels**: Outliers are classified based on financial impact:
    *   **Positive Outlier ()**: High margin/return ratios above the upper fence (e.g., strong profitability).
    *   **Negative Outlier ()**: High debt ratios or low liquidity/margin ratios (e.g., solvency risks).

### 5.5 Cell-Level Masking Philosophy
A key design choice is that companies are not excluded from analysis due to a single anomalous ratio. Instead of dropping the entire row, the system masks the specific outlier cell by setting it to `NaN` in the benchmark matrix. This allows the company to still be benchmarked on its remaining valid metrics.

---

## 6. Benchmarking Scoring Pipeline

The [benchmark_core.py](file:///D:/Python/PYCHARM\PANDAS/modules/benchmark_core.py) module standardizes ratios to a common scale, enabling comparison across different metrics.

```mermaid
graph TD
    A[Raw Ticker-Ratio Matrix] --> B[Apply Outlier Cell Masking]
    B --> C[Calculate Peer Statistics: Median, Q1, Q3, Deciles]
    C --> D[Apply Robust Scaling per Ratio]
    D --> E[Invert Scales for 'Lower is Better' Ratios]
    E --> F[Apply Logistic Sigmoid Mapping 0 to 100]
    F --> G[Aggregate Ratio Scores into 5 Pillars]
    G --> H[Apply Weighted Composite Formula]
    H --> I[Assign Risk Categories & Sector Rankings]
```

### 6.1 Robust Scaling
Because standard scaling is sensitive to outliers, the system uses **Robust Scaling** based on the median and IQR of the peer group:

$$\text{Robust Scaled } z_{i} = \frac{x_i - \text{median}(X)}{\text{IQR}(X)}$$

*   **Interpretation**:
    *   $z = 0$: Represents the sector median.
    *   $z = +1$: One IQR unit above the sector median.
    *   $z = -1$: One IQR unit below the sector median.

### 6.2 Directional Inversion
To align scores so that higher values always represent better performance, ratios where lower values are preferred (e.g., debt levels) are inverted:

$$\tilde{z}_{i} = z_i \quad \text{for Higher is Better ratios}$$
$$\tilde{z}_{i} = -z_i \quad \text{for Lower is Better ratios (such as debt to equity)}$$

### 6.3 Logistic Sigmoid Transformation
To map the unbounded scaled values to a standard 0–100 scale, the system applies a logistic sigmoid function:

$$\text{Score}_i = \frac{100}{1 + e^{-\tilde{z}_{i}}}$$

*   **Key Score Reference Points**:
    *   **Score = 50**: Matches the sector median.
    *   **Score > 50**: Better than the sector median.
    *   **Score < 50**: Worse than the sector median.
    *   **Score $\to$ 100**: Approaching the upper end of the peer distribution.

### 6.4 Aggregation Hierarchy & Weights
Scores are aggregated into five analytical pillars using the following weights:

```
[Composite Benchmark Score] (100%)
 ├── Profitability (30%)
 │    ├── Gross Margin (20%)
 │    ├── Operating Margin (25%)
 │    ├── Net Margin (25%)
 │    ├── Return on Equity (15%)
 │    └── Return on Assets (15%)
 ├── Solvency (20%)
 │    ├── Debt-to-Equity (40%) *Inverted*
 │    ├── Debt Ratio (35%) *Inverted*
 │    └── Interest Coverage (25%)
 ├── Growth (20%)
 │    ├── Revenue Growth (35%)
 │    ├── Net Income Growth (35%)
 │    └── OCF Growth (30%)
 ├── Liquidity (15%)
 │    ├── Current Ratio (40%)
 │    ├── Quick Ratio (35%)
 │    └── Cash Ratio (25%)
 └── Efficiency (15%)
      ├── Asset Turnover (40%)
      ├── Inventory Turnover (30%)
      └── Receivables Turnover (30%)
```

If a company is missing a ratio, the system redistributes the weights among the remaining metrics in that pillar, preventing `NaN` values from propagating.

### 6.5 Risk Categories
Composite scores map to five risk categories:

| Score Range | Category | Business Description |
|:---|:---|:---|
| $[80, 100]$ | **Excellent** | Strong fundamentals across all five pillars. |
| $[65, 80)$ | **Strong** | Consistent performer with minor areas for improvement. |
| $[50, 65)$ | **Moderate** | Operates in line with the sector average. |
| $[35, 50)$ | **Weak** | Shows underperformance in key areas (e.g., low profitability or elevated debt). |
| $[0, 35)$ | **Distressed** | High risk, with weaknesses in multiple pillars (e.g., liquidity issues). |

### 6.6 The Contribution Matrix
To keep calculations transparent, the system generates a `contribution_df` for each company:

$$\text{Contribution}_j = \text{Score}_j \times \text{Weight}_j$$
$$\text{Composite Score} = \sum_{j} \text{Contribution}_j$$

This table shows the exact points contributed by each ratio to the final composite score, helping users trace the results back to the source metrics.

---

## 7. Reporting & Explanation Engine

The [ReportGenerator](file:///D:/Python/PYCHARM/PANDAS/modules/report_generator.py) translates quantitative benchmark results into structured statistical explanations and multi-sheet Excel reports.

### 7.1 Statistical Explanations
For each ratio in the scorecard, the system generates plain-English evaluation narratives classifying the position into opportunities, risks, or neutral observations based on deviation from the sector median:
*   **Opportunity**: Metric performs above the peer benchmark quartile (e.g., higher margin or superior asset turnover).
*   **Risk**: Metric performs below the peer benchmark quartile (e.g., elevated leverage or compressed cash conversion).
*   **Neutral / At Benchmark**: Metric operates within the interquartile band of industry peers.

### 7.2 Multi-Sheet Excel Export
The report generator compiles an institutional workbook containing:
1.  **Ratio Scorecard**: Complete peer × ratio evaluation matrix with raw values, percentiles, and position labels.
2.  **Peer Benchmark**: Sector distribution summary including P10, Q1, Median, Mean, Q3, and P90 values.
3.  **Outliers**: Complete registry of univariate and multivariate outliers detected.
4.  **Composite Scores**: Overall 0–100 financial health scores, sector rankings, and pillar breakdown.
5.  **Business Report**: Granular statistical explanations and risk/opportunity classifications.
6.  **Summary**: Metadata regarding the analysis run, timestamp, and peer cohort size.

---

## 8. Operational Boundaries, Error Handling & Limitations

### 8.1 Error Handling & Pipeline Resiliency
*   **Missing Financial Fields**: If a company has incomplete filings, the `safe_divide()` wrapper prevents crashes, and the benchmarking engine adjusts weights accordingly.
*   **Delisted Tickers**: Invalid tickers are skipped during data fetching, and the sector baseline is built using the remaining peers.

### 8.2 Caching Policies
*   **Volatile In-Memory Storage**: Session-level calculations are stored in `st.session_state` to avoid redundant computations.
*   **Persistent Cache Storage**: Financial statements are saved as Parquet files under `data/cache/`. To clear outdated data and free storage, users can trigger a purge via the **Clear All Cache** button in the sidebar.

### 8.3 System & Analytical Limitations
1.  **Dependency on API Quality**: The accuracy of the ratios depends on how consistently Yahoo Finance standardizes raw financial reports.
2.  **Sector Homogeneity Assumption**: The benchmarking logic assumes that companies within a sector are comparable. If a sector contains both asset-heavy manufacturers and asset-light software developers, efficiency comparisons can be skewed.
3.  **Relative Benchmark Scores**: A high composite score indicates strong performance relative to peers. If the entire sector is in decline, a high score does not guarantee absolute financial health.

---
*FinMetrics Suite  Blueprint — End of Document*
