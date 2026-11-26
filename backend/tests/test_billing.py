from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from app.core.errors import Forbidden, QuotaExceeded
from app.integrations.payments.base import WebhookVerificationError
from app.integrations.payments.mock import MockPaymentProvider
from app.models.enums import PlanCode
from app.services.billing import apply_event
from app.services.entitlements import (
    assert_quota,
    assert_resume_limit,
    require_feature,
    resolve_entitlements,
)
from tests.conftest import USER_ID


def test_free_plan_has_two_analyses():
    ent = resolve_entitlements(PlanCode.FREE, 0)
    assert ent.analysis_quota == 2
    assert ent.analyses_remaining == 2
    assert not ent.allows("jd_matching")


def test_quota_is_enforced():
    ent = resolve_entitlements(PlanCode.FREE, 2)
    with pytest.raises(QuotaExceeded) as exc:
        assert_quota(ent)
    assert exc.value.status_code == 429


def test_pro_features_are_gated():
    free = resolve_entitlements(PlanCode.FREE, 0)
    with pytest.raises(Forbidden):
        require_feature(free, "jd_matching")
    pro = resolve_entitlements(PlanCode.PRO, 0)
    require_feature(pro, "jd_matching")


def test_resume_limit_is_enforced():
    ent = resolve_entitlements(PlanCode.FREE, 0)
    with pytest.raises(Forbidden):
        assert_resume_limit(ent, 2)


def _signed(provider: MockPaymentProvider, body: dict) -> tuple[bytes, dict[str, str]]:
    payload = json.dumps(body).encode()
    signature = hmac.new(b"test-webhook-secret", payload, hashlib.sha256).hexdigest()
    return payload, {"x-signature": signature}


def test_mock_webhook_signature_is_verified():
    provider = MockPaymentProvider("http://localhost:5173", "test-webhook-secret")
    payload, headers = _signed(
        provider,
        {"type": "checkout.completed", "user_id": USER_ID, "plan_code": "pro", "amount_cents": 1200},
    )
    event = provider.verify_webhook(payload, headers)
    assert event.user_id == USER_ID
    assert event.plan_code == "pro"
    assert event.is_success


def test_tampered_webhook_is_rejected():
    provider = MockPaymentProvider("http://localhost:5173", "test-webhook-secret")
    payload, headers = _signed(provider, {"type": "checkout.completed", "user_id": USER_ID})
    with pytest.raises(WebhookVerificationError):
        provider.verify_webhook(payload + b" ", headers)


def test_applying_an_event_upgrades_the_plan(repos):
    provider = MockPaymentProvider("http://localhost:5173", "test-webhook-secret")
    payload, headers = _signed(
        provider,
        {
            "type": "checkout.completed",
            "user_id": USER_ID,
            "plan_code": "pro",
            "amount_cents": 1200,
            "subscription_id": "sub_123",
            "transaction_id": "tx_123",
        },
    )
    event = provider.verify_webhook(payload, headers)
    result = apply_event(repos, event)
    assert result["applied"] is True
    assert repos.users.get_profile(USER_ID)["plan"] == "pro"
    assert repos.billing.subscriptions[USER_ID]["status"] == "active"
    assert repos.billing.transactions[-1]["provider_transaction_id"] == "tx_123"


def test_cancellation_returns_the_user_to_free(repos):
    provider = MockPaymentProvider("http://localhost:5173", "test-webhook-secret")
    repos.users.update_profile(USER_ID, {"plan": "pro"})
    payload, headers = _signed(
        provider,
        {"type": "subscription.canceled", "user_id": USER_ID, "plan_code": "pro", "transaction_id": "tx_9"},
    )
    apply_event(repos, provider.verify_webhook(payload, headers))
    assert repos.users.get_profile(USER_ID)["plan"] == "free"


def test_event_without_user_is_ignored(repos):
    provider = MockPaymentProvider("http://localhost:5173", "test-webhook-secret")
    payload, headers = _signed(provider, {"type": "checkout.completed", "plan_code": "pro"})
    result = apply_event(repos, provider.verify_webhook(payload, headers))
    assert result == {"applied": False, "reason": "missing_user"}
