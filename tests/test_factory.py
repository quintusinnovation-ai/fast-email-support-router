from pathlib import Path

import pytest

from support_router.backends.mock import MockDecisionBackend
from support_router.backends.jev import JevDecisionBackend
from support_router.config import Settings, load_company_config
from support_router.factory import create_backend


FIXTURES = Path(__file__).parent / "fixtures" / "mock_decisions.json"


def test_factory_builds_mock_backend():
    settings = Settings(
        backend="mock",
        api_token="12345",
        fixture_file=FIXTURES,
    )
    assert isinstance(create_backend(settings), MockDecisionBackend)


def test_factory_builds_live_jev_backend():
    settings = Settings(
        backend="jev",
        api_token="live",
        fixture_file=FIXTURES,
        typesafe_api_key="secret",
    )
    backend = create_backend(settings, load_company_config(Path(__file__).parents[1] / "config" / "teams.json"))
    assert isinstance(backend, JevDecisionBackend)
