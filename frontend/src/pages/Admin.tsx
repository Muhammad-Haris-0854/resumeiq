import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, DollarSign, Search, Users } from "lucide-react";
import { useState } from "react";

import { ErrorState, Loading, PageHeader, StatCard } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/field";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/utils";
import { adminApi } from "@/services/admin";

const WEIGHT_LABELS: Record<string, string> = {
  keyword_match: "Keyword match",
  technical_skills: "Technical skills",
  ats_compatibility: "ATS compatibility",
  content_quality: "Content quality",
  grammar: "Grammar",
  formatting: "Formatting",
  experience_relevance: "Experience relevance",
};

export function AdminPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [weights, setWeights] = useState<Record<string, number> | null>(null);

  const metricsQuery = useQuery({ queryKey: ["admin-metrics"], queryFn: adminApi.metrics });
  const usersQuery = useQuery({ queryKey: ["admin-users", search], queryFn: () => adminApi.users(search) });
  const healthQuery = useQuery({ queryKey: ["admin-health"], queryFn: adminApi.health });
  const scoringQuery = useQuery({
    queryKey: ["admin-scoring"],
    queryFn: adminApi.scoring,
    enabled: weights === null,
  });

  const currentWeights = weights ?? scoringQuery.data ?? null;
  const total = currentWeights ? Object.values(currentWeights).reduce((sum, value) => sum + value, 0) : 0;

  const updateUser = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: { role?: "user" | "administrator"; plan?: "free" | "pro" | "premium" } }) =>
      adminApi.updateUser(id, patch),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-metrics"] });
      toast.push("User updated", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Update failed", "error"),
  });

  const saveWeights = useMutation({
    mutationFn: (payload: Record<string, number>) => adminApi.updateScoring(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-scoring"] });
      setWeights(null);
      toast.push("Scoring weights saved", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Weights must sum to 100", "error"),
  });

  return (
    <div>
      <PageHeader
        eyebrow="Administration"
        title="Platform overview"
        description="Users, revenue, analysis volume and the levers you can change."
      />

      {metricsQuery.isLoading && <Loading label="Loading metrics" />}
      {metricsQuery.isError && <ErrorState error={metricsQuery.error as Error} onRetry={() => void metricsQuery.refetch()} />}

      {metricsQuery.data && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total users" value={metricsQuery.data.total_users} hint={`${metricsQuery.data.free_users} free`} icon={<Users className="h-4 w-4" />} tone="brand" />
          <StatCard label="Paid users" value={metricsQuery.data.paid_users} hint={`${metricsQuery.data.active_subscriptions} active subscriptions`} icon={<DollarSign className="h-4 w-4" />} tone="success" />
          <StatCard label="MRR" value={formatMoney(metricsQuery.data.mrr_cents)} hint="Normalised to monthly" />
          <StatCard label="Analyses this month" value={metricsQuery.data.analyses_this_month} hint={`${metricsQuery.data.failed_analyses_this_month} failed`} icon={<Activity className="h-4 w-4" />} tone="warning" />
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-slate-400" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search email or name"
                className="h-9 w-52"
              />
            </div>
          </CardHeader>
          {usersQuery.isError && <ErrorState error={usersQuery.error as Error} />}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 font-medium">User</th>
                  <th className="py-2 pr-3 font-medium">Plan</th>
                  <th className="py-2 pr-3 font-medium">Role</th>
                  <th className="py-2 font-medium">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {usersQuery.data?.items.map((user) => (
                  <tr key={user.id}>
                    <td className="py-2.5 pr-3">
                      <p className="font-medium text-ink">{user.full_name ?? "—"}</p>
                      <p className="text-xs text-slate-500">{user.email}</p>
                    </td>
                    <td className="py-2.5 pr-3">
                      <Select
                        value={user.plan}
                        className="h-8 w-24 text-xs"
                        onChange={(event) =>
                          updateUser.mutate({ id: user.id, patch: { plan: event.target.value as "free" | "pro" | "premium" } })
                        }
                      >
                        <option value="free">free</option>
                        <option value="pro">pro</option>
                        <option value="premium">premium</option>
                      </Select>
                    </td>
                    <td className="py-2.5 pr-3">
                      <Select
                        value={user.role}
                        className="h-8 w-32 text-xs"
                        onChange={(event) =>
                          updateUser.mutate({ id: user.id, patch: { role: event.target.value as "user" | "administrator" } })
                        }
                      >
                        <option value="user">user</option>
                        <option value="administrator">administrator</option>
                      </Select>
                    </td>
                    <td className="py-2.5 text-xs text-slate-500">{formatDate(user.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {usersQuery.data?.items.length === 0 && <p className="py-4 text-sm text-slate-500">No users match that search.</p>}
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Scoring weights</CardTitle></CardHeader>
            {currentWeights ? (
              <div className="space-y-2">
                {Object.entries(currentWeights).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-3">
                    <Label className="mb-0 text-xs text-slate-600">{WEIGHT_LABELS[key] ?? key}</Label>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      value={value}
                      className="h-8 w-20 text-right text-xs"
                      onChange={(event) =>
                        setWeights({ ...currentWeights, [key]: Number(event.target.value) })
                      }
                    />
                  </div>
                ))}
                <p className={total === 100 ? "text-xs text-emerald-600" : "text-xs text-rose-600"}>Total: {total} / 100</p>
                <Button
                  size="sm"
                  disabled={total !== 100}
                  loading={saveWeights.isPending}
                  onClick={() => currentWeights && saveWeights.mutate(currentWeights)}
                >
                  Save weights
                </Button>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Loading weights…</p>
            )}
          </Card>

          <Card>
            <CardHeader><CardTitle>System health</CardTitle></CardHeader>
            {healthQuery.data ? (
              <dl className="space-y-1.5 text-sm">
                {Object.entries(healthQuery.data).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-3">
                    <dt className="text-slate-500">{key.replace(/_/g, " ")}</dt>
                    <dd className="font-mono text-xs text-ink">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-slate-500">Loading…</p>
            )}
            <Badge tone="success" className="mt-3">Admin access verified server-side</Badge>
          </Card>
        </div>
      </div>
    </div>
  );
}
