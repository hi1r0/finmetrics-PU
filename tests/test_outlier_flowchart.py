import os

def test_flowchart_environment_and_labels():
    algo_path = "Report/chapters/algorithms.tex"
    assert os.path.exists(algo_path), "algorithms.tex must exist"
    with open(algo_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section and subsection titles
    assert "\\section{Algorithmic Workflow \\& Flowchart}" in content
    assert "\\subsection{Univariate Outlier Detection Process}" in content

    # Figure and label
    assert "\\begin{figure}" in content
    assert "\\label{fig:outlier_flowchart}" in content
    assert "Univariate Outlier Detection and Baseline Masking Flowchart" in content

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
