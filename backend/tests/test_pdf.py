from __future__ import annotations

import fitz

from app.services.builder import content_from_extracted, render_html
from app.services.normalizer import normalise
from app.services.pdf import render_pdf
from tests.conftest import RESUME_TEXT

TEMPLATE = {"layout": {"accent": "#4338ca", "font": "Inter"}}


def _content():
    content = content_from_extracted(normalise(RESUME_TEXT))
    content["full_name"] = "Muhammad Haris"
    return content


def test_pdf_contains_name_and_skills():
    pdf = render_pdf(_content(), TEMPLATE)
    assert pdf.startswith(b"%PDF")
    document = fitz.open(stream=pdf, filetype="pdf")
    text = "\n".join(page.get_text() for page in document)
    document.close()
    assert "Muhammad Haris" in text
    assert "React" in text
    assert "Experience" in text


def test_html_render_escapes_untrusted_content():
    content = _content()
    content["summary"] = "<script>alert('xss')</script>"
    html = render_html(content, TEMPLATE)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_pdf_export_has_no_blank_pages():
    pdf = render_pdf(_content(), TEMPLATE)
    document = fitz.open(stream=pdf, filetype="pdf")
    assert document.page_count >= 1
    assert document[0].get_text().strip()
    document.close()
