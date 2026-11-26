"""Offline provider.

Used by tests, in CI, and whenever no AI key is configured. It produces real, evidence-based
observations from rules over the structured context, so the product works end to end without a
provider and every AI-shaped output has a deterministic baseline to compare against.
"""

from __future__ import annotations

import json
from typing import Any

from app.services.ai.base import AIProviderError

WEAK_PHRASES = (
    "responsible for",
    "worked on",
    "helped with",
    "assisted in",
    "duties included",
    "involved in",
)


def _issue(category: str, severity: str, title: str, detail: str, evidence: str, suggestion: str) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "evidence": evidence,
        "suggestion": suggestion,
    }


class DeterministicProvider:
    name = "deterministic"
    model = "rules-v1"

    def __init__(self) -> None:
        self._tokens = 0

    @property
    def tokens_used(self) -> int:
        return self._tokens

    def complete_json(
        self,
        *,
        task: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        max_tokens: int = 1800,
    ) -> dict[str, Any]:
        if task == "resume_analysis":
            return self._analyse(user)
        if task == "jd_parse":
            return self._parse_jd(user)
        raise AIProviderError(f"Unsupported task: {task}")

    # -- analysis ---------------------------------------------------------
    def _analyse(self, user: str) -> dict[str, Any]:
        payload = self._payload(user)
        issues: list[dict[str, str]] = []
        rewrites: list[dict[str, str]] = []

        missing_required = payload.get("missing_required", [])
        missing_preferred = payload.get("missing_preferred", [])
        if missing_required:
            issues.append(
                _issue(
                    "keyword",
                    "high",
                    "Required domain keywords are absent",
                    "These skills are required for the selected domain and are not evidenced anywhere "
                    "in the resume: " + ", ".join(missing_required) + ".",
                    "Not found in the document.",
                    "If you have used " + ", ".join(missing_required[:3]) + ", name them in your skills "
                    "section and describe where you applied them.",
                )
            )
        if missing_preferred:
            issues.append(
                _issue(
                    "skill",
                    "medium",
                    "Preferred skills missing",
                    "Preferred for this domain but not evidenced: " + ", ".join(missing_preferred) + ".",
                    "Not found in the document.",
                    "Add only the ones you genuinely have, with a one-line usage example.",
                )
            )

        for weak in payload.get("weak_bullets", [])[:4]:
            issues.append(
                _issue(
                    "content",
                    "medium",
                    "Bullet describes a duty, not an outcome",
                    "The bullet opens with a responsibility phrase and states no result, scale or "
                    "technology.",
                    weak[:300],
                    "Rewrite as action + technology + measurable result, for example: 'Built X with Y, "
                    "cutting Z by N%'.",
                )
            )
            rewrites.append(
                {
                    "original": weak[:400],
                    "improved": self._rewrite(weak),
                }
            )

        for flag in payload.get("ats_flags", []):
            issues.append(
                _issue(
                    "ats",
                    "high" if flag in {"tables", "multi_column", "text_in_graphics"} else "medium",
                    "ATS readability risk: " + flag.replace("_", " "),
                    "Automated parsers may misread this layout.",
                    "Detected from document structure.",
                    "Use a single column, standard section headings and selectable text. The ATS-Friendly "
                    "template does this automatically.",
                )
            )

        for flag in payload.get("formatting_flags", []):
            issues.append(
                _issue(
                    "formatting",
                    "low" if flag in {"too_long", "dense_paragraphs"} else "medium",
                    "Formatting: " + flag.replace("_", " "),
                    "Formatting inconsistency that costs readability.",
                    "Detected from extracted structure.",
                    "Keep one bullet style, consistent date formats and 3-6 bullets per role.",
                )
            )

        for issue_text in payload.get("grammar_issues", [])[:5]:
            issues.append(
                _issue("grammar", "low", "Grammar or punctuation issue", issue_text, issue_text, "Fix the wording.")
            )
        for issue_text in payload.get("spelling_issues", [])[:5]:
            issues.append(
                _issue("spelling", "low", "Possible misspelling", issue_text, issue_text, "Correct the spelling.")
            )

        expected_sections = set(payload.get("required_sections", []))
        present = set(payload.get("sections_present", []))
        for missing in sorted(expected_sections - present):
            issues.append(
                _issue(
                    "section",
                    "high" if missing in {"experience", "skills"} else "medium",
                    f"Missing section: {missing.title()}",
                    "This section is expected for the selected domain and was not detected.",
                    "Section heading not found.",
                    f"Add a {missing.title()} section with concrete, quantified detail.",
                )
            )

        coverage = float(payload.get("required_coverage", 0.0))
        content_adjustment = 0
        if coverage >= 0.85 and payload.get("quantified_ratio", 0) >= 0.5:
            content_adjustment = 3
        elif coverage < 0.4:
            content_adjustment = -4
        experience_adjustment = 1 if payload.get("years_experience", 0) >= 3 else -1

        strengths = list(payload.get("deterministic_strengths", []))[:5]
        weaknesses = list(payload.get("deterministic_weaknesses", []))[:5]

        summary = (
            f"Review against {payload.get('domain_name', 'the selected domain')}: "
            f"{len(missing_required)} required keywords absent, "
            f"{len(payload.get('weak_bullets', []))} duty-style bullets, "
            f"{len(payload.get('ats_flags', []))} ATS risks."
        )
        self._tokens = 0
        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "issues": issues[:20],
            "rewrites": rewrites[:5],
            "content_adjustment": content_adjustment,
            "experience_adjustment": experience_adjustment,
        }

    @staticmethod
    def _rewrite(bullet: str) -> str:
        cleaned = bullet.strip().rstrip(".")
        for phrase in WEAK_PHRASES:
            cleaned = cleaned.replace(phrase, "").replace(phrase.title(), "")
        cleaned = cleaned.strip(" ,")
        if not cleaned:
            return "Led <project> using <technology>, delivering <measurable outcome>."
        return cleaned[0].upper() + cleaned[1:] + ", delivering <measurable outcome>."

    # -- job description --------------------------------------------------
    def _parse_jd(self, user: str) -> dict[str, Any]:
        from app.services.taxonomy import SkillRow, find_mentions

        text = self._document(user)
        from app.services.taxonomy_catalog import CATALOG

        required: list[str] = []
        soft: list[str] = []
        for entry in CATALOG:
            skill = SkillRow(
                canonical_name=entry["canonical_name"],
                aliases=entry["aliases"],
                kind=entry["kind"],
            )
            if find_mentions(text, skill):
                (soft if entry["kind"] == "soft" else required).append(entry["canonical_name"])

        import re

        years = 0.0
        matches = re.findall(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", text, re.I)
        if matches:
            years = float(max(int(m) for m in matches))
        education = re.findall(
            r"(bachelor[^.\n]{0,60}|master[^.\n]{0,60}|bs[cs]?[^.\n]{0,40}|degree in [^.\n]{0,60})",
            text,
            re.I,
        )
        self._tokens = 0
        return {
            "required_skills": required[:30],
            "soft_skills": soft[:15],
            "keywords": [s.lower() for s in required[:20]],
            "years_experience": min(years, 40),
            "education": [e.strip()[:120] for e in education[:5]],
        }

    @staticmethod
    def _payload(user: str) -> dict[str, Any]:
        try:
            head = user.split("RESUME TEXT", 1)[0]
            json_part = head.split("STRUCTURED RESUME DATA:", 1)[1]
            return json.loads(json_part)
        except Exception as exc:
            raise AIProviderError("Deterministic provider received an unreadable context") from exc

    @staticmethod
    def _document(user: str) -> str:
        if "<document>" in user:
            return user.split("<document>", 1)[1].split("</document>", 1)[0]
        return user
