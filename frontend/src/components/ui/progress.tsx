import { cn } from "@/lib/utils";

export function Progress({ value, className, tone = "brand" }: { value: number; className?: string; tone?: "brand" | "success" | "warning" | "danger" }) {
  const clamped = Math.max(0, Math.min(100, value));
  const colors = {
    brand: "bg-brand-600",
    success: "bg-emerald-600",
    warning: "bg-amber-500",
    danger: "bg-rose-600",
  } as const;
  return (
    <div
      className={cn("h-2 w-full overflow-hidden rounded-full bg-slate-100", className)}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className={cn("h-full rounded-full transition-all", colors[tone])} style={{ width: `${clamped}%` }} />
    </div>
  );
}
