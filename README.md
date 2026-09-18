# Thread Agent

A local-first personal agent project with evidence-based answers and explicit human decisions.

**Current state: architecture-aligned scaffold.** Package installation and CLI help/version/status are available. The agent loop, model connections, policy enforcement, HIL persistence, memory, and verification runtime are not implemented. No model accuracy or performance has been measured.

`thread-agent` is a working distribution/command name, not a published package or a checked registry-name reservation. A public repository URL and repository license have not yet been selected.

## Try the scaffold

From this directory, with Python 3.11 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
thread-agent --help
thread-agent --version
thread-agent status
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of `source`. Alternatively run the commands using the environment's Python executable directly. Installation may download the build backend and optional development tooling; the scaffold has no third-party runtime dependencies and needs no model or API account.

For a dependency-free source smoke check on macOS/Linux:

```sh
PYTHONPATH=src python3 -m thread_agent status --json
```

There is no `run` or chat command yet. Configuration examples and prompts are drafts and are not consumed by the CLI.

If you use uv, `uv sync --locked --extra dev` installs the versions recorded in uv.lock; then use `uv run --locked thread-agent status`. The pip instructions above resolve dependencies within pyproject.toml's ranges instead of using that lock.

## Project layout

```text
src/thread_agent/    Python package, CLI, and reserved architecture modules
configs/            Local, hosted, and private-endpoint draft configuration
prompts/            Versioned role-prompt drafts, not yet wired to models
schemas/            Record/trace schema design locations
tests/              Unit, integration, and acceptance test locations
evals/              Cases, isolated fixtures, graders, and ignored reports
examples/           Synthetic projects and future skill examples
docs/               Setup, component map, contribution/release guidance
.github/            Scaffold CI and contribution templates
steering/           Persistent project direction and engineering guidance
planning_examples/  Existing synthetic trace illustrations and negative cases
```

See the [component map](docs/structure.md) for detailed ownership and optional extension points. Modules containing only a docstring are reserved boundaries, not implemented features.

## Design and development

- [Plan](AGENT_PLAN.md), [specification](SPEC.md), [rationale](RATIONALE.md), and [Mermaid diagram](AGENT_ARCHITECTURE.mmd).
- [Agent instructions](AGENTS.md) and [current status](steering/status.md).
- [Development setup](docs/development.md), [contributing](CONTRIBUTING.md), and [release readiness](docs/releasing.md).
- [Configuration examples](configs/README.md), [optional integrations](docs/optional-integrations.md), and [evaluation layout](evals/README.md).

Future users will choose local inference without a paid API, or explicitly configure a hosted/private provider. Those capabilities remain staged according to SPEC.md; cloning the scaffold does not provide a running agent.
