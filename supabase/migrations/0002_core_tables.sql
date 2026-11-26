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
