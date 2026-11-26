"""Chat-completions provider.

Works with any OpenAI-compatible endpoint (OpenAI, Gemini, Azure OpenAI, Groq, OpenRouter,
vLLM). Three things make it production-safe:

* transient failures (429, 5xx, timeouts) are retried with backoff;
* output is schema-validated, with one repair attempt when the model's JSON is wrong or cut off;
* truncation is reported as truncation, so the operator knows to raise the token budget instead
  of hunting a schema bug.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

import httpx
import jsonschema

from app.core.logging import get_logger
from app.services.ai.base import AIOutputError, AIProviderError

logger = get_logger(__name__)

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45.0,
        max_retries: int = 3,
        reasoning_effort: str = "",
        client: httpx.Client | None = None,
    ) -> None:
        self.name = "openai_compatible"
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._reasoning_effort = reasoning_effort
        self._client = client
        self._tokens = 0

    @property
    def tokens_used(self) -> int:
        return self._tokens

    def complete_json(
        self,
        *,
        task: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        max_tokens: int = 3000,
    ) -> dict[str, Any]:
        # The schema must travel with the request: without it the model invents property
        # names, and every response fails validation.
        schema_block = (
            "\n\nREQUIRED JSON SCHEMA (use these exact property names, no extra keys):\n"
            f"{json.dumps(schema, separators=(',', ':'))}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user + schema_block},
        ]
        raw = self._call(messages, max_tokens=max_tokens)
        try:
            return self._validate(raw, schema)
        except (jsonschema.ValidationError, AIOutputError) as exc:
            logger.warning(
                "ai_schema_violation",
                extra={"extra_fields": {"task": task, "error": str(exc)[:200]}},
            )
            repair = messages + [
                {"role": "assistant", "content": json.dumps(raw)[:4000]},
                {
                    "role": "user",
                    "content": (
                        "That response did not match the required JSON schema "
                        f"({getattr(exc, 'message', str(exc))}).\n"
                        f"{schema_block}\nReturn only corrected JSON."
                    ),
                },
            ]
            try:
                repaired = self._call(repair, max_tokens=max_tokens)
                return self._validate(repaired, schema)
            except jsonschema.ValidationError as final_exc:
                raise AIOutputError("Provider returned JSON that does not match the schema") from final_exc

    def _call(self, messages: list[dict[str, str]], *, max_tokens: int) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        # Reasoning models spend output tokens on thinking; a low budget keeps JSON intact.
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = self._post(payload, headers)
        usage = body.get("usage") or {}
        self._tokens += int(usage.get("total_tokens") or 0)

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIOutputError("AI provider returned an unexpected payload") from exc

        if choice.get("finish_reason") == "length":
            raise AIOutputError(
                "The model ran out of output tokens before finishing. Raise AI_MAX_TOKENS."
            )
        return self._loads(content)

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        """POST with retries for transient failures only."""
        url = f"{self._base_url}/chat/completions"
        attempt = 0
        while True:
            attempt += 1
            try:
                if self._client is not None:
                    response = self._client.post(url, json=payload, headers=headers)
                else:
                    with httpx.Client(timeout=self._timeout) as client:
                        response = client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                if attempt > self._max_retries:
                    raise AIProviderError("AI provider is unreachable") from exc
                self._sleep(attempt)
                continue

            if response.status_code in RETRYABLE_STATUS and attempt <= self._max_retries:
                logger.warning(
                    "ai_provider_retry",
                    extra={
                        "extra_fields": {
                            "status": response.status_code,
                            "attempt": attempt,
                            "model": self.model,
                        }
                    },
                )
                self._sleep(
                    attempt,
                    status=response.status_code,
                    retry_after=response.headers.get("retry-after"),
                )
                continue

            if response.status_code >= 400:
                raise AIProviderError(f"AI provider returned {response.status_code}")

            body = response.json()
            # Some gateways wrap errors in a single-element array.
            if isinstance(body, list):
                body = body[0] if body else {}
            if not isinstance(body, dict):
                raise AIOutputError("AI provider returned an unexpected payload")
            return body

    @staticmethod
    def _sleep(attempt: int, *, status: int | None = None, retry_after: str | None = None) -> None:
        """Back off longer for rate limits than for a brief upstream blip."""
        if retry_after and retry_after.isdigit():
            delay = float(retry_after)
        elif status == 429:
            # Free-tier quotas are per minute, so a 2 second retry is wasted.
            delay = min(10 * attempt, 60)
        else:
            delay = min(2**attempt, 8)
        time.sleep(delay + random.uniform(0, 1.0))

    @staticmethod
    def _loads(content: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = (content or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1] if "```" in text[3:] else text[3:]
            text = text.lstrip("json").strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIOutputError("AI provider did not return JSON") from exc
        if not isinstance(parsed, dict):
            raise AIOutputError("AI provider returned a non-object JSON value")
        return parsed

    @classmethod
    def _validate(cls, raw: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        """Validate after dropping keys the schema does not define.

        Models routinely add helpful extra fields. Required fields and types are still enforced,
        but an unexpected key no longer costs a repair round trip and a token budget.
        """
        pruned = cls._prune(raw, schema)
        jsonschema.validate(instance=pruned, schema=schema)
        return pruned

    @classmethod
    def _prune(cls, instance: Any, schema: dict[str, Any]) -> Any:
        if isinstance(instance, list):
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                return [cls._prune(item, item_schema) for item in instance]
            return instance
        if not isinstance(instance, dict):
            return instance

        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return instance

        strict = schema.get("additionalProperties") is False
        result: dict[str, Any] = {}
        for key, value in instance.items():
            if key in properties:
                result[key] = cls._prune(value, properties[key])
            elif not strict:
                result[key] = value
        return result
