import os
import re
import fitz

def test_flowchart_environment_and_labels():
    algo_path = "Report/chapters/algorithms.tex"
    assert os.path.exists(algo_path), "algorithms.tex must exist"
    with open(algo_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section and subsection titles
    assert "\\section{Algorithmic Workflow \\& Flowchart}" in content
    assert "\\subsection{Univariate Outlier Detection Process}" in content

    # Placement and figure environment
    assert "\\clearpage" in content
    assert "\\begin{figure}[t!]" in content
    assert "\\label{fig:outlier_flowchart}" in content
    assert "Univariate Outlier Detection and Baseline Masking Flowchart" in content

    # Colors
    assert "\\definecolor{peachbg}{RGB}{253, 238, 226}" in content
    assert "\\definecolor{lavenderbg}{RGB}{238, 240, 252}" in content
    assert "\\definecolor{greenbg}{RGB}{228, 248, 232}" in content
    assert "\\definecolor{boxborder}{RGB}{40, 45, 55}" in content

    # Node dimensions and styles
    assert "minimum width=5.2cm" in content
    assert "minimum height=1.1cm" in content
    assert "font=\\rmfamily\\small" in content

    # Flowchart nodes
    assert "Select Ratio Column" in content
    assert "Remove Missing Values" in content
    assert "Enough Data?" in content
    assert "Skip Column" in content
    assert "Calculate IQR" in content
    assert "Calculate Z-score" in content
    assert "Is it an Outlier?" in content
    assert "Mask Value" in content
    assert "Keep Value" in content

    # Pseudocode block must be removed
    assert "\\begin{algorithmic}" not in content
    assert "\\begin{algorithm}" not in content
    assert "\\Procedure{DetectOutliers}" not in content


def test_pdf_compilation_and_layout():
    log_path = "Report/main.log"
    pdf_path = "Report/main.pdf"

    assert os.path.exists(log_path), "main.log must exist"
    assert os.path.exists(pdf_path), "main.pdf must exist"

    # 1. Verify build log has zero fatal errors, zero undefined references, zero undefined citations
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_text = f.read()

    fatal_errors = re.findall(r"! LaTeX Error.*", log_text)
    undef_refs = re.findall(r"Reference `.*' undefined", log_text)
    undef_cits = re.findall(r"Citation `.*' undefined", log_text)

    assert len(fatal_errors) == 0, f"Found fatal errors in main.log: {fatal_errors}"
    assert len(undef_refs) == 0, f"Found undefined references in main.log: {undef_refs}"
    assert len(undef_cits) == 0, f"Found undefined citations in main.log: {undef_cits}"

    # 2. Verify PDF TOC and page content
    doc = fitz.open(pdf_path)
    assert len(doc) == 39, f"Expected 39 pages, got {len(doc)}"

    toc = doc.get_toc()
    matching_toc = [item for item in toc if "Algorithmic Workflow" in item[1] and "Flowchart" in item[1]]
    assert len(matching_toc) > 0, f"TOC entry for Algorithmic Workflow & Flowchart not found in {toc}"
    assert matching_toc[0][2] == 24, f"TOC entry should target Page 24, got {matching_toc[0][2]}"

    # 3. Verify Page 25 (0-indexed page 24) contents and geometry
    page25 = doc[24]
    page25_text = page25.get_text()
    assert "Figure 4.2: Univariate Outlier Detection and Baseline Masking Flowchart" in page25_text

    blocks = page25.get_text("blocks")
    header_block = [b for b in blocks if "Algorithms and Methodology" in b[4]]
    start_block = [b for b in blocks if "START" in b[4]]
    caption_block = [b for b in blocks if "Figure 4.2" in b[4]]

    assert len(header_block) > 0, "Running header missing on Page 25"
    assert len(start_block) > 0, "'START' node missing on Page 25"
    assert len(caption_block) > 0, "Caption missing on Page 25"

    header_bottom = header_block[0][3]
    start_top = start_block[0][1]
    assert start_top - header_bottom < 150, f"Flowchart top is too far from header: {start_top - header_bottom} pt"
    assert caption_block[0][1] > 600, f"Flowchart should extend towards bottom, caption at {caption_block[0][1]}"

    # Verify Chapter 5 begins on Page 26 (0-indexed 25)
    page26_text = doc[25].get_text()
    assert "Chapter 5" in page26_text

    # 4. Verify flowchart node labels in extracted text
    mandatory_terms = [
        "Select Ratio Column",
        "Calculate IQR",
        "Is it an Outlier?",
        "Mask Value",
        "Remove Missing Values",
        "Enough Data?",
        "Skip Column",
        "Calculate Z-score",
        "Keep Value",
    ]

    for term in mandatory_terms:
        assert term.lower() in page25_text.lower(), f"Term '{term}' missing from Page 25 text"

