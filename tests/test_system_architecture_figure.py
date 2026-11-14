import os
import re
import fitz

def test_system_architecture_figure_tex():
    tex_path = "Report/chapters/implementation.tex"
    assert os.path.exists(tex_path), f"{tex_path} must exist"
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Figure environment, label, and scaling
    assert "\\begin{figure}" in content
    assert "\\label{fig:seq_diagram}" in content
    assert re.search(r"\\resizebox\{\\textwidth\}\{!\}", content), "Figure must be wrapped in \\resizebox{\\textwidth}{!}"

    # 2. Color definitions
    expected_colors = ["uifill", "uiborder", "pipefill", "pipeborder", "linegray"]
    for color in expected_colors:
        assert f"\\definecolor{{{color}}}" in content, f"Missing \\definecolor{{{color}}}"

    # 3. Helper macro for uniform bottom pipeline cards
    assert "\\providecommand{\\pipebox}" in content or "\\pipebox" in content, "Missing \\pipebox helper macro"

    # 4. TikZ node and arrow styles
    expected_styles = [
        "topbox/.style",
        "uibox/.style",
        "pipe/.style",
        "flowtop/.style",
        "flowbot/.style",
        "toplbl/.style",
        "vertlbl/.style",
        "arr/.style",
    ]
    for style in expected_styles:
        assert style in content, f"Missing style {style} in tikzpicture options"

    # 5. Top row controller & perimeter views
    assert "Streamlit UI" in content
    assert "User Input" in content
    assert "Output View" in content
    assert "app.py" in content

    # 6. Bottom row: 5 uniform pipeline modules
    for module in ["DataFetcher", "FinancialParser", "RatioEngine", "OutlierEngine", "BenchmarkCore"]:
        assert module in content, f"Missing pipeline module {module}"
        assert f"\\pipebox{{{module}}}" in content, f"Module {module} must use \\pipebox"

    # 7. Split labels on bottom pipeline horizontal arrows
    assert re.search(r"node\[flowtop\]\s*\{Raw\}\s*node\[flowbot\]\s*\{DF\}", content), "Missing split label Raw / DF"
    assert re.search(r"node\[flowtop\]\s*\{Parsed\}\s*node\[flowbot\]\s*\{DF\}", content), "Missing split label Parsed / DF"
    assert re.search(r"node\[flowtop\]\s*\{30\+\}\s*node\[flowbot\]\s*\{Ratios\}", content), "Missing split label 30+ / Ratios"
    assert re.search(r"node\[flowtop\]\s*\{Outlier\}\s*node\[flowbot\]\s*\{Mask\}", content), "Missing split label Outlier / Mask"

    # 8. Orchestration arrows and labels
    assert r"Config \& Tickers" in content
    assert "1. Dispatches" in content
    assert "2. Delivers" in content
    assert "3. Renders Views" in content


def test_pdf_figure52_layout():
    log_path = "Report/main.log"
    pdf_path = "Report/main.pdf"

    assert os.path.exists(log_path), f"{log_path} must exist"
    assert os.path.exists(pdf_path), f"{pdf_path} must exist"

    # 1. Verify build log has 0 fatal errors, 0 undefined references, 0 undefined citations
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_text = f.read()

    fatal_errors = (
        re.findall(r"! LaTeX Error.*", log_text)
        + re.findall(r"! Emergency stop", log_text)
        + re.findall(r"Fatal error occurred", log_text)
    )
    undef_refs = (
        re.findall(r"Reference `.*' on page .* undefined", log_text)
        + re.findall(r"LaTeX Warning: There were undefined references", log_text)
    )
    undef_cits = (
        re.findall(r"Citation `.*' on page .* undefined", log_text)
        + re.findall(r"LaTeX Warning: There were undefined citations", log_text)
    )

    assert len(fatal_errors) == 0, f"Found fatal errors in main.log: {fatal_errors}"
    assert len(undef_refs) == 0, f"Found undefined references in main.log: {undef_refs}"
    assert len(undef_cits) == 0, f"Found undefined citations in main.log: {undef_cits}"

    # 2. Verify total page count of exactly 39 pages
    doc = fitz.open(pdf_path)
    assert len(doc) == 39, f"Expected exactly 39 pages, got {len(doc)}"

    # 3. Verify Figure 5.2 is cleanly located on Page 30 (0-indexed 29) below Section 5.3 text
    page30 = doc[29]
    page30_text = page30.get_text()
    assert "Figure 5.2" in page30_text, "Figure 5.2 must be located on Page 30 (0-indexed 29)"
    assert "Following completion of the analytical pipeline" in page30_text, (
        "Section 5.3 text must be on Page 30"
    )
    sec_idx = page30_text.find("Following completion of the analytical pipeline")
    fig_idx = page30_text.find("Figure 5.2")
    assert sec_idx < fig_idx, "Section 5.3 text must appear above Figure 5.2 on Page 30"

    # 4. Verify text elements from Figure 5.2 are cleanly extracted
    expected_elements = [
        "DataFetcher",
        "FinancialParser",
        "RatioEngine",
        "OutlierEngine",
        "BenchmarkCore",
        "Streamlit UI",
        "Raw",
        "DF",
        "Parsed",
        "30+",
        "Ratios",
        "Outlier",
        "Mask",
        "1. Dispatches",
        "2. Delivers",
        "3. Renders",
    ]
    for elem in expected_elements:
        assert elem in page30_text, f"Missing element '{elem}' in Page 30 text"

    # 5. Verify Chapter 6 begins cleanly on Page 31 (0-indexed 30)
    page31 = doc[30]
    page31_text = page31.get_text()
    assert "Chapter 6" in page31_text, "Chapter 6 must begin cleanly on Page 31 (0-indexed 30)"
