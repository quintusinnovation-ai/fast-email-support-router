"""Decision backend protocol."""

from typing import Protocol

from support_router.domain import BackendDecision, EmailRequest


class BackendError(RuntimeError):
    """Raised when a decision provider cannot return a valid answer."""


class DecisionBackend(Protocol):
    def evaluate(self, request: EmailRequest) -> BackendDecision:
        """Evaluate one ordinary email request."""
        ...
