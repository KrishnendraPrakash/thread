# Local native packaging inventory preparation

The initial notice review kept all six release gates pending. Owner-approved BYO 0.2.1 now makes only the exact-scope official-companion gate not applicable; the other five remain pending. It adds exact native source/payload hashing to notice collection, including PyInstaller EXTENSION entries previously omitted from the binary census. Both source and packaged digests are retained because PyInstaller can rewrite native images. The exported provenance excludes absolute build-source paths. The census does not grant redistribution approval or cover generated bootloader/bytecode/data by itself.

A private copy of the existing approved darwin-arm64 backend was refreshed using the installed approved CPython 3.12.15/PyInstaller 6.22.3 build environment. Only plaintext notices/provenance changed: all other file bytes and modes are identical to the source payload. No packaged native image was built, executed or signed. Nine static notices and exact pathspec source access are retained without changing their legal texts. The source libpython hash matches the existing portable profile; both zstandard source extension hashes match wheel RECORD entries. Their rewritten payload hashes are recorded separately. The copy contains 40 files and three TOC native-image entries.

This is an existing-backend notice review, not a final release candidate: the compiled installer predates PR #7 and requires a final native rebuild. Empty `missing` means available notice searches succeeded; complete_distribution_review remains false and does not establish all binary dependency rights. No model/runtime assets are included or acquired, and the owner-selected BYO scope excludes official model redistribution.

## Actual six-target information

| Target | Available locally | Remaining source/notice gap |
| --- | --- | --- |
| darwin-arm64 | Existing payload, exact build TOC and source binaries; refreshed notices | Full component/distribution exceptions review and final code rebuild; signing and release acceptance still pending |
| win32-x64 | 89-file, 23,771,376-byte hash inventory from real run 38218047751 | Actual payload/TOC, source DLL hashes and exact distribution/VC/UCRT notice mapping unavailable |
| linux-x64 | 78-file, 77,905,275-byte hash inventory from that run | Actual payload/TOC, exact source-library/version/static dependency and notice mapping unavailable |
| darwin-x64 | Earlier native CI result | Actual payload/TOC/source hashes and distribution-specific notice inventory unavailable |
| linux-arm64 | Earlier native CI result | Actual payload/TOC/source hashes and distribution-specific notice inventory unavailable |
| win32-arm64 | Earlier native CI result | Actual payload/TOC/source hashes and distribution-specific notice inventory unavailable |

The five absent target payloads cannot be reconstructed from hashes. Approved acquisition or native target builds are required before their actual dependencies can be reviewed. Do not copy the portable Mac profile onto another target. No extra security-reporting gate or setting is added.

## Reproduce the completed local refresh

The local review directory is `build/local-packaging-review/`. Its refresh.py uses only the approved existing bundle and build TOC, verifies the input manifest/assets, copies the existing native payload and regenerates notices with the current collector. Invoke it with the existing `build/native-portable-venv/bin/python` and a new output directory; it rejects changed inputs/environments or an existing output. It never invokes PyInstaller, a signer, Ollama or a model. `notice-refresh-inputs.json` records exact input hashes and all output hashes; `six-target-inventory-gaps.json` and captured x64 inventories retain the concrete gap evidence. These are local ignored build files, not a production companion recipe or public release artifacts.

Acceptance fixtures cover the actual EXTENSION omission, rewritten source/payload identity, private-path omission, unsafe destinations, missing/conflicting/ambiguous payloads and parent-link containment. No runtime or license-completeness claim follows from those fixtures.


The approved build-only CI now creates a temporary model-free VSIX on each of the six standard hosted targets, probes its actual native backend, verifies BYO package identity/content and prints exact native-file/source/notice inventory metadata. Packages are deleted on the runner; no artifacts, model/Ollama acquisitions, OIDC or publishing are involved. This does not advance ordinary-user, real-inference, complete licensing or signing gates.


The later six-host BYO package check supplies current source/payload/file inventory metadata for every target; actual images were discarded. See [six-target receipts](byo-package-checks.md). This advances inventory availability only; complete license mappings and the five production gates remain pending.
