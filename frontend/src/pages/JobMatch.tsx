import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState, ErrorState, PageHeader, ScoreRing } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/field";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { jobMatchesApi } from "@/services/jobMatches";
import { resumesApi } from "@/services/resumes";

export function JobMatchPage() {
  const { me } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [resumeVersionId, setResumeVersionId] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [rawText, setRawText] = useState("");
  const [activeMatchId, setActiveMatchId] = useState<string | null>(null);

  const allowed = Boolean(me?.entitlements.features.jd_matching);
  const resumesQuery = useQuery({ queryKey: ["resumes", 0], queryFn: () => resumesApi.list(50, 0) });
  const matchesQuery = useQuery({ queryKey: ["job-matches"], queryFn: () => jobMatchesApi.list(10, 0) });

  const create = useMutation({
    mutationFn: () =>
      jobMatchesApi.create({
        resume_version_id: resumeVersionId,
        title: title || undefined,
        company: company || undefined,
        raw_text: rawText,
      }),
    onSuccess: async (match) => {
      setActiveMatchId(match.id);
      await queryClient.invalidateQueries({ queryKey: ["job-matches"] });
      toast.push("Match queued", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not start the match", "error"),
  });

  const activeQuery = useQuery({
    queryKey: ["job-match", activeMatchId],
    queryFn: () => jobMatchesApi.get(activeMatchId!),
    enabled: Boolean(activeMatchId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 2000 : false;
    },
  });

  const resumeOptions = resumesQuery.data?.items ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="Job matching"
        title="Match your resume to a posting"
        description="Paste the requirements. We extract what the posting asks for and compare it with your resume."
      />

      {!allowed ? (
        <Alert tone="warning" title="Job matching is a paid feature">
          <p>Upgrade to Pro to compare your resume against specific postings and see missing requirements.</p>
          <Link to="/pricing" className="mt-3 inline-block">
            <Button size="sm">See plans</Button>
          </Link>
        </Alert>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <Card>
            <CardHeader><CardTitle>New match</CardTitle></CardHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="resume">Resume</Label>
                <Select id="resume" value={resumeVersionId} onChange={(event) => setResumeVersionId(event.target.value)}>
                  <option value="">Select a processed resume</option>
                  {resumeOptions.map((resume) => (
                    <option key={resume.id} value={resume.current_version_id ?? ""} disabled={!resume.current_version_id}>
                      {resume.title} · {resume.status}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label htmlFor="role">Job title</Label>
                  <Input id="role" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Senior Frontend Developer" />
                </div>
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input id="company" value={company} onChange={(event) => setCompany(event.target.value)} placeholder="Systems Ltd" />
                </div>
              </div>
              <div>
                <Label htmlFor="jd">Job description</Label>
                <Textarea
                  id="jd"
                  rows={10}
                  value={rawText}
                  onChange={(event) => setRawText(event.target.value)}
                  placeholder="Paste the responsibilities and requirements…"
                />
                <p className="mt-1 text-xs text-slate-500">{rawText.length} / 20000 characters</p>
              </div>
              <Button
                onClick={() => create.mutate()}
                loading={create.isPending}
                disabled={!resumeVersionId || rawText.trim().length < 40}
              >
                <Briefcase className="h-4 w-4" /> Compare with posting
              </Button>
            </div>
          </Card>

          <div className="space-y-4">
            {activeMatchId && (
              <Card>
                {activeQuery.isLoading && (
                  <p className="flex items-center gap-2 text-sm text-slate-500">
                    <Loader2 className="h-4 w-4 animate-spin" /> Matching…
                  </p>
                )}
                {activeQuery.data && activeQuery.data.status === "ready" && (
                  <>
                    <div className="flex items-center gap-4">
                      <ScoreRing score={activeQuery.data.match_score ?? 0} size={104} label="match" />
                      <div>
                        <p className="text-sm font-semibold text-ink">
                          {activeQuery.data.matched.length} matched · {activeQuery.data.partial.length} partial ·{" "}
                          {activeQuery.data.missing.length} missing
                        </p>
                        <p className="mt-1 text-xs leading-relaxed text-slate-500">
                          A similarity indicator, not a probability of being hired.
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 space-y-3">
                      {activeQuery.data.missing.length > 0 && (
                        <div>
                          <p className="label text-rose-600">Missing</p>
                          <div className="mt-1 flex flex-wrap gap-1.5">
                            {activeQuery.data.missing.map((item) => (
                              <Badge key={item.label} tone="danger">{item.label}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {activeQuery.data.partial.length > 0 && (
                        <div>
                          <p className="label text-amber-600">Partial</p>
                          <div className="mt-1 flex flex-wrap gap-1.5">
                            {activeQuery.data.partial.map((item) => (
                              <Badge key={item.label} tone="warning">{item.label}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {activeQuery.data.matched.length > 0 && (
                        <div>
                          <p className="label text-emerald-600">Matched</p>
                          <div className="mt-1 flex flex-wrap gap-1.5">
                            {activeQuery.data.matched.map((item) => (
                              <Badge key={item.label} tone="success">{item.label}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      <div>
                        <p className="label">Recommendations</p>
                        <ul className="mt-1 space-y-1.5 text-sm text-slate-600">
                          {activeQuery.data.recommendations.map((item) => (
                            <li key={item} className="flex gap-2">
                              <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </>
                )}
                {activeQuery.data?.status === "failed" && <Alert tone="danger">Matching failed. Try again.</Alert>}
              </Card>
            )}

            <Card>
              <CardHeader><CardTitle>Recent matches</CardTitle></CardHeader>
              {matchesQuery.isError && <ErrorState error={matchesQuery.error as Error} />}
              {matchesQuery.data?.items.length ? (
                <ul className="divide-y divide-line">
                  {matchesQuery.data.items.map((match) => (
                    <li key={match.id} className="flex items-center justify-between py-2.5">
                      <button
                        type="button"
                        className="text-left text-sm font-medium text-ink hover:text-brand-600"
                        onClick={() => setActiveMatchId(match.id)}
                      >
                        {match.match_score !== null ? `${match.match_score}% match` : match.status}
                        <span className="block text-xs font-normal text-slate-500">{formatDateTime(match.created_at)}</span>
                      </button>
                      <Badge tone={match.status === "ready" ? "success" : "info"}>{match.status}</Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No matches yet" description="Paste a posting to see how your resume compares." />
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
