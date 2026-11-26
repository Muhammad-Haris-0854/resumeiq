"""AI provider factory.

Providers are resolved from configuration so the rest of the app never imports a concrete
implementation. Gemini is reached through Google's OpenAI-compatible endpoint, which keeps one
code path for every chat-completions provider.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.services.ai.base import AIProvider, AIProviderError
from app.services.ai.deterministic import DeterministicProvider
from app.services.ai.openai_compatible import OpenAICompatibleProvider

GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
GOOGLE_DEFAULT_MODEL = "gemini-3-flash-preview"

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


def _resolve_endpoint(settings: Settings) -> tuple[str, str] | None:
    """Return (base_url, model) for the configured provider, or None when unconfigured."""
    if not settings.ai_provider_api_key:
        return None

    provider = settings.ai_provider
    if provider == "google":
        return (
            settings.ai_base_url or GOOGLE_BASE_URL,
            settings.ai_model or GOOGLE_DEFAULT_MODEL,
        )
    if provider == "openai_compatible":
        return (
            settings.ai_base_url or OPENAI_BASE_URL,
            settings.ai_model or OPENAI_DEFAULT_MODEL,
        )
    # auto: an explicit base URL wins, otherwise assume OpenAI.
    return (
        settings.ai_base_url or OPENAI_BASE_URL,
        settings.ai_model or OPENAI_DEFAULT_MODEL,
    )


def build_provider(settings: Settings | None = None) -> AIProvider:
    """Resolve the configured provider, degrading to deterministic when unusable."""
    settings = settings or get_settings()
    if settings.ai_provider == "deterministic":
        return DeterministicProvider()

    endpoint = _resolve_endpoint(settings)
    if endpoint is None:
        return DeterministicProvider()

    base_url, model = endpoint
    reasoning = settings.ai_reasoning_effort or ("low" if settings.ai_provider == "google" else "")
    return OpenAICompatibleProvider(
        base_url=base_url,
        api_key=settings.ai_provider_api_key,
        model=model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_retries=settings.ai_max_retries,
        reasoning_effort=reasoning,
    )


__all__ = [
    "AIProvider",
    "AIProviderError",
    "DeterministicProvider",
    "OpenAICompatibleProvider",
    "build_provider",
    "GOOGLE_BASE_URL",
    "GOOGLE_DEFAULT_MODEL",
]
