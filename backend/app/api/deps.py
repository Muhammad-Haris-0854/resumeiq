"""FastAPI dependencies: identity, authorisation, entitlements, providers, queueing."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from fastapi import Depends, Header, Request

from app.core.config import Settings, get_settings
from app.core.errors import Forbidden, Unauthenticated
from app.core.security import Principal, TokenVerifier
from app.integrations.payments import PaymentProvider, build_payment_provider
from app.models.enums import PlanCode, Role
from app.repositories.base import Repositories, Row
from app.repositories.supabase_repo import build_repositories
from app.services.ai import AIProvider, build_provider
from app.services.entitlements import Entitlements, resolve_entitlements


@lru_cache
def get_verifier() -> TokenVerifier:
    return TokenVerifier(get_settings())


@lru_cache
def get_repositories() -> Repositories:
    return build_repositories()


@lru_cache
def get_ai_provider() -> AIProvider:
    return build_provider()


@lru_cache
def get_payments() -> PaymentProvider:
    return build_payment_provider()


def get_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthenticated("Sign in to continue")
    token = authorization.split(" ", 1)[1].strip()
    return get_verifier().verify(token)


@dataclass(frozen=True)
class CurrentUser:
    principal: Principal
    profile: Row
    role: Role

    @property
    def id(self) -> str:
        return self.principal.user_id

    @property
    def email(self) -> str:
        return str(self.profile.get("email") or self.principal.email or "")

    @property
    def plan(self) -> PlanCode:
        try:
            return PlanCode(str(self.profile.get("plan", "free")))
        except ValueError:
            return PlanCode.FREE

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMINISTRATOR


def current_user(
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
) -> CurrentUser:
    profile = repos.users.get_profile(principal.user_id)
    if profile is None:
        # Accounts created before the schema existed, or before the signup trigger ran, have no
        # profile row. Create it on first use instead of locking the user out of the product.
        profile = repos.users.ensure_profile(principal.user_id, principal.email)
    role_value = repos.users.get_role(principal.user_id)
    role = Role.ADMINISTRATOR if role_value == Role.ADMINISTRATOR.value else Role.USER
    return CurrentUser(principal=principal, profile=profile, role=role)


def require_admin(user: CurrentUser = Depends(current_user)) -> CurrentUser:
    if not user.is_admin:
        raise Forbidden("Administrator access required")
    return user


def entitlements_for(
    user: CurrentUser, repos: Repositories
) -> Entitlements:
    used = repos.billing.usage_this_period(user.id, "analysis")
    plan = user.plan
    if user.is_admin and plan is PlanCode.FREE:
        plan = PlanCode.PREMIUM
    return resolve_entitlements(plan, used)


def get_entitlements(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> Entitlements:
    return entitlements_for(user, repos)


def enqueue(task: Any, *args: Any) -> None:
    """Send to Celery, or run inline when eager mode is configured (tests, local demos)."""
    settings: Settings = get_settings()
    if settings.celery_eager:
        task(*args)
        return
    try:
        task.delay(*args)
    except Exception:
        # Broker unavailable: keep the record queued rather than blocking the request. The user
        # can retry via the reprocess endpoint and ops sees the warning.
        from app.core.logging import get_logger

        get_logger(__name__).warning(
            "enqueue_failed", extra={"extra_fields": {"task": getattr(task, "name", "unknown")}}
        )


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")
