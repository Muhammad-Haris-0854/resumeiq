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
