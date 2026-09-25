"""Backend construction."""

from support_router.backends.base import DecisionBackend
from support_router.backends.jev import JevDecisionBackend
from support_router.backends.mock import MockDecisionBackend
from support_router.config import CompanyConfig, Settings


def create_backend(settings: Settings, config: CompanyConfig | None = None) -> DecisionBackend:
    if settings.backend == "mock":
        return MockDecisionBackend(settings.fixture_file, settings.api_token)
    if config is None:
        raise ValueError("Company configuration is required for the JEV backend")
    if settings.typesafe_api_key is None:
        raise ValueError("TYPESAFE_API_KEY is required for the JEV backend")
    return JevDecisionBackend(
        config,
        settings.typesafe_api_key,
        settings.typesafe_default_model,
        base_url=settings.typesafe_base_url,
    )
