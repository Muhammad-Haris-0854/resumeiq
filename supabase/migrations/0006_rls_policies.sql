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
