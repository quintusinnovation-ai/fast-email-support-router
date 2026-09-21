"""Provider-neutral domain types and JEV response normalization."""

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
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class BackendDecision:
    """Normalized answer returned by either the mock or a live JEV adapter."""

    message_id: str
    routing: RoutingProfile
    signals: Signals
    provider: str
    model: str
    usage: Usage

    @classmethod
    def from_jev_response(
        cls, message_id: str, payload: dict[str, Any], *, provider: str
    ) -> "BackendDecision":
        answers = payload["answers"]
        winning_team = _choice(answers, "winning_team")
        candidates = tuple(
            Candidate(team_id=team_id, probability=float(probability))
            for team_id, probability in winning_team["probabilities"].items()
        )
        usage = payload.get("usage", {})
        return cls(
            message_id=message_id,
            routing=RoutingProfile(
                winning_team=str(winning_team["choice"]),
                confidence=float(winning_team["confidence"]),
                has_suitable_team_probability=float(
                    _noul(answers, "has_suitable_team")["noul"]
                ),
                candidates=candidates,
            ),
            signals=Signals(
                urgency=_score_label(answers, "urgency"),
                language=str(_choice(answers, "language")["choice"]),
                topic=str(_choice(answers, "topic")["choice"]),
                sentiment=_score_label(answers, "sentiment"),
                refund_intent_probability=float(
                    _noul(answers, "refund_intent")["noul"]
                ),
                churn_risk=_score_label(answers, "churn_risk"),
            ),
            provider=provider,
            model=str(payload["model"]),
            usage=Usage(
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
            ),
        )


@dataclass(frozen=True)
class Destination:
    team_id: str | None
    team_name: str
    email: str


@dataclass(frozen=True)
class DecisionResult:
    message_id: str
    action: RoutingAction
    destination: Destination
    routing: RoutingProfile
    signals: Signals
    provider: str
    model: str
    usage: Usage


def _choice(answers: dict[str, Any], key: str) -> dict[str, Any]:
    answer = answers[key]
    if answer.get("type") != "choice":
        raise ValueError(f"{key} must be a choice answer")
    probabilities = answer["probabilities"]
    choice = answer["choice"]
    if choice not in probabilities:
        raise ValueError(f"{key} choice is absent from probabilities")
    _validate_probabilities(probabilities)
    _validate_unit_interval(answer["confidence"], f"{key}.confidence")
    return answer


def _noul(answers: dict[str, Any], key: str) -> dict[str, Any]:
    answer = answers[key]
    if answer.get("type") != "noul":
        raise ValueError(f"{key} must be a noul answer")
    _validate_unit_interval(answer["noul"], f"{key}.noul")
    return answer


def _score_label(answers: dict[str, Any], key: str) -> str:
    answer = answers[key]
    if answer.get("type") != "score":
        raise ValueError(f"{key} must be a score answer")
    probabilities = answer["probabilities"]
    legend = answer["legend"]
    _validate_probabilities(probabilities)
    _validate_unit_interval(answer["confidence"], f"{key}.confidence")
    winning_level = max(probabilities, key=probabilities.get)
    return str(legend[winning_level])


def _validate_probabilities(probabilities: dict[str, Any]) -> None:
    if not probabilities:
        raise ValueError("probabilities must not be empty")
    for key, value in probabilities.items():
        _validate_unit_interval(value, f"probabilities.{key}")
    if abs(sum(float(value) for value in probabilities.values()) - 1.0) > 0.001:
        raise ValueError("probabilities must sum to 1")


def _validate_unit_interval(value: Any, field_name: str) -> None:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
