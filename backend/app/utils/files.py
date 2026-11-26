"""Upload validation. Client-declared MIME types are never trusted."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.core.errors import Unprocessable

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_FILENAME_LENGTH = 120
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class ValidatedUpload:
    data: bytes
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str

    @property
    def extension(self) -> str:
        return "pdf" if self.mime_type == PDF_MIME else "docx"


def sanitize_filename(name: str) -> str:
    base = (name or "resume").replace("\\", "/").split("/")[-1].strip()
    base = _SAFE.sub("_", base).strip("._") or "resume"
    return base[:MAX_FILENAME_LENGTH]


def validate_upload(data: bytes, filename: str, max_bytes: int) -> ValidatedUpload:
    if not data:
        raise Unprocessable("The uploaded file is empty", code="EMPTY_FILE")
    if len(data) > max_bytes:
        raise Unprocessable(
            f"File is larger than {max_bytes // (1024 * 1024)} MB",
            code="FILE_TOO_LARGE",
            details={"max_bytes": max_bytes},
        )

    lower = (filename or "").lower()
    if data.startswith(PDF_MAGIC):
        if not lower.endswith(".pdf"):
            raise Unprocessable("File content is PDF but the name is not .pdf", code="MIME_MISMATCH")
        mime = PDF_MIME
    elif data.startswith(ZIP_MAGIC):
        if not lower.endswith(".docx"):
            raise Unprocessable(
                "Only DOCX documents are supported, not legacy .doc or other archives",
                code="UNSUPPORTED_FORMAT",
            )
        mime = DOCX_MIME
    else:
        raise Unprocessable(
            "Unsupported file type. Upload a PDF or DOCX resume.",
            code="UNSUPPORTED_FORMAT",
        )

    return ValidatedUpload(
        data=data,
        filename=sanitize_filename(filename),
        mime_type=mime,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
