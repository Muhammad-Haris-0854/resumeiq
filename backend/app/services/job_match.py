"""Job-description parsing and matching.

The match score is a similarity indicator between the posting and the resume, not a hiring
probability, and the API says so in the response.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.services.ai.base import AIProvider, AIProviderError
from app.services.ai.prompts import JD_SCHEMA, JD_SYSTEM, build_jd_user
from app.services.taxonomy import SkillRow, find_mentions

logger = get_logger(__name__)

DISCLAIMER = (
    "This score measures how closely the resume matches the posting's stated requirements. "
    "It is not a probability of being hired."
)


def _catalog_rows(catalog: list[dict[str, Any]]) -> list[SkillRow]:
    return [
        SkillRow(
            canonical_name=str(entry["canonical_name"]),
            aliases=tuple(entry.get("aliases") or ()),
            kind=str(entry.get("kind") or "technical"),
        )
        for entry in catalog
    ]


def parse_job_description(
    raw_text: str, provider: AIProvider, catalog: list[dict[str, Any]]
) -> dict[str, Any]:
    """Structured requirements from a posting, with a deterministic fallback."""
    try:
        parsed = provider.complete_json(
            task="jd_parse",
            system=JD_SYSTEM,
            user=build_jd_user(raw_text),
            schema=JD_SCHEMA,
        )
        required = [str(s)[:60] for s in parsed.get("required_skills", [])][:30]
        soft = [str(s)[:60] for s in parsed.get("soft_skills", [])][:15]
        keywords = [str(s)[:60] for s in parsed.get("keywords", [])][:30]
        years = float(parsed.get("years_experience", 0) or 0)
        education = [str(s)[:120] for s in parsed.get("education", [])][:5]
    except AIProviderError as exc:
        logger.warning("jd_parse_fallback", extra={"extra_fields": {"reason": str(exc)}})
        required, soft, years, education = _deterministic_parse(raw_text, catalog)
        keywords = [s.lower() for s in required[:20]]

    if not required:
        required, soft, years, education = _deterministic_parse(raw_text, catalog)
        keywords = keywords or [s.lower() for s in required[:20]]

    return {
        "required_skills": required,
        "soft_skills": soft,
        "keywords": keywords,
        "years_experience": min(years, 40.0),
        "education": education,
    }


def _deterministic_parse(
    raw_text: str, catalog: list[dict[str, Any]]
) -> tuple[list[str], list[str], float, list[str]]:
    import re

    required: list[str] = []
    soft: list[str] = []
    for skill in _catalog_rows(catalog):
        if find_mentions(raw_text, skill):
            (soft if skill.kind == "soft" else required).append(skill.canonical_name)
    years = 0.0
    matches = re.findall(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", raw_text, re.I)
    if matches:
        years = float(max(int(m) for m in matches))
    education = [
        e.strip()[:120]
        for e in re.findall(r"(bachelor[^.\n]{0,60}|master[^.\n]{0,60}|degree in [^.\n]{0,60})", raw_text, re.I)
    ][:5]
    return required[:30], soft[:15], years, education


def compute_match(
    *,
    resume_text: str,
    extracted: dict[str, Any],
    parsed: dict[str, Any],
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = {row.canonical_name: row for row in _catalog_rows(catalog)}
    matched: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for name in parsed.get("required_skills", []):
        row = rows.get(name)
        if row is None:
            continue
        hits = find_mentions(resume_text, row)
        entry = {"label": name, "requirement": "required", "evidence": hits[0][1][:300] if hits else None}
        if len(hits) >= 2:
            matched.append(entry)
        elif len(hits) == 1:
            partial.append(entry)
        else:
            missing.append(entry)

    for name in parsed.get("soft_skills", []):
        row = rows.get(name)
        if row is None:
            continue
        hits = find_mentions(resume_text, row)
        entry = {"label": name, "requirement": "preferred", "evidence": hits[0][1][:300] if hits else None}
        if hits:
            matched.append(entry)
        else:
            partial.append(entry)

    total = len(matched) + len(partial) + len(missing)
    coverage = (len(matched) + 0.5 * len(partial)) / total if total else 0.0
    if total == 0:
        return {
            "match_score": 0,
            "matched": [],
            "partial": [],
            "missing": [],
            "recommendations": [
                "No requirements could be extracted from this posting. Paste the responsibilities "
                "and requirements sections for a meaningful comparison."
            ],
            "disclaimer": DISCLAIMER,
        }

    resume_years = float(extracted.get("years_experience", 0.0) or 0.0)
    target_years = float(parsed.get("years_experience", 0.0) or 0.0)
    years_ratio = min(1.0, resume_years / target_years) if target_years else 1.0

    education_required = parsed.get("education") or []
    education_hit = 1.0
    if education_required:
        lowered = resume_text.lower()
        education_hit = 1.0 if any(term.lower() in lowered for term in education_required) else 0.4

    score = int(round(100 * (0.65 * coverage + 0.2 * years_ratio + 0.15 * education_hit)))

    recommendations: list[str] = []
    if missing:
        recommendations.append(
            "Address these requirements explicitly if you have them: "
            + ", ".join(item["label"] for item in missing[:6])
            + "."
        )
    if partial:
        recommendations.append(
            "Strengthen these by showing where you used them: "
            + ", ".join(item["label"] for item in partial[:6])
            + "."
        )
    if target_years and resume_years < target_years:
        recommendations.append(
            f"The posting asks for about {target_years:g} years; your resume evidences "
            f"{resume_years:g}. Surface relevant projects and internships to close the gap."
        )
    if not recommendations:
        recommendations.append("Strong overlap. Tailor the summary to the posting's language and apply.")

    return {
        "match_score": max(0, min(100, score)),
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "recommendations": recommendations[:5],
        "disclaimer": DISCLAIMER,
    }
