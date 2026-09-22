# Current project status

As of: 2026-09-22. Inspect current files and outputs before relying on this snapshot.

## Active phase and authorization

**Experimental VS Code developer slice plus the existing field CLI; full milestone gates remain open.** The user explicitly requested a VS Code extension for repository understanding, debugging assistance, writing features and document summaries. That authorizes this interface, backend workflows and approved bounded edits. Model downloads, hosted fallback, Marketplace publication and a repository license decision remain outside this increment.

## Implemented

- VS Code sidebar and commands for repository questions, diagnosis, feature proposals and selected document summaries. Local installed Ollama model selection; Python 3.11+ subprocess with bundled editor dependencies; no paid API or model download.
- Bounded saved-source discovery with root/nested gitignore, path/type/size/link restrictions and lexical retrieval. Source snapshots include paths, lines and hashes. Coverage/exclusions are disclosed. General model interpretations remain labeled unverified.
- Diagnosis includes user errors and VS Code diagnostics. Explicitly selecting/confirming an existing task can execute it; only its exit code is observed. No breakpoint control, generated-command execution or terminal-output interpretation.
- Up to four proposed text-file replacements/creations, exact native diffs, explicit review/apply choices, custom refinement, More, pause/cancel, source/buffer revalidation, and post-edit buffer comparison. Existing edits remain unsaved. No deletes, renames, new directories, auto-save, commit or push actions in the product.
- UTF-8 text, extracted PDF text and DOCX main-body summaries with explicit ranges, limits and extraction omissions. No OCR or universal document-format support.
- Latest analysis/proposal persisted in VS Code workspace state; Clear removes the active entry. Pending proposals survive reload, but review confirmations must be repeated. This is separate from CLI SQLite and is not a durable knowledge memory or full history.
- Existing CLI exact TOML/JSON field reports, optional Ollama field suggestions, saved human field choices, trace and deterministic stored-source replay remain available.

See [VS Code usage](../docs/vscode.md), [editor Mermaid source](../docs/vscode-workflow.mmd), [field CLI](../docs/first-workflow.md), SPEC.md sections 12–13 and the component map. The base CLI still has no third-party runtime dependency; the optional editor extra adds pathspec and pypdf. Draft profiles remain unloaded; editor settings and explicit CLI flags configure their respective interfaces.

## Actual validation

Local environment: macOS arm64, Python 3.12.13, Node 25.6.1 and VS Code 1.138.0.

- Python deterministic/workflow tests cover the original field behavior plus retrieval/ignore boundaries, linked files, source locators, immutable/stale proposals, mode/citation rejection, UTF-8 ranges, PDF text/blank/malformed cases, DOCX/entity rejection and the subprocess protocol. The current suite has 45 tests; it includes synthetic model responses and is not a model benchmark.
- Three Node subprocess tests pass: invalid operations, executable failures, cancellation/concurrency. TypeScript compiles.
- An isolated VS Code Extension Host fixture passed activation, command registration, sidebar activation, macOS path-alias handling, approved native buffer edits, file creation, persisted decision state and duplicate/stale rejection. Approvals were scripted in a temporary synthetic repository, not exercised on user source. Visual layout and every interactive HIL branch have not been manually certified.
- One live editor smoke case used the existing Ollama 0.34.2 / llama3.1:8b Q4_K_M. It identified an add function's subtraction bug, returned the expected replacement proposal and left the fixture source unchanged. It is one synthetic example, not model certification, repeated-trial accuracy or a benchmark. The earlier CLI field smoke remains documented separately.
- A local VSIX built with the Python core and dependency notices, excluding node_modules, tests and workspace sources. No Marketplace publication or installation into the user's normal VS Code profile occurred.
- CI now includes Python checks plus Node compilation/subprocess checks and VSIX packaging. Hosted results for this commit are not yet verified. Linux UI, Windows and remote-host support are not certified.

## Outstanding limits and next work

Full semantic support checking, complete Contract/Evidence/Claim/Check/Decision schemas, all H01–H13 scenarios, exact tokenizer/global budgets, model-trajectory replay, durable memory/history/retention, richer document extraction, language-server/symbol retrieval and hosted/private adapters remain unfinished. The editor preserves completed model inputs/raw outputs, but failed calls do not retain a complete audit trail. It does not meet the full trace/replay contract.

Filesystem/editor checks support ordinary trusted local development, not hostile concurrent mutation or an OS sandbox. Use one editor window per working tree. General answers may be wrong despite valid citations; approved code still needs inspection and tests. No M0/M1/M6 or public release gate is declared complete. Qwen candidates remain untested; no model default was certified.

## Repository preferences

Git origin is https://github.com/KrishnendraPrakash/thread.git. The user requests detailed commit messages and pushes for completed work. Check actual Git status before claiming a commit/push. No package/Marketplace release, model download or license selection occurred.
