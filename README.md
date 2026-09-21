# Support Router

A provider-neutral Python core for routing incoming support emails to service teams or human review.

The first implementation uses a deterministic mock backend. It accepts the same email fields as a future live decision provider, authenticates every invocation, and selects fixture outcomes by email subject. This makes local development and CI reproducible, offline, and free of model usage costs.

## Local mock

```bash
export SUPPORT_ROUTER_BACKEND=mock
export SUPPORT_ROUTER_API_TOKEN=12345
export SUPPORT_ROUTER_CONFIG_FILE=config/teams.json
export SUPPORT_ROUTER_FIXTURE_FILE=tests/fixtures/mock_decisions.json
```

`config/teams.json` is the only company routing configuration. Each team needs only a stable key, name, destination email, and one concise `handles` description. Those keys and descriptions map directly to JEV Choice criteria.

The mock matches normalized email subjects against deterministic fixtures shaped exactly like JEV responses: Choice, Noul, and Score answers with probabilities, confidence, legends, model, and usage. The same normalization and policy used by a future live adapter turns that answer into `automatic_route` or `human_review`. The ordinary email input never contains a fixture ID, expected result, or other mock-only parameter.

```python
from support_router.config import Settings
from support_router.config import load_company_config
from support_router.domain import EmailRequest
from support_router.factory import create_backend
from support_router.router import route_email

settings = Settings.from_env()
backend = create_backend(settings)
company = load_company_config(settings.config_file)
result = route_email(
    backend,
    company,
    EmailRequest(
        message_id="gmail-message-123",
        sender="customer@example.com",
        subject="Charged twice for our subscription",
        body_text="We have two identical charges for September.",
    ),
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
