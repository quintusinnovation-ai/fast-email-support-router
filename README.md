# Support Router

A provider-neutral Python core for routing incoming support emails to service teams or human review.

The first implementation uses a deterministic mock backend. It accepts the same email fields as a future live decision provider, authenticates every invocation, and selects fixture outcomes by email subject. This makes local development and CI reproducible, offline, and free of model usage costs.

## Local mock

```bash
export SUPPORT_ROUTER_BACKEND=mock
export SUPPORT_ROUTER_API_TOKEN=12345
export SUPPORT_ROUTER_FIXTURE_FILE=tests/fixtures/mock_decisions.json
```

The mock matches normalized email subjects against deterministic fixtures. Unknown subjects return `human_review`. The ordinary email input never contains a fixture ID, expected result, or other mock-only parameter.

```python
from support_router.config import Settings
from support_router.domain import EmailRequest
from support_router.factory import create_backend

backend = create_backend(Settings.from_env())
result = backend.evaluate(
    EmailRequest(
        message_id="gmail-message-123",
        sender="customer@example.com",
        subject="Charged twice for our subscription",
        body_text="We have two identical charges for September.",
    )
)
```

The live JEV backend is intentionally deferred. Selecting `SUPPORT_ROUTER_BACKEND=jev` fails explicitly rather than silently substituting the mock.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## License

MIT
