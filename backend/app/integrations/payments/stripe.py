"""Stripe adapter.

Implemented against the REST API with httpx so the backend has no SDK lock-in. Checkout
Sessions carry the user id in metadata; webhooks are verified with the documented
`Stripe-Signature` scheme before anything is trusted.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.logging import get_logger
from app.integrations.payments.base import (
    CheckoutSession,
    PaymentEvent,
    WebhookVerificationError,
)

logger = get_logger(__name__)

API_BASE = "https://api.stripe.com/v1"
TOLERANCE_SECONDS = 300


class StripePaymentProvider:
    name = "stripe"

    def __init__(self, secret_key: str, webhook_secret: str, frontend_url: str) -> None:
        self._key = secret_key
        self._webhook_secret = webhook_secret
        self._frontend_url = frontend_url.rstrip("/")

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"{API_BASE}{path}",
                data=data,
                auth=(self._key, ""),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code >= 400:
            logger.error(
                "stripe_error",
                extra={"extra_fields": {"path": path, "status": response.status_code}},
            )
            raise httpx.HTTPStatusError(
                "Stripe request failed", request=response.request, response=response
            )
        return response.json()

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
        payload = {
            "mode": "subscription",
            "customer_email": email,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": user_id,
            "metadata[user_id]": user_id,
            "metadata[plan_code]": plan_code,
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][recurring][interval]": interval,
            "line_items[0][price_data][product_data][name]": f"ResumeIQ {plan_code.title()}",
        }
        session = self._post("/checkout/sessions", payload)
        return CheckoutSession(id=session["id"], url=session["url"])

    def create_portal(self, *, customer_id: str | None, return_url: str) -> str:
        if not customer_id:
            return f"{self._frontend_url}/pricing"
        session = self._post("/billing_portal/sessions", {"customer": customer_id, "return_url": return_url})
        return session["url"]

    def cancel(self, *, provider_subscription_id: str | None) -> None:
        if not provider_subscription_id:
            return
        with httpx.Client(timeout=20.0) as client:
            client.delete(
                f"{API_BASE}/subscriptions/{provider_subscription_id}",
                auth=(self._key, ""),
            )

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> PaymentEvent:
        header = headers.get("stripe-signature") or headers.get("Stripe-Signature") or ""
        timestamp, signatures = self._parse_header(header)
        if timestamp is None or not signatures:
            raise WebhookVerificationError("Missing Stripe signature")
        if abs(time.time() - timestamp) > TOLERANCE_SECONDS:
            raise WebhookVerificationError("Stripe signature timestamp outside tolerance")
        signed = f"{timestamp}.".encode() + payload
        expected = hmac.new(self._webhook_secret.encode(), signed, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
            raise WebhookVerificationError("Stripe signature mismatch")
        try:
            event = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("Payload is not JSON") from exc
        return self.parse(event)

    @staticmethod
    def _parse_header(header: str) -> tuple[int | None, list[str]]:
        timestamp: int | None = None
        signatures: list[str] = []
        for part in (header or "").split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key == "t":
                try:
                    timestamp = int(value)
                except ValueError:
                    timestamp = None
            elif key == "v1":
                signatures.append(value)
        return timestamp, signatures

    def parse(self, event: dict[str, Any]) -> PaymentEvent:
        event_type = str(event.get("type", ""))
        obj: dict[str, Any] = (event.get("data") or {}).get("object") or {}
        metadata = obj.get("metadata") or {}
        user_id = metadata.get("user_id") or obj.get("client_reference_id")
        plan_code = metadata.get("plan_code")
        period_end = obj.get("current_period_end")
        mapping = {
            "checkout.session.completed": "checkout.completed",
            "invoice.payment_succeeded": "subscription.renewed",
            "customer.subscription.updated": "subscription.updated",
            "customer.subscription.deleted": "subscription.canceled",
            "invoice.payment_failed": "payment.failed",
        }
        return PaymentEvent(
            type=mapping.get(event_type, event_type),
            status="active" if "succeeded" in event_type or "completed" in event_type else "canceled",
            user_id=user_id,
            plan_code=plan_code,
            interval=str((obj.get("plan") or {}).get("interval", metadata.get("interval", "month"))),
            provider_subscription_id=obj.get("subscription") or obj.get("id"),
            provider_customer_id=obj.get("customer"),
            transaction_id=obj.get("id") or event.get("id"),
            amount_cents=int(obj.get("amount_paid") or obj.get("amount_total") or 0),
            currency=str(obj.get("currency", "usd")),
            current_period_end=(
                datetime.fromtimestamp(int(period_end), tz=UTC) if period_end else None
            ),
            invoice_url=obj.get("hosted_invoice_url"),
            raw=event,
        )
