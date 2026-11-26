import { motion } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  FileSearch,
  Gauge,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { ScoreRing } from "@/components/shared";

const pillars = [
  {
    icon: FileSearch,
    title: "Reads your actual document",
    body: "PDF and DOCX are parsed on the server, including scanned files through OCR. Sections, bullets and dates are structured, not guessed.",
  },
  {
    icon: Target,
    title: "Scores against your domain",
    body: "Pick React.js Developer, Data Analyst or one of 16 domains. Every required, preferred and optional skill is checked with evidence.",
  },
  {
    icon: Gauge,
    title: "Numbers you can trust",
    body: "Seven deterministic scores computed from explicit inputs. The model writes observations, never the score.",
  },
  {
    icon: ShieldCheck,
    title: "Private by default",
    body: "Private storage bucket, signed downloads, row-level security. Your resume is never used to train a model.",
  },
];

const steps = [
  { number: "01", title: "Upload", body: "Drop a PDF or DOCX. We extract the text, sections and skills." },
  { number: "02", title: "Choose a domain", body: "The taxonomy defines what strong looks like for that role." },
  { number: "03", title: "Review the report", body: "Scores, gaps and rewrites with the evidence behind each one." },
  { number: "04", title: "Rebuild and export", body: "Edit in the builder, pick a template, download an ATS-safe PDF." },
];

const previewScores = [
  { label: "Keyword match", score: 68 },
  { label: "ATS compatibility", score: 92 },
  { label: "Content quality", score: 74 },
];

export function LandingPage() {
  return (
    <div>
      <section className="relative overflow-hidden border-b border-line bg-white">
        <div className="absolute inset-0 grid-lines opacity-60" aria-hidden />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
            <span className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
              <Sparkles className="h-3.5 w-3.5" />
              Built for students, graduates and engineers
            </span>
            <h1 className="mt-5 text-4xl font-bold leading-[1.08] tracking-tight text-ink sm:text-5xl">
              Your resume, scored against the job you actually want.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-600">
              ResumeIQ reads your resume, compares it with a career-domain skill taxonomy, and tells you
              exactly which keywords, sections and bullets are costing you interviews.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Link to="/signup">
                <Button size="lg">
                  Analyse my resume
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/pricing">
                <Button variant="outline" size="lg">See pricing</Button>
              </Link>
            </div>
            <p className="mt-4 text-xs text-slate-500">Free plan includes 2 analyses a month. No card required.</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="surface p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="label">Analysis preview</p>
                <p className="mt-1 text-sm font-semibold text-ink">Frontend Developer · v3</p>
              </div>
              <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 ring-1 ring-inset ring-amber-200">
                Needs work
              </span>
            </div>
            <div className="mt-5 flex items-center gap-6">
              <ScoreRing score={78} />
              <div className="flex-1 space-y-3">
                {previewScores.map((item) => (
                  <div key={item.label}>
                    <div className="flex items-center justify-between text-xs font-medium text-slate-600">
                      <span>{item.label}</span>
                      <span>{item.score}</span>
                    </div>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-brand-600" style={{ width: `${item.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-5 rounded-xl border border-line bg-canvas p-3.5">
              <p className="text-xs font-semibold text-rose-600">Missing required keywords</p>
              <p className="mt-1 text-xs text-slate-600">TypeScript · Redux · Testing</p>
              <p className="mt-3 text-xs font-semibold text-ink">Suggested rewrite</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">
                “Worked on frontend development” → “Built responsive React interfaces with TypeScript, cutting
                first-paint time by 38%.”
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16">
        <div className="max-w-2xl">
          <p className="label">Why it is different</p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
            A resume reviewer that shows its work.
          </h2>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {pillars.map((pillar) => (
            <div key={pillar.title} className="surface p-5">
              <span className="inline-flex rounded-xl bg-brand-50 p-2 text-brand-600">
                <pillar.icon className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="mt-3 text-base font-semibold text-ink">{pillar.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{pillar.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-canvas">
        <div className="mx-auto max-w-6xl px-5 py-16">
          <p className="label">How it works</p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">Four steps, ten minutes.</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step) => (
              <div key={step.number} className="rounded-2xl border border-line bg-white p-5">
                <span className="font-mono text-xs font-semibold text-brand-600">{step.number}</span>
                <h3 className="mt-2 text-sm font-semibold text-ink">{step.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16">
        <div className="grid gap-8 lg:grid-cols-[1fr_1fr] lg:items-center">
          <div>
            <p className="label">Domain coverage</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
              Taxonomies for the roles you are applying to.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Each domain ships with required, preferred and optional skills with aliases, so “ReactJS”, “React.js”
              and “React” all resolve to one skill. Administrators can edit any taxonomy.
            </p>
            <div className="mt-5 flex flex-wrap gap-2 text-xs font-medium text-slate-600">
              {[
                "Frontend Developer",
                "Backend Developer",
                "Full-Stack Developer",
                "React.js Developer",
                "Python Developer",
                "Java Developer",
                "Software Engineer",
                "UI/UX Designer",
                "Data Analyst",
                "Data Scientist",
                "Cybersecurity Engineer",
                "DevOps Engineer",
                "Digital Marketer",
                "Business Analyst",
                "Project Manager",
              ].map((domain) => (
                <span key={domain} className="rounded-full border border-line bg-white px-3 py-1">
                  {domain}
                </span>
              ))}
            </div>
          </div>
          <div className="surface bg-navy-900 p-7 text-white">
            <BadgeCheck className="h-6 w-6 text-emerald-400" aria-hidden />
            <h3 className="mt-3 text-xl font-semibold text-white">What you get on the free plan</h3>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-300">
              <li>2 full analyses every month</li>
              <li>All seven score dimensions</li>
              <li>Evidence-backed recommendations</li>
              <li>ATS-Friendly and Minimalist templates</li>
            </ul>
            <Link to="/signup" className="mt-6 inline-block">
              <Button variant="primary" size="md">Create a free account</Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-5 py-12 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Ready to see where you stand?</h2>
            <p className="mt-1 text-sm text-slate-600">Upload once. Get a report you can act on today.</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <BarChart3 className="h-4 w-4" aria-hidden />
            Deterministic scoring · Evidence-based advice
          </div>
        </div>
      </section>
    </div>
  );
}
