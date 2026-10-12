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

## Actual first provenance pass

Run 38247810107 passed all six targets at 9d9516e388a0be96b7ffe514a95387b22283b6fb. Both Mac builds observed OpenSSL 3.0.16, matching the pinned official Python build recipe and exact crypto/ssl source hashes; their three named notice gaps are resolved by core and OpenSSL text mappings. Linux collected all seven shared-library package origins/copyright files on each architecture; the follow-up bindings retain those exact source hashes, original full copyright and referenced common-license texts, package/source versions and access URLs. This resolves fourteen named shared-library notice/source-text attribution gaps, not all distribution terms.

Windows x64 collected SDK 10.0.26100.0 terms and 43 corresponding redist candidates: none of the packaged Windows OS image hashes matched the SDK redist images. The SDK terms impose distributor/end-user obligations; no terms were accepted and no SDK redistributable was substituted. The follow-up package uses the OS-provided API-set/UCRT on Windows 10+, omitting only system-origin images from those named families while retaining the original hashes for audit and requiring the extracted actual native protocol test. Other vendor libraries remain packaged. This avoids distributing those OS images rather than assigning them guessed rights. The production Windows guard remains in place. See Microsoft's [UCRT deployment guidance](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment?view=msvc-170).

The incorporated CPython license documentation is retained, but the complete build/compiler/static attribution review is still pending; no claim that the entire legal gate is closed follows from these mappings. Linux copyright texts identify shared OpenSSL under Apache-2.0, bzip2 under its BSD variant, libffi under MIT-like terms, liblzma upstream code as public domain with toolchain caveats, zlib under zlib terms and libuuid sources under BSD-3-Clause; the full mixed source-package copyright files are preserved, including their other sections. These labels describe the identified source components and do not blanket-relicense every compiler/header or distro patch contribution.

Windows ARM64 also completed: SDK 10.0.22621.0 terms were available; none of its 40 packaged OS-family source images matched SDK redistributables. The original Windows CPython combined LICENSE text is now retained unchanged and hash-bound to both Python DLLs on both architectures; exact OpenSSL 3.0.16 notices cover crypto/ssl on Windows as well. The combined license expressly preserves Microsoft distribution/end-user obligations. Residual Microsoft vendor runtime images are `vcruntime140.dll` on ARM64 and `vcruntime140.dll` plus `vcruntime140_1.dll` on x64. Their applicable redistribution/distributor/end-user requirements are not silently accepted under this task; they remain a concrete release blocker even after OS API-set/UCRT copies are omitted. No new SDK or binary acquisition is needed for the evidence obtained so far.

## Verification correction and bounded source resolution

Run 38248857822 passed all six targets at 311c490f4645b2de487c741d4da9424883b04478; Mac named gaps are empty and Linux has only the unmatched distribution-specific static-profile flag. It verified the new source/notice bindings. Windows still omitted zero images because the initial rule recognized only System32/SysWOW64 roots; passing a protocol check did not resolve those 83 image origins. The follow-up records sanitized Windows/program-files/toolcache relative origins, recognizes only the official Microsoft Windows component-store naming pattern inside SystemRoot, or requires exact source-byte correspondence with an installed system image. Unknown/outside copies remain packaged and unresolved; a filename or version alone never removes them. Original TOC/image hashes remain in the audit report, and actual package probes are required after any omissions. Notice text resolution is now restricted to its declared source root, allowing only contained links. The global notice gate remains pending.
