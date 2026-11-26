import { Brain, FileText, KeyRound, Layers, LineChart, ListChecks, Lock, ScanSearch, Timer } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

const groups = [
  {
    icon: ScanSearch,
    title: "Document processing",
    items: [
      "PDF and DOCX extraction with PyMuPDF and python-docx",
      "OCR fallback for scanned PDFs",
      "Section, bullet and date detection",
      "Multiple versions per resume with history",
    ],
  },
  {
    icon: ListChecks,
    title: "Domain analysis",
    items: [
      "Required, preferred and optional skills per domain",
      "Alias resolution so ReactJS equals React.js",
      "Found, partial and missing classification with evidence",
      "Never recommends claiming a skill you do not evidence",
    ],
  },
  {
    icon: Brain,
    title: "AI review",
    items: [
      "Schema-validated JSON output, never free text",
      "Provider-agnostic: OpenAI-compatible endpoints",
      "Deterministic fallback when the provider is down",
      "Prompt-injection resistant: resume text is data",
    ],
  },
  {
    icon: LineChart,
    title: "Scoring",
    items: [
      "Seven dimensions with configurable weights",
      "Every score shows its inputs",
      "Bounded AI adjustments (±8 max)",
      "Same resume, same score, every time",
    ],
  },
  {
    icon: FileText,
    title: "Builder and export",
    items: [
      "Seven professional templates",
      "Autosave with version history and restore",
      "Live preview that matches the PDF",
      "Server-side PDF export with selectable text",
    ],
  },
  {
    icon: Lock,
    title: "Security",
    items: [
      "Supabase Auth with JWT verification on every request",
      "Row-level security on every table",
      "Private buckets and 60-second signed URLs",
      "Server-side entitlement checks, never the client",
    ],
  },
];

const weights = [
  ["Keyword match", "20%"],
  ["Technical skills", "20%"],
  ["ATS compatibility", "15%"],
  ["Content quality", "15%"],
  ["Grammar", "10%"],
  ["Formatting", "10%"],
  ["Experience relevance", "10%"],
];

export function FeaturesPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-14">
      <div className="max-w-2xl">
        <p className="label">Features</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Everything between “here is my resume” and “here is the PDF I send”.
        </h1>
        <p className="mt-4 text-base leading-relaxed text-slate-600">
          ResumeIQ is not a keyword counter. It parses the document, models the target role, scores what is
          measurable, and keeps the model on a short leash for everything else.
        </p>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((group) => (
          <div key={group.title} className="surface p-5">
            <span className="inline-flex rounded-xl bg-brand-50 p-2 text-brand-600">
              <group.icon className="h-5 w-5" aria-hidden />
            </span>
            <h2 className="mt-3 text-base font-semibold">{group.title}</h2>
            <ul className="mt-2 space-y-2 text-sm leading-relaxed text-slate-600">
              {group.items.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-400" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="surface p-6">
          <h2 className="text-base font-semibold">How the score is weighted</h2>
          <p className="mt-1 text-sm text-slate-600">Defaults are shown; administrators can change them, as long as they sum to 100.</p>
          <div className="mt-4 divide-y divide-line">
            {weights.map(([label, value]) => (
              <div key={label} className="flex items-center justify-between py-2.5 text-sm">
                <span className="text-slate-700">{label}</span>
                <span className="font-mono text-xs font-semibold text-brand-700">{value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="surface flex flex-col justify-between p-6">
          <div>
            <span className="inline-flex rounded-xl bg-navy-900 p-2 text-white">
              <Timer className="h-5 w-5" aria-hidden />
            </span>
            <h2 className="mt-3 text-base font-semibold">Built to stay responsive</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Uploads return immediately. Extraction and AI work run on Celery workers with retries and per-task
              time limits, so a slow provider never blocks the product.
            </p>
          </div>
          <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="inline-flex items-center gap-1 rounded-full border border-line px-2.5 py-1">
              <Layers className="h-3.5 w-3.5" /> Redis queues
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-line px-2.5 py-1">
              <KeyRound className="h-3.5 w-3.5" /> JWT verified
            </span>
          </div>
        </div>
      </div>

      <div className="mt-10 flex flex-wrap items-center gap-3">
        <Link to="/signup"><Button size="lg">Start free</Button></Link>
        <Link to="/pricing"><Button variant="outline" size="lg">Compare plans</Button></Link>
      </div>
    </div>
  );
}
