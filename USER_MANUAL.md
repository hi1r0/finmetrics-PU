# FinMetrics Suite v2.0 - End-to-End User Manual

**AI-Powered Cross-Sectional Financial Analysis, Anomaly Detection, and Strategic Benchmarking for NSE-Listed Sectors and Private Clients.**

---

## Table of Contents
1. [Executive Summary and Value Proposition](#1-executive-summary-and-value-proposition)
2. [Global Configuration and Sidebar Control](#2-global-configuration-and-sidebar-control)
3. [Core Analytical Workflows](#3-core-analytical-workflows)
4. [Dashboard Tab-by-Tab Detailed Reference](#4-dashboard-tab-by-tab-detailed-reference)
5. [Comprehensive Visual Interface Walkthrough (Image Descriptions)](#5-comprehensive-visual-interface-walkthrough-image-descriptions)

---

## 1. Executive Summary and Value Proposition

Traditional financial analysis suffers from significant friction points: extensive time spent manually parsing PDF accounts, subjective normalization processes, and a lack of standardized benchmarking across peers. 

The FinMetrics Suite v2.0 resolves these inefficiencies by automating the entire pipeline, from raw data collection to deep analytical scoring and narrative explanations, executing complex workflows in under 60 seconds.

### The System Core Pillars:
*   **Automated Ingestion**: Directly fetches quarterly and annual statements for over 100 major NSE-listed companies across 13 sectors using Yahoo Finance. Data is normalized instantly via a proprietary 60-field alias-mapping engine.
*   **Statistical Outlier Scans**: Implements Tukey Fences (IQR), robust standard deviations (Z-Score), and multi-variate unsupervised anomalies (Isolation Forest) to isolate erratic accounting cells and ensure data integrity.
*   **Strategic Benchmarking**: Calculates over 30 ratios spanning Liquidity, Profitability, Solvency, Efficiency, Growth, Valuation, and Cash Flow. Ratios are scored using robust outlier-resistant scaling techniques.
*   **Client Comparator**: Benchmarks private companies (via standard CSV ratios or direct Tally ERP journal entries) directly against their selected public peer groups.
*   **SWOT Classifier**: Converts comparative metrics into a strategic 2x2 SWOT matrix (Strengths, Weaknesses, Opportunities, Threats) featuring plain-English analytical explanations.

---

## 2. Global Configuration and Sidebar Control

The sidebar acts as the global control center of the FinMetrics Suite v2.0. It manages security credentials, performance optimization, and clean memory states. All interface actions are designed to adapt instantly to user selections, with the sidebar maintaining persistent configurations across re-runs.

### Sidebar Components and Controls:

1.  **AI Search Integration and API Key Status**: Scans environment variables for a valid API key. A positive status enables natural-language AI searches for public peer tickers.
2.  **Use Data Cache (Toggle)**: A switch to enable or disable local caching to prevent API rate limiting and reduce loading times.
3.  **Clear All Cache (Action Button)**: A critical action button that deep-purges the system, clearing RAM caches and deleting persistent Parquet files.

---

## 3. Core Analytical Workflows

The application operates as a dual-phase system. Phase 1 establishes the public sector baseline. Phase 2 integrates a private client against that established baseline.

### Phase 1: Building Sector Benchmarks
Users navigate to the Home Tab, define the scope (Sector, Industry, or AI Search), optionally override tickers, adjust advanced calibration settings (IQR, Z-Score, Isolation Forest), and execute the benchmark build.

### Phase 2: Standard Client CSV Comparison
Users run Phase 1 for a target sector, navigate to the Client Comparison section, select the stored sector, upload a formatted CSV containing client ratios, and execute the comparison.

### Phase 3: TallySync Journal and Ledger Ingestion
Users export Ledger Master and Journal Vouchers from Tally ERP, upload these CSV files in the TallySync Upload sub-tab, and the system automatically parses, maps, and computes a Trial Balance and comparative scoring.

---

## 4. Dashboard Tab-by-Tab Detailed Reference

*   **Home Tab**: The primary command hub featuring scope selectors, calibration sliders, execution buttons, and client upload dropzones.
*   **Ratio Scorecard Tab**: Displays benchmark scorecards for selected companies, categorizing ratios against the sector baseline using horizontal bar charts and detailed data tables.
*   **Outliers Tab**: Highlights extreme financial values across the peer group using multi-color scatter plots and univariate/multivariate data tables.
*   **Peer Benchmark Tab**: Presents sector-wide descriptive statistics via a dense heat map and comprehensive data tables.
*   **Composite Score Tab**: Aggregates and displays weighted financial health scores for all companies within the peer group using ranked bar charts.
*   **Client Comparison Tab**: Unlocked after client data ingestion, containing specialized sub-tabs for Trial Balance viewing, Client Ratio Scorecards, Client Composite Scores, Ratio Distribution mapping, and a strategic 2x2 SWOT matrix.
*   **Export Tab**: Handles reporting pipelines, allowing users to extract the complete analysis into a multi-sheet Excel workbook.

---

## 5. Comprehensive Visual Interface Walkthrough (Image Descriptions)

This section provides a detailed textual breakdown of every visual asset (38 images) captured during a standard application workflow, describing the interface layout, data visualizations, and active states.

### Home Tab and Configuration Sequences
1.  **Screenshot 2026-05-18 104451**: Displays the Home tab focusing on the "1. Define Scope" section. The "Analysis Unit" radio button is set to "Sector". A dropdown menu labeled "Select Sector" shows "Automobile" as the active selection. Below this, the "Ticker Override" and "2. Calibration (Advanced)" expander menus are collapsed. The "3. Build Benchmark" section displays a prominent "Run Phase 1: Build Benchmark" button. The "4. Client Comparison" section shows two tab headers: "Standard CSV Upload" and "TallySync Upload".
2.  **Screenshot 2026-05-18 104536**: Shows the "Define Scope" section with the "Ticker Override" expander open. Inside, a multi-line text area labeled "Custom Tickers (one per line, .NS suffix)" is populated with specific ticker symbols: MARUTI.NS, TATAMOTORS.NS, M&M.NS, BAJAJ-AUTO.NS, and HEROMOTOCO.NS.
3.  **Screenshot 2026-05-18 104645**: The "Analysis Unit" radio button is now set to "Industry". The corresponding dropdown menu shows "2-Wheelers" selected. The "Ticker Override" expander is open, displaying an updated list of custom tickers relevant to the selected industry: BAJAJ-AUTO.NS, HEROMOTOCO.NS, EICHERMOT.NS, and TVSMOTOR.NS.
4.  **Screenshot 2026-05-18 104701**: The "Analysis Unit" is set to "AI Search". The interface changes to display text input fields. "Describe the Industry" contains the text "fmcg". "Market / Country" contains "NSE India". A "Discover Tickers" button is visible, beneath which a green success banner reads "Found 29 relevant tickers!". The "Ticker Override" expander is open, listing the AI-discovered tickers, starting with HINDUNILVR.NS, ITC.NS, NESTLEIND.NS, BRITANNIA.NS, and DABUR.NS.
5.  **Screenshot 2026-05-18 104807**: Focuses on the "2. Calibration (Advanced)" section, which is expanded. A "Reset Defaults" button is visible. Below it are three horizontal slider controls: "IQR Multiplier" is set to 1.50, "Z-Score Threshold" is set to 3.50, and "Isolation Forest (%)" is set to 10. The "Build Benchmark" execution button is visible below this section.

### Client Upload Sequences
6.  **Screenshot 2026-05-18 104848**: Displays the "4. Client Comparison" section. The "Standard CSV Upload" tab is active. A dropdown labeled "Compare against stored sector" has "AI: chocolate" selected. A file dropzone labeled "Upload Client Ratios (CSV)" is visible, indicating a 200MB file size limit. A "Run Client Comparison" execution button is at the bottom.
7.  **Screenshot 2026-05-18 104914**: Shows the same "Standard CSV Upload" interface as the previous image, confirming the layout and active state of the CSV upload dropzone.
8.  **Screenshot 2026-05-18 104936**: Another view of the "Standard CSV Upload" interface, maintaining focus on the "Compare against stored sector" dropdown with "AI: chocolate" selected.
9.  **Screenshot 2026-05-18 105027**: The "TallySync Upload" tab is now active within the Client Comparison section. The interface displays two distinct file dropzones with dashed borders: "Journal CSV (JV)" and "Ledger Master CSV". Input fields for the client name and target benchmark sector are present, along with a "Process Tally Data" execution button.

### Core Analysis Dashboards
10. **Screenshot 2026-05-18 105106**: Displays the upper section of the "Ratio Scorecard" tab. Three prominent horizontal metric cards display the aggregate counts: "Above Benchmark" shows 43, "At Benchmark" shows 34, and "Below Benchmark" shows 23. A "Select Company" dropdown is visible below the metric cards.
11. **Screenshot 2026-05-18 105124**: Shows the middle section of the "Ratio Scorecard" tab. The "Select Company" dropdown is set to "KR". Below is a detailed heatmap visualization grouping ratios by category (Profitability, Liquidity). Each ratio is represented by a horizontal bar indicating its percentile rank (0 to 100), color-coded to signify performance (green for strong, yellow for neutral, red for weak), with text annotations providing the exact raw value and benchmark status.
12. **Screenshot 2026-05-18 105221**: Displays the lower section of the "Ratio Scorecard" tab containing the "Raw Scorecard Data" table. The table is populated with data for the ticker "KR". Columns include ticker, pillar, ratio, raw_value, peer_median, quartiles (peer_q1, peer_q3), percentiles (peer_p10, peer_p90), percentile_rank, position_label, health_label, signal, and an exclusion flag.
13. **Screenshot 2026-05-18 105243**: Shows the upper section of the "Outliers" tab. A large multi-color scatter plot visualizes the outliers. The X-axis represents "Deviation from Sector Median (%)" and the Y-axis represents "Severity Score". Individual companies are plotted as circular nodes (bubbles). The nodes are color-coded based on severity, with bright red indicating extreme deviations and teal indicating moderate deviations. Nodes for specific tickers like SFM, GO, and ACI are visible.
14. **Screenshot 2026-05-18 105311**: Displays the lower section of the "Outliers" tab, containing a detailed data table listing the identified univariate outliers. The table includes columns for ticker, ratio, specific values, sector medians, statistical bounds, Z-scores, calculated deviation percentages, and severity scores. Rows for tickers ACI, SFM, GO, and VLGEA are clearly visible, showing specific triggered metrics like dividend_yield and interest_coverage.
15. **Screenshot 2026-05-18 105332**: Shows a secondary visualization within the "Outliers" tab. This chart represents the results of a multivariate anomaly detection scan (Isolation Forest), highlighting specific companies that exhibit complex, multi-dimensional structural anomalies across their financial ratios.
16. **Screenshot 2026-05-18 105355**: Displays the upper section of the "Peer Benchmark" tab. The primary visualization is a dense "Peer Stats Heatmap". The rows list various financial ratios (e.g., P/B Ratio, P/E Ratio, Cash Conversion Ratio). The columns represent statistical segments (Bottom 10%, Bottom 25%, Median, Mean, Top 25%, Top 10%). The cells within the grid are color-coded based on the numerical magnitude, providing a visual density map of the sector's financial distribution.
17. **Screenshot 2026-05-18 105441**: Shows the lower section of the "Peer Benchmark" tab, containing the "Descriptive Statistics" data table. This table provides the exact numerical data backing the heatmap. Columns include the ratio name, median, quartiles (q1, q3), percentiles (p10, p90), mean, standard deviation, number of peers analyzed, and number of excluded peers. Rows for current_ratio, quick_ratio, and cash_ratio are visible.
18. **Screenshot 2026-05-18 105505**: Displays the upper section of the "Composite Score" tab. The main visualization is a horizontal bar chart titled "Financial Health Score - Sector Ranking". It ranks companies from highest to lowest score (0 to 100). The bars feature a color gradient from red (low score) to purple (high score). The chart shows SFM at the top with 78.2 points, followed by VLGEA, GO, WMK, NGVC, KR, and ACI at the bottom with 34.8 points.
19. **Screenshot 2026-05-18 105540**: Shows the lower section of the "Composite Score" tab, containing a data table that breaks down the composite score. Columns include ticker, composite_score, sector_rank, percentile, risk_category, and individual scores for efficiency, growth, liquidity, profitability, and solvency. The table lists the detailed breakdown for companies including ACI, GO, KR, NGVC, SFM, VLGEA, and WMK.

### Client Comparison Dashboards
20. **Screenshot 2026-05-18 105714**: Displays the "Trial Balance" sub-tab within the "Client Comparison" section. Three primary summary cards show "Total Ledgers" (1385), "Total Debit" (590,856,997.09), and "Total Credit" (590,856,994.96). Below these is the Trial Balance data table with columns for Ledger Name, Final Debit, Final Credit, and Benchmark Category, showing the initial rows of the processed ledger data.
21. **Screenshot 2026-05-18 105732**: Shows a lower segment of the "Trial Balance" data table. The visible rows demonstrate how specific ledgers are mapped to benchmark categories (e.g., "0% Integrated Inward Supply" mapped to "cogs", "0% Integrated Outward Supply" mapped to "revenue"). A button labeled "Download Trial Balance CSV" is located below the table.
22. **Screenshot 2026-05-18 105846**: Displays the upper section of the "Ratio Scorecard" sub-tab for the private client. The title reads "Ratio Scorecard - FMCG Client". Three metric cards summarize the client's performance against the benchmark: "Above Benchmark" shows 5, "At Benchmark" shows 0, and "Below Benchmark" shows 8.
23. **Screenshot 2026-05-18 105908**: Shows the middle section of the client's "Ratio Scorecard" sub-tab. The heatmap visualization displays the FMCG Client's specific percentile ranks for Profitability, Liquidity, Solvency, and Efficiency ratios. The bars are distinctly colored (deep green for exceptional performance, stark red for critical underperformance) with textual annotations for the raw values.
24. **Screenshot 2026-05-18 105951**: Displays the lower section of the client's "Ratio Scorecard" sub-tab, showing the "Raw Scorecard Data" table specifically for the FMCG Client. The table lists the calculated ratios, raw values, peer medians, percentile ranks, and assigned health labels, allowing for granular review of the client's metrics.
25. **Screenshot 2026-05-18 110022**: Displays the upper section of the "Composite Scores" sub-tab for the private client. Three summary cards display the "Client Composite Score" (44.8 / 100), the overall "Risk Category" (Weak), and the "Sector Percentile" rank (14th).
26. **Screenshot 2026-05-18 110046**: Shows the "Financial Health Score - Sector Ranking (with Client)" bar chart. This is identical to the main sector ranking chart, but the private FMCG Client is now inserted into the ranking hierarchy. The FMCG Client's bar is visually highlighted with a distinct white border, placing it between KR (46.7) and ACI (34.8) with a score of 44.8.
27. **Screenshot 2026-05-18 110103**: Displays the lower section of the client's "Composite Scores" sub-tab. A data table titled "Client Pillar Breakdown" shows the individual component scores for the FMCG Client across profitability (85), liquidity (0), solvency (46.67), efficiency (0), and growth (50).
28. **Screenshot 2026-05-18 110142**: Shows the "Ratio Distribution" sub-tab within the Client Comparison section. Two dropdown menus allow the user to select the X-Axis Ratio and Y-Axis Ratio. Below is a 2D scatter plot designed to map the competitive landscape based on the selected metrics.
29. **Screenshot 2026-05-18 110213**: Provides a more detailed view of the "Competitive Mapping" scatter plot from the Ratio Distribution sub-tab. The plot shows numerous circular nodes representing public peers. The private client is plotted as a highly distinct node, allowing users to visually assess the client's spatial positioning relative to industry clusters.
30. **Screenshot 2026-05-18 110246**: Displays the upper half of the "SWOT Insights" sub-tab. The interface is divided into a 2x2 grid. The top-left quadrant, "Strengths (Internal / Positive)", lists high-performing metrics for the client, including Gross Margin, Operating Margin, Net Margin, and Return on Equity, alongside analytical text describing strong earnings power. The top-right quadrant, "Weaknesses (Internal / Negative)", lists poorly performing metrics such as Return on Assets, Return on Capital Employed, Asset Turnover, and Receivables Turnover, accompanied by text detailing margin compression and asset under-utilization.
31. **Screenshot 2026-05-18 110327**: Shows the lower half of the "SWOT Insights" 2x2 grid. The bottom-left quadrant, "Opportunities (External / Strategic)", highlights the Debt Ratio, suggesting conservative leverage provides untapped borrowing capacity. The bottom-right quadrant, "Threats (External / Risk)", highlights critical liquidity risks indicated by extremely low Current Ratio and Quick Ratio metrics.
32. **Screenshot 2026-05-18 110350**: Displays the "Export" tab. The interface is minimal, focusing entirely on a primary action button labeled "Generate Excel Report". This triggers the backend process to compile all analysis data into a downloadable multi-sheet workbook.

### High-Resolution Plotly Visualizations (Export Quality)
33. **newplot (6)**: A high-resolution, export-quality rendering of the horizontal bar chart heatmap from the Ratio Scorecard tab, specifically generated for the ticker "KR". It details percentile rankings across all financial pillars with crisp text rendering.
34. **newplot (7)**: A high-resolution, export-quality rendering of the dense Peer Stats Heatmap from the Peer Benchmark tab. The statistical grid (showing deciles, quartiles, and medians) is rendered with clear cell boundaries and distinct color scaling suitable for presentation reports.
35. **newplot (8)**: A high-resolution, export-quality rendering of the Financial Health Score Sector Ranking bar chart. It clearly delineates the peer group hierarchy from SFM at the top to ACI at the bottom.
36. **newplot (9)**: A high-resolution, export-quality rendering of the Ratio Scorecard heatmap generated specifically for the private FMCG Client. It clearly visualizes the extreme disparities in the client's performance (e.g., extremely high profitability against extremely low liquidity).
37. **newplot (10)**: A high-resolution, export-quality rendering of the Financial Health Score Sector Ranking bar chart, but with the private FMCG Client integrated and highlighted within the peer ranking list.
38. **newplot (11)**: A high-resolution, export-quality rendering of the 2D Peer Competitive Mapping scatter plot, showing the distinct spatial positioning of the client node relative to the industry peer cluster.
