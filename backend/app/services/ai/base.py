"""AI provider abstraction.

Services depend on this protocol only, so the provider can change without touching analysis
logic. Implementations must return JSON matching the supplied schema or raise AIProviderError.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class AIProviderError(Exception):
    """Raised when a provider is unreachable or returns unusable output."""


@runtime_checkable
class AIProvider(Protocol):
    name: str
    model: str

    def complete_json(
        self,
        *,
        task: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        max_tokens: int = 1800,
    ) -> dict[str, Any]:
        """Return a schema-valid dict for `task`."""
        ...

    @property
    def tokens_used(self) -> int:
        """Tokens consumed by the most recent call (0 when unknown)."""
        ...
