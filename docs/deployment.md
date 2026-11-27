# ResumeIQ — Deployment

## 1. Topology

| Component | Where | Notes |
|---|---|---|
| Frontend | Vercel / Netlify / Cloudflare Pages | Static build from `frontend/`, `VITE_*` at build time |
| API | Render / Fly.io / Railway / ECS | `backend/Dockerfile`, 2+ replicas, stateless |
| Worker | Same image, different command | `celery -A app.workers.celery_app.celery_app worker -Q default,ai,ai_priority` |
| Redis | Managed (Upstash, Elasticache, Render) | Broker + result backend |

### Cheapest working deployment (no Redis, one container)

For a demo or a single-tenant pilot you do not need Redis or a worker. Set
`CELERY_EAGER=true`: the API then runs extraction, analysis and export inline instead of
queueing them. Everything else stays the same.

1. Create a Render Web Service from this repo, runtime Docker, root directory `backend`.
2. Environment: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`,
   `AI_PROVIDER=google`, `AI_PROVIDER_API_KEY`, `CELERY_EAGER=true`,
   `ENVIRONMENT=production`, `CORS_ORIGINS=https://muhammad-haris-0854.github.io`.
3. Copy the service URL into the frontend's `VITE_API_BASE_URL` (repo secret for the Pages
   build) and redeploy the frontend.

Trade-off: a request now holds the connection for the whole analysis (roughly 5 to 15 seconds
with Gemini), so use a paid instance type or keep the prompt budget small. For real traffic,
switch `CELERY_EAGER` off and add the worker and Redis.

| Database / Auth / Storage | Supabase | Managed Postgres 15, RLS, private buckets |

## 2. Order of operations

1. **Supabase project** — create, then apply schema:
   ```bash
   supabase link --project-ref <ref>
   supabase db push
   psql "$DATABASE_URL" -f supabase/seed.sql
   ```
2. **Auth providers** — enable Email + Google; set the site URL and redirect allow-list to the
   frontend origin(s). Email templates: verification and recovery must point at `/login` and
   `/reset-password`.
3. **Storage** — migration `0007` creates `resumes`, `generated` and `template-previews` with
   policies. Verify the buckets exist and are private (except previews).
4. **API** — deploy `backend/Dockerfile` with the environment from `.env.example`. Set
   `ENVIRONMENT=production`, an explicit `CORS_ORIGINS`, and a real `PAYMENT_WEBHOOK_SECRET`.
   The app refuses to boot in production with a wildcard origin or missing Supabase keys.
5. **Worker** — deploy the same image with the Celery command and the same env. Scale
   `ai_priority` separately if Premium traffic grows.
6. **Frontend** — build with `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`,
   `VITE_API_BASE_URL`. Deploy `frontend/dist`.
7. **Payments** — either keep `PAYMENT_PROVIDER=mock` for a private beta, or set
   `PAYMENT_PROVIDER=stripe` with `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`. Register the
   webhook endpoint `https://api.<domain>/v1/billing/webhook/stripe` for
   `checkout.session.completed`, `invoice.payment_succeeded`, `invoice.payment_failed`,
   `customer.subscription.updated`, `customer.subscription.deleted`.
8. **Admin** — promote the first operator in SQL (`update user_roles set role='administrator' …`).

## 3. Environment checklist

- [ ] `SUPABASE_SERVICE_ROLE_KEY` present in API and worker only, never in the frontend build
- [ ] `SUPABASE_JWT_SECRET` set **only** if you verify legacy HS256 tokens; otherwise JWKS is used
- [ ] `CORS_ORIGINS` exact origins, no `*`
- [ ] `PAYMENT_WEBHOOK_SECRET` random, 32+ bytes, stored in the platform secret manager
- [ ] `AI_PROVIDER_API_KEY` server-side only; `AI_MODEL` pinned
- [ ] `REDIS_URL` with TLS if the provider requires it
- [ ] `OCR_ENABLED=true` and the image includes `tesseract-ocr` (it does)

## 4. Post-deploy verification

```bash
curl -s https://api.<domain>/health            # {"status":"ok",...}
curl -s https://api.<domain>/health/ready      # database + redis true
```

Then, in the app: sign up, upload a text-based PDF, confirm the report renders, confirm a
second user cannot open the first user's report id (expect 404), and confirm the free plan
blocks a third analysis with `QUOTA_EXCEEDED`.

## 5. Backups and retention

- Supabase daily backups plus PITR on paid plans; restore once into staging before launch.
- Documents are deleted with the resume or the account; audit logs keep tombstones only.
- Payment transactions are retained for accounting (see `docs/security.md`).

## 6. Scaling notes

- The API is stateless; add replicas behind the load balancer.
- Queue depth is exposed at `/v1/admin/health`; alert above 500.
- AI calls are capped by `AI_MAX_TOKENS` and run on the `ai` queue so uploads never queue
  behind them.
- Add a Redis-backed rate limiter (the in-process one is per replica) or enforce limits at the
  gateway.
