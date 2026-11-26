import { AlertTriangle, ArrowRight, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn, scoreTone, scoreToneClass } from "@/lib/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="label mb-1">{eyebrow}</p>}
        <h1 className="text-2xl font-bold tracking-tight text-ink sm:text-[1.7rem]">{title}</h1>
        {description && <p className="mt-1.5 max-w-2xl text-sm text-slate-600">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "neutral" | "brand" | "success" | "warning";
}) {
  const tones = {
    neutral: "bg-slate-50 text-slate-600",
    brand: "bg-brand-50 text-brand-600",
    success: "bg-emerald-50 text-emerald-600",
    warning: "bg-amber-50 text-amber-600",
  } as const;
  return (
    <div className="surface p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label">{label}</p>
          <p className="mt-2 text-2xl font-bold tracking-tight text-ink">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
        </div>
        {icon && <span className={cn("rounded-xl p-2", tones[tone])}>{icon}</span>}
      </div>
    </div>
  );
}

export function ScoreRing({ score, size = 132, label }: { score: number; size?: number; label?: string }) {
  const tone = scoreTone(score);
  const palette = scoreToneClass[tone];
  const radius = (size - 14) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" role="img" aria-label={`Score ${score} out of 100`}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={10} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={palette.stroke}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-3xl font-bold tracking-tight", palette.text)}>{score}</span>
        <span className="text-[0.65rem] font-medium uppercase tracking-wider text-slate-400">{label ?? "of 100"}</span>
      </div>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="surface flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      {icon && <div className="rounded-2xl bg-brand-50 p-3 text-brand-600">{icon}</div>}
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {description && <p className="max-w-md text-sm text-slate-600">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="surface flex flex-col items-start gap-3 border-rose-200 p-5">
      <div className="flex items-center gap-2 text-rose-700">
        <AlertTriangle className="h-4 w-4" />
        <p className="text-sm font-semibold">Something went wrong</p>
      </div>
      <p className="text-sm text-slate-600">{error.message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      {label}…
    </div>
  );
}

export function InlineLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <a href={to} className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700">
      {children}
      <ArrowRight className="h-3.5 w-3.5" />
    </a>
  );
}

export function SkillPill({
  name,
  status,
}: {
  name: string;
  status: "found" | "partial" | "missing" | "recommended";
}) {
  const tones = {
    found: "bg-emerald-50 text-emerald-800 ring-emerald-200",
    partial: "bg-amber-50 text-amber-800 ring-amber-200",
    missing: "bg-rose-50 text-rose-700 ring-rose-200",
    recommended: "bg-slate-50 text-slate-600 ring-slate-200",
  } as const;
  return (
    <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset", tones[status])}>{name}</span>
  );
}
