from __future__ import annotations

import pytest

from app.models.enums import DEFAULT_WEIGHTS, RequirementLevel, SkillStatus
from app.services.scoring import ScoreInputs, compute_scores, score_band
from app.services.taxonomy import SkillMatch


def _match(skill: str, status: SkillStatus, requirement=RequirementLevel.REQUIRED, weight=3.0, kind="technical"):
    return SkillMatch(
        skill=skill,
        requirement=requirement,
        weight=weight,
        status=status,
        mentions=2 if status is SkillStatus.FOUND else 0,
        evidence="Built it" if status is not SkillStatus.MISSING else None,
        kind=kind,
    )


def _strong_inputs(**overrides):
    base = dict(
        skill_matches=[
            _match("React.js", SkillStatus.FOUND),
            _match("TypeScript", SkillStatus.FOUND),
            _match("Redux", SkillStatus.FOUND),
            _match("Communication", SkillStatus.FOUND, RequirementLevel.PREFERRED, 1.5, "soft"),
        ],
        sections_present={"summary", "skills", "experience", "education"},
        required_sections={"summary", "skills", "experience", "education"},
        word_count=520,
        bullet_count=10,
        quantified_bullets=8,
        weak_bullets=1,
        grammar_issues=0,
        spelling_issues=0,
        formatting_flags=[],
        ats_flags=[],
        years_experience=4.0,
        target_years=3.0,
        experience_keyword_overlap=0.8,
    )
    base.update(overrides)
    return ScoreInputs(**base)


def test_strong_resume_scores_high():
    report = compute_scores(_strong_inputs())
    assert report.overall >= 85
    assert score_band(report.overall) == "strong"
    assert [d.key for d in report.details] == list(DEFAULT_WEIGHTS)


def test_scoring_is_deterministic():
    first = compute_scores(_strong_inputs()).as_dict()
    second = compute_scores(_strong_inputs()).as_dict()
    assert first == second


def test_weak_resume_scores_low():
    report = compute_scores(
        ScoreInputs(
            skill_matches=[
                _match("React.js", SkillStatus.MISSING),
                _match("TypeScript", SkillStatus.MISSING),
            ],
            sections_present={"education"},
            required_sections={"summary", "skills", "experience", "education"},
            word_count=120,
            bullet_count=2,
            quantified_bullets=0,
            weak_bullets=2,
            grammar_issues=5,
            spelling_issues=3,
            formatting_flags=["no_bullets", "too_short", "no_section_headings"],
            ats_flags=["tables", "missing_email"],
            years_experience=0.0,
            target_years=2.0,
            experience_keyword_overlap=0.0,
            has_contact_block=False,
        )
    )
    assert report.overall < 45
    assert score_band(report.overall) == "at_risk"


def test_weights_must_sum_to_one_hundred():
    with pytest.raises(ValueError):
        compute_scores(_strong_inputs(), {**DEFAULT_WEIGHTS, "keyword_match": 99})


def test_ai_adjustment_is_clamped():
    neutral = compute_scores(_strong_inputs()).as_dict()["content_quality"]
    inflated = compute_scores(_strong_inputs(ai_content_adjustment=50)).as_dict()["content_quality"]
    assert inflated - neutral <= 8


def test_each_score_explains_itself():
    report = compute_scores(_strong_inputs())
    for detail in report.details:
        assert detail.explanation
        assert detail.inputs is not None
        assert 0 <= detail.score <= 100
