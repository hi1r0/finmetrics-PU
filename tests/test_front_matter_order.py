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
    pos_lof = content.find("addcontentsline{toc}{chapter}{List of Figures}")
    pos_lot = content.find("addcontentsline{toc}{chapter}{List of Tables}")
    pos_abbr = content.find("addcontentsline{toc}{chapter}{List of Abbreviations}")
    pos_decl_ack = content.find("addcontentsline{toc}{chapter}{Declaration and Acknowledgements}")
    pos_abstract = content.find("addcontentsline{toc}{chapter}{Abstract}")
    pos_intro = content.find("\\include{chapters/introduction}")

    assert pos_cert != -1, "Certificate must be present"
    assert pos_intern != -1, "Internship Certificate must be present"
    assert pos_toc != -1, "Table of Contents must be present"
    assert pos_lof != -1, "List of Figures must be present"
    assert pos_lot != -1, "List of Tables must be present"
    assert pos_abbr != -1, "List of Abbreviations must be present"
    assert pos_decl_ack != -1, "Declaration and Acknowledgements must be present"
    assert pos_abstract != -1, "Abstract must be present"
    assert pos_intro != -1, "Introduction chapter must be present"

    # Order requirement: Certificate -> Internship Certificate -> TOC -> LOF -> LOT -> Abbreviations -> Decl & Ack -> Abstract -> Intro
    assert pos_cert < pos_intern, "Certificate must precede Internship Certificate"
    assert pos_intern < pos_toc, "Internship Certificate must precede Table of Contents"
    assert pos_toc < pos_lof, "Table of Contents must precede List of Figures"
    assert pos_lof < pos_lot, "List of Figures must precede List of Tables"
    assert pos_lot < pos_abbr, "List of Tables must precede List of Abbreviations"
    assert pos_abbr < pos_decl_ack, "List of Abbreviations must precede Declaration & Acknowledgements"
    assert pos_decl_ack < pos_abstract, "Declaration & Acknowledgements must precede Abstract"
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
    assert len(doc) == 43, f"Expected 43 pages total, got {len(doc)}"

    toc = doc.get_toc()
    # Extract front-matter chapter titles
    titles = [item[1] for item in toc if item[0] == 1]

    idx_toc = next(i for i, t in enumerate(titles) if "Table of Contents" in t)
    idx_lof = next(i for i, t in enumerate(titles) if "List of Figures" in t)
    idx_lot = next(i for i, t in enumerate(titles) if "List of Tables" in t)
    idx_abbr = next(i for i, t in enumerate(titles) if "List of Abbreviations" in t)
    idx_decl = next(i for i, t in enumerate(titles) if "Declaration and Acknowledgements" in t)
    idx_abs = next(i for i, t in enumerate(titles) if "Abstract" in t)
    idx_intro = next(i for i, t in enumerate(titles) if "Introduction" in t)

    assert idx_toc < idx_lof, f"TOC must precede List of Figures: {titles}"
    assert idx_lof < idx_lot, f"List of Figures must precede List of Tables: {titles}"
    assert idx_lot < idx_abbr, f"List of Tables must precede Abbreviations: {titles}"
    assert idx_abbr < idx_decl, f"Abbreviations must precede Declaration & Acknowledgements: {titles}"
    assert idx_decl < idx_abs, f"Declaration & Acknowledgements must precede Abstract: {titles}"
    assert idx_abs < idx_intro, f"Abstract must precede Introduction: {titles}"


def test_bottom_centered_page_numbers_and_appendix():
    pdf_path = "Report/main.pdf"
    assert os.path.exists(pdf_path), "Report/main.pdf must exist"

    doc = fitz.open(pdf_path)
    assert len(doc) == 43, f"Expected 43 pages total, got {len(doc)}"

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
                assert w.lower() not in ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"], f"Header has roman numeral on page {i+1}: {b[4]}"

        # Verify footer contains exactly one centered page number
        assert len(footer_blocks) == 1, f"Page {i+1} expected 1 footer block, got {len(footer_blocks)}: {footer_blocks}"
        b = footer_blocks[0]
        cx = (b[0] + b[2]) / 2.0
        assert abs(cx - 306.0) < 5.0, f"Page {i+1} page number not centered: cx={cx}, block={b}"

    # Appendix assertions
    # 1. Appendix page (Page 42, 0-indexed 41) and listing page (Page 43, 0-indexed 42)
    p42_text = doc[41].get_text()
    assert "Appendix" in p42_text, "Page 42 must contain 'Appendix'"
    assert "Appendix A" not in p42_text, "Page 42 must not contain 'Appendix A'"
    assert "Core Source Code" in p42_text, "Page 42 must contain 'Core Source Code'"
    assert "Outlier Filtering Logic" in p42_text, "Page 42 must contain 'Outlier Filtering Logic'"
    assert "A.1" not in p42_text, "Page 42 must not contain 'A.1'"

    p43_text = doc[42].get_text()
    assert "Listing: Univariate Outlier Detection Code" in p43_text, "Page 43 must contain 'Listing: Univariate Outlier Detection Code'"
    assert "Listing A.1" not in p43_text, "Page 43 must not contain 'Listing A.1'"

    # 2. Table of Contents contains Appendix: Core Source Code and Outlier Filtering Logic
    toc_text = ""
    for p_idx in [3, 4, 5]:  # Pages 4, 5, 6
        toc_text += doc[p_idx].get_text() + "\n"

    assert "Appendix: Core Source Code" in toc_text, "TOC must list 'Appendix: Core Source Code'"
    assert "A Core Source Code" not in toc_text, "TOC must not list 'A Core Source Code'"
    assert "Outlier Filtering Logic" in toc_text, "TOC must list 'Outlier Filtering Logic'"
    assert "A.1" not in toc_text, "TOC must not list 'A.1'"

    # 3. Bookmarks
    toc = doc.get_toc()
    app_bookmarks = [b for b in toc if "appendix" in b[1].lower()]
    assert len(app_bookmarks) == 1, f"Expected 1 appendix bookmark, got {app_bookmarks}"
    assert app_bookmarks[0][1] == "Appendix: Core Source Code"
    assert app_bookmarks[0][2] == 42

    sec_bookmarks = [b for b in toc if "outlier filtering logic" in b[1].lower()]
    assert len(sec_bookmarks) == 1, f"Expected 1 section bookmark, got {sec_bookmarks}"
    assert sec_bookmarks[0][1] == "Outlier Filtering Logic"
    assert sec_bookmarks[0][2] == 42



