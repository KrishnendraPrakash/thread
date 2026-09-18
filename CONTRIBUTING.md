# Contributing

Start with [AGENTS.md](AGENTS.md) and [engineering standards](steering/engineering.md). The current contribution target is the local M1 workflow; optional provider and UI folders are reservations.

1. Use Python 3.11+ and the [development setup](docs/development.md).
2. Keep changes focused and describe the behavior they establish.
3. Update the relevant specification, examples, and steering when behavior or scope changes.
4. Add outcome-oriented tests when implementing real behavior. Never report an empty test suite or scaffold smoke check as runtime validation.
5. Keep fixtures synthetic, isolate external integrations, and exclude credentials, private traces, and model weights.

The repository license and public hosting location are still open decisions. See [release readiness](docs/releasing.md) before publication.
