"""Live TypeSafe JEV decision backend."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from support_router.backends.base import BackendError
from support_router.config import CompanyConfig
from support_router.domain import BackendDecision, EmailRequest
from support_router.questions import build_questions
from support_router.state import build_state


DEFAULT_BASE_URL = "https://api.typesafe.ai/v1/systemone"


class JevDecisionBackend:
    """Evaluate support emails through TypeSafe's System One API."""

    def __init__(
        self,
        config: CompanyConfig,
        api_key: str,
        model: str = "jev-latest",
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 20.0,
        max_attempts: int = 3,
    ) -> None:
        if not api_key.strip():
            raise ValueError("TYPESAFE_API_KEY must not be empty")
        self._config = config
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts

    def evaluate(self, request: EmailRequest) -> BackendDecision:
        payload = {
            "state": build_state(request),
            "model": self._model,
            "questions": build_questions(self._config),
        }
        response = self._post(payload)
        try:
            return BackendDecision.from_jev_response(
                request.message_id, response, provider="jev"
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise BackendError("JEV response does not match the decision schema") from exc

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = Request(
            self._base_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                with urlopen(request, timeout=self._timeout_seconds) as response:
                    result = json.loads(response.read().decode("utf-8"))
                if not isinstance(result, dict):
                    raise BackendError("JEV returned a non-object response")
                return result
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                last_error = exc
            if attempt < self._max_attempts:
                time.sleep(0.25 * (2 ** (attempt - 1)))
        raise BackendError("JEV request failed after bounded retries") from last_error
