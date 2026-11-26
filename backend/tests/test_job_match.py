from __future__ import annotations

from app.services.ai.deterministic import DeterministicProvider
from app.services.job_match import compute_match, parse_job_description
from app.services.normalizer import normalise
from app.services.taxonomy_catalog import CATALOG
from tests.conftest import RESUME_TEXT

JD = """
Senior Frontend Developer
We are hiring a frontend engineer with 4+ years of experience.
Requirements: React, TypeScript, Redux, REST APIs, Git, Jest, accessibility.
Bachelor's degree in Computer Science or related field.
"""


def test_job_description_is_parsed():
    parsed = parse_job_description(JD, DeterministicProvider(), CATALOG)
    assert "React.js" in parsed["required_skills"]
    assert "TypeScript" in parsed["required_skills"]
    assert parsed["years_experience"] == 4.0


def test_match_reports_matched_partial_and_missing():
    parsed = parse_job_description(JD, DeterministicProvider(), CATALOG)
    result = compute_match(
        resume_text=RESUME_TEXT,
        extracted=normalise(RESUME_TEXT),
        parsed=parsed,
        catalog=CATALOG,
    )
    labels = {item["label"] for item in result["missing"]}
    assert "TypeScript" in labels
    matched = {item["label"] for item in result["matched"]} | {item["label"] for item in result["partial"]}
    assert "React.js" in matched
    assert 0 <= result["match_score"] <= 100
    assert result["recommendations"]


def test_match_score_is_not_presented_as_probability():
    parsed = parse_job_description(JD, DeterministicProvider(), CATALOG)
    result = compute_match(
        resume_text=RESUME_TEXT,
        extracted=normalise(RESUME_TEXT),
        parsed=parsed,
        catalog=CATALOG,
    )
    assert "not a probability" in result["disclaimer"]


def test_empty_requirements_yield_zero_score_without_crash():
    result = compute_match(
        resume_text=RESUME_TEXT,
        extracted=normalise(RESUME_TEXT),
        parsed={"required_skills": [], "soft_skills": [], "years_experience": 0, "education": []},
        catalog=CATALOG,
    )
    assert result["match_score"] == 0
    assert result["missing"] == []
    assert result["recommendations"]
