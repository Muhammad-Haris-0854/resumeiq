"""Supabase JWT verification.

The API never trusts a client-supplied user id, plan or role. Identity comes from a verified
token; authorisation is resolved from the database afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.errors import Unauthenticated
from app.core.logging import get_logger

logger = get_logger(__name__)

ASYMMETRIC_ALGORITHMS = ["ES256", "RS256"]
LEGACY_ALGORITHMS = ["HS256"]


@dataclass(frozen=True)
class Principal:
    """A verified caller."""

    user_id: str
    email: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_email_verified(self) -> bool:
        return bool(self.claims.get("email_verified", True))


class TokenVerifier:
    """Verifies Supabase access tokens via JWKS, with an HS256 fallback."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jwks_client: PyJWKClient | None = None
        if settings.supabase_jwks_url:
            self._jwks_client = PyJWKClient(settings.supabase_jwks_url, cache_keys=True)

    def verify(self, token: str) -> Principal:
        if not token:
            raise Unauthenticated("Missing access token")
        claims = self._decode(token)
        subject = claims.get("sub")
        if not subject:
            raise Unauthenticated("Token has no subject")
        return Principal(user_id=str(subject), email=claims.get("email"), claims=claims)

    def _decode(self, token: str) -> dict[str, Any]:
        options = {"verify_aud": bool(self._settings.supabase_jwt_aud)}
        common: dict[str, Any] = {
            "audience": self._settings.supabase_jwt_aud,
            "options": options,
        }
        if self._settings.supabase_jwt_issuer:
            common["issuer"] = self._settings.supabase_jwt_issuer

        if self._settings.supabase_jwt_secret:
            try:
                return jwt.decode(
                    token, self._settings.supabase_jwt_secret, algorithms=LEGACY_ALGORITHMS, **common
                )
            except jwt.PyJWTError:
                pass

        if self._jwks_client is not None:
            try:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(
                    token, signing_key.key, algorithms=ASYMMETRIC_ALGORITHMS, **common
                )
            except jwt.PyJWTError as exc:
                logger.info("jwt_rejected", extra={"extra_fields": {"reason": str(exc)}})
                raise Unauthenticated("Invalid or expired session") from exc
            except Exception as exc:  # network / JWKS fetch failure
                logger.warning("jwks_unavailable", extra={"extra_fields": {"reason": str(exc)}})
                raise Unauthenticated("Unable to verify session right now") from exc

        raise Unauthenticated("Token verification is not configured")
