# Thread — Local Developer Agent

Ask questions about your repository, diagnose errors, review proposed code changes, and summarize documents using a local Ollama model. Thread can manage the runtime and initial model setup on supported Macs. No paid API key is required.

Bundled backend packages and online/offline distribution for Windows, macOS and Linux are under development. Current published/built packages still require Python unless they include a native backend asset. Windows repository access remains blocked pending secure platform implementation. See [distribution progress](https://github.com/KrishnendraPrakash/thread/blob/main/docs/distribution-modes.md).

**Thread: Import Offline Local AI** imports an unpacked, trusted companion bundle after review of its manifest SHA-256, platform, model, native runtime and size. Copying is cancellable and checksum-verified; Thread checks the local model before activating it. Official companion bundles and real offline inference validation are still pending. Windows remains gated pending native validation of its new handle-based source reader.

Use one Thread window during offline setup. Copying is serialized with an import lock; cancelled or failed copies remove their staging data. Completed repeat imports preserve separate copies. See the distribution guide for crash recovery and retained manifests.

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

Private Apple Silicon native candidates now pass extracted-package probes without external Python. A maintained portable Python 3.12.15 build and real offline companion trial now pass on the current Mac with external networking denied; see [distribution trial](https://github.com/KrishnendraPrakash/thread/blob/main/docs/distribution-trial.md). The offline assembler uses already acquired, inventoried files and does not download or execute them.

The real trial exposed and corrected execute permissions for runtime helpers such as llama-server. Reviewed companion inventories now record executable flags for native backend/runtime assets. Other platforms and complete redistribution/signing gates remain pending.

The isolated VS Code host fixture now exercises the production offline command with scripted consent/decline, successful activation, missing-model and state-persistence rollback, cancellation cleanup and prior-installation preservation. Startup metadata is synthetic in that fixture; real copied-model inference was checked separately. Zstandard native-library notices are now retained separately from its Python wrapper notice; full portable-Python dependency notices, owner license selection and platform signing remain release gates.

## Native candidate validation update

Native CI for commit `3e436ad` passed all six targets (macOS ARM64/x64, Linux ARM64/x64 and Windows ARM64/x64): native builds, JSON/dependency probes, distribution tests and synthetic offline-import tests. Both Windows runners executed and passed the regular-read/enumeration/limits and hardlink/junction-rejection tests. [Verified run](https://github.com/KrishnendraPrakash/thread/actions/runs/38142298112). These are backend/fixture checks, not full editor, clean-machine or model-inference certification. Windows editor activation remains gated pending broader document/edit integration validation. The repository now offers a [beginner guide with clickable setup choices and expandable help](https://github.com/KrishnendraPrakash/thread/blob/native-distribution-validation/README.md). This source documentation update does not update the Marketplace page or provide an official offline release.

Publishing automation is being prepared as an inactive, gated design using Entra workload federation, exact package fingerprints and protected approval. No automated upload is enabled. See the repository's [automation preparation](https://github.com/KrishnendraPrakash/thread/blob/main/docs/marketplace-automation.md) after that documentation is reviewed and merged; this local source update does not change the Marketplace page.

Protected GitHub/Azure OIDC authentication and the publishing identity profile lookup passed. The owner reports Contributor membership; independent Marketplace verification remains pending. Publishing stays inactive while the six remaining release gates and production builder validation are unfinished.

Local release automation now includes host-native candidate packaging and offline companion assembly, six-target inventory aggregation, and a resumable upload/listing controller with a durable exact-release ledger. Both production workflows remain inactive under `release/*.yml.disabled`. Production execution and validation and six remaining evidence gates remain pending; no new public package is provided by this preparation.

Both inactive release workflows now pin every Action to a verified official upstream commit and disable persisted checkout credentials. Recovery restores only a validated same-commit publishing attempt. A CI-only review can exercise native probes and synthetic recovery tests without enabling publishing or resolving production release gates.

## Publishing identity lookup

The manual `Marketplace identity lookup` workflow resolves the publishing managed identity’s Marketplace User ID on `main` after owner approval in the protected `marketplace-publish` environment. It authenticates through GitHub OIDC and returns only the nonsecret profile ID. It does not publish extensions or assign Marketplace roles. The lookup is setup verification, not a completed release gate.

Cross-platform validation found and corrected Windows upload-ledger lock cleanup: the file handle closes before lock deletion. Recovery still stops after uncertain uploads. This does not enable publishing.

The next preview is **0.2.1**, with Thread-authored code/documentation under **MIT**. Bundled dependencies and optional runtime/model assets keep their own terms and notices. Complete native redistribution review and all other production gates remain pending; no Marketplace upload occurred.

Private Mac 0.2.1 installation checks passed for an offline-installed Python wheel and an isolated native VSIX profile. The local runtime produced a simple offline completion, but one structured Qwen 0.5B repository request was rejected as incomplete; model suitability and other-platform editor/inference checks remain open. Packaging preserves the exact MIT text and third-party notices. No new public installer is published.

A follow-up draft adds Windows x64 document/proposal/frozen-protocol fixtures and verifies that the Windows product guard still blocks setup. It also retains source-bound static dependency notices for the verified portable Mac Python build, including OpenSSL 3.5.9. These are core/transport fixtures and notice provenance checks, not Windows UI, real-model or clean-machine certification. Publishing stays inactive and the production gates remain pending.

Git now preserves project-license and dependency-notice bytes across platform checkouts, so Windows newline conversion cannot invalidate the reviewed SHA-256 records.

The next hosted Windows check installs the actual CI-only native VSIX in empty VS Code profiles and exercises its activation, commands, license and backend. Windows setup still rejects through the shipped guard; positive setup/edit/inference and normal-consumer installation remain unvalidated. No VS Code/test utility, model or CI-only installer is bundled into the public extension by this preparation.

The pinned Windows Code archive uses a commit-prefix wrapper directory. Test acquisition preserves the verified side-by-side executable/runtime layout before invoking Code; its version, commit and byte digest remain checked.

Installed-host guard observation uses the actual activated module's error handler, preserving its original behavior and the shipped guard. It avoids relying on a separate test extension's notification API facade.

### Private positive Windows integration candidate

The Windows CI fixture packages two unpublished VSIXs: an unchanged guard control and a candidate whose staging bytes omit exactly the known Windows platform rejection. Workspace trust, source boundaries, human review and stale/buffer validation remain in place. No runtime setting enables Windows in the shipped source. The candidate exercises actual installed commands and the native backend against synthetic loopback responses, including reviewed replacement/creation, pause/cancel, dirty/stale rejection, duplicate rejection and a second host launch requiring renewed review. These are scripted integration fixtures, not real-model, managed-runtime, manual UX or ordinary-user certification. CI results must be checked before claiming this candidate passed. Release and publishing gates remain pending.

Pathspec 0.12.1 source access is recorded in native notices; other target-specific binary inventories and the final offline companion rebuild/review remain open.

Positive Windows CI exposed a real workspace-identity mismatch between VS Code short paths/drive casing and Python final paths. Review/file-URI and dirty-buffer checks now resolve Windows paths through the native filesystem API on both sides, preserving case-sensitive component distinctions and rejecting different or missing workspaces. The shipped Windows guard remains in place; hosted validation of the correction is pending.

Windows candidate execution also demonstrated LF proposals becoming CRLF in newly created editor buffers. Edits now explicitly preserve consistent proposal line endings; mixed/bare-CR content is rejected before dispatch. Exact post-edit validation and uncertain-outcome handling remain mandatory. The actual installed fixture covers both LF and CRLF creation; CI validation is pending.
