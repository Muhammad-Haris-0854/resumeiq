import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const tones = {
  info: { wrap: "border-sky-200 bg-sky-50 text-sky-900", Icon: Info },
  success: { wrap: "border-emerald-200 bg-emerald-50 text-emerald-900", Icon: CheckCircle2 },
  warning: { wrap: "border-amber-200 bg-amber-50 text-amber-900", Icon: AlertTriangle },
  danger: { wrap: "border-rose-200 bg-rose-50 text-rose-900", Icon: XCircle },
} as const;

export function Alert({
  tone = "info",
  title,
  children,
  className,
}: {
  tone?: keyof typeof tones;
  title?: string;
  children?: ReactNode;
  className?: string;
}) {
  const { wrap, Icon } = tones[tone];
  return (
    <div className={cn("flex gap-3 rounded-xl border p-3.5 text-sm", wrap, className)} role="status">
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div>
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className={cn(title && "mt-1", "leading-relaxed")}>{children}</div>}
      </div>
    </div>
  );
}
