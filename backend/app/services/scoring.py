"""Deterministic scoring engine.

Every number is derived from explicit inputs so the same resume always scores the same and
each score can explain itself. The LLM never sets a score: it may contribute bounded
adjustments (max ±8 content quality, ±5 experience relevance) which are clamped here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.models.enums import DEFAULT_WEIGHTS, SCORE_KEYS, RequirementLevel, SkillStatus
from app.services.taxonomy import SkillMatch, weighted_coverage

SCORE_LABELS: dict[str, str] = {
    "keyword_match": "Keyword Match",
    "technical_skills": "Technical Skills",
    "ats_compatibility": "ATS Compatibility",
    "content_quality": "Content Quality",
    "grammar": "Grammar",
    "formatting": "Formatting",
    "experience_relevance": "Experience Relevance",
}

# Penalty per detected issue, kept explicit so tests can reason about them.
ATS_FLAG_PENALTIES: dict[str, int] = {
    "tables": 18,
    "multi_column": 15,
    "images": 12,
    "headers_footers": 10,
    "non_standard_headings": 8,
    "missing_email": 10,
    "missing_phone": 6,
    "text_in_graphics": 12,
}

FORMATTING_FLAG_PENALTIES: dict[str, int] = {
    "no_bullets": 15,
    "overlong_bullets": 10,
    "inconsistent_dates": 10,
    "no_section_headings": 15,
    "dense_paragraphs": 12,
    "too_short": 10,
    "too_long": 10,
}

CONTENT_ADJUSTMENT_CAP = 8
EXPERIENCE_ADJUSTMENT_CAP = 5


@dataclass(frozen=True)
class ScoreInputs:
    skill_matches: list[SkillMatch]
    sections_present: set[str]
    required_sections: set[str]
    word_count: int
    bullet_count: int
    quantified_bullets: int
    weak_bullets: int
    grammar_issues: int
    spelling_issues: int
    formatting_flags: list[str] = field(default_factory=list)
    ats_flags: list[str] = field(default_factory=list)
    years_experience: float = 0.0
    target_years: float = 0.0
    experience_keyword_overlap: float = 0.0
    ai_content_adjustment: int = 0
    ai_experience_adjustment: int = 0
    has_contact_block: bool = True


@dataclass(frozen=True)
class ScoreDetail:
    key: str
    label: str
    score: int
    weight: int
    explanation: str
    inputs: dict[str, object]


@dataclass(frozen=True)
class ScoreReport:
    overall: int
    details: list[ScoreDetail]

    def as_dict(self) -> dict[str, int]:
        return {detail.key: detail.score for detail in self.details}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> int:
    return int(round(max(low, min(high, value))))


def _validate_weights(weights: dict[str, int]) -> dict[str, int]:
    missing = [key for key in SCORE_KEYS if key not in weights]
    if missing:
        raise ValueError(f"Missing scoring weights: {missing}")
    total = sum(int(weights[key]) for key in SCORE_KEYS)
    if total != 100:
        raise ValueError(f"Scoring weights must sum to 100, got {total}")
    return {key: int(weights[key]) for key in SCORE_KEYS}


def _keyword_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    required = weighted_coverage(inputs.skill_matches, requirement=RequirementLevel.REQUIRED)
    all_coverage = weighted_coverage(inputs.skill_matches)
    score = _clamp(100 * (0.7 * required + 0.3 * all_coverage))
    found = sum(1 for m in inputs.skill_matches if m.status is SkillStatus.FOUND)
    partial = sum(1 for m in inputs.skill_matches if m.status is SkillStatus.PARTIAL)
    missing = sum(1 for m in inputs.skill_matches if m.status is SkillStatus.MISSING)
    explanation = (
        f"{found} of {len(inputs.skill_matches)} domain keywords evidenced, {partial} partially "
        f"matched, {missing} absent. Required skills coverage is {required:.0%}."
    )
    return score, explanation, {
        "required_coverage": round(required, 3),
        "overall_coverage": round(all_coverage, 3),
        "found": found,
        "partial": partial,
        "missing": missing,
    }


def _technical_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    technical = [m for m in inputs.skill_matches if m.kind == "technical"]
    soft = [m for m in inputs.skill_matches if m.kind == "soft"]
    tech_cov = weighted_coverage(technical)
    soft_cov = weighted_coverage(soft) if soft else 1.0
    score = _clamp(100 * (0.75 * tech_cov + 0.25 * soft_cov))
    explanation = (
        f"Technical coverage {tech_cov:.0%} across {len(technical)} tracked technical skills"
        + (f", soft-skill evidence {soft_cov:.0%}" if soft else "")
        + "."
    )
    return score, explanation, {
        "technical_coverage": round(tech_cov, 3),
        "soft_coverage": round(soft_cov, 3),
        "technical_tracked": len(technical),
    }


def _ats_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    penalty = sum(ATS_FLAG_PENALTIES.get(flag, 5) for flag in inputs.ats_flags)
    if not inputs.has_contact_block:
        penalty += 10
    score = _clamp(100 - penalty)
    if inputs.ats_flags:
        explanation = "Readability risk from: " + ", ".join(flag.replace("_", " ") for flag in inputs.ats_flags) + "."
    else:
        explanation = "Standard headings, single-column flow, selectable text: parsers should read this cleanly."
    return score, explanation, {"flags": list(inputs.ats_flags), "penalty": penalty}


def _content_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    sections_found = len(inputs.sections_present & inputs.required_sections)
    section_ratio = sections_found / max(1, len(inputs.required_sections))
    bullet_quality = (
        inputs.quantified_bullets / inputs.bullet_count if inputs.bullet_count else 0.0
    )
    weak_ratio = inputs.weak_bullets / inputs.bullet_count if inputs.bullet_count else 1.0
    length_score = 1.0 if 250 <= inputs.word_count <= 900 else 0.6 if 150 <= inputs.word_count <= 1200 else 0.3
    base = 100 * (
        0.35 * section_ratio
        + 0.30 * bullet_quality
        + 0.20 * (1 - weak_ratio)
        + 0.15 * length_score
    )
    adjustment = max(-CONTENT_ADJUSTMENT_CAP, min(CONTENT_ADJUSTMENT_CAP, inputs.ai_content_adjustment))
    score = _clamp(base + adjustment)
    explanation = (
        f"{sections_found}/{len(inputs.required_sections)} expected sections, "
        f"{inputs.quantified_bullets}/{inputs.bullet_count or 0} bullets carry a measurable outcome, "
        f"{inputs.word_count} words."
        + (f" AI review adjusted this by {adjustment:+d}." if adjustment else "")
    )
    return score, explanation, {
        "section_ratio": round(section_ratio, 3),
        "bullet_quality": round(bullet_quality, 3),
        "weak_ratio": round(weak_ratio, 3),
        "length_score": round(length_score, 3),
        "ai_adjustment": adjustment,
    }


def _grammar_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    penalty = inputs.grammar_issues * 8 + inputs.spelling_issues * 6
    score = _clamp(100 - penalty)
    explanation = (
        f"{inputs.grammar_issues} grammar and {inputs.spelling_issues} spelling issues detected."
        if penalty
        else "No grammar or spelling issues detected in the extracted text."
    )
    return score, explanation, {
        "grammar_issues": inputs.grammar_issues,
        "spelling_issues": inputs.spelling_issues,
    }


def _formatting_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    penalty = sum(FORMATTING_FLAG_PENALTIES.get(flag, 5) for flag in inputs.formatting_flags)
    score = _clamp(100 - penalty)
    if inputs.formatting_flags:
        explanation = "Formatting problems: " + ", ".join(f.replace("_", " ") for f in inputs.formatting_flags) + "."
    else:
        explanation = "Consistent bullet structure, dates and headings."
    return score, explanation, {"flags": list(inputs.formatting_flags), "penalty": penalty}


def _experience_score(inputs: ScoreInputs) -> tuple[int, str, dict[str, object]]:
    if inputs.target_years > 0:
        ratio = min(1.0, inputs.years_experience / inputs.target_years)
    else:
        ratio = 1.0 if inputs.years_experience > 0 else 0.6
    base = 100 * (0.55 * ratio + 0.45 * max(0.0, min(1.0, inputs.experience_keyword_overlap)))
    adjustment = max(
        -EXPERIENCE_ADJUSTMENT_CAP, min(EXPERIENCE_ADJUSTMENT_CAP, inputs.ai_experience_adjustment)
    )
    score = _clamp(base + adjustment)
    explanation = (
        f"{inputs.years_experience:g} years evidenced"
        + (f" against a {inputs.target_years:g}-year expectation" if inputs.target_years else "")
        + f"; experience section keyword overlap {inputs.experience_keyword_overlap:.0%}."
    )
    return score, explanation, {
        "years": inputs.years_experience,
        "target_years": inputs.target_years,
        "keyword_overlap": round(inputs.experience_keyword_overlap, 3),
        "ai_adjustment": adjustment,
    }


_COMPUTERS = {
    "keyword_match": _keyword_score,
    "technical_skills": _technical_score,
    "ats_compatibility": _ats_score,
    "content_quality": _content_score,
    "grammar": _grammar_score,
    "formatting": _formatting_score,
    "experience_relevance": _experience_score,
}


def compute_scores(
    inputs: ScoreInputs, weights: dict[str, int] | None = None
) -> ScoreReport:
    resolved = _validate_weights(weights or DEFAULT_WEIGHTS)
    details: list[ScoreDetail] = []
    for key in SCORE_KEYS:
        score, explanation, raw_inputs = _COMPUTERS[key](inputs)
        details.append(
            ScoreDetail(
                key=key,
                label=SCORE_LABELS[key],
                score=score,
                weight=resolved[key],
                explanation=explanation,
                inputs=raw_inputs,
            )
        )
    overall = int(round(sum(d.score * d.weight for d in details) / 100))
    return ScoreReport(overall=max(0, min(100, overall)), details=details)


def score_band(score: int) -> str:
    if score >= 85:
        return "strong"
    if score >= 70:
        return "solid"
    if score >= 50:
        return "needs_work"
    return "at_risk"


def summarise(report: ScoreReport, matches: Iterable[SkillMatch]) -> tuple[list[str], list[str]]:
    """Deterministic strengths and weaknesses, strongest signals first."""
    strengths: list[str] = []
    weaknesses: list[str] = []
    by_key = {detail.key: detail for detail in report.details}
    if by_key["keyword_match"].score >= 75:
        strengths.append("Strong alignment with the domain keyword set.")
    if by_key["ats_compatibility"].score >= 85:
        strengths.append("ATS-safe layout: single column, standard headings, selectable text.")
    if by_key["content_quality"].score >= 70:
        strengths.append("Bullets carry measurable outcomes rather than responsibilities.")
    if by_key["grammar"].score >= 90:
        strengths.append("Clean grammar and spelling.")
    for detail in sorted(report.details, key=lambda d: d.score):
        if detail.score < 60:
            weaknesses.append(f"{detail.label}: {detail.explanation}")
    missing = [m.skill for m in matches if m.status is SkillStatus.MISSING][:6]
    if missing:
        weaknesses.append("Missing domain keywords: " + ", ".join(missing) + ".")
    return strengths[:5], weaknesses[:5]
