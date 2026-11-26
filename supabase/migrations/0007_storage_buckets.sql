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
