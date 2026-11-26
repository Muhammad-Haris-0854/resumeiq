import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BarChart3, FileText, Plus, Sparkles, Upload } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState, ErrorState, Loading, PageHeader, ScoreRing, StatCard } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";
import { formatDateTime, scoreToneClass, scoreTone } from "@/lib/utils";
import { analysesApi } from "@/services/analyses";
import { resumesApi } from "@/services/resumes";

export function DashboardPage() {
  const { me } = useAuth();
  const navigate = useNavigate();

  const resumesQuery = useQuery({ queryKey: ["resumes", 0], queryFn: () => resumesApi.list(6, 0) });
  const analysesQuery = useQuery({ queryKey: ["analyses", 0], queryFn: () => analysesApi.list(6, 0) });

  const latest = analysesQuery.data?.items.find((item) => item.status === "ready");
  const trend = (analysesQuery.data?.items ?? [])
    .filter((item) => item.status === "ready" && item.overall_score !== null)
    .slice(0, 8)
    .reverse()
    .map((item, index) => ({ attempt: `#${index + 1}`, score: item.overall_score ?? 0 }));
  const used = me?.entitlements.analyses_used ?? 0;
  const quota = me?.entitlements.analysis_quota ?? 0;

  return (
    <div>
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome back${me?.profile.full_name ? `, ${me.profile.full_name.split(" ")[0]}` : ""}`}
        description="Your latest score, remaining analyses and everything waiting on you."
        actions={
          <>
            <Button variant="outline" onClick={() => navigate("/builder")}>
              <FileText className="h-4 w-4" /> Builder
            </Button>
            <Button onClick={() => navigate("/resumes/upload")}>
              <Upload className="h-4 w-4" /> Upload resume
            </Button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Resumes analysed"
          value={analysesQuery.data?.total ?? 0}
          hint="Reports generated"
          icon={<BarChart3 className="h-4 w-4" />}
          tone="brand"
        />
        <StatCard
          label="Latest score"
          value={latest?.overall_score ?? "—"}
          hint={latest ? formatDateTime(latest.created_at) : "No report yet"}
          icon={<Sparkles className="h-4 w-4" />}
          tone="success"
        />
        <StatCard
          label="Analyses left"
          value={`${me?.entitlements.analyses_remaining ?? 0}`}
          hint={`${used} of ${quota} used this month`}
          icon={<ArrowUpRight className="h-4 w-4" />}
        />
        <StatCard
          label="Plan"
          value={me?.entitlements.plan.toUpperCase() ?? "—"}
          hint={me?.entitlements.features.jd_matching ? "Job matching included" : "Upgrade for job matching"}
          icon={<FileText className="h-4 w-4" />}
          tone="warning"
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Latest report</CardTitle>
              <p className="mt-1 text-sm text-slate-600">Your most recent completed analysis.</p>
            </div>
            {latest && <Badge tone={scoreTone(latest.overall_score ?? 0) === "strong" ? "success" : "warning"}>{latest.overall_score}/100</Badge>}
          </CardHeader>

          {analysesQuery.isLoading && <Loading label="Loading reports" />}
          {analysesQuery.isError && (
            <ErrorState error={analysesQuery.error as Error} onRetry={() => void analysesQuery.refetch()} />
          )}

          {latest ? (
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
              <ScoreRing score={latest.overall_score ?? 0} />
              <div className="flex-1">
                <p className="text-sm leading-relaxed text-slate-600">{latest.summary ?? "Report ready."}</p>
                <div className="mt-3 space-y-2">
                  {latest.scores.slice(0, 3).map((score) => (
                    <div key={score.key}>
                      <div className="flex items-center justify-between text-xs font-medium text-slate-600">
                        <span>{score.label}</span>
                        <span>{score.score}</span>
                      </div>
                      <Progress value={score.score} className="mt-1" />
                    </div>
                  ))}
                </div>
                <Button size="sm" className="mt-4" onClick={() => navigate(`/analyses/${latest.id}`)}>
                  Open full report
                </Button>
              </div>
            </div>
          ) : (
            !analysesQuery.isLoading && (
              <EmptyState
                icon={<Sparkles className="h-5 w-5" />}
                title="No analysis yet"
                description="Upload a resume and pick a career domain to get your first scored report."
                action={
                  <Button onClick={() => navigate("/resumes/upload")}>
                    <Plus className="h-4 w-4" /> Start an analysis
                  </Button>
                }
              />
            )
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Monthly usage</CardTitle>
          </CardHeader>
          <div className={scoreToneClass[scoreTone(quota ? (used / quota) * 100 : 0)].text}>
            <p className="text-3xl font-bold">{Math.max(0, quota - used)}</p>
            <p className="text-xs font-medium uppercase tracking-wide">analyses remaining</p>
          </div>
          <Progress value={quota ? (used / quota) * 100 : 0} className="mt-3" />
          <p className="mt-2 text-xs text-slate-500">
            {used} used of {quota} on the {me?.entitlements.plan} plan. Resets on the 1st.
          </p>
          <div className="mt-5 space-y-2">
            <p className="label">Quick actions</p>
            {[
              { label: "Match a job description", to: "/job-match" },
              { label: "Browse templates", to: "/templates" },
              { label: "Change career domain", to: "/career" },
            ].map((action) => (
              <Link
                key={action.to}
                to={action.to}
                className="flex items-center justify-between rounded-xl border border-line px-3 py-2 text-sm text-slate-700 hover:border-slate-300 hover:bg-slate-50"
              >
                {action.label}
                <ArrowUpRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
            ))}
          </div>
        </Card>
      </div>

      {trend.length >= 2 && (
        <Card className="mt-6">
          <CardHeader>
            <div>
              <CardTitle>Score trend</CardTitle>
              <p className="mt-1 text-sm text-slate-600">Overall score across your last {trend.length} completed reports.</p>
            </div>
          </CardHeader>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="attempt" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                  labelFormatter={(label) => `Report ${label}`}
                />
                <Line type="monotone" dataKey="score" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
          </CardHeader>
          {analysesQuery.data?.items.length ? (
            <ul className="divide-y divide-line">
              {analysesQuery.data.items.map((analysis) => (
                <li key={analysis.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <Link to={`/analyses/${analysis.id}`} className="text-sm font-medium text-ink hover:text-brand-600">
                      {analysis.status === "ready" ? `Report · ${analysis.overall_score}/100` : `Report ${analysis.status}`}
                    </Link>
                    <p className="text-xs text-slate-500">{formatDateTime(analysis.created_at)}</p>
                  </div>
                  <Badge tone={analysis.status === "ready" ? "success" : analysis.status === "failed" ? "danger" : "info"}>
                    {analysis.status}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-600">Nothing here yet.</p>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Your resumes</CardTitle>
            <Link to="/resumes/upload" className="text-xs font-semibold text-brand-600">Upload</Link>
          </CardHeader>
          {resumesQuery.data?.items.length ? (
            <ul className="divide-y divide-line">
              {resumesQuery.data.items.map((resume) => (
                <li key={resume.id} className="flex items-center justify-between py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-ink">{resume.title}</p>
                    <p className="text-xs text-slate-500">
                      {resume.status} · {formatDateTime(resume.created_at)}
                    </p>
                  </div>
                  {resume.latest_score !== null && <Badge tone="brand">{resume.latest_score}</Badge>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-600">No resumes yet.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
