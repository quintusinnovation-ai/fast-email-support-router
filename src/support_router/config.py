"""Environment configuration for decision backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import os


MOCK_API_TOKEN = "12345"


class ConfigurationError(ValueError):
    """Raised when environment configuration is incomplete or invalid."""


class AuthenticationError(PermissionError):
    """Raised when a tool API token is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    backend: str
    api_token: str
    fixture_file: Path
    typesafe_api_key: str | None = None
    typesafe_default_model: str = "jev-latest"
    typesafe_log_level: str = "warning"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        backend = values.get("SUPPORT_ROUTER_BACKEND", "mock").strip().lower()
        if backend not in {"mock", "jev"}:
            raise ConfigurationError("SUPPORT_ROUTER_BACKEND must be 'mock' or 'jev'")

        api_token = values.get("SUPPORT_ROUTER_API_TOKEN", "").strip()
        if not api_token:
            raise AuthenticationError("SUPPORT_ROUTER_API_TOKEN is required")
        if backend == "mock" and api_token != MOCK_API_TOKEN:
            raise AuthenticationError("Invalid mock API token")

        typesafe_api_key = values.get("TYPESAFE_API_KEY", "").strip() or None
        if backend == "jev" and not typesafe_api_key:
            raise ConfigurationError("TYPESAFE_API_KEY is required for the JEV backend")

        return cls(
            backend=backend,
            api_token=api_token,
            fixture_file=Path(
                values.get(
                    "SUPPORT_ROUTER_FIXTURE_FILE",
                    "tests/fixtures/mock_decisions.json",
                )
            ),
            typesafe_api_key=typesafe_api_key,
            typesafe_default_model=values.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"),
            typesafe_log_level=values.get("TYPESAFE_LOG_LEVEL", "warning"),
        )
