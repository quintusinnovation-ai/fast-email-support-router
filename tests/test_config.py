import pytest

from support_router.config import AuthenticationError, ConfigurationError, Settings


def test_mock_is_default_and_requires_test_token():
    settings = Settings.from_env({"SUPPORT_ROUTER_API_TOKEN": "12345"})
    assert settings.backend == "mock"


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
