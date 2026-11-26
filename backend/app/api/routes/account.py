"""Profile, entitlements, export, deletion and notifications."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, current_user, entitlements_for, get_entitlements, get_repositories
from app.core.errors import NotFound
from app.repositories.base import Repositories
from app.schemas.core import EntitlementsOut, MeOut, ProfileOut, ProfileUpdate
from app.services.entitlements import Entitlements

router = APIRouter(prefix="/v1", tags=["account"])


def _profile_out(row: dict[str, Any]) -> ProfileOut:
    return ProfileOut(
        id=row["id"],
        email=row.get("email", ""),
        full_name=row.get("full_name"),
        headline=row.get("headline"),
        career_domain_id=row.get("career_domain_id"),
        plan=row.get("plan", "free"),
        onboarding_completed=bool(row.get("onboarding_completed")),
        created_at=row.get("created_at"),
    )


def _entitlements_out(ent: Entitlements, role: str) -> EntitlementsOut:
    data = ent.as_dict()
    return EntitlementsOut(role=role, **data)


@router.get("/me", response_model=MeOut)
def read_me(
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
) -> MeOut:
    return MeOut(
        profile=_profile_out(user.profile),
        entitlements=_entitlements_out(ent, user.role.value),
    )


@router.patch("/me", response_model=MeOut)
def update_me(
    payload: ProfileUpdate,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> MeOut:
    patch = payload.model_dump(exclude_none=True)
    profile = repos.users.update_profile(user.id, patch) if patch else user.profile
    updated = CurrentUser(principal=user.principal, profile=profile, role=user.role)
    return MeOut(
        profile=_profile_out(profile),
        entitlements=_entitlements_out(entitlements_for(updated, repos), user.role.value),
    )


@router.get("/me/notifications")
def list_notifications(
    limit: int = Query(default=20, ge=1, le=50),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, Any]:
    client = getattr(repos.users, "_client", None)
    if client is None:
        return {"items": []}
    rows = (
        client.table("notifications")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return {"items": rows}


@router.post("/me/export")
def export_account(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, str]:
    """GDPR-style export: profile, resume metadata, analyses. Documents stay in storage."""
    resumes, _ = repos.resumes.list(user.id, limit=100, offset=0)
    analyses, _ = repos.analyses.list(user.id, limit=200, offset=0)
    bundle = {
        "profile": user.profile,
        "resumes": [
            {k: v for k, v in resume.items() if k not in {"raw_text"}} for resume in resumes
        ],
        "analyses": analyses,
    }
    payload = json.dumps(bundle, default=str, indent=2).encode()
    path = f"{user.id}/export-{int(__import__('time').time())}.json"
    repos.storage.upload("generated", path, payload, "application/json")
    url = repos.storage.signed_url("generated", path, 300)
    return {"url": url, "expires_in": "300"}


@router.delete("/me", status_code=204, response_model=None)
def delete_account(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    """Deletes storage objects, then the auth user (cascades rows), then audits the tombstone."""
    resumes, _ = repos.resumes.list(user.id, limit=200, offset=0)
    for resume in resumes:
        for version in repos.resumes.list_versions(resume["id"]):
            repos.storage.delete("resumes", version["storage_path"])
        repos.resumes.soft_delete(user.id, resume["id"])

    client = getattr(repos.users, "_client", None)
    if client is not None:
        client.auth.admin.delete_user(user.id)
    repos.admin.audit(user.id, "account.deleted", "user", user.id, {"resumes": len(resumes)})


@router.get("/me/notifications/{notification_id}")
def read_notification(
    notification_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, Any]:
    client = getattr(repos.users, "_client", None)
    if client is None:
        raise NotFound("Notification not found")
    rows = (
        client.table("notifications")
        .update({"read_at": __import__("datetime").datetime.utcnow().isoformat()})
        .eq("id", notification_id)
        .eq("user_id", user.id)
        .execute()
        .data
        or []
    )
    if not rows:
        raise NotFound("Notification not found")
    return rows[0]
