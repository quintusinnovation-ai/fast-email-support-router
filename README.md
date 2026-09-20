# Support Router

A provider-neutral Python core for routing incoming support emails to service teams or human review.

The first implementation uses a deterministic mock backend. It accepts the same email fields as a future live decision provider, authenticates every invocation, and selects fixture outcomes by email subject. This makes local development and CI reproducible, offline, and free of model usage costs.

## Status

Initial project scaffold. The mock decision backend is added in the next commit.

## License

MIT

