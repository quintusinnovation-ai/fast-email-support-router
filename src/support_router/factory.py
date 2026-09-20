"""Backend construction."""

from support_router.backends.base import DecisionBackend
from support_router.backends.mock import MockDecisionBackend
from support_router.config import Settings


def create_backend(settings: Settings) -> DecisionBackend:
    if settings.backend == "mock":
        return MockDecisionBackend(settings.fixture_file, settings.api_token)
    raise NotImplementedError("JevDecisionBackend is intentionally deferred")
