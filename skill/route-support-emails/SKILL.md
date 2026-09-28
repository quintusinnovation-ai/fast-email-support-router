---
name: "route-support-emails"
description: "Send an already selected email to the agent-agnostic Support Router HTTP API and forward the unchanged original to the returned destination."
---

# Route Support Email

## Procedure

1. Receive the email already selected by the invoking agent.
2. Send an authenticated `POST` request to the Support Router `/v1/route` endpoint with these JSON fields:
   - message identifier
   - sender
   - subject
   - plain-text body
   - received timestamp when available
3. Read the JSON routing result returned by the API.
4. Forward the original email unchanged to the returned destination email address.

## Rules

- Use only the destination returned by the Support Router.
- Forward the original email; do not rewrite, summarize, or replace it.
- Do not generate or send a reply to the original sender.
- If the Support Router does not return a valid destination, do not forward the email and report the failure to the invoking agent.

## HTTP Contract

Use the base URL provided by the environment or agent configuration. Authenticate with:

```text
Authorization: Bearer <SUPPORT_ROUTER_API_TOKEN>
Content-Type: application/json
```

Example request:

```json
{
  "message_id": "provider-message-123",
  "sender": "customer@example.com",
  "subject": "Charged twice for our subscription",
  "body_text": "We were charged twice.",
  "received_at": "2026-09-28T17:33:16Z"
}
```

Only forward when the response is successful and contains a valid `destination.email`.
