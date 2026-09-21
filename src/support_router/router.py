"""Routing orchestration."""

from support_router.backends.base import BackendError, DecisionBackend
from support_router.config import CompanyConfig
from support_router.domain import DecisionResult, EmailRequest
from support_router.policy import apply_policy, human_review_result


def route_email(
    backend: DecisionBackend, config: CompanyConfig, request: EmailRequest
) -> DecisionResult:
    try:
        decision = backend.evaluate(request)
    except BackendError:
        return human_review_result(request.message_id, config)
    return apply_policy(decision, config)
