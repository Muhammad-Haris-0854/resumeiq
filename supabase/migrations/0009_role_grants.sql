-- 0009 — role grants
--
-- PostgREST connects as anon / authenticated / service_role, so the schema has to be reachable
-- by those roles. Supabase applies these grants by default to tables created in the SQL editor,
-- but not when a project is set up through the Management API or a fresh connection, which left
-- the API answering 42501 "permission denied" while the tables existed.
--
-- Row-level security remains the enforcement layer: these grants only make the tables visible to
-- the API roles, they do not bypass any policy.

grant usage on schema public to anon, authenticated, service_role;

grant all on all tables in schema public to anon, authenticated, service_role;
grant all on all sequences in schema public to anon, authenticated, service_role;
grant all on all functions in schema public to anon, authenticated, service_role;

-- Keep future tables reachable too, so a later migration cannot reintroduce the same outage.
alter default privileges in schema public
  grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public
  grant all on sequences to anon, authenticated, service_role;
alter default privileges in schema public
  grant all on functions to anon, authenticated, service_role;

-- Storage objects are accessed through the storage API, which runs as authenticated.
grant usage on schema storage to anon, authenticated, service_role;
grant all on storage.objects to anon, authenticated, service_role;
grant all on storage.buckets to anon, authenticated, service_role;
