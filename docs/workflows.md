# Workflow guide

For the implemented developer extension, see [VS Code workflows](vscode.md) and its [Mermaid source](vscode-workflow.mmd). The broader architecture diagrams below remain targets except where marked implemented.

[Back to the README](../README.md)

Thread now has an [experimental direct-field workflow](first-workflow.md) with local suggestions, saved field choices, and source-report replay. **The diagrams below describe the broader target architecture; they do not imply complete implementation.** The separate first-workflow guide shows the implemented path. The final contribution workflow describes current development.

These diagrams split the [full architecture](../AGENT_ARCHITECTURE.mmd) into readable views. Nodes describe responsibilities, not separate services or mandatory model calls. [SPEC.md](../SPEC.md) is authoritative. Every tool operation must pass runtime policy; arrows never grant permissions.

## Architecture

The first application will use a terminal, one local model adapter, and SQLite. Optional interfaces will share the same runtime controls.

```mermaid
flowchart TD
    cli["Terminal interface - M1"] --> runtime["Runtime: scope, routing, context, and budgets"]
    optional["Later: web, messaging, scheduling, delegation"] -.-> runtime
    runtime <--> decisions["Human decisions and saved checkpoints"]
    runtime --> policy["Runtime policy and typed tool arguments"]
    policy --> tools["Scoped file and calculation tools"]
    tools --> evidence["Evidence snapshots and provenance"]
    runtime --> models["Provider interface and capability checks"]
    models --> local["Local Ollama - M1"]
    models -.-> other["Optional hosted or private endpoints - M4B"]
    evidence --> checks["Claims, checks, and coverage"]
    checks --> render["Answer rendering and final fidelity"]
    render --> cli
    runtime <--> store[("SQLite: separate sessions, execution, memory, and caches")]
    decisions <--> store
    runtime --> trace["Allowed trace data and model-call records"]
    trace --> replay["Replay and independent evaluation"]
```

One local inference request at a time is the initial proposed default. Diagrams with multiple branches do not require simultaneous models. See the [component map](structure.md) for directory ownership.

## Task routing

Use the smallest path that can support the requested result. “What does this file say?” and “What is the running service doing?” can require different evidence.

```mermaid
flowchart TD
    request["Request and supplied material"] --> contract["Define objective, scope, constraints, and required results"]
    contract --> clear{"Essential scope clear?"}
    clear -->|No| human["Persist clarification and wait for a valid reply"]
    human --> contract
    clear -->|Yes| tier{"Choose and record task tier"}
    tier -->|T0| transform["Transform supplied input or compute explicit values"]
    transform --> fidelity{"Fidelity, values, and coverage checked?"}
    fidelity -->|Yes| deliver["Deliver checked output"]
    fidelity -->|Needs stronger checks| investigate
    tier -->|T1| lookup["Policy-controlled local lookup"]
    lookup --> exact{"Exact field or source report with adequate scope?"}
    exact -->|Yes| direct["Bind claim, check value and scope, then verify final answer"]
    direct --> deliver
    exact -->|Conflict, inference, or missing support| investigate
    tier -->|T2| investigate["Investigation or action with applicable checks and policy"]
    investigate --> result["Verified result, checked partial answer, clarification, or stop"]
```

T0 still uses supplied input as evidence. T1 does not establish runtime behavior from configuration alone. Tier reductions require a superseding contract justified by an explicit human scope decision or a versioned deterministic rule. A model cannot reduce its own obligations or permissions. See [task routing requirements](../SPEC.md#2-task-routing).

## Evidence to answer

Evidence identifies what was inspected; claims state what it supports. A matching source hash proves byte identity, not truth, freshness, or semantic support.

```mermaid
flowchart TD
    inputs["Supplied inputs or policy-controlled observations"] --> snapshot["Capture source bytes, scope, versions, hashes, and locators"]
    snapshot --> claims["Construct immutable evidence-bound claims"]
    claims --> checks["Run applicable deterministic and semantic checks"]
    checks --> status["Append claim status: supported, contradicted, or insufficient"]
    status --> enough{"Enough support for the requested result?"}
    enough -->|Yes| coverage["Check contract coverage before rendering"]
    enough -->|No| next{"Useful next step within budget?"}
    next -->|Authorized observation| inputs
    next -->|Human knowledge or scope needed| decision["Persist a human decision"]
    decision -->|Validated response; revise scope if needed| inputs
    next -->|No| partial["Select supported partial content and explicit gaps"]
    partial --> coverage
    coverage --> render["Render checked content with scope and limitations"]
    render --> fidelity{"Actual rendered output matches checked content?"}
    fidelity -->|Yes| deliver["Deliver the exact checked render"]
    fidelity -->|No| repair{"Repair budget remains?"}
    repair -->|Yes| claims
    repair -->|No| fallback["Render a bounded limitation template"]
    fallback --> fallbackcheck{"Limited output passes fidelity check?"}
    fallbackcheck -->|Yes| deliver
    fallbackcheck -->|No| halt["Stop without an unchecked factual answer"]
```

Required checks must finish before status transitions use them. Unsupported specifics, including precise line numbers, cannot be added during rendering. Any edit to the rendered text invalidates its previous fidelity check. Human approval does not turn a failed factual check into a pass. See [evidence and answer requirements](../SPEC.md#3-evidence-first-claims-second-prose-last).

## Human decisions

Dependent work pauses when a required answer or approval is missing. Independent work that is already authorized may continue.

```mermaid
flowchart TD
    need["Clarification, correction, provider choice, or approval needed"] --> save["Persist decision, checkpoint, reason, evidence, and proposal identity"]
    save --> menu["Show recommendation with reason, alternatives, More options, and free text"]
    menu --> wait["Wait for explicit response"]
    wait -->|More options| more["Show additional relevant choices"]
    more --> wait
    wait -->|Pause or restart| paused["Keep decision pending and restore its checkpoint"]
    paused --> wait
    wait -->|Cancel| cancel["Record cancellation and stop dependent work"]
    wait -->|Optional skip| skip{"Is skipping permitted?"}
    skip -->|No| wait
    skip -->|Yes| skiprecord["Record skip without granting approval"]
    wait -->|Selection or custom text| interpret["Record raw reply and proposed interpretation"]
    interpret --> clear{"Interpretation clear and valid?"}
    clear -->|No| clarify["Ask focused clarification; remain pending"]
    clarify --> wait
    clear -->|Yes| echo["Echo interpreted scope or proposal"]
    echo --> valid{"Matches current decision, proposal, and state?"}
    valid -->|Stale or material change| save
    valid -->|Valid| record["Persist validated decision"]
    record --> resume["Resume checkpoint; recheck policy for actions"]
    skiprecord --> resume
```

No timeout, preselected option, empty Enter, or restart submits a required approval. An echo is not consent. Action approvals bind to the exact action and relevant state and can be consumed only once. See [human decision requirements](../SPEC.md#5-human-in-the-loop).

## Model selection

Local access is the primary target. Additional providers require explicit configuration; no role may quietly send data elsewhere.

```mermaid
flowchart TD
    task["A task stage requests model inference"] --> profile["Load explicitly selected model profile"]
    profile --> kind{"Configured provider?"}
    kind -->|M1 local| local["Ollama on the local system"]
    kind -->|M4B hosted free| free["User credentials and visible quota/data terms"]
    kind -->|M4B hosted paid| paid["User credentials and explicit cost budget"]
    kind -->|M4B private| private["Configured endpoint, authentication, and TLS"]
    local --> gate
    free --> gate
    paid --> gate
    private --> gate
    gate{"Capabilities, destination, context, and budget allowed?"}
    gate -->|Yes| inference["Invoke selected model and record available metadata"]
    inference --> validate["Validate returned structure before using it"]
    validate --> outcome{"Valid result?"}
    outcome -->|Yes| stage["Return to requesting stage; factual checks still required"]
    outcome -->|No| recovery["Bounded repair or classified failure"]
    gate -->|No| unavailable["Disable affected mode; explain limitation or request configuration"]
    unavailable -->|Explicit user configuration change| profile
```

Schema-valid output is not automatically correct. Startup checks will test the capabilities required by the selected profile. Offline mode must cover tools, search, embeddings, and telemetry as well as model calls. Local model candidates are unbenchmarked; see [model requirements](../SPEC.md#8-model-access-and-public-distribution).

## Approved actions

An existing valid scope grant should avoid repetitive questions. Every action still passes policy, including an action introduced during a simpler task.

```mermaid
flowchart TD
    proposal["Concrete action, typed arguments, and expected state"] --> policy{"Runtime policy result?"}
    policy -->|Denied| deny["Report limitation; do not execute"]
    policy -->|Approval required| decision["Show exact proposal and persist human decision"]
    decision --> response{"Explicit valid response?"}
    response -->|Cancel| cancel["Cancel action"]
    response -->|Ambiguous or stale| decision
    response -->|Changed proposal| proposal
    response -->|Approve exact proposal| approval["Record approval bound to action and state"]
    approval --> policy
    policy -->|Allowed under current authorization| fresh{"Preconditions still match and approval unused if required?"}
    fresh -->|No| refresh["Invalidate stale proposal or approval; inspect current state"]
    refresh --> proposal
    fresh -->|Yes| execute["Dispatch once with idempotency and applicable approval consumption"]
    execute --> observed{"Outcome known?"}
    observed -->|No or interrupted| reconcile["Reconcile actual state before considering any retry"]
    reconcile --> report["Report checked outcome or unresolved status"]
    observed -->|Yes| check["Read and verify actual outcome"]
    check --> report
```

Policy denial cannot be overridden by a retrieved document, skill, or model. A successful tool return alone does not establish completion. Read-only extraction, checking, and rendering stages expose no action tools. See [tool and policy requirements](../SPEC.md#6-tools-errors-and-untrusted-data).

## Memory and cache

Conversation history, execution state, durable memory, and caches have different purposes even when they share SQLite.

```mermaid
flowchart TD
    input["Fact, preference, decision, observation, or generated conclusion"] --> eligible{"Eligible for attributed durable memory?"}
    eligible -->|Explicit fact or versioned observation| memory["Store scope, attribution, and provenance"]
    eligible -->|Inferred conclusion| run["Keep in run record; no automatic durable fact"]
    memory --> change{"Correction or deletion?"}
    change -->|Correction| supersede["Supersede prior fact and invalidate dependent caches"]
    change -->|Deletion| remove["Remove from active retrieval and retained stores under retention policy"]
    change -->|No| retrieve["Retrieve only within applicable scope"]
    remove --> incomplete["Replay needing removed evidence fails explicitly"]

    query["Potential cached answer"] --> complete{"All source dependencies and search scope known?"}
    complete -->|No| fresh["Fresh authorized retrieval; no cross-run discovery or absence cache"]
    complete -->|Yes| versions{"Sources, request scope, model, prompt, and retrieval policy unchanged?"}
    versions -->|Yes| reuse["Reuse only within validated scope"]
    versions -->|No| evict["Evict stale entry"]
    evict --> fresh
```

Hashing previously retrieved files cannot detect a newly added relevant file. Open-ended discovery and absence claims therefore cannot reuse a cross-run cache without a complete versioned search scope. See [memory requirements](../SPEC.md#7-memory-and-cache-first-version).

## Failure and recovery

Failure is a recorded result, not permission to switch providers, repeat a side effect blindly, or claim success.

```mermaid
flowchart TD
    error["Failure or incomplete result"] --> type{"Classify the problem"}
    type -->|Transport or rate limit| retry{"Retry safe, useful, and within budget?"}
    type -->|Interrupted action| reconcile["Inspect actual state and reconcile uncertain effects"]
    reconcile --> retry
    type -->|Malformed tool call| reject["Reject before dispatch"]
    reject --> repair{"Bounded repair available?"}
    repair -->|Yes| validate["Repair and revalidate arguments and policy"]
    repair -->|No| stop["Report limitation or persist paused state"]
    type -->|Policy denied| stop
    type -->|Stale state| refresh["Refresh evidence; invalidate checks and approvals"]
    type -->|Missing or truncated evidence| gather["Page or gather within scope; preserve gaps"]
    type -->|Unsupported capability| configure["Disable mode; request an explicit supported configuration"]
    retry -->|Yes| again["Retry with backoff and current policy checks"]
    retry -->|No| stop
    validate --> budget{"Still within global limits?"}
    refresh --> budget
    gather --> budget
    budget -->|Yes| resume["Resume the applicable workflow"]
    budget -->|No| stop
```

Cancellation must stop further dependent work; interrupted effects still need reconciliation. Human waiting is recorded separately from active computation. A timeout, empty result, or truncated search does not prove absence beyond the inspected scope. See [errors](../SPEC.md#6-tools-errors-and-untrusted-data) and [resource limits](../SPEC.md#4-small-model-execution-profile).

## Replay and evaluation

Runtime checks help produce an answer. Independent evaluation determines whether the system actually met the task requirements.

```mermaid
flowchart TD
    traces["Permitted records: inputs, outputs, evidence, decisions, versions, and budgets"] --> complete{"Required records present and consistent?"}
    complete -->|No| incomplete["Mark replay incomplete and stop"]
    complete -->|Yes| mode{"Replay mode?"}
    mode -->|Step| step["Reevaluate one recorded input; no live tools"]
    mode -->|Strict trajectory| match{"Request, arguments, occurrence, state, and proposal match?"}
    match -->|No| mismatch["Stop with replay mismatch; never invent a result"]
    match -->|Yes| recorded["Use corresponding recorded observation; no live effects"]
    step --> grade["Independent reference checks and human labels"]
    recorded --> grade
    fixtures["Fresh isolated end-to-end fixtures for full or changed plans"] --> grade
    grade --> metrics["Report correctness, coverage, unsupported claims, HIL, latency, and cost"]
    metrics --> profile["Publish results per model, runtime, quantization, and hardware profile"]
```

Strict replay repeats the match check for each request; changed approvals stop it. Held-out answers stay outside agent context, memory, and replay inputs. Optional model graders require calibration and cannot simply reuse the system's own score. Current [planning traces](../planning_examples/README.md) are synthetic and do not establish model performance. See [evaluation requirements](../SPEC.md#9-trace-replay-and-evaluation).

## Contribution workflow

This is the workflow available **today**. Runtime contributions must add meaningful tests as behavior is implemented.

```mermaid
flowchart TD
    clone["Fork or clone the repository"] --> context["Read project status, contributor guidance, and relevant requirements"]
    context --> branch["Create a branch and make a focused change"]
    branch --> docs["Update affected docs, diagrams, and examples"]
    docs --> checks["Run checks appropriate to the change"]
    checks --> pass{"Checks pass and claims match actual behavior?"}
    pass -->|No| branch
    pass -->|Yes| pr["Commit and open a pull request"]
    pr --> ci["Scaffold CI and reviewer feedback"]
    ci --> revise{"Changes requested?"}
    revise -->|Yes| branch
    revise -->|No| merge["Maintainer review and merge"]
```

The current CI checks style, syntax, CLI behavior, boundary tests, and deterministic development fixtures without a model server. It is not the full M1 or model benchmark suite. See [development commands](development.md) and [contribution guidance](../CONTRIBUTING.md).
