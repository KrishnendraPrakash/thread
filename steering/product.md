# Project direction

Updated: 2026-09-24. Basis: the user's planning instructions, subsequent scaffold and first local workflow authorization, and the current [plan](../AGENT_PLAN.md).

## Established direction

Build a public, reusable personal AI agent that completes useful tasks, makes important conclusions checkable, and gives the human meaningful choices. The main access path runs locally without a paid LLM API account. Optional hosted free tiers, paid APIs using the user's keys, and private on-premises endpoints use the same runtime.

The first application is one user per installation, with a Python core, VS Code developer interface, a separate field CLI with SQLite persistence, and scoped local tools. Keep the design understandable and portable; publish support claims only for configurations actually tested. A public repository does not imply a hosted multi-tenant service.

Accuracy includes answering the intended question, using applicable evidence, preserving scope, covering the requested result, and checking actual action outcomes. Do not promise perfect accuracy or equate a passing schema/citation check with truth.

Human-in-the-loop is part of the first version. Present a recommendation with a reason, relevant alternatives, More options where useful, explicit custom input, and pause/cancel; optional questions can allow skip. Recommendations, silence, and ambiguous replies do not authorize actions. Existing valid authorization should not cause repetitive prompts.

## Proposed choices that remain unproven

- Local Ollama is the first adapter target. Qwen3.5-9B and Qwen3.5-4B are model candidates, not benchmarked defaults. Exact artifacts, licenses/notices, quantizations, hardware, and runtime compatibility must be checked before release.
- The user selected repository understanding, debugging assistance, writing features and document summaries as the immediate VS Code workflows. Bounded experimental implementations exist; full semantic verification and autonomous debugger operation do not. Durable memory remains planned.
- SPEC.md's latency, context, tool, and accuracy numbers are proposed gates or starting limits. They are not measured results or guarantees about a user's machine.
- Hosted provider/model selection, minimum hardware/OS, repository license, retention settings, and final cost/latency budgets remain open.

## Delivery boundaries

M1 uses one local provider and a complete human-decision cycle. Hosted/private adapters arrive at M4B. Dashboard, scheduling, messaging, and delegation follow demonstrated need. Do not introduce a paid verifier, remote embeddings, or paid search as a hidden requirement of the local core.

Local inference and offline operation are distinct: offline rules must cover every model role, tool, and data destination. Product runtime permissions are enforced in code and cannot be granted by retrieved text, skills, or an LLM's own assessment.

The user has explicitly requested public installation through a published VS Code extension. Deliver a clearly labeled preview while full release gates remain incomplete; public packaging must use the owner-selected license and a confirmed Marketplace identity. A public code repository or CI artifact alone is not a Marketplace release.
