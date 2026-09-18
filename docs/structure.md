# Architecture-to-folder map

The experimental [direct-field workflow](first-workflow.md) implements the components identified below. Other packages remain reserved boundaries. The full architecture is not implemented, and these first APIs are not frozen.

| Package under src/thread_agent | Intended responsibility |
| --- | --- |
| cli | Help/status, exact field reports, doctor, saved choices, traces, and replay |
| config | Reserved for typed configuration loading and validation; not implemented. |
| domain | Evidence dataclass, hashes, canonical JSON, timestamps, and errors; full shared record schemas remain pending. |
| contracts | Reserved for task scope, completeness criteria, and justified contract revisions. |
| context | Reserved for role budgets and selection of history, evidence, memory, and skills. |
| runtime | runtime/lookup.py implements the restricted T1 lifecycle, field decisions, check/render ordering, and deterministic replay. General routing/loop/budgets remain pending. |
| providers | Local field-suggestion adapter exists; a generalized provider interface remains pending. |
| providers/ollama | Loopback HTTP inventory, model metadata, constrained field suggestions, and validated outputs. Full capability gates remain pending. |
| providers/hosted | Optional M4B hosted free-tier and paid adapters; no SDK dependencies yet. |
| providers/private | Optional M4B private endpoint adapter; endpoint and auth policy remain required. |
| tools | Reserved for typed tool registration and dispatch after runtime policy checks. |
| tools/filesystem | Descriptor-based bounded reads of explicitly selected TOML/JSON files. Listing, search, and edits remain pending. |
| tools/calculation | Reserved for bounded deterministic calculations; never execute arbitrary model text. |
| policy | Reserved for authority, workspace boundaries, network rules, and action preconditions. |
| evidence | Scalar field extraction with exact JSON pointers; snapshots are retained in the session store. |
| verification | General verification package reserved; exact field and output-slot checks currently live in runtime/lookup.py. |
| rendering | General renderer reserved; the direct-field JSON renderer currently lives in runtime/lookup.py. |
| decisions | General decision service reserved; persisted field choices live in runtime/lookup.py. No action approvals. |
| sessions | Reserved for conversation history and resumable task/execution state. |
| memory | Reserved for attributed durable facts and dependency-aware bounded caches. |
| skills | Reserved for versioned reusable procedures; skills cannot grant permissions. |
| observability | Reserved for sequenced events, model-call metadata, counters, and trace storage. |
| replay | General step/trajectory replay reserved; stored-source report replay is implemented in runtime/lookup.py. |
| storage | Reserved for persistence interfaces; keep storage separate from runtime policy. |
| storage/sqlite | SQLite sessions and ordered events, with revision checks and atomic updates. |
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
- Captured evidence and post-render slot checks remain distinct from rendering; the narrow workflow currently coordinates them in one runtime module.
- Sessions/execution state, durable memory, and trace storage have separate responsibilities, even when stored in the same SQLite database.
- Evaluation and replay must not depend on live side effects or model self-grading.
- Optional adapters/gateways/integrations remain unused until their capability is implemented.

This folder map does not imply that every responsibility needs a separate model call or service.
