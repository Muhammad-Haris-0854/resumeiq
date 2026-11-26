"""Provider transport behaviour, exercised with a stub HTTP client (no network, no key)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.services.ai.base import AIOutputError, AIProviderError
from app.services.ai.openai_compatible import OpenAICompatibleProvider

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "issues"],
    "properties": {
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title"],
                "properties": {"title": {"type": "string"}, "severity": {"type": "string"}},
            },
        },
    },
}


class _Response:
    def __init__(self, status_code: int, body: Any, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self) -> Any:
        return self._body


def _completion(payload: Any, finish_reason: str = "stop") -> _Response:
    content = payload if isinstance(payload, str) else json.dumps(payload)
    return _Response(
        200,
        {
            "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
            "usage": {"total_tokens": 42},
        },
    )


class _Client:
    def __init__(self, responses: list[_Response]) -> None:
        self.responses = responses
        self.calls = 0

    def post(self, url: str, json: Any = None, headers: Any = None) -> _Response:  # noqa: A002
        self.calls += 1
        return self.responses.pop(0)


def _provider(client: _Client, **kwargs: Any) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="test-key",
        model="test-model",
        max_retries=kwargs.pop("max_retries", 2),
        client=client,  # type: ignore[arg-type]
        **kwargs,
    )


def _ask(provider: OpenAICompatibleProvider) -> dict[str, Any]:
    return provider.complete_json(
        task="test", system="sys", user="usr", schema=SCHEMA, max_tokens=500
    )


def test_extra_keys_are_dropped_instead_of_triggering_a_repair() -> None:
    client = _Client([_completion({"summary": "ok", "issues": [{"title": "t", "note": "x"}], "extra": 1})])
    result = _ask(_provider(client))
    assert result == {"summary": "ok", "issues": [{"title": "t"}]}
    assert client.calls == 1


def test_markdown_fences_are_tolerated() -> None:
    fenced = '```json\n{"summary": "ok", "issues": []}\n```'
    result = _ask(_provider(_Client([_completion(fenced)])))
    assert result["summary"] == "ok"


def test_truncated_output_names_the_cause() -> None:
    client = _Client([_completion({"summary": "half"}, finish_reason="length")])
    with pytest.raises(AIOutputError) as exc:
        _ask(_provider(client))
    assert "AI_MAX_TOKENS" in str(exc.value)


def test_transient_status_is_retried_then_succeeds() -> None:
    client = _Client([_Response(503, {"error": "busy"}), _completion({"summary": "ok", "issues": []})])
    provider = _provider(client)
    assert _ask(provider)["summary"] == "ok"
    assert client.calls == 2


def test_retries_are_bounded() -> None:
    client = _Client([_Response(503, {}), _Response(503, {}), _Response(503, {})])
    with pytest.raises(AIProviderError):
        _ask(_provider(client, max_retries=2))
    assert client.calls == 3


def test_client_error_is_not_retried() -> None:
    client = _Client([_Response(400, {"error": "bad model"})])
    with pytest.raises(AIProviderError) as exc:
        _ask(_provider(client))
    assert "400" in str(exc.value)
    assert client.calls == 1


def test_schema_violation_gets_one_repair_attempt() -> None:
    client = _Client(
        [
            _completion({"summary": 5, "issues": []}),  # wrong type, not just an extra key
            _completion({"summary": "fixed", "issues": []}),
        ]
    )
    assert _ask(_provider(client))["summary"] == "fixed"
    assert client.calls == 2


def test_non_json_answer_raises_output_error() -> None:
    client = _Client([_completion("I cannot do that.")])
    with pytest.raises(AIOutputError):
        _ask(_provider(client))
