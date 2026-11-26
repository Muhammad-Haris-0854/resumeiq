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
