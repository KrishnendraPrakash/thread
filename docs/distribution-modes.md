# Distribution modes under development

The owner requested Windows, macOS and Linux from the start, with both online first-use setup and an offline option. The goal is no separate user Python installation. These are authorized requirements, not delivered platform support.

## Owner-approved 0.2.1 scope

Public distribution is six native VSIXs with bundled backend/Python dependencies and **user-supplied models**. No model weights or official runtime/model companion ZIPs are shipped. This explicitly replaces the earlier ready-to-use offline bundle plan for 0.2.1; future model/companion distribution needs a new reviewed scope.

Users can select existing local Ollama models, optionally confirm runtime-only acquisition, or import their own complete trusted schema-1 bundle. The user import's model/runtime roles, integrity checks, explicit native-code approval and rollback are preserved. No Llama branding/redistribution is introduced into Thread's official artifacts. Current Windows activation remains gated; the target matrix is retained unchanged.

The official-companion distribution gate is not applicable only under the exact BYO 0.2.1 scope. Backend third-party terms, all-target editor/inference, Windows activation, clean-machine setup and signing remain pending. Native source/payload hashes support review rather than resolving those gates. The historical trials below are not official bundle promises.

## Target matrix

| Target | Packaging foundation | Current repository access | Managed AI acquisition |
| --- | --- | --- | --- |
| darwin-arm64 | Native launch/build configuration | Existing macOS-tested POSIX path | Existing macOS 14+ installer |
| darwin-x64 | Native launch/build configuration | POSIX backend build/probe CI passed; full editor pending | Pinned archive installer; unverified on Intel Mac |
| linux-x64 | Native launch/build configuration | POSIX backend build/probe CI passed; full editor pending | Pinned Zstandard archive installer; unverified |
| linux-arm64 | Native launch/build configuration | POSIX backend build/probe CI passed; full editor pending | Pinned Zstandard archive installer; unverified |
| win32-x64 | Native launch/build configuration | Native handle-read tests passed; broader editor gate remains blocked | Pinned ZIP installer; unverified |
| win32-arm64 | Native launch/build configuration | Native handle-read tests passed; broader editor gate remains blocked | Official ARM64 ZIP verified in metadata; execution unverified |

32-bit, web and remote-host profiles are excluded from this initial target matrix. Listing a target does not certify its OS minimum, hardware suitability or inference support.

## Implemented foundation

```mermaid
flowchart TD
    Install[Platform VSIX with native backend: planned release] --> Choice{AI assets available?}
    Choice -->|Existing local server| Existing[Select installed local model]
    Choice -->|Online setup| Consent[Review identity and terms; confirm downloads]
    Consent --> Download[Pinned platform archive installer; full editor/inference checks pending]
    Choice -->|Offline companion| Audit[Inventory validator implemented]
    Audit --> Import[Stage verified bytes; check local model; activate]
    Existing --> Native[Native source-access and inference validation required]
    Download --> Native
    Import --> Native
```

The extension prefers `native/<target>/thread-backend/thread-backend` (`.exe` on Windows), probes it through the existing bounded JSON protocol, and launches it without interpreter flags. Packages without that asset retain existing Python discovery. Managed macOS installation can call the packaged backend's explicit `install-runtime` command. Windows editor activation remains blocked pending broader document/edit integration; native handle-read CI now passes.

`extensions/vscode/scripts/freeze.py --target <target>` describes a native one-folder build using **already installed** PyInstaller plus the editor dependencies. It refuses a target different from the build host. With explicit owner approval, pinned PyInstaller and zstandard were installed in project-local environments, and two darwin-arm64 native candidates were built and probed. Signing, provenance, notices, platform-specific VSIX verification and executable permissions must be validated before distribution. Current release checking still accepts only the existing POSIX profiles and is not yet a frozen-package release gate.

`offline_bundle.validate_bundle` remains a development inventory audit; its assembler copies explicitly inventoried local inputs into a new companion without downloads/execution. The extension importer additionally requires manifest fields `runtimeExecutable`, `runtimeVersion`, `modelDirectory` and `model`, verifies inventory roles and streams only listed assets. `bundle.json` has `schema: 1`, a matching `target` and an `assets` list. Each regular, unlinked asset requires `path`, `role`, `size`, `sha256`, `source`, `license` and `version`. Roles must include backend, runtime, model and notice. Optional boolean executable flags authorize execute permissions only for backend/runtime assets, including inference helpers. Traversal, duplicate paths, links, missing provenance and changed bytes are rejected. Imported executable/model paths must point into the verified inventory. A signed/trusted release inventory is still required for official distribution; importer approval authorizes the selected native code rather than establishing its safety.

## Distribution constraints

The private native Mac candidates are 15,551,982 bytes (Homebrew Python 3.12) and 9,243,875 bytes (Apple CLT Python 3.9). Both include bundled Python and pass extracted-package protocol/dependency probes. The pinned macOS runtime is about 160 MB. Version 0.2.1 neither supplies model weights nor distributes an official companion; user-provided bundle sizes depend on the user’s assets. Models and runtime distributions require artifact-specific redistribution review and retained notices; license strings in a manifest do not grant redistribution rights. The owner selected MIT for Thread-authored code; third-party distribution terms remain separate and incompletely reviewed.

Windows source access now uses `NtCreateFile` opens relative to retained directory handles, no reparse processing, disk-file/type/link checks and denied write/delete sharing. Native enumeration marks reparse entries excluded. Tests for real junctions and hard links are prepared but skipped on Mac. The editor gate stays closed until native source, document and edit checks pass. POSIX tests cannot establish Windows behavior. Linux builds need an explicit native library/OS baseline. macOS releases need signing/notarization validation. All profiles need clean-machine setup and inference checks; no such cross-platform claim is made here.

## Verified provider metadata and pending native checks

Ollama 0.34.4 metadata from the [official release](https://github.com/ollama/ollama/releases/tag/v0.34.4) records macOS archive 160 MB, Linux x64 1.43 GB, Linux ARM64 1.55 GB, Windows x64 1.46 GB and Windows ARM64 208 MB. `runtime_assets.py` pins exact byte sizes and SHA-256 digests. Only the explicitly approved Mac archive was downloaded in the later local trial; Windows/Linux archives remain metadata-only. ZIP/tar extraction rejects unsafe paths and external links; Linux Zstandard decoding needs the build-only dependency in `requirements-native.txt`. Native packages bundle that decoder, so users do not install it. Current conservative temporary-space checks allow roughly 19 GB for Linux runtime extraction and 11 GB for Windows x64, before model-space checks; these are safety allowances, not measured minimums.

All six pinned metadata entries were independently cross-checked against the release API and its `sha256sum.txt` on 2026-10-11. Mac archive bytes and one local native inference trial now passed; other runtime archive bytes/native behavior remain unverified. Decoder availability is checked before a Linux download; an invalid existing runtime marker/executable identity stops reuse without overwriting the existing installation. Tar extraction checks count/size limits incrementally, including materialized internal-link copies.

The [Ollama license](https://raw.githubusercontent.com/ollama/ollama/v0.34.4/LICENSE) is MIT and requires retaining its notice. Individual runtime distributions include additional dependencies whose notices and redistribution terms still need artifact inspection. User-provided model terms remain separate; Thread publishes no model weights or model-default certification.

The branch-scoped `native-backend.yml` workflow prepares native builds on all six host architectures, tests Windows handle boundaries, probes frozen JSON execution and runs synthetic offline-import tests. It has not been dispatched. Its artifacts retain validation text and notice provenance only; binary redistribution remains gated, and these checks are not inference certification. Local Mac builds and extracted-package checks passed; actual macOS 14 and the other five platform executions remain pending.

## Local portability evidence — 2026-10-11

`artifacts/thread-agent-0.2.0-darwin-arm64-local.vsix` uses the existing Homebrew Python 3.12 and collected Mach-O libraries requiring macOS 26.0. `artifacts/thread-agent-0.2.0-darwin-arm64-local-macos14.vsix` reuses the already installed Apple CLT Python 3.9.6; its collected Mach-O maximum minimum is 14.0. This avoids downloading another interpreter, but Python 3.9 is an experimental portability route rather than the maintained public release baseline. Both candidates executed only on macOS 27.0.1. A maintained Python build on the intended oldest native runner, complete distributor notices and real minimum-OS execution remain release requirements. No Mach-O headers were patched to claim compatibility.

The macOS 14 candidate SHA-256 is `094732f7cd609ef41ad683efdd92382e166615c196d0f92d71b4d2720994dc91`; the macOS 26 candidate is `e7cecf50109355fc43340da56e619934f8936d609ca04e37383e85873d2d9992`. Both remain private previews with public-release readiness false. PyInstaller's generated internal aliases were materialized as regular files before VSIX packaging, allowing the normal secret scanner to run. Native provenance retains found CPython/bootloader notices and records an unresolved Python3 nearest-notice lookup; this is evidence for review, not full redistribution certification.

See [the exact pending download and remote CI proposal](distribution-trial.md). Local assembly fixtures verify copying, hash mismatch cleanup and preservation of existing bundles.

The maintained portable Python 3.12.15 Mac backend records a macOS 11.0 binary minimum and passed local native/package checks. The corrected 92-asset companion passed real offline import/inference. Executable flags for native helpers are included in the reviewed manifest; see [trial evidence and remaining limits](distribution-trial.md#completed-local-trial--2026-10-11).

## Verified native CI snapshot

Native CI for commit `3e436ad` passed all six targets (macOS ARM64/x64, Linux ARM64/x64 and Windows ARM64/x64): native builds, JSON/dependency probes, distribution tests and synthetic offline-import tests. Both Windows runners executed and passed the regular-read/enumeration/limits and hardlink/junction-rejection tests. [Verified run](https://github.com/KrishnendraPrakash/thread/actions/runs/38142298112). These are backend/fixture checks, not full editor, clean-machine or model-inference certification. Windows editor activation remains gated pending broader document/edit integration validation. CI uploaded only six small probe/provenance metadata artifacts; no runtime, model or backend binary was redistributed.
