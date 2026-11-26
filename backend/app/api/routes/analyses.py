"""Analysis creation, retrieval, issue triage and comparison."""

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
from app.core.errors import NotFound, Unprocessable
from app.models.enums import IssueStatus, RequirementLevel, Severity, SkillStatus
from app.repositories.base import Repositories
from app.schemas.core import (
    AnalysisCreate,
    AnalysisOut,
    ComparisonOut,
    IssueOut,
    IssueUpdate,
    Page,
    ScoreDetail,
    SkillBreakdownItem,
)
from app.services.entitlements import Entitlements, assert_quota, require_feature
from app.workers.tasks import analyse_resume

router = APIRouter(prefix="/v1/analyses", tags=["analyses"])


def _issue_out(row: dict[str, Any]) -> IssueOut:
    return IssueOut(
        id=row["id"],
        category=row.get("category", "content"),
        severity=row.get("severity", Severity.MEDIUM),
        title=row.get("title", ""),
        detail=row.get("detail"),
        evidence=row.get("evidence"),
        suggestion=row.get("suggestion"),
        status=row.get("status", IssueStatus.OPEN),
        user_edit=row.get("user_edit"),
    )


def _analysis_out(row: dict[str, Any], issues: list[dict[str, Any]] | None = None) -> AnalysisOut:
    return AnalysisOut(
        id=row["id"],
        resume_id=row["resume_id"],
        resume_version_id=row["resume_version_id"],
        career_domain_id=row.get("career_domain_id"),
        job_description_id=row.get("job_description_id"),
        status=row.get("status", "queued"),
        overall_score=row.get("overall_score"),
        scores=[ScoreDetail(**score) for score in (row.get("scores") or [])],
        summary=row.get("summary"),
        strengths=row.get("strengths") or [],
        weaknesses=row.get("weaknesses") or [],
        detected_skills=row.get("detected_skills") or [],
        missing_keywords=row.get("missing_keywords") or [],
        skill_breakdown=[
            SkillBreakdownItem(
                skill=item["skill"],
                status=SkillStatus(item.get("status", "missing")),
                requirement=RequirementLevel(item.get("requirement", "required")),
                evidence=item.get("evidence"),
            )
            for item in (row.get("skill_breakdown") or [])
        ],
        issues=[_issue_out(issue) for issue in (issues or [])],
        ai_model=row.get("ai_model"),
        error_code=row.get("error_code"),
        error_message=row.get("error_message"),
        created_at=row["created_at"],
        completed_at=row.get("completed_at"),
    )


@router.post("", response_model=AnalysisOut, status_code=status.HTTP_202_ACCEPTED)
def create_analysis(
    payload: AnalysisCreate,
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> AnalysisOut:
    version = repos.resumes.get_version_for_user(user.id, str(payload.resume_version_id))
    if not version:
        raise NotFound("Resume version not found")
    domain = repos.taxonomy.get_domain(str(payload.career_domain_id))
    if not domain:
        raise Unprocessable("Unknown career domain", code="UNKNOWN_DOMAIN")
    if not version.get("extracted"):
        raise Unprocessable(
            "This resume is still being processed. Try again in a few seconds.",
            code="EXTRACTION_PENDING",
        )
    if payload.job_description_id:
        require_feature(ent, "jd_matching")

    assert_quota(ent)
    analysis = repos.analyses.create(
        {
            "user_id": user.id,
            "resume_id": version["resume_id"],
            "resume_version_id": version["id"],
            "career_domain_id": str(payload.career_domain_id),
            "job_description_id": str(payload.job_description_id) if payload.job_description_id else None,
            "status": "queued",
        }
    )
    repos.billing.record_usage(user.id, "analysis", 1, {"analysis_id": analysis["id"]})
    repos.admin.audit(user.id, "analysis.created", "analysis", analysis["id"], {})
    enqueue(analyse_resume, analysis["id"])
    return _analysis_out(analysis, [])


@router.get("", response_model=Page)
def list_analyses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.analyses.list(user.id, limit=limit, offset=offset)
    return Page(
        items=[_analysis_out(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(
    analysis_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> AnalysisOut:
    row = repos.analyses.get(user.id, analysis_id)
    if not row:
        raise NotFound("Analysis not found")
    issues = repos.analyses.list_issues(analysis_id) if row.get("status") == "ready" else []
    return _analysis_out(row, issues)


@router.delete("/{analysis_id}", status_code=204, response_model=None)
def delete_analysis(
    analysis_id: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    if not repos.analyses.get(user.id, analysis_id):
        raise NotFound("Analysis not found")
    repos.analyses.delete(user.id, analysis_id)


@router.post("/{analysis_id}/rerun", response_model=AnalysisOut, status_code=202)
def rerun_analysis(
    analysis_id: str,
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> AnalysisOut:
    original = repos.analyses.get(user.id, analysis_id)
    if not original:
        raise NotFound("Analysis not found")
    assert_quota(ent)
    analysis = repos.analyses.create(
        {
            "user_id": user.id,
            "resume_id": original["resume_id"],
            "resume_version_id": original["resume_version_id"],
            "career_domain_id": original.get("career_domain_id"),
            "job_description_id": original.get("job_description_id"),
            "status": "queued",
        }
    )
    repos.billing.record_usage(user.id, "analysis", 1, {"analysis_id": analysis["id"], "rerun_of": analysis_id})
    enqueue(analyse_resume, analysis["id"])
    return _analysis_out(analysis, [])


@router.get("/{analysis_id}/compare/{other_id}", response_model=ComparisonOut)
def compare_analyses(
    analysis_id: str,
    other_id: str,
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> ComparisonOut:
    require_feature(ent, "version_compare")
    base = repos.analyses.get(user.id, analysis_id)
    other = repos.analyses.get(user.id, other_id)
    if not base or not other:
        raise NotFound("Analysis not found")
    if base.get("status") != "ready" or other.get("status") != "ready":
        raise Unprocessable("Both reports must be complete before comparing", code="NOT_READY")

    def as_map(row: dict[str, Any]) -> dict[str, int]:
        return {item["key"]: int(item["score"]) for item in (row.get("scores") or [])}

    base_scores, other_scores = as_map(base), as_map(other)
    deltas = {
        key: other_scores.get(key, 0) - base_scores.get(key, 0)
        for key in set(base_scores) | set(other_scores)
    }
    return ComparisonOut(
        base_id=base["id"],
        compare_id=other["id"],
        overall_delta=int(other.get("overall_score") or 0) - int(base.get("overall_score") or 0),
        deltas=deltas,
    )


@router.patch("/{analysis_id}/issues/{issue_id}", response_model=IssueOut)
def update_issue(
    analysis_id: str,
    issue_id: str,
    payload: IssueUpdate,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> IssueOut:
    if not repos.analyses.get(user.id, analysis_id):
        raise NotFound("Analysis not found")
    patch: dict[str, Any] = {"status": payload.status}
    if payload.status == "edited":
        if not payload.user_edit:
            raise Unprocessable("Provide the edited text", code="MISSING_EDIT")
        patch["user_edit"] = payload.user_edit
    row = repos.analyses.update_issue(analysis_id, issue_id, patch)
    if not row:
        raise NotFound("Issue not found")
    return _issue_out(row)
