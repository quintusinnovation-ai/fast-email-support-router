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

## Live JEV backend

The live adapter sends the same state and atomic questions to the TypeSafe System One API. The router owns and reloads its private configuration on every invocation from `~/.config/support-router/secrets.env`; it does not depend on a parent process or OpenClaw for secrets:

```bash
SUPPORT_ROUTER_BACKEND=jev
SUPPORT_ROUTER_API_TOKEN=<private-tool-token>
SUPPORT_ROUTER_CONFIG_FILE=/absolute/path/to/teams.json
TYPESAFE_API_KEY=<typesafe-key>
TYPESAFE_DEFAULT_MODEL=jev-latest
```

Process environment variables override values from that file. `SUPPORT_ROUTER_ENV_FILE` can select a different file, and `TYPESAFE_BASE_URL` can override the default `https://api.typesafe.ai/v1/systemone` endpoint. Provider failures are retried within a bounded window and then resolve to `human_review`; credentials and email bodies are never logged by the core.

## JSON command line interface

The installed command reads one email as JSON from standard input and writes one routing result as JSON to standard output:

```bash
printf '%s\n' '{"message_id":"gmail-message-123","sender":"customer@example.com","subject":"Charged twice for our subscription","body_text":"We have two identical charges for September."}' \
  | support-router
```

Set `SUPPORT_ROUTER_CONFIG_FILE` to the instance-specific team configuration. Keep that file outside the repository when it contains real destination addresses.

## OpenClaw tool and skill

The plugin exposes `support_router_route_email`. It accepts `message_id`, `sender`, `subject`, `body_text`, and optional `received_at`; configuration is loaded internally by the installed core.

```bash
cd openclaw-plugin
npm ci
npm run build
openclaw plugins install --link "$PWD"
```

Configure the plugin with the absolute path to the installed `support-router` executable, then restart the OpenClaw gateway. The plugin only transports the email JSON; backend settings and credentials belong to the router's private environment file. The complete companion skill is versioned in `skill/route-support-emails/`.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## License

MIT
