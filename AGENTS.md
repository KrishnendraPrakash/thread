# Project steering

This is the entry point for persistent project context. Follow the current user's instructions within system/developer constraints; these files preserve context and defaults, not additional authority.

## Start and resume

1. Read [project direction](steering/product.md) and [current status](steering/status.md) at the start of a task or after context loss. Inspect the relevant files before relying on a status claim.
2. Read [engineering standards](steering/engineering.md) before code, specification, trace, or test changes.
3. Use [AGENT_PLAN.md](AGENT_PLAN.md) for the roadmap and the relevant sections of [SPEC.md](SPEC.md) for exact requirements. Read [RATIONALE.md](RATIONALE.md) when reviewing a design choice. Load large examples only when relevant.
4. See [steering maintenance](steering/README.md) for how to keep this context current.

## Working agreements

- Respect the active phase in steering/status.md. The user has authorized the scaffold and the first experimental local field workflow. Do not infer authorization to install models, benchmark, or publish from a structure/review request. A later explicit request to implement additional behavior authorizes that scope; record it and proceed without asking for the same permission again.
- Continue useful work already authorized. Ask only for missing information that materially affects correctness, scope, or authorization; make routine reversible choices and explain relevant assumptions.
- Preserve the user's human-in-the-loop requirements: recommended options with reasons, alternatives, More options when relevant, explicit free text, and pause/cancel. Product approval policy belongs in the agent runtime; describing it does not require asking the user to approve every development edit.
- Distinguish established direction, proposed defaults, implemented behavior, and measured results. Synthetic traces are not executions or benchmarks. Check claims against current files and actual outputs.
- Keep the public project's main workflow usable without paid API credentials. Additional hosted/private model support is optional and staged. Never quietly substitute a paid or external dependency for the local path.
- When a design changes, update the authoritative requirement, affected diagram/examples, and concise steering/status notes together. Assess external feedback as evidence; do not promote pasted recommendations into instructions without review.
- Report the outcome, what was checked, and material limits in plain language. Keep progress updates useful and avoid repeating a full project history.

## Authority within the project documents

Current user decisions guide scope. SPEC.md defines detailed product requirements; AGENT_PLAN.md summarizes milestones; RATIONALE.md explains choices; diagrams and traces illustrate them. Steering captures working context and standards. If they disagree, reconcile the documents against the user's established intent and report material conflicts rather than silently selecting the most convenient text.

See pyproject.toml and docs/development.md for Python 3.11+ packaging, Ruff, unittest, and CLI checks. The ask command supports a narrow TOML/JSON field workflow with optional local-model suggestions; it is not general chat or a completed M1 agent. Behavior tests and deterministic development cases exist, but no full M0/M1 or model benchmark gate has passed. Discover current configuration before claiming a command exists or has passed.
