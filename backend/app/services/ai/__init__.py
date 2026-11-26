"""AI provider factory."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.services.ai.base import AIProvider, AIProviderError
from app.services.ai.deterministic import DeterministicProvider
from app.services.ai.openai_compatible import OpenAICompatibleProvider


def build_provider(settings: Settings | None = None) -> AIProvider:
    """Resolve the configured provider, degrading to deterministic when unusable."""
    settings = settings or get_settings()
    if settings.ai_provider == "deterministic":
        return DeterministicProvider()
    if settings.ai_provider_api_key:
        return OpenAICompatibleProvider(
            base_url=settings.ai_base_url,
            api_key=settings.ai_provider_api_key,
            model=settings.ai_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    return DeterministicProvider()


__all__ = ["AIProvider", "AIProviderError", "DeterministicProvider", "OpenAICompatibleProvider", "build_provider"]
