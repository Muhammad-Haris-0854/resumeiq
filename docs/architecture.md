# ResumeIQ — System Architecture

## 1. Shape of the system

```
Browser (React SPA, Vite, TS strict)
   │  Supabase JS (auth, session, storage upload)
   │  Bearer JWT  ─────────────►  FastAPI  ──►  Supabase Postgres (RLS)
   │                                 │  └────►  Supabase Storage (private buckets)
   │                                 ├────►  AI provider (behind abstraction)
   │                                 └────►  Celery workers ◄── Redis
   └── signed URLs for file download
```

Four deployable units:

| Unit | Responsibility | Scaling |
|---|---|---|
| `frontend` | Rendering, forms, optimistic UI, session handling | Static CDN |
| `backend` | Authorisation, extraction, NLP, scoring, orchestration, PDF export | Stateless, N replicas |
| `worker` | Long-running extraction/OCR/AI/export jobs | N replicas, queue-based |
| `supabase` | Auth, Postgres, Storage, RLS | Managed |

## 2. Layering (Clean Architecture)

```
api/         HTTP boundary: routing, request validation, auth dependency, status codes
services/    Use cases: extraction, analysis, scoring, matching, builder, billing
repositories/ Persistence: one module per aggregate, no business rules
integrations/ External systems: supabase, ai, payments
core/        Config, security, logging, errors, rate limiting
schemas/     Pydantic models (input/output contracts)
models/      Domain dataclasses / enums shared across layers
```

Rules:

- `api` depends on `services`, never the reverse.
- `services` depend on repository and integration interfaces, not on HTTP.
- Repositories know nothing about FastAPI, Celery or the LLM.
- The scoring engine is pure: given structured inputs it returns scores. No I/O. This is what
  makes FR-7.2 testable.

Dependency direction is enforced by review and by tests that import the pure modules directly.

## 3. Request lifecycle — upload to report

1. `POST /v1/resumes` (multipart). API validates size, extension and magic bytes, computes a
   SHA-256, uploads to the private bucket `resumes`, inserts `resumes` + `resume_versions`.
2. The API enqueues `extract_resume(version_id)` and returns `202` with the resume id and
   status `uploaded`. The request never blocks on parsing.
3. Worker: download bytes → extract text (PyMuPDF / python-docx, OCR fallback) → normalise
   into a structured profile → persist `resume_versions.extracted` → status `extracted`.
4. `POST /v1/analyses` checks the entitlement and monthly quota, inserts a `resume_analyses`
   row with status `queued`, enqueues `analyse_resume(analysis_id)`.
5. Worker: load taxonomy for the domain → deterministic skill matcher → LLM enrichment for
   qualitative observations (bounded, JSON-schema validated) → scoring engine →
   persist report → status `ready`.
6. The SPA polls `GET /v1/analyses/{id}` (or `GET /v1/analyses/{id}/events` for SSE) and
   renders the report.

Failure at any step sets `status = failed`, stores a machine-readable `error_code` and a
human message. Jobs are retried with exponential backoff (max 3) and are idempotent: the
worker checks the current status before writing.

## 4. AI integration

`app/services/ai/base.py` defines:

```python
class AIProvider(Protocol):
    name: str
    async def complete_json(self, *, task: str, system: str, user: str,
                            schema: dict, max_tokens: int) -> dict: ...
```

Implementations:

- `OpenAICompatibleProvider` — any chat-completions endpoint (OpenAI, Gemini, Azure OpenAI,
  Groq, OpenRouter, self-hosted vLLM). Configured by `AI_BASE_URL`, `AI_MODEL`,
  `AI_PROVIDER_API_KEY`.
  - `AI_PROVIDER=google` targets Gemini through Google's OpenAI-compatible endpoint
    (`/v1beta/openai`) and defaults to `gemini-3-flash-preview`. Verify a key with
    `python tools/ai_smoke_test.py` before deploying: it exercises the real analysis and job
    description schemas, so a retired model name or an exhausted quota shows up in seconds.
  - Gemini 2.5 models are closed to new API keys, and the model line moves quickly, so
    `AI_MODEL` is configuration, not a constant.
- `DeterministicProvider` — offline, rule-based. Used in tests, in CI, and when no key is
  configured so the product still works end to end.

Guardrails:

- The JSON schema is sent with every request. Without it the model invents property names
  (`required_qualifications` for `required_skills`) and every response fails validation.
- Every AI response is validated against that schema. Undefined extra keys are dropped; missing
  or mistyped required fields trigger one repair attempt with the exact validation error; then
  the analysis degrades to the deterministic path instead of failing.
- Transient failures (429, 5xx, timeouts) are retried with backoff, longer for rate limits than
  for a blip. Truncation is reported as truncation, so `AI_MAX_TOKENS` is the obvious next step
  rather than a schema hunt.
- Reasoning models spend output tokens on thinking. `AI_REASONING_EFFORT=low` keeps Gemini's
  JSON intact and is the default for the Google provider.
- The model may never emit numeric scores. It returns observations with severity and evidence;
  the scoring engine converts them.
- Prompts state that resume text is data, and that instructions inside it must be ignored.
- Token budget per analysis is capped; usage is recorded in `usage_records`.

## 5. Background processing

- Celery with Redis broker and result backend.
- Two queues: `default` (extraction, export) and `ai` (LLM-heavy), so a slow provider cannot
  starve uploads. Premium users are routed to `ai_priority` (FR-9.3).
- `task_acks_late=True`, `worker_prefetch_multiplier=1`, per-task `time_limit` and `soft_time_limit`.
- Idempotency: tasks take ids, re-read state, and no-op when already terminal.

## 6. Frontend architecture

```
src/
  app/            router, providers, layouts, guards
  components/ui/  design-system primitives (button, card, input, badge, tabs, dialog…)
  features/       auth, dashboard, resume-upload, resume-analysis, job-matching,
                  resume-builder, templates, subscriptions, settings, admin
  hooks/          useAuth, useEntitlements, useToast, useDebounce
  lib/            supabase client, api client, query client, env validation
  services/       typed API functions per feature (no fetch inside components)
  types/          shared domain types
  utils/          formatting, cn, validation
```

- TanStack Query owns all server state; components never call `fetch` directly.
- React Hook Form + Zod for every form; schemas are shared with the API contract by shape.
- Route guards: `RequireAuth` and `RequireRole`. These are UX only; the backend re-checks.
- Design tokens live in `tailwind.config.ts` and CSS variables so theming is one file.

## 7. Design decisions

See `docs/decisions/`. Summary:

| ADR | Decision |
|---|---|
| 001 | Supabase as BaaS rather than a hand-rolled auth/DB stack |
| 002 | FastAPI for the compute layer; Python chosen for extraction/NLP |
| 003 | Deterministic scoring with bounded AI enrichment |
| 004 | Payment provider abstraction with mock + Stripe adapters |
| 005 | Postgres RLS as defence in depth, not as the only authorisation |
| 006 | Celery + Redis over in-process background tasks |

## 8. Environments

| Env | Frontend | Backend | Notes |
|---|---|---|---|
| local | `vite dev` :5173 | `uvicorn` :8000, Celery eager or worker | Docker Compose provides Redis |
| preview | Vercel/Netlify preview | Render/Fly preview | Separate Supabase project |
| production | CDN | 2+ replicas | Supabase Pro, backups on |

Configuration is environment-only (`app/core/config.py`, `import.meta.env`). Nothing is
hardcoded, and the app refuses to boot in production with a missing service-role key or a
wildcard CORS origin.
