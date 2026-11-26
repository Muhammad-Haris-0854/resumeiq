"""Deterministic local provider.

Lets the entire subscription lifecycle (checkout, activation, renewal, cancellation, failed
payment) be exercised and tested with no network and no gateway account.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings
from app.integrations.payments.base import (
    CheckoutSession,
    PaymentEvent,
    WebhookVerificationError,
)


class MockPaymentProvider:
    name = "mock"

    def __init__(self, frontend_url: str, webhook_secret: str) -> None:
        self._frontend_url = frontend_url.rstrip("/")
        self._secret = webhook_secret.encode()

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
    ) -> CheckoutSession:
        session_id = f"mock_cs_{uuid.uuid4().hex[:16]}"
        url = (
            f"{self._frontend_url}/billing/mock-checkout"
            f"?session={session_id}&plan={plan_code}&interval={interval}"
            f"&amount={amount_cents}&success={success_url}&cancel={cancel_url}"
        )
        return CheckoutSession(id=session_id, url=url)

    def create_portal(self, *, customer_id: str | None, return_url: str) -> str:
        return f"{self._frontend_url}/billing/mock-portal?return={return_url}"

    def cancel(self, *, provider_subscription_id: str | None) -> None:
        return None

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> PaymentEvent:
        signature = headers.get("x-signature") or headers.get("X-Signature") or ""
        expected = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise WebhookVerificationError("Invalid mock webhook signature")
        try:
            body: dict[str, Any] = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("Webhook payload is not JSON") from exc
        return self.parse(body)

    def parse(self, body: dict[str, Any]) -> PaymentEvent:
        period_end = body.get("current_period_end")
        return PaymentEvent(
            type=str(body.get("type", "checkout.completed")),
            status=str(body.get("status", "active")),
            user_id=body.get("user_id"),
            plan_code=body.get("plan_code"),
            interval=str(body.get("interval", "month")),
            provider_subscription_id=body.get("subscription_id") or f"mock_sub_{uuid.uuid4().hex[:12]}",
            provider_customer_id=body.get("customer_id") or "mock_customer",
            transaction_id=body.get("transaction_id") or f"mock_tx_{uuid.uuid4().hex[:12]}",
            amount_cents=int(body.get("amount_cents", 0) or 0),
            currency=str(body.get("currency", "usd")),
            current_period_end=(
                datetime.fromisoformat(period_end)
                if period_end
                else datetime.now(UTC) + timedelta(days=30)
            ),
            invoice_url=body.get("invoice_url"),
            raw=body,
        )


def build_mock_provider() -> MockPaymentProvider:
    settings = get_settings()
    return MockPaymentProvider(settings.frontend_url, settings.payment_webhook_secret)
