"""Environment and lightweight team configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


MOCK_API_TOKEN = "12345"
TEAM_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_ENV_FILE = Path.home() / ".config" / "support-router" / "secrets.env"


class ConfigurationError(ValueError):
    """Raised when environment or team configuration is invalid."""


class AuthenticationError(PermissionError):
    """Raised when a tool API token is missing or invalid."""


@dataclass(frozen=True)
class TeamConfig:
    team_id: str
    name: str
    email: str
    handles: str


@dataclass(frozen=True)
class CompanyConfig:
    human_review_email: str
    teams: Mapping[str, TeamConfig]

    @property
    def jev_choice_criteria(self) -> dict[str, str]:
        return {team_id: team.handles for team_id, team in self.teams.items()}


def load_company_config(path: Path) -> CompanyConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Unable to load team configuration: {path}") from exc
    if not isinstance(payload, dict) or set(payload) != {"human_review_email", "teams"}:
        raise ConfigurationError(
            "Team configuration must contain exactly human_review_email and teams"
        )
    human_review_email = _required_text(payload, "human_review_email")
    _validate_email(human_review_email, "human_review_email")
    raw_teams = payload["teams"]
    if not isinstance(raw_teams, dict) or not raw_teams:
        raise ConfigurationError("teams must be a non-empty object")
    teams: dict[str, TeamConfig] = {}
    for team_id, raw_team in raw_teams.items():
        if not isinstance(team_id, str) or not TEAM_ID_PATTERN.fullmatch(team_id):
            raise ConfigurationError(f"Invalid team id: {team_id!r}")
        if not isinstance(raw_team, dict) or set(raw_team) != {
            "name",
            "email",
            "handles",
        }:
            raise ConfigurationError(
                f"Team {team_id!r} must contain exactly name, email and handles"
            )
        name = _required_text(raw_team, "name")
        email = _required_text(raw_team, "email")
        handles = _required_text(raw_team, "handles")
        _validate_email(email, f"teams.{team_id}.email")
        teams[team_id] = TeamConfig(team_id, name, email, handles)
    return CompanyConfig(human_review_email=human_review_email, teams=teams)


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{key} must be a non-empty string")
    return value.strip()


def _validate_email(value: str, field_name: str) -> None:
    if not EMAIL_PATTERN.fullmatch(value):
        raise ConfigurationError(f"{field_name} must be a valid email address")


@dataclass(frozen=True)
class Settings:
    backend: str
    api_token: str
    config_file: Path = Path("config/teams.json")
    fixture_file: Path = Path("tests/fixtures/mock_decisions.json")
    typesafe_api_key: str | None = None
    typesafe_default_model: str = "jev-latest"
    typesafe_log_level: str = "warning"
    typesafe_base_url: str = "https://api.typesafe.ai/v1/systemone"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        process_values = os.environ if env is None else env
        configured_env_file = process_values.get("SUPPORT_ROUTER_ENV_FILE")
        env_file = (
            Path(configured_env_file).expanduser()
            if configured_env_file
            else DEFAULT_ENV_FILE
        )
        file_values = _load_env_file(env_file) if env is None or configured_env_file else {}
        values = {**file_values, **process_values}
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
            config_file=Path(values.get("SUPPORT_ROUTER_CONFIG_FILE", "config/teams.json")),
            fixture_file=Path(
                values.get("SUPPORT_ROUTER_FIXTURE_FILE", "tests/fixtures/mock_decisions.json")
            ),
            typesafe_api_key=typesafe_api_key,
            typesafe_default_model=values.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"),
            typesafe_log_level=values.get("TYPESAFE_LOG_LEVEL", "warning"),
            typesafe_base_url=values.get(
                "TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1/systemone"
            ),
        )


def _load_env_file(path: Path) -> dict[str, str]:
    """Load the router's private configuration without modifying process state."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise ConfigurationError(f"Unable to load environment file: {path}") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ConfigurationError(
                f"Invalid environment entry in {path} at line {line_number}"
            )
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "a").isalnum():
            raise ConfigurationError(
                f"Invalid environment key in {path} at line {line_number}"
            )
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values
