"""Decision backend protocol."""

from typing import Protocol

from support_router.domain import DecisionResult, EmailRequest


class DecisionBackend(Protocol):
    def evaluate(self, request: EmailRequest) -> DecisionResult:
        """Evaluate one ordinary email request."""
        ...
