import io
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from support_router.backends.base import BackendError
from support_router.backends.jev import JevDecisionBackend
from support_router.config import load_company_config
from support_router.domain import EmailRequest


ROOT = Path(__file__).parents[1]
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "mock_decisions.json").read_text()
)["subjects"]["Charged twice for our subscription"]


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(FIXTURE).encode()


def backend(**kwargs):
    return JevDecisionBackend(
        load_company_config(ROOT / "config" / "teams.json"),
        "secret",
        max_attempts=1,
        **kwargs,
    )


def test_jev_backend_posts_shared_state_and_atomic_questions(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("support_router.backends.jev.urlopen", fake_urlopen)
    result = backend().evaluate(
        EmailRequest("msg-1", "a@example.com", "Charged twice", "Please refund me")
    )
    payload = json.loads(captured["request"].data)
    assert payload["state"]["email"]["message_id"] == "msg-1"
    assert set(payload["questions"]) == {
        "winning_team", "has_suitable_team", "urgency", "language",
        "topic", "sentiment", "refund_intent", "churn_risk",
    }
    assert captured["request"].get_header("Authorization") == "Bearer secret"
    assert result.provider == "jev"
    assert result.routing.winning_team == "billing"


def test_jev_backend_converts_provider_error_to_backend_error(monkeypatch):
    def fail(*_args, **_kwargs):
        raise HTTPError("url", 401, "unauthorized", {}, io.BytesIO())

    monkeypatch.setattr("support_router.backends.jev.urlopen", fail)
    with pytest.raises(BackendError):
        backend().evaluate(EmailRequest("msg-1", "a@example.com", "Subject", "Body"))
