"""Domain enums shared by services and repositories."""

from __future__ import annotations

from enum import StrEnum


class PlanCode(StrEnum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class Role(StrEnum):
    USER = "user"
    ADMINISTRATOR = "administrator"


class RequirementLevel(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"


class SkillStatus(StrEnum):
    FOUND = "found"
    PARTIAL = "partial"
    MISSING = "missing"
    RECOMMENDED = "recommended"


class IssueCategory(StrEnum):
    KEYWORD = "keyword"
    SKILL = "skill"
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    FORMATTING = "formatting"
    ATS = "ats"
    CONTENT = "content"
    SECTION = "section"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueStatus(StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


SCORE_KEYS: tuple[str, ...] = (
    "keyword_match",
    "technical_skills",
    "ats_compatibility",
    "content_quality",
    "grammar",
    "formatting",
    "experience_relevance",
)

DEFAULT_WEIGHTS: dict[str, int] = {
    "keyword_match": 20,
    "technical_skills": 20,
    "ats_compatibility": 15,
    "content_quality": 15,
    "grammar": 10,
    "formatting": 10,
    "experience_relevance": 10,
}

PLAN_FEATURES: dict[PlanCode, dict[str, object]] = {
    PlanCode.FREE: {
        "jd_matching": False,
        "ai_rewrite": False,
        "version_compare": False,
        "priority_queue": False,
        "analysis_quota": 2,
        "max_resumes": 2,
        "templates": ["ats-friendly", "minimalist"],
    },
    PlanCode.PRO: {
        "jd_matching": True,
        "ai_rewrite": True,
        "version_compare": True,
        "priority_queue": False,
        "analysis_quota": 20,
        "max_resumes": 10,
        "templates": [
            "ats-friendly",
            "minimalist",
            "modern-professional",
            "software-developer",
            "fresh-graduate",
        ],
    },
    PlanCode.PREMIUM: {
        "jd_matching": True,
        "ai_rewrite": True,
        "version_compare": True,
        "priority_queue": True,
        "analysis_quota": 60,
        "max_resumes": 30,
        "templates": [
            "ats-friendly",
            "minimalist",
            "modern-professional",
            "software-developer",
            "fresh-graduate",
            "experienced-professional",
            "creative-designer",
        ],
    },
}
