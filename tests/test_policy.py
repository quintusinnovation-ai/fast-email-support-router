from dataclasses import replace
from pathlib import Path

from support_router.backends.base import BackendError
from support_router.backends.mock import MockDecisionBackend
from support_router.config import load_company_config
from support_router.domain import EmailRequest, RoutingAction
from support_router.policy import apply_policy
from support_router.router import route_email


FIXTURES = Path(__file__).parent / "fixtures" / "mock_decisions.json"
CONFIG = Path(__file__).parents[1] / "config" / "teams.json"


def decision():
    return MockDecisionBackend(FIXTURES, "12345").evaluate(
        EmailRequest("msg", "customer@example.com", "Charged twice for our subscription", "Body")
    )


def test_choice_confidence_below_threshold_routes_to_human_review():
    original = decision()
    changed = replace(original, routing=replace(original.routing, confidence=0.849))
    result = apply_policy(changed, load_company_config(CONFIG))
    assert result.action is RoutingAction.HUMAN_REVIEW


def test_suitability_below_threshold_routes_to_human_review():
    original = decision()
    changed = replace(
        original,
        routing=replace(original.routing, has_suitable_team_probability=0.799),
    )
    result = apply_policy(changed, load_company_config(CONFIG))
    assert result.action is RoutingAction.HUMAN_REVIEW


def test_unknown_team_routes_to_human_review():
    original = decision()
    changed = replace(original, routing=replace(original.routing, winning_team="sales"))
    result = apply_policy(changed, load_company_config(CONFIG))
    assert result.action is RoutingAction.HUMAN_REVIEW
    assert result.destination.email == "support-router@acme.example"


def test_threshold_boundaries_allow_automatic_route():
    original = decision()
    changed = replace(
        original,
        routing=replace(
            original.routing,
            confidence=0.85,
            has_suitable_team_probability=0.80,
        ),
    )
    assert apply_policy(changed, load_company_config(CONFIG)).action is RoutingAction.AUTOMATIC_ROUTE


def test_backend_error_fails_closed_to_human_review():
    class FailingBackend:
        def evaluate(self, request):
            raise BackendError("provider failed")

    request = EmailRequest("failed-msg", "customer@example.com", "Subject", "Body")
    result = route_email(FailingBackend(), load_company_config(CONFIG), request)
    assert result.action is RoutingAction.HUMAN_REVIEW
    assert result.message_id == "failed-msg"
    assert result.destination.email == "support-router@acme.example"
