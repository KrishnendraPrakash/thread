# Architecture-to-folder map

Only the CLI currently contains application behavior. All other source packages are docstring placeholders reserving responsibility; they are not implemented services or finalized APIs.

| Package under src/thread_agent | Intended responsibility |
| --- | --- |
| cli | Implemented scaffold help, version, and status |
| config | Reserved for typed configuration loading and validation; not implemented. |
| domain | Reserved for shared Contract, Evidence, Claim, Check, and Decision records. |
| contracts | Reserved for task scope, completeness criteria, and justified contract revisions. |
| context | Reserved for role budgets and selection of history, evidence, memory, and skills. |
| runtime | Reserved for the agent loop, task tiers, budgets, cancellation, and recovery. |
| providers | Reserved for provider interfaces and capability checks; no connections exist yet. |
| providers/ollama | Reserved for the first local adapter and model capability checks. |
| providers/hosted | Optional M4B hosted free-tier and paid adapters; no SDK dependencies yet. |
| providers/private | Optional M4B private endpoint adapter; endpoint and auth policy remain required. |
| tools | Reserved for typed tool registration and dispatch after runtime policy checks. |
| tools/filesystem | Reserved for scoped file listing, reading, searching, and later approved edits. |
| tools/calculation | Reserved for bounded deterministic calculations; never execute arbitrary model text. |
| policy | Reserved for authority, workspace boundaries, network rules, and action preconditions. |
| evidence | Reserved for immutable source snapshots, hashes, locators, and evidence records. |
| verification | Reserved for support, applicability, coverage, and post-render fidelity checks. |
| rendering | Reserved for checked-claim templates and answer assembly before final fidelity checks. |
| decisions | Reserved for persistent human choices, interpretations, and exact-action approvals. |
| sessions | Reserved for conversation history and resumable task/execution state. |
| memory | Reserved for attributed durable facts and dependency-aware bounded caches. |
| skills | Reserved for versioned reusable procedures; skills cannot grant permissions. |
| observability | Reserved for sequenced events, model-call metadata, counters, and trace storage. |
| replay | Reserved for step and strict trajectory replay; replay must never execute live effects. |
| storage | Reserved for persistence interfaces; keep storage separate from runtime policy. |
| storage/sqlite | Reserved for SQLite repositories and transactional state updates. |
| evaluation | Reserved for evaluation runners and independent graders, not production self-grading. |
| interfaces | Reserved for optional gateways that share the runtime and decision service. |
| interfaces/web | Optional future dashboard/API gateway; no server or UI is implemented. |
| integrations | Reserved for optional integrations; none are imported or enabled by default. |
| integrations/messaging | Optional future authenticated messaging gateway and HIL responses. |
| integrations/scheduling | Optional future persisted scheduling with policy and idempotency. |
| integrations/delegation | Optional future bounded specialist tasks; no autonomous delegation exists. |

Supporting locations are described in [README.md](../README.md). Root design documents and planning_examples have been kept in place to preserve existing links.

## Boundaries

- CLI/gateways call runtime interfaces; they do not implement policy or provider-specific logic.
- Domain records are shared; provider adapters normalize external protocols.
- Policy controls tools. Decisions supply scoped human responses, not bypasses.
- Evidence and verification remain separate from answer rendering.
- Sessions/execution state, durable memory, and trace storage have separate responsibilities, even when stored in the same SQLite database.
- Evaluation and replay must not depend on live side effects or model self-grading.
- Optional adapters/gateways/integrations remain unused until their capability is implemented.

This folder map does not imply that every responsibility needs a separate model call or service.
