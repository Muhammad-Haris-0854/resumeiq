"""Typed application errors mapped to HTTP responses at a single boundary."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details or {}


class Unauthenticated(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"


class Forbidden(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFound(AppError):
    status_code = 404
    code = "NOT_FOUND"


class Conflict(AppError):
    status_code = 409
    code = "CONFLICT"


class Unprocessable(AppError):
    status_code = 422
    code = "UNPROCESSABLE"


class RateLimited(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class QuotaExceeded(AppError):
    status_code = 429
    code = "QUOTA_EXCEEDED"


class UpstreamFailure(AppError):
    status_code = 502
    code = "UPSTREAM_FAILURE"
