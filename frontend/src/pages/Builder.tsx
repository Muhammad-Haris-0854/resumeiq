import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FilePlus2, FileText, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { EmptyState, ErrorState, PageHeader } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/field";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { builderApi } from "@/services/builder";
import { resumesApi } from "@/services/resumes";

export function BuilderPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [templateId, setTemplateId] = useState("");
  const [title, setTitle] = useState("My resume");
  const [versionId, setVersionId] = useState("");

  const templatesQuery = useQuery({ queryKey: ["templates"], queryFn: builderApi.templates });
  const listQuery = useQuery({ queryKey: ["generated-resumes"], queryFn: () => builderApi.list(20, 0) });
  const resumesQuery = useQuery({ queryKey: ["resumes", 0], queryFn: () => resumesApi.list(50, 0) });

  const create = useMutation({
    mutationFn: () =>
      builderApi.create({
        template_id: templateId,
        title,
        resume_version_id: versionId || undefined,
      }),
    onSuccess: async (resume) => {
      await queryClient.invalidateQueries({ queryKey: ["generated-resumes"] });
      navigate(`/builder/${resume.id}`);
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not create the resume", "error"),
  });

  const available = templatesQuery.data?.filter((template) => !template.locked) ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="Resume builder"
        title="Write or import, then export"
        description="Edits autosave with version history. Export produces an ATS-readable PDF."
      />

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <Card>
          <CardHeader><CardTitle>Start a resume</CardTitle></CardHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Name</Label>
              <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} />
            </div>
            <div>
              <Label htmlFor="template">Template</Label>
              <Select id="template" value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
                <option value="">Select a template</option>
                {available.map((template) => (
                  <option key={template.id} value={template.id}>{template.name}</option>
                ))}
              </Select>
              {available.length === 0 && !templatesQuery.isLoading && (
                <p className="mt-1 text-xs text-slate-500">No templates available on your plan yet.</p>
              )}
            </div>
            <div>
              <Label htmlFor="import">Import from an uploaded resume (optional)</Label>
              <Select id="import" value={versionId} onChange={(event) => setVersionId(event.target.value)}>
                <option value="">Start from scratch</option>
                {(resumesQuery.data?.items ?? []).map((resume) => (
                  <option key={resume.id} value={resume.current_version_id ?? ""}>
                    {resume.title}
                  </option>
                ))}
              </Select>
            </div>
            <Button
              onClick={() => create.mutate()}
              loading={create.isPending}
              disabled={!templateId || !title.trim()}
            >
              <FilePlus2 className="h-4 w-4" /> Create resume
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader><CardTitle>Your builder resumes</CardTitle></CardHeader>
          {listQuery.isLoading && (
            <p className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading…</p>
          )}
          {listQuery.isError && <ErrorState error={listQuery.error as Error} onRetry={() => void listQuery.refetch()} />}
          {listQuery.data?.items.length ? (
            <ul className="divide-y divide-line">
              {listQuery.data.items.map((resume) => (
                <li key={resume.id} className="flex items-center justify-between gap-3 py-3">
                  <button type="button" className="min-w-0 text-left" onClick={() => navigate(`/builder/${resume.id}`)}>
                    <p className="truncate text-sm font-medium text-ink hover:text-brand-600">{resume.title}</p>
                    <p className="text-xs text-slate-500">
                      v{resume.version} · edited {formatDateTime(resume.updated_at)}
                    </p>
                  </button>
                  <div className="flex items-center gap-2">
                    <Badge tone={resume.status === "ready" ? "success" : "info"}>{resume.status}</Badge>
                    <Button size="sm" variant="outline" onClick={() => navigate(`/builder/${resume.id}`)}>
                      <FileText className="h-3.5 w-3.5" /> Edit
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            !listQuery.isLoading && (
              <EmptyState
                icon={<FileText className="h-5 w-5" />}
                title="No builder resumes yet"
                description="Create one from a template, or import an uploaded resume to edit it."
              />
            )
          )}
          <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            <Trash2 className="h-3.5 w-3.5" /> Deleting a resume from the uploads page also removes its builder source.
          </p>
        </Card>
      </div>
    </div>
  );
}
