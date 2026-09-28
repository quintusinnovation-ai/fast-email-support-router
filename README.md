# Fast Email Support Router

Fast Email Support Router classifies incoming support emails and returns the right service-team destination through a small authenticated HTTP API. It is built independently of any agent harness and can be used by agents, applications, and automations through standard HTTP or OpenAPI clients.

The included agent skill completes the workflow: it sends a selected email to the routing service and forwards the unchanged original to the returned destination.

## What it does

- Selects the best team from company-defined routing criteria
- Returns an automatic route only when confidence and team suitability meet the routing policy
- Sends uncertain decisions and provider failures to a human-review destination
- Provides routing probabilities and signals for urgency, language, topic, sentiment, refund intent, and churn risk
- Authenticates routing requests with a bearer token
- Publishes an OpenAPI contract and interactive API documentation
- Keeps team destinations and routing descriptions in a simple JSON configuration

## How it works

```text
Email agent or application
        |
        | POST /v1/route
        v
Fast Email Support Router
        |
        | structured decision request
        v
TypeSafe JEV
        |
        v
Automatic team destination or human review
```

The service evaluates the email against the configured support teams. It routes a decision automatically when the winning team reaches both policy thresholds:

- team confidence: `0.85`
- suitable-team probability: `0.80`

All other decisions use the configured human-review destination.

## HTTP API

- `POST /v1/route` — route one support email
- `GET /health` — service health
- `GET /openapi.json` — machine-readable API contract
- `GET /docs` — interactive API documentation

### Request

```bash
curl --fail-with-body \
  -H "Authorization: Bearer $SUPPORT_ROUTER_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "provider-message-123",
    "sender": "customer@example.com",
    "subject": "Charged twice for our subscription",
    "body_text": "We have two identical charges for September.",
    "received_at": "2026-09-28T17:33:16Z"
  }' \
  http://127.0.0.1:8080/v1/route
```

### Response

```json
{
  "message_id": "provider-message-123",
  "action": "automatic_route",
  "destination": {
    "team_id": "billing",
    "team_name": "Billing Support",
    "email": "billing@example.com"
  },
  "routing": {
    "winning_team": "billing",
    "confidence": 0.96,
    "has_suitable_team_probability": 0.99,
    "candidates": [
      {
        "team_id": "billing",
        "probability": 0.96
      }
    ]
  },
  "signals": {
    "urgency": "medium",
    "language": "English",
    "topic": "billing",
    "sentiment": "negative",
    "refund_intent_probability": 0.88,
    "churn_risk": "medium"
  },
  "provider": "jev",
  "model": "jev-latest",
  "usage": {
    "input_tokens": 184,
    "output_tokens": 62
  }
}
```

## Agent skill

The skill in [`skill/route-support-emails/`](skill/route-support-emails/) gives an HTTP-capable agent a reusable workflow:

1. Take an already selected support email.
2. Call `POST /v1/route` with the original message fields.
3. Read the returned destination.
4. Forward the original email unchanged to that destination.
5. Stop and report the failure when no valid destination is returned.

The skill can be installed in any agent harness that supports instruction-based skills and authenticated HTTP requests.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/quintusinnovation-ai/fast-email-support-router.git
cd fast-email-support-router
python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

## Configuration

Create a private environment file at `~/.config/support-router/secrets.env`:

```bash
SUPPORT_ROUTER_BACKEND=jev
SUPPORT_ROUTER_API_TOKEN=<router-api-token>
SUPPORT_ROUTER_CONFIG_FILE=/absolute/path/to/teams.json
TYPESAFE_API_KEY=<typesafe-api-key>
TYPESAFE_DEFAULT_MODEL=jev-latest
```

`SUPPORT_ROUTER_ENV_FILE` selects another environment file. Process environment variables take precedence. `TYPESAFE_BASE_URL` can override the default TypeSafe System One endpoint.

Define the available teams and the human-review destination in the configured JSON file:

```json
{
  "human_review_email": "support-triage@example.com",
  "teams": {
    "billing": {
      "name": "Billing Support",
      "email": "billing@example.com",
      "handles": "Invoices, payments, subscription charges, and refunds"
    }
  }
}
```

## Run the service

```bash
support-router-api
```

The default address is `http://127.0.0.1:8080`. Set `SUPPORT_ROUTER_HOST` and `SUPPORT_ROUTER_PORT` to change it.

### Run with systemd

```bash
install -D -m 644 \
  deploy/systemd/fast-email-support-router.service \
  ~/.config/systemd/user/fast-email-support-router.service
systemctl --user daemon-reload
systemctl --user enable --now fast-email-support-router.service
```

## Command-line use

The CLI reads one email as JSON from standard input and writes the routing result as JSON:

```bash
printf '%s\n' '{
  "message_id": "provider-message-123",
  "sender": "customer@example.com",
  "subject": "Charged twice for our subscription",
  "body_text": "We have two identical charges for September."
}' | support-router
```

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Mock backend

The deterministic mock backend supports local development and automated tests:

```bash
export SUPPORT_ROUTER_BACKEND=mock
export SUPPORT_ROUTER_API_TOKEN=12345
export SUPPORT_ROUTER_CONFIG_FILE=config/teams.json
export SUPPORT_ROUTER_FIXTURE_FILE=tests/fixtures/mock_decisions.json
```

Mock decisions use the same request, response, normalization, and routing-policy path as live decisions.

## License

MIT
