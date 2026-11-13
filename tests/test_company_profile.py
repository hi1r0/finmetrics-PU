import os

def test_company_profile_section_content():
    intro_path = "Report/chapters/introduction.tex"
    assert os.path.exists(intro_path), "introduction.tex must exist"
    with open(intro_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section header
    assert "\\section{Host Organization Profile: IQ Business Advisors}" in content

    # Leadership and titles
    assert "Naga Arjun" in content
    assert "Rajesh Kannan" in content
    assert "Founders and Managing Partners" in content

    # Corporate facts
    assert "Kavundanpalayam" in content
    assert "Puducherry" in content
    assert "December 2024" in content
    assert "Financial Analyst and Process Re-engineering" in content
    assert "IQBA/2026/013" in content
    assert "FinMetrics Suite" in content

    # Exclusions
    assert "DRIVE SMART" not in content
    assert "Mission Statement" not in content
    assert "Dynamic Stock Audit" not in content
