# ResumeIQ — Database Design

PostgreSQL 15 on Supabase. All identifiers are `uuid` with `gen_random_uuid()` defaults.
Every table has `created_at timestamptz not null default now()` and
`updated_at timestamptz not null default now()` (maintained by the `touch_updated_at` trigger).

## 1. Entity relationships

```
auth.users (Supabase)
   └─1:1─ profiles ──1:N─ resumes ──1:N─ resume_versions ──1:N─ resume_analyses
                     │                        │                    └─1:N─ analysis_issues
                     │                        └─1:N─ generated_resumes
                     ├─1:N─ job_descriptions ──1:N─ job_matches
                     ├─1:1─ subscriptions ──N:1─ subscription_plans
                     ├─1:N─ usage_records
                     ├─1:N─ payment_transactions
                     └─1:N─ notifications
user_roles ──N:1─ auth.users
career_domains ──1:N─ domain_skills ──N:1─ skills
resume_templates
audit_logs
```

## 2. Tables

### profiles
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | = `auth.users.id` |
| email | citext unique | mirrored from auth |
| full_name | text | |
| headline | text | e.g. "Frontend Developer" |
| career_domain_id | uuid FK → career_domains | default domain |
| plan | plan_enum | `free/pro/premium`, denormalised cache of the subscription |
| onboarding_completed | boolean | |
| deleted_at | timestamptz | soft-delete marker for account deletion |

### user_roles
`id`, `user_id FK → auth.users unique`, `role role_enum ('user','administrator')`, `granted_by`,
`created_at`. Only service-role writes; users may read their own row.

### subscription_plans
`id`, `code unique ('free','pro','premium')`, `name`, `monthly_price_cents`, `annual_price_cents`,
`analysis_quota`, `max_resumes`, `features jsonb`, `is_active`.

### subscriptions
`id`, `user_id FK`, `plan_id FK`, `status ('active','past_due','canceled','trialing','incomplete')`,
`interval ('month','year')`, `provider ('mock','stripe')`, `provider_subscription_id`,
`current_period_start`, `current_period_end`, `cancel_at_period_end`, `canceled_at`.
Partial unique index: one non-terminal subscription per user.

### resumes
`id`, `user_id FK`, `title`, `career_domain_id FK`, `current_version_id FK → resume_versions`,
`status ('uploaded','extracting','extracted','failed','archived')`, `source ('upload','builder')`,
`deleted_at`.

### resume_versions
`id`, `resume_id FK on delete cascade`, `version int`, `storage_path`, `file_name`,
`mime_type`, `size_bytes`, `sha256`, `raw_text`, `extracted jsonb`, `page_count`,
`extraction_method ('pdf_text','docx','ocr')`, `created_by`.
Unique `(resume_id, version)`.

### resume_analyses
`id`, `user_id FK`, `resume_version_id FK`, `career_domain_id FK`, `job_description_id FK null`,
`status ('queued','running','ready','failed')`, `overall_score int`,
`scores jsonb` (the seven dimensions + inputs), `summary text`, `strengths jsonb`,
`weaknesses jsonb`, `detected_skills jsonb`, `missing_keywords jsonb`, `ai_model`,
`ai_tokens_used`, `error_code`, `duration_ms`, `completed_at`.

### analysis_issues
`id`, `analysis_id FK cascade`, `category ('keyword','skill','grammar','spelling','formatting','ats','content','section')`,
`severity ('low','medium','high')`, `title`, `detail`, `evidence text`, `suggestion text`,
`status ('open','accepted','rejected','edited')`, `user_edit text`, `skill_id FK null`.

### skills / career_domains / domain_skills
`skills`: `id`, `canonical_name unique`, `aliases text[]`, `kind ('technical','soft','tool','domain')`,
`category`.
`career_domains`: `id`, `slug unique`, `name`, `description`, `icon`, `is_active`.
`domain_skills`: `domain_id FK`, `skill_id FK`, `requirement ('required','preferred','optional')`,
`weight numeric`, PK `(domain_id, skill_id)`.

### job_descriptions
`id`, `user_id FK`, `title`, `company`, `raw_text`, `parsed jsonb`.

### job_matches
`id`, `user_id FK`, `resume_version_id FK`, `job_description_id FK`, `match_score int`,
`matched jsonb`, `partial jsonb`, `missing jsonb`, `recommendations jsonb`, `created_at`.

### resume_templates
`id`, `slug unique`, `name`, `description`, `preview_image_path`, `tier ('free','pro','premium')`,
`is_ats_safe boolean`, `layout jsonb`, `is_active`.

### generated_resumes
`id`, `user_id FK`, `resume_id FK null`, `template_id FK`, `title`, `content jsonb`,
`version int`, `pdf_storage_path`, `status`, unique `(resume_id, version)`.

### usage_records
`id`, `user_id FK`, `metric ('analysis','job_match','export','ai_rewrite')`, `quantity int`,
`period_start date`, `metadata jsonb`. Index `(user_id, metric, period_start)` — this is what
quota checks read.

### payment_transactions
`id`, `user_id FK`, `subscription_id FK null`, `provider`, `provider_transaction_id unique`,
`amount_cents`, `currency`, `status ('succeeded','failed','refunded','pending')`,
`invoice_url`, `raw_event jsonb`.

### notifications
`id`, `user_id FK`, `type`, `title`, `body`, `read_at`, `link`.

### audit_logs
`id`, `actor_id`, `action`, `target_type`, `target_id`, `metadata jsonb`, `ip`, `created_at`.
Append-only; admins read, nobody updates.

## 3. Indexes

```sql
create index on resumes (user_id, created_at desc) where deleted_at is null;
create index on resume_versions (resume_id, version desc);
create index on resume_analyses (user_id, created_at desc);
create index on resume_analyses (resume_version_id);
create index on analysis_issues (analysis_id, severity);
create index on usage_records (user_id, metric, period_start);
create index on job_matches (user_id, created_at desc);
create index on payment_transactions (user_id, created_at desc);
create index on domain_skills (domain_id);
create index on skills using gin (aliases);
```

## 4. Row Level Security

RLS is enabled on every table. The pattern is identical everywhere:

```sql
create policy "own rows" on <table>
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());
```

- `profiles`: `id = auth.uid()` for select/update; insert only via the `handle_new_user` trigger.
- `resume_versions`, `analysis_issues`: no direct `user_id`; policies use an `exists` join to the
  parent row, which is indexed.
- `career_domains`, `skills`, `domain_skills`, `resume_templates`: readable by any authenticated
  user when `is_active`; writable only by administrators (`is_admin()` helper).
- `subscriptions`, `payment_transactions`, `usage_records`: user reads own, writes only via
  service role (the API).
- `audit_logs`: no client access at all; service role only.

Helper:

```sql
create function is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from user_roles where user_id = auth.uid() and role = 'administrator');
$$;
```

Defence in depth: the FastAPI layer re-checks ownership and entitlements even though RLS also
enforces it, because the API uses the service-role key (which bypasses RLS) and therefore must
never rely on it.

## 5. Storage buckets

| Bucket | Public | Path convention | Policy |
|---|---|---|---|
| `resumes` | no | `{user_id}/{resume_id}/{version}.{ext}` | owner-only select/insert/delete |
| `generated` | no | `{user_id}/{generated_id}.pdf` | owner-only |
| `templates` | yes | `previews/{slug}.png` | public read, service-role write |

Uploads are validated server-side after download (magic bytes, size). Signed URLs expire in
60 seconds and are generated server-side only.

## 6. Migrations

`supabase/migrations/`:

1. `0001_extensions_and_enums.sql` — pgcrypto, citext, enum types, `touch_updated_at`.
2. `0002_core_tables.sql` — profiles, user_roles, plans, subscriptions.
3. `0003_resume_tables.sql` — resumes, versions, analyses, issues.
4. `0004_taxonomy_and_content.sql` — skills, domains, templates, generated resumes, JD matching.
5. `0005_billing_and_ops.sql` — usage, payments, notifications, audit.
6. `0006_rls_policies.sql` — enable RLS and all policies.
7. `0007_storage_buckets.sql` — buckets and storage policies.
8. `0008_functions_and_triggers.sql` — new-user trigger, quota helper, admin helpers.

Applied with `supabase db push`; the same SQL is idempotent enough to re-run on a fresh project.
`supabase/seed.sql` loads domains, taxonomy and templates (reference data, not fake user data).
