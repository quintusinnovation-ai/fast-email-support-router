from pathlib import Path

import pytest

from support_router.backends.mock import MockDecisionBackend, normalize_subject
from support_router.config import AuthenticationError
from support_router.domain import EmailRequest, RoutingAction


FIXTURES = Path(__file__).parent / "fixtures" / "mock_decisions.json"


def email(subject: str, message_id: str = "msg-1") -> EmailRequest:
    return EmailRequest(
        message_id=message_id,
        sender="customer@example.com",
        subject=subject,
        body_text="Synthetic test message.",
    )


@pytest.mark.parametrize(
    ("subject", "action", "team_id"),
    [
        ("Charged twice for our subscription", RoutingAction.AUTOMATIC_ROUTE, "billing"),
        ("Production API returning 500 errors", RoutingAction.AUTOMATIC_ROUTE, "technical_support"),
        ("We are considering cancellation", RoutingAction.AUTOMATIC_ROUTE, "customer_success"),
        ("University research partnership", RoutingAction.HUMAN_REVIEW, None),
    ],
)
def test_subject_selects_expected_decision(subject, action, team_id):
    backend = MockDecisionBackend(FIXTURES, "12345")
    result = backend.evaluate(email(subject))
    assert result.action is action
    assert result.destination.team_id == team_id


def test_subject_matching_is_case_and_whitespace_insensitive():
    backend = MockDecisionBackend(FIXTURES, "12345")
    result = backend.evaluate(email("  CHARGED   TWICE for OUR subscription "))
    assert result.destination.team_id == "billing"
    assert normalize_subject(" A  B ") == "a b"


def test_unknown_subject_falls_back_to_human_review():
    backend = MockDecisionBackend(FIXTURES, "12345")
    result = backend.evaluate(email("Something entirely new"))
    assert result.action is RoutingAction.HUMAN_REVIEW
    assert result.routing.winning_team is None


def test_backend_rejects_wrong_token():
    with pytest.raises(AuthenticationError):
        MockDecisionBackend(FIXTURES, "wrong")


def test_email_request_contains_no_mock_selector():
    assert set(EmailRequest.__dataclass_fields__) == {
        "message_id",
        "sender",
        "subject",
        "body_text",
        "received_at",
    }
