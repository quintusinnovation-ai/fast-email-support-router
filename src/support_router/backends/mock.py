"""Deterministic subject-based decision backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from support_router.backends.base import BackendError
from support_router.config import AuthenticationError, MOCK_API_TOKEN
from support_router.domain import BackendDecision, EmailRequest


class FixtureError(BackendError):
    """Raised when mock fixtures are missing or invalid."""


def normalize_subject(subject: str) -> str:
    return " ".join(subject.casefold().split())


class MockDecisionBackend:
    def __init__(self, fixture_file: Path, api_token: str) -> None:
        if api_token != MOCK_API_TOKEN:
            raise AuthenticationError("Invalid mock API token")
        self._fixtures = self._load_fixtures(fixture_file)

    @staticmethod
    def _load_fixtures(fixture_file: Path) -> dict[str, dict[str, Any]]:
        try:
            payload = json.loads(fixture_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FixtureError(f"Unable to load mock fixtures: {fixture_file}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("subjects"), dict):
            raise FixtureError("Fixture file must contain a 'subjects' object")
        return {
            normalize_subject(subject): result
            for subject, result in payload["subjects"].items()
        }

    def evaluate(self, request: EmailRequest) -> BackendDecision:
        payload = self._fixtures.get(normalize_subject(request.subject))
        if payload is None:
            payload = self._fixtures.get("__default__")
        if payload is None:
            raise FixtureError("Fixture file must define a '__default__' result")
        try:
            return BackendDecision.from_jev_response(
                request.message_id, payload, provider="mock"
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FixtureError("Fixture result does not match the decision schema") from exc
