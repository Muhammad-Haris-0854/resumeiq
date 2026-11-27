"""Background jobs.

Each task takes ids, re-reads state and no-ops when the work is already terminal, so retries and
duplicate deliveries are safe.
"""

from __future__ import annotations

from celery import Task

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.supabase_repo import build_repositories
from app.services.ai import build_provider
from app.services.analysis import run_analysis
from app.services.extraction import extract_document
from app.services.job_match import compute_match, parse_job_description
from app.services.normalizer import normalise
from app.services.pdf import render_pdf
from app.services.taxonomy_catalog import CATALOG
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


class BaseTask(Task):
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True
    max_retries = 3


@celery_app.task(bind=True, base=BaseTask, name="resumeiq.extract_resume")
def extract_resume(self: Task, resume_id: str, version_id: str) -> dict[str, str]:
    settings = get_settings()
    repos = build_repositories()
    version = repos.resumes.get_version(version_id)
    if not version:
        return {"status": "missing"}
    if version.get("extracted"):
        return {"status": "already_extracted"}

    data = repos.storage.download("resumes", version["storage_path"])
    result = extract_document(data, version["mime_type"], ocr_enabled=settings.ocr_enabled)
    extracted = normalise(result.text, result.page_count)
    repos.resumes.update_by_id(resume_id, {"status": "extracted"})
    _update_version(version_id, {
        "raw_text": result.text,
        "extracted": extracted,
        "page_count": result.page_count,
        "extraction_method": result.method,
    })
    return {"status": "extracted", "method": result.method}


@celery_app.task(bind=True, base=BaseTask, name="resumeiq.analyse_resume")
def analyse_resume(self: Task, analysis_id: str) -> dict[str, str]:
    repos = build_repositories()
    weights = _scoring_weights(repos)
    run_analysis(repos, analysis_id=analysis_id, provider=build_provider(), weights=weights)
    return {"status": "ready"}


@celery_app.task(bind=True, base=BaseTask, name="resumeiq.match_job")
def match_job(self: Task, match_id: str) -> dict[str, str]:
    repos = build_repositories()
    match = _load_match(repos, match_id)
    if not match or match.get("status") in {"ready", "failed"}:
        return {"status": "skipped"}
    repos.jobs.update_match(match_id, {"status": "running"})
    try:
        version = repos.resumes.get_version(match["resume_version_id"])
        description = repos.jobs.get_description(match["user_id"], match["job_description_id"])
        if not version or not description:
            raise ValueError("missing resume version or job description")
        parsed = description.get("parsed") or parse_job_description(description["raw_text"], build_provider(), CATALOG)
        result = compute_match(
            resume_text=version.get("raw_text") or "",
            extracted=version.get("extracted") or {},
            parsed=parsed,
            catalog=CATALOG,
        )
        repos.jobs.update_match(
            match_id,
            {
                "status": "ready",
                "match_score": result["match_score"],
                "matched": result["matched"],
                "partial": result["partial"],
                "missing": result["missing"],
                "recommendations": result["recommendations"],
            },
        )
        return {"status": "ready", "score": str(result["match_score"])}
    except Exception as exc:
        repos.jobs.update_match(match_id, {"status": "failed", "error_message": str(exc)[:400]})
        raise


@celery_app.task(bind=True, base=BaseTask, name="resumeiq.export_resume")
def export_resume(self: Task, generated_id: str) -> dict[str, str]:
    repos = build_repositories()
    generated = _load_generated(repos, generated_id)
    if not generated:
        return {"status": "missing"}
    repos.generated.update(generated["user_id"], generated_id, {"status": "running"})
    try:
        template = repos.templates.get(generated["template_id"]) or {}
        pdf = render_pdf(generated["content"], template)
        path = f"{generated['user_id']}/{generated_id}.pdf"
        repos.storage.upload("generated", path, pdf, "application/pdf")
        repos.generated.update(
            generated["user_id"], generated_id, {"status": "ready", "pdf_storage_path": path}
        )
        return {"status": "ready", "path": path}
    except Exception as exc:
        repos.generated.update(
            generated["user_id"], generated_id, {"status": "failed"}
        )
        raise exc


# --- helpers ---------------------------------------------------------------


def _update_version(version_id: str, patch: dict) -> None:
    from app.integrations.supabase.client import get_service_client

    get_service_client().table("resume_versions").update(
        {**patch, "extracted": patch.get("extracted")}
    ).eq("id", version_id).execute()


def _load_match(repos, match_id: str) -> dict | None:
    client = getattr(repos.jobs, "_client", None)
    if client is None:
        return None
    rows = client.table("job_matches").select("*").eq("id", match_id).limit(1).execute().data or []
    return rows[0] if rows else None


def _load_generated(repos, generated_id: str) -> dict | None:
    client = getattr(repos.generated, "_client", None)
    if client is None:
        return None
    rows = client.table("generated_resumes").select("*").eq("id", generated_id).limit(1).execute().data or []
    return rows[0] if rows else None


def _scoring_weights(repos) -> dict[str, int] | None:
    from app.models.enums import DEFAULT_WEIGHTS

    setting = repos.admin.get_setting("scoring_weights")
    if not setting:
        return DEFAULT_WEIGHTS
    value = setting.get("value") or {}
    try:
        resolved = {key: int(value[key]) for key in DEFAULT_WEIGHTS}
    except (KeyError, TypeError, ValueError):
        return DEFAULT_WEIGHTS
    return resolved if sum(resolved.values()) == 100 else DEFAULT_WEIGHTS
