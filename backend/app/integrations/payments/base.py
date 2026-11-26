"""Payment provider contract.

The subscription lifecycle is identical for every gateway; only checkout, portal and signature
verification differ. Entitlements are derived from `subscriptions` rows written by a verified
webhook, never from a client success screen.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


class WebhookVerificationError(Exception):
    """Signature missing or invalid. The event must be ignored."""


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str


@dataclass(frozen=True)
class PaymentEvent:
    type: str
    status: str
    user_id: str | None = None
    plan_code: str | None = None
    interval: str = "month"
    provider_subscription_id: str | None = None
    provider_customer_id: str | None = None
    transaction_id: str | None = None
    amount_cents: int = 0
    currency: str = "usd"
    current_period_end: datetime | None = None
    invoice_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.type in {"checkout.completed", "subscription.renewed", "subscription.updated"}

    @property
    def is_cancellation(self) -> bool:
        return self.type in {"subscription.canceled", "subscription.deleted"}

    @property
    def is_failure(self) -> bool:
        return self.type in {"payment.failed", "subscription.past_due"}


class PaymentProvider(Protocol):
    name: str

    def create_checkout(
        self,
        *,
        user_id: str,
        email: str,
        plan_code: str,
        interval: str,
        amount_cents: int,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSession: ...

    def create_portal(self, *, customer_id: str | None, return_url: str) -> str: ...

    def cancel(self, *, provider_subscription_id: str | None) -> None: ...

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> PaymentEvent: ...
