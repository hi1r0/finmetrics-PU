"""
pptx_design_tokens.py
=====================
Centralized design-token registry for the FinMetrics Suite PPTX export system.
All visual constants (colors, fonts, spacing, semantic mappings) live here so
that every slide, component, and chart draws from a single source of truth.

Preserves the Abyss Teal brand identity exactly as defined in the Streamlit
dashboard and visualization module.
"""

from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt, Emu

# ============================================================================
# SLIDE DIMENSIONS (16:9 Widescreen)
# ============================================================================
SLIDE_WIDTH = 13.333
SLIDE_HEIGHT = 7.5

# ============================================================================
# COLOR TOKENS -- Background Layer
# ============================================================================
COLOR_BG = RGBColor(0, 31, 30)            # #001F1E  Slide canvas
COLOR_CARD = RGBColor(0, 38, 35)          # #002623  Container cards
COLOR_SURFACE = RGBColor(13, 46, 43)      # #0D2E2B  Elevated surfaces
COLOR_BORDER = RGBColor(26, 58, 55)       # #1A3A37  Borders, dividers, gridlines

# ============================================================================
# COLOR TOKENS -- Accent Layer
# ============================================================================
COLOR_TEAL = RGBColor(0, 196, 167)        # #00C4A7  Primary accent
COLOR_TEAL_DIM = RGBColor(0, 95, 82)      # #005F52  Dimmed teal (bar tracks)
COLOR_SECONDARY = RGBColor(90, 138, 133)  # #5A8A85  Secondary accent

# ============================================================================
# COLOR TOKENS -- Text Layer
# ============================================================================
COLOR_WHITE = RGBColor(212, 240, 236)     # #D4F0EC  Primary text
COLOR_MUTED = RGBColor(122, 184, 178)     # #7AB8B2  Secondary text / labels
COLOR_DIM = RGBColor(61, 110, 105)        # #3D6E69  Captions, footnotes

# ============================================================================
# COLOR TOKENS -- Semantic Layer
# ============================================================================
COLOR_GREEN = RGBColor(46, 204, 113)      # #2ECC71  Positive / Strengths
COLOR_ORANGE = RGBColor(255, 159, 67)     # #FF9F43  Warning / Opportunities
COLOR_CORAL = RGBColor(255, 94, 87)       # #FF5E57  Negative / Weaknesses
COLOR_PURPLE = RGBColor(165, 94, 234)     # #A55EEA  Capital / Special
COLOR_YELLOW = RGBColor(210, 153, 34)     # #D29922  Caution / Neutral

# ============================================================================
# COLOR TOKENS -- Health Gradient (for gauges and progress bars)
# ============================================================================
HEALTH_GRADIENT = {
    "Distressed": RGBColor(255, 94, 87),   # #FF5E57
    "Weak":       RGBColor(255, 166, 87),  # #FFA657
    "Moderate":   RGBColor(210, 153, 34),  # #D29922
    "Strong":     RGBColor(90, 138, 133),  # #5A8A85
    "Excellent":  RGBColor(0, 196, 167),   # #00C4A7
}

# Category color mappings (matches visualization.py _CAT_COLORS)
CATEGORY_COLORS = {
    "Elite":      COLOR_TEAL,
    "Excellent":  COLOR_TEAL,
    "Strong":     COLOR_SECONDARY,
    "Healthy":    COLOR_MUTED,
    "Moderate":   COLOR_YELLOW,
    "Weak":       COLOR_ORANGE,
    "Critical":   COLOR_CORAL,
    "Distressed": COLOR_CORAL,
}

# ============================================================================
# TYPOGRAPHY TOKENS
# ============================================================================
FONT_PRIMARY = "Calibri"

# Font size hierarchy
FONT_H1 = Pt(28)          # Slide titles
FONT_H2 = Pt(16)          # Section headers / Card titles
FONT_H3 = Pt(11)          # KPI labels / Category headers
FONT_BODY = Pt(10.5)      # Narrative text / Descriptions
FONT_CAPTION = Pt(8.5)    # Footnotes / Methodology notes

# Special sizes
FONT_KPI_LARGE = Pt(48)   # Large KPI numbers
FONT_KPI_MEDIUM = Pt(32)  # Medium KPI numbers
FONT_TITLE_COVER = Pt(40) # Cover slide title
FONT_SUBTITLE = Pt(18)    # Cover slide subtitle
FONT_ACTION_NUMBER = Pt(28)  # Action plan numbering (01, 02, etc.)
FONT_TABLE_HEADER = Pt(9)    # Table column headers
FONT_TABLE_BODY = Pt(9)      # Table cell values

# ============================================================================
# LAYOUT TOKENS (Spacing Grid)
# ============================================================================
MARGIN_SLIDE = 0.6       # Outer margin from slide edges
MARGIN_CARD = 0.3        # Internal card padding
GAP_CARDS = 0.25         # Gap between adjacent cards
GAP_SECTIONS = 0.15      # Gap between header and content area
HEADER_HEIGHT = 1.0      # Reserved height for slide header block
CONTENT_TOP = 1.3        # Top of content area (below header)
FOOTER_TOP = 7.0         # Top of footer area
FOOTER_HEIGHT = 0.4      # Reserved height for footer

# Computed content area
CONTENT_WIDTH = SLIDE_WIDTH - 2 * MARGIN_SLIDE  # ~12.133"
CONTENT_HEIGHT = FOOTER_TOP - CONTENT_TOP        # ~5.7"

# Accent stripe thickness
STRIPE_HEIGHT = 0.06     # Top/bottom accent stripe
DIVIDER_HEIGHT = 0.015   # Section divider line
CARD_ACCENT_WIDTH = 0.06 # Left accent stripe on cards

# ============================================================================
# SWOT QUADRANT CONFIGURATION
# ============================================================================
SWOT_CONFIG = {
    "strengths": {
        "title": "STRENGTHS",
        "subtitle": "Internal Advantages",
        "color": COLOR_GREEN,
        "bg_tint": RGBColor(13, 46, 30),   # #0D2E1E
    },
    "weaknesses": {
        "title": "WEAKNESSES",
        "subtitle": "Internal Vulnerabilities",
        "color": COLOR_CORAL,
        "bg_tint": RGBColor(46, 32, 13),   # #2E200D
    },
    "opportunities": {
        "title": "OPPORTUNITIES",
        "subtitle": "External Potential",
        "color": COLOR_TEAL,
        "bg_tint": RGBColor(0, 38, 35),    # #002623
    },
    "threats": {
        "title": "THREATS",
        "subtitle": "External Risks",
        "color": COLOR_ORANGE,
        "bg_tint": RGBColor(46, 32, 13),   # #2E200D
    },
}

# ============================================================================
# ACTION PLAN CONFIGURATION
# ============================================================================
ACTION_PLAN_CONFIG = [
    {
        "number": "01",
        "title": "STRUCTURAL COST CONTROL",
        "subtitle": "Cost & Operations Specialist Lens",
        "color": COLOR_TEAL,
    },
    {
        "number": "02",
        "title": "WORKING CAPITAL & LIQUIDITY",
        "subtitle": "Liquidity Specialist Lens",
        "color": COLOR_ORANGE,
    },
    {
        "number": "03",
        "title": "SCALE & GROWTH ACTION",
        "subtitle": "Growth Advisor Lens",
        "color": COLOR_CORAL,
    },
    {
        "number": "04",
        "title": "CAPITAL ALLOCATION",
        "subtitle": "Value Specialist Lens",
        "color": COLOR_PURPLE,
    },
]

# ============================================================================
# PILLAR CONFIGURATION
# ============================================================================
PILLAR_CONFIG = [
    ("Profitability",  "profitability_score",  0.30),
    ("Solvency",       "solvency_score",       0.20),
    ("Liquidity",      "liquidity_score",       0.15),
    ("Efficiency",     "efficiency_score",      0.15),
    ("Growth",         "growth_score",          0.20),
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def health_color(score: float) -> RGBColor:
    """Return the appropriate color for a health/pillar score (0-100)."""
    if score >= 80:
        return HEALTH_GRADIENT["Excellent"]
    elif score >= 65:
        return HEALTH_GRADIENT["Strong"]
    elif score >= 50:
        return HEALTH_GRADIENT["Moderate"]
    elif score >= 35:
        return HEALTH_GRADIENT["Weak"]
    else:
        return HEALTH_GRADIENT["Distressed"]


def health_label(score: float) -> str:
    """Return the health label for a score (0-100)."""
    if score >= 80:
        return "EXCELLENT"
    elif score >= 65:
        return "STRONG"
    elif score >= 50:
        return "MODERATE"
    elif score >= 35:
        return "WEAK"
    else:
        return "DISTRESSED"


def category_color(category: str) -> RGBColor:
    """Return the color for a risk/health category string."""
    return CATEGORY_COLORS.get(category, COLOR_YELLOW)


def is_percentage_ratio(ratio_name: str) -> bool:
    """Check if a ratio should be displayed as a percentage."""
    pct_keywords = [
        "margin", "growth", "roe", "roa", "roce",
        "yield", "return", "payout",
    ]
    return any(kw in ratio_name.lower() for kw in pct_keywords)


def format_ratio_value(value: float, ratio_name: str) -> str:
    """Format a ratio value with appropriate suffix."""
    if is_percentage_ratio(ratio_name):
        return f"{value:.1f}%"
    return f"{value:.1f}x"
