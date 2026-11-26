import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ErrorState, PageHeader } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { accountApi } from "@/services/account";
import { catalogApi } from "@/services/catalog";

export function CareerPage() {
  const { me, refreshMe } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [selected, setSelected] = useState<string | null>(me?.profile.career_domain_id ?? null);

  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: catalogApi.domains });
  const selectedDomain = domainsQuery.data?.find((domain) => domain.id === selected);
  const detailQuery = useQuery({
    queryKey: ["domain", selectedDomain?.slug],
    queryFn: () => catalogApi.domain(selectedDomain!.slug),
    enabled: Boolean(selectedDomain),
  });

  const save = useMutation({
    mutationFn: (domainId: string) => accountApi.updateProfile({ career_domain_id: domainId, onboarding_completed: true }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      await refreshMe();
      toast.push("Career domain saved", "success");
      navigate("/resumes/upload");
    },
    onError: (error) => {
      toast.push(error instanceof ApiError ? error.message : "Could not save your domain", "error");
    },
  });

  return (
    <div>
      <PageHeader
        eyebrow="Step 1"
        title="Choose your career domain"
        description="The domain defines the skill taxonomy your resume is scored against. You can change it any time."
      />

      {domainsQuery.isLoading && (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading domains…
        </div>
      )}
      {domainsQuery.isError && (
        <ErrorState error={domainsQuery.error as Error} onRetry={() => void domainsQuery.refetch()} />
      )}

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <div className="grid gap-3 sm:grid-cols-2">
          {domainsQuery.data?.map((domain) => {
            const active = selected === domain.id;
            return (
              <button
                key={domain.id}
                type="button"
                onClick={() => setSelected(domain.id)}
                className={cn(
                  "rounded-2xl border p-4 text-left transition-all",
                  active
                    ? "border-brand-500 bg-brand-50/60 ring-2 ring-brand-500/30"
                    : "border-line bg-white hover:border-slate-300 hover:shadow-card",
                )}
                aria-pressed={active}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-ink">{domain.name}</p>
                  {active && <Check className="h-4 w-4 text-brand-600" />}
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{domain.description}</p>
                <p className="mt-2 text-xs font-medium text-slate-500">{domain.skill_count} tracked skills</p>
              </button>
            );
          })}
        </div>

        <div className="surface h-fit p-5">
          {selectedDomain ? (
            <>
              <p className="label">Taxonomy preview</p>
              <h2 className="mt-1 text-lg font-semibold">{selectedDomain.name}</h2>
              <p className="mt-1 text-sm text-slate-600">{selectedDomain.description}</p>

              {detailQuery.isLoading && <p className="mt-4 text-sm text-slate-500">Loading skills…</p>}
              {detailQuery.data && (
                <div className="mt-4 space-y-4">
                  {(["required", "preferred", "optional"] as const).map((level) => {
                    const skills = detailQuery.data.skills.filter((skill) => skill.requirement === level);
                    if (!skills.length) return null;
                    return (
                      <div key={level}>
                        <div className="flex items-center gap-2">
                          <Badge tone={level === "required" ? "danger" : level === "preferred" ? "warning" : "neutral"}>
                            {level}
                          </Badge>
                          <span className="text-xs text-slate-500">{skills.length} skills</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {skills.map((skill) => (
                            <span key={skill.id} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                              {skill.canonical_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <Button
                className="mt-5 w-full"
                loading={save.isPending}
                onClick={() => selected && save.mutate(selected)}
              >
                Use this domain <ArrowRight className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <p className="text-sm text-slate-600">Select a domain to see the skills it scores against.</p>
          )}
        </div>
      </div>
    </div>
  );
}
