# Thread preview: data and execution

Thread itself has no analytics service, advertising, account system, hosted backend or paid API integration. It runs a local Python subprocess and sends selected context to Ollama at `http://127.0.0.1:11434` for an existing server or a private IPv4 loopback port for a Thread-managed server. Detected cloud-backed models are rejected. Use a local Ollama installation/model you trust; Thread does not audit the server's implementation or its own logging.

## Data used

Repository requests inspect eligible saved workspace files. Root/nested .gitignore rules and path/size/type exclusions apply. Selected source excerpts, your request, and—for diagnosis—VS Code diagnostics may enter the model prompt. Secret-name exclusions are not a general secret scanner. Summaries read the document you explicitly choose, including documents outside the workspace when selected by you.

Python is discovered from absolute PATH directories and common local installation locations using bounded subprocess probes. Executables inside the inspected workspace (including symlink aliases) are excluded from automatic discovery. An optional explicit user-level Python override can select a project environment; the model name is also a user-level machine setting. Workspace overrides are ignored. No model weights or API keys are distributed in this extension.

## Optional setup downloads

On Apple Silicon macOS 14+, an explicit setup confirmation allows Thread to download a pinned Ollama runtime from GitHub release infrastructure and a selected starter model through Ollama’s registry/download infrastructure. Checksums verify the runtime archive, and Ollama verifies model layers. This sends ordinary download metadata to those services, not repository context. The managed server has cloud mode disabled. No download is triggered by a model response or retrieved source.

Managed runtime/model files are stored in the extension’s global storage `local-runtime` directory. Ollama may also create its normal user configuration. Files persist after cancellation/uninstall unless removed separately. **Clear Saved Analysis** does not remove these downloads. The extension stops only its own managed server on disposal; cancelling a transfer stops the client and managed server, but partial model layers may remain for a later retry. A crash or forced termination can leave an installer lock or temporary files; see setup recovery documentation.

## Local storage

The most recent completed analysis is kept in VS Code workspace state. It includes your prompt, source excerpts and hashes, model inputs/raw outputs, available usage metadata, and any proposal's before/after content and decision state. A completed new request replaces the stored analysis. Failed requests do not retain a complete audit trail.

**Thread: Clear Saved Analysis** removes this active workspace-state entry and in-memory snapshots. It does not erase open editor content, undo history, VS Code backups or physical database remnants. This version has no configurable retention schedule or secure-erasure guarantee. CLI sessions are separate and are not cleared by this command.

## Actions and network boundaries

The model does not execute shell commands. Proposed source changes require explicit review and approval. Existing-file edits remain unsaved; native creation may create new files on disk. Optional execution of an existing VS Code task requires a separate explicit selection and confirmation. That task can execute dependencies and access files/networks with your permissions.

Stopping an analysis terminates its Python client process. Ollama can briefly continue inference after disconnection. Already-started VS Code tasks must be stopped using VS Code's task controls.

VS Code, Marketplace installation, dependency/model setup downloads, other extensions, Ollama configuration and user-selected tasks have their own networking and privacy behavior. Thread's local inference path is not a guarantee that the entire editor or machine is offline.

Do not post source snapshots, raw traces, secrets or private documents in public issue reports. Report non-sensitive product issues through the repository issue tracker. A private security-reporting channel and response SLA have not yet been established.
