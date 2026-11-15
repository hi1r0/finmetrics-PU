import os
import re
import fitz

def test_bibliography_bibtex_keys():
    bib_path = "Report/references.bib"
    assert os.path.exists(bib_path), "Report/references.bib must exist"
    with open(bib_path, "r", encoding="utf-8") as f:
        bib_content = f.read()

    expected_keys = [
        "tukey1977exploratory",
        "iglewicz1993how",
        "liu2008isolation",
        "altman1968financial",
        "damodaran2012investment",
        "yfinance",
        "gemini2023",
        "streamlit",
        "nseindia",
        "scikit-learn",
        "mckinney2012python",
    ]
    for key in expected_keys:
        assert f"{{{key}," in bib_content, f"Missing BibTeX key '{key}' in references.bib"


def test_bibliography_in_pdf():
    pdf_path = "Report/main.pdf"
    log_path = "Report/main.log"
    assert os.path.exists(pdf_path), "Report/main.pdf must exist"
    assert os.path.exists(log_path), "Report/main.log must exist"

    # Verify log has no undefined citations
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_text = f.read()
    undef_cits = re.findall(r"Citation `.*' undefined", log_text)
    assert len(undef_cits) == 0, f"Undefined citations found: {undef_cits}"

    # Verify Bibliography on Page 41 (0-indexed 40)
    doc = fitz.open(pdf_path)
    assert len(doc) == 43, f"Expected 43 pages, got {len(doc)}"
    page41_text = doc[40].get_text()
    assert "Bibliography" in page41_text, "Page 41 must contain the Bibliography"

    expected_authors_and_titles = [
        "Edward I. Altman",
        "Ran Aroussi",
        "yfinance",
        "Aswath Damodaran",
        "Gemini Team, Google DeepMind",
        "Boris Iglewicz and David C. Hoaglin",
        "Fei Tony Liu",
        "Wes McKinney",
        "National Stock Exchange of India",
        "Fabian Pedregosa",
        "Streamlit Inc.",
        "John W. Tukey",
    ]
    for item in expected_authors_and_titles:
        assert item in page41_text, f"Expected '{item}' in Page 41 Bibliography text"
