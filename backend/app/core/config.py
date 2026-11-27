"""Environment-driven configuration. Nothing here is hardcoded per environment."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "ResumeIQ API"
    version: str = "1.0.0"
    environment: Literal["local", "test", "preview", "production"] = "local"
    debug: bool = False
    api_prefix: str = "/v1"

    # --- Supabase -----------------------------------------------------------
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""
    supabase_jwt_aud: str = "authenticated"
    supabase_jwt_issuer: str = ""

    # --- Data stores --------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = ""

    # --- AI -----------------------------------------------------------------
    ai_provider: Literal["auto", "openai_compatible", "google", "deterministic"] = "auto"
    ai_base_url: str = ""
    ai_model: str = ""
    ai_provider_api_key: str = ""
    ai_timeout_seconds: float = 60.0
    ai_max_tokens: int = 3000
    ai_max_retries: int = 3
    ai_reasoning_effort: Literal["", "low", "medium", "high"] = ""

    # --- Payments -----------------------------------------------------------
    payment_provider: Literal["mock", "stripe"] = "mock"
    payment_webhook_secret: str = "dev-webhook-secret"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    frontend_url: str = "http://localhost:5173"

    # --- HTTP ---------------------------------------------------------------
    # NoDecode: allow a plain comma-separated value in .env. Without it pydantic-settings
    # tries to JSON-decode the field first and the app refuses to start on "a,b".
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    rate_limit_per_minute: int = 120
    max_upload_bytes: int = 5 * 1024 * 1024
    signed_url_ttl_seconds: int = 60

    # --- Processing ---------------------------------------------------------
    celery_eager: bool = False
    ocr_enabled: bool = True
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _production_guards(self) -> Settings:
        if self.environment == "production":
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origin is not allowed in production")
            if not self.supabase_url or not self.supabase_service_role_key:
                raise ValueError("Supabase URL and service role key are required in production")
        if self.supabase_url and not self.supabase_jwks_url:
            object.__setattr__(
                self,
                "supabase_jwks_url",
                f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json",
            )
        if self.supabase_url and not self.supabase_jwt_issuer:
            object.__setattr__(
                self, "supabase_jwt_issuer", f"{self.supabase_url.rstrip('/')}/auth/v1"
            )
        return self

    @property
    def ai_enabled(self) -> bool:
        """True when a model provider is configured rather than the offline fallback."""
        return self.ai_provider != "deterministic" and bool(self.ai_provider_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
