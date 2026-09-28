"""Agent-agnostic HTTP API for the Support Router."""

from __future__ import annotations

import hmac
import os
from typing import Annotated, Literal

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from support_router.cli import route_payload
from support_router.config import Settings


class EmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1)
    sender: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    body_text: str = Field(min_length=1)
    received_at: str | None = Field(default=None, min_length=1)


class CandidateOutput(BaseModel):
    team_id: str
    probability: float = Field(ge=0.0, le=1.0)


class RoutingOutput(BaseModel):
    winning_team: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    has_suitable_team_probability: float = Field(ge=0.0, le=1.0)
    candidates: list[CandidateOutput]


class DestinationOutput(BaseModel):
    team_id: str | None
    team_name: str
    email: str


class SignalsOutput(BaseModel):
    urgency: str
    language: str
    topic: str
    sentiment: str
    refund_intent_probability: float = Field(ge=0.0, le=1.0)
    churn_risk: str


class UsageOutput(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class RoutingDecisionOutput(BaseModel):
    message_id: str
    action: Literal["automatic_route", "human_review"]
    destination: DestinationOutput
    routing: RoutingOutput
    signals: SignalsOutput
    provider: str
    model: str
    usage: UsageOutput


class HealthOutput(BaseModel):
    status: Literal["ok"] = "ok"


bearer = HTTPBearer(auto_error=False)


def authenticated_settings(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Settings:
    try:
        settings = Settings.from_env()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Router configuration is unavailable",
        ) from exc
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not hmac.compare_digest(credentials.credentials, settings.api_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return settings


app = FastAPI(
    title="Fast Email Support Router",
    description="Route support emails through a provider-neutral decision API.",
    version="0.2.0",
)


@app.get("/health", response_model=HealthOutput, tags=["operations"])
def health() -> HealthOutput:
    return HealthOutput()


@app.post(
    "/v1/route",
    response_model=RoutingDecisionOutput,
    tags=["routing"],
)
def route_email_http(
    email: EmailInput,
    settings: Annotated[Settings, Depends(authenticated_settings)],
) -> dict[str, object]:
    try:
        return route_payload(email.model_dump(exclude_none=True), settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Routing service is unavailable",
        ) from exc


def run() -> None:
    uvicorn.run(
        "support_router.api:app",
        host=os.environ.get("SUPPORT_ROUTER_HOST", "127.0.0.1"),
        port=int(os.environ.get("SUPPORT_ROUTER_PORT", "8080")),
    )
