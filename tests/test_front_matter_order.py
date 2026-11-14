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
