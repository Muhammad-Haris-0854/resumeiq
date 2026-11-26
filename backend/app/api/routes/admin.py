"""Administrator API. Every endpoint depends on require_admin, which re-reads the role."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_repositories, require_admin
from app.core.errors import Conflict, NotFound, Unprocessable
from app.models.enums import DEFAULT_WEIGHTS, PlanCode, Role
from app.repositories.base import Repositories
from app.schemas.core import (
    AdminMetricsOut,
    AdminUserOut,
    AdminUserUpdate,
    DomainOut,
    DomainSkillsWrite,
    DomainWrite,
    Page,
    ScoringWeights,
    TemplateOut,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/metrics", response_model=AdminMetricsOut)
def metrics(repos: Repositories = Depends(get_repositories)) -> AdminMetricsOut:
    data = repos.admin.metrics()
    return AdminMetricsOut(**{**{k: v for k, v in data.items() if k in AdminMetricsOut.model_fields}})


@router.get("/users", response_model=Page)
def list_users(
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.users.list_users(search=search, limit=limit, offset=offset)
    roles = repos.users.list_roles([row["id"] for row in rows])
    items = [
        AdminUserOut(
            id=row["id"],
            email=row.get("email", ""),
            full_name=row.get("full_name"),
            plan=row.get("plan", PlanCode.FREE),
            role=Role(roles.get(row["id"], "user")),
            created_at=row["created_at"],
        ).model_dump(mode="json")
        for row in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> AdminUserOut:
    if payload.role:
        if user_id == admin.id and payload.role != "administrator":
            raise Conflict("You cannot remove your own administrator role", code="SELF_DEMOTION")
        repos.users.set_role(user_id, payload.role)
    profile: dict[str, Any] | None = None
    if payload.plan:
        profile = repos.users.update_profile(user_id, {"plan": payload.plan})
    else:
        profile = repos.users.get_profile(user_id)
    if not profile:
        raise NotFound("User not found")
    role = repos.users.get_role(user_id)
    repos.admin.audit(admin.id, "admin.user_updated", "user", user_id, payload.model_dump(exclude_none=True))
    return AdminUserOut(
        id=profile["id"],
        email=profile.get("email", ""),
        full_name=profile.get("full_name"),
        plan=profile.get("plan", "free"),
        role=Role(role),
        created_at=profile["created_at"],
    )


@router.get("/analyses", response_model=Page)
def list_all_analyses(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repos: Repositories = Depends(get_repositories),
) -> Page:
    rows, total = repos.admin.list_analyses(limit=limit, offset=offset)
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("/domains", response_model=DomainOut, status_code=status.HTTP_201_CREATED)
def create_domain(
    payload: DomainWrite,
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> DomainOut:
    if repos.taxonomy.get_domain_by_slug(payload.slug):
        raise Conflict("That slug already exists", code="SLUG_TAKEN")
    row = repos.taxonomy.create_domain(payload.model_dump())
    repos.admin.audit(admin.id, "admin.domain_created", "career_domain", row["id"], {"slug": payload.slug})
    return DomainOut(**{**row, "skill_count": 0})


@router.patch("/domains/{domain_id}", response_model=DomainOut)
def update_domain(
    domain_id: str,
    payload: DomainWrite,
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> DomainOut:
    if not repos.taxonomy.get_domain(domain_id):
        raise NotFound("Domain not found")
    row = repos.taxonomy.update_domain(domain_id, payload.model_dump())
    repos.admin.audit(admin.id, "admin.domain_updated", "career_domain", domain_id, {})
    return DomainOut(**{**row, "skill_count": len(repos.taxonomy.domain_skills(domain_id))})


@router.put("/domains/{domain_id}/skills", status_code=204, response_model=None)
def replace_domain_skills(
    domain_id: str,
    payload: DomainSkillsWrite,
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> None:
    if not repos.taxonomy.get_domain(domain_id):
        raise NotFound("Domain not found")
    valid_ids = {skill["id"] for skill in repos.taxonomy.all_skills()}
    entries: list[dict[str, Any]] = []
    for item in payload.skills:
        if item["skill_id"] not in valid_ids:
            raise Unprocessable(f"Unknown skill: {item['skill_id']}", code="UNKNOWN_SKILL")
        weight = float(item.get("weight", 1.0))
        if not 0 < weight <= 10:
            raise Unprocessable("Weight must be between 0 and 10", code="INVALID_WEIGHT")
        entries.append(
            {
                "skill_id": item["skill_id"],
                "requirement": item.get("requirement", "required"),
                "weight": weight,
            }
        )
    repos.taxonomy.replace_domain_skills(domain_id, entries)
    repos.admin.audit(admin.id, "admin.domain_skills_replaced", "career_domain", domain_id, {"count": len(entries)})


@router.post("/templates", response_model=TemplateOut, status_code=201)
def upsert_template(
    payload: dict[str, Any],
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> TemplateOut:
    required = {"slug", "name"}
    if not required.issubset(payload):
        raise Unprocessable("slug and name are required", code="MISSING_FIELDS")
    row = repos.templates.upsert(payload)
    repos.admin.audit(admin.id, "admin.template_saved", "template", row["id"], {"slug": payload["slug"]})
    return TemplateOut(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        description=row.get("description"),
        tier=row.get("tier", "free"),
        is_ats_safe=bool(row.get("is_ats_safe", True)),
        layout=row.get("layout") or {},
    )


@router.get("/settings/scoring", response_model=ScoringWeights)
def read_scoring_weights(repos: Repositories = Depends(get_repositories)) -> ScoringWeights:
    setting = repos.admin.get_setting("scoring_weights")
    value = (setting or {}).get("value") or DEFAULT_WEIGHTS
    return ScoringWeights(**value)


@router.patch("/settings/scoring", response_model=ScoringWeights)
def update_scoring_weights(
    payload: ScoringWeights,
    admin=Depends(require_admin),
    repos: Repositories = Depends(get_repositories),
) -> ScoringWeights:
    repos.admin.set_setting("scoring_weights", payload.model_dump())
    repos.admin.audit(admin.id, "admin.scoring_weights_updated", "setting", "scoring_weights", payload.model_dump())
    return payload


@router.get("/health")
def system_health(repos: Repositories = Depends(get_repositories)) -> dict[str, Any]:
    from app.core.config import get_settings

    settings = get_settings()
    queue_depth = None
    try:
        import redis

        queue_depth = int(redis.Redis.from_url(settings.redis_url).llen("ai") or 0)
    except Exception:
        queue_depth = None
    return {
        "environment": settings.environment,
        "ai_provider": settings.ai_provider,
        "ai_key_configured": bool(settings.ai_provider_api_key),
        "payment_provider": settings.payment_provider,
        "queue_depth_ai": queue_depth,
        "celery_eager": settings.celery_eager,
    }
