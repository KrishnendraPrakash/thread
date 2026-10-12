# Source-only VSIX upload automation

The owner-approved immediate release is universal Thread 0.2.1, in the existing stable Marketplace channel with its experimental preview label. Users still install Python 3.9+. This automates the manual package/upload path, without acquiring or distributing a Python runtime, Ollama or models. Windows activation remains guarded. The six-native packaging effort is preserved separately and is not promoted by this workflow.

The public 0.2.0 VSIX matches the existing local file SHA-256 `b061ece70d40327d469e324487b2a8d8fdedb99da90757f9a889825ce53f2032` (501,273 bytes). It has zero native images/models, readable pathspec/pypdf sources and their licenses, but declares UNLICENSED and omits the project LICENSE. The new package uses the already approved MIT declaration/text. The old package has a preview label but no Marketplace pre-release property; those are different concepts.

## Source baseline and behavior delta

Build from current reviewed main after PR #9, not historical 77c8f9f. This retains current source/editor, filesystem, cancellation and offline-import fixes. Compared with published 0.2.0, installed-model selection is retained but automatic model pulling is removed; acquisition is runtime-only and models are user-supplied. User-provided complete offline import is available with its existing integrity, approval and rollback boundaries. No 0.2.0 behavioral equivalence or new model benchmark is claimed.

The staged package marker selects the source profile. Optional runtime acquisition remains Apple Silicon macOS 14+ only, avoiding the Linux Zstandard decoder that belongs in a native backend. Existing installed Ollama remains the recommended path. Source staging is an explicit allowlist of compiled editor JavaScript, media/public documents, Thread Python source, bridge/installer source, pure pathspec 0.12.1 and pypdf 6.19.0, and their notices. Generated native/model/notices directories never enter the stage. Installer bookkeeping/private URLs and bytecode are excluded.

## Build and dry-run

Use a clean committed checkout with existing Node development dependencies and the exact pure-Python package versions installed. No PyInstaller/native build requirement is added.

```sh
python extensions/vscode/scripts/source_package.py build --output build/source-candidate
python extensions/vscode/scripts/source_upload.py --package build/source-candidate/thread-agent-0.2.1-source.vsix --commit COMMIT --sha256 SHA256
```

The build compiles current TypeScript, stages in an owned temporary directory, packages once, canonicalizes ZIP order/timestamps/permissions using the source commit time, validates archive/identity/version/universal target/stable channel/preview label/external Python/MIT/independent notices, and probes the actual extracted source backend without a model. It refuses dirty source or overwrite of an existing candidate. Hashes still must be checked; canonical ZIP metadata alone is not a cross-environment reproducibility certificate.

The default upload command is a local plan: no authentication, Marketplace query, upload or ledger write. Explicit execution fails outside the protected main dispatch context. `--packagePath` uploads the built existing file; the publishing job does not recompile/repackage it.

## Protected workflow and artifact destinations

`.github/workflows/source-vsix-release.yml` runs nonpublishing source/package checks on the preparation branch and PR. These checks log candidate receipts but retain no binary artifacts. A manual dispatch defaults to `publish=false` and `check_access=false`. Explicit dispatch retains the VSIX and receipt only in this repository's GitHub Actions artifact `thread-source-candidate-RUN-ATTEMPT` for seven days; it is not a Marketplace release or public download asset.

After review/merge, dispatch on main with `publish=false`, `check_access=true` to build/review the candidate and, after the existing owner environment approval, check the existing OIDC identity's publisher rights using read-only `vsce verify-pat --azure-credential Krishnendra`. No role or credential is created. Existing identity lookup/Members evidence corroborates setup, but this direct check establishes the permission of the actual publishing identity. The developer's local Azure user is a different identity.

Only a subsequent explicit main dispatch with `publish=true` enables the upload step. Supply the reviewed main candidate SHA-256 to stop before authentication if bytes differ. The existing `marketplace-publish` environment has owner review and main-only deployment rules; no access policy changes are made. The job validates the exact downloaded candidate before OIDC, checks Contributor rights, and uploads the same verified bytes in the stable channel. It then verifies exact publisher/version/universal channel and the Marketplace VSIX SHA-256. The owner approves the concrete candidate after the build summary is available.

The per-release ledger records uploading/uploaded/verified/uncertain states. Upload receipts are retained in this repository for 30 days. If upload or network outcome is uncertain, do not blindly rerun: inspect the preserved receipt and reconcile the exact public listing first. A rerun that finds an existing version without its ledger fails closed rather than overwrite/re-upload. Automated ledger-restoration across attempts is not implemented in this narrow workflow.

No merge or publication is performed by implementing this workflow. The actual release requires reviewed main code, successful package checks, a fresh version slot, successful OIDC publisher-rights check and owner protected-environment approval. Native legal/signing/editor certification is not silently waived; it applies to its separate future native distribution.

See [workflow diagram](source-vsix-upload.mmd).
