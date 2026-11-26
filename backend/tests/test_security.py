from __future__ import annotations

from datetime import UTC

import pytest

from app.core.errors import Unauthenticated
from tests.conftest import make_token


def test_valid_token_is_accepted(verifier):
    principal = verifier.verify(make_token())
    assert principal.user_id == "11111111-1111-1111-1111-111111111111"


def test_expired_token_is_rejected(verifier):
    with pytest.raises(Unauthenticated):
        verifier.verify(make_token(expires_in=-10))


def test_wrong_signature_is_rejected(verifier):
    with pytest.raises(Unauthenticated):
        verifier.verify(make_token(secret="not-the-secret"))


def test_token_without_subject_is_rejected(verifier):
    from datetime import datetime, timedelta

    import jwt

    token = jwt.encode(
        {"aud": "authenticated", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "test-jwt-secret",
        algorithm="HS256",
    )
    with pytest.raises(Unauthenticated):
        verifier.verify(token)


def test_missing_token_is_rejected(verifier):
    with pytest.raises(Unauthenticated):
        verifier.verify("")


def test_protected_endpoint_requires_bearer(repos):
    from fastapi.testclient import TestClient

    from app.api.deps import get_repositories
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_repositories] = lambda: repos
    with TestClient(app) as anon:
        for headers in ({}, {"Authorization": ""}, {"Authorization": "Bearer not-a-token"}):
            response = anon.get("/v1/me", headers=headers)
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "UNAUTHENTICATED"
