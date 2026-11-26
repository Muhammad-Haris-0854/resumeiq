# ResumeIQ — Security & Privacy

## 1. Threat model

| Asset | Threat | Control |
|---|---|---|
| Resume documents | Cross-tenant read | Private bucket, signed URLs, RLS, ownership checks |
| Account | Credential stuffing | Supabase auth limits, strong password policy, optional MFA |
| Session | Token theft | Short-lived access tokens, refresh rotation, no tokens in URLs |
| Billing | Forged subscription | Server-side webhook signature verification, no client trust |
| Admin | Privilege escalation | Roles in DB only, server-side `require_admin`, RLS `is_admin()` |
| Uploads | Malicious file | Magic-byte validation, size cap, no execution, sandboxed parsing |
| Prompt | Injection via resume text | Content delimited and labelled as data, output schema validated |
| API | Abuse | Per-user and per-IP rate limits, quota enforcement |

## 2. Authentication

- Supabase Auth issues JWTs. The API verifies the signature (JWKS, ES256), `exp`, `aud` and `iss`.
- `sub` identifies the user. Roles are read from `user_roles` per request (cached 60 s in Redis).
- The service-role key exists only in the backend and worker environments. It is never shipped
  to the browser, never logged, and never used in a client-side code path.
- The SPA stores the session with Supabase's default storage and refreshes silently; on 401 the
  API client attempts one refresh, then redirects to login.
- Account deletion revokes sessions before deleting rows.

## 3. Authorisation

Two independent layers:

1. **RLS** in Postgres — every user-owned table restricts to `auth.uid()`.
2. **API checks** — because the API uses the service role, every repository call is scoped by
   `user_id` taken from the verified token. A handler never accepts a `user_id` from the body.
3. **Entitlements** — `services/entitlements.py` maps plan → feature flags and quotas; every
   gated endpoint calls `require_entitlement(user, "jd_matching")` or `consume_quota(user, "analysis")`.

Admin routes additionally require `require_admin` which re-reads the role from the database.

## 4. Input handling

- Pydantic v2 models with `extra="forbid"` on all request bodies; length and pattern constraints.
- File upload: extension allow-list, MIME allow-list, 5 MB cap, magic bytes `%PDF-` / `PK\x03\x04`,
  SHA-256 recorded. Archives inside DOCX are read with `zipfile` guards against zip bombs.
- SQL: parameterised queries only, via the Supabase client and SQLAlchemy. No string-built SQL.
- XSS: React escapes by default; `dangerouslySetInnerHTML` is not used anywhere. User content
  rendered in PDFs is HTML-escaped by the renderer.
- CSRF: the API is token-authenticated and sets no cookies, so CSRF does not apply to `/v1`.
  Any future cookie-based session would require SameSite=Lax + double-submit token.
- CORS: explicit allow-list from `CORS_ORIGINS`; wildcard is rejected at startup in production.

## 5. AI-specific controls

- Resume text is wrapped in `<document>` tags and the system prompt states that anything inside
  is data, never instructions.
- Responses must match a JSON schema; a violation triggers one repair attempt, then the
  deterministic fallback. The analysis never stores unvalidated model output.
- The model cannot set scores. It returns observations with evidence; `scoring.py` converts them.
- `AI_PROVIDER_API_KEY` lives only in the backend environment.
- User documents are not used for training. Providers are called with `store=false` where the
  provider supports it, and no fine-tuning jobs are created.

## 6. Data protection

| Data | Retention | Notes |
|---|---|---|
| Resume files | Until deleted by user or account deletion | Private bucket |
| Extracted text | Same as file | Encrypted at rest by Supabase |
| Analyses | Same as resume | |
| Payment records | 7 years | Legal/tax requirement, no resume content |
| Audit logs | 24 months | Actor ids, no document content |
| AI request logs | 30 days | Token counts only, no document text |

- Transport: HTTPS/TLS 1.2+ enforced by the platform; HSTS at the CDN.
- At rest: Supabase Postgres and Storage encryption.
- Backups: daily automated, 7-day PITR on paid Supabase plans.
- Export: `POST /me/export` returns a JSON bundle with profile, resumes metadata, analyses.
- Deletion: `DELETE /me` removes storage objects first, then rows, then the auth user; the audit
  log keeps a tombstone without content.

## 7. Observability and response

- Structured JSON logs, `request_id` propagated from `X-Request-Id` or generated.
- Secrets and document text are redacted by a logging filter (`core/logging.py`).
- Failed auth, quota denials, admin mutations and webhook signature failures are audit-logged.
- Alerting thresholds: 5xx rate > 1 %, queue depth > 500, worker heartbeat missing > 2 min.

## 8. Pre-production checklist

- [ ] `.env` not committed; `.env.example` only placeholders.
- [ ] Service-role key absent from the frontend bundle (`npm run build` + grep).
- [ ] RLS enabled and tested per table (`tests/test_rls.py` against a staging project).
- [ ] CORS allow-list exact, no `*`.
- [ ] Webhook signature verified with the provider secret.
- [ ] Rate limits active in the gateway and in the app.
- [ ] Dependency audit clean (`pip-audit`, `npm audit`).
- [ ] Backups restored once in staging.
