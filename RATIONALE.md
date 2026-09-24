# Design rationale and review disposition

Status: planning review, 2026-09-14. Requirements live in SPEC.md; this file records why they were chosen. No performance claims below are project measurements.

## Review conclusion

The feedback correctly identifies execution details missing from the original plan. The strongest changes are explicit task routing, evidence-bound claims before prose, trace replay, measured claim coverage, concrete resource limits, and a smaller durable-memory design. These make the primary local-model path more concrete.

Several suggestions need qualification: a source span's existence does not establish its interpretation; supplied text is still evidence; fixed seeds do not universally guarantee reproducibility; and changing a model used for grading does not establish grader quality. Human-in-the-loop options remain part of the user's requested first version.

## Disposition of the supplied feedback

| Feedback | Decision | Reason |
| --- | --- | --- |
| Every request takes 5–7 calls and tens of seconds | Accept the latency concern, not the numerical claim | Architecture boxes are not necessarily calls. No local timings were supplied or measured. Add budgets, routing, and benchmarks. |
| T0/T1/T2 routing | Adopt with eligibility and promotion rules | Avoid full semantic verification for simple tasks without allowing routing to bypass policy. |
| T0 needs no evidence, including summaries | Correct | Summaries must preserve supplied evidence; arithmetic depends on correct inputs/units. Difficult transformations may need stronger checks. |
| T1 span existence replaces a critic | Narrow | Safe for exact source reports or parsed fields with scope preserved, not arbitrary paraphrase, synthesis, runtime assertions, or inference. |
| Generate evidence-bound claims before prose | Adopt | Reduces reliance on retrospective extraction, but the renderer can still add or omit facts. Keep final prose coverage checks and annotated claim evaluations. |
| Verification becomes largely deterministic | Qualify | Syntax, source identity, parsed fields, calculations, and observed outcomes can be deterministic. Semantic support still needs assessment. |
| Constrained decoding mandatory for all adapters | Adopt for initial local structured profile; allow tested equivalents | Server-side constraints improve shape. They do not establish truth or justify rejecting every other native structured interface. Unsupported profiles are disabled. |
| Binary semantic verification | Change to supported/contradicted/insufficient | A forced yes/no hides missing evidence. Use focused checks without removing needed multi-premise context. |
| 5–8 tools as a universal ceiling | Do not treat as established | Set 4 relevant tools as a provisional project default and test it. No supporting measurement was supplied for the claimed general threshold. |
| Temperature 0 and seeds | Adopt as reproducibility controls, not guarantees | Runtime, device, scheduling, and implementation still matter; repeated trials remain required. |
| Stable prefixes, keep-alive, role budgets | Adopt and measure | They make resource behavior inspectable. Cache benefit depends on runtime behavior and actual prompt reuse. |
| Trace replay | Adopt early | Step replay isolates model changes; strict trajectory replay catches divergence. Changed action plans still need real isolated fixture runs. |
| Independent graders | Adopt | Production self-checks are not independent evaluation. Free local releases can rely on deterministic fixtures and human labels; a paid grader is optional. |
| Prompt-injection controls | Adopt runtime enforcement, qualify delimiters | Separate source content and disable action tools during extraction/checking. A later planner remains exposed to semantic influence, so authorization and boundaries must be enforced outside the model. |
| Do not persist derived facts in v1 | Adopt | Keep direct attributed facts/preferences/decisions. Use explicitly source-keyed caches and revalidate their inputs; defer a durable inference graph. |
| Hash the retrieved source set | Strengthen | This misses newly added evidence. Disable cross-run discovery/absence caches unless the complete search scope can be versioned. |
| Error taxonomy and result truncation | Adopt | Distinguish retryable transport from uncertain side effects, and make incomplete evidence visible. |
| Numerical M1 gates | Adopt as provisional targets | Define benchmark workload and hardware first; numbers are acceptance goals, not promises about any 9B model or laptop. |
| Cut HIL menu features | Simplify implementation, preserve user requirements | A flat terminal menu can include recommended/alternative choices, More options, free text, and pause/cancel. Defer elaborate navigation and dashboards. |
| One provider at M1 | Confirm | This was already the intended milestone split. Make local-only M1 and optional providers at M4B unambiguous. |
| Split spec and rationale; add glossary/worked trace | Adopt | Keep AGENT_PLAN.md as the concise entry point, SPEC.md as requirements, this file as rationale, and a synthetic JSON trace as a concrete example. |
| Recheck model existence/license | Keep candidate status and artifact checks | Official model cards were inspected during planning. Their listing is evidence of current availability/license metadata, not certification of a particular redistributed artifact or its quality. |

## Architecture choices

The five central records are Contract, Evidence, Claim, Check, and Decision. They are typed objects in one application, not five services or a mandatory five-call chain. Deterministic code should handle routing rules, parsing, policy, calculations, and state checks when appropriate.

T1 is intentionally narrow: “the database.default field is sqlite in this file” is easier to establish than “the running service uses SQLite.” The latter requires applicable runtime observations and belongs in T2 if existing evidence cannot establish it. Cheap mode must change the permitted claim scope, not lower truthfulness standards.

The claim-first representation reduces one failure channel but creates two measurable responsibilities: selecting all material claims needed by the request and ensuring final text stays within checked claims. We therefore measure both omitted claims and unsupported additions. Semantic verification includes insufficient evidence rather than forcing a binary answer.

Local-first is an access and deployment goal, not a promise that a small model matches any hosted model. Keep one model resident, avoid unnecessary calls, and measure every supported quantization/profile separately. A schema can ensure that evidence_ids is an array without ensuring the IDs are real or their contents support the answer.

HIL is a decision protocol, not a substitute for evidence verification. Its first UI is small, but exact-action approvals, persistence, custom replies, and existing authorization are requirements from the start. The system does not need to ask again for a reversible read already within scope.

The first memory service stores explicit facts with attribution and direct observations with versions. Generated conclusions remain in the run record or a cache with known dependencies. If the complete source set is unknown, caching is disabled rather than claiming that hashing a partial set solves invalidation.

Replay prevents unnecessary tool execution, but cannot establish that a changed plan works in the real world. If a new model asks for a different file or changes action arguments, replay reports divergence; it must not feed that request a convenient recorded answer. End-to-end tests use fresh synthetic workspaces and fake services.

## Second trace review

The second feedback identifies defects in the teaching trace and gaps in its relationship to SPEC.md. The original example was labeled incomplete, but that did not justify illustrating invariants incorrectly. The earlier syntax/reference checks did not establish causal ordering, semantic support, or replay completeness.

| Observation | Review and change |
| --- | --- |
| The renderer introduced a field-specific line 2 | Correct. The value happened to be on that line, but no checked output established that precise locator. Remove the extra detail from the positive example and retain the original as an intentionally negative case. |
| No model-call inputs or runtime metadata | The provenance was unspecified, which is a real gap. The claim that C1, CL1, and rendering necessarily came from a model is not established: these can be deterministic. The revised direct example names deterministic producers; a separate model-call specimen defines exact input/output and metadata without inventing an invocation. Every real future model call must be recorded. |
| Missing trace version, sequence, config, timestamps, budgets | Add trace envelope rules and explicitly scripted teaching records. Actual runtime counters and latency remain unavailable; examples do not demonstrate measured performance. |
| Unchecked claim inside a supported answer | Correct. Use immutable claims plus claim_status events referencing completed checks, and require delivery to reference the current status projection. |
| Custom reply silently becomes a new scope | Correct. Add interpretation, validated delta, provenance, and user-visible echo. Ambiguity keeps the decision pending. An echo is not consent, and clear harmless scope changes do not need repetitive confirmation. |
| Tier decrease was implicit | Correct. Add an explicit superseding contract and tier_change justified by human scope or a deterministic rule, with retained/removed obligations. Model self-assessment cannot reduce checks. |
| K1 could compare evidence with itself | The method did not define its reference. It now names a separately loaded immutable source snapshot and byte hash. This is integrity checking, not independent corroboration of source truth. Rereading a changed live file would be a new observation, not verification of old bytes. |
| K3 claimed fidelity before text existed | Correct. Separate pre-render contract coverage, render, post-render fidelity against independently bound template inputs, and delivery. Any output change invalidates the fidelity result. |
| fixture-v1 was mutable identity | Correct for this fixture design. Retain that label only for display; source bytes and structured records receive content hashes. A genuine immutable version ID can be useful, but the example had not established one. |
| Policy was an opaque string | Add rule/version, grant, evaluated boundary, state preconditions, and action hash. Policy remains outside the model. |
| Decision snapshot/timing was absent | Add snapshot hash, issue/response times, and optional expiry. Timestamps support auditing; absence of automatic submission must also be exercised by HIL tests. |
| Only a happy-path example | Add conflicting records with insufficient runtime evidence, a revised action with rejected stale approval, and a strict replay mismatch with zero writes. |

The teaching examples are internally checkable data, not implemented agent tests. Actual model metadata, usage counters, and tokenizer-dependent truncation checks cannot be populated truthfully until a real model call exists. The separate specimen marks these unavailable and is ineligible as a measured model replay.

## Initial scaffold choices — 2026-09-18

The user explicitly requested creation of the folder structure and necessary/optional project foundations. This authorizes the package scaffold, not a claim that the agent works. The project now uses a src/thread_agent layout, Python 3.11+, setuptools packaging, a standard-library CLI, Ruff as an optional development dependency, and reserved unittest directories. uv.lock records the initially resolved development dependency; pip remains a supported setup path. No cloud SDK, model download, runtime database, or external service is required by the scaffold.

The CLI implements only help, version, and implementation status. Other packages have descriptive docstrings rather than fake successful operations or premature abstract interfaces. Configuration and prompt files are explicitly draft/not loaded. Optional web, messaging, scheduling, delegation, hosted/private providers, and deployment have locations and ownership notes but no enabled behavior.

These choices keep the first package installable and reviewable while preserving open model, hardware, task, and license decisions. Existing plan/spec/trace documents remain in place to preserve references. Packaging follows the [Python packaging guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/). Scaffold CI uses the documented [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) actions; CI has not yet run on a hosted repository.

## Research sources and limits

- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) documents schema-constrained responses, subsequent validation, and lower-temperature settings. This supports the initial structured-output path; it does not prove semantic correctness. The page also distinguishes local support from cloud support.
- [Ollama chat API](https://docs.ollama.com/api/chat) documents format, tool interfaces, keep_alive, and timing/cache usage fields. These enable measurement; they do not guarantee a latency improvement.
- [Ollama FAQ](https://docs.ollama.com/faq) documents local-only cloud controls and operational settings. Offline policy also needs to cover the rest of this application's tools.
- [vLLM reproducibility](https://docs.vllm.ai/en/latest/usage/reproducibility/) documents reproducibility limitations and runtime/hardware conditions. This is why pinned seeds supplement rather than replace repeated tests.
- [Self-RAG](https://arxiv.org/abs/2310.11511) motivates adaptive retrieval and critique, but its specially trained model's reported gains cannot be attributed to this proposed prompt-based runtime.
- [Self-correction research](https://arxiv.org/abs/2310.01798) motivates external feedback; its results are tied to the studied settings rather than every current model.
- [Lost in the Middle](https://arxiv.org/abs/2307.03172) motivates testing evidence order and bounded context on our chosen models.
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) motivates simple composable workflows and criteria-driven refinement.
- [Agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) motivates outcome grading, isolated trials, multiple grader types, and repeated attempts.
- [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), and the [Ollama distribution listing](https://ollama.com/library/qwen3.5) were checked during planning. The model cards identify Apache-2.0 licensing. Exact selected artifacts, notices, compatibility, and quality remain release checks.
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) is a reference for an optional hosted free-tier candidate. Availability, quotas, and data terms must be checked when that integration is introduced.

## First usable increment — 2026-09-18

After running scaffold status, the user requested the next step. The implemented profile deliberately limits an answer to a scalar field in an explicitly selected TOML/JSON source. A local model can suggest a field but cannot generate its value or silently establish the user's intended scope. Persisted human field selection precedes deterministic parsing, claim/status records, coverage, rendering, and checking the actual rendered slots.

This provides a useful local operation without presenting general semantic verification as solved. Explicit --field lookups need no model; optional Ollama calls use a model the caller selects. An existing llama3.1:8b was used for one synthetic smoke case, not adopted as a certified default or substituted for the planned Qwen evaluation. No models were downloaded.

The profile is pre-M1: source-report replay is narrower than model trajectory replay; field decisions are narrower than exact-action approvals; records and budgets are not the full release schemas. These gaps are named in SPEC.md section 12 and docs/first-workflow.md. Adding deterministic reference fixtures does not establish the full M0 workload or a benchmark result.

## VS Code developer slice — 2026-09-22

The user explicitly chose VS Code and four developer workflows. A TypeScript extension calls the existing Python core through isolated, bounded subprocess requests rather than introducing a public HTTP service or a second orchestration framework. Local Ollama remains the only model destination; a model is selected explicitly, without automatic downloads. General answers are clearly labeled unverified because checking a real source ID does not establish entailment.

The first repository context path uses bounded lexical retrieval and root/nested gitignore rules. This is useful without paid embeddings, but cannot claim complete repository comprehension. Native VS Code diffs and WorkspaceEdit provide review and normal editor integration. Snapshot/source/version checks surround approval; uncertain outcomes cannot reuse a proposal. This remains a trusted local-workspace workflow, not an adversarial filesystem sandbox or complete action recovery runtime.

Text, PDF and DOCX cover common documents with explicit extraction limits. Larger ranges stop instead of silently truncating. The extension retains only the latest analysis in workspace state, separate from CLI SQLite sessions. Future work should improve symbol-aware retrieval, independent semantic checks, task-output evidence, richer document coverage and provider profiles against real fixtures before claiming general autonomy.

## Public preview distribution — 2026-09-24

The owner requested that others can install Thread publicly. This authorizes publication work, but does not supply a license grant or Marketplace account identity. The first publication path uses a clearly marked pre-release VSIX and manual Marketplace upload, avoiding a new long-lived token dependency. Package checks bind publisher/version/license/target/channel and retain dependency notices and a checksum/provenance sidecar. A manual Actions workflow builds artifacts with read-only repository permission and no publishing secrets. These packaging checks do not certify model accuracy or satisfy M6.
