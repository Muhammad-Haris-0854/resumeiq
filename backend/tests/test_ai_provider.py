"""Provider resolution: configuration must never silently pick the wrong endpoint."""

from __future__ import annotations

from app.core.config import Settings
from app.services.ai import (
    GOOGLE_BASE_URL,
    GOOGLE_DEFAULT_MODEL,
    DeterministicProvider,
    OpenAICompatibleProvider,
    build_provider,
)


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ai_provider": "auto",
        "ai_base_url": "",
        "ai_model": "",
        "ai_provider_api_key": "",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_missing_key_falls_back_to_deterministic() -> None:
    assert isinstance(build_provider(_settings()), DeterministicProvider)


def test_google_provider_targets_the_openai_compatible_endpoint() -> None:
    provider = build_provider(_settings(ai_provider="google", ai_provider_api_key="test-key"))
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == GOOGLE_DEFAULT_MODEL
    assert GOOGLE_BASE_URL.endswith("/v1beta/openai")


def test_explicit_model_overrides_the_provider_default() -> None:
    provider = build_provider(
        _settings(ai_provider="google", ai_provider_api_key="test-key", ai_model="gemini-2.5-pro")
    )
    assert provider.model == "gemini-2.5-pro"


def test_openai_compatible_defaults_to_openai() -> None:
    provider = build_provider(_settings(ai_provider="openai_compatible", ai_provider_api_key="test-key"))
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "gpt-4o-mini"


def test_deterministic_wins_even_with_a_key() -> None:
    provider = build_provider(_settings(ai_provider="deterministic", ai_provider_api_key="test-key"))
    assert isinstance(provider, DeterministicProvider)


def test_ai_enabled_reflects_a_configured_model() -> None:
    assert _settings(ai_provider="google", ai_provider_api_key="test-key").ai_enabled is True
    assert _settings().ai_enabled is False
    assert _settings(ai_provider="deterministic", ai_provider_api_key="test-key").ai_enabled is False
