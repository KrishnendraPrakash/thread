# Changelog

## 0.1.1 — Claim schema fix

- Require at least one claim in the Ollama generation schema, matching independent validation.
- Clarify cited statement and uncertainty instructions without allowing fabricated claims.
- Show the invalid statement count and recovery steps when a model response is rejected.

Validated with deterministic provider-response cases; this patch is not a model accuracy benchmark.

## 0.1.0 — Preview candidate

- Ask questions across eligible saved repository files with captured source references.
- Diagnose problems from user-provided errors and VS Code diagnostics.
- Propose up to four bounded file changes with native diffs and explicit human approval.
- Summarize UTF-8 text, PDF text and DOCX main-body content with range and size limits.
- Select an installed local Ollama model; no paid API account or automatic model download.
- Preserve the latest analysis locally, cancel requests, and clear saved analysis.

Tested in an isolated macOS arm64 VS Code session and a small synthetic local-model smoke case. This is not a certified accuracy benchmark or completed M1/M6 release. Windows, OCR, autonomous debugger operation, hosted providers and durable knowledge memory are not supported.
