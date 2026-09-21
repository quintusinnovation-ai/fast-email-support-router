import json
from pathlib import Path

import pytest

from support_router.backends.mock import MockDecisionBackend, normalize_subject
from support_router.config import AuthenticationError, load_company_config
from support_router.domain import EmailRequest, RoutingAction
from support_router.router import route_email


FIXTURES = Path(__file__).parent / "fixtures" / "mock_decisions.json"
CONFIG = Path(__file__).parents[1] / "config" / "teams.json"


def email(subject: str, message_id: str = "msg-1") -> EmailRequest:
    return EmailRequest(message_id, "customer@example.com", subject, "Synthetic test message.")


@pytest.mark.parametrize(
    ("subject", "action", "team_id"),
    [
        ("Charged twice for our subscription", RoutingAction.AUTOMATIC_ROUTE, "billing"),
        ("Production API returning 500 errors", RoutingAction.AUTOMATIC_ROUTE, "technical_support"),
        ("We are considering cancellation", RoutingAction.AUTOMATIC_ROUTE, "customer_success"),
        ("University research partnership", RoutingAction.HUMAN_REVIEW, None),
    ],
)
def test_subject_selects_expected_route(subject, action, team_id):
    backend = MockDecisionBackend(FIXTURES, "12345")
    result = route_email(backend, load_company_config(CONFIG), email(subject))
    assert result.action is action
    assert result.destination.team_id == team_id


def test_mock_normalizes_real_jev_answer_shapes():
    decision = MockDecisionBackend(FIXTURES, "12345").evaluate(
        email("Charged twice for our subscription")
    )
    assert decision.routing.winning_team == "billing"
    assert decision.routing.has_suitable_team_probability == 0.99
    assert decision.signals.urgency == "medium"
    assert decision.signals.refund_intent_probability == 0.92
    assert decision.model == "mock-jev-1.13.0"
    assert decision.usage.input_tokens == 0


def test_fixture_payload_uses_jev_response_contract():
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))["subjects"]
    required_answers = {
        "winning_team", "has_suitable_team", "urgency", "language", "topic",
        "sentiment", "refund_intent", "churn_risk",
    }
    for response in payload.values():
        assert set(response) == {"model", "answers", "usage"}
        assert set(response["answers"]) == required_answers
        assert response["answers"]["winning_team"]["type"] == "choice"
        assert response["answers"]["has_suitable_team"]["type"] == "noul"
        assert response["answers"]["urgency"]["type"] == "score"


def test_subject_matching_is_case_and_whitespace_insensitive():
    backend = MockDecisionBackend(FIXTURES, "12345")
    decision = backend.evaluate(email("  CHARGED   TWICE for OUR subscription "))
    assert decision.routing.winning_team == "billing"
    assert normalize_subject(" A  B ") == "a b"


def test_unknown_subject_falls_back_to_human_review():
    backend = MockDecisionBackend(FIXTURES, "12345")
    result = route_email(backend, load_company_config(CONFIG), email("Something entirely new"))
    assert result.action is RoutingAction.HUMAN_REVIEW
    assert result.routing.winning_team is None


def test_backend_rejects_wrong_token():
    with pytest.raises(AuthenticationError):
        MockDecisionBackend(FIXTURES, "wrong")


def test_email_request_contains_no_mock_selector():
    assert set(EmailRequest.__dataclass_fields__) == {
        "message_id", "sender", "subject", "body_text", "received_at"
    }
