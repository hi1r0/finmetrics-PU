import os
import re
import fitz

def test_front_matter_order_in_tex():
    tex_path = "Report/main.tex"
    assert os.path.exists(tex_path), "Report/main.tex must exist"
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    pos_cert = content.find("addcontentsline{toc}{chapter}{Certificate}")
    pos_intern = content.find("addcontentsline{toc}{chapter}{Internship Certificate}")
    pos_toc = content.find("addcontentsline{toc}{chapter}{Table of Contents}")
    pos_abbr = content.find("addcontentsline{toc}{chapter}{List of Abbreviations}")
    pos_abstract = content.find("addcontentsline{toc}{chapter}{Abstract}")
    pos_intro = content.find("\\include{chapters/introduction}")

    assert pos_cert != -1, "Certificate must be present"
    assert pos_intern != -1, "Internship Certificate must be present"
    assert pos_toc != -1, "Table of Contents must be present"
    assert pos_abbr != -1, "List of Abbreviations must be present"
    assert pos_abstract != -1, "Abstract must be present"
    assert pos_intro != -1, "Introduction chapter must be present"

    # Order requirement: TOC -> List of Abbreviations -> Abstract -> Chapter 1 Introduction
    assert pos_cert < pos_intern, "Certificate must precede Internship Certificate"
    assert pos_intern < pos_toc, "Internship Certificate must precede Table of Contents"
    assert pos_toc < pos_abbr, "Table of Contents must precede List of Abbreviations"
    assert pos_abbr < pos_abstract, "List of Abbreviations must precede Abstract"
    assert pos_abstract < pos_intro, "Abstract must precede Chapter 1 Introduction"


def test_front_matter_order_in_pdf():
    pdf_path = "Report/main.pdf"
    log_path = "Report/main.log"
    assert os.path.exists(pdf_path), "Report/main.pdf must exist"
    assert os.path.exists(log_path), "Report/main.log must exist"

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_text = f.read()

    fatal_errors = re.findall(r"^! LaTeX Error.*", log_text, re.MULTILINE)
    undef_refs = re.findall(r"Reference `.*' undefined", log_text)
    undef_cits = re.findall(r"Citation `.*' undefined", log_text)

    assert len(fatal_errors) == 0, f"Fatal errors in log: {fatal_errors}"
    assert len(undef_refs) == 0, f"Undefined references: {undef_refs}"
    assert len(undef_cits) == 0, f"Undefined citations: {undef_cits}"

    doc = fitz.open(pdf_path)
    assert len(doc) == 39, f"Expected 39 pages total, got {len(doc)}"

    toc = doc.get_toc()
    # Extract front-matter chapter titles
    titles = [item[1] for item in toc if item[0] == 1]
    
    idx_toc = next(i for i, t in enumerate(titles) if "Table of Contents" in t)
    idx_abbr = next(i for i, t in enumerate(titles) if "List of Abbreviations" in t)
    idx_abs = next(i for i, t in enumerate(titles) if "Abstract" in t)
    idx_intro = next(i for i, t in enumerate(titles) if "Introduction" in t)

    assert idx_toc < idx_abbr, f"TOC must precede Abbreviations: {titles}"
    assert idx_abbr < idx_abs, f"Abbreviations must precede Abstract: {titles}"
    assert idx_abs < idx_intro, f"Abstract must precede Introduction: {titles}"


def test_bottom_centered_page_numbers_and_appendix():
    pdf_path = "Report/main.pdf"
    assert os.path.exists(pdf_path), "Report/main.pdf must exist"

    doc = fitz.open(pdf_path)
    assert len(doc) == 39, f"Expected 39 pages total, got {len(doc)}"

    for i, page in enumerate(doc):
        if i == 0:
            continue  # Title page is unnumbered
        blocks = page.get_text("blocks")
        footer_blocks = [b for b in blocks if b[1] >= 735]
        header_blocks = [b for b in blocks if b[3] <= 45]

        # Verify running header contains no page numbers
        for b in header_blocks:
            words = b[4].strip().split()
            for w in words:
                assert not (w.isdigit() and len(w) <= 3), f"Header has page number on page {i+1}: {b[4]}"
                assert w.lower() not in ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"], f"Header has roman numeral on page {i+1}: {b[4]}"

        # Verify footer contains exactly one centered page number
        assert len(footer_blocks) == 1, f"Page {i+1} expected 1 footer block, got {len(footer_blocks)}: {footer_blocks}"
        b = footer_blocks[0]
        cx = (b[0] + b[2]) / 2.0
        assert abs(cx - 306.0) < 5.0, f"Page {i+1} page number not centered: cx={cx}, block={b}"

    # Appendix assertions
    # 1. Appendix page (Page 38, 0-indexed 37)
    p38_text = doc[37].get_text()
    assert "Appendix" in p38_text, "Page 38 must contain 'Appendix'"
    assert "Appendix A" not in p38_text, "Page 38 must not contain 'Appendix A'"
    assert "Core Source Code" in p38_text, "Page 38 must contain 'Core Source Code'"

    # 2. Table of Contents on Page 6 (0-indexed 5)
    p6_text = doc[5].get_text()
    assert "Appendix: Core Source Code" in p6_text, "TOC must list 'Appendix: Core Source Code'"
    assert "A Core Source Code" not in p6_text, "TOC must not list 'A Core Source Code'"

    # 3. Bookmarks
    toc = doc.get_toc()
    app_bookmarks = [b for b in toc if "appendix" in b[1].lower()]
    assert len(app_bookmarks) == 1, f"Expected 1 appendix bookmark, got {app_bookmarks}"
    assert app_bookmarks[0][1] == "Appendix: Core Source Code"
    assert app_bookmarks[0][2] == 38

