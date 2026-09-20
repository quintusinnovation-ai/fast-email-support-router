from pathlib import Path

import pytest

from support_router.backends.mock import MockDecisionBackend
from support_router.config import Settings
from support_router.factory import create_backend


FIXTURES = Path(__file__).parent / "fixtures" / "mock_decisions.json"


def test_factory_builds_mock_backend():
    settings = Settings(
        backend="mock",
        api_token="12345",
        fixture_file=FIXTURES,
    )
    assert isinstance(create_backend(settings), MockDecisionBackend)


def test_factory_does_not_silently_substitute_jev():
    settings = Settings(
        backend="jev",
        api_token="live",
        fixture_file=FIXTURES,
        typesafe_api_key="secret",
    )
    with pytest.raises(NotImplementedError):
        create_backend(settings)
