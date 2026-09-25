# Changelog

## 0.2.0 — Managed local AI setup

- Offer a confirmed runtime/model download when local AI is unavailable, with progress, cancellation, alternatives and recovery guidance.
- Manage a pinned, checksum-verified Ollama 0.34.4 runtime on Apple Silicon macOS 14+, without Homebrew, Docker or admin scripts.
- Keep models in extension storage and run an owned server on a private loopback port with cloud disabled; preserve existing-server support.
- Add small/larger starter downloads with sizes and terms; neither is accuracy-certified.
- Runtime installation/startup and synthetic download/error cases tested; a complete starter-model download/inference trial remains unverified.

## 0.1.3 — Automatic Python setup and public dependencies

- Detect installed Python automatically; recover from stale paths without the normal interpreter input prompt. Manual configuration is an advanced fallback.
- Support Python 3.9+ for the bundled editor runtime; the separate field CLI and build tooling still require 3.11+.
- Bound and allow cancellation of discovery; exclude repository executables, relative PATH entries and workspace symlink aliases.
- Show prerequisites, bundled dependency versions, setup and troubleshooting in the extension Details page.
- Compatibility checks passed on Python 3.9.6, 3.12.13 and 3.14.7, plus an isolated macOS VS Code setup test. These are not model accuracy benchmarks.

## 0.1.2 — Python setup recovery

- Probe the exact Python path entered during setup before saving it; use the same input for the model check instead of rereading settings.
- Report the detected Python version/path and distinguish missing Ollama from a failed Python launch. Preserve a valid Python setting even when Ollama is unavailable.
- Reject relative interpreter paths and explain that Thread setup is separate from the Python extension’s interpreter selection.

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
