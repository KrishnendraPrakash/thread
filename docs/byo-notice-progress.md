# BYO 0.2.1 dependency notice progress

Local preparation against the six-target run 38243563529, exact head 50eec6cd8ad18ca69853f14ba48666801480f57e. These source hashes came from actual BINARY/EXTENSION inventories; local replay of their records is a mapping check, not a new native build. No gate has been marked passed.

## Closed text/mapping gaps

CPython core license text only is now bound to the following exact source images. The full official [3.12.10 LICENSE](https://raw.githubusercontent.com/python/cpython/v3.12.10/LICENSE) and [3.12.15 LICENSE](https://raw.githubusercontent.com/python/cpython/v3.12.15/LICENSE) were retrieved as text and both independently hash to `3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf`, matching the CPython notice already retained in all four packages. Original terms/copyrights are unchanged. Bindings retain run, job, commit, version, source image and notice hashes; changed or unknown profiles receive no mapping.

| Target | CPython | Source image SHA-256 |
| --- | --- | --- |
| darwin-arm64 | 3.12.10 | `14e61fb22a897d238248dfd8fe3b472b4541338c293368b4747803055b8bb3aa` |
| darwin-x64 | 3.12.10 | `14e61fb22a897d238248dfd8fe3b472b4541338c293368b4747803055b8bb3aa` |
| linux-arm64 | 3.12.15 | `3b7bb403d2d32495309dfb412559ea3a3b20daaa4522ae64b4fa2c639aa8179d` |
| linux-x64 | 3.12.15 | `210b4c2f6be72f3fc739a0479cda75f93d268a0ca6f6a5e40f7c6d64579aef6d` |

This closes the missing `Python` core-license mapping for both Mac targets and `libpython3.12.so.1.0` core-license mapping for both Linux targets. It does not cover incorporated third-party code, statically linked dependencies, distribution-specific modifications, or complete redistribution terms. The existing portable Mac 3.12.15 static profile is not applied to these images. Windows CPython’s retained license has a different hash and is deliberately not substituted with this core text.

The collector also rejects DLL/EXE/native extensions, binary magic, NUL-containing files and non-UTF-8 data as notice text. The previous Windows ARM64 receipt incorrectly included `LicenseManagerApi.dll`, `LicenseManagerShellext.exe`, `LicenseManagerSvc.dll` and `licenseprotection.dll` as ucrtbase notices. Those images are not license documents. Future builds will exclude them; previous package receipts are not silently rewritten or declared clean. Adjacent text discovery remains a candidate, not proof of component attribution.

## Inputs still unavailable

- Mac x64/ARM64: exact bundled OpenSSL version/build provenance and LICENSE/AUTHORS/NOTICE requirements; python.org distribution build recipe/patch and incorporated static-component notices for the universal CPython image. Recorded hashes alone do not identify those versions.
- Linux x64/ARM64: source distribution/package ownership, exact version and retained distribution copyright/source-access notices for libcrypto/libssl, liblzma, libbz2, libz, libuuid and libffi; CPython build/static dependency attribution. An upstream license with a guessed version cannot close these mappings.
- Windows x64/ARM64: actual origins and versions of UCRT and every API-set DLL (39 ARM64 missing API-set entries, 42 x64 API-set entries plus ucrtbase in the historical report), applicable SDK/runtime redistribution rights and required text; original CPython distribution license contents and embedded dependencies. ARM64 ucrtbase attribution must be reopened because the prior collector used executable files as evidence. The reported counts are diagnostic, not complete dependency closure.
- Across targets: incorporated-code notices and bootloader/package data coverage must be checked against exact distributions. The TOC census and nearest-name collector do not constitute an exhaustive license inventory.

## One focused next CI proposal

Propose one six-target notice-provenance pass in the existing temporary BYO package workflow, subject to owner authorization; no run or workflow change was made here. On the same build inputs, retain sanitized source-root classification and hashes for every TOC image, exact setup-python distribution/build metadata, Linux dpkg package owner/version plus `/usr/share/doc/<package>/copyright` bytes, Mac python.org included license/build/embedded OpenSSL metadata, and Windows DLL version/origin plus applicable SDK/runtime license and redistributable-list text. Include the actual distribution license bytes and the revised notice output. Do not acquire models/Ollama, export native images, change identities/signatures, activate release workflows or promote gates. Unresolved origins must remain explicit. This pass supplies the absent evidence for subsequent exact mappings; it is not an automatic promise to finish the gate if the distributions omit required inputs.

## Checks performed

Six notice behavior tests passed, including executable-name rejection, exact source/target/version matching, unknown-profile rejection and tampered-notice failure. The four mapping results were replayed against existing six-target receipts (four matched, both Windows intentionally unmatched). Ruff lint/format and diff whitespace checks passed. No runtime/model binary was downloaded or executed, remote workflow run, commit or push performed. The production Windows guard and all release policy values remain unchanged.

## Authorized provenance follow-up

The owner approved the focused six-platform provenance pass. It now retains Linux dpkg origin/version/copyright and referenced common-license texts, Windows existing SDK redist hash matches and available license candidates, Python distribution license/build inputs and official version-pinned incorporated-software license documentation. Mac OpenSSL 3.0.16 LICENSE/AUTHORS are mapped only to the recorded source hashes and require the observed runtime version to agree. All sources retain their original text. Outcomes will be recorded after the actual CI runs. No SDK acquisition or acceptance, model/runtime acquisition beyond existing build tooling, signing change or artifact export is added.
