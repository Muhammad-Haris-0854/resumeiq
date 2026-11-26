"""Chat-completions provider.

Works with any OpenAI-compatible endpoint (OpenAI, Azure OpenAI, Groq, OpenRouter, vLLM).
Output is schema-validated; one repair attempt is made before giving up so a single malformed
response does not fail an analysis.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import jsonschema

from app.core.logging import get_logger
from app.services.ai.base import AIProviderError

logger = get_logger(__name__)


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.name = "openai_compatible"
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
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
        max_tokens: int = 1800,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        raw = self._call(messages, max_tokens=max_tokens)
        try:
            return self._validate(raw, schema)
        except jsonschema.ValidationError as exc:
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
                        f"({exc.message}). Return only corrected JSON."
                    ),
                },
            ]
            raw = self._call(repair, max_tokens=max_tokens)
            try:
                return self._validate(raw, schema)
            except jsonschema.ValidationError as final_exc:
                raise AIProviderError("Provider returned JSON that does not match the schema") from final_exc

    def _call(self, messages: list[dict[str, str]], *, max_tokens: int) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            if self._client is not None:
                response = self._client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions", json=payload, headers=headers
                    )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(f"AI provider returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError("AI provider is unreachable") from exc

        body = response.json()
        usage = body.get("usage") or {}
        self._tokens = int(usage.get("total_tokens") or 0)
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("AI provider returned an unexpected payload") from exc
        return self._loads(content)

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
            raise AIProviderError("AI provider did not return JSON") from exc
        if not isinstance(parsed, dict):
            raise AIProviderError("AI provider returned a non-object JSON value")
        return parsed

    @staticmethod
    def _validate(raw: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        jsonschema.validate(instance=raw, schema=schema)
        return raw
