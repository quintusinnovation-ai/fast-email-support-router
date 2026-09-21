"""JEV question construction from the lightweight team configuration."""

from typing import Any

from support_router.config import CompanyConfig


def build_questions(config: CompanyConfig) -> dict[str, dict[str, Any]]:
    team_context = config.jev_choice_criteria
    return {
        "winning_team": {
            "type": "choice",
            "instructions": "Which configured team should handle this support email?",
            "criteria": team_context,
        },
        "has_suitable_team": {
            "type": "noul",
            "instructions": {
                "question": "Does exactly one configured team clearly own this support email?",
                "teams": team_context,
            },
            "criteria": {
                "true": "One team clearly owns the request under its stated scope.",
                "false": "No team clearly owns it, or ownership is ambiguous.",
            },
        },
        "urgency": _score("How urgent is the request?", ["low", "medium", "high", "critical"]),
        "language": {
            "type": "choice",
            "instructions": "What language is the email written in?",
            "criteria": {"en": "English", "de": "German", "other_or_unknown": "Any other language or unclear"},
        },
        "topic": {
            "type": "choice",
            "instructions": "What is the primary topic?",
            "criteria": {"billing": "Billing or payment", "technical_issue": "Technical issue", "account_and_retention": "Account adoption, renewal or cancellation", "other": "Anything else"},
        },
        "sentiment": _score("How negative is the customer's sentiment?", ["neutral", "concerned", "frustrated"]),
        "refund_intent": {"type": "noul", "instructions": "Is the customer asking for or expecting a refund?"},
        "churn_risk": _score("How strong is the churn risk?", ["low", "medium", "high"]),
    }


def _score(instructions: str, levels: list[str]) -> dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": levels}
