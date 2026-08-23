# NSE Financial Outlier Detection & Benchmarking System
## Technical Documentation — Part 3: Benchmarking, Scoring & Explanations

---

## Section 9 — Benchmark Logic

The benchmarking engine is the core analytical component of the system. It converts raw, differently-scaled financial ratios into standardized scores, allowing for apples-to-apples comparison between companies.

### 9.1 Ratio-Centric Approach
Unlike traditional scoring models that compare companies holistically from the start, this system computes the benchmark **strictly at the ratio level**. 
1. Every ratio (e.g., Gross Margin) is evaluated across all companies in the sector.
2. The scores for each ratio are then aggregated into pillars.
3. The pillars are aggregated into the final composite score.

This bottom-up approach allows the system to pinpoint exactly *why* a company scored the way it did, down to the specific weight of an individual metric.

### 9.2 The "Clean" Matrix Concept
Before benchmarking begins, the system masks extreme outliers.
If Company A has an extreme outlier in `debt_to_equity`, that specific cell is replaced with `NaN` in the benchmark pipeline. 
- **Why?** If the outlier was included, the scale would stretch so far that all other companies would appear virtually identical, destroying the comparative value of the benchmark.
- **Result**: The benchmark calculation uses a "clean" matrix containing only normal, representative business data.

---

## Section 10 — Robust Scaling

### 10.1 What is Robust Scaling?
Financial ratios exist on vastly different scales. Gross margin is a percentage (e.g., 40.0), while Current Ratio is a small decimal (e.g., 1.5). To combine them, they must be converted to a common scale.

Standard scaling uses Mean and Standard Deviation. However, financial data is highly skewed. The system uses **Robust Scaling**, which relies on the Median and the Interquartile Range (IQR).

### 10.2 Formula
For a given ratio value `x`:
`Scaled Value = (x - Median) / IQR`

### 10.3 Why Robust Scaling?
- **Resilient to skewness**: Median is not dragged by extreme values the way Mean is.
- **Resilient to variance**: IQR represents the middle 50% of the data, ignoring tails.
- **Outcome**: A scaled value of `0` means the company is exactly at the sector median. A value of `+1` means the company is one full IQR above the median.

---

## Section 11 — Directional Normalization

### 11.1 The Directional Problem
After robust scaling, a positive number means "above average". But for financial ratios, "above average" is not always good.
- **Above average ROE** = Good (Positive signal)
- **Above average Debt/Equity** = Bad (Negative signal)

### 11.2 The Inversion Logic
The system applies a directional mask:
- For "Higher is Better" ratios (e.g., margins, returns), the scaled values remain unchanged.
- For "Lower is Better" ratios (e.g., leverage), the scaled values are multiplied by `-1`.

**Result**: After step 11, across *all* ratios, a **positive scaled value ALWAYS means "better than sector median"**, and a negative value means "worse than sector median".

---

## Section 12 — Benchmark Score Calculation

### 12.1 Sigmoid Transformation (0–100 Mapping)
The scaled, directionally-aligned values (which range roughly from -3.0 to +3.0) are passed through an adjusted sigmoid function:
`Score = 100 / (1 + exp(-scaled_value))`

This maps all theoretically infinite mathematical values into a bounded `0` to `100` range, where:
- Score `50` = Exactly sector median
- Score > `50` = Better than median
- Score < `50` = Worse than median

### 12.2 Aggregation hierarchy
1. **Ratio Score**: The 0–100 score for a single metric.
2. **Pillar Score**: The weighted average of the ratio scores within a specific category.
3. **Composite Benchmark Score**: The weighted average of the five Pillar Scores.

---

## Section 13 — Pillar Definitions

The system groups the 17 core benchmark ratios into 5 pillars.

1. **Profitability (30% weight)**
   - Ratios: Gross Margin (20%), Operating Margin (25%), Net Margin (25%), ROE (15%), ROA (15%).
   - *Meaning*: Ability to extract profit from operations and capital.

2. **Solvency (20% weight)**
   - Ratios: Debt to Equity (40%), Debt Ratio (35%), Interest Coverage (25%).
   - *Meaning*: Long-term stability and resilience against debt burdens.

3. **Growth (20% weight)**
   - Ratios: Revenue Growth (35%), Net Income Growth (35%), OCF Growth (30%).
   - *Meaning*: Trajectory and momentum over the past year.

4. **Liquidity (15% weight)**
   - Ratios: Current Ratio (40%), Quick Ratio (35%), Cash Ratio (25%).
   - *Meaning*: Short-term survival; ability to pay immediate bills.

5. **Efficiency (15% weight)**
   - Ratios: Asset Turnover (40%), Inventory Turnover (30%), Receivables Turnover (30%).
   - *Meaning*: Operational tightness; how well assets are spun into sales.

---

## Section 14 — Composite Score & Categories

The final Composite Benchmark Score is a single number representing a company's relative financial health compared strictly to its current sector peers.

**Categories:**
- **90–100: [Tier 1 - Elite]** (Top-tier performer across almost all pillars)
- **75–90: [Tier 2 - Strong]** (Excellent fundamentals, few weaknesses)
- **60–75: [Tier 3 - Healthy]** (Solid, above-average core operations)
- **40–60: [Tier 4 - Moderate]** (Average; performing in line with the sector pack)
- **20–40: [Tier 5 - Weak]** (Below average; distinct operational or financial drag)
- **0–20: [Tier 6 - Critical]** (Severe underperformance or distress relative to peers)

---

## Section 15 — Company Ranking

Companies are ranked descending based on their Composite Benchmark Score.
- **Rank 1**: The best performing company in the selected peer group.
- **Interpretation Rule**: Because the benchmark uses *robust scaling against the sector median*, a "Strong" score in the Automobile sector cannot be directly compared to a "Strong" score in the IT sector. The rank and score are purely relative to the currently selected peers.

---

## Section 16 — Descriptive Ratio Breakdown

To ensure the black-box score is fully transparent, the system generates a `contribution_df` table.
For every company, this table shows exactly how the final score was built.

**Columns:**
- `Pillar`: The parent category.
- `Ratio`: The specific metric.
- `Raw Value`: The actual unscaled financial number.
- `Benchmark Score`: The 0-100 mapped score for this metric.
- `Weight`: The metric's relative impact on the composite score.
- `Contribution`: `Score × Weight` (Summing these equals the composite score).
- `Status`: Categorical tag (`strong` >65, `weak` <40, `neutral`, or `outlier-excluded`).

This table serves as the audit trail for the benchmark engine.

---

## Section 17 — Explanation Engine

The `BenchmarkExplainer` module translates the raw math of the contribution table into human-readable narratives suitable for a management report.

### 17.1 How it Works
1. It looks at a company's performance within a specific pillar.
2. It counts how many metrics have a `strong` status vs `weak` status.
3. It selects a linguistic template based on that distribution (e.g., "Strong", "Weak", "Mixed", "Neutral").
4. It inserts the human-readable names of the driving metrics into the template.

### 17.2 Narrative Structure
A generated explanation consists of:
- **Overall Statement**: Rank, score, category, and a list of highest and lowest performing pillars.
- **Pillar Sentences**: E.g., "Mixed profitability: Gross Margin is solid, but ROE needs attention."
- **Outlier Note**: Explicitly lists any ratios that were ignored due to being statistical outliers.

This ensures that a non-technical stakeholder can immediately understand the output of the complex statistical pipeline.

---

*Continued in Part 4: Visualization, Limitations & Conclusion*
