"""Plans, subscriptions, invoices and provider webhooks."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status

from app.api.deps import (
    CurrentUser,
    current_user,
    get_payments,
    get_repositories,
)
from app.core.config import get_settings
from app.core.errors import AppError, NotFound, UpstreamFailure
from app.core.logging import get_logger
from app.integrations.payments import PaymentProvider, WebhookVerificationError
from app.repositories.base import Repositories
from app.schemas.core import (
    CheckoutOut,
    CheckoutRequest,
    InvoiceOut,
    PlanOut,
    SubscriptionOut,
)
from app.services.billing import apply_event, request_cancellation, start_checkout

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans(repos: Repositories = Depends(get_repositories)) -> list[PlanOut]:
    return [
        PlanOut(
            id=row.get("id"),
            code=row["code"],
            name=row["name"],
            description=row.get("description"),
            monthly_price_cents=int(row.get("monthly_price_cents", 0)),
            annual_price_cents=int(row.get("annual_price_cents", 0)),
            analysis_quota=int(row.get("analysis_quota", 0)),
            max_resumes=int(row.get("max_resumes", 0)),
            features=row.get("features") or {},
        )
        for row in repos.billing.list_plans()
    ]


@router.get("/subscription", response_model=SubscriptionOut)
def read_subscription(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> SubscriptionOut:
    row = repos.billing.get_subscription(user.id)
    if not row:
        return SubscriptionOut(plan=user.plan, status="none", interval=None)
    plan_code = (row.get("subscription_plans") or {}).get("code") or user.plan.value
    return SubscriptionOut(
        plan=plan_code,
        status=row.get("status", "active"),
        interval=row.get("interval"),
        current_period_end=row.get("current_period_end"),
        cancel_at_period_end=bool(row.get("cancel_at_period_end")),
        provider=row.get("provider"),
    )


@router.post("/checkout", response_model=CheckoutOut)
def create_checkout(
    payload: CheckoutRequest,
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
    provider: PaymentProvider = Depends(get_payments),
) -> CheckoutOut:
    frontend_url = get_settings().frontend_url
    session = start_checkout(
        repos,
        provider,
        user_id=user.id,
        email=user.email,
        plan_code=payload.plan_code,
        interval=payload.interval,
        success_url=f"{frontend_url}/billing/success",
        cancel_url=f"{frontend_url}/pricing",
    )
    repos.admin.audit(user.id, "billing.checkout_started", "plan", payload.plan_code, {"interval": payload.interval})
    return CheckoutOut(checkout_url=session.url, session_id=session.id)


@router.post("/portal")
def create_portal(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
    provider: PaymentProvider = Depends(get_payments),
) -> dict[str, str]:
    subscription = repos.billing.get_subscription(user.id) or {}
    url = provider.create_portal(
        customer_id=subscription.get("provider_customer_id"),
        return_url=f"{get_settings().frontend_url}/subscription",
    )
    return {"portal_url": url}


@router.post("/cancel", response_model=SubscriptionOut)
def cancel_subscription(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
    provider: PaymentProvider = Depends(get_payments),
) -> SubscriptionOut:
    row = request_cancellation(repos, provider, user_id=user.id)
    repos.admin.audit(user.id, "billing.canceled", "subscription", row.get("id"), {})
    return SubscriptionOut(
        plan=user.plan,
        status=row.get("status", "active"),
        interval=row.get("interval"),
        current_period_end=row.get("current_period_end"),
        cancel_at_period_end=bool(row.get("cancel_at_period_end")),
        provider=row.get("provider"),
    )


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    user: CurrentUser = Depends(current_user),
    repos: Repositories = Depends(get_repositories),
) -> list[InvoiceOut]:
    rows = repos.billing.list_transactions(user.id, 24)
    return [
        InvoiceOut(
            id=row["id"],
            amount_cents=int(row.get("amount_cents", 0)),
            currency=row.get("currency", "usd"),
            status=row.get("status", "pending"),
            description=row.get("description"),
            invoice_url=row.get("invoice_url"),
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.post("/webhook/{provider_name}", status_code=status.HTTP_200_OK)
async def payment_webhook(
    provider_name: str,
    request: Request,
    signature: str | None = Header(default=None),
    repos: Repositories = Depends(get_repositories),
    provider: PaymentProvider = Depends(get_payments),
) -> dict[str, Any]:
    """Server-side verification is the only thing that can change a plan."""
    if provider.name != provider_name:
        raise NotFound("Unknown payment provider")
    payload = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}
    if signature:
        headers.setdefault("x-signature", signature)
    try:
        event = provider.verify_webhook(payload, headers)
    except WebhookVerificationError as exc:
        logger.warning("webhook_rejected", extra={"extra_fields": {"provider": provider_name}})
        raise AppError(str(exc), code="INVALID_SIGNATURE", status_code=401) from exc
    try:
        result = apply_event(repos, event)
    except Exception as exc:
        logger.exception("webhook_apply_failed")
        raise UpstreamFailure("Webhook could not be applied") from exc
    repos.admin.audit(event.user_id, "billing.webhook", "subscription", event.provider_subscription_id, {"type": event.type})
    return {"received": True, **result}
