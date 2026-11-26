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
