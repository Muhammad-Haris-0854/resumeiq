"""Job-description matching."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentUser,
    current_user,
    enqueue,
    get_ai_provider,
    get_entitlements,
    get_repositories,
)
from app.core.errors import NotFound, Unprocessable
from app.repositories.base import Repositories
from app.schemas.core import JobMatchCreate, JobMatchOut, JobRequirementOut, Page
from app.services.ai import AIProvider
from app.services.entitlements import Entitlements, require_feature
from app.services.job_match import parse_job_description
from app.services.taxonomy_catalog import CATALOG
from app.workers.tasks import match_job

router = APIRouter(prefix="/v1/job-matches", tags=["job-matching"])


def _match_out(row: dict[str, Any]) -> JobMatchOut:
    return JobMatchOut(
        id=row["id"],
        status=row.get("status", "queued"),
        match_score=row.get("match_score"),
        matched=[JobRequirementOut(**item) for item in (row.get("matched") or [])],
        partial=[JobRequirementOut(**item) for item in (row.get("partial") or [])],
        missing=[JobRequirementOut(**item) for item in (row.get("missing") or [])],
        recommendations=row.get("recommendations") or [],
        created_at=row["created_at"],
    )


@router.post("", response_model=JobMatchOut, status_code=status.HTTP_202_ACCEPTED)
def create_match(
    payload: JobMatchCreate,
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
    provider: AIProvider = Depends(get_ai_provider),
) -> JobMatchOut:
    require_feature(ent, "jd_matching")
    version = repos.resumes.get_version_for_user(user.id, str(payload.resume_version_id))
    if not version:
        raise NotFound("Resume version not found")
    if not version.get("extracted"):
        raise Unprocessable("This resume is still being processed", code="EXTRACTION_PENDING")

    parsed = parse_job_description(payload.raw_text, provider, CATALOG)
    description = repos.jobs.create_description(
        user.id,
        {
            "title": payload.title,
            "company": payload.company,
            "raw_text": payload.raw_text,
            "parsed": parsed,
        },
    )
    match = repos.jobs.create_match(
        user.id,
        {
            "resume_version_id": version["id"],
            "job_description_id": description["id"],
            "status": "queued",
        },
    )
    repos.billing.record_usage(user.id, "job_match", 1, {"match_id": match["id"]})
    enqueue(match_job, match["id"])
    return _match_out(match)


@router.get("", response_model=Page)
def list_matches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.jobs.list_matches(user.id, limit=limit, offset=offset)
    return Page(
        items=[_match_out(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{match_id}", response_model=JobMatchOut)
def get_match(
    match_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> JobMatchOut:
    row = repos.jobs.get_match(user.id, match_id)
    if not row:
        raise NotFound("Match not found")
    return _match_out(row)
