# Thread — Local Developer Agent

Thread 0.2.1 uses a **local model you supply** for repository questions, diagnosis, reviewed changes and document summaries. No model weights, including Llama, are distributed or downloaded by Thread. No paid API account is required.

The immediate 0.2.1 package is a universal **Python-source VSIX**, using the existing Marketplace stable channel with an experimental preview label. Install Python 3.9+ separately; no Python/native runtime, Ollama or models are bundled. Windows activation remains gated. The six-target native work is preserved as a separate future release effort. Source changes do not update the Marketplace listing.

## Dependencies — what you need

| Component | Requirement |
| --- | --- |
| VS Code | 1.95+ |
| Backend | **Python 3.9+ must already be installed**; Thread discovers it automatically |
| Ollama | Your existing local server; optional explicitly confirmed runtime-only installation on Apple Silicon macOS 14+ |
| Model | Your installed local completion model; supply it separately under its own terms |

## Start using Thread

1. Install Python 3.9+, install the universal source VSIX, and open a trusted local project.
2. Run **Thread: Setup Local Model** and select an installed model.
3. If setup needs attention, **Use existing Ollama (Recommended)** connects to port 11434 without downloads. **More options** provides setup details and explicit installed-model name entry; **Cancel** makes no setup change.
4. **Install local runtime only** offers a pinned Ollama download after size/location/terms confirmation. It never obtains model weights. Supply your own Ollama model store in the shown Thread storage location, or import your own offline bundle, then rerun setup.
5. Open the Thread sidebar and choose a workflow. Answers remain unverified; review sources and approve changes explicitly.

## User-provided offline setup

**Thread: Import Offline Local AI** continues to accept your own complete, trusted schema-1 bundle containing a matching backend/runtime, your model and notices. Inspect its manifest fingerprint and explicitly approve native execution. Existing integrity, traversal/link restrictions, cancellation and rollback remain. This is user import functionality; 0.2.1 distributes no official ready-to-use companions. Models in your bundle retain their original terms.

Keep one Thread window active during setup/import. Existing local servers are not terminated by Thread. See [distribution scope and limits](https://github.com/KrishnendraPrakash/thread/blob/main/docs/distribution-modes.md) and [runtime setup](https://github.com/KrishnendraPrakash/thread/blob/main/docs/local-setup.md).

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

Positive Windows CI exposed a real workspace-identity mismatch between VS Code short paths/drive casing and Python final paths. Review/file-URI and dirty-buffer checks now resolve Windows paths through the native filesystem API on both sides, preserving case-sensitive component distinctions and rejecting different or missing workspaces. The shipped Windows guard remains in place; the correction passed the actual installed Windows fixture.

Windows candidate execution also demonstrated LF proposals becoming CRLF in newly created editor buffers. Edits now explicitly preserve consistent proposal line endings; mixed/bare-CR content is rejected before dispatch. Exact post-edit validation and uncertain-outcome handling remain mandatory. The actual installed fixture covers both LF and CRLF creation; The actual installed Windows fixture passed LF and CRLF creation.

The pinned VS Code SDK disables disk storage during extension tests. The positive reload fixture therefore uses a private development driver without extensionTestsPath in the same disposable profile, allowing ordinary storage across two launches. The official binary is unchanged. The guard control continues using the standard SDK host; no normal user profile or model/runtime is involved.

Verified private Windows result (2026-10-12): [run 38209002553](https://github.com/KrishnendraPrakash/thread/actions/runs/38209002553) passed at source commit 256d159cbc2636485d28333cb11033ec4af970a5; all 19 branch/PR checks passed and no CI artifacts were exported. The unchanged installed package retained its Windows guard. The private candidate passed actual native inventory/setup selection, reviewed replacement remaining unsaved, LF/CRLF creation, pause/cancel, dirty/stale and duplicate rejection, and mixed-ending rejection before any staged creation or buffer edit. Two ordinary isolated Code launches retained the pending proposal and required renewed diff review. A private development driver avoids the SDK's deliberately in-memory extension-test storage; no binary is patched. Synthetic HTTP responses and scripted approvals are not real-model/runtime, manual UX, ordinary-user, bare-machine or Windows ARM certification. The source guard and global release gates remain unchanged. Draft PR: https://github.com/KrishnendraPrakash/thread/pull/6.


A manual runtime-integration suite now tests pinned Ollama 0.34.4 and Qwen2.5-Coder 0.5B on standard temporary Windows x64/Linux x64 GitHub runners, capped at 45 minutes per job. It checks disk space before downloads, inventories binaries/notices before execution, stops for additional vendor agreements, and separates CPU completion from unchanged production structured-response acceptance. No model/runtime downloads run on the developer Mac, no artifacts are exported, and the production Windows guard and starter models remain unchanged. This is pending integration evidence, not model-quality or release certification.


Runtime integration attempt (2026-10-12): draft PR #7, tested head 8669617dc07b9b017d92c37f23c4d0f1e932dbbe, manual run https://github.com/KrishnendraPrakash/thread/actions/runs/38214558895. Both disk preflights passed (Windows 157846134784 bytes free, Linux 92559486976 bytes free). Windows installed the pinned runtime and produced native/runtime inventories, then stopped before execution/model acquisition because CUDNN_LICENSE.txt and MLX notices were present. Additional vendor review/approval is pending; cuDNN agreement: https://docs.nvidia.com/deeplearning/cudnn/backend/v9.18.1/reference/eula.html. Linux downloaded the pinned runtime but the production extractor rejected an archive link with “Runtime link must reference an extracted internal file”; native build/probe passed, but runtime inventory/inference did not complete. Neither job acquired model blobs or executed Ollama. No artifacts were exported and no release guard was changed. Source CI passed; no real inference or model-quality result is claimed.


A separately selected manual `runtime-metadata` diagnostic reads only the exact approved Windows/Linux archive manifests and license text on temporary GitHub runners. It neither extracts nor executes payloads or acquires models; archives are deleted after inspection. This diagnoses the unresolved cuDNN notice and Linux archive-link rejection without continuing the blocked integration suite.


Metadata-only diagnosis passed on both runners: the cuDNN-named and MLX notices in the approved main Windows archive are permissive texts, with no cuDNN/MLX runtime binaries present. No extra SDK acceptance is needed for those exact notices. The audit now distinguishes exact inspected notice hashes from unapproved binaries. Linux extraction now supports bounded internal file-link chains by regular copying, retaining containment and size limits; synthetic security regressions pass. Real inference has not been rerun. [Evidence, exact component revisions and conditional SDK approval →](../../docs/runtime-integration.md)


Real integration retries exposed a Windows CI cleanup defect: the PowerShell ownership query returned system-process paths, so prior Windows cleanup attempts cannot establish owned-only termination. Affected temporary runs were requested force-stopped. Cleanup now treats process-query output solely as metadata and independently filters exact dedicated-directory paths in Node, rejects ambiguous identities, and rechecks executable/PID ownership before direct termination. Portable regressions exclude system paths, sibling prefixes, traversal, empty roots and duplicate IDs. Linux integration passed in multiple runs; one intervening zero-VRAM assertion failed and remains an unresolved inconsistency. No zero-VRAM check was weakened. Model outputs on both platforms were rejected separately from CPU completion.


The real CPU integration harness now explicitly selects Ollama’s documented `OLLAMA_LLM_LIBRARY=cpu`, disables Vulkan/integrated GPU discovery and masks accelerator visibility only for the owned test runtime child. This addresses a runner residency discrepancy without changing production settings or the captured structured request. Zero-VRAM assertions remain mandatory before/after the production call. Windows owned-process classification regressions remain enabled before acquisition.


Final Windows x64/Linux x64 real runtime integration passed at d003dbfd403e079c6f9ea196f74d9ebd406c1836: https://github.com/KrishnendraPrakash/thread/actions/runs/38218047751. Both actual native installs, exact model acquisition, CPU READY completions, unchanged structured-request capture, source preservation and independently checked zero-owned-process cleanup passed; zero VRAM before/after and zero artifacts. Production model answers were rejected separately (Windows invalid source references; Linux prohibited ask-mode edits), so model suitability remains unresolved. Earlier Windows cleanup filtering was defective and affected runs were cancelled; independent Node ownership checks and regressions now enforce the boundary. The production guard/starter list remain intact and release gates remain pending. See docs/runtime-integration.md for exact tested head, prior failures and limits.


Cleanup incident clarification: in cancelled run 38217103078 (head d5885b0), the pre-termination record listed unowned lsass.exe PID 1008 first, followed by svchost.exe PID 716. The exact sequential cleanup code reached PID 716 and logged its failed taskkill, with no failure logged for PID 1008. This establishes by control flow that the unowned PID 1008 termination command returned success; it was not merely a query. Successful stdout and an independent post-kill probe were not retained, so the actual process exit and full OS impact cannot be independently reconstructed. It would be incorrect to claim no unowned processes were terminated. The impact was confined to disposable Windows CI runners, whose teardown stalled; affected runs reached terminal cancelled state. Final corrected runs independently enforce ownership and report zero remaining owned processes. No user Mac process was involved.


Local packaging preparation now records exact PyInstaller BINARY and EXTENSION source/payload hashes while keeping redistribution review false. A private existing Mac backend copy has refreshed plaintext notices with unchanged non-notice bytes; its compiled installer still needs a final rebuild. Five target payload/source inventories and the release model decision remain unavailable/pending. No acquisitions, packaged-backend/Ollama/model execution, signing or remote changes were performed. [Concrete local inventory evidence](../../docs/local-packaging-inventory.md).


Current owner-approved 0.2.1 scope: six model-free native VSIXs; users supply models. No starter-model downloads or official companion ZIPs are shipped. User-owned offline import is preserved. The exact-scope companion-distribution gate is not applicable; five notice/editor-inference/Windows/clean-machine/signing gates remain pending. No signing, hosting, workflow activation or publication occurred.


The approved build-only CI now creates a temporary model-free VSIX on each of the six standard hosted targets, probes its actual native backend, verifies BYO package identity/content and prints exact native-file/source/notice inventory metadata. Packages are deleted on the runner; no artifacts, model/Ollama acquisitions, OIDC or publishing are involved. This does not advance ordinary-user, real-inference, complete licensing or signing gates.


Six-target temporary BYO VSIX proof passed at 50eec6cd8ad18ca69853f14ba48666801480f57e: https://github.com/KrishnendraPrakash/thread/actions/runs/38243563529. Actual packaged native protocol, model-free contents, per-file/source/notice inventories and synthetic offline import passed on Windows/macOS/Linux ARM64/x64; temporary packages were removed, with zero artifact exports. A Windows UTF-8 decoding fix resolved the first run. These results do not establish ordinary-user trust, real editor/inference, complete redistribution rights or signing. All five production gates and Windows activation remain pending. [Evidence](../../docs/byo-package-checks.md).

Local notice preparation (2026-10-12): [exact CPython core mappings and remaining distribution inputs](../../docs/byo-notice-progress.md) cover the recorded Mac/Linux source hashes and reject executable images mistaken for notice text. This is locally tested preparation; native notice completeness and publication remain pending.

Owner-approved follow-up: six free hosted targets collect exact installed distribution origins, versions and bounded original notice text; existing SDK redist hashes are compared without acquiring an SDK or accepting terms. Pinned Mac OpenSSL 3.0.16 and incorporated CPython license text supplement the exact core mappings. This work is under review; it does not promote the notice gate or activate publication.

Actual first provenance pass passed all six targets. Follow-up exact Ubuntu shared-library notice bindings retain full distribution copyright/source access; Windows 10+ packaging omits only OS-origin API-set/UCRT copies and probes the resulting package. No SDK terms are accepted, no redistributables are substituted, and Windows activation/publication remain gated. Full incorporated/static attribution is still pending.

Follow-up verification retains unresolved Windows copies until exact system-directory/component-store origin or installed-OS byte matching supports omission. Source paths are classified relative to trusted installation roots; notice links cannot escape their declared roots. Actual six-target results and Microsoft vendor-runtime obligations are tracked in the notice progress report.

Windows provenance traced the unwanted OS DLL copies to the runner JDK on PATH. Native build discovery now uses only selected Python/Windows roots; actual native probes run with nonexistent PATH/Python overrides. CPython packaging changes are summarized alongside its retained terms. The notice gate stays pending until final payload evidence and outstanding vendor/static obligations are resolved.
