"""
pptx_components.py
==================
Reusable, parameterized shape-builder components for FinMetrics Suite
PPTX slides. Each function adds a composable visual element (card, KPI block,
progress bar, data table, etc.) to a slide using absolute-coordinate placement.

All components draw from the centralized design tokens in pptx_design_tokens.py.
"""

from typing import List, Optional, Tuple

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

from modules.pptx_design_tokens import (
    COLOR_BG, COLOR_CARD, COLOR_SURFACE, COLOR_BORDER,
    COLOR_TEAL, COLOR_TEAL_DIM, COLOR_SECONDARY,
    COLOR_WHITE, COLOR_MUTED, COLOR_DIM,
    COLOR_GREEN, COLOR_ORANGE, COLOR_CORAL, COLOR_PURPLE, COLOR_YELLOW,
    FONT_PRIMARY, FONT_H1, FONT_H2, FONT_H3, FONT_BODY, FONT_CAPTION,
    MARGIN_SLIDE, MARGIN_CARD, GAP_CARDS, STRIPE_HEIGHT, DIVIDER_HEIGHT,
    CARD_ACCENT_WIDTH, SLIDE_WIDTH, FOOTER_TOP,
    CONTENT_TOP, CONTENT_WIDTH,
)


# ============================================================================
# SLIDE-LEVEL COMPONENTS
# ============================================================================

def set_slide_bg(slide) -> None:
    """Set the solid dark Abyss Teal background on a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG


def add_slide_header(
    slide,
    title_text: str,
    subtitle_text: str = "",
) -> None:
    """
    Add a premium header block at the top of a slide.

    Structure:
      - Thin teal accent stripe (full width, top edge)
      - Title text in H1 style
      - Optional subtitle in muted text
      - Thin divider line below
    """
    # Top accent stripe
    stripe = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0), Inches(SLIDE_WIDTH), Inches(STRIPE_HEIGHT)
    )
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = COLOR_TEAL
    stripe.line.fill.background()

    # Title text
    tx_box = slide.shapes.add_textbox(
        Inches(MARGIN_SLIDE), Inches(0.3), Inches(CONTENT_WIDTH), Inches(0.5)
    )
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = FONT_PRIMARY
    p.font.size = FONT_H1
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL

    # Optional subtitle
    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = FONT_PRIMARY
        p_sub.font.size = FONT_BODY
        p_sub.font.color.rgb = COLOR_MUTED

    # Divider line
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(MARGIN_SLIDE), Inches(0.95), Inches(CONTENT_WIDTH), Inches(DIVIDER_HEIGHT)
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_BORDER
    divider.line.fill.background()


def add_slide_footer(slide, page_num: int, total_pages: int) -> None:
    """
    Add a footer with page number in bottom-right corner.
    """
    tx_box = slide.shapes.add_textbox(
        Inches(11.5), Inches(FOOTER_TOP), Inches(1.5), Inches(0.35)
    )
    tf = tx_box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = f"{page_num}  /  {total_pages}"
    p.alignment = PP_ALIGN.RIGHT
    p.font.name = FONT_PRIMARY
    p.font.size = FONT_CAPTION
    p.font.color.rgb = COLOR_DIM


# ============================================================================
# CARD COMPONENTS
# ============================================================================

def add_card(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    border_color: RGBColor = COLOR_BORDER,
    fill_color: RGBColor = None,
    accent_side: bool = False,
    accent_color: RGBColor = None,
) -> None:
    """
    Draw a rounded rectangular container card.

    Parameters
    ----------
    accent_side : bool
        If True, adds a thin colored stripe on the left edge.
    accent_color : RGBColor
        Color of the left accent stripe (defaults to border_color).
    """
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = fill_color or COLOR_CARD
    card.line.color.rgb = border_color
    card.line.width = Pt(1)

    # Accent stripes removed globally as requested by the user
    # if accent_side:
    #     ac = accent_color or border_color
    #     stripe = slide.shapes.add_shape(
    #         MSO_SHAPE.RECTANGLE,
    #         Inches(left), Inches(top), Inches(CARD_ACCENT_WIDTH), Inches(height)
    #     )
    #     stripe.fill.solid()
    #     stripe.fill.fore_color.rgb = ac
    #     stripe.line.fill.background()


# ============================================================================
# KPI COMPONENTS
# ============================================================================

def add_kpi_block(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    value: str,
    label: str,
    sublabel: str = "",
    value_color: RGBColor = COLOR_WHITE,
    value_size: Pt = None,
    label_color: RGBColor = COLOR_MUTED,
    alignment: int = PP_ALIGN.LEFT,
) -> None:
    """
    Add a large numeric KPI display with label and optional sublabel.
    """
    from modules.pptx_design_tokens import FONT_KPI_LARGE

    tx_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Label (above value)
    p_label = tf.paragraphs[0]
    p_label.text = label
    p_label.alignment = alignment
    p_label.font.name = FONT_PRIMARY
    p_label.font.size = FONT_H3
    p_label.font.bold = True
    p_label.font.color.rgb = label_color
    p_label.space_after = Pt(4)

    # Value
    p_value = tf.add_paragraph()
    p_value.text = value
    p_value.alignment = alignment
    p_value.font.name = FONT_PRIMARY
    p_value.font.size = value_size or FONT_KPI_LARGE
    p_value.font.bold = True
    p_value.font.color.rgb = value_color
    p_value.space_after = Pt(2)

    # Sublabel
    if sublabel:
        p_sub = tf.add_paragraph()
        p_sub.text = sublabel
        p_sub.alignment = alignment
        p_sub.font.name = FONT_PRIMARY
        p_sub.font.size = FONT_CAPTION
        p_sub.font.color.rgb = COLOR_DIM


def add_badge(
    slide,
    left: float,
    top: float,
    text: str,
    color: RGBColor,
    width: float = 1.5,
    height: float = 0.35,
) -> None:
    """
    Add a small status badge (pill shape) with text.
    """
    badge = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_SURFACE
    badge.line.color.rgb = color
    badge.line.width = Pt(1.5)

    tf = badge.text_frame
    tf.word_wrap = False
    tf.margin_left = Pt(6)
    tf.margin_right = Pt(6)
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)

    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = color


# ============================================================================
# PROGRESS BAR COMPONENT
# ============================================================================

def add_progress_bar(
    slide,
    left: float,
    top: float,
    width: float,
    height: float = 0.18,
    value: float = 50.0,
    max_value: float = 100.0,
    fill_color: RGBColor = COLOR_TEAL,
    track_color: RGBColor = None,
) -> None:
    """
    Draw a horizontal progress bar with filled portion and track.

    Parameters
    ----------
    value : float
        Current value (will be clamped to 0..max_value).
    max_value : float
        Maximum value for the bar.
    fill_color : RGBColor
        Color of the filled portion.
    track_color : RGBColor
        Color of the empty track (defaults to COLOR_TEAL_DIM).
    """
    track_c = track_color or COLOR_TEAL_DIM
    pct = max(0.0, min(value / max_value, 1.0))

    # Track (full width)
    track = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    track.fill.solid()
    track.fill.fore_color.rgb = track_c
    track.line.fill.background()

    # Filled portion
    fill_width = width * pct
    if fill_width > 0.05:  # Minimum visible width
        filled = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left), Inches(top), Inches(fill_width), Inches(height)
        )
        filled.fill.solid()
        filled.fill.fore_color.rgb = fill_color
        filled.line.fill.background()


# ============================================================================
# DATA TABLE COMPONENT
# ============================================================================

def add_data_table(
    slide,
    left: float,
    top: float,
    col_widths: List[float],
    headers: List[str],
    rows: List[List[str]],
    row_colors: Optional[List[List[RGBColor]]] = None,
    max_rows: int = 15,
) -> float:
    """
    Draw a formatted data table with header row and alternating row backgrounds.

    Parameters
    ----------
    col_widths : List[float]
        Width of each column in inches.
    headers : List[str]
        Column header labels.
    rows : List[List[str]]
        Data rows (list of lists of strings).
    row_colors : Optional[List[List[RGBColor]]]
        Optional per-cell color overrides. Same shape as rows.
    max_rows : int
        Maximum number of data rows to render.

    Returns
    -------
    float
        The Y-coordinate (in inches) just below the last row.
    """
    from modules.pptx_design_tokens import FONT_TABLE_HEADER, FONT_TABLE_BODY

    row_height = 0.28
    header_height = 0.32
    total_width = sum(col_widths)

    # Header background
    hdr_bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(total_width), Inches(header_height)
    )
    hdr_bg.fill.solid()
    hdr_bg.fill.fore_color.rgb = COLOR_SURFACE
    hdr_bg.line.fill.background()

    # Header text cells
    x_offset = left
    for i, header in enumerate(headers):
        tx = slide.shapes.add_textbox(
            Inches(x_offset), Inches(top), Inches(col_widths[i]), Inches(header_height)
        )
        tf = tx.text_frame
        tf.word_wrap = False
        tf.margin_left = Pt(6)
        tf.margin_right = Pt(4)
        tf.margin_top = Pt(4)
        tf.margin_bottom = Pt(2)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE

        p = tf.paragraphs[0]
        p.text = header
        p.font.name = FONT_PRIMARY
        p.font.size = FONT_TABLE_HEADER
        p.font.bold = True
        p.font.color.rgb = COLOR_TEAL
        x_offset += col_widths[i]

    # Data rows
    y = top + header_height
    display_rows = rows[:max_rows]
    for r_idx, row in enumerate(display_rows):
        # Alternating row background
        if r_idx % 2 == 1:
            row_bg = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(left), Inches(y), Inches(total_width), Inches(row_height)
            )
            row_bg.fill.solid()
            row_bg.fill.fore_color.rgb = RGBColor(0, 33, 31)  # Slightly lighter than BG
            row_bg.line.fill.background()

        x_offset = left
        for c_idx, cell_val in enumerate(row):
            tx = slide.shapes.add_textbox(
                Inches(x_offset), Inches(y), Inches(col_widths[c_idx]), Inches(row_height)
            )
            tf = tx.text_frame
            tf.word_wrap = False
            tf.margin_left = Pt(6)
            tf.margin_right = Pt(4)
            tf.margin_top = Pt(2)
            tf.margin_bottom = Pt(2)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE

            p = tf.paragraphs[0]
            p.text = cell_val
            p.font.name = FONT_PRIMARY
            p.font.size = FONT_TABLE_BODY
            p.font.bold = (c_idx == 0)  # Bold first column (ratio names)

            # Apply custom color or default
            if row_colors and r_idx < len(row_colors) and c_idx < len(row_colors[r_idx]):
                p.font.color.rgb = row_colors[r_idx][c_idx]
            else:
                p.font.color.rgb = COLOR_WHITE if c_idx == 0 else COLOR_MUTED

            x_offset += col_widths[c_idx]

        y += row_height

    # Bottom border line
    bottom_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(y), Inches(total_width), Inches(DIVIDER_HEIGHT)
    )
    bottom_line.fill.solid()
    bottom_line.fill.fore_color.rgb = COLOR_BORDER
    bottom_line.line.fill.background()

    return y


# ============================================================================
# BULLET LIST COMPONENT
# ============================================================================

def add_bullet_list(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    items: List[Tuple[str, str, RGBColor]],
    bullet_char: str = "--",
    font_size: Pt = None,
    space_after: Pt = None,
) -> None:
    """
    Add a styled bullet list with optional font size and spacing overrides.

    Parameters
    ----------
    items : List[Tuple[str, str, RGBColor]]
        Each tuple is (title_text, detail_text, title_color).
    """
    tx_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    f_size = font_size or FONT_BODY
    s_after = space_after or Pt(8)

    for i, (title, detail, color) in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        # Bullet + Title
        run_title = p.add_run()
        run_title.text = f"{bullet_char}  {title}"
        run_title.font.name = FONT_PRIMARY
        run_title.font.size = f_size
        run_title.font.bold = True
        run_title.font.color.rgb = color

        if detail:
            # Detail on same line
            run_detail = p.add_run()
            run_detail.text = f"  {detail}"
            run_detail.font.name = FONT_PRIMARY
            run_detail.font.size = f_size
            run_detail.font.bold = False
            run_detail.font.color.rgb = COLOR_MUTED

        p.space_after = s_after


# ============================================================================
# DIVIDER COMPONENT
# ============================================================================

def add_divider(
    slide,
    left: float,
    top: float,
    width: float,
    color: RGBColor = COLOR_BORDER,
) -> None:
    """Add a thin horizontal divider line."""
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(DIVIDER_HEIGHT)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()


# ============================================================================
# TEXT BLOCK COMPONENT
# ============================================================================

def add_text_block(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    font_size: Pt = None,
    font_color: RGBColor = COLOR_WHITE,
    bold: bool = False,
    italic: bool = False,
    alignment: int = PP_ALIGN.LEFT,
    line_spacing: float = 1.15,
) -> None:
    """Add a simple text block."""
    tx_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = text
    p.alignment = alignment
    p.font.name = FONT_PRIMARY
    p.font.size = font_size or FONT_BODY
    p.font.bold = bold
    p.font.italic = italic
    p.font.color.rgb = font_color
    p.line_spacing = line_spacing


def add_multiline_text(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    lines: List[Tuple[str, Pt, RGBColor, bool]],
    alignment: int = PP_ALIGN.LEFT,
) -> None:
    """
    Add a text block with multiple styled lines.

    Parameters
    ----------
    lines : List[Tuple[str, Pt, RGBColor, bool]]
        Each tuple is (text, font_size, color, is_bold).
    """
    tx_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    for i, (text, size, color, bold) in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.text = text
        p.alignment = alignment
        p.font.name = FONT_PRIMARY
        p.font.size = size
        p.font.bold = bold
        p.font.color.rgb = color
        p.space_after = Pt(4)
