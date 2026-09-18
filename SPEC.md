# Agent specification

Status: requirements for the target agent. An experimental source-field workflow now exists; the complete runtime and milestone gates have not been implemented or benchmarked. Updated 2026-09-18.
MUST is a release requirement for the applicable capability; SHOULD is a proposed default that can change with documented evaluation evidence. Numerical settings below are initial targets, not measured hardware capabilities.

## 1. Scope and terminology

| Term | Definition |
| --- | --- |
| Goal | Public reusable agent, local operation without paid LLM credentials as primary, evidence-based answers, persistent human decisions, optional hosted and private models |
| Contract | Request objective, entities, scope, constraints, assumptions, and completeness criteria; an object, not necessarily a separate model call |
| Evidence | Versioned source excerpt, supplied input, structured value, or tool observation with provenance |
| Material claim | An assertion whose removal or alteration changes the answer, requested result, or user's likely decision |
| Scope | The entity, environment, timeframe, and version to which a statement applies |
| Claim | A scoped assertion bound to evidence IDs or explicit derivation inputs |
| Check | A recorded deterministic or semantic assessment with a method, result, and evidence references |
| Decision | A persisted human clarification, choice, correction, or scoped approval |
| Direct observation | What a tool established about the state it inspected, within its limits |
| Source report | What a document or person states; it does not automatically establish external truth |
| Supported | Applicable checks establish support for this scoped claim; not a universal truth guarantee |
| Insufficient | Required evidence or a reliable check is missing; distinct from contradicted |

| ID | Requirement |
| --- | --- |
| S1 | The first vertical slice MUST use Python, terminal UI, SQLite, and one local model adapter. Other providers MUST remain optional and arrive in M4B. |
| S2 | The core MUST support one user per installation, scoped local files, corrections to memory, and approved bounded actions. Multi-tenant hosting and delegation are deferred. |
| S3 | Documentation MUST identify tested OS, hardware, model, quantization, context, and runtime versions. It MUST NOT imply support for every laptop. |

## 2. Task routing

| Tier | Eligibility | Required path | Escalation |
| --- | --- | --- | --- |
| T0: bounded transformation | Formatting supplied material, simple source-bound summaries, or explicit arithmetic; no external facts or side effects | Transform or compute; verify fidelity, preserved values, units, and required coverage | Ambiguous operands, unsupported additions, difficult synthesis, or unverifiable fidelity require a stronger check or T2 |
| T1: direct local evidence | Narrow read-only question answerable with a structured field or exact source report | Retrieve; bind claim to evidence; parser/quote and scope checks; render a constrained answer | Conflicts, causal inference, multi-source synthesis, or requested runtime claims not established by the source require T2 |
| T2: investigation or action | Contested facts, complex synthesis, changing external facts, or side effects | Evidence and claim construction; applicable semantic/deterministic checks; bounded investigation; policy and HIL where needed | Useful partial answer, clarification, or stop when evidence/budget is insufficient |

| ID | Requirement |
| --- | --- |
| T1 | Routing SHOULD use rules from the request and contract first; a model classifier is optional when ambiguous. The model MUST NOT choose its own permissions. |
| T2 | The trace MUST record initial tier, reason, promotions, and selected checks. Tiers MUST be reevaluated when new evidence or proposed actions change the task. |
| T3 | Every proposed action MUST pass runtime policy regardless of tier. An apparently harmless request cannot bypass action checks through misclassification. |
| T4 | T0 MUST NOT mean evidence-free: the supplied source and arithmetic inputs are evidence. T1 MUST NOT equate citation existence with entailment. |
| T5 | Contracts, routing, evidence selection, and claims MAY be combined into fewer calls when reliably validated. Architecture nodes MUST NOT imply a fixed minimum call count. |
| T6 | Tier reduction MUST require a superseding contract justified by an explicit human scope decision or a versioned deterministic routing rule over established inputs. A model's assessment that its own answer is adequate MUST NOT reduce its checks. Record a tier_change with old/new contract IDs, from/to tiers, direction, cause event/rule, removed obligations, and retained obligations. Remaining conflicts or requested actions MUST NOT silently disappear; revised actions still require policy and any applicable approval. |

## 3. Evidence first, claims second, prose last

| Object | Minimum fields |
| --- | --- |
| Contract | id, objective, scope, required_results, assumptions, tier |
| Evidence | id, source_key, content_hash of captured bytes, display version when useful, locator, excerpt/value, source_kind, scope, observed_at, effective_at when known, truncation metadata |
| Claim | immutable id, statement or structured proposition, scope, evidence_ids, type, derivation when applicable; status is projected from claim_status events |
| Check | id, claim_ids, evidence_ids, method/version, exact input refs/hashes, result, short justification or computed output |
| Claim status | claim_id, previous/new status, supporting check IDs, evidence snapshot hash, reducer rule/version |
| Render | id, text, limitations, claim IDs, claim-status references, template/model-call reference, output hash |
| Answer | render_id, rendered_text, claim_ids, limitations, final_fidelity_check, claim-status references |

| ID | Requirement |
| --- | --- |
| E1 | Factual paths MUST select evidence IDs and construct scoped claims before final prose. Each evidence ID and quoted span MUST resolve to the stored source version. |
| E2 | Deterministic support MUST be restricted to checks actually justified by parsing, exact source reporting, calculation, or observed outcomes. General paraphrase and inference need semantic checks; source metadata itself may be uncertain. |
| E3 | Semantic checks SHOULD evaluate one material claim and the minimum complete supporting context. Result MUST allow supported, contradicted, or insufficient. Multi-premise claims MUST retain all necessary premises. |
| E4 | The final renderer MUST preserve checked scope and limitations and MUST NOT add factual specifics. T1 SHOULD use templates for exact fields/quotes. Free prose MUST undergo material-claim coverage/fidelity review; if budget is exhausted, use a supported template or bounded partial result. |
| E5 | Final-answer factual coverage and claim extraction recall MUST be evaluated using human-annotated claim sets. Unknown or missed claims MUST NOT count as verified. Contract coverage MUST detect omissions. |
| E6 | Sources MUST retain entity/version/date, headings, units, and context sufficient for meaning. Retrieval time MUST NOT substitute for effective date. Duplicated reports from one origin MUST NOT count as independent corroboration. |
| E7 | Contradictions SHOULD trigger the smallest authorized check that distinguishes alternatives. Failed retrieval MUST NOT establish absence outside the inspected scope. |
| E8 | Checks MUST use one stable evidence snapshot. Changed inputs MUST invalidate relevant checks and stale action proposals. Human approval MUST NOT convert failed factual checks into passes. |
| E9 | Every factual output detail, including a field-specific line number, date, or unit, MUST resolve to a checked claim, derivation, or checked citation metadata. A span covering lines 1–2 MUST NOT be narrowed to a field on line 2 without a locator check. Templates MAY omit unverified specifics. |
| E10 | Claims MUST be immutable; status changes MUST be append-only claim_status events referring to completed checks. Delivery MUST require current statuses for every material claim, or explicitly identify unresolved claims. A source-integrity check alone MUST NOT support a semantic claim. |
| E11 | Contract coverage MUST run before rendering; final fidelity MUST inspect the actual rendered text and limitations after rendering, using its output hash. Any text change MUST require a new fidelity check. Delivery MUST refer to that exact checked render. |
| E12 | Source-integrity methods MUST name both inputs: the captured tool excerpt and a separately loaded immutable snapshot with a verified byte hash and locator. Matching a value to itself MUST NOT be called independent corroboration. Snapshot integrity establishes reproducible bytes, not source truth or freshness; establishing current state requires a fresh observation. |

## 4. Small-model execution profile

| Role | Initial maximum input tokens, including instructions/history/schemas | Output token reserve | Evidence limit and placement |
| --- | --- | --- | --- |
| Contract / next-step selection | 2,048 | 512 | At most 4 short identified excerpts if needed |
| T0 transform | 4,096 | 1,024 | Supplied source clearly separated; long or lossy inputs require chunking/fidelity checks |
| Evidence-bound claims | 6,144 | 1,024 | At most 8 relevant spans with IDs, adjacent to the claim task; never split a needed qualifier |
| Semantic check | 4,096 | 512 | One claim with 1–4 necessary spans; promote/restructure if more context is essential |
| Final rendering | 4,096 | 1,024 | Checked claims and limitations; raw evidence only when needed |

| ID | Requirement |
| --- | --- |
| L1 | Total input, output, and any model reasoning budget MUST fit the tested runtime context. Caps MUST be measured with the actual tokenizer where available or conservative accounting. Oversized input MUST be retrieved in smaller pieces or rejected explicitly, not silently dropped. |
| L2 | The initial local structured-claim profile MUST use server-side schema-constrained generation where supported and independently validate its outputs. Missing required capabilities MUST disable that profile. A future adapter MAY implement a tested equivalent via native structured tools; no universal requirement for one vendor's grammar interface. |
| L3 | Models SHOULD see at most 4 relevant tools per call initially. This is a tunable project default, not a proven universal threshold. Raw text MUST NOT be executed as a tool call. |
| L4 | Planning and checking SHOULD use temperature 0 and recorded seeds where supported. Evaluations MUST pin model/runtime/template/options and hardware metadata, and MUST still use repeated trials. A seed MUST NOT be described as a guarantee across runtimes or devices. |
| L5 | Role prompt prefixes SHOULD remain stable when semantics are unchanged. Local keep_alive SHOULD initially be 5 minutes, subject to memory limits. Actual cache hits, warm/cold load time, and peak memory MUST be measured; caching is not guaranteed. |
| L6 | Local inference concurrency SHOULD default to 1. Independent verification branches MAY run concurrently on a tested profile; no second loaded model is required. |
| L7 | Initial global active-run limits SHOULD be 12 model requests, 8 tool calls, 2 repair passes, and 120 seconds, plus configured token/cost limits. Human waiting is recorded separately and does not count as active computation. Caps are tunable before benchmark freeze; no limit exhaustion authorizes an action or upgrades evidence. |

## 5. Human-in-the-loop

| ID | Requirement |
| --- | --- |
| H1 | M1 MUST include a compact terminal decision: why input is needed, evidence/proposal, 2–4 relevant options when possible, recommendation with a short rationale, alternatives, More options when available, explicit free text, and pause/cancel. Optional decisions MAY allow skip. These preserve the user's requested features without a nested dashboard UI. |
| H2 | Decisions MUST persist an ID, checkpoint, type, displayed choices/recommendation, evidence/proposal snapshot hash, issued_at, applicable expiry, response time, and status. An empty evidence set MUST still have an explicit snapshot identity. Action decisions MUST include exact action/argument hash and relevant state preconditions. |
| H3 | No timeout, default selection, empty Enter, or restart MAY submit a required approval. Existing scoped authorization MUST be respected without repetitive prompts. |
| H4 | Dependent work MUST pause. Independent already-authorized work MAY continue. Restart MUST restore pending decisions. |
| H5 | Replies MUST be matched to a decision and validated. An approval MUST be consumed once for its exact action. Duplicate/stale replies MUST fail. Material proposal changes or custom instructions MUST trigger revalidation and a revised reviewable proposal where approval is needed. |
| H6 | The first UI uses pending, answered, and cancelled states plus a validity check for replaced proposals. Rich dashboards, multi-user response authentication, and complex navigation are deferred. External interfaces MUST authenticate responders before introduction. |
| H7 | Human assertions about facts MUST retain provenance and appropriate uncertainty. Facts do not become verified merely because the user selected an option. |
| H8 | Custom replies MUST produce an interpretation record with raw response ref, interpreted contract/proposal delta, normalizer rule or model_call ref, validation result, and a concise echo shown to the human. Exact deterministic mappings MAY resolve to an existing option ID. Ambiguous replies MUST remain pending and receive focused clarification; an echo alone is not approval or proof of correct interpretation. Clear low-impact scope changes need no redundant approval. Material action changes require a revised concrete proposal and approval when policy requires it. |

## 6. Tools, errors, and untrusted data

| Error class | Required response |
| --- | --- |
| transport / rate_limit | Bounded retry/backoff where safe; no unapproved endpoint or paid fallback |
| timeout / interrupted_action | Reads may retry within budget; uncertain side effects require reconciliation before retry |
| schema / malformed_tool_call | Reject before dispatch; one bounded repair within global limits or stop |
| policy_denied | Do not retry unchanged or allow retrieved text to override policy |
| approval_required | Create/reuse an applicable concrete HIL decision |
| empty_result | Record inspected scope; broaden authorized retrieval or report missing evidence |
| oversized_result | Store permitted bounded source data, return locator/summary plus truncation metadata and paging cursor |
| stale_state / conflict | Refresh relevant evidence and invalidate outdated checks/approvals |
| unsupported_capability | Disable affected mode or request an explicit supported configuration |

| ID | Requirement |
| --- | --- |
| X1 | Tools MUST enforce typed arguments, workspace/path boundaries, allowed operations, and network destinations outside the model. Side-effect retries MUST use idempotency or state reconciliation; completion claims MUST read/check actual outcomes. |
| X2 | Tool responses SHOULD initially expose at most 2,000 tokens per page. They MUST include source/version/locator, truncation flag, and a way to retrieve omitted content where feasible. Total response bytes stored MUST also be capped. Truncated results cannot establish complete coverage or absence. |
| X3 | Retrieved text MUST use separate source/tool messages with fixed provenance and boundaries, never injected as system instructions. Delimiters alone are not a security boundary. |
| X4 | Extraction, semantic checking, and rendering turns MUST expose no action tools. A subsequent planner MAY propose tools, but the runtime MUST intersect them with the original authorized task scope and phase allowlist. Tainted content and derived summaries cannot grant authority. |
| X5 | Tests MUST include a retrieved document and an injected source filename that attempt writes, data export, tool substitution, or memory poisoning. Their success condition is no unauthorized effect, not simply a polite model refusal. |
| X6 | Policy records MUST name the allow/deny/approval-required result, policy rule/version, existing scope grant if applicable, evaluated operation/path/network boundary, action hash, and evaluated state preconditions. Human approval is an input to policy, not a bypass. |

## 7. Memory and cache, first version

| ID | Requirement |
| --- | --- |
| M1 | SQLite MUST separate conversations, execution state, direct attributed facts/preferences/decisions, and caches. V1 MUST NOT automatically persist inferred/derived conclusions as durable facts. |
| M2 | Cache entries MUST record every explicit source key/hash plus request scope, prompt/model version, and retrieval-policy version. Reuse MUST revalidate source versions. Internal writes MUST evict affected entries by source key; external changes MUST be detected on read/reuse. |
| M3 | V1 MUST disable cross-run caches for open-ended discovery, absence claims, or queries whose complete source set cannot be established. Hashing yesterday's retrieved files does not detect a newly added relevant file. |
| M4 | Corrections MUST replace/supersede attributed memory and evict affected cache entries. Deletion MUST remove content from active retrieval, indexes, summaries, applicable caches, and retained snapshots/traces under the documented retention policy. A replay lacking deleted evidence MUST fail explicitly. |
| M5 | A later durable derivation graph requires separately evaluated dependency creation and invalidation. It is outside v1. Skills MUST remain versioned procedures subject to runtime policy. |

## 8. Model access and public distribution

| Profile | Initial policy |
| --- | --- |
| M1 local | Ollama; Qwen3.5-9B and Qwen3.5-4B are candidates, not certified defaults; choose tested quantizations and hardware profiles |
| M4B hosted free | User-owned credentials, currently eligible provider/model, quota and data terms visible; Gemini is a candidate |
| M4B hosted paid | User-owned credentials and explicit budget; no dependency of the local workflow |
| M4B on-premises | Organization endpoint, model ID, authentication, and verified TLS; tested compatible serving stack |

| ID | Requirement |
| --- | --- |
| P1 | The adapter MUST normalize messages, tool IDs/results, schemas, errors, streaming where available, and usage. Startup MUST test harmless tool round trips and capabilities required by the selected profile. |
| P2 | Every model role MUST obey configured destination/privacy/budget rules. Offline mode MUST also disable remote search, embeddings, and telemetry. Setup downloads are explicit. |
| P3 | Model artifact digest, quantization, license metadata/notices, source, runtime, template, and context settings MUST be checked and recorded before release. Current model-card availability is not certification. |
| P4 | Keys MUST remain in local secret storage/environment, never tracked files or logs. Public examples and fixtures MUST be synthetic. Core tests MUST run without paid credentials; live integrations are separate. |
| P5 | Public release MUST include the repository license decision, setup instructions, compatibility reports, notices, provider examples for supported modes, and measured limitations. Model weights MUST NOT be committed. |

## 9. Trace replay and evaluation

| Mode | Rules and limits |
| --- | --- |
| Step replay | Reevaluate a stored model/check input with immutable recorded evidence; executes no live tools; measures that step only |
| Strict trajectory replay | Match canonical tool name/arguments, occurrence, and recorded state against recorded results; new or divergent requests MUST stop with replay_mismatch, never receive invented results |
| End-to-end fixture run | Run tools against a fresh isolated synthetic environment; required to assess changed plans, recovery, writes, and real task success |

| ID | Requirement |
| --- | --- |
| V1 | Replay traces MUST retain allowed tool inputs/outputs, state/version, sequencing, decisions, model/options/template, errors, and truncation metadata. Replay MUST never consume live approvals or perform external actions. Redacted/missing records MUST mark replay incomplete. |
| V2 | Historical approved decisions in a fixture MAY simulate a human response only for the identical recorded proposal. Changed proposals MUST stop for a fixture response or invalidate the replay. |
| V3 | Runtime self-check scores MUST NOT be used as independent release grades. Deterministic reference checks and human labels are primary; optional independently configured model graders MUST be calibrated against human labels and MUST NOT be the system-under-test grading itself. Stronger or different does not automatically mean accurate. |
| V4 | Start with about 40 development and 20 held-out tasks, then expand for each capability. Held-out answers MUST remain outside agent context, memory, and replay inputs. Different trials MUST start from isolated state. |
| V5 | Report task correctness/completeness, material-claim recall, unsupported-claim rate, final-prose additions, semantic-check false positives/negatives, wrong-tier rates, unnecessary abstention, HIL outcomes, replay divergence, cost, latency, and memory by model profile. |
| V6 | Test document order, irrelevant text, negations, changed dates/units, conflicting versions, removed evidence, corrected/deleted memory, newly added files, failures, and injected instructions. Routing evals MUST include T0/T1 cases that should promote to T2. |
| V7 | Repeated trials MUST report variation. Paired baseline/evidence/verification comparisons MUST hold fixtures and workload budgets constant or report extra compute explicitly. |
| V8 | Every trace MUST declare schema_version, run ID/mode, config hash, source manifest hashes, and sequenced events with IDs, seq, timestamps, producer/rule or model-call refs, and budget snapshots. Actual active elapsed time MUST use a monotonic clock; wall-clock and human-wait time MUST be recorded separately. Synthetic examples MUST label scripted values and unavailable measurements explicitly. |
| V9 | Every actual model invocation MUST have a model_call event retaining role, exact serialized model input and hash, raw returned output before validation, model artifact digest/quantization, runtime/version, chat template ID/hash, prompt/schema IDs/hashes, effective context and decoding options including temperature/seed where supported, usage counters, timings, and finish/truncation metadata. Inputs may be content-addressed blobs. Unknown provider fields MUST be null with a reason and reduced replay guarantees, never invented. Secrets are excluded; any content redaction affecting model input MUST mark replay incomplete. |
| V10 | Hashes MUST bind canonical structured objects or exact source/input/output bytes under an identified algorithm/encoding. Display labels such as fixture-v1 are insufficient identity. Model-call token counts MUST be compared with preflight token accounting under compatible tokenization; a discrepancy requires investigation, not automatic proof of truncation. Unsupported counters remain unknown. |
| V11 | Trace provenance MUST distinguish deterministic code, human input, tool execution, model output, and synthetic fixture records. A deterministic contract/parser/template MUST NOT be attributed to a model. A teaching trace with no model calls can replay deterministic steps only; it MUST NOT be described as a model benchmark. |
| V12 | Budget snapshots MUST count attempted requests/tool dispatches including failures and retries, repairs, token/cost usage when known, active time, and human wait against configured limits. Policy-denied proposals are recorded separately from dispatched tools. Unknown token/time observations MUST NOT silently count as zero consumption. |

## 10. Milestone gates

| Milestone | Gate |
| --- | --- |
| M0: fixtures and profile | Freeze initial scope, synthetic fixtures/reference outcomes, one baseline hardware profile, schemas, routing expectations, and provisional budgets before scoring |
| M1: local vertical slice | At least 27/30 correct complete trials over 10 direct-local fixtures repeated 3 times; all 13 defined HIL scenarios pass; no unauthorized effects/false completion; warm T1 p50 <=20 s and p95 <=45 s on the frozen profile for <=2,000 input and <=150 output tokens; record cold start and peak memory separately |
| M2: claims and checks | At least 95% material-claim recall on an expanded annotated draft set; zero missed critical claims in that set; reject all defined unsupported-critical-claim fixtures; no loss of required answer coverage versus baseline |
| M3: tiering and investigation | All defined side-effect promotion cases pass; report tier precision/recall; bounded repair, oversized responses, and replay mismatch stop correctly; broader task correctness improves or added complexity is reconsidered |
| M4: memory, skills, and actions | Defined correction/deletion/cache-new-source cases pass; changed/stale approvals cannot execute; replay never causes live effects; side-effect recovery invariants pass |
| M4B: providers | Repeat capability and task gates per supported configuration; no averaging a failing local preset with a stronger hosted result; no unauthorized fallback |
| M5: external research | Source applicability, freshness, synthesis, and completeness meet task rubric in isolated and live checks with separately reported results |
| M6: public release | All deterministic invariants pass; >=90% complete/correct answerable trials and >=90% correctly limited unanswerable trials; no unsupported critical or false completion claims observed in release suite; publish sample counts, uncertainty, costs, limits, and reproducible setup |

| HIL fixture IDs | Required scenarios |
| --- | --- |
| H01–H04 | Recommended choice; alternative; more options; explicit custom response |
| H05–H08 | Optional skip; cancel; no reply/default not submitted; restart while pending |
| H09–H12 | Duplicate reply; changed action arguments; changed relevant state; reuse existing valid scoped authorization |
| H13 | Ambiguous custom reply remains pending: no inferred approval, unauthorized scope reduction, or action |

## 11. Trace teaching cases and invariants

| Case | Required illustration |
| --- | --- |
| Direct scoped lookup | Interpreted custom reply and echo; explicit authorized tier reduction; structured read policy; byte-addressed source; checks then claim status; render then fidelity then delivery |
| Unsupported locator, negative | A renderer adds an unverified field line; expected fidelity failure even if the number happens to be correct |
| Conflicting records | Both source reports retained; targeted observation cannot establish runtime truth; unresolved runtime claim retained and bounded answer delivered |
| Changed action and replay | Custom reply changes proposal; obsolete approval rejected; no write occurs; strict replay of a changed request stops with replay_mismatch |
| Model-call record specimen | Exact synthetic input/output and prompt hashes; explicit null actual runtime/artifact/usage values until a real call exists; specimen must not count as a replayable measured model run |

Trace linting MUST check causal event ordering, referential integrity, hashes, status projections, decision validity, budget accounting, and the exact render checked. Passing trace linting establishes internal consistency only; it does not establish a model's factual accuracy or a runtime's correct implementation.

The latency and success gates are proposed engineering targets. They MUST be reviewed against the initial hardware baseline before freezing; changes MUST be documented and MUST NOT be used to retroactively label a failing run successful. Small suites do not establish population-wide reliability.

## 12. Experimental direct-field increment

The first implementation increment is a restricted T1 source report, documented in [the workflow guide](docs/first-workflow.md). It is pre-M1 work and does not waive the release requirements above.

- The caller explicitly selects a scoped TOML/JSON file. An exact scalar field pointer supplies the contract directly; otherwise a persisted human choice establishes that source-field scope.
- An explicitly selected local Ollama model may suggest a field using structured output. It receives the question and field names, not source values. Its suggestion cannot submit the human choice or establish that the original question was answered.
- Python parses the value, binds it to captured source bytes, records checks/status/coverage, renders a JSON report, then checks actual output slots. A report describes captured file content only. It makes no runtime, causal, multi-source, or semantic truth claim.
- Pending field choices support recommendations, alternatives, More, exact custom field input, pause/cancel, restart, and stale/duplicate rejection. This required choice has no optional Skip. Natural-language ambiguity remains pending. Action proposal approvals and the complete H01–H13 suite are not implemented.
- Local SQLite retains source snapshots and a smaller field-lookup-v1 event format. Replay checks the stored field report only, without live tool or model calls. Full trace schemas, model-trajectory replay, deletion/retention, tokenizer-aware budgets, and complete startup capability gates remain outstanding.
- Deterministic development fixtures and one local-model smoke call establish limited implementation evidence, not full M0/M1 acceptance. Models are explicitly chosen and no download, cloud fallback, or source edit occurs.

This narrows the initial implementation, not the product goal or the acceptance criteria. The full architecture diagram remains a target; the first workflow guide shows the implemented path separately.
