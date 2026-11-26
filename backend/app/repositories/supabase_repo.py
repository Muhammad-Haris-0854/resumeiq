"""Supabase/PostgREST implementations of the repository interfaces."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.errors import NotFound
from app.core.logging import get_logger
from app.repositories.base import (
    AdminRepository,
    AnalysisRepository,
    BillingRepository,
    GeneratedResumeRepository,
    JobRepository,
    Repositories,
    ResumeRepository,
    Row,
    StorageGateway,
    TaxonomyRepository,
    TemplateRepository,
    UserRepository,
)

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _plain(value: Any) -> Any:
    if isinstance(value, UUID | datetime | date):
        return str(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


class _Base:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _table(self, name: str):
        return self._client.table(name)

    @staticmethod
    def _one(response: Any) -> Row | None:
        data = getattr(response, "data", None) or []
        return data[0] if data else None

    @staticmethod
    def _all(response: Any) -> list[Row]:
        return list(getattr(response, "data", None) or [])

    @staticmethod
    def _count(response: Any) -> int:
        count = getattr(response, "count", None)
        if count is not None:
            return int(count)
        return len(getattr(response, "data", None) or [])


class SupabaseUserRepository(_Base, UserRepository):
    def get_profile(self, user_id: str) -> Row | None:
        return self._one(self._table("profiles").select("*").eq("id", user_id).limit(1).execute())

    def update_profile(self, user_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("profiles")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", user_id)
            .execute()
        )
        if not row:
            raise NotFound("Profile not found")
        return row

    def get_role(self, user_id: str) -> str:
        row = self._one(
            self._table("user_roles").select("role").eq("user_id", user_id).limit(1).execute()
        )
        return (row or {}).get("role", "user")

    def set_role(self, user_id: str, role: str) -> None:
        self._table("user_roles").upsert(
            {"user_id": user_id, "role": role}, on_conflict="user_id"
        ).execute()

    def list_users(self, *, search: str | None, limit: int, offset: int) -> tuple[list[Row], int]:
        query = self._table("profiles").select("*", count="exact")
        if search:
            query = query.or_(f"email.ilike.%{search}%,full_name.ilike.%{search}%")
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return self._all(response), self._count(response)

    def list_roles(self, user_ids: list[str]) -> dict[str, str]:
        if not user_ids:
            return {}
        rows = self._all(
            self._table("user_roles").select("user_id,role").in_("user_id", user_ids).execute()
        )
        return {row["user_id"]: row["role"] for row in rows}


class SupabaseResumeRepository(_Base, ResumeRepository):
    def create(self, user_id: str, payload: Row) -> Row:
        row = self._one(
            self._table("resumes")
            .insert({**_plain(payload), "user_id": user_id, "created_at": _now(), "updated_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Resume could not be created")
        return row

    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]:
        response = (
            self._table("resumes")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return self._all(response), self._count(response)

    def get(self, user_id: str, resume_id: str) -> Row | None:
        return self._one(
            self._table("resumes")
            .select("*")
            .eq("id", resume_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )

    def update(self, user_id: str, resume_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("resumes")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", resume_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not row:
            raise NotFound("Resume not found")
        return row

    def soft_delete(self, user_id: str, resume_id: str) -> None:
        self._table("resumes").update({"deleted_at": _now()}).eq("id", resume_id).eq(
            "user_id", user_id
        ).execute()

    def count_active(self, user_id: str) -> int:
        response = (
            self._table("resumes")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return self._count(response)

    def add_version(self, resume_id: str, payload: Row) -> Row:
        row = self._one(
            self._table("resume_versions")
            .insert({**_plain(payload), "resume_id": resume_id, "created_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Resume version could not be created")
        return row

    def get_version(self, version_id: str) -> Row | None:
        return self._one(
            self._table("resume_versions").select("*").eq("id", version_id).limit(1).execute()
        )

    def get_version_for_user(self, user_id: str, version_id: str) -> Row | None:
        version = self.get_version(version_id)
        if not version:
            return None
        resume = self.get(user_id, version["resume_id"])
        return version if resume else None

    def list_versions(self, resume_id: str) -> list[Row]:
        return self._all(
            self._table("resume_versions")
            .select("*")
            .eq("resume_id", resume_id)
            .order("version", desc=True)
            .execute()
        )

    def next_version_number(self, resume_id: str) -> int:
        rows = self._all(
            self._table("resume_versions")
            .select("version")
            .eq("resume_id", resume_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        return (rows[0]["version"] + 1) if rows else 1


class SupabaseAnalysisRepository(_Base, AnalysisRepository):
    def create(self, payload: Row) -> Row:
        row = self._one(
            self._table("resume_analyses")
            .insert({**_plain(payload), "created_at": _now(), "updated_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Analysis could not be created")
        return row

    def get(self, user_id: str, analysis_id: str) -> Row | None:
        return self._one(
            self._table("resume_analyses")
            .select("*")
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]:
        response = (
            self._table("resume_analyses")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return self._all(response), self._count(response)

    def update(self, analysis_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("resume_analyses")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", analysis_id)
            .execute()
        )
        if not row:
            raise NotFound("Analysis not found")
        return row

    def delete(self, user_id: str, analysis_id: str) -> None:
        self._table("resume_analyses").delete().eq("id", analysis_id).eq(
            "user_id", user_id
        ).execute()

    def add_issues(self, analysis_id: str, issues: list[Row]) -> list[Row]:
        if not issues:
            return []
        rows = [
            {**_plain(issue), "analysis_id": analysis_id, "created_at": _now(), "updated_at": _now()}
            for issue in issues
        ]
        return self._all(self._table("analysis_issues").insert(rows).execute())

    def list_issues(self, analysis_id: str) -> list[Row]:
        return self._all(
            self._table("analysis_issues")
            .select("*")
            .eq("analysis_id", analysis_id)
            .order("sort_order")
            .execute()
        )

    def update_issue(self, analysis_id: str, issue_id: str, patch: Row) -> Row | None:
        return self._one(
            self._table("analysis_issues")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", issue_id)
            .eq("analysis_id", analysis_id)
            .execute()
        )

    def latest_score_for_resume(self, resume_id: str) -> int | None:
        rows = self._all(
            self._table("resume_analyses")
            .select("overall_score")
            .eq("resume_id", resume_id)
            .eq("status", "ready")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return rows[0]["overall_score"] if rows else None


class SupabaseTaxonomyRepository(_Base, TaxonomyRepository):
    def list_domains(self) -> list[Row]:
        return self._all(
            self._table("career_domains")
            .select("*, domain_skills(skill_id)")
            .eq("is_active", True)
            .order("sort_order")
            .execute()
        )

    def get_domain(self, domain_id: str) -> Row | None:
        return self._one(
            self._table("career_domains").select("*").eq("id", domain_id).limit(1).execute()
        )

    def get_domain_by_slug(self, slug: str) -> Row | None:
        return self._one(
            self._table("career_domains").select("*").eq("slug", slug).limit(1).execute()
        )

    def domain_skills(self, domain_id: str) -> list[Row]:
        rows = self._all(
            self._table("domain_skills")
            .select("requirement,weight,skills(id,canonical_name,aliases,kind,category)")
            .eq("domain_id", domain_id)
            .execute()
        )
        result: list[Row] = []
        for row in rows:
            skill = row.get("skills") or {}
            result.append(
                {
                    "id": skill.get("id"),
                    "canonical_name": skill.get("canonical_name"),
                    "aliases": skill.get("aliases") or [],
                    "kind": skill.get("kind"),
                    "category": skill.get("category"),
                    "requirement": row.get("requirement"),
                    "weight": float(row.get("weight") or 1.0),
                }
            )
        return result

    def all_skills(self) -> list[Row]:
        return self._all(self._table("skills").select("*").order("canonical_name").execute())

    def search_skills(self, query: str, limit: int) -> list[Row]:
        like = f"%{query}%"
        return self._all(
            self._table("skills")
            .select("*")
            .or_(f"canonical_name.ilike.{like},category.ilike.{like}")
            .order("canonical_name")
            .limit(limit)
            .execute()
        )

    def create_domain(self, payload: Row) -> Row:
        row = self._one(self._table("career_domains").insert(_plain(payload)).execute())
        if not row:
            raise NotFound("Domain could not be created")
        return row

    def update_domain(self, domain_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("career_domains")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", domain_id)
            .execute()
        )
        if not row:
            raise NotFound("Domain not found")
        return row

    def replace_domain_skills(self, domain_id: str, skills: list[Row]) -> None:
        self._table("domain_skills").delete().eq("domain_id", domain_id).execute()
        if skills:
            rows = [{**skill, "domain_id": domain_id} for skill in skills]
            self._table("domain_skills").insert(rows).execute()


class SupabaseTemplateRepository(_Base, TemplateRepository):
    def list(self, include_inactive: bool = False) -> list[Row]:
        query = self._table("resume_templates").select("*")
        if not include_inactive:
            query = query.eq("is_active", True)
        return self._all(query.order("sort_order").execute())

    def get(self, template_id: str) -> Row | None:
        return self._one(
            self._table("resume_templates").select("*").eq("id", template_id).limit(1).execute()
        )

    def get_by_slug(self, slug: str) -> Row | None:
        return self._one(
            self._table("resume_templates").select("*").eq("slug", slug).limit(1).execute()
        )

    def upsert(self, payload: Row) -> Row:
        row = self._one(
            self._table("resume_templates")
            .upsert(_plain(payload), on_conflict="slug")
            .execute()
        )
        if not row:
            raise NotFound("Template could not be saved")
        return row

    def update(self, template_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("resume_templates")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", template_id)
            .execute()
        )
        if not row:
            raise NotFound("Template not found")
        return row


class SupabaseGeneratedResumeRepository(_Base, GeneratedResumeRepository):
    def create(self, user_id: str, payload: Row) -> Row:
        row = self._one(
            self._table("generated_resumes")
            .insert({**_plain(payload), "user_id": user_id, "created_at": _now(), "updated_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Resume could not be created")
        return row

    def get(self, user_id: str, generated_id: str) -> Row | None:
        return self._one(
            self._table("generated_resumes")
            .select("*")
            .eq("id", generated_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]:
        response = (
            self._table("generated_resumes")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return self._all(response), self._count(response)

    def update(self, user_id: str, generated_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("generated_resumes")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", generated_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not row:
            raise NotFound("Resume not found")
        return row

    def add_version(self, generated_id: str, version: int, content: Row) -> None:
        self._table("generated_resume_versions").upsert(
            {"generated_resume_id": generated_id, "version": version, "content": _plain(content)},
            on_conflict="generated_resume_id,version",
        ).execute()

    def list_versions(self, generated_id: str) -> list[Row]:
        return self._all(
            self._table("generated_resume_versions")
            .select("version,created_at")
            .eq("generated_resume_id", generated_id)
            .order("version", desc=True)
            .execute()
        )

    def get_version(self, generated_id: str, version: int) -> Row | None:
        return self._one(
            self._table("generated_resume_versions")
            .select("*")
            .eq("generated_resume_id", generated_id)
            .eq("version", version)
            .limit(1)
            .execute()
        )


class SupabaseJobRepository(_Base, JobRepository):
    def create_description(self, user_id: str, payload: Row) -> Row:
        row = self._one(
            self._table("job_descriptions")
            .insert({**_plain(payload), "user_id": user_id, "created_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Job description could not be saved")
        return row

    def get_description(self, user_id: str, description_id: str) -> Row | None:
        return self._one(
            self._table("job_descriptions")
            .select("*")
            .eq("id", description_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

    def create_match(self, user_id: str, payload: Row) -> Row:
        row = self._one(
            self._table("job_matches")
            .insert({**_plain(payload), "user_id": user_id, "created_at": _now(), "updated_at": _now()})
            .execute()
        )
        if not row:
            raise NotFound("Match could not be created")
        return row

    def update_match(self, match_id: str, patch: Row) -> Row:
        row = self._one(
            self._table("job_matches")
            .update({**_plain(patch), "updated_at": _now()})
            .eq("id", match_id)
            .execute()
        )
        if not row:
            raise NotFound("Match not found")
        return row

    def get_match(self, user_id: str, match_id: str) -> Row | None:
        return self._one(
            self._table("job_matches")
            .select("*")
            .eq("id", match_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

    def list_matches(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]:
        response = (
            self._table("job_matches")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return self._all(response), self._count(response)


class SupabaseBillingRepository(_Base, BillingRepository):
    def list_plans(self) -> list[Row]:
        return self._all(
            self._table("subscription_plans").select("*").eq("is_active", True).order("sort_order").execute()
        )

    def get_plan_by_code(self, code: str) -> Row | None:
        return self._one(
            self._table("subscription_plans").select("*").eq("code", code).limit(1).execute()
        )

    def get_subscription(self, user_id: str) -> Row | None:
        return self._one(
            self._table("subscriptions")
            .select("*, subscription_plans(code,name)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

    def upsert_subscription(self, user_id: str, payload: Row) -> Row:
        existing = self._one(
            self._table("subscriptions")
            .select("id")
            .eq("user_id", user_id)
            .in_("status", ["active", "trialing", "past_due", "incomplete"])
            .limit(1)
            .execute()
        )
        body = {**_plain(payload), "user_id": user_id, "updated_at": _now()}
        if existing:
            row = self._one(
                self._table("subscriptions").update(body).eq("id", existing["id"]).execute()
            )
        else:
            row = self._one(
                self._table("subscriptions").insert({**body, "created_at": _now()}).execute()
            )
        if not row:
            raise NotFound("Subscription could not be saved")
        return row

    def record_transaction(self, payload: Row) -> Row:
        row = self._one(
            self._table("payment_transactions")
            .upsert({**_plain(payload), "created_at": _now()}, on_conflict="provider_transaction_id")
            .execute()
        )
        if not row:
            raise NotFound("Transaction could not be recorded")
        return row

    def list_transactions(self, user_id: str, limit: int) -> list[Row]:
        return self._all(
            self._table("payment_transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

    def usage_this_period(self, user_id: str, metric: str) -> int:
        period = date.today().replace(day=1).isoformat()
        rows = self._all(
            self._table("usage_records")
            .select("quantity")
            .eq("user_id", user_id)
            .eq("metric", metric)
            .eq("period_start", period)
            .execute()
        )
        return sum(int(row.get("quantity") or 0) for row in rows)

    def record_usage(self, user_id: str, metric: str, quantity: int, metadata: Row) -> None:
        self._table("usage_records").insert(
            {
                "user_id": user_id,
                "metric": metric,
                "quantity": quantity,
                "period_start": date.today().replace(day=1).isoformat(),
                "metadata": _plain(metadata),
            }
        ).execute()


class SupabaseAdminRepository(_Base, AdminRepository):
    def metrics(self) -> Row:
        period = date.today().replace(day=1).isoformat()
        profiles = self._all(self._table("profiles").select("plan").execute())
        subscriptions = self._all(
            self._table("subscriptions")
            .select("id,interval,subscription_plans(monthly_price_cents,annual_price_cents)")
            .in_("status", ["active", "trialing"])
            .execute()
        )
        analyses = self._all(
            self._table("resume_analyses")
            .select("status,ai_tokens_used,created_at")
            .gte("created_at", period)
            .execute()
        )
        paid = sum(1 for row in profiles if row.get("plan") in ("pro", "premium"))
        mrr = 0
        for sub in subscriptions:
            plan = sub.get("subscription_plans") or {}
            if sub.get("interval") == "year":
                mrr += int(plan.get("annual_price_cents") or 0) // 12
            else:
                mrr += int(plan.get("monthly_price_cents") or 0)
        return {
            "total_users": len(profiles),
            "paid_users": paid,
            "free_users": len(profiles) - paid,
            "active_subscriptions": len(subscriptions),
            "mrr_cents": mrr,
            "analyses_this_month": len(analyses),
            "ai_tokens_this_month": sum(int(a.get("ai_tokens_used") or 0) for a in analyses),
            "failed_analyses_this_month": sum(1 for a in analyses if a.get("status") == "failed"),
        }

    def list_analyses(self, *, limit: int, offset: int) -> tuple[list[Row], int]:
        response = (
            self._table("resume_analyses")
            .select("*", count="exact")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return self._all(response), self._count(response)

    def audit(
        self,
        actor_id: str | None,
        action: str,
        target_type: str | None,
        target_id: str | None,
        metadata: Row,
    ) -> None:
        try:
            self._table("audit_logs").insert(
                {
                    "actor_id": actor_id,
                    "action": action,
                    "target_type": target_type,
                    "target_id": target_id,
                    "metadata": _plain(metadata),
                }
            ).execute()
        except Exception:  # auditing must never break the request
            logger.warning("audit_write_failed", extra={"extra_fields": {"action": action}})

    def get_setting(self, key: str) -> Row | None:
        return self._one(self._table("app_settings").select("*").eq("key", key).limit(1).execute())

    def set_setting(self, key: str, value: Row) -> None:
        self._table("app_settings").upsert(
            {"key": key, "value": value, "updated_at": _now()}, on_conflict="key"
        ).execute()


class SupabaseStorageGateway(StorageGateway):
    def __init__(self, client: Client) -> None:
        self._client = client

    def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> str:
        self._client.storage.from_(bucket).upload(
            path=path, file=data, file_options={"content-type": content_type, "upsert": "true"}
        )
        return path

    def download(self, bucket: str, path: str) -> bytes:
        return self._client.storage.from_(bucket).download(path)

    def signed_url(self, bucket: str, path: str, ttl_seconds: int) -> str:
        response = self._client.storage.from_(bucket).create_signed_url(path, ttl_seconds)
        url = response.get("signedURL") or response.get("signedUrl") or ""
        if not url:
            raise NotFound("Could not create a download link")
        return url

    def delete(self, bucket: str, path: str) -> None:
        try:
            self._client.storage.from_(bucket).remove([path])
        except Exception:
            logger.warning("storage_delete_failed", extra={"extra_fields": {"path": path}})


def build_repositories(client: Client | None = None) -> Repositories:
    from app.integrations.supabase.client import get_service_client

    client = client or get_service_client()
    return Repositories(
        users=SupabaseUserRepository(client),
        resumes=SupabaseResumeRepository(client),
        analyses=SupabaseAnalysisRepository(client),
        taxonomy=SupabaseTaxonomyRepository(client),
        templates=SupabaseTemplateRepository(client),
        generated=SupabaseGeneratedResumeRepository(client),
        jobs=SupabaseJobRepository(client),
        billing=SupabaseBillingRepository(client),
        admin=SupabaseAdminRepository(client),
        storage=SupabaseStorageGateway(client),
    )
