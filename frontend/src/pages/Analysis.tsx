import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Check, Pencil, RefreshCw, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState, ErrorState, Loading, PageHeader, ScoreRing, SkillPill } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/field";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { formatDateTime, scoreTone, scoreToneClass } from "@/lib/utils";
import { analysesApi } from "@/services/analyses";

const severityTone = { high: "danger", medium: "warning", low: "neutral" } as const;

export function AnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { me } = useAuth();
  const [tab, setTab] = useState("issues");
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const analysisQuery = useQuery({
    queryKey: ["analysis", analysisId],
    queryFn: () => analysesApi.get(analysisId!),
    enabled: Boolean(analysisId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 2500 : false;
    },
  });

  const issueMutation = useMutation({
    mutationFn: ({ issueId, status, userEdit }: { issueId: string; status: "accepted" | "rejected" | "edited"; userEdit?: string }) =>
      analysesApi.updateIssue(analysisId!, issueId, status, userEdit),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analysis", analysisId] });
      setEditing(null);
      toast.push("Suggestion updated", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not update", "error"),
  });

  const rerunMutation = useMutation({
    mutationFn: () => analysesApi.rerun(analysisId!),
    onSuccess: async (analysis) => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      toast.push("New analysis queued", "success");
      window.location.href = `/analyses/${analysis.id}`;
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not rerun", "error"),
  });

  if (analysisQuery.isLoading) return <Loading label="Loading report" />;
  if (analysisQuery.isError) {
    return <ErrorState error={analysisQuery.error as Error} onRetry={() => void analysisQuery.refetch()} />;
  }

  const analysis = analysisQuery.data;
  if (!analysis) return null;

  if (analysis.status === "queued" || analysis.status === "running") {
    return (
      <div className="mx-auto max-w-xl py-16 text-center">
        <div className="surface p-8">
          <RefreshCw className="mx-auto h-6 w-6 animate-spin text-brand-600" />
          <h1 className="mt-4 text-xl font-semibold">Analysing your resume</h1>
          <p className="mt-2 text-sm text-slate-600">
            Extracting evidence, matching the domain taxonomy and computing your scores. This page refreshes itself.
          </p>
          <Progress value={45} className="mt-6" />
        </div>
      </div>
    );
  }

  if (analysis.status === "failed") {
    return (
      <div className="mx-auto max-w-xl py-16">
        <Alert tone="danger" title="Analysis failed">
          {analysis.error_message ?? "The analysis could not be completed."}
        </Alert>
        <Button className="mt-4" onClick={() => rerunMutation.mutate()} loading={rerunMutation.isPending}>
          Try again
        </Button>
      </div>
    );
  }

  const tone = scoreTone(analysis.overall_score ?? 0);
  const palette = scoreToneClass[tone];
  const openIssues = analysis.issues.filter((issue) => issue.status === "open");
  const accepted = analysis.issues.filter((issue) => issue.status === "accepted" || issue.status === "edited");

  return (
    <div>
      <div className="mb-4">
        <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-ink">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
        </Link>
      </div>

      <PageHeader
        eyebrow="Analysis report"
        title={`${analysis.overall_score}/100 overall`}
        description={`Generated ${formatDateTime(analysis.completed_at ?? analysis.created_at)}${analysis.ai_model ? ` · reviewed by ${analysis.ai_model}` : ""}`}
        actions={
          <>
            <Button variant="outline" onClick={() => rerunMutation.mutate()} loading={rerunMutation.isPending}>
              <RefreshCw className="h-4 w-4" /> Re-analyse
            </Button>
            <Link to="/builder">
              <Button><Sparkles className="h-4 w-4" /> Build improved resume</Button>
            </Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        <div className="space-y-4">
          <Card className="text-center">
            <div className="flex justify-center">
              <ScoreRing score={analysis.overall_score ?? 0} size={148} />
            </div>
            <p className={`mt-3 text-sm font-semibold capitalize ${palette.text}`}>{tone.replace("-", " ")}</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{analysis.summary}</p>
          </Card>

          <Card>
            <CardHeader><CardTitle>Score breakdown</CardTitle></CardHeader>
            <div className="space-y-3">
              {analysis.scores.map((score) => (
                <div key={score.key}>
                  <div className="flex items-center justify-between text-xs font-medium text-slate-600">
                    <span>{score.label}</span>
                    <span className="font-mono">{score.score} · {score.weight}%</span>
                  </div>
                  <Progress
                    value={score.score}
                    className="mt-1"
                    tone={score.score >= 85 ? "success" : score.score >= 60 ? "brand" : score.score >= 40 ? "warning" : "danger"}
                  />
                  <p className="mt-1 text-[0.7rem] leading-relaxed text-slate-500">{score.explanation}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader><CardTitle>At a glance</CardTitle></CardHeader>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Skills detected</dt><dd className="font-medium">{analysis.detected_skills.length}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Missing keywords</dt><dd className="font-medium">{analysis.missing_keywords.length}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Open issues</dt><dd className="font-medium">{openIssues.length}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Accepted</dt><dd className="font-medium">{accepted.length}</dd></div>
            </dl>
          </Card>
        </div>

        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="text-emerald-700">Strengths</CardTitle></CardHeader>
              <ul className="space-y-2 text-sm text-slate-600">
                {analysis.strengths.length ? analysis.strengths.map((item) => (
                  <li key={item} className="flex gap-2"><Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />{item}</li>
                )) : <li className="text-slate-500">No standout strengths detected yet.</li>}
              </ul>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-rose-700">Needs work</CardTitle></CardHeader>
              <ul className="space-y-2 text-sm text-slate-600">
                {analysis.weaknesses.length ? analysis.weaknesses.map((item) => (
                  <li key={item} className="flex gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />{item}</li>
                )) : <li className="text-slate-500">Nothing major flagged.</li>}
              </ul>
            </Card>
          </div>

          <Tabs
            value={tab}
            onChange={setTab}
            items={[
              { id: "issues", label: "Recommendations", count: analysis.issues.length },
              { id: "skills", label: "Skills", count: analysis.skill_breakdown.length },
              { id: "keywords", label: "Missing keywords", count: analysis.missing_keywords.length },
            ]}
          />

          {tab === "issues" && (
            <div className="space-y-3">
              {analysis.issues.length === 0 && (
                <EmptyState title="No issues found" description="This resume passed every check for the selected domain." />
              )}
              {analysis.issues.map((issue) => (
                <Card key={issue.id} className="p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge tone={severityTone[issue.severity]}>{issue.severity}</Badge>
                        <Badge tone="neutral">{issue.category}</Badge>
                        {issue.status !== "open" && <Badge tone="success">{issue.status}</Badge>}
                      </div>
                      <h4 className="mt-2 text-sm font-semibold text-ink">{issue.title}</h4>
                      {issue.detail && <p className="mt-1 text-sm leading-relaxed text-slate-600">{issue.detail}</p>}
                    </div>
                    {issue.status === "open" && (
                      <div className="flex gap-1">
                        <Button size="icon" variant="ghost" aria-label="Accept suggestion" onClick={() => issueMutation.mutate({ issueId: issue.id, status: "accepted" })}>
                          <Check className="h-4 w-4 text-emerald-600" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label="Edit suggestion"
                          onClick={() => {
                            setEditing(issue.id);
                            setDraft(issue.user_edit ?? issue.suggestion ?? "");
                          }}
                        >
                          <Pencil className="h-4 w-4 text-slate-500" />
                        </Button>
                        <Button size="icon" variant="ghost" aria-label="Reject suggestion" onClick={() => issueMutation.mutate({ issueId: issue.id, status: "rejected" })}>
                          <X className="h-4 w-4 text-rose-500" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {issue.evidence && (
                    <div className="mt-3 rounded-xl bg-slate-50 p-3">
                      <p className="text-[0.7rem] font-semibold uppercase tracking-wide text-slate-500">In your resume</p>
                      <p className="mt-1 text-sm italic text-slate-700">“{issue.evidence}”</p>
                    </div>
                  )}
                  {issue.suggestion && (
                    <div className="mt-2 rounded-xl bg-brand-50 p-3">
                      <p className="text-[0.7rem] font-semibold uppercase tracking-wide text-brand-700">Suggested</p>
                      <p className="mt-1 text-sm text-brand-900">{issue.user_edit ?? issue.suggestion}</p>
                    </div>
                  )}

                  {editing === issue.id && (
                    <div className="mt-3">
                      <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} rows={3} />
                      <div className="mt-2 flex gap-2">
                        <Button
                          size="sm"
                          loading={issueMutation.isPending}
                          onClick={() => issueMutation.mutate({ issueId: issue.id, status: "edited", userEdit: draft })}
                        >
                          Save edit
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button>
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}

          {tab === "skills" && (
            <Card>
              <CardHeader><CardTitle>Skill evidence</CardTitle></CardHeader>
              <div className="space-y-3">
                {(["required", "preferred", "optional"] as const).map((level) => {
                  const items = analysis.skill_breakdown.filter((skill) => skill.requirement === level);
                  if (!items.length) return null;
                  return (
                    <div key={level}>
                      <p className="label">{level}</p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {items.map((skill) => (
                          <SkillPill key={skill.skill} name={skill.skill} status={skill.status} />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="mt-4 text-xs text-slate-500">
                Green means the resume shows evidence. Amber means it is only listed. Red means it is absent.
              </p>
            </Card>
          )}

          {tab === "keywords" && (
            <Card>
              <CardHeader><CardTitle>Missing keywords</CardTitle></CardHeader>
              {analysis.missing_keywords.length ? (
                <>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.missing_keywords.map((keyword) => (
                      <SkillPill key={keyword} name={keyword} status="missing" />
                    ))}
                  </div>
                  <p className="mt-4 text-xs leading-relaxed text-slate-500">
                    Add only the ones you genuinely have, with one line of evidence each. Listing a skill you cannot
                    discuss is worse than omitting it.
                  </p>
                </>
              ) : (
                <p className="text-sm text-slate-600">Every tracked keyword for this domain is evidenced.</p>
              )}
            </Card>
          )}

          {me?.entitlements.features.version_compare && (
            <p className="text-xs text-slate-500">
              Tip: re-analyse after editing and open both reports to compare dimension deltas.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
