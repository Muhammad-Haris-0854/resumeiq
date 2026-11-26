import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

export function Tabs({
  items,
  value,
  onChange,
  className,
}: {
  items: TabItem[];
  value: string;
  onChange: (id: string) => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1", className)} role="tablist">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={value === item.id}
          onClick={() => onChange(item.id)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
            value === item.id ? "bg-white text-ink shadow-sm" : "text-slate-600 hover:text-ink",
          )}
        >
          {item.label}
          {typeof item.count === "number" && <span className="ml-1.5 text-xs text-slate-400">{item.count}</span>}
        </button>
      ))}
    </div>
  );
}
