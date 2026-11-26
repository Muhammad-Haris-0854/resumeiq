from __future__ import annotations

from app.models.enums import RequirementLevel, SkillStatus
from app.services.taxonomy import SkillRow, match_domain_skills, match_skill, weighted_coverage


def _skill(name: str, aliases=(), requirement=RequirementLevel.REQUIRED, weight=3.0, kind="technical"):
    return SkillRow(canonical_name=name, aliases=aliases, requirement=requirement, weight=weight, kind=kind)


def test_alias_matches_canonical_skill():
    match = match_skill("Built interfaces with ReactJS and hooks", _skill("React.js", ["ReactJS"]))
    assert match.status is SkillStatus.FOUND


def test_java_does_not_match_javascript():
    java = match_skill("Three years of JavaScript and TypeScript", _skill("Java"))
    assert java.status is SkillStatus.MISSING


def test_csharp_and_dotnet_survive_escaping():
    assert match_skill("Built services in C# with ASP.NET Core", _skill("C#")).status is SkillStatus.FOUND
    assert match_skill("Deployed on .NET 8", _skill("ASP.NET", [".NET"])).status is SkillStatus.FOUND


def test_bare_skill_list_is_partial_not_found():
    text = "Skills\nReact, Redux, TypeScript\n"
    match = match_skill(text, _skill("React.js", ["React"]))
    assert match.status is SkillStatus.PARTIAL
    assert match.credit == 0.5


def test_usage_in_a_sentence_is_found():
    text = "Built a design system in React used by four product teams."
    assert match_skill(text, _skill("React.js", ["React"])).status is SkillStatus.FOUND


def test_weighted_coverage_respects_requirement_weights():
    matches = match_domain_skills(
        "Built React screens and TypeScript services for four product teams.",
        [
            _skill("React.js", ["React"], weight=3.0),
            _skill("TypeScript", weight=1.0),
            _skill("Redux", weight=1.0),
        ],
    )
    coverage = weighted_coverage(matches)
    assert 0.75 < coverage <= 0.85
    assert weighted_coverage(matches, requirement=RequirementLevel.REQUIRED) == coverage


def test_missing_skills_are_grouped_by_requirement():
    matches = match_domain_skills(
        "React only",
        [
            _skill("React.js", ["React"]),
            _skill("TypeScript", requirement=RequirementLevel.PREFERRED),
        ],
    )
    missing = [m for m in matches if m.status is SkillStatus.MISSING]
    assert [m.skill for m in missing] == ["TypeScript"]
