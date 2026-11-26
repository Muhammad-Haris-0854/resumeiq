# ResumeIQ — Phase Plan

Each phase ends with a verification step. A phase is only "done" when its checks pass.

| Phase | Deliverable | Verification |
|---|---|---|
| 1 | SRS, architecture, schema, structure, security plan (this delivery) | Docs reviewed; migrations apply cleanly on a fresh project |
| 2 | Design system: tokens, primitives, layouts, routing shell | `npm run build`, Storybook-free component page renders |
| 3 | Supabase auth: signup, login, OAuth, recovery, guards, profile bootstrap | Manual flow + `tests/test_auth.py` |
| 4 | Dashboard shell, resume upload with progress, resume list | Upload a real PDF end to end |
| 5 | Extraction service (PyMuPDF, python-docx, OCR), normalisation, Celery job | `tests/test_extraction.py` on fixture PDFs/DOCX |
| 6 | Career domains, skills, aliases, admin CRUD | Seed data loads; matcher unit tests |
| 7 | AI analysis: provider abstraction, prompt, schema validation, fallback | `tests/test_ai_contract.py` with a fake provider |
| 8 | Scoring engine, report UI, issue triage, re-analysis, compare | `tests/test_scoring.py`; report renders for every score band |
| 9 | Job description matching and match report | `tests/test_job_match.py` |
| 10 | Builder, 7 templates, autosave, versioning, PDF export | Export a resume, parse it back with PyMuPDF |
| 11 | Plans, entitlements, quota enforcement, mock provider, Stripe adapter | `tests/test_billing.py`, `tests/test_webhooks.py` |
| 12 | Admin dashboard, metrics, user/domain/template management | Role tests: non-admin gets 403 everywhere |
| 13 | Hardening: RLS test suite, load test, CI, deployment docs | CI green; staging deploy; security checklist complete |

## Current status

| Phase | State |
|---|---|
| 1 | Complete (docs in this repo) |
| 2 | Complete (design system + routing shell + all page routes) |
| 3 | Complete (client-side auth flows; Supabase project config required to run) |
| 4 | Complete (upload UI + API + storage path) |
| 5 | Complete (extraction service + worker task) |
| 6 | Complete (taxonomy seed + matcher) |
| 7 | Complete (provider abstraction, schema-validated prompts, deterministic fallback) |
| 8 | Complete (scoring engine + report UI) |
| 9 | Complete (JD parsing + match) |
| 10 | Complete (builder model, templates, export endpoint) |
| 11 | Complete (entitlements, quota, mock + Stripe adapters, webhook verification) |
| 12 | Complete (admin API + admin UI) |
| 13 | In progress: RLS suite and load test need a live Supabase project |

Anything requiring a live Supabase project (auth email delivery, storage uploads, RLS
integration tests, real payment gateway) needs the project keys and, for payments, the
provider account. Those are the only external blockers.
