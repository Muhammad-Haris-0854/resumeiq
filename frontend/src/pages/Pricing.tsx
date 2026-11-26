import { useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ErrorState } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { cn, formatMoney } from "@/lib/utils";
import { billingApi } from "@/services/billing";

const planCopy: Record<string, string[]> = {
  free: ["2 analyses per month", "All seven score dimensions", "2 resumes stored", "ATS-Friendly and Minimalist templates"],
  pro: [
    "20 analyses per month",
    "Job description matching",
    "AI rewriting suggestions",
    "10 resumes, 5 templates",
    "Version comparison",
  ],
  premium: [
    "60 analyses per month",
    "Priority processing queue",
    "All seven templates",
    "30 resumes stored",
    "Advanced career insights",
  ],
};

export function PricingPage() {
  const [interval, setInterval] = useState<"month" | "year">("month");
  const { session, me } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const plansQuery = useQuery({ queryKey: ["plans"], queryFn: billingApi.plans, retry: 1 });

  const startCheckout = async (code: "pro" | "premium") => {
    if (!session) {
      navigate("/signup");
      return;
    }
    try {
      const { checkout_url } = await billingApi.checkout(code, interval);
      window.location.href = checkout_url;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Checkout could not be started.";
      toast.push(message, "error");
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-5 py-14">
      <div className="mx-auto max-w-2xl text-center">
        <p className="label">Pricing</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Pay for the searches you are actually running.</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          Every plan includes the full scoring engine. Paid plans add volume, job matching and the AI rewriting pass.
        </p>
        <div className="mt-6 inline-flex rounded-xl bg-slate-100 p-1">
          {(["month", "year"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setInterval(option)}
              className={cn(
                "rounded-lg px-4 py-1.5 text-sm font-medium transition-colors",
                interval === option ? "bg-white text-ink shadow-sm" : "text-slate-600",
              )}
            >
              {option === "month" ? "Monthly" : "Annual · save 20%"}
            </button>
          ))}
        </div>
      </div>

      {plansQuery.isError && (
        <div className="mx-auto mt-8 max-w-xl">
          <ErrorState error={plansQuery.error as Error} onRetry={() => void plansQuery.refetch()} />
        </div>
      )}

      {plansQuery.isLoading && (
        <div className="mt-10 flex justify-center text-sm text-slate-500">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading plans…
        </div>
      )}

      {plansQuery.data && (
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {plansQuery.data.map((plan) => {
            const price = interval === "year" ? plan.annual_price_cents : plan.monthly_price_cents;
            const current = me?.entitlements.plan === plan.code;
            const highlight = plan.code === "pro";
            return (
              <div
                key={plan.code}
                className={cn(
                  "surface flex flex-col p-6",
                  highlight && "ring-2 ring-brand-500 ring-offset-2 ring-offset-canvas",
                )}
              >
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">{plan.name}</h2>
                  {highlight && <Badge tone="brand">Most popular</Badge>}
                  {current && !highlight && <Badge tone="success">Current</Badge>}
                </div>
                <p className="mt-1 min-h-10 text-sm text-slate-600">{plan.description}</p>
                <p className="mt-4 text-3xl font-bold tracking-tight">
                  {price === 0 ? "Free" : formatMoney(price)}
                  {price > 0 && <span className="text-sm font-medium text-slate-500">/{interval}</span>}
                </p>
                <ul className="mt-5 flex-1 space-y-2.5 text-sm text-slate-600">
                  {(planCopy[plan.code] ?? []).map((item) => (
                    <li key={item} className="flex gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden />
                      {item}
                    </li>
                  ))}
                </ul>
                {plan.code === "free" ? (
                  <Button variant="outline" className="mt-6" onClick={() => navigate(session ? "/dashboard" : "/signup")}>
                    {session ? "Go to dashboard" : "Start free"}
                  </Button>
                ) : (
                  <Button
                    className="mt-6"
                    variant={highlight ? "primary" : "secondary"}
                    disabled={current}
                    onClick={() => void startCheckout(plan.code as "pro" | "premium")}
                  >
                    {current ? "Current plan" : `Choose ${plan.name}`}
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-10 rounded-2xl border border-line bg-canvas p-6 text-sm text-slate-600">
        <p className="font-semibold text-ink">About payments</p>
        <p className="mt-1.5 leading-relaxed">
          Plans are activated only after a verified server-side payment event. Card data never touches ResumeIQ.
          You can cancel any time; access continues until the end of the paid period.
        </p>
      </div>
    </div>
  );
}
