# ResumeIQ — API Reference (v1)

Base URL: `{VITE_API_BASE_URL}/v1`. All responses are JSON. All authenticated endpoints require
`Authorization: Bearer <supabase access token>`.

## Conventions

- **Auth**: the token is verified against Supabase's JWKS (ES256/RS256) with an optional HS256
  `SUPABASE_JWT_SECRET` fallback for legacy projects. `sub` is the user id. Roles come from
  `user_roles`, never from the token claims.
- **Errors**: `{ "error": { "code": "QUOTA_EXCEEDED", "message": "...", "details": {...}, "request_id": "..." } }`
- **Status codes**: 200 ok, 201 created, 202 accepted (queued), 204 no content, 400 validation,
  401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 422 domain rule, 429 rate limited,
  500 internal.
- **Pagination**: `?limit=20&offset=0`, response `{ items: [], total: n, limit, offset }`.
- **Idempotency**: mutating endpoints accept `Idempotency-Key`; repeats return the first result.

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | no | Liveness + version |
| GET | `/health/ready` | no | DB and Redis reachability |

## Resumes

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/resumes` | yes | multipart `file`, `title`, `career_domain_id` → 202, resume + version, enqueues extraction |
| GET | `/resumes` | yes | List own resumes (`status`, `limit`, `offset`) |
| GET | `/resumes/{id}` | yes | Resume with current version metadata |
| PATCH | `/resumes/{id}` | yes | Rename, change domain |
| DELETE | `/resumes/{id}` | yes | Delete resume, versions, storage objects |
| POST | `/resumes/{id}/versions` | yes | Upload a new version |
| GET | `/resumes/{id}/versions` | yes | Version history |
| GET | `/resumes/{id}/download` | yes | `{ url }` signed, 60 s TTL |
| GET | `/resumes/{id}/preview` | yes | Extracted text preview (first 8 000 chars) |
| POST | `/resumes/{id}/reprocess` | yes | Re-run extraction (e.g. after an OCR fix) |

## Analyses

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/analyses` | yes | `{ resume_version_id, career_domain_id, job_description_id? }` → 202; enforces quota |
| GET | `/analyses` | yes | Own analyses, newest first |
| GET | `/analyses/{id}` | yes | Full report: scores, issues, skills, summary |
| DELETE | `/analyses/{id}` | yes | Delete a report |
| POST | `/analyses/{id}/rerun` | yes | New analysis from the same version |
| GET | `/analyses/{id}/compare/{other_id}` | yes | Score deltas between two reports |
| PATCH | `/analyses/{id}/issues/{issue_id}` | yes | `{ status: accepted\|rejected\|edited, user_edit? }` |

## Career domains and taxonomy

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/domains` | yes | Active domains with skill counts |
| GET | `/domains/{slug}` | yes | Domain + skills grouped by requirement |
| GET | `/skills?q=` | yes | Skill search (canonical + aliases) |

## Job matching

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/job-matches` | yes | `{ resume_version_id, title?, company?, raw_text }` → 202 |
| GET | `/job-matches` | yes | History |
| GET | `/job-matches/{id}` | yes | Matched / partial / missing + score |

## Builder and templates

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/templates` | yes | Templates the caller's plan can use |
| POST | `/generated-resumes` | yes | Create from scratch or from a resume version |
| GET | `/generated-resumes` | yes | List |
| GET | `/generated-resumes/{id}` | yes | Content model |
| PUT | `/generated-resumes/{id}` | yes | Autosave (creates a version) |
| POST | `/generated-resumes/{id}/export` | yes | → 202, renders PDF, returns signed URL when ready |
| GET | `/generated-resumes/{id}/versions` | yes | Version history |
| POST | `/generated-resumes/{id}/versions/{version}/restore` | yes | Restore |

## Billing

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/billing/plans` | no | Public plan catalogue |
| GET | `/billing/subscription` | yes | Current subscription + entitlements + usage |
| POST | `/billing/checkout` | yes | `{ plan_code, interval }` → `{ checkout_url }` |
| POST | `/billing/portal` | yes | `{ return_url }` → `{ portal_url }` |
| POST | `/billing/cancel` | yes | Cancel at period end |
| POST | `/billing/resume` | yes | Undo cancellation |
| GET | `/billing/invoices` | yes | Payment history |
| POST | `/billing/webhook/{provider}` | no (signature) | Provider webhook; verified server-side |

## Account

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/me` | yes | Profile, role, entitlements, usage |
| PATCH | `/me` | yes | Name, headline, default domain |
| POST | `/me/export` | yes | GDPR data export (JSON, signed URL) |
| DELETE | `/me` | yes | Delete account and all documents |
| GET | `/me/notifications` | yes | In-app notifications |
| POST | `/me/notifications/{id}/read` | yes | Mark read |

## Admin (role: administrator)

| Method | Path | Description |
|---|---|---|
| GET | `/admin/metrics` | Users, paid/free, MRR, analyses, AI tokens, error rate |
| GET | `/admin/users` | Search, paginate, plan, role |
| PATCH | `/admin/users/{id}` | Set role, plan override, suspend |
| GET | `/admin/analyses` | All analyses with filters |
| GET/POST/PATCH/DELETE | `/admin/domains[/{id}]` | Domain CRUD |
| PUT | `/admin/domains/{id}/skills` | Replace domain skill set |
| GET/POST/PATCH/DELETE | `/admin/templates[/{id}]` | Template CRUD |
| GET/PATCH | `/admin/settings/scoring` | Read/update scoring weights |
| GET | `/admin/health` | Queue depth, worker heartbeat, failed jobs |

## Rate limits

| Scope | Limit |
|---|---|
| Authenticated general | 120 req / min / user |
| Upload | 10 / hour / user |
| Analysis creation | plan quota, plus 20 / hour burst |
| Webhooks | 300 / min / provider |
| Unauthenticated | 30 / min / IP |
