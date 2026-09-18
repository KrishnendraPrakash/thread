# Contributing

Start with [AGENTS.md](AGENTS.md) and [engineering standards](steering/engineering.md). The current contribution target is the local M1 workflow; optional provider and UI folders are reservations.

1. Use Python 3.11+ and the [development setup](docs/development.md).
2. Keep changes focused and describe the behavior they establish.
3. Update the relevant specification, examples, and steering when behavior or scope changes.
4. Add outcome-oriented tests when implementing real behavior. Never report an empty test suite or scaffold smoke check as runtime validation.
5. Keep fixtures synthetic, isolate external integrations, and exclude credentials, private traces, and model weights.

The source repository is hosted at [KrishnendraPrakash/thread](https://github.com/KrishnendraPrakash/thread). The repository license remains an open decision. See [release readiness](docs/releasing.md) before a package or agent release, and the [workflow guide](docs/workflows.md) for the planned runtime paths.
