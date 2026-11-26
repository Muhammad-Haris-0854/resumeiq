import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function formatMoney(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export type ScoreTone = "strong" | "solid" | "needs-work" | "at-risk";

export function scoreTone(score: number): ScoreTone {
  if (score >= 85) return "strong";
  if (score >= 70) return "solid";
  if (score >= 50) return "needs-work";
  return "at-risk";
}

export const scoreToneClass: Record<ScoreTone, { text: string; bg: string; ring: string; stroke: string }> = {
  strong: { text: "text-emerald-700", bg: "bg-emerald-50", ring: "ring-emerald-200", stroke: "#059669" },
  solid: { text: "text-brand-700", bg: "bg-brand-50", ring: "ring-brand-200", stroke: "#4f46e5" },
  "needs-work": { text: "text-amber-700", bg: "bg-amber-50", ring: "ring-amber-200", stroke: "#d97706" },
  "at-risk": { text: "text-rose-700", bg: "bg-rose-50", ring: "ring-rose-200", stroke: "#e11d48" },
};

export function initials(name: string | null | undefined): string {
  if (!name) return "RI";
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || "RI";
}

export function truncate(value: string, max = 120): string {
  return value.length <= max ? value : `${value.slice(0, max - 1)}…`;
}

export function slugToTitle(slug: string): string {
  return slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
