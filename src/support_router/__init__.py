"""Provider-neutral support email routing."""

from support_router.domain import DecisionResult, EmailRequest, RoutingAction
from support_router.factory import create_backend

__all__ = ["DecisionResult", "EmailRequest", "RoutingAction", "create_backend"]
