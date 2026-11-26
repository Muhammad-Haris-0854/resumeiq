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
