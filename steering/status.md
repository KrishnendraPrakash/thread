# Current project status

As of: 2026-09-18. Recheck the workspace before relying on this snapshot.

## Active phase

**Initial implementation: architecture-aligned repository scaffold, with public onboarding documentation.** The scaffold is complete. The user subsequently requested Git publication and a clearer public README with workflow diagrams. The source repository has been pushed; agent runtime behavior, model installation/benchmarking, and package/release publication have not been performed.

Continue within the next user-authorized scope. A structure request does not require building all future capabilities, and the former planning-only status must not block implementation that the user now requests.

## What exists

- [README.md](../README.md), [pyproject.toml](../pyproject.toml), and [uv.lock](../uv.lock): package setup and initial development dependency resolution.
- [src/thread_agent](../src/thread_agent): Python source tree. CLI help, version, and implementation status work; other component packages are documented placeholders.
- [Component map](../docs/structure.md): responsibilities and optional extension locations.
- [Public quick start](../README.md) and [workflow guide](../docs/workflows.md): clone/install instructions, working CLI examples, troubleshooting, roadmap, and separate diagrams of the major planned workflows. Planned behavior is explicitly distinguished from the current scaffold.
- Draft configuration and prompt files, schema locations, synthetic sample projects, test/evaluation directories, developer/release docs, and scaffold-only GitHub CI/templates.
- [AGENT_PLAN.md](../AGENT_PLAN.md), [SPEC.md](../SPEC.md), [RATIONALE.md](../RATIONALE.md), and [AGENT_ARCHITECTURE.mmd](../AGENT_ARCHITECTURE.mmd): design and roadmap.
- [EXAMPLE_TRACE.json](../EXAMPLE_TRACE.json) and [planning_examples](../planning_examples/README.md): synthetic teaching traces, not runtime outputs or a frozen schema.
- [AGENTS.md](../AGENTS.md) and this steering directory: persistent development context.

Python minimum is now 3.11. Packaging uses setuptools; the current core has no third-party runtime dependencies. Ruff is an optional development extra; future behavior tests use unittest. pip and optional uv setup are documented.

## Actual validation

On local Python 3.12.13:

- Installed the editable scaffold and development tooling into an ignored local .venv.
- Ruff lint and formatting, Python syntax compilation, TOML/JSON parsing, and document-link checks passed.
- Built a wheel and source distribution.
- Installed the wheel into a separate temporary environment without network/runtime dependencies; console and module entry points worked.
- Verified that the unsupported run command is rejected and the smoke commands do not create agent data.
- Checked wheel contents for accidental test/evaluation/configuration fixture inclusion.

CI configuration targets Python 3.11 and 3.12 on Linux; hosted CI results have not been verified in this documentation task and cross-platform support is not yet certified. No behavior tests exist; no M0/M1 acceptance gate or live model evaluation has passed. Mermaid source exists; rendered-diagram validation and fresh-session steering discovery remain unverified.

Previous planning work checked synthetic trace hashes, references, status transitions, ordering, and scripted budgets. Those checks are not runtime/model measurements.

The public documentation update checked local links and heading anchors, matched the README's expected output to the working CLI, and exercised help/version/status plus the source-only invocation. Mermaid 11 parsed all 12 embedded diagrams and the existing full architecture source. Parser tooling was installed only in a temporary directory; no project dependency changed. GitHub visual rendering and the Windows setup commands remain unverified.

## Remaining implementation

The agent loop, adapters, tools/policy, HIL persistence, memory, source snapshots, rendering/verification, replay, and independent graders are not implemented. Configuration examples and prompt drafts are not loaded by the scaffold CLI. Optional provider/gateway/integration folders do not enable services.

Git is initialized on main with origin at https://github.com/KrishnendraPrakash/thread.git. The user reported a successful push, and local main and origin/main matched the corrected initial commit when this documentation task began. No package publication, model download, or license selection has occurred. Source publication does not satisfy the M6 release gate.

## Open decisions before freezing M0

1. The user's three real priority tasks and their acceptance outcomes.
2. Minimum supported hardware/OS and a baseline model-test configuration.
3. Exact model artifact/quantization and compatibility checks; model names remain candidates.
4. Final latency/cost limits, action policy, and data retention.
5. Public repository license and initial optional provider coverage.

## Next boundary

Define M0 acceptance fixtures and scope, then implement the narrow local M1 workflow with a complete human-decision cycle. Packaging success does not establish agent-task success. Keep optional integrations staged, and preserve the reviewed trace/HIL invariants from SPEC.md.
