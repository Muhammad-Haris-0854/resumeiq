"""Vercel serverless entrypoint.

Vercel's Python runtime looks for a module-level ASGI callable in `api/`. The application code
lives one level up in `backend/app`, so the project root is added to the path before import.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402  (path setup must happen first)

__all__ = ["app"]
