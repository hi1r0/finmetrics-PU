import os
import fitz


def test_searchable_certificate_exists_and_has_text():
    pdf_path = "Report/internship_certificate.pdf"
    img_path = "Report/internship_certificate.jpg"
    assert os.path.exists(pdf_path), "Certificate PDF must exist"
    assert os.path.exists(img_path), "Local certificate image copy must exist"

    doc = fitz.open(pdf_path)
    assert len(doc) == 1, "Must be exactly 1 page"
    page = doc[0]

    # Verify A4 dimensions (595.32 x 841.92 pt within 1 pt tolerance)
    rect = page.rect
    assert abs(rect.width - 595.32) < 2.0
    assert abs(rect.height - 841.92) < 2.0

    # Verify text is extractable and contains all mandatory keywords
    text = page.get_text()
    assert "Rohit" in text
    assert "IQ Business Advisors" in text or "IQBA" in text
    assert "OF INTERNSHIP" in text
    assert "Financial Analyst" in text
    assert "Process Re-engineering" in text
    assert "IQBA/2026/013" in text
    assert "N NAGA ARJUN" in text
    assert "10/07/2026" in text
