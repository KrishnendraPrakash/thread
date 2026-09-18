# Development setup

The scaffold selects Python 3.11+ for modern typing and standard-library TOML support, setuptools for packaging, Ruff for lint/format checks, and standard-library unittest for automated tests. No runtime third-party library is required yet. These are initial repository conventions, not hardware certification.

Install from the checkout using the [root README](../README.md). Package metadata is in [pyproject.toml](../pyproject.toml). Optional development tools install via `.[dev]`; there are no cloud-provider extras until those adapters exist.

For the recorded development dependency versions, use `uv sync --locked --extra dev` with [uv.lock](../uv.lock). This lock records the project/development dependencies, not a model artifact or the separately resolved build backend. The scaffold was checked locally with Python 3.12.13 and uv 0.10.9; Python 3.11 is declared and included in future CI but has not been exercised locally.

## Current checks

Run from an environment with the development extra installed:

```sh
python -m ruff check .
python -m ruff format --check .
python -m compileall -q src
python -m unittest discover -s tests -v
thread-agent --help
thread-agent --version
thread-agent status --json
```

These cover style, syntax, CLI integration, source boundaries, decisions, provider validation, replay, and ten deterministic reference cases. No model server is required: provider responses in tests are synthetic. A run discovering zero tests is not a pass. They do not establish full M1 acceptance or model quality.

The package also supports `python -m thread_agent`. A source checkout can use `PYTHONPATH=src` on macOS/Linux for this command before installation.

## Implementation sequence

The [first experimental workflow](first-workflow.md) implements a narrow direct-field path. Expand initial fixtures and freeze the hardware/model profile (M0), then complete typed records, capability checks, budgets, the general loop, and all persistent HIL scenarios (M1). Introduce concrete APIs and migrations as their behavior is implemented; package placeholders do not freeze interfaces.

Keep test fixtures outside the agent's allowed workspace unless explicitly copied there for the scenario. Reference answers and graders must remain outside the workspace visible to the agent under test.
