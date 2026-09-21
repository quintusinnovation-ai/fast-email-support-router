"""Deterministic provider-neutral routing policy."""

from support_router.config import CompanyConfig
from support_router.domain import (
    BackendDecision,
    DecisionResult,
    Destination,
    RoutingAction,
    RoutingProfile,
    Signals,
    Usage,
)


TEAM_CHOICE_CONFIDENCE_THRESHOLD = 0.85
TEAM_SUITABILITY_THRESHOLD = 0.80


def apply_policy(decision: BackendDecision, config: CompanyConfig) -> DecisionResult:
    routing = decision.routing
    team = config.teams.get(routing.winning_team or "")
    automatic = (
        team is not None
        and routing.confidence >= TEAM_CHOICE_CONFIDENCE_THRESHOLD
        and routing.has_suitable_team_probability >= TEAM_SUITABILITY_THRESHOLD
    )
    if automatic and team is not None:
        action = RoutingAction.AUTOMATIC_ROUTE
        destination = Destination(team.team_id, team.name, team.email)
        final_routing = routing
    else:
        action = RoutingAction.HUMAN_REVIEW
        destination = Destination(None, "Human Router", config.human_review_email)
        final_routing = RoutingProfile(
            winning_team=None,
            confidence=routing.confidence,
            has_suitable_team_probability=routing.has_suitable_team_probability,
            candidates=routing.candidates,
        )
    return DecisionResult(
        message_id=decision.message_id,
        action=action,
        destination=destination,
        routing=final_routing,
        signals=decision.signals,
        provider=decision.provider,
        model=decision.model,
        usage=decision.usage,
    )


def human_review_result(message_id: str, config: CompanyConfig) -> DecisionResult:
    """Return the deterministic fail-closed result for an exhausted backend error."""
    return DecisionResult(
        message_id=message_id,
        action=RoutingAction.HUMAN_REVIEW,
        destination=Destination(None, "Human Router", config.human_review_email),
        routing=RoutingProfile(None, 0.0, 0.0, ()),
        signals=Signals(
            urgency="low",
            language="other_or_unknown",
            topic="other",
            sentiment="neutral",
            refund_intent_probability=0.0,
            churn_risk="low",
        ),
        provider="unavailable",
        model="unavailable",
        usage=Usage(0, 0),
    )
