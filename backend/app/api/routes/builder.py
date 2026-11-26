"""Resume builder: content model, autosave with versions, PDF export."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentUser,
    current_user,
    enqueue,
    get_entitlements,
    get_repositories,
)
from app.core.errors import Forbidden, NotFound, Unprocessable
from app.repositories.base import Repositories
from app.schemas.core import (
    GeneratedResumeCreate,
    GeneratedResumeOut,
    Page,
    ResumeContent,
)
from app.services.builder import content_from_extracted, empty_content
from app.services.entitlements import Entitlements
from app.workers.tasks import export_resume

router = APIRouter(prefix="/v1/generated-resumes", tags=["builder"])


def _content(row: dict[str, Any]) -> ResumeContent:
    try:
        return ResumeContent(**(row.get("content") or {}))
    except Exception:
        return ResumeContent(**empty_content())


def _out(row: dict[str, Any], pdf_url: str | None = None) -> GeneratedResumeOut:
    return GeneratedResumeOut(
        id=row["id"],
        title=row["title"],
        template_id=row["template_id"],
        resume_id=row.get("resume_id"),
        version=int(row.get("version", 1)),
        status=row.get("status", "ready"),
        content=_content(row),
        pdf_url=pdf_url,
        updated_at=row.get("updated_at"),
    )


def _assert_template_allowed(template: dict[str, Any], ent: Entitlements) -> None:
    allowed = set(ent.features.get("templates") or [])
    if template["slug"] not in allowed:
        raise Forbidden(
            f"The {template['name']} template is part of a higher plan.",
            code="TEMPLATE_LOCKED",
            details={"template": template["slug"], "plan": ent.plan.value},
        )


@router.post("", response_model=GeneratedResumeOut, status_code=status.HTTP_201_CREATED)
def create_generated_resume(
    payload: GeneratedResumeCreate,
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> GeneratedResumeOut:
    template = repos.templates.get(str(payload.template_id))
    if not template:
        raise NotFound("Template not found")
    _assert_template_allowed(template, ent)

    if payload.content:
        content = payload.content.model_dump()
    elif payload.resume_version_id:
        version = repos.resumes.get_version_for_user(user.id, str(payload.resume_version_id))
        if not version:
            raise NotFound("Resume version not found")
        content = content_from_extracted(
            version.get("extracted") or {}, fallback_name=str(user.profile.get("full_name") or "")
        )
    else:
        content = empty_content(
            str(user.profile.get("full_name") or ""), user.email
        )

    content["section_order"] = content.get("section_order") or (template.get("layout") or {}).get(
        "section_order", ["summary", "skills", "experience", "education", "projects"]
    )
    row = repos.generated.create(
        user.id,
        {
            "resume_id": None,
            "template_id": template["id"],
            "title": payload.title,
            "content": content,
            "version": 1,
            "status": "ready",
        },
    )
    repos.generated.add_version(row["id"], 1, content)
    return _out(row)


@router.get("", response_model=Page)
def list_generated_resumes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.generated.list(user.id, limit=limit, offset=offset)
    return Page(
        items=[_out(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{generated_id}", response_model=GeneratedResumeOut)
def get_generated_resume(
    generated_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> GeneratedResumeOut:
    row = repos.generated.get(user.id, generated_id)
    if not row:
        raise NotFound("Resume not found")
    pdf_url = None
    if row.get("pdf_storage_path"):
        pdf_url = repos.storage.signed_url("generated", row["pdf_storage_path"], 60)
    return _out(row, pdf_url)


@router.put("/{generated_id}", response_model=GeneratedResumeOut)
def save_generated_resume(
    generated_id: str,
    payload: ResumeContent,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> GeneratedResumeOut:
    row = repos.generated.get(user.id, generated_id)
    if not row:
        raise NotFound("Resume not found")
    content = payload.model_dump()
    next_version = int(row.get("version", 1)) + 1
    updated = repos.generated.update(
        user.id,
        generated_id,
        {"content": content, "version": next_version, "pdf_storage_path": None, "status": "ready"},
    )
    repos.generated.add_version(generated_id, next_version, content)
    return _out(updated)


@router.post("/{generated_id}/export", response_model=GeneratedResumeOut, status_code=202)
def export_generated_resume(
    generated_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> GeneratedResumeOut:
    row = repos.generated.get(user.id, generated_id)
    if not row:
        raise NotFound("Resume not found")
    if not (row.get("content") or {}).get("full_name"):
        raise Unprocessable("Add your name before exporting", code="INCOMPLETE_RESUME")
    repos.billing.record_usage(user.id, "export", 1, {"generated_id": generated_id})
    updated = repos.generated.update(user.id, generated_id, {"status": "queued"})
    enqueue(export_resume, generated_id)
    return _out(updated)


@router.get("/{generated_id}/versions")
def list_generated_versions(
    generated_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, Any]:
    if not repos.generated.get(user.id, generated_id):
        raise NotFound("Resume not found")
    return {"items": repos.generated.list_versions(generated_id)}


@router.post("/{generated_id}/versions/{version}/restore", response_model=GeneratedResumeOut)
def restore_generated_version(
    generated_id: str,
    version: int,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> GeneratedResumeOut:
    row = repos.generated.get(user.id, generated_id)
    if not row:
        raise NotFound("Resume not found")
    snapshot = repos.generated.get_version(generated_id, version)
    if not snapshot:
        raise NotFound("Version not found")
    content = snapshot.get("content") or {}
    next_version = int(row.get("version", 1)) + 1
    updated = repos.generated.update(
        user.id, generated_id, {"content": content, "version": next_version, "status": "ready"}
    )
    repos.generated.add_version(generated_id, next_version, content)
    return _out(updated)
