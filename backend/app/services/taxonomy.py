"""Deterministic skill matching against a career-domain taxonomy.

Alias-aware, word-boundary safe (so "Java" does not match "JavaScript", and "C#" survives
regex escaping), and evidence-carrying: every match points at the line that produced it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from app.models.enums import RequirementLevel, SkillStatus

_ALIAS_SPLIT = re.compile(r"[,\n]")


@dataclass(frozen=True)
class SkillRow:
    canonical_name: str
    aliases: Sequence[str] = field(default_factory=tuple)
    requirement: RequirementLevel = RequirementLevel.REQUIRED
    weight: float = 1.0
    kind: str = "technical"

    @property
    def terms(self) -> tuple[str, ...]:
        seen: list[str] = []
        for term in (self.canonical_name, *self.aliases):
            cleaned = (term or "").strip()
            if cleaned and cleaned.lower() not in {s.lower() for s in seen}:
                seen.append(cleaned)
        return tuple(seen)


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    requirement: RequirementLevel
    weight: float
    status: SkillStatus
    mentions: int
    evidence: str | None
    kind: str = "technical"

    @property
    def credit(self) -> float:
        if self.status is SkillStatus.FOUND:
            return 1.0
        if self.status is SkillStatus.PARTIAL:
            return 0.5
        return 0.0


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    # Allow flexible whitespace inside multi-word terms and optional separators in "Node.js".
    escaped = escaped.replace(r"\ ", r"\s+").replace(r"\.", r"[.\s]?")
    return re.compile(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)


def _lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _is_list_line(line: str, matched_term: str) -> bool:
    """A bare list ("React, Redux, TypeScript") is a claim without evidence."""
    remainder = _term_pattern(matched_term).sub(" ", line)
    comma_separated = "," in remainder or ";" in remainder or "|" in remainder
    remainder = _ALIAS_SPLIT.sub(" ", remainder)
    leftover = [w for w in remainder.split() if w]
    return comma_separated or len(leftover) <= 2


def find_mentions(text: str, skill: SkillRow) -> list[tuple[str, str]]:
    """Returns (matched_term, line) pairs for every occurrence."""
    hits: list[tuple[str, str]] = []
    for line in _lines(text):
        for term in skill.terms:
            if _term_pattern(term).search(line):
                hits.append((term, line))
                break
    return hits


def match_skill(text: str, skill: SkillRow) -> SkillMatch:
    hits = find_mentions(text, skill)
    if not hits:
        return SkillMatch(
            skill=skill.canonical_name,
            requirement=skill.requirement,
            weight=skill.weight,
            status=SkillStatus.MISSING,
            mentions=0,
            evidence=None,
            kind=skill.kind,
        )
    evidence = hits[0][1]
    status = SkillStatus.FOUND
    if len(hits) == 1 and _is_list_line(evidence, hits[0][0]):
        status = SkillStatus.PARTIAL
    return SkillMatch(
        skill=skill.canonical_name,
        requirement=skill.requirement,
        weight=skill.weight,
        status=status,
        mentions=len(hits),
        evidence=evidence[:300],
        kind=skill.kind,
    )


def match_domain_skills(text: str, skills: Iterable[SkillRow]) -> list[SkillMatch]:
    matches = [match_skill(text, skill) for skill in skills]
    order = {RequirementLevel.REQUIRED: 0, RequirementLevel.PREFERRED: 1, RequirementLevel.OPTIONAL: 2}
    matches.sort(key=lambda m: (order.get(m.requirement, 3), m.skill.lower()))
    return matches


def weighted_coverage(matches: Iterable[SkillMatch], *, requirement: RequirementLevel | None = None) -> float:
    """Weighted fraction of taxonomy skills evidenced, in [0, 1]."""
    relevant = [m for m in matches if requirement is None or m.requirement is requirement]
    total = sum(m.weight for m in relevant)
    if total <= 0:
        return 0.0
    earned = sum(m.weight * m.credit for m in relevant)
    return max(0.0, min(1.0, earned / total))


def missing_by_requirement(matches: Iterable[SkillMatch]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"required": [], "preferred": [], "optional": []}
    for match in matches:
        if match.status is SkillStatus.MISSING:
            grouped[match.requirement.value].append(match.skill)
    return grouped


def detect_skills_from_taxonomy(text: str, all_skills: Sequence[SkillRow]) -> list[SkillRow]:
    """All canonical skills mentioned anywhere in the document."""
    return [skill for skill in all_skills if find_mentions(text, skill)]
