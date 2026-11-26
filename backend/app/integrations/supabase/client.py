"""Supabase client factory. The service-role client is server-only."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings
from app.core.errors import AppError


@lru_cache
def get_service_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
            code="SUPABASE_NOT_CONFIGURED",
            status_code=503,
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
