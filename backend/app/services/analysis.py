"""Analysis orchestration.

`compose_report` is pure: given a context and a provider it returns the report payload. That is
what tests exercise. `run_analysis` performs the I/O around it and is what the worker calls.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.models.enums import DEFAULT_WEIGHTS, IssueCategory, RequirementLevel, Severity, SkillStatus
from app.repositories.base import Repositories
from app.services.ai.base import AIProvider, AIProviderError
from app.services.ai.prompts import ANALYSIS_SCHEMA, ANALYSIS_SYSTEM, build_analysis_user
from app.services.scoring import ScoreInputs, compute_scores, score_band, summarise
from app.services.taxonomy import SkillMatch, SkillRow, match_domain_skills, weighted_coverage

logger = get_logger(__name__)

EXPECTED_SECTIONS: dict[str, set[str]] = {
    "default": {"summary", "skills", "experience", "education"},
    "fresh": {"summary", "skills", "education", "projects"},
}
WEAK_PHRASES = ("responsible for", "worked on", "helped with", "assisted in", "duties included", "involved in")


def build_skill_rows(domain_skills: list[dict[str, Any]]) -> list[SkillRow]:
    rows: list[SkillRow] = []
    for item in domain_skills:
        rows.append(
            SkillRow(
                canonical_name=str(item["canonical_name"]),
                aliases=tuple(item.get("aliases") or ()),
                requirement=RequirementLevel(item.get("requirement", "required")),
                weight=float(item.get("weight") or 1.0),
                kind=str(item.get("kind") or "technical"),
            )
        )
    return rows


def build_context(
    *,
    resume_text: str,
    extracted: dict[str, Any],
    domain: dict[str, Any],
    matches: list[SkillMatch],
    target_years: float = 0.0,
) -> dict[str, Any]:
    required = [m for m in matches if m.requirement is RequirementLevel.REQUIRED]
    preferred = [m for m in matches if m.requirement is RequirementLevel.PREFERRED]
    weak_bullets = [
        bullet for bullet in extracted.get("bullets", []) if any(p in bullet.lower() for p in WEAK_PHRASES)
    ][:8]
    bullets = extracted.get("bullets", []) or []
    quantified_ratio = (extracted.get("quantified_bullets", 0) / len(bullets)) if bullets else 0.0
    expected = EXPECTED_SECTIONS["fresh"] if "projects" in (extracted.get("sections_present") or []) and not extracted.get("experience") else EXPECTED_SECTIONS["default"]

    return {
        "domain_name": domain.get("name", ""),
        "domain_slug": domain.get("slug", ""),
        "required_skills": [m.skill for m in required],
        "preferred_skills": [m.skill for m in preferred],
        "found_skills": [m.skill for m in matches if m.status is SkillStatus.FOUND],
        "partial_skills": [m.skill for m in matches if m.status is SkillStatus.PARTIAL],
        "missing_required": [m.skill for m in required if m.status is SkillStatus.MISSING],
        "missing_preferred": [m.skill for m in preferred if m.status is SkillStatus.MISSING],
        "required_coverage": round(weighted_coverage(matches, requirement=RequirementLevel.REQUIRED), 3),
        "sections_present": extracted.get("sections_present", []),
        "required_sections": sorted(expected),
        "weak_bullets": weak_bullets,
        "quantified_ratio": round(quantified_ratio, 3),
        "formatting_flags": extracted.get("formatting_flags", []),
        "ats_flags": extracted.get("ats_flags", []),
        "grammar_issues": extracted.get("grammar_issues", [])[:8],
        "spelling_issues": extracted.get("spelling_issues", [])[:8],
        "years_experience": extracted.get("years_experience", 0.0),
        "target_years": target_years,
        "word_count": extracted.get("word_count", 0),
        "bullet_count": len(bullets),
        "deterministic_strengths": [
            s for s in extracted.get("_strengths", []) if isinstance(s, str)
        ],
        "deterministic_weaknesses": [],
        "resume_text": resume_text,
    }


def _normalise_ai_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Clamp and coerce anything the model returns into the contract."""
    issues: list[dict[str, Any]] = []
    for raw in payload.get("issues", [])[:20]:
        category = str(raw.get("category", "content")).lower()
        severity = str(raw.get("severity", "medium")).lower()
        issues.append(
            {
                "category": category if category in {c.value for c in IssueCategory} else "content",
                "severity": severity if severity in {s.value for s in Severity} else "medium",
                "title": str(raw.get("title", ""))[:140] or "Observation",
                "detail": str(raw.get("detail", ""))[:600],
                "evidence": str(raw.get("evidence", ""))[:400],
                "suggestion": str(raw.get("suggestion", ""))[:600],
            }
        )
    return {
        "summary": str(payload.get("summary", ""))[:600],
        "strengths": [str(s)[:200] for s in payload.get("strengths", [])][:5],
        "weaknesses": [str(s)[:200] for s in payload.get("weaknesses", [])][:5],
        "issues": issues,
        "rewrites": payload.get("rewrites", [])[:5],
        "content_adjustment": max(-8, min(8, int(payload.get("content_adjustment", 0) or 0))),
        "experience_adjustment": max(-5, min(5, int(payload.get("experience_adjustment", 0) or 0))),
    }


def compose_report(
    *,
    context: dict[str, Any],
    extracted: dict[str, Any],
    matches: list[SkillMatch],
    provider: AIProvider,
    weights: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Deterministic scores + schema-validated qualitative review."""
    ai_payload: dict[str, Any] | None = None
    ai_error: str | None = None
    try:
        ai_payload = provider.complete_json(
            task="resume_analysis",
            system=ANALYSIS_SYSTEM,
            user=build_analysis_user(context),
            schema=ANALYSIS_SCHEMA,
        )
        ai_payload = _normalise_ai_payload(ai_payload)
    except AIProviderError as exc:
        ai_error = str(exc)
        logger.warning("ai_analysis_fallback", extra={"extra_fields": {"reason": ai_error}})
        fallback = provider.__class__.__name__
        ai_payload = _normalise_ai_payload(
            {
                "summary": "Scored from measurable inputs; the AI review was unavailable.",
                "strengths": [],
                "weaknesses": [],
                "issues": [],
                "rewrites": [],
                "content_adjustment": 0,
                "experience_adjustment": 0,
            }
        )
        ai_payload["_fallback"] = fallback

    experience_text = " ".join(
        f"{entry.get('title', '')} {entry.get('company', '')} {' '.join(entry.get('bullets', []))}"
        for entry in extracted.get("experience", [])
    )
    domain_terms = [m.skill for m in matches]
    if domain_terms and experience_text:
        lowered = experience_text.lower()
        hits = sum(1 for term in domain_terms if term.lower() in lowered)
        overlap = hits / len(domain_terms)
    else:
        overlap = 0.0

    bullets = extracted.get("bullets", []) or []
    weak_count = len([b for b in bullets if any(p in b.lower() for p in WEAK_PHRASES)])

    score_inputs = ScoreInputs(
        skill_matches=matches,
        sections_present=set(context.get("sections_present", [])),
        required_sections=set(context.get("required_sections", [])),
        word_count=int(extracted.get("word_count", 0)),
        bullet_count=len(bullets),
        quantified_bullets=int(extracted.get("quantified_bullets", 0)),
        weak_bullets=weak_count,
        grammar_issues=len(extracted.get("grammar_issues", [])),
        spelling_issues=len(extracted.get("spelling_issues", [])),
        formatting_flags=list(extracted.get("formatting_flags", [])),
        ats_flags=list(extracted.get("ats_flags", [])),
        years_experience=float(extracted.get("years_experience", 0.0)),
        target_years=float(context.get("target_years", 0.0)),
        experience_keyword_overlap=overlap,
        ai_content_adjustment=ai_payload["content_adjustment"],
        ai_experience_adjustment=ai_payload["experience_adjustment"],
        has_contact_block=bool(extracted.get("has_contact_block", True)),
    )
    report = compute_scores(score_inputs, weights or DEFAULT_WEIGHTS)
    strengths, weaknesses = summarise(report, matches)
    strengths = list(dict.fromkeys(ai_payload["strengths"] + strengths))[:5]
    weaknesses = list(dict.fromkeys(ai_payload["weaknesses"] + weaknesses))[:5]

    issues = list(ai_payload["issues"])
    for rewrite in ai_payload.get("rewrites", []):
        issues.append(
            {
                "category": "content",
                "severity": "medium",
                "title": "Suggested rewrite",
                "detail": "Stronger phrasing that keeps the same facts.",
                "evidence": str(rewrite.get("original", ""))[:400],
                "suggestion": str(rewrite.get("improved", ""))[:600],
            }
        )
    missing_required = [m.skill for m in matches if m.requirement is RequirementLevel.REQUIRED and m.status is SkillStatus.MISSING]
    missing_keywords = missing_required + [
        m.skill
        for m in matches
        if m.requirement is not RequirementLevel.REQUIRED and m.status is SkillStatus.MISSING
    ]

    return {
        "overall_score": report.overall,
        "band": score_band(report.overall),
        "scores": [asdict(detail) for detail in report.details],
        "summary": ai_payload["summary"],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "detected_skills": [m.skill for m in matches if m.status is not SkillStatus.MISSING],
        "missing_keywords": missing_keywords[:20],
        "skill_breakdown": [
            {
                "skill": m.skill,
                "status": m.status.value,
                "requirement": m.requirement.value,
                "evidence": m.evidence,
            }
            for m in matches
        ],
        "issues": issues,
        "ai_model": provider.model,
        "ai_tokens_used": provider.tokens_used,
        "ai_fallback": "_fallback" in ai_payload,
    }


def run_analysis(
    repos: Repositories,
    *,
    analysis_id: str,
    provider: AIProvider,
    weights: dict[str, int] | None = None,
) -> None:
    """Worker entry point: load, analyse, persist. Idempotent per analysis id."""
    started = time.perf_counter()
    analysis = None
    try:
        analysis = repos.analyses.get_by_id(analysis_id) if hasattr(repos.analyses, "get_by_id") else None
    except Exception:  # pragma: no cover - repository without the helper
        analysis = None
    if analysis is None:
        analysis = _load_analysis(repos, analysis_id)
    if analysis is None:
        logger.warning("analysis_missing", extra={"extra_fields": {"analysis_id": analysis_id}})
        return
    if analysis.get("status") in {"ready", "failed"}:
        return

    repos.analyses.update(analysis_id, {"status": "running"})
    try:
        version = repos.resumes.get_version(analysis["resume_version_id"])
        if not version:
            raise ValueError("resume version not found")
        extracted = version.get("extracted") or {}
        domain = repos.taxonomy.get_domain(analysis["career_domain_id"]) if analysis.get("career_domain_id") else None
        domain_skills = repos.taxonomy.domain_skills(analysis["career_domain_id"]) if analysis.get("career_domain_id") else []
        matches = match_domain_skills(version.get("raw_text") or "", build_skill_rows(domain_skills))
        context = build_context(
            resume_text=version.get("raw_text") or "",
            extracted=extracted,
            domain=domain or {},
            matches=matches,
        )
        result = compose_report(
            context=context,
            extracted=extracted,
            matches=matches,
            provider=provider,
            weights=weights,
        )
        repos.analyses.update(
            analysis_id,
            {
                "status": "ready",
                "overall_score": result["overall_score"],
                "scores": result["scores"],
                "summary": result["summary"],
                "strengths": result["strengths"],
                "weaknesses": result["weaknesses"],
                "detected_skills": result["detected_skills"],
                "missing_keywords": result["missing_keywords"],
                "skill_breakdown": result["skill_breakdown"],
                "ai_model": result["ai_model"],
                "ai_tokens_used": result["ai_tokens_used"],
                "completed_at": datetime.now(UTC).isoformat(),
                "duration_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        repos.analyses.add_issues(
            analysis_id,
            [
                {
                    "category": issue["category"],
                    "severity": issue["severity"],
                    "title": issue["title"],
                    "detail": issue["detail"],
                    "evidence": issue["evidence"],
                    "suggestion": issue["suggestion"],
                    "sort_order": index,
                }
                for index, issue in enumerate(result["issues"])
            ],
        )
    except Exception as exc:  # keep the record actionable rather than silent
        logger.exception("analysis_failed", extra={"extra_fields": {"analysis_id": analysis_id}})
        repos.analyses.update(
            analysis_id,
            {
                "status": "failed",
                "error_code": "ANALYSIS_FAILED",
                "error_message": str(exc)[:400],
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
        raise


def _load_analysis(repos: Repositories, analysis_id: str) -> dict[str, Any] | None:
    """Loads an analysis without a user scope (worker context)."""
    client = getattr(repos.analyses, "_client", None)
    if client is None:
        return None
    response = client.table("resume_analyses").select("*").eq("id", analysis_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None
