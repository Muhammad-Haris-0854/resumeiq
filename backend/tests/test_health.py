from __future__ import annotations


def test_health_reports_version(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_readiness_reports_checks(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "checks" in body
    assert isinstance(body["ready"], bool)


def test_request_id_header_is_echoed(client):
    response = client.get("/health", headers={"X-Request-Id": "abc123"})
    assert response.headers["X-Request-Id"] == "abc123"
