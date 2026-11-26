"""Payment provider factory."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.integrations.payments.base import (
    CheckoutSession,
    PaymentEvent,
    PaymentProvider,
    WebhookVerificationError,
)
from app.integrations.payments.mock import MockPaymentProvider
from app.integrations.payments.stripe import StripePaymentProvider


def build_payment_provider(settings: Settings | None = None) -> PaymentProvider:
    settings = settings or get_settings()
    if settings.payment_provider == "stripe":
        if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
            raise AppError(
                "Stripe is selected but STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET is missing",
                code="PAYMENT_NOT_CONFIGURED",
                status_code=503,
            )
        return StripePaymentProvider(
            settings.stripe_secret_key, settings.stripe_webhook_secret, settings.frontend_url
        )
    return MockPaymentProvider(settings.frontend_url, settings.payment_webhook_secret)


__all__ = [
    "CheckoutSession",
    "PaymentEvent",
    "PaymentProvider",
    "WebhookVerificationError",
    "build_payment_provider",
    "MockPaymentProvider",
    "StripePaymentProvider",
]
