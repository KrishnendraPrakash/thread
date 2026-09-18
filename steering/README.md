# Persistent steering

Updated: 2026-09-15.

These Markdown files preserve project context for future development sessions. They are development guidance; they do not implement the planned application's memory or context builder.

| File | Purpose | When to read |
| --- | --- | --- |
| [../AGENTS.md](../AGENTS.md) | Entry point, reading order, working agreements | At task start |
| [product.md](product.md) | User intent, established scope, provisional choices | At task start or after context loss |
| [status.md](status.md) | Current phase, completed work, open decisions, next boundary | At task start/resume and before claiming progress |
| [engineering.md](engineering.md) | Implementation patterns, review and validation standards | Before technical changes |

## Discovery

Codex supports repository instructions through AGENTS.md. The root file explicitly instructs the assistant to read these linked files; arbitrary steering filenames are not assumed to be automatically included. This follows the [official AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Start future sessions in this project directory. Other tools can read the same Markdown, but their instruction-discovery behavior must be configured or verified separately. No machine-global configuration is required by this setup. Fresh-session discovery has not been independently exercised by this planning task.

## Maintenance rules

- Keep stable purpose in product.md, technical conventions in engineering.md, and changing progress/open decisions in status.md. Keep detailed requirements in SPEC.md instead of copying its tables here.
- When the user changes direction, update the affected steering file and authoritative documents in the same task. Mark proposals as proposals until decided; mark measurements only after an actual run with recorded evidence.
- Update status.md after a milestone or material decision, not after every tool call. Replace stale current-state statements rather than accumulating contradictory appendices.
- Record the basis of important decisions using repository-relative links or a concise description of the user's instruction. Do not copy private conversation transcripts, credentials, host paths, or personal data into public steering.
- At a phase transition, record what the user authorized, what actually exists, and what remains. Planning language must not block a later explicit implementation request.
- Check that links resolve and that steering agrees with SPEC.md and the actual workspace. A handoff note is a starting point for inspection, not proof of current state.
- Keep always-read files short. Load detailed rationale, trace specimens, and schemas only when the task needs them.

## Sources of project context

Project direction comes from the user's planning requests: a public reusable agent, primary access through free local models, optional API/private endpoints, explicit human choice interfaces, stronger answer verification, and persistent steering before implementation. Exact requirements and reviewed feedback are recorded in [SPEC.md](../SPEC.md) and [RATIONALE.md](../RATIONALE.md).
