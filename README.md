# ResumeIQ

AI-assisted resume intelligence: upload a resume, pick a career domain, and get a scored,
evidence-backed report plus a rebuilt, ATS-safe PDF.

- **Frontend** — React 18 + TypeScript (strict) + Vite + Tailwind + shadcn-style primitives
- **Backend** — FastAPI (Python 3.11) for extraction, matching, scoring and PDF export
- **Data** — Supabase (Auth, PostgreSQL with RLS, private Storage)
- **Async** — Celery + Redis for extraction, AI analysis and exports
- **AI** — provider-agnostic, schema-validated, with a deterministic offline fallback

---

## Live preview

**https://muhammad-haris-0854.github.io/resumeiq/** (GitHub Pages, rebuilt on every push to `main`)

The preview is the real React app with Supabase auth wired from repository secrets, but it has no
FastAPI service behind it, so analysis calls return `API_NOT_CONFIGURED` and the UI shows a banner
saying so. Add the `VITE_API_BASE_URL` repository secret pointing at a deployed backend and the
same build becomes fully functional.

## What actually works

| Area | State |
|---|---|
| Auth (email, Google, recovery, verification) | Wired to Supabase Auth in the SPA |
| Resume upload, versioning, private storage, signed URLs | Implemented end to end (API + UI) |
| PDF/DOCX extraction + OCR fallback | Implemented, unit tested with generated fixtures |
| Section/skill normalisation | Implemented, tested |
| Domain taxonomy (16 domains, 94 skills, aliases) | Seeded, matched deterministically |
| 7-dimension scoring | Deterministic, unit tested, admin-configurable weights |
| AI review (issues, rewrites) | Schema-validated; deterministic provider by default |
| Job description matching | Implemented, tested |
| Builder, 7 templates, autosave, versions, PDF export | Implemented; export re-parsed in tests |
| Plans, entitlements, quota enforcement | Implemented and tested |
| Payments | Mock provider fully functional; Stripe adapter implemented (needs keys) |
| Admin dashboard | Metrics, users, roles, plans, scoring weights, health |
| RLS policies | Written for every table and bucket; **needs applying to your project** |

Verification performed in this repository:

```bash
cd backend  && ruff check app tests && pytest        # 78 tests, lint clean
cd frontend && npm run typecheck && npm run build    # strict TS, production build
python tools/validate_sql.py                         # every migration parses
```

Not verified here, because it needs live infrastructure: applying migrations to a Supabase
project, real auth email delivery, storage round-trips, a real AI provider, and a real payment
gateway. See [Deployment](docs/deployment.md).

---

## Quick start

### 1. Supabase

1. Create a project, then apply the schema:

```bash
supabase link --project-ref <your-ref>
supabase db push          # migrations in supabase/migrations
psql "$DATABASE_URL" -f supabase/seed.sql   # or paste seed.sql into the SQL editor
```

2. In **Authentication → Providers**, enable Email and Google. Add
   `http://localhost:5173/**` and your production origin to the redirect allow-list.
3. Copy the project URL, the **publishable** key, and the **service role** key.

### 2. Environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Fill in `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (server only), `VITE_SUPABASE_URL`,
`VITE_SUPABASE_PUBLISHABLE_KEY`. Leave `AI_PROVIDER_API_KEY` empty to run the deterministic
provider.

### 3. Run

```bash
docker compose up --build        # redis + api + worker + frontend
```

Or natively:

```bash
cd backend  && pip install -r requirements-dev.txt && uvicorn app.main:app --reload
cd backend  && celery -A app.workers.celery_app.celery_app worker -Q default,ai -l info
cd frontend && npm install && npm run dev
```

- App: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health/ready

### 4. Make yourself an administrator

```sql
update user_roles set role = 'administrator' where user_id = '<your-auth-user-id>';
```

Then reload the app; the **Admin** item appears in the sidebar. The API re-checks the role on
every admin request, so a client cannot grant itself anything.

### 5. Exercise the subscription flow (mock provider)

```bash
PAYMENT_WEBHOOK_SECRET=dev-webhook-secret \
python tools/mock_webhook.py --user <your-auth-user-id> --plan pro
```

The plan changes only after the signed webhook is applied. The mock checkout page explains
this and cannot fake a payment.

---

## Repository layout

```
backend/
  app/
    api/            routes + dependencies (auth, entitlements, providers)
    core/           config, JWT verification, errors, structured logging
    models/         domain enums and plan features
    repositories/   interfaces + Supabase implementations
    services/       extraction, normalisation, taxonomy, scoring, analysis,
                    job matching, builder, PDF, billing, entitlements, ai/
    integrations/   supabase client, payment providers
    workers/        Celery app and tasks
  tests/            78 tests: scoring, taxonomy, extraction, auth, API, billing, PDF
frontend/
  src/
    app/            router, providers, guards, layouts
    components/ui/  design-system primitives
    pages/          landing, auth, dashboard, upload, report, builder, admin…
    services/       typed API clients (no fetch in components)
    hooks/          auth, toast
    lib/            supabase client, API client, preview renderer, utils
supabase/
  migrations/       8 migrations: schema, RLS, storage, triggers
  seed.sql          plans, 16 domains, 94 skills, 7 templates
docs/               SRS, architecture, database, API, security, roadmap, ADRs
tools/              reference-data generator, SQL validator, mock webhook sender
```

---

## Design decisions worth knowing

- **Scores are computed in Python, not by the model.** The LLM returns observations and
  evidence; `services/scoring.py` converts them with bounded adjustments (±8 content,
  ±5 experience). Same resume, same score.
- **The API never trusts the client.** Identity comes from a verified Supabase JWT; plan and
  role come from the database. The service-role key stays server-side.
- **RLS is defence in depth.** Every table has policies, and every repository query is also
  scoped by `user_id`, because the API bypasses RLS by design.
- **AI output is schema-validated** (`jsonschema`) with one repair attempt, then a
  deterministic fallback. A provider outage degrades the report, it does not fail it.
- **Uploaded documents are data.** Text is delimited and the prompt states that instructions
  inside it must be ignored; parsing never executes document content.

More in [`docs/architecture.md`](docs/architecture.md), [`docs/database.md`](docs/database.md),
[`docs/api.md`](docs/api.md), [`docs/security.md`](docs/security.md) and
[`docs/decisions/`](docs/decisions).

---

## Scripts

| Where | Command | What it does |
|---|---|---|
| backend | `pytest` | Test suite |
| backend | `ruff check app tests` | Lint |
| frontend | `npm run dev` | Dev server |
| frontend | `npm run typecheck` | Strict TypeScript |
| frontend | `npm run build` | Production build |
| root | `python tools/build_catalog.py` | Regenerate `seed.sql` + the offline taxonomy |
| root | `python tools/validate_sql.py` | Parse all SQL with a Postgres grammar |
| root | `python tools/mock_webhook.py` | Send a signed mock payment event |

CI runs all of the above on every push (`.github/workflows/ci.yml`).

---

## Roadmap

Phase-by-phase status lives in [`docs/roadmap.md`](docs/roadmap.md). Remaining work is
integration against live infrastructure plus the hardening items in
[`docs/security.md`](docs/security.md#8-pre-production-checklist).

## License

Proprietary. All rights reserved.
