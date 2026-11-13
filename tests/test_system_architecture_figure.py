import os
import re
import fitz

def test_system_architecture_figure_tex():
    tex_path = "Report/chapters/implementation.tex"
    assert os.path.exists(tex_path), f"{tex_path} must exist"
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Figure environment and scaling
    assert "\\begin{figure}" in content
    assert "\\label{fig:seq_diagram}" in content
    assert "\\resizebox{\\textwidth}{!}" in content, "Figure must be wrapped in \\resizebox{\\textwidth}{!}"

    # 2. Local colors defined
    for color in ["peachbg", "peachborder", "lavenderbg", "lavenderborder", "boxborder", "darktext"]:
        assert f"\\definecolor{{{color}}}" in content, f"Missing \\definecolor{{{color}}}"

    # 3. Pill badge tag style and intermediate data tags
    assert "tag/.style" in content, "tag/.style must be defined in tikzpicture options"
    assert "fill=white" in content
    for badge in ["Raw DF", "Parsed DF", "30+ Ratios", "Outlier Mask"]:
        assert badge in content, f"Missing badge text: {badge}"
        assert re.search(rf"node\[[^\]]*tag[^\]]*\]\s*\{{{re.escape(badge)}\}}", content), f"Badge {badge} must use tag style"

    # 4. Top row nodes and non-colliding widths (controller <= 10.5cm)
    assert "User Input" in content
    assert "Streamlit UI" in content
    assert "Output View" in content
    match_width = re.search(r"orchestrator/\.style=\{[^}]*minimum width=([\d\.]+)cm", content)
    assert match_width, "orchestrator style must define minimum width"
    width = float(match_width.group(1))
    assert width <= 10.5, f"orchestrator minimum width must be <= 10.5cm (got {width}cm)"

    # 5. Removal of unpadded \rule cutting across engine text
    assert "\\rule{" not in content, "Unpadded \\rule cutting across engine text must be removed"

    # 6. Presence of closed loop orchestration steps
    assert "1. Dispatches" in content
    assert "2. Delivers" in content
    assert "3. Renders" in content


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

    # 3. Verify Figure 5.2 is cleanly located on Page 30 (0-indexed 29)
    page30 = doc[29]
    page30_text = page30.get_text()
    assert "Figure 5.2" in page30_text, "Figure 5.2 must be located on Page 30 (0-indexed 29)"

    # 4. Verify text elements from Figure 5.2 are cleanly extracted
    expected_elements = [
        "DataFetcher",
        "FinancialParser",
        "RatioEngine",
        "OutlierEngine",
        "BenchmarkCore",
        "Streamlit UI",
        "Raw DF",
        "Parsed DF",
        "30+ Ratios",
        "Outlier Mask",
    ]
    for elem in expected_elements:
        assert elem in page30_text, f"Missing element '{elem}' in Page 30 text"

    # 5. Verify Chapter 6 begins cleanly on Page 31 (0-indexed 30)
    page31 = doc[30]
    page31_text = page31.get_text()
    assert "Chapter 6" in page31_text, "Chapter 6 must begin cleanly on Page 31 (0-indexed 30)"

