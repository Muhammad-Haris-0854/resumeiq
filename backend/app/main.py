"""Application factory."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    account,
    admin,
    analyses,
    billing,
    builder,
    catalog,
    health,
    job_matches,
    resumes,
)
from app.core.config import get_settings
from app.core.errors import AppError, RateLimited
from app.core.logging import configure_logging, get_logger, request_id_ctx

logger = get_logger(__name__)


class RateLimitMiddleware:
    """Fixed-window limiter per caller.

    Single-process and deliberately simple; in production the CDN/API gateway enforces the same
    numbers across replicas, and this stays as a backstop.
    """

    def __init__(self, app, limit_per_minute: int) -> None:
        self.app = app
        self.limit = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode()
        key = auth[-32:] if auth else (scope.get("client") or ("unknown",))[0]
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= self.limit:
            response = JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED", "message": "Too many requests. Slow down."}},
            )
            await response(scope, receive, send)
            return
        bucket.append(now)
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "api_starting",
        extra={"extra_fields": {"environment": settings.environment, "version": settings.version}},
    )
    yield
    logger.info("api_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "ResumeIQ API: resume extraction, AI analysis, deterministic scoring, job matching "
            "and billing."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
        max_age=600,
    )
    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = rid
        token = request_id_ctx.set(rid)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["X-Request-Id"] = rid
        response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.0f}"
        logger.info(
            "request",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                }
            },
        )
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error(
                "app_error",
                extra={"extra_fields": {"code": exc.code, "path": request.url.path}},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": getattr(request.state, "request_id", "-"),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Some fields are invalid.",
                    "details": {"errors": exc.errors()[:10]},
                    "request_id": getattr(request.state, "request_id", "-"),
                }
            },
        )

    @app.exception_handler(RateLimited)
    async def rate_handler(request: Request, exc: RateLimited) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": exc.code, "message": exc.message, "details": {}}},
        )

    for module in (health, account, resumes, analyses, catalog, job_matches, builder, billing, admin):
        app.include_router(module.router)

    return app


app = create_app()
