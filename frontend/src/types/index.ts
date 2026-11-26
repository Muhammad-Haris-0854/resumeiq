/** Shared contracts mirroring docs/api.md. Keep in step with backend/app/schemas/core.py. */

export type PlanCode = "free" | "pro" | "premium";
export type Role = "user" | "administrator";
export type JobStatus = "queued" | "running" | "ready" | "failed";
export type SkillStatus = "found" | "partial" | "missing" | "recommended";
export type RequirementLevel = "required" | "preferred" | "optional";
export type Severity = "low" | "medium" | "high";
export type IssueStatus = "open" | "accepted" | "rejected" | "edited";

export interface ApiErrorBody {
  error: { code: string; message: string; details?: Record<string, unknown>; request_id?: string };
}

export interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  headline: string | null;
  career_domain_id: string | null;
  plan: PlanCode;
  onboarding_completed: boolean;
  created_at: string | null;
}

export interface Entitlements {
  plan: PlanCode;
  role: Role;
  analysis_quota: number;
  analyses_used: number;
  analyses_remaining: number;
  max_resumes: number;
  features: {
    jd_matching?: boolean;
    ai_rewrite?: boolean;
    version_compare?: boolean;
    priority_queue?: boolean;
    templates?: string[];
  };
  period_start: string;
}

export interface Me {
  profile: Profile;
  entitlements: Entitlements;
}

export interface Resume {
  id: string;
  title: string;
  status: "uploaded" | "extracting" | "extracted" | "failed" | "archived";
  source: "upload" | "builder";
  career_domain_id: string | null;
  current_version_id: string | null;
  created_at: string;
  updated_at: string | null;
  latest_score: number | null;
}

export interface ResumeVersion {
  id: string;
  version: number;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  page_count: number | null;
  extraction_method: string | null;
  created_at: string;
}

export interface ResumeDetail extends Resume {
  versions: ResumeVersion[];
  extracted: Record<string, unknown> | null;
}

export interface ScoreDetail {
  key: string;
  label: string;
  score: number;
  weight: number;
  explanation: string;
  inputs: Record<string, unknown>;
}

export interface Issue {
  id: string;
  category: string;
  severity: Severity;
  title: string;
  detail: string | null;
  evidence: string | null;
  suggestion: string | null;
  status: IssueStatus;
  user_edit: string | null;
}

export interface SkillBreakdown {
  skill: string;
  status: SkillStatus;
  requirement: RequirementLevel;
  evidence: string | null;
}

export interface Analysis {
  id: string;
  resume_id: string;
  resume_version_id: string;
  career_domain_id: string | null;
  job_description_id: string | null;
  status: JobStatus;
  overall_score: number | null;
  scores: ScoreDetail[];
  summary: string | null;
  strengths: string[];
  weaknesses: string[];
  detected_skills: string[];
  missing_keywords: string[];
  skill_breakdown: SkillBreakdown[];
  issues: Issue[];
  ai_model: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface Domain {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  skill_count: number;
}

export interface DomainSkill {
  id: string;
  canonical_name: string;
  kind: string;
  category: string | null;
  requirement: RequirementLevel;
  weight: number;
}

export interface DomainDetail extends Domain {
  skills: DomainSkill[];
}

export interface Template {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  tier: string;
  is_ats_safe: boolean;
  layout: Record<string, unknown>;
  locked: boolean;
}

export interface JobRequirement {
  label: string;
  requirement: RequirementLevel;
  evidence: string | null;
}

export interface JobMatch {
  id: string;
  status: JobStatus;
  match_score: number | null;
  matched: JobRequirement[];
  partial: JobRequirement[];
  missing: JobRequirement[];
  recommendations: string[];
  created_at: string;
}

export interface ResumeContent {
  full_name: string;
  headline: string;
  email: string;
  phone: string;
  location: string;
  links: string[];
  summary: string;
  skills: string[];
  experience: Array<{
    title: string;
    company: string;
    location: string;
    start_date: string;
    end_date: string;
    bullets: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    location: string;
    start_date: string;
    end_date: string;
    details: string;
  }>;
  projects: Array<{ name: string; description: string; link: string; technologies: string[] }>;
  certifications: string[];
  achievements: string[];
  languages: string[];
  custom_sections: Record<string, string[]>;
  section_order: string[];
}

export interface GeneratedResume {
  id: string;
  title: string;
  template_id: string;
  resume_id: string | null;
  version: number;
  status: JobStatus;
  content: ResumeContent;
  pdf_url: string | null;
  updated_at: string | null;
}

export interface Plan {
  id: string | null;
  code: PlanCode;
  name: string;
  description: string | null;
  monthly_price_cents: number;
  annual_price_cents: number;
  analysis_quota: number;
  max_resumes: number;
  features: Record<string, unknown>;
}

export interface Subscription {
  plan: PlanCode;
  status: string;
  interval: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  provider: string | null;
}

export interface Invoice {
  id: string;
  amount_cents: number;
  currency: string;
  status: string;
  description: string | null;
  invoice_url: string | null;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminMetrics {
  total_users: number;
  paid_users: number;
  free_users: number;
  active_subscriptions: number;
  mrr_cents: number;
  analyses_this_month: number;
  ai_tokens_this_month: number;
  failed_analyses_this_month: number;
  queue_depth?: number | null;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  plan: PlanCode;
  role: Role;
  created_at: string;
}
