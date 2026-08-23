# NSE Financial Outlier Detection & Benchmarking System
## Technical Documentation — Part 1: Overview, Architecture & Data Flow

---

## Section 1 — Project Overview

### 1.1 What the System Does

This system is an AI-powered financial analytics platform for companies listed on the National Stock Exchange of India (NSE). It automates the collection, computation, analysis, and visualization of financial health metrics across entire market sectors.

The system performs five core functions:

1. **Data Collection** — Automatically fetches quarterly income statements, balance sheets, cash flow statements, and market data for all companies in a selected sector using the yfinance API.

2. **Ratio Computation** — Calculates 30+ financial ratios spanning liquidity, solvency, profitability, efficiency, cash flow, valuation, and growth categories.

3. **Outlier Detection** — Identifies statistically abnormal ratio values using IQR fences, Z-scores, and Isolation Forest, classifying each outlier by severity, direction, and financial interpretation.

4. **Benchmark Scoring** — Constructs a robust, outlier-resistant benchmark score for every company by scaling clean ratios, aggregating them into five financial pillars, and producing a composite 0–100 score with rankings and categories.

5. **Interactive Dashboard** — Presents all results through a Streamlit web application with interactive Plotly charts, filterable tables, downloadable reports, and human-readable explanations.

### 1.2 Business Problem Solved

Traditional financial analysis requires analysts to manually download financial statements, compute ratios in spreadsheets, and subjectively compare companies. This process is:

- **Time-consuming** — hours per company, multiplied across an entire sector.
- **Error-prone** — manual formula entry leads to inconsistencies.
- **Subjective** — comparing companies without normalization hides the true relative picture.
- **Not scalable** — adding companies requires repeating the entire workflow.

This system solves all four problems by automating the entire pipeline from raw data to ranked, explained, and visualized results in under 60 seconds for a full sector.

### 1.3 Intended Users

| User Type | How They Use It |
|-----------|----------------|
| **Equity Analysts** | Screen sectors for investment-worthy companies, identify red flags |
| **Portfolio Managers** | Compare holdings against sector peers on standardized metrics |
| **Risk Officers** | Detect outlier financial behavior that may indicate fraud or distress |
| **Academic Researchers** | Study cross-sectional financial patterns with clean, normalized data |
| **Students** | Learn financial ratio analysis through an interactive, visual tool |

### 1.4 Key Insights Provided

- Which companies in a sector are financially strongest/weakest
- Which specific ratios caused a company to score high or low
- Whether extreme values are positive signals (e.g., exceptional profitability) or negative signals (e.g., dangerous leverage)
- How each company compares to the sector median on every financial dimension
- Trend analysis showing ratio movement over recent quarters

---

## Section 2 — System Architecture

### 2.1 Module Overview

The system follows a strict modular pipeline architecture. Each module has a single responsibility, well-defined inputs/outputs, and can be tested independently.

```
┌─────────────────────────────────────────────────────────┐
│                     app.py (Streamlit UI)                │
│  Orchestrates the pipeline, manages state, renders tabs  │
└──────┬──────────────────────────────────────────────────┘
       │ calls
       ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ sector_loader│→│ data_fetcher │→│ financial_parser  │
│  (companies) │  │  (yfinance)  │  │ (standardize)    │
└──────────────┘  └──────────────┘  └────────┬─────────┘
                                             │
                                             ▼
                                    ┌────────────────┐
                                    │  ratio_engine   │
                                    │ (30+ ratios)    │
                                    └────────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                     ┌──────────────┐ ┌─────────────┐ ┌───────────────┐
                     │outlier_engine│ │scoring_engine│ │benchmark_engine│
                     │ (IQR/Z/IF)  │ │(health score)│ │(robust bench) │
                     └──────────────┘ └─────────────┘ └───────┬───────┘
                                                              │
                                                              ▼
                                                    ┌─────────────────┐
                                                    │benchmark_explainer│
                                                    │(narrative text)  │
                                                    └─────────────────┘
                              │
                              ▼
                     ┌──────────────────┐  ┌──────────────────┐
                     │  visualization   │  │ report_generator  │
                     │ (Plotly charts)  │  │ (Excel/PDF)       │
                     └──────────────────┘  └──────────────────┘
```

### 2.2 Module Details

#### `sector_loader.py`
- **Purpose**: Provides a curated mapping of NSE sectors to ticker symbols.
- **Input**: None (uses hardcoded sector map).
- **Output**: List of ticker strings (e.g., `["MARUTI.NS", "M&M.NS", ...]`).
- **Design Choice**: A curated map was chosen over scraping because NSE sector classifications are inconsistent across sources, and a curated list ensures reliable, tested ticker coverage.
- **Coverage**: 13 sectors, ~100+ companies, with optional industry sub-grouping.

#### `data_fetcher.py`
- **Purpose**: Fetches financial statements from the yfinance API with caching and retry logic.
- **Input**: List of ticker strings.
- **Output**: Dict mapping each ticker to its 6 DataFrames (quarterly income, quarterly balance sheet, quarterly cash flow, annual income, annual balance sheet, annual cash flow) plus market info.
- **Design Choices**:
  - **Caching**: Responses are cached locally (24-hour TTL) to avoid redundant API calls during development and re-runs.
  - **Retry logic**: Each API call is retried up to 3 times with exponential backoff to handle transient network failures.
  - **Rate limiting**: A configurable delay (default 0.5s) between calls avoids triggering yfinance rate limits.
  - **Progress callback**: Supports Streamlit progress bar updates during fetching.

#### `financial_parser.py`
- **Purpose**: Normalizes raw yfinance DataFrames into a canonical structure with consistent column names.
- **Input**: Raw yfinance statement DataFrames.
- **Output**: Dict with standardized DataFrames (`income_q`, `balance_q`, `cashflow_q`, `income`, `balance`, `cashflow`).
- **Why it exists**: yfinance returns inconsistent column names across companies and time periods (e.g., "Total Revenue" vs "Revenue" vs "Net Revenue"). The parser maps all variants to a single canonical key using alias dictionaries.
- **Alias coverage**: 60+ field mappings across income, balance sheet, and cash flow statements.

#### `ratio_engine.py`
- **Purpose**: Computes all financial ratios from parsed statements.
- **Input**: Parsed statement dict + market info dict.
- **Output**: DataFrame where rows = tickers, columns = ratio names.
- **Design Choice**: Uses `safe_divide()` to prevent division-by-zero crashes. Returns `NaN` for any ratio where the denominator is zero or missing.

#### `outlier_engine.py`
- **Purpose**: Detects statistically abnormal ratio values using IQR, Z-score, and Isolation Forest.
- **Input**: Ratio matrix DataFrame.
- **Output**: DataFrame of outlier records with severity scores, direction flags, and labels.
- **Key Constants**: `HIGH_IS_BAD` set (ratios where high values are negative signals), `LOW_IS_BAD` set (ratios where low values are negative signals), `RATIO_LABELS` dict (human-readable names).

#### `scoring_engine.py`
- **Purpose**: Computes a Financial Health Score (0–100) using weighted pillar aggregation.
- **Input**: Ratio matrix.
- **Output**: DataFrame with health score, pillar scores, and risk category per company.
- **Constants exported**: `PILLARS` (ratio→pillar mapping with weights), `PILLAR_WEIGHTS` (pillar→composite weights).

#### `benchmark_engine.py`
- **Purpose**: Advanced metric-level benchmarking that excludes outlier cells, applies robust scaling, and produces ranked composite scores.
- **Input**: Ratio matrix + outlier DataFrame.
- **Output**: `BenchmarkResult` NamedTuple with 7 DataFrames (summary, ratio scores, clean matrix, explanations, analytics, contribution table, hierarchical summary).
- **Design Choice**: Benchmarks ratios, not companies — only abnormal cells are masked, not entire rows.

#### `benchmark_explainer.py`
- **Purpose**: Generates pillar-level financial narratives using template-based sentence construction.
- **Input**: Contribution table + summary DataFrame.
- **Output**: DataFrame with per-company overall, pillar-level, and outlier explanations.

#### `visualization.py`
- **Purpose**: All chart-building functions using Plotly (interactive) and Matplotlib/Seaborn (static exports).
- **Input**: Various DataFrames from the pipeline.
- **Output**: Plotly Figure objects rendered in Streamlit.
- **Theme**: Consistent dark theme with constants (`DARK_BG`, `CARD_BG`, `ACCENT`, `GREEN`, `RED`, `YELLOW`, `TEXT`, `GRID`).

#### `utils.py`
- **Purpose**: Shared utility functions — `safe_divide()`, `pct_change()`, caching, logging setup, retry decorator, path management.

#### `app.py`
- **Purpose**: Streamlit application — orchestrates the pipeline, manages session state, and renders 9 dashboard tabs (Home, Overview, Company, Ratios, Outliers, Health, Benchmark, Insights, Export).

---

## Section 3 — End-to-End Data Flow

### Step 1: Sector Selection
The user selects a sector (e.g., "Automobile") from a dropdown populated by `SectorLoader.get_sectors()`. Alternatively, they can select an industry sub-group or manually override the ticker list.

### Step 2: Company List Creation
`SectorLoader.get_companies_by_sector("Automobile")` returns the ticker list: `["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", ...]`.

### Step 3: Fetching Statements from yfinance
`DataFetcher.fetch_all(tickers)` calls the yfinance API for each ticker, retrieving:
- `quarterly_income_stmt` — quarterly P&L (up to 8 quarters)
- `quarterly_balance_sheet` — quarterly balance sheet
- `quarterly_cashflow` — quarterly cash flow statement
- `income_stmt` — annual income statement (up to 4 years)
- `balance_sheet` — annual balance sheet
- `cashflow` — annual cash flow statement

Additionally, `fetch_market_info(ticker)` retrieves real-time market data: PE ratio, PB ratio, EV/EBITDA, EPS, market cap, and dividend yield.

### Step 4: Parsing Raw Data
`FinancialParser.parse_all(raw_data)` normalizes every DataFrame:
1. Transposes yfinance's column-per-date format to row-per-date.
2. Maps raw column names to canonical keys using alias dictionaries (e.g., "Total Revenue" → `total_revenue`).
3. Converts all values to float64.
4. Sorts by date ascending.
5. Drops duplicate columns.

### Step 5: Computing Financial Ratios
`RatioEngine.compute_all(parsed, market_info)` extracts the latest quarter's data for each company and computes 26 financial ratios plus 8 raw values.

### Step 6: Computing Growth Metrics
`RatioEngine.compute_growth_metrics(parsed)` computes year-over-year growth rates for revenue, net income, EBITDA, and operating cash flow using annual statements.

### Step 7: Merging into Ratio Matrix
The growth metrics are joined to the ratio DataFrame, creating a complete ratio matrix with rows = tickers and columns = all ratios.

### Step 8: Detecting Outliers
`OutlierEngine.detect(ratio_matrix)` runs IQR and Z-score tests on every ratio column, producing a DataFrame of outlier records with severity scores.

### Step 9: Running Benchmark Pipeline
`BenchmarkEngine.run(ratio_matrix, outlier_df)` executes the 11-step benchmark pipeline (detailed in Part 2).

### Step 10: Computing Health Scores
`ScoringEngine.score(ratio_matrix)` produces a separate health score using MinMax/Robust scaling — this operates independently from the benchmark engine.

### Step 11: Generating Explanations
Both `BenchmarkEngine._generate_explanations()` and `BenchmarkExplainer.explain_all()` produce human-readable narratives.

### Step 12: Rendering Dashboard
All results are stored in `st.session_state` and rendered across 9 tabs with interactive Plotly charts, filterable tables, and downloadable CSVs/Excel reports.

---

## Section 4 — Financial Data Sources

### 4.1 What Data Is Pulled

| Statement | Frequency | Depth | Key Fields |
|-----------|-----------|-------|------------|
| Income Statement | Quarterly & Annual | ~2 years | Revenue, Gross Profit, Operating Income, EBITDA, Net Income, Interest Expense, Tax, EPS |
| Balance Sheet | Quarterly & Annual | ~2 years | Total Assets, Total Liabilities, Total Equity, Current Assets, Current Liabilities, Cash, Inventory, Receivables, Total Debt |
| Cash Flow | Quarterly & Annual | ~2 years | Operating Cash Flow, Capital Expenditure, Free Cash Flow |
| Market Info | Real-time | Current | PE Ratio, PB Ratio, EV/EBITDA, EPS (TTM), Market Cap, Dividend Yield |

### 4.2 Why Quarterly Data

Quarterly data provides the most recent financial snapshot. Annual statements lag by up to 12 months. For ratio computation, the system uses the **latest available quarter** to capture the most current financial position.

### 4.3 Why 2 Years of History

Two years of quarterly data (8 quarters) provides sufficient history for:
- Trend analysis (QoQ and YoY changes)
- Seasonal pattern detection
- Growth rate computation (comparing latest year to prior year)

### 4.4 Data Quality Issues

| Issue | How It's Handled |
|-------|-----------------|
| Missing fields | `safe_divide()` returns `NaN` instead of crashing |
| Inconsistent labels | Alias mapping normalizes 60+ variants to canonical keys |
| Delisted/invalid tickers | Caught by try/except in fetch loop; skipped with warning |
| API rate limits | Configurable delay between calls + retry decorator |
| `inf` values | Replaced with `NaN` before any computation |

---

## Section 5 — Financial Parsing and Standardization

### 5.1 Why Raw yfinance Data Cannot Be Used Directly

yfinance returns DataFrames where:
- Column names vary across companies (e.g., "Total Revenue" for one company, "Revenue" for another, "Net Revenue" for a third).
- The orientation is transposed (dates as columns, fields as rows).
- Some fields appear under different names in different quarters.
- Duplicate column names can occur.

### 5.2 Alias Mapping

The parser maintains three alias dictionaries:
- **`INCOME_ALIASES`**: 15 canonical fields mapped from 50+ variants
- **`BALANCE_ALIASES`**: 14 canonical fields mapped from 40+ variants
- **`CASHFLOW_ALIASES`**: 6 canonical fields mapped from 20+ variants

**Example**: The canonical field `total_revenue` accepts any of: "Total Revenue", "Revenue", "Net Revenue", "TotalRevenue", "Net Sales", "Revenues", "Operating Revenue".

### 5.3 Parsing Pipeline

1. **Transpose**: Convert yfinance's field-as-row format to field-as-column.
2. **Alias resolution**: For each canonical key, search all known aliases in the DataFrame columns. Take the first match.
3. **Type casting**: Force all values to `float64`.
4. **Date sorting**: Sort index chronologically (ascending).
5. **Deduplication**: Drop duplicate columns if alias mapping created them.
6. **NaN handling**: Preserve `NaN` — downstream functions handle missing values gracefully.

---

*Continued in Part 2: Ratio Engine & Outlier Detection*
