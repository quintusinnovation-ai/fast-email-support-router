"""JSON command-line boundary for the Support Router core."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import json
import sys
from typing import Any, TextIO

from support_router.config import Settings, load_company_config
from support_router.domain import EmailRequest
from support_router.factory import create_backend
from support_router.router import route_email


INPUT_FIELDS = {"message_id", "sender", "subject", "body_text", "received_at"}
REQUIRED_INPUT_FIELDS = {"message_id", "sender", "subject", "body_text"}


def route_payload(payload: Any, settings: Settings) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object")
    unknown = set(payload) - INPUT_FIELDS
    missing = REQUIRED_INPUT_FIELDS - set(payload)
    if unknown:
        raise ValueError(f"Unknown input fields: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"Missing input fields: {', '.join(sorted(missing))}")
    request = EmailRequest(
        message_id=payload["message_id"],
        sender=payload["sender"],
        subject=payload["subject"],
        body_text=payload["body_text"],
        received_at=payload.get("received_at"),
    )
    config = load_company_config(settings.config_file)
    backend = create_backend(settings)
    return _json_value(route_email(backend, config, request))


def run(
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    try:
        payload = json.load(stdin)
        result = route_payload(payload, Settings.from_env())
    except Exception as exc:
        print(str(exc), file=stderr)
        return 2
    json.dump(result, stdout, separators=(",", ":"), ensure_ascii=False)
    stdout.write("\n")
    return 0


def main() -> None:
    raise SystemExit(run())


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value
