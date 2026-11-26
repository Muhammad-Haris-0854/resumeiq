# ADR-002 — FastAPI for the compute layer

**Status:** accepted · **Date:** 2026-11-26

## Context
Resume parsing, OCR, NLP and PDF rendering have mature Python libraries (PyMuPDF, python-docx,
spaCy, pytesseract, ReportLab). The scoring engine must be deterministic and unit-testable.

## Decision
A separate FastAPI service owns extraction, analysis, scoring and export. The SPA never parses
documents in the browser.

## Consequences
- Two languages in the repo, so shared types are maintained as JSON contracts documented in
  `docs/api.md` and mirrored in `frontend/src/types`.
- The API is stateless and scales horizontally behind a load balancer.
