import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutTemplate, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ErrorState, PageHeader } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { builderApi } from "@/services/builder";
import { catalogApi } from "@/services/catalog";

const swatches: Record<string, string> = {
  "ats-friendly": "from-slate-700 to-slate-900",
  "modern-professional": "from-brand-600 to-brand-800",
  "software-developer": "from-teal-600 to-teal-800",
  "fresh-graduate": "from-blue-500 to-blue-700",
  "experienced-professional": "from-slate-500 to-slate-700",
  "creative-designer": "from-pink-600 to-rose-700",
  minimalist: "from-slate-200 to-slate-400",
};

export function TemplatesPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const templatesQuery = useQuery({ queryKey: ["templates"], queryFn: catalogApi.templates });

  const create = useMutation({
    mutationFn: (templateId: string) => builderApi.create({ template_id: templateId, title: "Untitled resume" }),
    onSuccess: async (resume) => {
      await queryClient.invalidateQueries({ queryKey: ["generated-resumes"] });
      navigate(`/builder/${resume.id}`);
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not open the template", "error"),
  });

  return (
    <div>
      <PageHeader
        eyebrow="Templates"
        title="Pick a template to start from"
        description="All templates are single column with selectable text, so parsers read them correctly."
      />

      {templatesQuery.isError && <ErrorState error={templatesQuery.error as Error} onRetry={() => void templatesQuery.refetch()} />}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {templatesQuery.data?.map((template) => (
          <div key={template.id} className="surface flex flex-col overflow-hidden p-0">
            <div className={cn("relative h-36 bg-gradient-to-br p-4", swatches[template.slug] ?? "from-slate-400 to-slate-600")}>
              <div className="h-full rounded-lg bg-white/95 p-3">
                <div className="h-2 w-1/2 rounded bg-slate-800/80" />
                <div className="mt-1.5 h-1 w-1/3 rounded bg-slate-400" />
                <div className="mt-3 space-y-1">
                  <div className="h-1 w-full rounded bg-slate-200" />
                  <div className="h-1 w-11/12 rounded bg-slate-200" />
                  <div className="h-1 w-10/12 rounded bg-slate-200" />
                  <div className="mt-2 h-1 w-1/4 rounded bg-slate-300" />
                  <div className="h-1 w-full rounded bg-slate-200" />
                  <div className="h-1 w-9/12 rounded bg-slate-200" />
                </div>
              </div>
              {template.locked && (
                <span className="absolute right-3 top-3 rounded-full bg-navy-900/90 p-1.5 text-white">
                  <Lock className="h-3.5 w-3.5" />
                </span>
              )}
            </div>
            <div className="flex flex-1 flex-col p-4">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-ink">{template.name}</h3>
                <Badge tone={template.tier === "free" ? "neutral" : template.tier === "pro" ? "brand" : "warning"}>
                  {template.tier}
                </Badge>
              </div>
              <p className="mt-1 flex-1 text-xs leading-relaxed text-slate-600">{template.description}</p>
              <div className="mt-3 flex items-center gap-2">
                {template.is_ats_safe && <Badge tone="success">ATS safe</Badge>}
                <Button
                  size="sm"
                  className="ml-auto"
                  variant={template.locked ? "outline" : "primary"}
                  disabled={template.locked}
                  loading={create.isPending && create.variables === template.id}
                  onClick={() => create.mutate(template.id)}
                >
                  <LayoutTemplate className="h-3.5 w-3.5" />
                  {template.locked ? "Upgrade" : "Use template"}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
