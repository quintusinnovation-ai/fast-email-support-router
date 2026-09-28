import asyncio
from pathlib import Path

import httpx

from support_router.api import app


ROOT = Path(__file__).parents[1]


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def configure_mock(monkeypatch):
    monkeypatch.setenv("SUPPORT_ROUTER_BACKEND", "mock")
    monkeypatch.setenv("SUPPORT_ROUTER_API_TOKEN", "12345")
    monkeypatch.setenv("SUPPORT_ROUTER_CONFIG_FILE", str(ROOT / "config" / "teams.json"))
    monkeypatch.setenv(
        "SUPPORT_ROUTER_FIXTURE_FILE",
        str(ROOT / "tests" / "fixtures" / "mock_decisions.json"),
    )


def email_payload():
    return {
        "message_id": "api-message-1",
        "sender": "customer@example.com",
        "subject": "Charged twice for our subscription",
        "body_text": "We were charged twice.",
    }


def test_health_is_public_and_reports_ok():
    response = request("GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_requires_bearer_token(monkeypatch):
    configure_mock(monkeypatch)
    response = request("POST", "/v1/route", json=email_payload())
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_route_rejects_wrong_bearer_token(monkeypatch):
    configure_mock(monkeypatch)
    response = request(
        "POST",
        "/v1/route",
        headers={"Authorization": "Bearer wrong"},
        json=email_payload(),
    )
    assert response.status_code == 401


def test_route_returns_complete_decision(monkeypatch):
    configure_mock(monkeypatch)
    response = request(
        "POST",
        "/v1/route",
        headers={"Authorization": "Bearer 12345"},
        json=email_payload(),
    )
    assert response.status_code == 200
    result = response.json()
    assert result["message_id"] == "api-message-1"
    assert result["action"] == "automatic_route"
    assert result["destination"]["team_id"] == "billing"
    assert result["provider"] == "mock"


def test_route_rejects_unknown_or_missing_email_fields(monkeypatch):
    configure_mock(monkeypatch)
    headers = {"Authorization": "Bearer 12345"}
    unknown = request(
        "POST",
        "/v1/route",
        headers=headers,
        json=email_payload() | {"teams": {}},
    )
    missing_payload = email_payload()
    del missing_payload["body_text"]
    missing = request("POST", "/v1/route", headers=headers, json=missing_payload)
    assert unknown.status_code == 422
    assert missing.status_code == 422


def test_openapi_documents_bearer_auth_and_response_contract():
    schema = app.openapi()
    operation = schema["paths"]["/v1/route"]["post"]
    assert operation["security"] == [{"HTTPBearer": []}]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
