---
name: "route-support-emails"
description: "Send an already selected email to the Support Router tool and forward the unchanged original to the returned destination."
---

# Route Support Email

## Procedure

1. Receive the email already selected by the invoking agent.
2. Send these fields to the `support_router_route_email` tool:
   - message identifier
   - sender
   - subject
   - plain-text body
   - received timestamp when available
3. Read the routing result returned by the tool.
4. Forward the original email unchanged to the returned destination email address.

## Rules

- Use only the destination returned by the Support Router.
- Forward the original email; do not rewrite, summarize, or replace it.
- Do not generate or send a reply to the original sender.
- If the Support Router does not return a valid destination, do not forward the email and report the failure to the invoking agent.
