from __future__ import annotations

import io

import pytest

from app.core.errors import Unprocessable
from app.services.extraction import extract_document
from app.utils.files import DOCX_MIME, PDF_MIME, validate_upload
from tests.conftest import RESUME_TEXT


def _pdf_bytes(text: str) -> bytes:
    import fitz

    document = fitz.open()
    page = document.new_page()
    page.insert_text((56, 72), text[:1500], fontsize=9)
    data = document.tobytes()
    document.close()
    return data


def _docx_bytes(text: str) -> bytes:
    import docx

    document = docx.Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_pdf_text_is_extracted():
    result = extract_document(_pdf_bytes(RESUME_TEXT), PDF_MIME)
    assert result.method == "pdf_text"
    assert "Muhammad Haris" in result.text
    assert result.page_count == 1


def test_docx_text_is_extracted():
    result = extract_document(_docx_bytes(RESUME_TEXT), DOCX_MIME)
    assert result.method == "docx"
    assert "React" in result.text


def test_corrupted_pdf_raises_actionable_error():
    with pytest.raises(Unprocessable) as exc:
        extract_document(b"%PDF-1.4 not really a pdf", PDF_MIME)
    assert exc.value.code in {"PDF_UNREADABLE", "NO_TEXT"}


def test_blank_pdf_is_rejected():
    import fitz

    document = fitz.open()
    document.new_page()
    data = document.tobytes()
    document.close()
    with pytest.raises(Unprocessable):
        extract_document(data, PDF_MIME, ocr_enabled=False)


def test_unsupported_mime_is_rejected():
    with pytest.raises(Unprocessable):
        extract_document(b"hello", "text/plain")


def test_upload_validation_accepts_pdf_and_rejects_renamed_file():
    pdf = _pdf_bytes(RESUME_TEXT)
    validated = validate_upload(pdf, "resume.pdf", 5 * 1024 * 1024)
    assert validated.mime_type == PDF_MIME
    with pytest.raises(Unprocessable):
        validate_upload(b"plain text pretending", "resume.pdf", 5 * 1024 * 1024)
    with pytest.raises(Unprocessable):
        validate_upload(pdf, "resume.docx", 5 * 1024 * 1024)


def test_upload_rejects_oversized_file():
    with pytest.raises(Unprocessable):
        validate_upload(b"%PDF-" + b"0" * 200, "big.pdf", 100)
