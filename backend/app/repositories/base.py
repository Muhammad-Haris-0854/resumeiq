"""Repository interfaces.

The API and services depend on these abstractions, never on Supabase directly. That keeps the
domain testable without a database and makes a future storage swap a one-module change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

Row = dict[str, Any]


class UserRepository(ABC):
    @abstractmethod
    def get_profile(self, user_id: str) -> Row | None: ...

    @abstractmethod
    def update_profile(self, user_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def get_role(self, user_id: str) -> str: ...

    @abstractmethod
    def set_role(self, user_id: str, role: str) -> None: ...

    @abstractmethod
    def list_users(self, *, search: str | None, limit: int, offset: int) -> tuple[list[Row], int]: ...

    @abstractmethod
    def list_roles(self, user_ids: list[str]) -> dict[str, str]: ...


class ResumeRepository(ABC):
    @abstractmethod
    def create(self, user_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]: ...

    @abstractmethod
    def get(self, user_id: str, resume_id: str) -> Row | None: ...

    @abstractmethod
    def update(self, user_id: str, resume_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def soft_delete(self, user_id: str, resume_id: str) -> None: ...

    @abstractmethod
    def count_active(self, user_id: str) -> int: ...

    @abstractmethod
    def add_version(self, resume_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def get_version(self, version_id: str) -> Row | None: ...

    @abstractmethod
    def get_version_for_user(self, user_id: str, version_id: str) -> Row | None: ...

    @abstractmethod
    def list_versions(self, resume_id: str) -> list[Row]: ...

    @abstractmethod
    def next_version_number(self, resume_id: str) -> int: ...


class AnalysisRepository(ABC):
    @abstractmethod
    def create(self, payload: Row) -> Row: ...

    @abstractmethod
    def get(self, user_id: str, analysis_id: str) -> Row | None: ...

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> Row | None:
        """Unscoped read used by the worker, which has no user session."""

    @abstractmethod
    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]: ...

    @abstractmethod
    def update(self, analysis_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def delete(self, user_id: str, analysis_id: str) -> None: ...

    @abstractmethod
    def add_issues(self, analysis_id: str, issues: list[Row]) -> list[Row]: ...

    @abstractmethod
    def list_issues(self, analysis_id: str) -> list[Row]: ...

    @abstractmethod
    def update_issue(self, analysis_id: str, issue_id: str, patch: Row) -> Row | None: ...

    @abstractmethod
    def latest_score_for_resume(self, resume_id: str) -> int | None: ...


class TaxonomyRepository(ABC):
    @abstractmethod
    def list_domains(self) -> list[Row]: ...

    @abstractmethod
    def get_domain(self, domain_id: str) -> Row | None: ...

    @abstractmethod
    def get_domain_by_slug(self, slug: str) -> Row | None: ...

    @abstractmethod
    def domain_skills(self, domain_id: str) -> list[Row]: ...

    @abstractmethod
    def all_skills(self) -> list[Row]: ...

    @abstractmethod
    def search_skills(self, query: str, limit: int) -> list[Row]: ...

    @abstractmethod
    def create_domain(self, payload: Row) -> Row: ...

    @abstractmethod
    def update_domain(self, domain_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def replace_domain_skills(self, domain_id: str, skills: list[Row]) -> None: ...


class TemplateRepository(ABC):
    @abstractmethod
    def list(self, include_inactive: bool = False) -> list[Row]: ...

    @abstractmethod
    def get(self, template_id: str) -> Row | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> Row | None: ...

    @abstractmethod
    def upsert(self, payload: Row) -> Row: ...

    @abstractmethod
    def update(self, template_id: str, patch: Row) -> Row: ...


class GeneratedResumeRepository(ABC):
    @abstractmethod
    def create(self, user_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def get(self, user_id: str, generated_id: str) -> Row | None: ...

    @abstractmethod
    def list(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]: ...

    @abstractmethod
    def update(self, user_id: str, generated_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def add_version(self, generated_id: str, version: int, content: Row) -> None: ...

    @abstractmethod
    def list_versions(self, generated_id: str) -> list[Row]: ...

    @abstractmethod
    def get_version(self, generated_id: str, version: int) -> Row | None: ...


class JobRepository(ABC):
    @abstractmethod
    def create_description(self, user_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def get_description(self, user_id: str, description_id: str) -> Row | None: ...

    @abstractmethod
    def create_match(self, user_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def update_match(self, match_id: str, patch: Row) -> Row: ...

    @abstractmethod
    def get_match(self, user_id: str, match_id: str) -> Row | None: ...

    @abstractmethod
    def list_matches(self, user_id: str, *, limit: int, offset: int) -> tuple[list[Row], int]: ...


class BillingRepository(ABC):
    @abstractmethod
    def list_plans(self) -> list[Row]: ...

    @abstractmethod
    def get_plan_by_code(self, code: str) -> Row | None: ...

    @abstractmethod
    def get_subscription(self, user_id: str) -> Row | None: ...

    @abstractmethod
    def upsert_subscription(self, user_id: str, payload: Row) -> Row: ...

    @abstractmethod
    def record_transaction(self, payload: Row) -> Row: ...

    @abstractmethod
    def list_transactions(self, user_id: str, limit: int) -> list[Row]: ...

    @abstractmethod
    def usage_this_period(self, user_id: str, metric: str) -> int: ...

    @abstractmethod
    def record_usage(self, user_id: str, metric: str, quantity: int, metadata: Row) -> None: ...


class AdminRepository(ABC):
    @abstractmethod
    def metrics(self) -> Row: ...

    @abstractmethod
    def list_analyses(self, *, limit: int, offset: int) -> tuple[list[Row], int]: ...

    @abstractmethod
    def audit(self, actor_id: str | None, action: str, target_type: str | None, target_id: str | None, metadata: Row) -> None: ...

    @abstractmethod
    def get_setting(self, key: str) -> Row | None: ...

    @abstractmethod
    def set_setting(self, key: str, value: Row) -> None: ...


class StorageGateway(ABC):
    @abstractmethod
    def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> str: ...

    @abstractmethod
    def download(self, bucket: str, path: str) -> bytes: ...

    @abstractmethod
    def signed_url(self, bucket: str, path: str, ttl_seconds: int) -> str: ...

    @abstractmethod
    def delete(self, bucket: str, path: str) -> None: ...


class Repositories:
    """Bundle handed to request handlers through dependency injection."""

    def __init__(
        self,
        *,
        users: UserRepository,
        resumes: ResumeRepository,
        analyses: AnalysisRepository,
        taxonomy: TaxonomyRepository,
        templates: TemplateRepository,
        generated: GeneratedResumeRepository,
        jobs: JobRepository,
        billing: BillingRepository,
        admin: AdminRepository,
        storage: StorageGateway,
    ) -> None:
        self.users = users
        self.resumes = resumes
        self.analyses = analyses
        self.taxonomy = taxonomy
        self.templates = templates
        self.generated = generated
        self.jobs = jobs
        self.billing = billing
        self.admin = admin
        self.storage = storage
