"""Subscription lifecycle.

Everything that changes a plan goes through here, and it only ever reacts to a verified
provider event. The frontend's "payment succeeded" screen changes nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.errors import NotFound, UpstreamFailure
from app.core.logging import get_logger
from app.integrations.payments.base import CheckoutSession, PaymentEvent, PaymentProvider
from app.repositories.base import Repositories

logger = get_logger(__name__)


def start_checkout(
    repos: Repositories,
    provider: PaymentProvider,
    *,
    user_id: str,
    email: str,
    plan_code: str,
    interval: str,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    plan = repos.billing.get_plan_by_code(plan_code)
    if not plan or not plan.get("is_active", True):
        raise NotFound("That plan is not available")
    amount = int(
        plan["annual_price_cents"] if interval == "year" else plan["monthly_price_cents"]
    )
    if amount <= 0:
        raise UpstreamFailure("Free plans do not require checkout")
    try:
        return provider.create_checkout(
            user_id=user_id,
            email=email,
            plan_code=plan_code,
            interval=interval,
            amount_cents=amount,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as exc:
        logger.error("checkout_failed", extra={"extra_fields": {"plan": plan_code}})
        raise UpstreamFailure("Could not start checkout. Please try again.") from exc


def apply_event(repos: Repositories, event: PaymentEvent) -> dict[str, Any]:
    """Idempotent: the same event applied twice leaves the same state."""
    if not event.user_id:
        logger.warning("payment_event_without_user", extra={"extra_fields": {"type": event.type}})
        return {"applied": False, "reason": "missing_user"}

    plan_code = event.plan_code or "pro"
    plan = repos.billing.get_plan_by_code(plan_code)
    if not plan:
        logger.warning("payment_event_unknown_plan", extra={"extra_fields": {"plan": plan_code}})
        return {"applied": False, "reason": "unknown_plan"}

    status = "active"
    if event.is_failure:
        status = "past_due"
    elif event.is_cancellation:
        status = "canceled"

    subscription = repos.billing.upsert_subscription(
        event.user_id,
        {
            "plan_id": plan["id"],
            "status": status,
            "interval": event.interval,
            "provider": "mock" if (event.raw or {}).get("mock", True) else "stripe",
            "provider_subscription_id": event.provider_subscription_id,
            "provider_customer_id": event.provider_customer_id,
            "current_period_start": datetime.now(UTC).isoformat(),
            "current_period_end": (
                event.current_period_end.isoformat()
                if event.current_period_end
                else None
            ),
            "cancel_at_period_end": event.is_cancellation,
            "canceled_at": datetime.now(UTC).isoformat() if event.is_cancellation else None,
        },
    )

    if event.transaction_id:
        repos.billing.record_transaction(
            {
                "user_id": event.user_id,
                "subscription_id": subscription.get("id"),
                "provider": subscription.get("provider", "mock"),
                "provider_transaction_id": event.transaction_id,
                "amount_cents": event.amount_cents,
                "currency": event.currency,
                "status": "succeeded" if event.is_success and not event.is_failure else ("failed" if event.is_failure else "pending"),
                "invoice_url": event.invoice_url,
                "description": f"{plan.get('name', plan_code)} · {event.interval}",
                "raw_event": event.raw,
            }
        )

    if event.is_success or event.is_cancellation:
        repos.users.update_profile(event.user_id, {"plan": "free" if event.is_cancellation else plan_code})

    return {"applied": True, "status": status, "plan": plan_code}


def request_cancellation(
    repos: Repositories, provider: PaymentProvider, *, user_id: str
) -> dict[str, Any]:
    subscription = repos.billing.get_subscription(user_id)
    if not subscription:
        raise NotFound("No subscription to cancel")
    try:
        provider.cancel(provider_subscription_id=subscription.get("provider_subscription_id"))
    except Exception:  # the provider may already have cancelled it
        logger.warning("provider_cancel_failed", extra={"extra_fields": {"user_id": user_id}})
    updated = repos.billing.upsert_subscription(
        user_id,
        {
            **{k: subscription[k] for k in ("plan_id", "status", "interval", "provider") if k in subscription},
            "cancel_at_period_end": True,
            "canceled_at": datetime.now(UTC).isoformat(),
        },
    )
    return updated
