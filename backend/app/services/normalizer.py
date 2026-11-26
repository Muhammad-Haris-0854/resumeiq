"""Turn extracted text into a structured resume profile.

Heuristic, deterministic and conservative: when a field cannot be identified it stays empty
rather than being guessed. Downstream analysis only ever reads this structure plus the raw text.
"""

from __future__ import annotations

import re
from typing import Any

from app.utils.text import has_quantified_metric, normalize_whitespace, word_count, years_of_experience

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?){2,4}\d{2,4}")
LINK_RE = re.compile(r"(?:https?://|www\.)[^\s,;)]+|(?:github|linkedin)\.com/[^\s,;)]+", re.I)

SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "summary": re.compile(r"^(professional\s+summary|summary|profile|objective|about\s+me)\s*:?$", re.I),
    "skills": re.compile(r"^(technical\s+skills|skills|core\s+competencies|technologies|tech\s+stack)\s*:?$", re.I),
    "experience": re.compile(
        r"^(work\s+experience|professional\s+experience|experience|employment(\s+history)?|work\s+history)\s*:?$",
        re.I,
    ),
    "education": re.compile(r"^(education|academic\s+background|qualifications)\s*:?$", re.I),
    "projects": re.compile(r"^(projects?|personal\s+projects|selected\s+projects)\s*:?$", re.I),
    "certifications": re.compile(r"^(certifications?|licenses?|courses?)\s*:?$", re.I),
    "achievements": re.compile(r"^(achievements?|awards?|honors?|accomplishments?)\s*:?$", re.I),
    "languages": re.compile(r"^(languages?)\s*:?$", re.I),
}

BULLET_PREFIX = re.compile(r"^\s*(?:[-•*·‣▪◦]|\d{1,2}[.)])\s+")
DATE_RANGE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{1,2}/\d{4}|\d{4})"
    r"\s*(?:-|–|—|to)\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{1,2}/\d{4}|\d{4}|present|current)",
    re.I,
)
WEAK_PHRASES = (
    "responsible for",
    "worked on",
    "helped with",
    "assisted in",
    "duties included",
    "involved in",
    "participated in",
)
COMMON_MISSPELLINGS = {
    "recieve": "receive",
    "seperate": "separate",
    "occured": "occurred",
    "managment": "management",
    "developement": "development",
    "enviroment": "environment",
    "responsable": "responsible",
    "sucessfully": "successfully",
    "experiance": "experience",
    "acheive": "achieve",
    "teh": "the",
    "adress": "address",
}


def _is_heading(line: str) -> str | None:
    candidate = line.strip().rstrip(":").strip()
    if len(candidate) > 48:
        return None
    for key, pattern in SECTION_PATTERNS.items():
        if pattern.match(candidate):
            return key
    return None


def split_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    """Returns (sections, prelude_lines). Lines before the first heading are the prelude."""
    sections: dict[str, list[str]] = {}
    prelude: list[str] = []
    current: str | None = None
    for raw_line in normalize_whitespace(text).split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        heading = _is_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if current is None:
            prelude.append(line)
        else:
            sections[current].append(line)
    return sections, prelude


def _guess_name(prelude: list[str]) -> str:
    for line in prelude[:4]:
        cleaned = line.strip()
        if not cleaned or "@" in cleaned or LINK_RE.search(cleaned):
            continue
        if any(char.isdigit() for char in cleaned):
            continue
        tokens = cleaned.split()
        if 2 <= len(tokens) <= 5 and all(token[:1].isupper() for token in tokens if token):
            return cleaned[:120]
    return ""


def _skills_from_lines(lines: list[str]) -> list[str]:
    raw = " ".join(lines)
    parts = re.split(r"[,;|/•·]|\s{3,}", raw)
    seen: list[str] = []
    for part in parts:
        item = part.strip(" .-–—")
        if not item or len(item) > 40:
            continue
        if len(item.split()) > 4:
            continue
        if item.lower() not in {s.lower() for s in seen}:
            seen.append(item)
    return seen[:60]


COMPANY_HINTS = (
    "ltd", "limited", "inc", "llc", "corp", "company", "technologies", "solutions", "systems",
    "software", "university", "college", "bank", "labs", "studio", "agency", "group", "pvt",
)


def _looks_like_company(line: str) -> bool:
    stripped = line.strip().rstrip(".")
    if line.strip().endswith("."):
        return False
    tokens = stripped.split()
    if not 1 <= len(tokens) <= 6:
        return False
    lowered = stripped.lower()
    if any(hint in lowered for hint in COMPANY_HINTS):
        return True
    return all(token[:1].isupper() or token.isupper() for token in tokens if token)


def _parse_experience(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        stripped = BULLET_PREFIX.sub("", line).strip()
        is_bullet = bool(BULLET_PREFIX.match(line))
        dates = DATE_RANGE.search(stripped)
        if not is_bullet and (dates or (current is None and len(stripped.split()) <= 12)):
            if current and (current["bullets"] or current["title"]):
                entries.append(current)
            current = {
                "title": stripped[:160],
                "company": "",
                "start_date": dates.group(1) if dates else "",
                "end_date": dates.group(2) if dates else "",
                "bullets": [],
            }
            continue
        if current is None:
            current = {"title": stripped[:160], "company": "", "start_date": "", "end_date": "", "bullets": []}
            continue
        if not current["company"] and _looks_like_company(stripped) and not has_quantified_metric(stripped):
            current["company"] = stripped[:160]
            continue
        current["bullets"].append(stripped[:500])
    if current and (current["bullets"] or current["title"]):
        entries.append(current)
    return entries[:12]


def _parse_education(lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in lines:
        stripped = BULLET_PREFIX.sub("", line).strip()
        if not stripped:
            continue
        dates = DATE_RANGE.search(stripped)
        degree = re.split(r"\s+[|,]\s+|\s+at\s+", stripped)[0][:160]
        institution = ""
        parts = re.split(r"\s+[|,]\s+|\s+at\s+", stripped)
        if len(parts) > 1:
            institution = parts[1][:160]
        entries.append(
            {
                "degree": degree,
                "institution": institution,
                "start_date": dates.group(1) if dates else "",
                "end_date": dates.group(2) if dates else "",
                "details": "" if len(stripped) < 80 else stripped[:400],
            }
        )
    return entries[:8]


def _parse_projects(lines: list[str]) -> list[dict[str, str]]:
    projects: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines:
        stripped = BULLET_PREFIX.sub("", line).strip()
        if not stripped:
            continue
        if not BULLET_PREFIX.match(line) and len(stripped.split()) <= 10:
            if current:
                projects.append(current)
            current = {"name": stripped[:160], "description": "", "link": ""}
            link = LINK_RE.search(stripped)
            if link:
                current["link"] = link.group(0)[:300]
            continue
        if current is None:
            current = {"name": stripped[:80], "description": "", "link": ""}
        else:
            current["description"] = (current["description"] + " " + stripped).strip()[:1200]
    if current:
        projects.append(current)
    return projects[:10]


def detect_grammar_issues(text: str) -> list[str]:
    issues: list[str] = []
    for line in text.split("\n"):
        stripped = BULLET_PREFIX.sub("", line).strip()
        if not stripped:
            continue
        if re.search(r"\s{2,}\S", stripped):
            issues.append(f"Double spacing: '{stripped[:70]}'")
        if re.search(r"\b(\w+)\s+\1\b", stripped, re.I):
            issues.append(f"Repeated word: '{stripped[:70]}'")
        if re.search(r",(?=\S)", stripped):
            issues.append(f"Missing space after comma: '{stripped[:70]}'")
        if re.match(r"^[a-z]", stripped) and len(stripped.split()) > 4:
            issues.append(f"Lowercase sentence start: '{stripped[:70]}'")
        if stripped.count("(") != stripped.count(")"):
            issues.append(f"Unbalanced parentheses: '{stripped[:70]}'")
    return issues[:25]


def detect_spelling_issues(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    lowered = text.lower()
    for wrong, right in COMMON_MISSPELLINGS.items():
        if re.search(rf"\b{re.escape(wrong)}\b", lowered):
            found.append((wrong, right))
    return found


def detect_ats_flags(text: str, page_count: int) -> list[str]:
    flags: list[str] = []
    lowered = text.lower()
    if "|" in text and text.count("|") > 12:
        flags.append("tables")
    if re.search(r"page\s+\d+\s+of\s+\d+", lowered):
        flags.append("headers_footers")
    if len(text.strip()) < 400 and page_count <= 1:
        flags.append("non_standard_headings")
    return flags


def normalise(text: str, page_count: int = 1) -> dict[str, Any]:
    sections, prelude = split_sections(text)
    skill_lines = sections.get("skills", [])
    listed_skills = _skills_from_lines(skill_lines)
    experience = _parse_experience(sections.get("experience", []))
    education = _parse_education(sections.get("education", []))
    projects = _parse_projects(sections.get("projects", []))

    bullets: list[str] = []
    for entry in experience:
        bullets.extend(entry["bullets"])
    bullets.extend(BULLET_PREFIX.sub("", line).strip() for line in sections.get("projects", []) if BULLET_PREFIX.match(line))

    weak = [b for b in bullets if any(phrase in b.lower() for phrase in WEAK_PHRASES)]
    quantified = [b for b in bullets if has_quantified_metric(b)]

    formatting_flags: list[str] = []
    if bullets and not any(BULLET_PREFIX.match(line) for line in text.split("\n")):
        formatting_flags.append("no_bullets")
    if any(len(b.split()) > 45 for b in bullets):
        formatting_flags.append("overlong_bullets")
    if not sections:
        formatting_flags.append("no_section_headings")
    words = word_count(text)
    if words < 150:
        formatting_flags.append("too_short")
    if words > 1100:
        formatting_flags.append("too_long")
    if re.search(r"\n[^\n]{400,}\n", text):
        formatting_flags.append("dense_paragraphs")

    emails = EMAIL_RE.findall(text)
    phones = [p.strip() for p in PHONE_RE.findall(prelude and " ".join(prelude[:6]) or text[:400]) if len(re.sub(r"\D", "", p)) >= 9]
    links = list(dict.fromkeys(LINK_RE.findall(text)))

    summary_lines = sections.get("summary", [])
    summary = " ".join(summary_lines)[:1200] if summary_lines else ""

    return {
        "full_name": _guess_name(prelude),
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "links": links[:6],
        "summary": summary,
        "listed_skills": listed_skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": [BULLET_PREFIX.sub("", line).strip() for line in sections.get("certifications", [])][:12],
        "achievements": [BULLET_PREFIX.sub("", line).strip() for line in sections.get("achievements", [])][:12],
        "languages": _skills_from_lines(sections.get("languages", []))[:8],
        "sections_present": sorted(sections.keys()),
        "bullets": bullets[:80],
        "weak_bullets": weak[:20],
        "quantified_bullets": len(quantified),
        "word_count": words,
        "years_experience": years_of_experience(text),
        "formatting_flags": formatting_flags,
        "ats_flags": detect_ats_flags(text, page_count),
        "grammar_issues": detect_grammar_issues(text),
        "spelling_issues": [f"{wrong} -> {right}" for wrong, right in detect_spelling_issues(text)],
        "has_contact_block": bool(emails or phones),
    }
