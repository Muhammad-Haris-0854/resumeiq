"""Document text extraction.

PDF via PyMuPDF, DOCX via python-docx, OCR via Tesseract when a PDF carries no text layer.
Uploaded documents are untrusted input: they are read, never executed, and their content is
never interpreted as instructions.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from app.core.errors import Unprocessable
from app.core.logging import get_logger
from app.utils.files import DOCX_MIME, PDF_MIME
from app.utils.text import normalize_whitespace

logger = get_logger(__name__)

MIN_TEXT_CHARS = 80
OCR_DPI = 200


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    method: str
    page_count: int


def _extract_pdf_text(data: bytes) -> tuple[str, int]:
    import fitz  # PyMuPDF

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise Unprocessable("This PDF is corrupted or password protected", code="PDF_UNREADABLE") from exc

    try:
        if document.needs_pass:
            raise Unprocessable("Password protected PDFs are not supported", code="PDF_ENCRYPTED")
        pages = [page.get_text("text") for page in document]
        return "\n".join(pages), document.page_count
    finally:
        document.close()


def _ocr_pdf(data: bytes) -> tuple[str, int]:
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on host image
        raise Unprocessable(
            "This PDF has no text layer and OCR is unavailable on the server",
            code="OCR_UNAVAILABLE",
        ) from exc

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise Unprocessable("This PDF is corrupted", code="PDF_UNREADABLE") from exc

    try:
        chunks: list[str] = []
        zoom = OCR_DPI / 72
        matrix = fitz.Matrix(zoom, zoom)
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            chunks.append(pytesseract.image_to_string(image))
        return "\n".join(chunks), document.page_count
    except Exception as exc:
        raise Unprocessable(
            "We could not read the text from this PDF. Try exporting it again or uploading a DOCX.",
            code="OCR_FAILED",
        ) from exc
    finally:
        document.close()


def _extract_docx_text(data: bytes) -> tuple[str, int]:
    import docx

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise Unprocessable("This DOCX file could not be opened", code="DOCX_UNREADABLE") from exc

    parts: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts), max(1, len(parts) // 45 or 1)


def extract_document(data: bytes, mime_type: str, *, ocr_enabled: bool = True) -> ExtractionResult:
    if mime_type == PDF_MIME:
        text, pages = _extract_pdf_text(data)
        method = "pdf_text"
        if len(text.strip()) < MIN_TEXT_CHARS:
            if not ocr_enabled:
                raise Unprocessable(
                    "This PDF appears to be a scan and OCR is disabled",
                    code="OCR_DISABLED",
                )
            logger.info("ocr_fallback", extra={"extra_fields": {"pages": pages}})
            text, pages = _ocr_pdf(data)
            method = "ocr"
    elif mime_type == DOCX_MIME:
        text, pages = _extract_docx_text(data)
        method = "docx"
    else:
        raise Unprocessable("Unsupported document type", code="UNSUPPORTED_FORMAT")

    cleaned = normalize_whitespace(text)
    if len(cleaned) < 30:
        raise Unprocessable(
            "We could not find readable text in this document",
            code="NO_TEXT",
        )
    return ExtractionResult(text=cleaned, method=method, page_count=pages)
