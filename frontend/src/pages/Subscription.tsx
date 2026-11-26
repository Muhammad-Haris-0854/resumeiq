import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CreditCard, Download, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

import { ErrorState, PageHeader, StatCard } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/utils";
import { billingApi } from "@/services/billing";

export function SubscriptionPage() {
  const { me, refreshMe } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();

  const subscriptionQuery = useQuery({ queryKey: ["subscription"], queryFn: billingApi.subscription });
  const invoicesQuery = useQuery({ queryKey: ["invoices"], queryFn: billingApi.invoices });

  const portal = useMutation({
    mutationFn: billingApi.portal,
    onSuccess: ({ portal_url }) => {
      window.location.href = portal_url;
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not open the portal", "error"),
  });

  const cancel = useMutation({
    mutationFn: billingApi.cancel,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["subscription"] });
      await refreshMe();
      toast.push("Subscription will end at the current period", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not cancel", "error"),
  });

  const ent = me?.entitlements;
  const used = ent?.analyses_used ?? 0;
  const quota = ent?.analysis_quota ?? 0;

  return (
    <div>
      <PageHeader
        eyebrow="Plan & billing"
        title="Your subscription"
        description="Plans change only after a verified payment event. Nothing here trusts a browser redirect."
        actions={<Link to="/pricing"><Button>Compare plans</Button></Link>}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Current plan" value={ent?.plan.toUpperCase() ?? "—"} hint={subscriptionQuery.data?.status ?? ""} icon={<CreditCard className="h-4 w-4" />} tone="brand" />
        <StatCard label="Analyses this month" value={`${used}/${quota}`} hint="Resets on the 1st" />
        <StatCard
          label="Renews"
          value={formatDate(subscriptionQuery.data?.current_period_end)}
          hint={subscriptionQuery.data?.cancel_at_period_end ? "Cancelled" : subscriptionQuery.data?.interval ?? ""}
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader><CardTitle>Usage</CardTitle></CardHeader>
          <Progress value={quota ? (used / quota) * 100 : 0} />
          <p className="mt-2 text-sm text-slate-600">
            {Math.max(0, quota - used)} analyses remaining on the {ent?.plan} plan.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => portal.mutate()} loading={portal.isPending}>
              <ExternalLink className="h-3.5 w-3.5" /> Manage payment
            </Button>
            {ent?.plan !== "free" && !subscriptionQuery.data?.cancel_at_period_end && (
              <Button variant="ghost" size="sm" className="text-rose-600" onClick={() => cancel.mutate()} loading={cancel.isPending}>
                Cancel subscription
              </Button>
            )}
          </div>
          {ent?.plan === "free" && (
            <div className="mt-4 rounded-xl bg-canvas p-3 text-sm text-slate-600">
              Upgrade for job matching, AI rewriting and more analyses per month.
              <Link to="/pricing" className="ml-1 font-semibold text-brand-600">See plans</Link>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader><CardTitle>Invoices</CardTitle></CardHeader>
          {invoicesQuery.isError && <ErrorState error={invoicesQuery.error as Error} />}
          {invoicesQuery.data?.length ? (
            <ul className="divide-y divide-line">
              {invoicesQuery.data.map((invoice) => (
                <li key={invoice.id} className="flex items-center justify-between py-2.5 text-sm">
                  <div>
                    <p className="font-medium text-ink">{formatMoney(invoice.amount_cents, invoice.currency.toUpperCase())}</p>
                    <p className="text-xs text-slate-500">{formatDate(invoice.created_at)} · {invoice.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={invoice.status === "succeeded" ? "success" : invoice.status === "failed" ? "danger" : "neutral"}>
                      {invoice.status}
                    </Badge>
                    {invoice.invoice_url && (
                      <a href={invoice.invoice_url} target="_blank" rel="noreferrer" aria-label="Open invoice">
                        <Download className="h-4 w-4 text-slate-500" />
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-600">No payments yet.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
