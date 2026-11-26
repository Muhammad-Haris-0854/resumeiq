"""Small, dependency-free text utilities used by extraction, matching and scoring."""

from __future__ import annotations

import re
from collections import Counter

_WHITESPACE = re.compile(r"[ \t\u00a0]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}")
_NUMBER = re.compile(r"\b\d[\d,.]*\b")

STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then than that this these those of in on at to for with without from by
    as is are was were be been being it its it's i we you they he she them our your their my me us
    not no do does did done have has had will would can could should may might must about into over
    under more most other some such only own same so too very just also using used use work worked
    working experience experiences responsible responsibilities including include includes etc
    """.split()
)


def normalize_whitespace(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE.sub(" ", text)
    return _BLANK_LINES.sub("\n\n", text).strip()


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text or "")]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(normalize_whitespace(text)) if s.strip()]


def word_count(text: str) -> int:
    return len(_WORD.findall(text or ""))


def has_quantified_metric(text: str) -> bool:
    """True when a line contains a number that reads as an outcome, not a date."""
    if not _NUMBER.search(text or ""):
        return False
    without_years = re.sub(r"\b(19|20)\d{2}\b", " ", text)
    return bool(re.search(r"\b\d+\s*(%|percent|x|k|m|bn|users|clients|students|hours|days)\b", without_years, re.I)) or bool(
        re.search(r"\b\d{2,}\b", without_years)
    )


def extract_keywords(text: str, limit: int = 40) -> list[str]:
    """Frequency-ranked unigrams and bigrams, stopword filtered. Deterministic."""
    tokens = words(text)
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    unigrams = Counter(filtered)
    bigrams: Counter[str] = Counter()
    for first, second in zip(tokens, tokens[1:], strict=False):
        if first in STOPWORDS or second in STOPWORDS:
            continue
        if len(first) > 2 and len(second) > 2:
            bigrams[f"{first} {second}"] += 1
    scored: list[tuple[str, float]] = []
    for term, count in unigrams.items():
        scored.append((term, float(count)))
    for term, count in bigrams.items():
        if count > 1:
            scored.append((term, count * 1.5))
    scored.sort(key=lambda item: (-item[1], item[0]))
    seen: set[str] = set()
    result: list[str] = []
    for term, _ in scored:
        if term in seen:
            continue
        seen.add(term)
        result.append(term)
        if len(result) >= limit:
            break
    return result


def years_of_experience(text: str) -> float:
    """Best-effort total years from explicit statements like '5+ years of experience'."""
    matches = re.findall(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", text or "", re.I)
    if not matches:
        return 0.0
    return float(max(int(m) for m in matches))
