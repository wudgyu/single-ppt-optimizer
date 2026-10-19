"""Structured LLM adapter boundary."""

from collections.abc import Mapping
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas.source import FactLedger


class ModelClientError(Exception):
    pass


class FactModelClient(Protocol):
    def complete_json(self, prompt: str) -> Mapping[str, Any]:
        """Return one JSON-compatible mapping from the configured model."""


class StructuredFactAdapter:
    def __init__(
        self,
        client: FactModelClient,
        *,
        model_name: str,
        max_retries: int = 2,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        self.client = client
        self.model_name = model_name
        self.max_retries = max_retries
        self.last_usage: dict[str, int] | None = None

    def extract_fact_ledger(self, prompt: str) -> FactLedger:
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                payload = self.client.complete_json(prompt)
                usage = getattr(self.client, "last_usage", None)
                if isinstance(usage, Mapping):
                    self.last_usage = dict(usage)
                return FactLedger.model_validate(payload)
            except (ModelClientError, TimeoutError, ValidationError) as exc:
                last_error = exc

        raise ModelClientError(
            f"The configured model '{self.model_name}' did not return valid fact JSON."
        ) from last_error
