"""Resume intake, versions, previews and deletion."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.deps import (
    CurrentUser,
    current_user,
    enqueue,
    get_entitlements,
    get_repositories,
    get_settings,
)
from app.core.errors import NotFound, Unprocessable
from app.repositories.base import Repositories
from app.schemas.core import (
    Page,
    ResumeDetailOut,
    ResumeOut,
    ResumeUpdate,
    ResumeVersionOut,
    SignedUrlOut,
)
from app.services.entitlements import Entitlements, assert_resume_limit
from app.utils.files import validate_upload
from app.workers.tasks import extract_resume

router = APIRouter(prefix="/v1/resumes", tags=["resumes"])


def _resume_out(row: dict[str, Any], score: int | None = None) -> ResumeOut:
    return ResumeOut(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        source=row.get("source", "upload"),
        career_domain_id=row.get("career_domain_id"),
        current_version_id=row.get("current_version_id"),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        latest_score=score,
    )


def _version_out(row: dict[str, Any]) -> ResumeVersionOut:
    return ResumeVersionOut(
        id=row["id"],
        version=row["version"],
        file_name=row["file_name"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        page_count=row.get("page_count"),
        extraction_method=row.get("extraction_method"),
        created_at=row["created_at"],
    )


async def _read_upload(file: UploadFile, max_bytes: int) -> bytes:
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise Unprocessable(
            f"File is larger than {max_bytes // (1024 * 1024)} MB", code="FILE_TOO_LARGE"
        )
    return data


@router.post("", response_model=ResumeOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    career_domain_id: str | None = Form(default=None),
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> ResumeOut:
    settings = get_settings()
    assert_resume_limit(ent, repos.resumes.count_active(user.id))

    raw = await _read_upload(file, settings.max_upload_bytes)
    upload = validate_upload(raw, file.filename or "resume.pdf", settings.max_upload_bytes)

    if career_domain_id and not repos.taxonomy.get_domain(career_domain_id):
        raise Unprocessable("Unknown career domain", code="UNKNOWN_DOMAIN")

    resume = repos.resumes.create(
        user.id,
        {
            "title": (title or upload.filename.rsplit(".", 1)[0])[:120],
            "career_domain_id": career_domain_id or user.profile.get("career_domain_id"),
            "status": "uploaded",
            "source": "upload",
        },
    )
    version_number = repos.resumes.next_version_number(resume["id"])
    path = f"{user.id}/{resume['id']}/{version_number}.{upload.extension}"
    repos.storage.upload("resumes", path, upload.data, upload.mime_type)
    version = repos.resumes.add_version(
        resume["id"],
        {
            "version": version_number,
            "storage_path": path,
            "file_name": upload.filename,
            "mime_type": upload.mime_type,
            "size_bytes": upload.size_bytes,
            "sha256": upload.sha256,
            "created_by": user.id,
        },
    )
    repos.resumes.update(user.id, resume["id"], {"current_version_id": version["id"]})
    repos.admin.audit(user.id, "resume.uploaded", "resume", resume["id"], {"size": upload.size_bytes})
    enqueue(extract_resume, resume["id"], version["id"])
    return _resume_out({**resume, "current_version_id": version["id"]})


@router.get("", response_model=Page)
def list_resumes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.resumes.list(user.id, limit=limit, offset=offset)
    items = [
        _resume_out(row, repos.analyses.latest_score_for_resume(row["id"])).model_dump(mode="json")
        for row in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def get_resume(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> ResumeDetailOut:
    resume = repos.resumes.get(user.id, resume_id)
    if not resume:
        raise NotFound("Resume not found")
    versions = repos.resumes.list_versions(resume_id)
    current = next((v for v in versions if v["id"] == resume.get("current_version_id")), None)
    base = _resume_out(resume, repos.analyses.latest_score_for_resume(resume_id))
    return ResumeDetailOut(
        **base.model_dump(),
        versions=[_version_out(v) for v in versions],
        extracted=(current or {}).get("extracted"),
    )


@router.patch("/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: str,
    payload: ResumeUpdate,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> ResumeOut:
    patch = payload.model_dump(exclude_none=True)
    if not repos.resumes.get(user.id, resume_id):
        raise NotFound("Resume not found")
    row = repos.resumes.update(user.id, resume_id, patch) if patch else repos.resumes.get(user.id, resume_id)
    assert row is not None
    return _resume_out(row, repos.analyses.latest_score_for_resume(resume_id))


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_resume(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    resume = repos.resumes.get(user.id, resume_id)
    if not resume:
        raise NotFound("Resume not found")
    for version in repos.resumes.list_versions(resume_id):
        repos.storage.delete("resumes", version["storage_path"])
    repos.resumes.soft_delete(user.id, resume_id)
    repos.admin.audit(user.id, "resume.deleted", "resume", resume_id, {})


@router.post("/{resume_id}/versions", response_model=ResumeVersionOut, status_code=202)
async def add_version(
    resume_id: str,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> ResumeVersionOut:
    settings = get_settings()
    resume = repos.resumes.get(user.id, resume_id)
    if not resume:
        raise NotFound("Resume not found")
    raw = await _read_upload(file, settings.max_upload_bytes)
    upload = validate_upload(raw, file.filename or "resume.pdf", settings.max_upload_bytes)
    number = repos.resumes.next_version_number(resume_id)
    path = f"{user.id}/{resume_id}/{number}.{upload.extension}"
    repos.storage.upload("resumes", path, upload.data, upload.mime_type)
    version = repos.resumes.add_version(
        resume_id,
        {
            "version": number,
            "storage_path": path,
            "file_name": upload.filename,
            "mime_type": upload.mime_type,
            "size_bytes": upload.size_bytes,
            "sha256": upload.sha256,
            "created_by": user.id,
        },
    )
    repos.resumes.update(user.id, resume_id, {"current_version_id": version["id"], "status": "uploaded"})
    enqueue(extract_resume, resume_id, version["id"])
    return _version_out(version)


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionOut])
def list_versions(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> list[ResumeVersionOut]:
    if not repos.resumes.get(user.id, resume_id):
        raise NotFound("Resume not found")
    return [_version_out(row) for row in repos.resumes.list_versions(resume_id)]


@router.get("/{resume_id}/download", response_model=SignedUrlOut)
def download_resume(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> SignedUrlOut:
    settings = get_settings()
    resume = repos.resumes.get(user.id, resume_id)
    if not resume or not resume.get("current_version_id"):
        raise NotFound("Resume not found")
    version = repos.resumes.get_version(resume["current_version_id"])
    if not version:
        raise NotFound("Resume version not found")
    url = repos.storage.signed_url("resumes", version["storage_path"], settings.signed_url_ttl_seconds)
    return SignedUrlOut(url=url, expires_in=settings.signed_url_ttl_seconds)


@router.get("/{resume_id}/preview")
def preview_resume(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, Any]:
    resume = repos.resumes.get(user.id, resume_id)
    if not resume or not resume.get("current_version_id"):
        raise NotFound("Resume not found")
    version = repos.resumes.get_version(resume["current_version_id"])
    if not version:
        raise NotFound("Resume version not found")
    text = version.get("raw_text") or ""
    return {
        "status": resume.get("status"),
        "method": version.get("extraction_method"),
        "page_count": version.get("page_count"),
        "text": text[:8000],
        "truncated": len(text) > 8000,
    }


@router.post("/{resume_id}/reprocess", status_code=202)
def reprocess_resume(
    resume_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, str]:
    resume = repos.resumes.get(user.id, resume_id)
    if not resume or not resume.get("current_version_id"):
        raise NotFound("Resume not found")
    repos.resumes.update(user.id, resume_id, {"status": "extracting"})
    enqueue(extract_resume, resume_id, resume["current_version_id"])
    return {"status": "queued"}
