# Current project status

As of: 2026-09-18. Recheck the workspace before relying on this snapshot.

## Active phase

**Initial implementation: experimental direct-field workflow (pre-M1).** After trying scaffold status, the user requested the next step toward use. That authorizes the first local workflow and its validation. It does not complete the full M0/M1 acceptance gates or authorize model downloads, general actions, hosted providers, or a package release.

The public documentation is already on GitHub. The current implementation increment makes a narrow source-report workflow usable; broader architecture remains a target.

## Implemented

- `thread-agent ask --file FILE --field POINTER`: exact scalar TOML/JSON field reports with source hashes and explicit captured-file scope. No model needed.
- Optional natural-language question plus `--model NAME`: local Ollama suggests a field, which requires explicit human scope confirmation. Values are parsed, not generated. Source values are not included in the model prompt.
- Numbered recommendations and alternatives, More, exact custom field text, pause/cancel, ambiguity handling, persistence across restart, and stale/duplicate field-reply rejection. These are field clarifications, not action approvals.
- Scoped descriptor-based reads on macOS/Linux, size/type limits, rejected traversal/symlinks/hard links, and no source writes or shell tools.
- SQLite session snapshots and ordered events; `sessions`, `resume`, `trace`, and deterministic stored-source `replay`.
- `doctor` lists installed models from literal loopback Ollama; no model download or automatic provider fallback.
- [First workflow guide](../docs/first-workflow.md), current [README](../README.md), [component map](../docs/structure.md), and ten [development fixtures](../evals/cases/development/field_lookup.json).

Python minimum remains 3.11. No third-party runtime dependency was added. Draft config files are not loaded; explicit CLI flags configure this increment. Other source packages remain placeholders.

## Actual validation

Local Python 3.12.13 / macOS arm64:

- All 28 automated tests pass. They cover field outcomes, path boundaries, malformed input, unchanged source files, persisted/restarted choices, ambiguous/stale/duplicate replies, provider output validation, and replay without live source/model access.
- Ten synthetic development fixtures compare exact field values against references kept outside the source workspace. They are deterministic tests, not 30 model trials or a held-out benchmark.
- One live field-suggestion call used existing Ollama 0.34.2 and llama3.1:8b Q4_K_M. It suggested /database/default, remained pending, then returned sqlite after a scripted fixture confirmation. Stored-source replay passed. Exact model identity is recorded in the workflow guide; this does not establish a certified model default or performance distribution.
- CLI help/status, local source reports, trace/replay, Ruff, and syntax checks are verified during implementation. CI is configured to run tests without a model server; hosted results for this increment are not yet verified.
- Built a wheel and source distribution; installed the wheel into a fresh temporary environment without runtime dependency downloads and exercised the exact-field report and replay there. The wheel contains the new runtime modules and excludes evaluation/test fixtures.
- Checked 103 local documentation links/anchors, matched the README status example, and parsed all 14 current Mermaid sources. Diagram tooling remains temporary; visual rendering on GitHub is not claimed.

Earlier scaffold work checked installation, wheel/source builds, isolated wheel CLI entry points, and public documentation links. The documentation update parsed 12 embedded Mermaid diagrams plus the original full architecture; those prior checks are not runtime measurements. Fresh-session steering discovery and GitHub visual rendering remain unverified.

## Still unimplemented or incomplete

General chat and file search; multi-file synthesis and semantic support checking; T0/T2 routing; full Contract/Evidence/Claim/Check/Decision schemas; exact tokenizer-aware/global budgets; complete HIL/action approval scenarios; arbitrary custom-language interpretation; strict model-trajectory replay; durable memory, retention/deletion operations, skills, file edits, and hosted/private adapters.

The first workflow uses a smaller versioned event format. Unknown provider usage remains null; its records do not meet every full-spec trace/replay requirement. Source-report replay validates stored bytes and reported fields, not source truth, question intent, current state, or model quality. The three real priority tasks, minimum hardware, and full profile/benchmark freeze remain open. No M0/M1 or release gate is declared complete.

## Repository and working preferences

Git is on main with origin at https://github.com/KrishnendraPrakash/thread.git. The user requested detailed commit messages; follow [engineering standards](engineering.md). Check actual Git status before assuming an implementation change has been committed or pushed. No package publication, model download, or license selection has occurred. Source publication does not satisfy M6.

## Next boundary

Use the experimental workflow, gather real task requirements, and expand the M0/M1 profile deliberately. Add full typed records, budgets, capability tests, human-decision scenarios, and replay guarantees before attempting the broader acceptance gates. Qwen3.5-9B/4B remain untested candidates; the available llama smoke test is not a replacement default.
