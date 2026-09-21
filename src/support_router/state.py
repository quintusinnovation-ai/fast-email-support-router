"""JEV state construction."""

from typing import Any

from support_router.domain import EmailRequest


def build_state(request: EmailRequest) -> dict[str, Any]:
    state: dict[str, Any] = {
        "email": {
            "message_id": request.message_id,
            "from": request.sender,
            "subject": request.subject,
            "body_text": request.body_text,
        }
    }
    if request.received_at is not None:
        state["email"]["received_at"] = request.received_at
    return state
