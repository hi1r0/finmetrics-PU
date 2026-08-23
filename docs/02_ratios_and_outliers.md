# NSE Financial Outlier Detection & Benchmarking System
## Technical Documentation — Part 2: Ratios, Formulas & Outliers

---

## Section 6 — Ratio Engine

The Ratio Engine computes all financial metrics from the parsed statements. Ratios are grouped into categories to provide a holistic view of financial health.

### 6.1 Liquidity Ratios
Measure a company's ability to pay off its short-term debt obligations.
- **Current Ratio**: Broadest measure of short-term liquidity. High is better, though extremely high may indicate inefficient cash use.
- **Quick Ratio**: Stricter than current ratio; excludes inventory (which is harder to liquidate). High is better.
- **Cash Ratio**: Most conservative liquidity ratio, measuring only cash against short-term liabilities. High is better.

### 6.2 Leverage / Solvency Ratios
Measure how much debt a company is using to finance its assets and its ability to meet long-term obligations.
- **Debt to Equity**: Compares total debt to shareholders' equity. Low is generally better (less financial risk).
- **Debt Ratio**: Proportion of a company's total assets financed by debt. Low is better.
- **Interest Coverage**: Ability to pay interest expenses from operating profit. High is better; below 1.5 is a warning sign.

### 6.3 Profitability Ratios
Measure a company's ability to generate earnings relative to sales, assets, and equity.
- **Gross Margin**: Percentage of revenue left after deducting the cost of goods sold. High is better.
- **Operating Margin**: Percentage of revenue left after paying operating expenses. High is better.
- **Net Margin**: Percentage of revenue remaining as profit after all expenses, taxes, and interest. High is better.
- **ROE (Return on Equity)**: Profitability relative to shareholders' equity. High is better.
- **ROA (Return on Assets)**: How efficiently assets are used to generate profit. High is better.
- **ROCE (Return on Capital Employed)**: Profitability of the capital invested. High is better.

### 6.4 Efficiency Ratios
Measure how effectively a company uses its assets to manage operations.
- **Asset Turnover**: Revenue generated per unit of asset. High is better.
- **Inventory Turnover**: How many times inventory is sold and replaced over a period. High is better.
- **Receivables Turnover**: Effectiveness in collecting revenue. High is better.

### 6.5 Cash Flow Ratios
Measure the cash generating ability of the operations.
- **Operating CF Ratio**: Cash from operations relative to current liabilities. High is better.
- **FCF Margin**: Free cash flow as a percentage of revenue. High is better.
- **Cash Conversion Ratio**: Proportion of net income converted to operating cash flow. High is better.

### 6.6 Valuation Ratios
Market-based multiples measuring how the stock is priced.
- **PE Ratio**: Price to Earnings. Low can indicate undervaluation, but depends on growth expectations.
- **PB Ratio**: Price to Book value. Low can indicate a value stock.
- **EV/EBITDA**: Enterprise Value to EBITDA. Useful for comparing companies regardless of capital structure.
- **EPS**: Earnings Per Share. High is better.

### 6.7 Growth Metrics
Measure the year-over-year percentage change in fundamental metrics.
- **Revenue Growth**: High is better.
- **Net Income Growth**: High is better.
- **EBITDA Growth**: High is better.
- **OCF Growth**: Operating cash flow growth. High is better.

---

## Section 7 — Ratio Formulas

Mathematical definitions for the computed metrics.

*Note: All margin and return metrics are multiplied by 100 to display as percentages.*

**Liquidity**
- `Current Ratio` = Current Assets / Current Liabilities
- `Quick Ratio` = (Current Assets - Inventory) / Current Liabilities
- `Cash Ratio` = Cash & Equivalents / Current Liabilities

**Leverage**
- `Debt to Equity` = Total Debt / Total Equity
- `Debt Ratio` = Total Liabilities / Total Assets
- `Interest Coverage` = Operating Income / |Interest Expense|

**Profitability**
- `Gross Margin` = (Gross Profit / Total Revenue) × 100
- `Operating Margin` = (Operating Income / Total Revenue) × 100
- `Net Margin` = (Net Income / Total Revenue) × 100
- `ROE` = (Net Income / Total Equity) × 100
- `ROA` = (Net Income / Total Assets) × 100
- `ROCE` = (Operating Income / (Total Assets - Current Liabilities)) × 100

**Efficiency**
- `Asset Turnover` = Total Revenue / Total Assets
- `Inventory Turnover` = Total Revenue / Inventory
- `Receivables Turnover` = Total Revenue / Accounts Receivable

**Cash Flow**
- `Operating CF Ratio` = Operating Cash Flow / Current Liabilities
- `FCF Margin` = (Free Cash Flow / Total Revenue) × 100
- `Cash Conversion` = Operating Cash Flow / Net Income

**Growth (YoY)**
- `Metric Growth` = ((Metric_Current / Metric_Prior) - 1) × 100

**Handling Missing Denominators:** If the denominator is 0, NaN, or missing, the system's `safe_divide()` returns `NaN`. This prevents infinite values (`inf`) from breaking the statistical models downstream.

---

## Section 8 — Outlier Detection

### 8.1 Why Outlier Detection is Needed
Financial data is noisy. A company might have a PE ratio of 5000 due to near-zero earnings, or an interest coverage of -400. If we compare companies directly using averages or standard scaling, these extreme values skew the entire distribution, masking the true relative performance of normal companies.

### 8.2 The Interquartile Range (IQR) Method
The system uses the Tukey Fence method (IQR) as the primary detection mechanism because it is **non-parametric** — it does not assume financial ratios follow a normal (bell-curve) distribution, which they rarely do.

- **Q1 (25th Percentile)**: The value below which 25% of the data falls.
- **Q3 (75th Percentile)**: The value below which 75% of the data falls.
- **IQR (Interquartile Range)** = Q3 - Q1
- **Lower Bound** = Q1 - (1.5 × IQR)
- **Upper Bound** = Q3 + (1.5 × IQR)

Any value falling outside the `[Lower Bound, Upper Bound]` range is flagged as a statistical outlier.

### 8.3 Z-Score and Isolation Forest Additions
- **Z-Score**: Measures how many standard deviations a value is from the mean. The system calculates a robust Z-score and flags values where `|Z| > 2.5`.
- **Isolation Forest**: An unsupervised machine learning algorithm that detects multivariate anomalies (e.g., a company whose individual ratios are normal, but whose *combination* of ratios is highly unusual).

### 8.4 Severity Computation
To rank outliers, a composite severity score is calculated:
`Severity = (0.6 × IQR_Deviation) + (0.4 × Z_Score_Deviation)`
This tells the user not just *that* a value is an outlier, but *how extreme* it is compared to other outliers.

### 8.5 Direction and Interpretation
An outlier is just a mathematical extremity. The system interprets whether it's a "good" or "bad" extremity using the `HIGH_IS_BAD` and `LOW_IS_BAD` sets.

- **Positive Outlier [Favorable]**: e.g., Net Margin is mathematically exceptionally high (above upper fence). This represents an operational strength.
- **Negative Outlier [Adverse]**: e.g., Debt/Equity is exceptionally high. This represents a financial risk.

### 8.6 The "Cell-Level" Philosophy
**Crucial Design Choice:** When an outlier is detected, the company is *not* removed from the analysis. A company might have 29 normal ratios and 1 extreme outlier (e.g., due to a one-time write-off). 
Instead of dropping the company, the system isolates the specific **abnormal ratio cell**. This allows the company to still be benchmarked fairly on its 29 normal metrics.

---

*Continued in Part 3: Benchmarking & Scoring*
