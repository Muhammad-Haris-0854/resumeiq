"""In-memory repositories for tests.

They implement the same interfaces as the Supabase adapters, so route tests exercise real
handler logic without a database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from app.repositories.base import (
    AdminRepository,
    AnalysisRepository,
    BillingRepository,
    GeneratedResumeRepository,
    JobRepository,
    Repositories,
    ResumeRepository,
    StorageGateway,
    TaxonomyRepository,
    TemplateRepository,
    UserRepository,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _id() -> str:
    return str(uuid.uuid4())


class FakeUsers(UserRepository):
    def __init__(self, profiles: list[dict[str, Any]] | None = None, roles: dict[str, str] | None = None):
        self.profiles = {row["id"]: row for row in (profiles or [])}
        self.roles = roles or {}

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profiles.get(user_id)

    def ensure_profile(self, user_id: str, email: str | None) -> dict[str, Any]:
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "id": user_id, "email": email or "", "plan": "free", "created_at": _now()
            }
        return self.profiles[user_id]

    def update_profile(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        row = self.profiles.setdefault(
            user_id, {"id": user_id, "email": "", "plan": "free", "created_at": _now()}
        )
        row.update(patch)
        return row

    def get_role(self, user_id: str) -> str:
        return self.roles.get(user_id, "user")

    def set_role(self, user_id: str, role: str) -> None:
        self.roles[user_id] = role

    def list_users(self, *, search: str | None, limit: int, offset: int):
        rows = list(self.profiles.values())
        if search:
            rows = [r for r in rows if search.lower() in str(r.get("email", "")).lower()]
        return rows[offset : offset + limit], len(rows)

    def list_roles(self, user_ids: list[str]) -> dict[str, str]:
        return {uid: self.roles.get(uid, "user") for uid in user_ids}


class FakeResumes(ResumeRepository):
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def create(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "id": _id(),
            "user_id": user_id,
            "created_at": _now(),
            "updated_at": _now(),
            "deleted_at": None,
            "status": payload.get("status", "uploaded"),
            "source": payload.get("source", "upload"),
            **payload,
        }
        self.rows[row["id"]] = row
        return row

    def list(self, user_id: str, *, limit: int, offset: int):
        rows = [r for r in self.rows.values() if r["user_id"] == user_id and not r["deleted_at"]]
        return rows[offset : offset + limit], len(rows)

    def get(self, user_id: str, resume_id: str) -> dict[str, Any] | None:
        row = self.rows.get(resume_id)
        return row if row and row["user_id"] == user_id and not row["deleted_at"] else None

    def update(self, user_id: str, resume_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        row = self.rows[resume_id]
        row.update(patch)
        return row

    def update_by_id(self, resume_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        row = self.rows[resume_id]
        row.update(patch)
        return row

    def soft_delete(self, user_id: str, resume_id: str) -> None:
        self.rows[resume_id]["deleted_at"] = _now()

    def count_active(self, user_id: str) -> int:
        return len([r for r in self.rows.values() if r["user_id"] == user_id and not r["deleted_at"]])

    def add_version(self, resume_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": _id(), "resume_id": resume_id, "created_at": _now(), **payload}
        self.versions[row["id"]] = row
        return row

    def get_version(self, version_id: str) -> dict[str, Any] | None:
        return self.versions.get(version_id)

    def get_version_for_user(self, user_id: str, version_id: str) -> dict[str, Any] | None:
        version = self.versions.get(version_id)
        if not version:
            return None
        return version if self.get(user_id, version["resume_id"]) else None

    def list_versions(self, resume_id: str) -> list[dict[str, Any]]:
        return sorted(
            [v for v in self.versions.values() if v["resume_id"] == resume_id],
            key=lambda v: v["version"],
            reverse=True,
        )

    def next_version_number(self, resume_id: str) -> int:
        existing = [v["version"] for v in self.versions.values() if v["resume_id"] == resume_id]
        return max(existing) + 1 if existing else 1


class FakeAnalyses(AnalysisRepository):
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.issues: dict[str, list[dict[str, Any]]] = {}

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": _id(), "created_at": _now(), "status": "queued", **payload}
        self.rows[row["id"]] = row
        return row

    def get(self, user_id: str, analysis_id: str) -> dict[str, Any] | None:
        row = self.rows.get(analysis_id)
        return row if row and row["user_id"] == user_id else None

    def get_by_id(self, analysis_id: str) -> dict[str, Any] | None:
        return self.rows.get(analysis_id)

    def list(self, user_id: str, *, limit: int, offset: int):
        rows = [r for r in self.rows.values() if r["user_id"] == user_id]
        return rows[offset : offset + limit], len(rows)

    def update(self, analysis_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        self.rows[analysis_id].update(patch)
        return self.rows[analysis_id]

    def delete(self, user_id: str, analysis_id: str) -> None:
        self.rows.pop(analysis_id, None)

    def add_issues(self, analysis_id: str, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        stored = []
        for issue in issues:
            row = {"id": _id(), "analysis_id": analysis_id, "status": "open", **issue}
            stored.append(row)
        self.issues.setdefault(analysis_id, []).extend(stored)
        return stored

    def list_issues(self, analysis_id: str) -> list[dict[str, Any]]:
        return self.issues.get(analysis_id, [])

    def update_issue(self, analysis_id: str, issue_id: str, patch: dict[str, Any]):
        for issue in self.issues.get(analysis_id, []):
            if issue["id"] == issue_id:
                issue.update(patch)
                return issue
        return None

    def latest_score_for_resume(self, resume_id: str) -> int | None:
        scores = [
            r.get("overall_score")
            for r in self.rows.values()
            if r.get("resume_id") == resume_id and r.get("status") == "ready"
        ]
        return scores[-1] if scores else None


class FakeTaxonomy(TaxonomyRepository):
    def __init__(self, domains: list[dict[str, Any]] | None = None, skills: list[dict[str, Any]] | None = None):
        self.domains = {row["id"]: row for row in (domains or [])}
        self.skills = {row["id"]: row for row in (skills or [])}
        self.links: dict[str, list[dict[str, Any]]] = {}

    def list_domains(self):
        return [dict(row, domain_skills=[{"skill_id": s["id"]} for s in self.domain_skills(row["id"])]) for row in self.domains.values()]

    def get_domain(self, domain_id: str):
        return self.domains.get(domain_id)

    def get_domain_by_slug(self, slug: str):
        return next((row for row in self.domains.values() if row["slug"] == slug), None)

    def domain_skills(self, domain_id: str):
        return self.links.get(domain_id, [])

    def all_skills(self):
        return list(self.skills.values())

    def search_skills(self, query: str, limit: int):
        q = query.lower()
        return [row for row in self.skills.values() if q in row["canonical_name"].lower()][:limit]

    def create_domain(self, payload: dict[str, Any]):
        row = {"id": _id(), **payload}
        self.domains[row["id"]] = row
        return row

    def update_domain(self, domain_id: str, patch: dict[str, Any]):
        self.domains[domain_id].update(patch)
        return self.domains[domain_id]

    def replace_domain_skills(self, domain_id: str, skills: list[dict[str, Any]]) -> None:
        resolved = []
        for entry in skills:
            skill = self.skills[entry["skill_id"]]
            resolved.append({**skill, **entry})
        self.links[domain_id] = resolved


class FakeTemplates(TemplateRepository):
    def __init__(self, rows: list[dict[str, Any]] | None = None):
        self.rows = {row["id"]: row for row in (rows or [])}

    def list(self, include_inactive: bool = False):
        return [r for r in self.rows.values() if include_inactive or r.get("is_active", True)]

    def get(self, template_id: str):
        return self.rows.get(template_id)

    def get_by_slug(self, slug: str):
        return next((r for r in self.rows.values() if r["slug"] == slug), None)

    def upsert(self, payload: dict[str, Any]):
        existing = self.get_by_slug(payload["slug"])
        if existing:
            existing.update(payload)
            return existing
        row = {"id": _id(), "is_active": True, **payload}
        self.rows[row["id"]] = row
        return row

    def update(self, template_id: str, patch: dict[str, Any]):
        self.rows[template_id].update(patch)
        return self.rows[template_id]


class FakeGenerated(GeneratedResumeRepository):
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, list[dict[str, Any]]] = {}

    def create(self, user_id: str, payload: dict[str, Any]):
        row = {"id": _id(), "user_id": user_id, "created_at": _now(), "updated_at": _now(), **payload}
        self.rows[row["id"]] = row
        return row

    def get(self, user_id: str, generated_id: str):
        row = self.rows.get(generated_id)
        return row if row and row["user_id"] == user_id else None

    def list(self, user_id: str, *, limit: int, offset: int):
        rows = [r for r in self.rows.values() if r["user_id"] == user_id]
        return rows[offset : offset + limit], len(rows)

    def update(self, user_id: str, generated_id: str, patch: dict[str, Any]):
        self.rows[generated_id].update(patch)
        return self.rows[generated_id]

    def add_version(self, generated_id: str, version: int, content: dict[str, Any]) -> None:
        self.versions.setdefault(generated_id, []).append({"version": version, "content": content})

    def list_versions(self, generated_id: str):
        return [{"version": v["version"]} for v in self.versions.get(generated_id, [])]

    def get_version(self, generated_id: str, version: int):
        return next(
            (v for v in self.versions.get(generated_id, []) if v["version"] == version), None
        )


class FakeJobs(JobRepository):
    def __init__(self) -> None:
        self.descriptions: dict[str, dict[str, Any]] = {}
        self.matches: dict[str, dict[str, Any]] = {}

    def create_description(self, user_id: str, payload: dict[str, Any]):
        row = {"id": _id(), "user_id": user_id, "created_at": _now(), **payload}
        self.descriptions[row["id"]] = row
        return row

    def get_description(self, user_id: str, description_id: str):
        row = self.descriptions.get(description_id)
        return row if row and row["user_id"] == user_id else None

    def create_match(self, user_id: str, payload: dict[str, Any]):
        row = {"id": _id(), "user_id": user_id, "created_at": _now(), "status": "queued", **payload}
        self.matches[row["id"]] = row
        return row

    def update_match(self, match_id: str, patch: dict[str, Any]):
        self.matches[match_id].update(patch)
        return self.matches[match_id]

    def get_match(self, user_id: str, match_id: str):
        row = self.matches.get(match_id)
        return row if row and row["user_id"] == user_id else None

    def list_matches(self, user_id: str, *, limit: int, offset: int):
        rows = [r for r in self.matches.values() if r["user_id"] == user_id]
        return rows[offset : offset + limit], len(rows)


class FakeBilling(BillingRepository):
    def __init__(self, plans: list[dict[str, Any]] | None = None):
        self.plans = {row["code"]: row for row in (plans or [])}
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.transactions: list[dict[str, Any]] = []
        self.usage: list[dict[str, Any]] = []

    def list_plans(self):
        return list(self.plans.values())

    def get_plan_by_code(self, code: str):
        return self.plans.get(code)

    def get_subscription(self, user_id: str):
        return self.subscriptions.get(user_id)

    def upsert_subscription(self, user_id: str, payload: dict[str, Any]):
        row = {"id": _id(), "user_id": user_id, **payload}
        self.subscriptions[user_id] = row
        return row

    def record_transaction(self, payload: dict[str, Any]):
        row = {"id": _id(), "created_at": _now(), **payload}
        self.transactions.append(row)
        return row

    def list_transactions(self, user_id: str, limit: int):
        return [t for t in self.transactions if t["user_id"] == user_id][:limit]

    def usage_this_period(self, user_id: str, metric: str) -> int:
        period = date.today().replace(day=1).isoformat()
        return sum(
            int(u["quantity"])
            for u in self.usage
            if u["user_id"] == user_id and u["metric"] == metric and u["period_start"] == period
        )

    def record_usage(self, user_id: str, metric: str, quantity: int, metadata: dict[str, Any]) -> None:
        self.usage.append(
            {
                "user_id": user_id,
                "metric": metric,
                "quantity": quantity,
                "metadata": metadata,
                "period_start": date.today().replace(day=1).isoformat(),
            }
        )


class FakeAdmin(AdminRepository):
    def __init__(self, users: FakeUsers | None = None, billing: FakeBilling | None = None):
        self.audit_entries: list[dict[str, Any]] = []
        self.settings: dict[str, dict[str, Any]] = {}
        self._users = users
        self._billing = billing

    def metrics(self):
        total = len(self._users.profiles) if self._users else 0
        paid = sum(1 for p in (self._users.profiles.values() if self._users else []) if p.get("plan") in {"pro", "premium"})
        return {
            "total_users": total,
            "paid_users": paid,
            "free_users": total - paid,
            "active_subscriptions": len(self._billing.subscriptions) if self._billing else 0,
            "mrr_cents": 0,
            "analyses_this_month": 0,
            "ai_tokens_this_month": 0,
            "failed_analyses_this_month": 0,
        }

    def list_analyses(self, *, limit: int, offset: int):
        return [], 0

    def audit(self, actor_id, action, target_type, target_id, metadata) -> None:
        self.audit_entries.append({"action": action, "actor_id": actor_id, "metadata": metadata})

    def get_setting(self, key: str):
        return self.settings.get(key)

    def set_setting(self, key: str, value: dict[str, Any]) -> None:
        self.settings[key] = {"key": key, "value": value}


class FakeStorage(StorageGateway):
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> str:
        self.objects[(bucket, path)] = data
        return path

    def download(self, bucket: str, path: str) -> bytes:
        return self.objects[(bucket, path)]

    def signed_url(self, bucket: str, path: str, ttl_seconds: int) -> str:
        return f"https://storage.test/{bucket}/{path}?ttl={ttl_seconds}"

    def delete(self, bucket: str, path: str) -> None:
        self.objects.pop((bucket, path), None)


def build_fake_repositories(
    *,
    user_id: str,
    plan: str = "free",
    role: str = "user",
    domains: list[dict[str, Any]] | None = None,
    skills: list[dict[str, Any]] | None = None,
    templates: list[dict[str, Any]] | None = None,
) -> Repositories:
    users = FakeUsers(
        profiles=[
            {
                "id": user_id,
                "email": "haris@example.com",
                "full_name": "Muhammad Haris",
                "plan": plan,
                "created_at": _now(),
                "onboarding_completed": True,
            }
        ],
        roles={user_id: role},
    )
    billing = FakeBilling(
        plans=[
            {
                "id": "plan-free",
                "code": "free",
                "name": "Free",
                "monthly_price_cents": 0,
                "annual_price_cents": 0,
                "analysis_quota": 2,
                "max_resumes": 2,
                "features": {},
                "is_active": True,
            },
            {
                "id": "plan-pro",
                "code": "pro",
                "name": "Pro",
                "monthly_price_cents": 1200,
                "annual_price_cents": 11500,
                "analysis_quota": 20,
                "max_resumes": 10,
                "features": {},
                "is_active": True,
            },
        ]
    )
    taxonomy = FakeTaxonomy(domains=domains, skills=skills)
    return Repositories(
        users=users,
        resumes=FakeResumes(),
        analyses=FakeAnalyses(),
        taxonomy=taxonomy,
        templates=FakeTemplates(rows=templates),
        generated=FakeGenerated(),
        jobs=FakeJobs(),
        billing=billing,
        admin=FakeAdmin(users=users, billing=billing),
        storage=FakeStorage(),
    )
