-- ResumeIQ one-shot setup: schema, policies, storage and seed data.
-- Paste this whole file into the Supabase SQL editor and run it once on a fresh project.
-- Generated from supabase/migrations/*.sql + supabase/seed.sql by tools/build_setup_sql.sh.

-- =====================================================================
-- supabase/migrations/0001_extensions_and_enums.sql
-- =====================================================================
-- 0001 — extensions, enums, shared helpers
create extension if not exists pgcrypto;
create extension if not exists citext;

do $$ begin
  create type plan_code as enum ('free', 'pro', 'premium');
exception when duplicate_object then null; end $$;

do $$ begin
  create type user_role as enum ('user', 'administrator');
exception when duplicate_object then null; end $$;

do $$ begin
  create type subscription_status as enum ('trialing', 'active', 'past_due', 'canceled', 'incomplete');
exception when duplicate_object then null; end $$;

do $$ begin
  create type billing_interval as enum ('month', 'year');
exception when duplicate_object then null; end $$;

do $$ begin
  create type resume_status as enum ('uploaded', 'extracting', 'extracted', 'failed', 'archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type job_status as enum ('queued', 'running', 'ready', 'failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type requirement_level as enum ('required', 'preferred', 'optional');
exception when duplicate_object then null; end $$;

do $$ begin
  create type skill_kind as enum ('technical', 'soft', 'tool', 'domain');
exception when duplicate_object then null; end $$;

do $$ begin
  create type issue_severity as enum ('low', 'medium', 'high');
exception when duplicate_object then null; end $$;

do $$ begin
  create type issue_status as enum ('open', 'accepted', 'rejected', 'edited');
exception when duplicate_object then null; end $$;

do $$ begin
  create type template_tier as enum ('free', 'pro', 'premium');
exception when duplicate_object then null; end $$;

do $$ begin
  create type usage_metric as enum ('analysis', 'job_match', 'export', 'ai_rewrite');
exception when duplicate_object then null; end $$;

do $$ begin
  create type transaction_status as enum ('pending', 'succeeded', 'failed', 'refunded');
exception when duplicate_object then null; end $$;

create or replace function touch_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- Applies the updated_at trigger to a table by name.
create or replace function attach_updated_at(target regclass) returns void
language plpgsql as $$
begin
  execute format(
    'drop trigger if exists set_updated_at on %s;
     create trigger set_updated_at before update on %s
     for each row execute function touch_updated_at();',
    target, target
  );
end $$;

-- =====================================================================
-- supabase/migrations/0002_core_tables.sql
-- =====================================================================
-- 0002 — profiles, roles, plans, subscriptions

create table if not exists subscription_plans (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  description text,
  monthly_price_cents integer not null default 0 check (monthly_price_cents >= 0),
  annual_price_cents integer not null default 0 check (annual_price_cents >= 0),
  analysis_quota integer not null default 0 check (analysis_quota >= 0),
  max_resumes integer not null default 1 check (max_resumes >= 0),
  features jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
select attach_updated_at('subscription_plans');

create table if not exists career_domains (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9-]+$'),
  name text not null,
  description text,
  icon text,
  is_active boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
select attach_updated_at('career_domains');

create table if not exists profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email citext not null,
  full_name text,
  headline text,
  career_domain_id uuid references career_domains (id) on delete set null,
  plan plan_code not null default 'free',
  onboarding_completed boolean not null default false,
  last_seen_at timestamptz,
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists profiles_email_key on profiles (email);
create index if not exists profiles_plan_idx on profiles (plan);
select attach_updated_at('profiles');

create table if not exists user_roles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users (id) on delete cascade,
  role user_role not null default 'user',
  granted_by uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  plan_id uuid not null references subscription_plans (id),
  status subscription_status not null default 'incomplete',
  interval billing_interval not null default 'month',
  provider text not null default 'mock',
  provider_subscription_id text,
  provider_customer_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  canceled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists subscriptions_one_active_per_user
  on subscriptions (user_id) where status in ('active', 'trialing', 'past_due');
create index if not exists subscriptions_user_idx on subscriptions (user_id, created_at desc);
select attach_updated_at('subscriptions');

-- =====================================================================
-- supabase/migrations/0003_resume_tables.sql
-- =====================================================================
-- 0003 — resumes, versions, analyses, issues

create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  career_domain_id uuid references career_domains (id) on delete set null,
  current_version_id uuid,
  status resume_status not null default 'uploaded',
  source text not null default 'upload' check (source in ('upload', 'builder')),
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists resumes_user_idx on resumes (user_id, created_at desc) where deleted_at is null;
select attach_updated_at('resumes');

create table if not exists resume_versions (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid not null references resumes (id) on delete cascade,
  version integer not null check (version > 0),
  storage_path text not null,
  file_name text not null,
  mime_type text not null,
  size_bytes bigint not null check (size_bytes > 0),
  sha256 text,
  page_count integer,
  extraction_method text,
  raw_text text,
  extracted jsonb,
  created_by uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now(),
  unique (resume_id, version)
);
create index if not exists resume_versions_resume_idx on resume_versions (resume_id, version desc);

alter table resumes
  drop constraint if exists resumes_current_version_fk;
alter table resumes
  add constraint resumes_current_version_fk
  foreign key (current_version_id) references resume_versions (id) on delete set null;

create table if not exists job_descriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text,
  company text,
  raw_text text not null,
  parsed jsonb,
  created_at timestamptz not null default now()
);
create index if not exists job_descriptions_user_idx on job_descriptions (user_id, created_at desc);

create table if not exists resume_analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  resume_id uuid not null references resumes (id) on delete cascade,
  resume_version_id uuid not null references resume_versions (id) on delete cascade,
  career_domain_id uuid references career_domains (id) on delete set null,
  job_description_id uuid references job_descriptions (id) on delete set null,
  status job_status not null default 'queued',
  overall_score integer check (overall_score between 0 and 100),
  scores jsonb,
  summary text,
  strengths jsonb not null default '[]'::jsonb,
  weaknesses jsonb not null default '[]'::jsonb,
  detected_skills jsonb not null default '[]'::jsonb,
  missing_keywords jsonb not null default '[]'::jsonb,
  skill_breakdown jsonb not null default '[]'::jsonb,
  ai_model text,
  ai_tokens_used integer not null default 0,
  error_code text,
  error_message text,
  duration_ms integer,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists analyses_user_idx on resume_analyses (user_id, created_at desc);
create index if not exists analyses_version_idx on resume_analyses (resume_version_id);
select attach_updated_at('resume_analyses');

create table if not exists analysis_issues (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references resume_analyses (id) on delete cascade,
  category text not null,
  severity issue_severity not null default 'medium',
  title text not null,
  detail text,
  evidence text,
  suggestion text,
  status issue_status not null default 'open',
  user_edit text,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists issues_analysis_idx on analysis_issues (analysis_id, severity);
select attach_updated_at('analysis_issues');

create table if not exists job_matches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  resume_version_id uuid not null references resume_versions (id) on delete cascade,
  job_description_id uuid not null references job_descriptions (id) on delete cascade,
  status job_status not null default 'queued',
  match_score integer check (match_score between 0 and 100),
  matched jsonb not null default '[]'::jsonb,
  partial jsonb not null default '[]'::jsonb,
  missing jsonb not null default '[]'::jsonb,
  recommendations jsonb not null default '[]'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists job_matches_user_idx on job_matches (user_id, created_at desc);
select attach_updated_at('job_matches');

-- =====================================================================
-- supabase/migrations/0004_taxonomy_and_content.sql
-- =====================================================================
-- 0004 — skills taxonomy, templates, generated resumes

create table if not exists skills (
  id uuid primary key default gen_random_uuid(),
  canonical_name text not null unique,
  aliases text[] not null default '{}',
  kind skill_kind not null default 'technical',
  category text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists skills_aliases_idx on skills using gin (aliases);
create index if not exists skills_kind_idx on skills (kind);
select attach_updated_at('skills');

create table if not exists domain_skills (
  domain_id uuid not null references career_domains (id) on delete cascade,
  skill_id uuid not null references skills (id) on delete cascade,
  requirement requirement_level not null default 'required',
  weight numeric(4, 2) not null default 1.0 check (weight > 0 and weight <= 10),
  primary key (domain_id, skill_id)
);
create index if not exists domain_skills_domain_idx on domain_skills (domain_id);

create table if not exists resume_templates (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text,
  preview_image_path text,
  tier template_tier not null default 'free',
  is_ats_safe boolean not null default true,
  layout jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
select attach_updated_at('resume_templates');

create table if not exists generated_resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  resume_id uuid references resumes (id) on delete set null,
  template_id uuid not null references resume_templates (id),
  title text not null,
  content jsonb not null default '{}'::jsonb,
  version integer not null default 1 check (version > 0),
  pdf_storage_path text,
  status job_status not null default 'ready',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists generated_resumes_user_idx on generated_resumes (user_id, updated_at desc);
select attach_updated_at('generated_resumes');

create table if not exists generated_resume_versions (
  id uuid primary key default gen_random_uuid(),
  generated_resume_id uuid not null references generated_resumes (id) on delete cascade,
  version integer not null check (version > 0),
  content jsonb not null,
  created_at timestamptz not null default now(),
  unique (generated_resume_id, version)
);

create table if not exists app_settings (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);
select attach_updated_at('app_settings');

-- =====================================================================
-- supabase/migrations/0005_billing_and_ops.sql
-- =====================================================================
-- 0005 — usage metering, payments, notifications, audit

create table if not exists usage_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  metric usage_metric not null,
  quantity integer not null default 1 check (quantity > 0),
  period_start date not null default date_trunc('month', now())::date,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists usage_user_metric_period_idx on usage_records (user_id, metric, period_start);

create table if not exists payment_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  subscription_id uuid references subscriptions (id) on delete set null,
  provider text not null default 'mock',
  provider_transaction_id text not null unique,
  amount_cents integer not null default 0,
  currency text not null default 'usd',
  status transaction_status not null default 'pending',
  invoice_url text,
  description text,
  raw_event jsonb,
  created_at timestamptz not null default now()
);
create index if not exists payments_user_idx on payment_transactions (user_id, created_at desc);

create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  type text not null,
  title text not null,
  body text,
  link text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists notifications_user_idx on notifications (user_id, created_at desc);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid references auth.users (id) on delete set null,
  action text not null,
  target_type text,
  target_id text,
  metadata jsonb not null default '{}'::jsonb,
  ip text,
  created_at timestamptz not null default now()
);
create index if not exists audit_logs_created_idx on audit_logs (created_at desc);
create index if not exists audit_logs_actor_idx on audit_logs (actor_id, created_at desc);

-- =====================================================================
-- supabase/migrations/0006_rls_policies.sql
-- =====================================================================
-- 0006 — row level security

alter table profiles enable row level security;
alter table user_roles enable row level security;
alter table subscription_plans enable row level security;
alter table subscriptions enable row level security;
alter table career_domains enable row level security;
alter table skills enable row level security;
alter table domain_skills enable row level security;
alter table resumes enable row level security;
alter table resume_versions enable row level security;
alter table resume_analyses enable row level security;
alter table analysis_issues enable row level security;
alter table job_descriptions enable row level security;
alter table job_matches enable row level security;
alter table resume_templates enable row level security;
alter table generated_resumes enable row level security;
alter table generated_resume_versions enable row level security;
alter table usage_records enable row level security;
alter table payment_transactions enable row level security;
alter table notifications enable row level security;
alter table audit_logs enable row level security;
alter table app_settings enable row level security;

create or replace function is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from user_roles where user_id = auth.uid() and role = 'administrator'
  );
$$;

-- profiles
drop policy if exists profiles_select_own on profiles;
create policy profiles_select_own on profiles for select using (id = auth.uid() or is_admin());
drop policy if exists profiles_update_own on profiles;
create policy profiles_update_own on profiles for update using (id = auth.uid()) with check (id = auth.uid());

-- user_roles: read own, admins read all; writes only via service role
drop policy if exists user_roles_select_own on user_roles;
create policy user_roles_select_own on user_roles for select using (user_id = auth.uid() or is_admin());

-- catalogue tables: readable by authenticated users
drop policy if exists plans_read on subscription_plans;
create policy plans_read on subscription_plans for select using (is_active or is_admin());
drop policy if exists domains_read on career_domains;
create policy domains_read on career_domains for select using (is_active or is_admin());
drop policy if exists skills_read on skills;
create policy skills_read on skills for select using (auth.uid() is not null or is_admin());
drop policy if exists domain_skills_read on domain_skills;
create policy domain_skills_read on domain_skills for select using (auth.uid() is not null or is_admin());
drop policy if exists templates_read on resume_templates;
create policy templates_read on resume_templates for select using (is_active or is_admin());

-- own-row tables
drop policy if exists resumes_own on resumes;
create policy resumes_own on resumes for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists analyses_own on resume_analyses;
create policy analyses_own on resume_analyses for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists job_descriptions_own on job_descriptions;
create policy job_descriptions_own on job_descriptions for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists job_matches_own on job_matches;
create policy job_matches_own on job_matches for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists generated_resumes_own on generated_resumes;
create policy generated_resumes_own on generated_resumes for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists notifications_own on notifications;
create policy notifications_own on notifications for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- child tables: ownership via parent
drop policy if exists resume_versions_own on resume_versions;
create policy resume_versions_own on resume_versions for all
  using (exists (select 1 from resumes r where r.id = resume_versions.resume_id and r.user_id = auth.uid()))
  with check (exists (select 1 from resumes r where r.id = resume_versions.resume_id and r.user_id = auth.uid()));

drop policy if exists analysis_issues_own on analysis_issues;
create policy analysis_issues_own on analysis_issues for all
  using (exists (select 1 from resume_analyses a where a.id = analysis_issues.analysis_id and a.user_id = auth.uid()))
  with check (exists (select 1 from resume_analyses a where a.id = analysis_issues.analysis_id and a.user_id = auth.uid()));

drop policy if exists generated_resume_versions_own on generated_resume_versions;
create policy generated_resume_versions_own on generated_resume_versions for all
  using (exists (select 1 from generated_resumes g where g.id = generated_resume_versions.generated_resume_id and g.user_id = auth.uid()))
  with check (exists (select 1 from generated_resumes g where g.id = generated_resume_versions.generated_resume_id and g.user_id = auth.uid()));

-- read-only for the user, writes via service role
drop policy if exists subscriptions_read_own on subscriptions;
create policy subscriptions_read_own on subscriptions for select using (user_id = auth.uid() or is_admin());
drop policy if exists usage_read_own on usage_records;
create policy usage_read_own on usage_records for select using (user_id = auth.uid() or is_admin());
drop policy if exists payments_read_own on payment_transactions;
create policy payments_read_own on payment_transactions for select using (user_id = auth.uid() or is_admin());
drop policy if exists audit_admin_read on audit_logs;
create policy audit_admin_read on audit_logs for select using (is_admin());
drop policy if exists settings_admin_read on app_settings;
create policy settings_admin_read on app_settings for select using (is_admin());

-- =====================================================================
-- supabase/migrations/0007_storage_buckets.sql
-- =====================================================================
-- 0007 — private storage buckets and policies

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('resumes', 'resumes', false, 5242880,
    array['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']),
  ('generated', 'generated', false, 5242880, array['application/pdf']),
  ('template-previews', 'template-previews', true, 1048576, array['image/png', 'image/jpeg'])
on conflict (id) do nothing;

-- resumes: path is {user_id}/{resume_id}/{file}
drop policy if exists resumes_bucket_select on storage.objects;
create policy resumes_bucket_select on storage.objects for select
  using (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists resumes_bucket_insert on storage.objects;
create policy resumes_bucket_insert on storage.objects for insert
  with check (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists resumes_bucket_delete on storage.objects;
create policy resumes_bucket_delete on storage.objects for delete
  using (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

-- generated PDFs
drop policy if exists generated_bucket_select on storage.objects;
create policy generated_bucket_select on storage.objects for select
  using (bucket_id = 'generated' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists generated_bucket_delete on storage.objects;
create policy generated_bucket_delete on storage.objects for delete
  using (bucket_id = 'generated' and (storage.foldername(name))[1] = auth.uid()::text);

-- template previews are public read
drop policy if exists template_previews_read on storage.objects;
create policy template_previews_read on storage.objects for select
  using (bucket_id = 'template-previews');

-- =====================================================================
-- supabase/migrations/0008_functions_and_triggers.sql
-- =====================================================================
-- 0008 — bootstrap trigger and helper functions

create or replace function handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    coalesce(new.email, ''),
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name')
  )
  on conflict (id) do nothing;

  insert into public.user_roles (user_id, role)
  values (new.id, 'user')
  on conflict (user_id) do nothing;

  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- Monthly usage for the current period, used by the API quota check.
create or replace function usage_this_period(p_user_id uuid, p_metric usage_metric)
returns integer language sql stable as $$
  select coalesce(sum(quantity), 0)::int
  from usage_records
  where user_id = p_user_id
    and metric = p_metric
    and period_start = date_trunc('month', now())::date;
$$;

-- Effective plan for a user: active subscription, else free.
create or replace function effective_plan(p_user_id uuid) returns plan_code
language sql stable as $$
  select coalesce(
    (select p.code::plan_code
       from subscriptions s
       join subscription_plans p on p.id = s.plan_id
      where s.user_id = p_user_id
        and s.status in ('active', 'trialing')
        and (s.current_period_end is null or s.current_period_end > now())
      order by s.created_at desc
      limit 1),
    'free'::plan_code
  );
$$;

-- =====================================================================
-- supabase/seed.sql
-- =====================================================================
-- ResumeIQ seed: reference data only. No fake users or fake resumes.
-- Idempotent: safe to re-run with `supabase db reset` or `psql -f`.

-- Plans
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('free', 'Free', 'Try the core analysis on one or two resumes a month.', 0, 0, 2, 2, '{"jd_matching": false, "ai_rewrite": false, "version_compare": false, "templates": ["ats-friendly", "minimalist"], "priority_queue": false, "exports": 2}'::jsonb, 0)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('pro', 'Pro', 'For active job seekers who tailor a resume per application.', 1200, 11500, 20, 10, '{"jd_matching": true, "ai_rewrite": true, "version_compare": true, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate"], "priority_queue": false, "exports": 25}'::jsonb, 1)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('premium', 'Premium', 'For senior candidates and career changers running many searches.', 2900, 27900, 60, 30, '{"jd_matching": true, "ai_rewrite": true, "version_compare": true, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate", "experienced-professional", "creative-designer"], "priority_queue": true, "exports": 100}'::jsonb, 2)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;

-- Career domains
insert into career_domains (slug, name, description, icon, sort_order) values ('frontend-developer', 'Frontend Developer', 'Interfaces, component architecture and browser performance.', 'layout', 0)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('backend-developer', 'Backend Developer', 'APIs, data modelling, reliability and server-side logic.', 'server', 1)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('full-stack-developer', 'Full-Stack Developer', 'End-to-end product delivery across client and server.', 'layers', 2)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('react-developer', 'React.js Developer', 'Deep React expertise: state, rendering and component design.', 'atom', 3)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('python-developer', 'Python Developer', 'Python services, automation, data pipelines and scripting.', 'code', 4)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('java-developer', 'Java Developer', 'JVM services, enterprise integration and concurrency.', 'coffee', 5)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('software-engineer', 'Software Engineer', 'Generalist engineering: design, build, test, operate.', 'cpu', 6)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('ui-ux-designer', 'UI/UX Designer', 'Research, flows, interface design and design systems.', 'pen-tool', 7)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('graphic-designer', 'Graphic Designer', 'Visual identity, layout and brand communication.', 'palette', 8)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('data-analyst', 'Data Analyst', 'Turn data into decisions: SQL, dashboards and clear reporting.', 'bar-chart', 9)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('data-scientist', 'Data Scientist', 'Modelling, experimentation and production ML.', 'brain', 10)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('cybersecurity-engineer', 'Cybersecurity Engineer', 'Harden systems, test defences and respond to incidents.', 'shield', 11)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('devops-engineer', 'DevOps Engineer', 'Automate build, release and infrastructure with observability.', 'infinity', 12)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('digital-marketer', 'Digital Marketer', 'Acquisition, content and lifecycle marketing with measurable ROI.', 'megaphone', 13)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('business-analyst', 'Business Analyst', 'Translate business needs into testable requirements.', 'clipboard', 14)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('project-manager', 'Project Manager', 'Plan, coordinate and deliver across teams and constraints.', 'calendar', 15)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;

-- Skills
insert into skills (canonical_name, aliases, kind, category) values ('HTML5', array['HTML', 'HTML 5'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('CSS3', array['CSS', 'CSS 3'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('JavaScript', array['JS', 'ES6', 'ECMAScript', 'JavaScript ES6'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('TypeScript', array['TS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('React.js', array['React', 'ReactJS', 'React JS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Next.js', array['NextJS', 'Next JS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Vue.js', array['Vue', 'VueJS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Angular', array['AngularJS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Redux', array['Redux Toolkit', 'RTK'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Tailwind CSS', array['Tailwind', 'TailwindCSS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Responsive Design', array['Responsive Web Design', 'Mobile First Design'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Accessibility', array['a11y', 'WCAG'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('REST APIs', array['REST', 'RESTful APIs', 'REST API'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('GraphQL', array['Graph QL', 'Apollo'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Node.js', array['Node', 'NodeJS'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Express.js', array['Express', 'ExpressJS'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Python', array['Python 3'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('FastAPI', array['Fast API'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Django', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Flask', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Java', array['Java 8', 'Java 17'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Spring Boot', array['Spring'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('C#', array['CSharp', 'C Sharp'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('ASP.NET', array['ASP.NET Core', 'dotnet', '.NET'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PHP', array['PHP 8'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Laravel', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Go', array['Golang'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('SQL', array['Structured Query Language'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PostgreSQL', array['Postgres', 'psql'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('MySQL', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('MongoDB', array['Mongo'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Redis', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Database Design', array['Schema Design', 'Normalization', 'Data Modeling'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Pandas', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('NumPy', array['Numpy'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Scikit-learn', array['sklearn', 'Scikit Learn'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('TensorFlow', array['TF'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PyTorch', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Machine Learning', array['ML', 'Statistical Learning'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Data Visualization', array['Data Visualisation', 'Dashboards'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Statistics', array['Statistical Analysis', 'Probability'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Excel', array['Microsoft Excel', 'Advanced Excel'], 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Power BI', array['PowerBI'], 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Tableau', '{}', 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Git', array['Version Control'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('GitHub', array['Git Hub'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Docker', array['Containerization', 'Containers'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Kubernetes', array['K8s'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('CI/CD', array['Continuous Integration', 'Continuous Delivery', 'GitHub Actions', 'Jenkins'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Linux', array['Ubuntu', 'Unix', 'Bash', 'Shell Scripting'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('AWS', array['Amazon Web Services', 'EC2', 'S3', 'Lambda'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Azure', array['Microsoft Azure'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Google Cloud', array['GCP'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Terraform', array['Infrastructure as Code', 'IaC'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Nginx', '{}', 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Jest', array['Unit Testing', 'Vitest'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Pytest', array['PyTest'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Selenium', array['Playwright', 'Cypress', 'End-to-End Testing'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Figma', array['Figma Design'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adobe Photoshop', array['Photoshop'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adobe Illustrator', array['Illustrator'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Sketch', '{}', 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('User Research', array['UX Research', 'Usability Testing', 'Interviews'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Wireframing', array['Wireframes', 'Prototyping', 'Prototypes'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Design Systems', array['Component Library', 'UI Kit'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Typography', array['Type Hierarchy'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Brand Identity', array['Branding', 'Logo Design'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Penetration Testing', array['Pen Testing', 'Ethical Hacking', 'Pentesting'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Network Security', array['Firewalls', 'IDS', 'IPS'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('OWASP', array['OWASP Top 10', 'Web Application Security'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Cryptography', array['Encryption', 'TLS'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Incident Response', array['Forensics', 'SIEM'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('SEO', array['Search Engine Optimization', 'On-page SEO'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Google Analytics', array['GA4', 'Web Analytics'], 'tool'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Content Marketing', array['Copywriting', 'Content Strategy'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Email Marketing', array['Mailchimp', 'Campaigns'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Paid Advertising', array['Google Ads', 'Meta Ads', 'PPC'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Social Media Marketing', array['SMM', 'Social Media'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Market Research', array['Competitive Analysis'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Business Process Modeling', array['BPMN', 'Process Mapping'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Requirements Gathering', array['Elicitation', 'BRD', 'User Stories'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Stakeholder Management', array['Stakeholder Communication'], 'soft'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Agile', array['Scrum', 'Kanban', 'Sprint Planning'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Jira', array['Atlassian Jira'], 'tool'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Project Planning', array['Roadmapping', 'Gantt', 'Timeline Planning'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Risk Management', array['Risk Assessment'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Communication', array['Written Communication', 'Verbal Communication'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Teamwork', array['Collaboration', 'Cross-functional Collaboration'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Problem Solving', array['Analytical Thinking', 'Critical Thinking'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Leadership', array['Team Leadership', 'Mentoring'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Time Management', array['Prioritization', 'Deadline Management'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adaptability', array['Flexibility'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Attention to Detail', array['Detail Oriented'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Presentation Skills', array['Public Speaking', 'Demoing'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;

-- Domain skill mapping
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Responsive Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Redux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Tailwind CSS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Jest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Vue.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Node.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'FastAPI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Express.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'GraphQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Node.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Redux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Responsive Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Jest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Tailwind CSS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'GraphQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'FastAPI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Django'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Pytest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'NumPy'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Java'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Spring Boot'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Problem Solving'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'User Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Wireframing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Typography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Adobe Illustrator'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Sketch'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Illustrator'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Typography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Brand Identity'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Attention to Detail'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Social Media Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Statistics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Power BI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Tableau'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Machine Learning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Google Analytics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Statistics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Machine Learning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Scikit-learn'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'NumPy'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'TensorFlow'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'PyTorch'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Network Security'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'OWASP'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Penetration Testing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Cryptography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Incident Response'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Terraform'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Nginx'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Network Security'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Incident Response'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'SEO'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Google Analytics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Content Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Social Media Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Email Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Paid Advertising'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Requirements Gathering'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Business Process Modeling'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Stakeholder Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Jira'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Power BI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Project Planning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Project Planning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Stakeholder Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Risk Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Jira'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Time Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Leadership'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Business Process Modeling'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;

-- Templates
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('ats-friendly', 'ATS-Friendly', 'Single column, standard headings, no graphics. Maximum parser compatibility.', 'free'::template_tier, true, '{"columns": 1, "accent": "#1e293b", "font": "Inter", "show_photo": false, "section_order": ["summary", "skills", "experience", "education", "projects", "certifications"]}'::jsonb, 0)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('modern-professional', 'Modern Professional', 'Two-column header with a subtle accent rule. Balanced for corporate roles.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#4338ca", "font": "Inter", "show_photo": false, "section_order": ["summary", "experience", "skills", "education", "projects", "certifications"]}'::jsonb, 1)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('software-developer', 'Software Developer', 'Technical skills grid above experience, project-first for engineers.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#0f766e", "font": "JetBrains Mono", "show_photo": false, "section_order": ["summary", "skills", "projects", "experience", "education", "certifications"]}'::jsonb, 2)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('fresh-graduate', 'Fresh Graduate', 'Education and coursework lead, projects carry the weight.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#2563eb", "font": "Inter", "show_photo": false, "section_order": ["summary", "education", "projects", "skills", "experience", "achievements"]}'::jsonb, 3)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('experienced-professional', 'Experienced Professional', 'Achievement-dense experience section for 5+ years.', 'premium'::template_tier, true, '{"columns": 1, "accent": "#334155", "font": "Source Serif", "show_photo": false, "section_order": ["summary", "experience", "achievements", "skills", "education", "certifications"]}'::jsonb, 4)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('creative-designer', 'Creative Designer', 'Asymmetric header, strong type hierarchy, still single column body.', 'premium'::template_tier, false, '{"columns": 1, "accent": "#be185d", "font": "Playfair Display", "show_photo": true, "section_order": ["summary", "skills", "projects", "experience", "education", "achievements"]}'::jsonb, 5)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('minimalist', 'Minimalist', 'Quiet typography, generous whitespace, no rules or boxes.', 'free'::template_tier, true, '{"columns": 1, "accent": "#111827", "font": "Inter", "show_photo": false, "section_order": ["summary", "experience", "education", "skills", "projects"]}'::jsonb, 6)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;

-- Default scoring weights (admin-editable)
insert into app_settings (key, value)
values ('scoring_weights', '{"keyword_match": 20, "technical_skills": 20, "ats_compatibility": 15, "content_quality": 15, "grammar": 10, "formatting": 10, "experience_relevance": 10}'::jsonb)
on conflict (key) do nothing;

