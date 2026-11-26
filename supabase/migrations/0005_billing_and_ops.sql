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
