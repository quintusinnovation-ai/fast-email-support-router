import json
from pathlib import Path

import pytest

from support_router.config import (
    AuthenticationError,
    ConfigurationError,
    Settings,
    load_company_config,
)


CONFIG = Path(__file__).parents[1] / "config" / "teams.json"


def test_mock_is_default_and_requires_test_token():
    settings = Settings.from_env({"SUPPORT_ROUTER_API_TOKEN": "12345"})
    assert settings.backend == "mock"
    assert settings.config_file == Path("config/teams.json")


def test_missing_token_is_rejected():
    with pytest.raises(AuthenticationError):
        Settings.from_env({})


def test_wrong_mock_token_is_rejected():
    with pytest.raises(AuthenticationError):
        Settings.from_env({"SUPPORT_ROUTER_API_TOKEN": "wrong"})


def test_jev_requires_typesafe_key():
    with pytest.raises(ConfigurationError):
        Settings.from_env(
            {"SUPPORT_ROUTER_BACKEND": "jev", "SUPPORT_ROUTER_API_TOKEN": "live"}
        )


def test_settings_load_router_owned_env_file(tmp_path):
    env_file = tmp_path / "router.env"
    env_file.write_text(
        "SUPPORT_ROUTER_BACKEND=jev\n"
        "SUPPORT_ROUTER_API_TOKEN=live\n"
        "TYPESAFE_API_KEY=from-file\n",
        encoding="utf-8",
    )

    settings = Settings.from_env({"SUPPORT_ROUTER_ENV_FILE": str(env_file)})

    assert settings.backend == "jev"
    assert settings.api_token == "live"
    assert settings.typesafe_api_key == "from-file"


def test_process_environment_overrides_router_env_file(tmp_path):
    env_file = tmp_path / "router.env"
    env_file.write_text(
        "SUPPORT_ROUTER_API_TOKEN=12345\nTYPESAFE_DEFAULT_MODEL=old-model\n",
        encoding="utf-8",
    )

    settings = Settings.from_env(
        {
            "SUPPORT_ROUTER_ENV_FILE": str(env_file),
            "TYPESAFE_DEFAULT_MODEL": "new-model",
        }
    )

    assert settings.typesafe_default_model == "new-model"


def test_minimal_config_loads_and_maps_directly_to_jev_choice_criteria():
    config = load_company_config(CONFIG)
    assert set(config.teams) == {"billing", "technical_support", "customer_success"}
    assert config.jev_choice_criteria["billing"] == config.teams["billing"].handles
    assert config.human_review_email == "support-router@acme.example"


@pytest.mark.parametrize(
    "payload",
    [
        {"human_review_email": "review@example.com", "teams": {}},
        {"human_review_email": "invalid", "teams": {"billing": {"name": "Billing", "email": "billing@example.com", "handles": "Bills"}}},
        {"human_review_email": "review@example.com", "teams": {"Bad ID": {"name": "Billing", "email": "billing@example.com", "handles": "Bills"}}},
        {"human_review_email": "review@example.com", "teams": {"billing": {"name": "Billing", "email": "billing@example.com", "handles": "Bills", "extra": True}}},
    ],
)
def test_invalid_minimal_config_is_rejected(tmp_path, payload):
    path = tmp_path / "teams.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_company_config(path)
