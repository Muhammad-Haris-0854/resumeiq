"""Career domains, skill taxonomy and resume templates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, current_user, get_entitlements, get_repositories
from app.core.errors import NotFound
from app.repositories.base import Repositories
from app.schemas.core import DomainDetailOut, DomainOut, DomainSkillOut, SkillOut, TemplateOut
from app.services.entitlements import Entitlements

router = APIRouter(prefix="/v1", tags=["catalog"])


@router.get("/domains", response_model=list[DomainOut])
def list_domains(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> list[DomainOut]:
    rows = repos.taxonomy.list_domains()
    result: list[DomainOut] = []
    for row in rows:
        skill_links = row.get("domain_skills") or []
        result.append(
            DomainOut(
                id=row["id"],
                slug=row["slug"],
                name=row["name"],
                description=row.get("description"),
                icon=row.get("icon"),
                skill_count=len(skill_links),
            )
        )
    return result


@router.get("/domains/{slug}", response_model=DomainDetailOut)
def get_domain(
    slug: str,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> DomainDetailOut:
    domain = repos.taxonomy.get_domain_by_slug(slug) or repos.taxonomy.get_domain(slug)
    if not domain:
        raise NotFound("Career domain not found")
    skills = repos.taxonomy.domain_skills(domain["id"])
    return DomainDetailOut(
        id=domain["id"],
        slug=domain["slug"],
        name=domain["name"],
        description=domain.get("description"),
        icon=domain.get("icon"),
        skill_count=len(skills),
        skills=[
            DomainSkillOut(
                id=skill["id"],
                canonical_name=skill["canonical_name"],
                kind=skill.get("kind", "technical"),
                category=skill.get("category"),
                requirement=skill["requirement"],
                weight=skill["weight"],
            )
            for skill in skills
            if skill.get("id")
        ],
    )


@router.get("/skills", response_model=list[SkillOut])
def search_skills(
    q: str = Query(min_length=1, max_length=40),
    limit: int = Query(default=15, ge=1, le=50),
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> list[SkillOut]:
    rows = repos.taxonomy.search_skills(q, limit)
    return [
        SkillOut(
            id=row["id"],
            canonical_name=row["canonical_name"],
            kind=row.get("kind", "technical"),
            category=row.get("category"),
        )
        for row in rows
    ]


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    user: CurrentUser = Depends(current_user),
    ent: Entitlements = Depends(get_entitlements),
    repos: Repositories = Depends(get_repositories),
) -> list[TemplateOut]:
    allowed = set(ent.features.get("templates") or [])
    rows = repos.templates.list()
    return [
        TemplateOut(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            description=row.get("description"),
            tier=row.get("tier", "free"),
            is_ats_safe=bool(row.get("is_ats_safe", True)),
            layout=row.get("layout") or {},
            locked=row["slug"] not in allowed,
        )
        for row in rows
    ]
