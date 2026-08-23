"""Generate a polished PDF document for the FinMetrics Suite system overview."""
import os
from fpdf import FPDF

# ── Paths ──────────────────────────────────────────────────────────────────
ART_DIR = r"C:\Users\Hp\.gemini\antigravity\brain\77c9ec04-1e98-4d7f-bdf8-e1009977aeb1"
OUT_PATH = r"d:\Python\PYCHARM\PANDAS\FinMetrics_Suite_Overview.pdf"

SCREENSHOTS = {
    "home":     os.path.join(ART_DIR, "home_page.png"),
    "overview": os.path.join(ART_DIR, "overview_tab.png"),
    "company":  os.path.join(ART_DIR, "company_tab.png"),
    "ratios":   os.path.join(ART_DIR, "ratios_tab.png"),
    "outliers": os.path.join(ART_DIR, "outliers_tab.png"),
    "health":   os.path.join(ART_DIR, "health_tab.png"),
    "insights": os.path.join(ART_DIR, "insights_tab.png"),
    "export":   os.path.join(ART_DIR, "export_tab.png"),
}


class PDFReport(FPDF):
    """Custom PDF with header/footer and helper methods."""

    DARK_BG    = (14, 17, 23)
    CARD_BG    = (30, 37, 48)
    ACCENT     = (0, 212, 170)
    TEXT_WHITE = (224, 224, 232)
    TEXT_MUTED = (160, 160, 175)
    HEADING_CLR = (0, 212, 170)
    TABLE_HDR  = (20, 60, 80)
    TABLE_ROW1 = (22, 28, 36)
    TABLE_ROW2 = (28, 35, 45)
    BORDER_CLR = (50, 60, 75)
    LINK_CLR   = (100, 180, 255)

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 18, 18)

    # ── Header / Footer ───────────────────────────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return  # title page has its own header
        self.set_fill_color(*self.DARK_BG)
        self.rect(0, 0, 210, 297, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 6, "FinMetrics Suite - System Overview", align="L")
        self.set_x(-50)
        self.cell(0, 6, f"Page {self.page_no()}", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 5, "Confidential - For Internal Use Only", align="C")

    # ── Helpers ────────────────────────────────────────────────────────────
    def _bg(self):
        """Fill entire page background."""
        self.set_fill_color(*self.DARK_BG)
        self.rect(0, 0, 210, 297, "F")

    def section_title(self, num, text):
        """Render a numbered section heading."""
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.HEADING_CLR)
        self.cell(0, 10, f"{num}. {text}", new_x="LMARGIN", new_y="NEXT")
        # accent underline
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.6)
        x = self.l_margin
        self.line(x, self.get_y(), x + 174, self.get_y())
        self.ln(5)

    def sub_heading(self, text):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.TEXT_WHITE)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.TEXT_WHITE)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=8):
        x = self.get_x()
        self.set_x(x + indent)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.TEXT_WHITE)
        self.cell(4, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.set_x(x)

    def info_box(self, text):
        self.set_fill_color(20, 50, 60)
        self.set_draw_color(*self.ACCENT)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*self.TEXT_WHITE)
        x, y = self.get_x(), self.get_y()
        self.rect(x, y, 174, 12, "DF")
        self.set_xy(x + 3, y + 2)
        self.multi_cell(168, 4, text)
        self.ln(6)

    def add_table(self, headers, rows, col_widths=None):
        """Render a styled table."""
        n = len(headers)
        if col_widths is None:
            col_widths = [174 / n] * n

        # Header row
        self.set_fill_color(*self.TABLE_HDR)
        self.set_draw_color(*self.BORDER_CLR)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.ACCENT)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_WHITE)
        for ri, row in enumerate(rows):
            bg = self.TABLE_ROW1 if ri % 2 == 0 else self.TABLE_ROW2
            self.set_fill_color(*bg)
            row_h = 7
            # Check if any cell needs wrapping
            for i, cell in enumerate(row):
                if len(str(cell)) > col_widths[i] / 2:
                    row_h = max(row_h, 10)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], row_h, str(cell), border=1, fill=True, align="C")
            self.ln()
        self.ln(4)

    def add_screenshot(self, path, caption, max_w=170):
        """Embed a screenshot with caption."""
        if not os.path.exists(path):
            self.body_text(f"[Screenshot not found: {os.path.basename(path)}]")
            return
        # Check if enough space
        if self.get_y() > 180:
            self.add_page()
        self.image(path, x=self.l_margin + 2, w=max_w)
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 4, caption, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)


def build_pdf():
    pdf = PDFReport()

    # ══════════════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()

    # Accent bar at top
    pdf.set_fill_color(*pdf.ACCENT)
    pdf.rect(0, 0, 210, 4, "F")

    # Title block
    pdf.ln(60)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*pdf.TEXT_WHITE)
    pdf.cell(0, 14, "FinMetrics Suite", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*pdf.ACCENT)
    pdf.cell(0, 8, "System Overview Document", align="C", new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.ln(10)
    pdf.set_draw_color(*pdf.ACCENT)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)

    # Subtitle
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*pdf.TEXT_WHITE)
    pdf.cell(0, 7, "Automated Ratio-First Financial Analysis", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "for NSE-Listed Companies", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(30)

    # Metadata
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.TEXT_MUTED)
    pdf.cell(0, 6, "Prepared for: Management & Stakeholders", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Date: May 2026  |  Version: 1.0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Classification: Internal Use Only", align="C", new_x="LMARGIN", new_y="NEXT")

    # Bottom accent bar
    pdf.set_fill_color(*pdf.ACCENT)
    pdf.rect(0, 293, 210, 4, "F")

    # ══════════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*pdf.HEADING_CLR)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    toc = [
        ("1", "What Is This System?"),
        ("2", "How Does It Work?"),
        ("  2.1", "Data Collection"),
        ("  2.2", "Ratio Computation"),
        ("  2.3", "Outlier Detection"),
        ("  2.4", "Insights & Reporting"),
        ("3", "The Dashboard - What Each Tab Does"),
        ("  3.1", "Home"),
        ("  3.2", "Overview"),
        ("  3.3", "Company"),
        ("  3.4", "Ratios"),
        ("  3.5", "Outliers"),
        ("  3.6", "Health"),
        ("  3.7", "Insights"),
        ("  3.8", "Export"),
        ("4", "How to Use the System"),
        ("5", "Key Business Benefits"),
        ("6", "Technical Summary"),
    ]
    for num, title in toc:
        is_sub = num.startswith("  ")
        pdf.set_font("Helvetica", "" if is_sub else "B", 10 if is_sub else 11)
        pdf.set_text_color(*pdf.TEXT_WHITE)
        indent = 10 if is_sub else 0
        pdf.set_x(pdf.l_margin + indent)
        pdf.cell(0, 7, f"{num.strip()}   {title}", new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 - WHAT IS THIS SYSTEM
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("1", "What Is This System?")

    pdf.body_text(
        "The FinMetrics Suite is an automated financial analysis dashboard that "
        "automatically identifies companies in any sector of the National Stock Exchange (NSE) "
        "that behave significantly different from their peers - either positively or negatively."
    )
    pdf.ln(2)
    pdf.body_text("Think of it as an automated financial analyst that:")
    pdf.bullet("Pulls real-time financial data for all companies in a chosen sector")
    pdf.bullet("Computes 30+ financial ratios for each company")
    pdf.bullet("Compares every company against its sector peers")
    pdf.bullet("Flags the ones that stand out as statistical outliers")
    pdf.bullet("Explains why they stand out and whether it's a risk or an opportunity")
    pdf.ln(3)
    pdf.info_box(
        "NOTE: The system does not provide investment advice. It highlights anomalies that "
        "warrant further human investigation - saving analysts hours of manual spreadsheet work."
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2 - HOW DOES IT WORK
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("2", "How Does It Work?")

    pdf.body_text("The system follows a four-stage pipeline:")
    pdf.ln(2)

    # Pipeline diagram as styled boxes
    stages = [
        ("1", "Data Collection", "Fetch financial statements from Yahoo Finance"),
        ("2", "Ratio Computation", "Compute 30+ financial ratios per company"),
        ("3", "Outlier Detection", "Apply IQR, Z-Score, and Isolation Forest"),
        ("4", "Insights & Reporting", "Generate explanations and export reports"),
    ]
    box_w = 40
    gap = 2
    start_x = pdf.l_margin + 2
    y = pdf.get_y()
    for i, (num, title, desc) in enumerate(stages):
        x = start_x + i * (box_w + gap)
        # Box
        pdf.set_fill_color(20, 60, 80)
        pdf.set_draw_color(*pdf.ACCENT)
        pdf.rect(x, y, box_w, 22, "DF")
        # Number circle
        pdf.set_fill_color(*pdf.ACCENT)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*pdf.DARK_BG)
        pdf.set_xy(x + 2, y + 2)
        pdf.cell(6, 6, num, align="C")
        # Title
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*pdf.TEXT_WHITE)
        pdf.set_xy(x + 2, y + 8)
        pdf.cell(box_w - 4, 4, title, align="C")
        # Desc
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*pdf.TEXT_MUTED)
        pdf.set_xy(x + 2, y + 13)
        pdf.multi_cell(box_w - 4, 3, desc, align="C")
        # Arrow
        if i < 3:
            ax = x + box_w
            pdf.set_draw_color(*pdf.ACCENT)
            pdf.set_line_width(0.4)
            pdf.line(ax, y + 11, ax + gap, y + 11)
    pdf.set_y(y + 30)

    # Stage 1
    pdf.sub_heading("2.1  Data Collection")
    pdf.body_text(
        "The system connects to Yahoo Finance (yfinance) and automatically pulls the latest "
        "financial statements for every company in the selected sector:"
    )
    pdf.add_table(
        ["Statement", "Period", "Purpose"],
        [
            ["Income Statement", "Last 2 years (quarterly)", "Revenue, margins, profit trends"],
            ["Balance Sheet", "Last 2 years (quarterly)", "Debt levels, asset quality, liquidity"],
            ["Cash Flow Statement", "Last 2 years (quarterly)", "Cash generation, capital expenditure"],
            ["Market Data", "Current", "P/E, P/B, market cap, enterprise value"],
        ],
        [50, 50, 74],
    )

    # Stage 2
    pdf.sub_heading("2.2  Ratio Computation")
    pdf.body_text("The system calculates 30+ financial ratios, organized into five pillars:")
    pdf.add_table(
        ["Pillar", "Key Ratios", "What It Measures"],
        [
            ["Profitability", "Gross/Operating/Net Margin, ROE, ROA", "How efficiently profit is generated"],
            ["Liquidity", "Current, Quick, Cash Ratio", "Can short-term obligations be met?"],
            ["Solvency", "Debt/Equity, Debt Ratio, Interest Cov.", "How much debt risk is carried?"],
            ["Efficiency", "Asset/Inventory/Receivables Turnover", "How well resources are used"],
            ["Growth", "Revenue/Income/EBITDA/OCF Growth", "Is the company growing?"],
        ],
        [32, 70, 72],
    )

    # Stage 3
    pdf.add_page()
    pdf.sub_heading("2.3  Outlier Detection")
    pdf.body_text("Three independent statistical methods identify outliers:")
    pdf.add_table(
        ["Method", "How It Works", "What It Catches"],
        [
            ["IQR Fencing", "Flags values outside 1.5x IQR", "Values far from sector middle 50%"],
            ["Z-Score", "Flags >2.5 std deviations from mean", "Extreme statistical deviations"],
            ["Isolation Forest", "ML algorithm for multi-dim anomalies", "Multi-ratio anomalies"],
        ],
        [35, 70, 69],
    )
    pdf.body_text(
        "Each outlier receives a severity score (0-5) and is classified as either a "
        "Positive Outlier (unusually strong performance) or a Negative Outlier (red flag)."
    )

    # Stage 4
    pdf.sub_heading("2.4  Insights & Reporting")
    pdf.body_text(
        "The system generates plain-English explanations using rule-based logic, identifying "
        "risk flags (high debt, declining margins) and opportunity signals (fortress balance sheets, "
        "superior growth). Results can be exported as Excel workbooks or CSV files."
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3 - DASHBOARD TABS
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("3", "The Dashboard - What Each Tab Does")
    pdf.body_text("The dashboard has 8 tabs, each serving a specific analytical purpose.")

    # --- Home ---
    pdf.ln(3)
    pdf.sub_heading("3.1  Home - Landing Page")
    pdf.body_text(
        "The entry point of the application. Provides an overview of the system's capabilities "
        "and guides the user to select a sector and begin analysis."
    )
    pdf.add_screenshot(SCREENSHOTS["home"], "Figure 1 - Home Page")

    # --- Overview ---
    pdf.add_page()
    pdf.sub_heading("3.2  Overview - Sector-Wide Dashboard")
    pdf.body_text(
        "After running an analysis, this tab shows key metrics (companies analysed, total outliers), "
        "a color-coded Peer Ratio Matrix comparing all companies side-by-side, and a Z-Score "
        "normalized heatmap. The coloring is direction-aware: green always means 'financially healthy' "
        "regardless of whether higher or lower values are better for that ratio."
    )
    pdf.add_screenshot(SCREENSHOTS["overview"], "Figure 2 - Overview Tab with Peer Ratio Matrix")

    # --- Company ---
    pdf.add_page()
    pdf.sub_heading("3.3  Company - Individual Deep Dive")
    pdf.body_text(
        "Select any company to see its market data (price, market cap, P/E), financial ratio table "
        "with sector percentile ranks, a radar chart showing performance across all five pillars, "
        "and specific outlier flags for that company."
    )
    pdf.add_screenshot(SCREENSHOTS["company"], "Figure 3 - Company Tab with Radar Chart")

    # --- Ratios ---
    pdf.add_page()
    pdf.sub_heading("3.4  Ratios - Detailed Ratio Analysis")
    pdf.body_text(
        "Three sub-tabs: Distribution (box plots showing ratio spread across the sector), "
        "Correlation (heatmap showing inter-ratio relationships), and Peer Comparison (full table "
        "of actual ratio values with direction-aware coloring)."
    )
    pdf.add_screenshot(SCREENSHOTS["ratios"], "Figure 4 - Ratios Tab: Peer Comparison")

    # --- Outliers ---
    pdf.add_page()
    pdf.sub_heading("3.5  Outliers - Detection Dashboard")
    pdf.body_text(
        "The core analytical screen. Features interactive filters (All/Positive/Negative, minimum severity, "
        "specific ratio), a scatter plot mapping Deviation vs. Severity, a sortable Top Outliers table, "
        "box plots with outlier companies highlighted, Isolation Forest anomaly scores, and one-click "
        "CSV export of all outlier records."
    )
    pdf.add_screenshot(SCREENSHOTS["outliers"], "Figure 5 - Outliers Tab: Scatter Plot & Top Outliers Table")

    # --- Health ---
    pdf.add_page()
    pdf.sub_heading("3.6  Health - Financial Health Scorecard")
    pdf.body_text(
        "Each company receives a composite Financial Health Score (0-100) based on weighted pillar scores. "
        "Shows a ranking chart, pillar score breakdown table, and radar comparison."
    )
    pdf.add_table(
        ["Pillar", "Weight"],
        [
            ["Profitability", "25%"],
            ["Liquidity", "20%"],
            ["Solvency", "25%"],
            ["Efficiency", "15%"],
            ["Growth", "15%"],
        ],
        [87, 87],
    )
    pdf.add_screenshot(SCREENSHOTS["health"], "Figure 6 - Health Tab: Company Rankings")

    # --- Insights ---
    pdf.add_page()
    pdf.sub_heading("3.7  Insights - AI-Generated Explanations")
    pdf.body_text(
        "Automatically generated plain-English insights for each company, organized into "
        "Risk Signals and Opportunity Signals. Example: 'M&M.NS has a Debt-to-Equity ratio of 1.62, "
        "significantly above the sector median of 0.03 - indicating higher leverage risk.'"
    )
    pdf.add_screenshot(SCREENSHOTS["insights"], "Figure 7 - Insights Tab: Risk & Opportunity Signals")

    # --- Export ---
    pdf.sub_heading("3.8  Export - Download Reports")
    pdf.body_text(
        "Generate and download analysis results as multi-sheet Excel workbooks (.xlsx) or CSV files "
        "for import into other tools like Power BI or Tableau."
    )
    pdf.add_screenshot(SCREENSHOTS["export"], "Figure 8 - Export Tab: Download Options")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4 - HOW TO USE
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("4", "How to Use the System")

    pdf.body_text("Using the system requires just three steps:")
    pdf.ln(2)

    steps = [
        ("Step 1: Select Sector", "Choose from the sidebar dropdown (e.g., Automobile, IT, Banking, Pharma)"),
        ("Step 2: Run Analysis", "Click the 'Run Analysis' button. The system fetches data, computes ratios, "
         "and detects outliers automatically (takes 10-30 seconds)"),
        ("Step 3: Explore Tabs", "Navigate through Overview, Company, Ratios, Outliers, Health, and Insights"),
    ]
    for title, desc in steps:
        pdf.set_fill_color(20, 60, 80)
        pdf.set_draw_color(*pdf.ACCENT)
        y = pdf.get_y()
        pdf.rect(pdf.l_margin, y, 174, 14, "DF")
        pdf.set_xy(pdf.l_margin + 3, y + 1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*pdf.ACCENT)
        pdf.cell(0, 5, title)
        pdf.set_xy(pdf.l_margin + 3, y + 7)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*pdf.TEXT_WHITE)
        pdf.cell(0, 5, desc)
        pdf.set_y(y + 17)

    pdf.ln(5)
    pdf.sub_heading("Optional Customisation")
    pdf.bullet("IQR Multiplier - Controls IQR sensitivity (default: 1.5)")
    pdf.bullet("Z-Score Threshold - How far a value must deviate to be flagged (default: 2.5)")
    pdf.bullet("Isolation Forest % - Expected proportion of anomalies (default: 10%)")
    pdf.bullet("Ticker Override - Manually add or remove companies from the analysis")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5 - BUSINESS BENEFITS
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("5", "Key Business Benefits")
    pdf.add_table(
        ["Benefit", "Description"],
        [
            ["Time Savings", "Automates hours of data collection - analysis runs in under 30 seconds"],
            ["Consistency", "Same ratios and methods for every company - no human bias"],
            ["Coverage", "Analyses entire sectors at once (5-30+ companies)"],
            ["Early Detection", "Statistical methods catch anomalies missed by traditional screening"],
            ["Actionable Output", "Plain-English insights and exportable reports for decision-making"],
        ],
        [40, 134],
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6 - TECHNICAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    pdf.section_title("6", "Technical Summary")
    pdf.add_table(
        ["Component", "Technology"],
        [
            ["Data Source", "Yahoo Finance API (yfinance)"],
            ["Backend", "Python 3.13, Pandas, NumPy, SciPy"],
            ["ML Engine", "scikit-learn (Isolation Forest)"],
            ["Dashboard", "Streamlit (web-based, runs locally)"],
            ["Visualisations", "Plotly (interactive charts)"],
            ["Sectors Covered", "13 NSE sectors"],
            ["Ratios Computed", "30+ across 5 pillars"],
            ["Detection Methods", "3 (IQR, Z-Score, Isolation Forest)"],
        ],
        [50, 124],
    )

    pdf.ln(5)
    pdf.sub_heading("To Run")
    pdf.set_font("Courier", "", 11)
    pdf.set_text_color(*pdf.ACCENT)
    pdf.cell(0, 8, "  streamlit run app.py", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.TEXT_WHITE)
    pdf.body_text(
        "The dashboard opens in any web browser at http://localhost:8501. "
        "No installation beyond Python dependencies is required."
    )

    pdf.ln(8)
    pdf.info_box(
        "NOTE: This system uses publicly available data from Yahoo Finance. Always cross-reference "
        "critical findings with primary sources (NSE filings, annual reports) before making decisions."
    )

    # ══════════════════════════════════════════════════════════════════════
    # SAVE
    # ══════════════════════════════════════════════════════════════════════
    pdf.output(OUT_PATH)
    print(f"PDF saved to: {OUT_PATH}")
    print(f"  Pages: {pdf.pages_count}")
    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"  Size: {size_kb:.0f} KB")


if __name__ == "__main__":
    build_pdf()
