from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SUPABASE_JWT_AUD", "authenticated")
os.environ.setdefault("PAYMENT_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("AI_PROVIDER", "deterministic")
os.environ.setdefault("CELERY_EAGER", "false")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "10000")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_principal, get_repositories  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.core.security import Principal, TokenVerifier  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.taxonomy_catalog import CATALOG, DOMAIN_SKILLS  # noqa: E402
from tests.fakes import build_fake_repositories  # noqa: E402

USER_ID = "11111111-1111-1111-1111-111111111111"
DOM_REACT = "a0000000-0000-4000-8000-000000000001"
DOM_BACKEND = "a0000000-0000-4000-8000-000000000002"
TPL_ATS = "b0000000-0000-4000-8000-000000000001"
TPL_PREMIUM = "b0000000-0000-4000-8000-000000000002"


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def verifier(settings: Settings) -> TokenVerifier:
    return TokenVerifier(settings)


def make_token(sub: str = USER_ID, *, secret: str = "test-jwt-secret", expires_in: int = 3600, **claims: Any) -> str:
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "email": "haris@example.com",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
        **claims,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token()}"}


def _domain_rows() -> list[dict[str, Any]]:
    return [
        {"id": DOM_REACT, "slug": "react-developer", "name": "React.js Developer", "description": "", "icon": "atom", "is_active": True},
        {"id": DOM_BACKEND, "slug": "backend-developer", "name": "Backend Developer", "description": "", "icon": "server", "is_active": True},
    ]


def _skill_rows() -> list[dict[str, Any]]:
    rows = []
    for index, entry in enumerate(CATALOG):
        rows.append(
            {
                "id": f"skill-{index}",
                "canonical_name": entry["canonical_name"],
                "aliases": entry["aliases"],
                "kind": entry["kind"],
                "category": entry["category"],
            }
        )
    return rows


def _link_skills(repos, domain_id: str, slug: str) -> None:
    mapping = DOMAIN_SKILLS[slug]
    by_name = {row["canonical_name"]: row for row in repos.taxonomy.all_skills()}
    links = []
    for level, names in mapping.items():
        for name in names:
            skill = by_name.get(name)
            if skill:
                links.append(
                    {
                        **skill,
                        "requirement": level,
                        "weight": {"required": 3.0, "preferred": 1.5, "optional": 0.5}[level],
                    }
                )
    repos.taxonomy.links[domain_id] = links


@pytest.fixture
def repos():
    bundle = build_fake_repositories(
        user_id=USER_ID,
        plan="free",
        role="user",
        domains=_domain_rows(),
        skills=_skill_rows(),
        templates=[
            {
                "id": TPL_ATS,
                "slug": "ats-friendly",
                "name": "ATS-Friendly",
                "description": "",
                "tier": "free",
                "is_ats_safe": True,
                "layout": {"accent": "#1e293b", "section_order": ["summary", "skills", "experience", "education"]},
                "is_active": True,
            },
            {
                "id": TPL_PREMIUM,
                "slug": "experienced-professional",
                "name": "Experienced Professional",
                "description": "",
                "tier": "premium",
                "is_ats_safe": True,
                "layout": {},
                "is_active": True,
            },
        ],
    )
    _link_skills(bundle, DOM_REACT, "react-developer")
    _link_skills(bundle, DOM_BACKEND, "backend-developer")
    return bundle


@pytest.fixture
def client(repos, monkeypatch):
    app = create_app()
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=USER_ID, email="haris@example.com", claims={"sub": USER_ID}
    )
    for module in (
        "app.api.routes.resumes",
        "app.api.routes.analyses",
        "app.api.routes.job_matches",
        "app.api.routes.builder",
    ):
        monkeypatch.setattr(f"{module}.enqueue", lambda *args, **kwargs: None)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(repos, monkeypatch):
    repos.users.roles[USER_ID] = "administrator"
    app = create_app()
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_principal] = lambda: Principal(user_id=USER_ID, email="haris@example.com")
    monkeypatch.setattr("app.api.routes.resumes.enqueue", lambda *args, **kwargs: None)
    with TestClient(app) as test_client:
        yield test_client


RESUME_TEXT = """Muhammad Haris
haris@example.com | +92 300 1234567 | github.com/haris

Professional Summary
Frontend developer with 3 years of experience building React applications for fintech products.

Technical Skills
React, Redux, JavaScript, HTML, CSS, Git

Work Experience
Frontend Developer | Systems Ltd | 2022 - Present
Responsible for building dashboards.
Worked on API integration for payment flows.
Built a component library used by 4 teams, cutting UI defects by 30%.

Education
BS Software Engineering | FAST NUClear University | 2018 - 2022

Projects
ResumeIQ
A resume analysis platform built with React and FastAPI serving 1200 students.
"""
