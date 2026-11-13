import os
import re

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
