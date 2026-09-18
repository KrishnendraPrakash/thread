# Agent plan

Status: an experimental exact-field workflow is implemented; the full agent runtime, model benchmarks, and public release remain pending.
Updated: 2026-09-18 after the user's request for the next usable step beyond scaffold status.

## Goal

Build a public, reusable personal agent that runs primarily with a local model without paid API credentials, produces evidence-based answers, and supports persistent human choices and approvals. Optional hosted free tiers, paid APIs, and on-premises models use the same runtime.

Initial scope is one user per installation, Python, a terminal interface, SQLite, and scoped local files. First tasks: answer project questions, remember/correct explicit project decisions, and perform approved bounded edits with observable outcome checks. The actual three user-priority tasks still need to be finalized.

## Five records explain the design

| Record | Question it answers | Example |
| --- | --- | --- |
| Contract | What exactly must be answered or done? | Identify the checked-in database default |
| Evidence | What was actually supplied or inspected? | A versioned settings.toml field |
| Claim | What can we assert from that evidence? | The file's default is sqlite |
| Check | What establishes support and task completion? | Parse the field, check scope, preserve it in the answer |
| Decision | Where does the human choose or authorize? | Choose file configuration, runtime behavior, or write a custom scope |

These are data records, not mandatory separate model calls or services. A short request may use deterministic routing and templated output. Important factual paths build evidence-bound claims before prose. Uncertainty, permission, and completion remain separate concerns.

## Choose the amount of work

| Tier | Example | Path |
| --- | --- | --- |
| T0: supplied-input transformation | Reformat a list or compute explicit arithmetic | Transform/compute and check fidelity/values |
| T1: direct local lookup | Report an exact configuration field | Retrieve, bind evidence, parse/check scope, render |
| T2: investigation or action | Resolve contradictory docs or edit a file | Applicable semantic checks, targeted investigation, policy, and HIL |

A supplied document is evidence. An existing citation is not proof of interpretation. Complex summaries, unsupported inferences, or changing state promote to stronger checks. All actions pass runtime policy regardless of task tier.

## Human control stays in the first version

The terminal will show why input is needed, a recommended choice with a rationale, relevant alternatives, More options when available, explicit free text, and pause/cancel. Optional questions can allow skip. Keep this a flat interaction rather than a complex nested UI.

Pending decisions survive restarts. Recommendations and silence never submit approvals. Approvals bind to a concrete proposal and its current state; custom changes require revalidation. Existing scoped authorization is preserved.

## Model and deployment direction

One local Ollama adapter is the M1 implementation target. Qwen3.5-9B and Qwen3.5-4B remain candidates to evaluate at pinned quantizations and context sizes; neither is a certified default. Current official model-card links and operational sources are in [RATIONALE.md](RATIONALE.md).

Small-model defaults include schema-constrained records, narrow tool lists, bounded role contexts, focused three-way semantic checks, one resident model, and sequential inference. These settings are tunable through measurements.

Hosted free/paid APIs and private endpoints remain planned at M4B. A free hosted tier is optional, not a prerequisite or permanent cost guarantee. Local/offline policy covers verification, embeddings, search, and telemetry; there is no silent paid or external fallback.

## Milestones

The package scaffold and a narrow source-field workflow now exist: scoped TOML/JSON reads, optional local Ollama field suggestions, saved human field choices, deterministic verification, and stored-source replay. See the [first workflow guide](docs/first-workflow.md). Ten deterministic development fixtures and boundary tests have been added. This is a pre-M1 increment, not full M1 acceptance. See [README.md](README.md) and the [component map](docs/structure.md). M0 decisions and M1 acceptance gates are not complete; packaging success is not agent-task success.

| Milestone | Deliverable | Primary gate |
| --- | --- | --- |
| M0 | Fixtures, schemas, task routing, baseline hardware profile | Freeze reference outcomes and provisional budgets |
| M1 | Local vertical slice, terminal HIL, scoped reads, sessions, traces, basic replay | 27/30 correct local trials; 13 HIL scenarios including ambiguous custom text; proposed warm T1 p50 <=20 s and p95 <=45 s on the specified short workload/profile |
| M2 | Claims before prose, focused checks, annotated claim evaluation | Claim recall and final-answer fidelity gates |
| M3 | Tier promotion, conflicting evidence, bounded repair, error handling | No policy bypass through routing; reliable failure and replay-divergence behavior |
| M4 | Attributed memory, source-keyed cache, skills, approved edits | Correction/deletion, invalidation, approvals, and recovery checks |
| M4B | Hosted and private provider adapters | Capability and acceptance results per model/runtime profile |
| M5 | External research | Source applicability, freshness, synthesis, and coverage |
| M6 | Public release | Reproducible local setup, documented license/compatibility, held-out results and limitations |

Numerical targets are proposed acceptance criteria, not measured speed or reliability. SPEC.md defines the workload, trial counts, hardware-freeze rule, and complete gates. The initial 60-case suite is diagnostic; it must expand as features are added.

## What changed after review

- Explicit tiers replace a single assumed full workflow.
- Evidence-bound claims precede prose; final text still needs coverage checks.
- Replay supports model/prompt comparisons without rerunning live tools, and stops on unmatched actions.
- Runtime self-checks are separate from independent release grading.
- V1 durable memory excludes automatically inferred conclusions; cache reuse validates source versions.
- Role/tool/output limits, error categories, and prompt-injection controls are explicit.
- Human options remain; elaborate UI and all nonlocal providers are deferred.
- Timing, tool-count, and determinism assertions from the feedback are treated as hypotheses or defaults to test, not established facts.
- Trace review now also requires byte hashes, explicit producers/status transitions, interpreted custom replies, authorized tier reductions, and render-before-fidelity ordering. A citation's precise locator is checked data too.

## Documents

- [AGENTS.md](AGENTS.md) and [steering guide](steering/README.md): persistent project context, engineering standards, and current phase for future development sessions.
- [SPEC.md](SPEC.md): normative requirements, glossary, resource budgets, HIL, errors, replay, and evaluation gates.
- [RATIONALE.md](RATIONALE.md): item-by-item disposition of the feedback, design reasons, and sources.
- [AGENT_ARCHITECTURE.mmd](AGENT_ARCHITECTURE.mmd): tiered workflow, model routing, human decisions, and checks.
- [EXAMPLE_TRACE.json](EXAMPLE_TRACE.json): revised deterministic teaching trace with interpreted custom input, authorized tier reduction, hashed evidence, explicit claim status, and post-render fidelity. It is not a model execution log.
- [Planning example guide](planning_examples/README.md): negative locator, conflicting evidence, changed action/stale approval, strict replay mismatch, and model-call record examples. All are synthetic planning artifacts.

## Open planning decisions

Finalize the three real tasks, minimum supported hardware/OS, acceptable latency/cost, action policy and data retention, repository license, and the first optional hosted integration. Benchmark candidate models before choosing defaults when that work is requested. The scaffold source is on GitHub; broader agent behavior and a package/agent release remain pending. The [public README](README.md) and [workflow guide](docs/workflows.md) explain current usage and the planned paths.
