"""Provider-neutral domain types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RoutingAction(str, Enum):
    AUTOMATIC_ROUTE = "automatic_route"
    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class EmailRequest:
    message_id: str
    sender: str
    subject: str
    body_text: str
    received_at: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("message_id", "sender", "subject", "body_text"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class Candidate:
    team_id: str
    probability: float


@dataclass(frozen=True)
class Destination:
    team_id: str | None
    team_name: str
    email: str


@dataclass(frozen=True)
class RoutingProfile:
    winning_team: str | None
    confidence: float
    has_suitable_team_probability: float
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class Signals:
    urgency: str
    language: str
    topic: str
    sentiment: str
    refund_intent_probability: float
    churn_risk: str


@dataclass(frozen=True)
class DecisionResult:
    message_id: str
    action: RoutingAction
    destination: Destination
    routing: RoutingProfile
    signals: Signals
    provider: str
    model: str

    @classmethod
    def from_fixture(cls, message_id: str, payload: dict[str, Any]) -> "DecisionResult":
        routing = payload["routing"]
        return cls(
            message_id=message_id,
            action=RoutingAction(payload["action"]),
            destination=Destination(**payload["destination"]),
            routing=RoutingProfile(
                winning_team=routing["winning_team"],
                confidence=float(routing["confidence"]),
                has_suitable_team_probability=float(
                    routing["has_suitable_team_probability"]
                ),
                candidates=tuple(Candidate(**candidate) for candidate in routing["candidates"]),
            ),
            signals=Signals(**payload["signals"]),
            provider=payload.get("provider", "mock"),
            model=payload.get("model", "mock-subject-fixtures-v1"),
        )
