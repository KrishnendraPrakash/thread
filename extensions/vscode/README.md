# Thread — Local Developer Agent

An experimental VS Code extension for repository questions, debugging assistance, reviewable feature edits and document summaries. It uses a selected local Ollama model with no paid API requirement.

Run **Thread: Setup Local Model**, choose Python 3.11+ and an installed local text model, then open the **Thread** sidebar. Open a trusted local repository and save your files before analysis.

- Ask questions across eligible repository files and inspect cited snapshots.
- Diagnose errors using your description and VS Code diagnostics.
- Propose small features or fixes; inspect every diff before explicit approval.
- Summarize UTF-8 text, PDF text and DOCX main-body content, with explicit bounds.

General model answers are **not independently verified**. Source references are inspectable evidence, not a truth guarantee. Edits remain subject to review, source freshness and editor-buffer checks. Suggested tests have not run unless you explicitly launch a task.

Use **Thread: Review Pending Changes** for recommendations, custom refinement, More, pause and cancel. Use **Thread: Cancel Current Request** to stop inference, and **Thread: Clear Saved Analysis** to remove the latest stored analysis. Model inputs and source snapshots are retained in local VS Code workspace state until replaced or cleared.

Requires macOS/Linux, VS Code 1.95+, Python 3.11+, local Ollama and an installed text completion model. No automatic model download, cloud fallback, Windows secure-backend support, OCR, arbitrary binary document parsing, breakpoint control or autonomous shell execution.

[Full installation, usage, limits and troubleshooting](https://github.com/KrishnendraPrakash/thread/blob/main/docs/vscode.md)

This is an experimental preview candidate. Publication status is tracked in the repository; preparation does not mean a Marketplace listing is live. See the [publishing guide](https://github.com/KrishnendraPrakash/thread/blob/main/docs/publishing.md). Included Python dependencies retain their own notices under `python/*dist-info`.

[Privacy and local data storage](https://github.com/KrishnendraPrakash/thread/blob/main/extensions/vscode/PRIVACY.md) · [Changelog](https://github.com/KrishnendraPrakash/thread/blob/main/extensions/vscode/CHANGELOG.md)
