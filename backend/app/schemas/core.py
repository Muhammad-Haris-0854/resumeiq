"""Request/response contracts. `extra="forbid"` everywhere so typos fail loudly."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    IssueCategory,
    IssueStatus,
    JobStatus,
    PlanCode,
    RequirementLevel,
    Role,
    Severity,
    SkillStatus,
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Pagination(Strict):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


# --- account ----------------------------------------------------------------


class ProfileOut(BaseModel):
    id: UUID
    email: str
    full_name: str | None = None
    headline: str | None = None
    career_domain_id: UUID | None = None
    plan: PlanCode
    onboarding_completed: bool = False
    created_at: datetime | None = None


class EntitlementsOut(BaseModel):
    plan: PlanCode
    role: Role
    analysis_quota: int
    analyses_used: int
    analyses_remaining: int
    max_resumes: int
    features: dict[str, Any]
    period_start: str


class MeOut(BaseModel):
    profile: ProfileOut
    entitlements: EntitlementsOut


class ProfileUpdate(Strict):
    full_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    career_domain_id: UUID | None = None
    onboarding_completed: bool | None = None


# --- resumes ----------------------------------------------------------------


class ResumeOut(BaseModel):
    id: UUID
    title: str
    status: str
    source: str
    career_domain_id: UUID | None = None
    current_version_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    latest_score: int | None = None


class ResumeVersionOut(BaseModel):
    id: UUID
    version: int
    file_name: str
    mime_type: str
    size_bytes: int
    page_count: int | None = None
    extraction_method: str | None = None
    created_at: datetime


class ResumeDetailOut(ResumeOut):
    versions: list[ResumeVersionOut] = Field(default_factory=list)
    extracted: dict[str, Any] | None = None


class ResumeUpdate(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    career_domain_id: UUID | None = None


class SignedUrlOut(BaseModel):
    url: str
    expires_in: int


# --- taxonomy ---------------------------------------------------------------


class SkillOut(BaseModel):
    id: UUID
    canonical_name: str
    kind: str
    category: str | None = None


class DomainSkillOut(SkillOut):
    requirement: RequirementLevel
    weight: float


class DomainOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    skill_count: int = 0


class DomainDetailOut(DomainOut):
    skills: list[DomainSkillOut] = Field(default_factory=list)


# --- analysis ---------------------------------------------------------------


class SkillBreakdownItem(BaseModel):
    skill: str
    status: SkillStatus
    requirement: RequirementLevel
    evidence: str | None = None


class ScoreDetail(BaseModel):
    key: str
    label: str
    score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0, le=100)
    explanation: str
    inputs: dict[str, Any] = Field(default_factory=dict)


class IssueOut(BaseModel):
    id: UUID
    category: IssueCategory
    severity: Severity
    title: str
    detail: str | None = None
    evidence: str | None = None
    suggestion: str | None = None
    status: IssueStatus = IssueStatus.OPEN
    user_edit: str | None = None


class AnalysisOut(BaseModel):
    id: UUID
    resume_id: UUID
    resume_version_id: UUID
    career_domain_id: UUID | None = None
    job_description_id: UUID | None = None
    status: JobStatus
    overall_score: int | None = None
    scores: list[ScoreDetail] = Field(default_factory=list)
    summary: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    detected_skills: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    skill_breakdown: list[SkillBreakdownItem] = Field(default_factory=list)
    issues: list[IssueOut] = Field(default_factory=list)
    ai_model: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisCreate(Strict):
    resume_version_id: UUID
    career_domain_id: UUID
    job_description_id: UUID | None = None


class IssueUpdate(Strict):
    status: Literal["open", "accepted", "rejected", "edited"]
    user_edit: str | None = Field(default=None, max_length=2000)


class ComparisonOut(BaseModel):
    base_id: UUID
    compare_id: UUID
    overall_delta: int
    deltas: dict[str, int]


# --- job matching -----------------------------------------------------------


class JobMatchCreate(Strict):
    resume_version_id: UUID
    title: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    raw_text: str = Field(min_length=40, max_length=20000)


class JobRequirementOut(BaseModel):
    label: str
    requirement: RequirementLevel = RequirementLevel.REQUIRED
    evidence: str | None = None


class JobMatchOut(BaseModel):
    id: UUID
    status: JobStatus
    match_score: int | None = None
    matched: list[JobRequirementOut] = Field(default_factory=list)
    partial: list[JobRequirementOut] = Field(default_factory=list)
    missing: list[JobRequirementOut] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime


# --- builder ----------------------------------------------------------------


class TemplateOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None = None
    tier: str
    is_ats_safe: bool
    layout: dict[str, Any] = Field(default_factory=dict)
    locked: bool = False


class ExperienceItem(Strict):
    title: str = Field(default="", max_length=160)
    company: str = Field(default="", max_length=160)
    location: str = Field(default="", max_length=120)
    start_date: str = Field(default="", max_length=40)
    end_date: str = Field(default="", max_length=40)
    bullets: list[str] = Field(default_factory=list)


class EducationItem(Strict):
    degree: str = Field(default="", max_length=160)
    institution: str = Field(default="", max_length=160)
    location: str = Field(default="", max_length=120)
    start_date: str = Field(default="", max_length=40)
    end_date: str = Field(default="", max_length=40)
    details: str = Field(default="", max_length=600)


class ProjectItem(Strict):
    name: str = Field(default="", max_length=160)
    description: str = Field(default="", max_length=1200)
    link: str = Field(default="", max_length=300)
    technologies: list[str] = Field(default_factory=list)


class ResumeContent(Strict):
    full_name: str = Field(default="", max_length=120)
    headline: str = Field(default="", max_length=160)
    email: str = Field(default="", max_length=160)
    phone: str = Field(default="", max_length=60)
    location: str = Field(default="", max_length=120)
    links: list[str] = Field(default_factory=list)
    summary: str = Field(default="", max_length=1200)
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    custom_sections: dict[str, list[str]] = Field(default_factory=dict)
    section_order: list[str] = Field(
        default_factory=lambda: ["summary", "skills", "experience", "education", "projects"]
    )


class GeneratedResumeCreate(Strict):
    template_id: UUID
    title: str = Field(min_length=1, max_length=120)
    resume_version_id: UUID | None = None
    content: ResumeContent | None = None


class GeneratedResumeOut(BaseModel):
    id: UUID
    title: str
    template_id: UUID
    resume_id: UUID | None = None
    version: int
    status: JobStatus
    content: ResumeContent
    pdf_url: str | None = None
    updated_at: datetime | None = None


# --- billing ----------------------------------------------------------------


class PlanOut(BaseModel):
    id: UUID | None = None
    code: str
    name: str
    description: str | None = None
    monthly_price_cents: int
    annual_price_cents: int
    analysis_quota: int
    max_resumes: int
    features: dict[str, Any] = Field(default_factory=dict)


class SubscriptionOut(BaseModel):
    plan: PlanCode
    status: str
    interval: str | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    provider: str | None = None


class CheckoutRequest(Strict):
    plan_code: Literal["pro", "premium"]
    interval: Literal["month", "year"] = "month"


class CheckoutOut(BaseModel):
    checkout_url: str
    session_id: str


class InvoiceOut(BaseModel):
    id: UUID
    amount_cents: int
    currency: str
    status: str
    description: str | None = None
    invoice_url: str | None = None
    created_at: datetime


# --- admin ------------------------------------------------------------------


class AdminMetricsOut(BaseModel):
    total_users: int
    paid_users: int
    free_users: int
    active_subscriptions: int
    mrr_cents: int
    analyses_this_month: int
    ai_tokens_this_month: int
    failed_analyses_this_month: int
    queue_depth: int | None = None


class AdminUserOut(BaseModel):
    id: UUID
    email: str
    full_name: str | None = None
    plan: PlanCode
    role: Role
    created_at: datetime


class AdminUserUpdate(Strict):
    role: Literal["user", "administrator"] | None = None
    plan: Literal["free", "pro", "premium"] | None = None


class DomainWrite(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]{2,60}$")
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=400)
    icon: str | None = Field(default=None, max_length=60)
    is_active: bool = True


class DomainSkillsWrite(Strict):
    skills: list[dict[str, Any]]

    @field_validator("skills")
    @classmethod
    def _validate(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            if "skill_id" not in item:
                raise ValueError("each entry needs skill_id")
            if item.get("requirement", "required") not in {"required", "preferred", "optional"}:
                raise ValueError("requirement must be required, preferred or optional")
        return value


class ScoringWeights(Strict):
    keyword_match: int = Field(ge=0, le=100)
    technical_skills: int = Field(ge=0, le=100)
    ats_compatibility: int = Field(ge=0, le=100)
    content_quality: int = Field(ge=0, le=100)
    grammar: int = Field(ge=0, le=100)
    formatting: int = Field(ge=0, le=100)
    experience_relevance: int = Field(ge=0, le=100)

    @field_validator("experience_relevance")
    @classmethod
    def _sum(cls, value: int, info: Any) -> int:
        data = info.data
        total = sum(data.get(key, 0) for key in (
            "keyword_match",
            "technical_skills",
            "ats_compatibility",
            "content_quality",
            "grammar",
            "formatting",
        )) + value
        if total != 100:
            raise ValueError(f"weights must sum to 100, got {total}")
        return value
