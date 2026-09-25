# Thread — Local Developer Agent

Ask questions about your repository, diagnose errors, review proposed code changes, and summarize documents using a local Ollama model. Thread can manage the runtime and initial model setup on supported Macs. No paid API key is required.

## Dependencies — what you need

| Dependency | Requirement | Installed by Thread? |
| --- | --- | --- |
| VS Code | Version 1.95 or newer, with a trusted local folder open | No |
| Operating system | macOS or Linux; macOS arm64 has local VS Code host testing | No; Windows and remote extension hosts are not supported in this preview |
| Python 3 | **3.9 or newer**, automatically detected from the extension host’s PATH and common installation locations | No; install Python once if it is missing |
| Ollama | Managed setup on Apple Silicon macOS 14+; existing local server on other supported systems | **Optional managed download** after confirmation |
| Text-generation model | Choose a starter download or an already installed local completion model | **Optional managed download** after confirmation; embedding-only models cannot answer questions |
| `pathspec` 0.12.1 | Repository ignore-rule handling | **Bundled**, no pip installation needed |
| `pypdf` 6.19.0 | PDF text extraction | **Bundled**, no pip installation needed |

You do **not** need a project virtual environment, LangChain, `uv sync`, a separate Node.js installation, or the Microsoft Python extension to use Thread. Python libraries needed by Thread are isolated from your project and included in the extension. Python itself remains a separate installation. Managed setup handles the Ollama runtime and model download on supported Macs; no Homebrew, Docker, admin commands or project changes are needed.

The extension runtime supports Python 3.9+; it does not require a specific version such as 3.12. Use a maintained Python release when possible. [pypdf’s Python requirement](https://pypi.org/project/pypdf/6.19.0/) sets the current compatibility floor; older Python 3 releases are not supported. The separate field CLI and extension build tools still require Python 3.11+.

## Start using Thread

1. Install Python 3.9+ if your machine does not already have it. [Python downloads](https://www.python.org/downloads/).
2. On Apple Silicon macOS 14+, let Thread handle local AI setup in the next steps. On Linux or Intel Mac, install/start [Ollama](https://ollama.com/download) and a text model separately.
3. Open your project in VS Code and save the files you want analyzed.
4. Run **Thread: Setup Local Model** from the Command Palette. Thread detects and checks Python automatically; there is no Python path prompt in the normal setup flow.
5. If local AI is unavailable, choose **Set up local AI for me (Recommended)**, select a starter model, and confirm the displayed download. If Ollama is already ready, choose an installed model. No model is certified for accuracy.
6. Open the **Thread** sidebar or run **Thread: Ask About Repository**.

Try: “Explain how this project handles an incoming request. Cite the relevant source excerpts.” Open the relevant source file to help retrieval focus on it.

## Managed local setup — no terminal commands

The runtime download is **160 MB** (Ollama 0.34.4, verified SHA-256). Starter choices are **qwen2.5-coder:1.5b**, about **986 MB**, or **qwen2.5-coder:7b**, about **4.7 GB**. Both list Apache 2.0 terms; the confirmation links to model details. The small starter minimizes the download and has limited reasoning quality. No model accuracy benchmark has certified either choice.

Setup checks for at least 4 GB free disk space for the small starter or 10 GB for the larger one. These are setup allowances, not RAM guarantees; inference also needs sufficient memory. Progress and Cancel are available. Runtime and models stay in Thread’s VS Code global storage; Ollama may create its normal user configuration. The server uses a private loopback port with cloud disabled and stops when this extension instance is disposed. Setup does not replace an existing Ollama installation. Repeated use starts the saved runtime without downloading it again.

**Scope:** managed installation currently supports Apple Silicon macOS 14+ only. Python 3.9+ is still needed. Existing Ollama remains supported on macOS/Linux. Full starter-model download/inference has not yet been verified on a clean machine; runtime download/startup and synthetic transfer/error tests have passed. [Setup details and recovery](https://github.com/KrishnendraPrakash/thread/blob/main/docs/local-setup.md).

## If setup needs attention

- **Python missing or incompatible:** install Python 3.9+ and restart VS Code so its PATH can refresh, then rerun setup. Detection tries a bounded list of local installations, including common Homebrew and system locations.
- **Stale path from another machine:** detection tries the saved user override, then discovers another compatible local installation and reports the chosen path. Clear the optional **Thread: Python Path** setting to return to automatic detection.
- **Unusual Python location:** use **Thread: Configure Python (Advanced)** to supply an absolute executable path. This is optional, not part of normal setup. Repository-local virtual environments are not automatically executed; selecting one requires this explicit override. **Python: Select Interpreter** is a separate extension setting.
- **Python ready, Ollama unavailable:** rerun setup and choose managed setup on a supported Mac. Use **Retry existing Ollama** after starting an existing server. **More options** includes documentation and an explicit installed-model name field.
- **No models found:** use the managed starter download on supported Macs, or install a text model in your existing Ollama. An embedding model alone is insufficient.
- **Unsaved files:** choose **File → Save All** before repository analysis. No Git commit is required.

## What Thread can do

- Ask questions across eligible saved repository files and inspect cited snapshots.
- Diagnose errors using your description and VS Code diagnostics.
- Propose small features or fixes; inspect every diff before explicit approval.
- Summarize UTF-8 text, PDF text and DOCX main-body content, with explicit bounds.

General model answers are **not independently verified**. Source references are inspectable evidence, not a truth guarantee. Edits remain subject to review, source freshness and editor-buffer checks. Suggested tests have not run unless you explicitly launch a task.

Use **Thread: Review Pending Changes** for recommendations, custom refinement, More, pause and cancel. Use **Thread: Cancel Current Request** to stop a request, and **Thread: Clear Saved Analysis** to remove the latest stored analysis. Model inputs and source snapshots are retained in local VS Code workspace state until replaced or cleared.

No unconfirmed downloads, cloud fallback, OCR, arbitrary binary document parsing, breakpoint control or autonomous shell execution. The extension reads a bounded selection of excerpts; it does not place an entire repository in the model context.

## Compatibility checks

The bundled editor suite has been run locally on Python 3.9.6, 3.12.13 and 3.14.7. The automatic setup flow has an isolated macOS VS Code host check. These are compatibility and behavior checks, not model accuracy benchmarks or certification of every OS/Python combination. Broader Python-version checks are defined in CI; a configured CI matrix is not a passing CI result.

[Full usage and troubleshooting](https://github.com/KrishnendraPrakash/thread/blob/main/docs/vscode.md) · [Privacy and local data storage](https://github.com/KrishnendraPrakash/thread/blob/main/extensions/vscode/PRIVACY.md) · [Changelog](https://github.com/KrishnendraPrakash/thread/blob/main/extensions/vscode/CHANGELOG.md)

This is an experimental preview. Included Python dependencies retain their notices under `python/*dist-info`. Source updates and a local VSIX do not update the Marketplace listing until a new version is published. See the [publishing guide](https://github.com/KrishnendraPrakash/thread/blob/main/docs/publishing.md).
