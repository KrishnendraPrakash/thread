# Engineering and review standards

Updated: 2026-09-22. The experimental field CLI and VS Code developer slice are implemented; other architecture modules remain reserved boundaries. Detailed product invariants are in [SPEC.md](../SPEC.md).

## Code organization and patterns

- Prefer a small Python application with explicit module boundaries. Keep provider SDK details in adapters and UI presentation outside the agent loop. Avoid separate services or orchestration frameworks unless a measured need justifies them.
- Use typed records at module boundaries for Contract, Evidence, Claim, Check, and Decision. Prefer clear functions and explicit dependencies; avoid hidden mutable global state and unnecessary abstraction layers.
- Keep business decisions and transformations testable independently of the terminal, model server, filesystem, and clock. Use deterministic code for policy, parsing, calculation, hashing, state reduction, and validated templates where appropriate.
- Separate immutable records from state projections. Define serialization, canonical hashes, schema versions, and migrations deliberately when persistence is implemented. Include provenance instead of reconstructing it from prose later.
- Use explicit error categories and bounded retries. Preserve meaningful errors; do not catch exceptions broadly and silently turn them into success. Reconcile uncertain side effects before retrying them.
- Prefer standard-library facilities when adequate and keep new dependencies purposeful. The field CLI and build tools use Python 3.11+; the bundled editor import path must also run on Python 3.9+ (avoid importing tomllib there). The project uses setuptools, pip-compatible packaging, optional uv with uv.lock, Ruff lint/format, and unittest for behavior tests. Follow pyproject.toml and docs/development.md. Behavior and deterministic development-fixture tests exist. They are not the full M1/model benchmark suite.
- Keep secrets in environment variables or local secret storage. Public fixtures and examples use synthetic data and portable paths. The local core and its tests must not require a paid provider.

## Architecture invariants to preserve

- T0 still needs supplied-input fidelity; T1 is direct scoped reporting; T2 handles investigation, inference, and actions. Tier reduction needs an explicit superseding contract and justified rule or human scope change. Every action still passes policy.
- Build factual claims from evidence before prose. Valid JSON, a real citation, or a self-checking model's agreement does not establish semantic support. Preserve supported, contradicted, and insufficient outcomes.
- Track exact source bytes/hashes and distinguish source integrity, factual support, freshness, and independent corroboration. A field-specific citation locator is a checkable output detail.
- Record completed checks, then claim-status transitions. Render from checked inputs, inspect that actual render, then deliver the same output. Never use a render as its own expected reference.
- Persist human decisions, raw custom replies, validated interpretations, and concrete approval scope. Ambiguous replies remain pending; stale/duplicate approvals cannot execute changed actions.
- In v1, durable memory contains attributed facts/preferences/decisions, not automatically promoted inferences. Cache reuse validates all known dependencies; discovery/absence results need a complete versioned scope or no cross-run cache.
- Name deterministic, human, tool, model, and synthetic producers. Capture real model inputs, raw outputs, options, and available usage without fabricating missing metadata. Mark incomplete replay explicitly.
- Strict replay never executes live effects and stops on divergent requests. Step replay does not establish end-to-end correctness; changed action plans need fresh isolated fixture runs.

## Validation and review

- Scale checks to the change. For Markdown, check relevant links and consistency; for trace edits, also check hashes, references, ordering, state transitions, and budget accounting. Preserve deliberately negative examples as negative.
- Once runtime code exists, test behavior and outcomes rather than mirroring implementation. Prioritize boundary cases: missing/conflicting evidence, malformed/truncated results, ambiguous HIL, stale approval, duplicate action, changed source, and replay mismatch.
- Keep production self-checks separate from release grading. Use deterministic reference outcomes and human labels; optional model graders need independent calibration. Report results per model/runtime/quantization and include workload, sample count, and limitations.
- Do not label a synthetic fixture or documentation consistency check as a model benchmark or runtime test. Do not claim checks ran when they were only specified.
- Review supplied feedback against the files and user intent. Fix established defects, retain useful counterexamples, and qualify unsupported numerical claims. Update SPEC.md first for requirements, RATIONALE.md for decisions, and diagrams/examples when their behavior changes.

## Collaboration

Use detailed commit messages for this project, as requested by the user. Include a concise subject and a body explaining the problem, changes, validation performed, and material limitations. Apply this to every commit prepared for a push; the preference does not itself authorize unrelated changes or publication.

Explain the concrete change and why it matters. Keep the user informed during longer work. Respect existing authorization and reserve questions for material missing information. Preserve unrelated work; avoid unnecessary rewrites or formatting churn. End with the result, actual validation, and unresolved limits.
