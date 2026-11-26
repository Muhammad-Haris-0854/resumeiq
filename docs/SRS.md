# ResumeIQ — Software Requirements Specification (SRS)

**Version:** 1.0
**Status:** Approved for Phase 1 delivery
**Owner:** Muhammad Haris
**Last updated:** 2026-11-26

## 1. Purpose

ResumeIQ is a multi-tenant SaaS platform that analyses a candidate's resume against a chosen
career domain (and optionally a specific job description), scores it on measurable dimensions,
and helps the candidate produce a stronger, ATS-readable resume.

This document is the contract for what the system must do. Implementation detail lives in
`docs/architecture.md`, the data model in `docs/database.md`, and the HTTP surface in `docs/api.md`.

## 2. Scope

### 2.1 In scope

- Account creation and authentication (email/password, Google OAuth, verification, recovery).
- Resume upload (PDF/DOCX), secure private storage, versioning, deletion.
- Deterministic document extraction, optional OCR for scanned PDFs.
- Career-domain taxonomy with required / preferred / optional skills.
- AI-assisted analysis: skill detection, missing keywords, weak bullets, grammar and
  formatting observations, rewrite suggestions with evidence.
- Job-description matching with a job-specific match score.
- Multi-dimensional resume scoring with administrator-configurable weights.
- Resume builder with templates, live preview, version history, PDF export.
- Subscription plans, entitlements and usage enforcement.
- User dashboard, admin dashboard, settings, account deletion and data export.

### 2.2 Out of scope (v1)

- Recruiter-side marketplace, candidate sourcing, or employer accounts.
- Native mobile applications (the web app is responsive).
- Automated job applications on the user's behalf.
- AI model training on user documents. Uploaded resumes are never used for training.

## 3. Actors

| Actor | Description | Capabilities |
|---|---|---|
| Guest | Unauthenticated visitor | Landing, features, pricing, signup, login |
| Free | Authenticated, no paid plan | 2 analyses / month, basic scoring, 2 templates |
| Pro | Paid monthly/annual | 20 analyses / month, JD matching, AI rewrite, 5 templates |
| Premium | Paid monthly/annual | 60 analyses / month, all templates, version compare, priority queue |
| Administrator | Platform operator | Domains, taxonomy, templates, plans, users, revenue, system health |

Roles are additive: `administrator` implies Premium entitlements.

## 4. Functional requirements

Requirement identifiers are stable and referenced by tests.

### FR-1 Authentication and accounts

- FR-1.1 Register with email + password; password policy: min 8 chars, 1 letter, 1 digit.
- FR-1.2 Email verification required before the first analysis.
- FR-1.3 Google OAuth sign-in.
- FR-1.4 Password recovery by email link.
- FR-1.5 Session persistence and silent token refresh in the SPA.
- FR-1.6 Logout clears the local session.
- FR-1.7 Account deletion removes profile, resumes, storage objects and analyses (hard delete
  of documents, anonymised audit trail).
- FR-1.8 Roles are stored server-side only (`user_roles`); the client never asserts a role.

### FR-2 Resume intake

- FR-2.1 Drag-and-drop or file-picker upload; PDF and DOCX only; max 5 MB.
- FR-2.2 Client-side MIME + extension check, server-side magic-byte check (never trust the client).
- FR-2.3 Upload progress and explicit processing states: `uploaded → extracting → analysing → ready | failed`.
- FR-2.4 Multiple resumes per user; each has an immutable version history.
- FR-2.5 Private storage bucket; downloads only via short-lived signed URLs.
- FR-2.6 Deletion of a resume deletes its storage object and dependent rows.
- FR-2.7 Uploaded content is untrusted data: it is parsed, never executed, and any
  instruction-like text inside a document is treated as content, not as a command.

### FR-3 Extraction and normalisation

- FR-3.1 Extract raw text with PyMuPDF (PDF) and python-docx (DOCX).
- FR-3.2 If a PDF yields fewer than 80 characters, run OCR (Tesseract) page by page.
- FR-3.3 Normalise into a structured profile: name, email, phone, links, summary,
  technical skills, soft skills, experience[], education[], projects[], certifications[],
  languages[], achievements[].
- FR-3.4 Both raw text and structured data are persisted so a re-analysis never re-parses
  the original file unnecessarily.
- FR-3.5 A file that cannot be parsed fails with an actionable message, not a 500.

### FR-4 Domain and taxonomy management

- FR-4.1 The user selects a career domain before analysis.
- FR-4.2 Each domain has skills tagged `required | preferred | optional` with a weight.
- FR-4.3 Administrators can create, edit, archive domains and edit their skill sets.
- FR-4.4 Skill aliases (e.g. "ReactJS", "React.js", "react") resolve to one canonical skill.

### FR-5 Analysis

- FR-5.1 Detect technical skills, soft skills, missing keywords, weakly demonstrated skills,
  irrelevant keywords, repetition, grammar issues, spelling issues, weak descriptions,
  missing sections, formatting issues and ATS readability issues.
- FR-5.2 Classify each taxonomy skill as `found | partial | missing | recommended`.
- FR-5.3 Every recommendation carries evidence (the quoted source text or the absence that
  triggered it) and a rationale.
- FR-5.4 Never recommend claiming a skill the resume does not evidence; missing skills are
  phrased conditionally ("If you have hands-on REST API experience…").
- FR-5.5 Suggestions can be accepted, rejected or edited; originals are never overwritten.
- FR-5.6 Re-analysis creates a new analysis record; previous reports stay comparable.

### FR-6 Job description matching

- FR-6.1 Paste a job description (max 20 000 chars) and match it against a resume.
- FR-6.2 Extract required skills, soft skills, years of experience, education requirements,
  and high-signal keywords.
- FR-6.3 Report matched / partially matched / missing requirements and a match score
  presented as a similarity indicator, never as a probability of being hired.

### FR-7 Scoring

- FR-7.1 Produce: overall, keyword match, technical skills, ATS compatibility, content quality,
  grammar, formatting, experience relevance.
- FR-7.2 Measurable dimensions are computed deterministically in Python; the LLM may only
  supply qualitative observations that feed bounded adjustments.
- FR-7.3 Default weights: keyword 20, technical 20, ATS 15, content 15, grammar 10,
  formatting 10, experience 10. Administrators can change them; weights must sum to 100.
- FR-7.4 Every score is accompanied by the inputs that produced it.

### FR-8 Builder

- FR-8.1 Create a resume from scratch or from an imported resume.
- FR-8.2 Edit every section, add custom sections, reorder, remove, live preview, autosave.
- FR-8.3 Seven templates: ATS-Friendly, Modern Professional, Software Developer,
  Fresh Graduate, Experienced Professional, Creative Designer, Minimalist.
- FR-8.4 Server-side PDF export from the same render model the preview uses.
- FR-8.5 Version history with restore.

### FR-9 Subscriptions and entitlements

- FR-9.1 Plans: Free, Pro, Premium; monthly and annual intervals.
- FR-9.2 Upgrade, downgrade, cancel; access continues until period end.
- FR-9.3 Usage is metered per calendar month against the plan's analysis quota.
- FR-9.4 Quotas and feature entitlements are enforced server-side on every request.
- FR-9.5 Payment events are verified server-side by webhook signature; frontend success
  screens are never authoritative.
- FR-9.6 Invoices and payment history are visible to the user.

### FR-10 Dashboards

- FR-10.1 User dashboard: totals, latest score, recent activity, quota, plan, quick actions.
- FR-10.2 Admin dashboard: users, paid/free split, MRR, analyses, AI usage, error rates,
  domain and template management, user role management.
- FR-10.3 Admin endpoints require a server-side role check on every call.

## 5. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | p95 API latency < 400 ms for non-AI endpoints; AI work is asynchronous. |
| NFR-2 | No API request blocks on LLM or OCR work; jobs run on Celery workers. |
| NFR-3 | All user data isolated by Postgres RLS and re-checked in the API layer. |
| NFR-4 | Every table has UUID PKs, created_at/updated_at, FKs and indexes on lookup columns. |
| NFR-5 | Secrets only in environment variables; `.env` is git-ignored; `.env.example` has placeholders. |
| NFR-6 | WCAG 2.1 AA contrast, keyboard navigable, visible focus states. |
| NFR-7 | Responsive from 360 px to 1920 px. |
| NFR-8 | Structured JSON logs with request ids; errors reported with a correlation id. |
| NFR-9 | Horizontal scaling: stateless API, shared Redis, Supabase-managed Postgres. |
| NFR-10 | Tests cover scoring, extraction, taxonomy matching, auth, RLS and webhook verification. |

## 6. Assumptions and decisions

- **A-1** Supabase is the system of record for auth, files and relational data.
- **A-2** The AI provider is chosen behind an abstraction (`app/services/ai/`). v1 ships an
  OpenAI-compatible provider plus a deterministic offline provider used by tests and by
  deployments without a key.
- **A-3** Payments are behind a provider abstraction. Because gateway availability in the
  target market is not confirmed, v1 ships a fully working `mock` provider and a Stripe
  adapter skeleton, both driven by the same `PaymentProvider` interface. See ADR-004.
- **A-4** PDF export uses WeasyPrint-compatible HTML rendering with a ReportLab fallback.

## 7. Acceptance criteria for v1

1. A new user can register, verify, pick a domain, upload a PDF, and receive a scored report
   with evidence-backed recommendations.
2. Free-tier quota is enforced on the third attempt in a month.
3. A second user cannot read the first user's resume by id, file path, or signed URL.
4. Re-analysing a resume produces a second comparable report without mutating the first.
5. `pytest` and `npm run build` pass in CI.
