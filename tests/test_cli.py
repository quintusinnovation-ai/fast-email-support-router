import io
import json
from pathlib import Path

from support_router.cli import route_payload, run
from support_router.config import Settings


ROOT = Path(__file__).parents[1]


def settings() -> Settings:
    return Settings(
        backend="mock",
        api_token="12345",
        config_file=ROOT / "config" / "teams.json",
        fixture_file=ROOT / "tests" / "fixtures" / "mock_decisions.json",
    )


def payload() -> dict[str, str]:
    return {
        "message_id": "provider-message-123",
        "sender": "customer@example.com",
        "subject": "Charged twice for our subscription",
        "body_text": "We were charged twice.",
    }


def test_route_payload_returns_complete_decision_result():
    result = route_payload(payload(), settings())
    assert result["message_id"] == "provider-message-123"
    assert result["action"] == "automatic_route"
    assert result["destination"]["team_id"] == "billing"
    assert result["provider"] == "mock"
    assert result["usage"] == {"input_tokens": 0, "output_tokens": 0}


def test_route_payload_rejects_configuration_fields():
    request = payload() | {"teams": {}}
    try:
        route_payload(request, settings())
    except ValueError as exc:
        assert str(exc) == "Unknown input fields: teams"
    else:
        raise AssertionError("configuration field was accepted")


def test_run_reads_one_json_object_and_writes_one_json_result(monkeypatch):
    monkeypatch.setenv("SUPPORT_ROUTER_API_TOKEN", "12345")
    monkeypatch.setenv("SUPPORT_ROUTER_CONFIG_FILE", str(ROOT / "config" / "teams.json"))
    monkeypatch.setenv(
        "SUPPORT_ROUTER_FIXTURE_FILE",
        str(ROOT / "tests" / "fixtures" / "mock_decisions.json"),
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = run(io.StringIO(json.dumps(payload())), stdout, stderr)
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert json.loads(stdout.getvalue())["destination"]["team_id"] == "billing"


def test_run_reports_invalid_json_only_on_stderr():
    stdout = io.StringIO()
    stderr = io.StringIO()
    assert run(io.StringIO("{"), stdout, stderr) == 2
    assert stdout.getvalue() == ""
    assert stderr.getvalue()
