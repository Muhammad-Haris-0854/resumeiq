#!/usr/bin/env python3
"""Prove the configured AI provider works end to end, against the real schemas.

Run this before deploying: it catches a bad key, a wrong model name, a region block, or a
provider that cannot follow the JSON contract, without needing Supabase or Redis.

    AI_PROVIDER=google AI_MODEL=gemini-2.5-flash AI_PROVIDER_API_KEY=... \
        python tools/ai_smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.services.ai import build_provider  # noqa: E402
from app.services.ai.base import AIProviderError  # noqa: E402
from app.services.ai.prompts import (  # noqa: E402
    ANALYSIS_SCHEMA,
    ANALYSIS_SYSTEM,
    JD_SCHEMA,
    JD_SYSTEM,
    build_analysis_user,
    build_jd_user,
)

RESUME = """ALEX MERCER
Karachi, Pakistan | alex.mercer@example.com | +92 300 0000000

SUMMARY
Frontend developer with two years of experience building dashboards for logistics companies.

SKILLS
JavaScript, HTML, CSS, React, Git, Figma

EXPERIENCE
Frontend Developer - Northwind Logistics (2024 - present)
- Worked on frontend development for the internal dashboard.
- Fixed bugs reported by the operations team.

Junior Web Developer - Kite Studio (2023 - 2024)
- Built landing pages for clients using HTML and CSS.

EDUCATION
BS Software Engineering, University of Karachi, 2023

PROJECTS
Expense tracker: a small React app for tracking monthly spending.
"""

CONTEXT = {
    "resume_text": RESUME,
    "career_domain": {"code": "react_developer", "name": "React.js Developer"},
    "taxonomy": [
        {"skill": "HTML5", "aliases": ["html"], "requirement": "required"},
        {"skill": "CSS3", "aliases": ["css"], "requirement": "required"},
        {"skill": "JavaScript", "aliases": ["js"], "requirement": "required"},
        {"skill": "React.js", "aliases": ["react"], "requirement": "required"},
        {"skill": "TypeScript", "aliases": ["ts"], "requirement": "required"},
        {"skill": "Redux", "aliases": [], "requirement": "preferred"},
        {"skill": "REST APIs", "aliases": ["rest api"], "requirement": "required"},
        {"skill": "Git/GitHub", "aliases": ["git"], "requirement": "required"},
        {"skill": "Responsive Design", "aliases": [], "requirement": "preferred"},
        {"skill": "API Integration", "aliases": [], "requirement": "preferred"},
    ],
    "sections_present": ["summary", "skills", "experience", "education", "projects"],
    "required_sections": ["summary", "skills", "experience", "education"],
    "extracted": {
        "full_name": "Alex Mercer",
        "email": "alex.mercer@example.com",
        "experience": [
            {
                "title": "Frontend Developer",
                "company": "Northwind Logistics",
                "bullets": ["Worked on frontend development for the internal dashboard."],
            }
        ],
    },
}

JOB_DESCRIPTION = """React Developer - Fintech (Karachi, hybrid)
Requirements:
- 2+ years building production React applications
- Strong JavaScript and TypeScript
- Experience with Redux or similar state management
- Comfortable consuming REST APIs
- Git-based workflow
Nice to have: testing with Jest, CI/CD experience.
"""


def run(label: str, fn) -> int:
    started = time.perf_counter()
    try:
        payload = fn()
    except AIProviderError as exc:
        print(f"FAIL {label}: {exc}")
        return 1
    elapsed = time.perf_counter() - started
    print(f"OK   {label} in {elapsed:.1f}s, {len(json.dumps(payload))} chars")
    return 0


def main() -> int:
    api_key = os.environ.get("AI_PROVIDER_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("Set AI_PROVIDER_API_KEY (or GOOGLE_API_KEY) first.")
        return 2

    settings = Settings(
        ai_provider=os.environ.get("AI_PROVIDER", "google"),  # type: ignore[arg-type]
        ai_model=os.environ.get("AI_MODEL", ""),
        ai_base_url=os.environ.get("AI_BASE_URL", ""),
        ai_provider_api_key=api_key,
    )
    provider = build_provider(settings)
    print(f"provider={provider.name} model={provider.model}")

    def analysis() -> dict:
        result = provider.complete_json(
            task="resume_analysis",
            system=ANALYSIS_SYSTEM,
            user=build_analysis_user(CONTEXT),
            schema=ANALYSIS_SCHEMA,
        )
        issues = result.get("issues", [])
        print(f"     issues={len(issues)} strengths={len(result.get('strengths', []))}")
        for issue in issues[:3]:
            print(f"     - [{issue.get('severity')}] {issue.get('title')}")
        print(f"     summary: {str(result.get('summary', ''))[:160]}")
        return result

    def job_match() -> dict:
        result = provider.complete_json(
            task="jd_extraction",
            system=JD_SYSTEM,
            user=build_jd_user(JOB_DESCRIPTION),
            schema=JD_SCHEMA,
            max_tokens=900,
        )
        skills = result.get("required_skills", [])
        print(f"     required_skills={len(skills)}: {', '.join(str(s) for s in skills[:6])}")
        return result

    failures = run("analysis schema", analysis) + run("job description schema", job_match)
    print(f"tokens_used={provider.tokens_used}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
