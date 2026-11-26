"""Liveness and readiness."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.version,
        "environment": settings.environment,
        "ai_provider": settings.ai_provider,
        "payment_provider": settings.payment_provider,
    }


@router.get("/health/ready")
def readiness() -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, bool] = {}

    try:
        from app.integrations.supabase.client import get_service_client

        get_service_client().table("subscription_plans").select("code").limit(1).execute()
        checks["database"] = True
    except Exception:
        checks["database"] = False

    try:
        import redis

        redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    checks["supabase_configured"] = bool(settings.supabase_url and settings.supabase_service_role_key)
    ready = checks["supabase_configured"] and checks["database"]
    return {"ready": ready, "checks": checks}
