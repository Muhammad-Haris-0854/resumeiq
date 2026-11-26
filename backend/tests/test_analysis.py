from __future__ import annotations

from app.services.ai.base import AIProviderError
from app.services.ai.deterministic import DeterministicProvider
from app.services.analysis import build_context, build_skill_rows, compose_report
from app.services.normalizer import normalise
from app.services.taxonomy import match_domain_skills
from app.services.taxonomy_catalog import CATALOG, DOMAIN_SKILLS
from tests.conftest import RESUME_TEXT


def _skill_rows(slug: str = "react-developer"):
    mapping = DOMAIN_SKILLS[slug]
    catalog = {entry["canonical_name"]: entry for entry in CATALOG}
    rows = []
    weights = {"required": 3.0, "preferred": 1.5, "optional": 0.5}
    for level, names in mapping.items():
        for name in names:
            entry = catalog.get(name, {"canonical_name": name, "aliases": [], "kind": "technical"})
            rows.append(
                {
                    "canonical_name": entry["canonical_name"],
                    "aliases": entry["aliases"],
                    "requirement": level,
                    "weight": weights[level],
                    "kind": entry["kind"],
                }
            )
    return build_skill_rows(rows)


def _report(text: str = RESUME_TEXT, provider=None):
    extracted = normalise(text)
    matches = match_domain_skills(text, _skill_rows())
    context = build_context(
        resume_text=text,
        extracted=extracted,
        domain={"name": "React.js Developer", "slug": "react-developer"},
        matches=matches,
    )
    return compose_report(
        context=context,
        extracted=extracted,
        matches=matches,
        provider=provider or DeterministicProvider(),
    )


def test_report_contains_all_seven_scores():
    report = _report()
    assert len(report["scores"]) == 7
    assert 0 <= report["overall_score"] <= 100
    assert report["band"] in {"strong", "solid", "needs_work", "at_risk"}


def test_report_is_reproducible():
    first, second = _report(), _report()
    assert first["overall_score"] == second["overall_score"]
    assert [s["score"] for s in first["scores"]] == [s["score"] for s in second["scores"]]


def test_missing_required_keywords_are_reported_with_advice():
    report = _report()
    missing = set(report["missing_keywords"])
    assert "TypeScript" in missing
    issues = [issue for issue in report["issues"] if issue["category"] == "keyword"]
    assert issues
    assert "TypeScript" in issues[0]["detail"]
    assert issues[0]["suggestion"].startswith("If you have used")


def test_weak_bullets_become_content_issues_with_rewrites():
    report = _report()
    content_issues = [issue for issue in report["issues"] if issue["category"] == "content"]
    assert content_issues
    rewrite = next((i for i in content_issues if i["title"] == "Suggested rewrite"), None)
    assert rewrite is not None
    assert rewrite["evidence"] and rewrite["suggestion"]


def test_skill_breakdown_marks_partial_skills():
    report = _report()
    statuses = {item["skill"]: item["status"] for item in report["skill_breakdown"]}
    assert statuses["React.js"] in {"found", "partial"}
    assert statuses["TypeScript"] == "missing"


def test_ai_failure_degrades_instead_of_failing():
    class BrokenProvider:
        name = "broken"
        model = "broken-1"

        @property
        def tokens_used(self) -> int:
            return 0

        def complete_json(self, **kwargs):
            raise AIProviderError("provider down")

    report = _report(provider=BrokenProvider())
    assert report["ai_fallback"] is True
    assert len(report["scores"]) == 7
    assert report["summary"]


def test_ai_cannot_inflate_scores():
    class InflatingProvider(DeterministicProvider):
        def complete_json(self, **kwargs):
            payload = super().complete_json(**kwargs)
            payload["content_adjustment"] = 999
            payload["experience_adjustment"] = 999
            return payload

    normal = _report()
    inflated = _report(provider=InflatingProvider())
    delta = inflated["overall_score"] - normal["overall_score"]
    assert delta <= 3


def test_required_coverage_is_computed():
    report = _report()
    keyword_detail = next(s for s in report["scores"] if s["key"] == "keyword_match")
    assert keyword_detail["inputs"]["required_coverage"] < 1.0
    assert keyword_detail["inputs"]["missing"] >= 1
