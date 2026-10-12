# Verified additional native notices

`zstd-1.5.7-LICENSE` retains the upstream Zstandard BSD license, obtained without a new download from the already installed Homebrew zstd 1.5.7_1 distribution. The approved zstandard 0.25.0 build environment reports its embedded native ZSTD_VERSION as 1.5.7. SHA-256: `7055266497633c9025b777c78eb7235af13922117480ed5c674677adc381c9d8`.

The Python wrapper's own BSD notice is separately included in its distribution metadata. The native build copies this additional library notice only when the embedded library version matches; otherwise provenance records the missing notice. This file does not grant a license for Thread, whose Thread-authored code now uses the owner-approved MIT license; third-party components keep their own terms.

The approved Ollama Mac archive already supplies GO_LICENSE, LLAMA_CPP_LICENSE, LLAMA_CPP_VENDORS_LICENSE, MLX_LICENSE, MLX_C_LICENSE, CPP_HTTPLIB_LICENSE, DLPACK_LICENSE, FMT_LICENSE, PICOJSON_LICENSE, XGRAMMAR_LICENSE and XGRAMMAR_NOTICE. The private companion retains all of these plus the previously acquired Ollama MIT text and exact Qwen Apache-2.0 license layer.

The portable install-only Python archive supplies CPython LICENSE.txt but lacks the full build archive's dependency license inventory. Exact OpenSSL 3.5.9 texts are retained for the matched portable Mac profile below; full static dependency redistribution review remains open. Do not substitute notices from a different installed OpenSSL build or claim complete redistribution review. No new download was made for this notice review.

## Exact portable-Python static notice snapshot

`portable-darwin-arm64-20261009/profile.json` binds CPython 3.12.15 and seven identified static dependencies to the source-library SHA-256 extracted from the already verified portable archive. It retains CPython, OpenSSL 3.5.9 LICENSE/AUTHORS, bzip2, expat, libffi, liblzma, mpdecimal and SQLite texts from official pinned sources. Build-recipe versions are recorded separately from runtime observations; the original texts/copyrights are unchanged. The source snapshot is excluded from VSIX roots; matched builds copy verified notices into their native notice directory. Unknown target/version/library hashes receive no misleading attribution and remain flagged.

This addresses missing notice texts and CPython mapping for that exact private Mac build. Full component-specific attribution/modification review and other distribution profiles remain open; complete_distribution_review is false and the global production gate remains pending. Thread's MIT grant does not override any dependency's terms. No OpenSSL/other binary or model was downloaded.

`pathspec-0.12.1-SOURCE.txt` records exact upstream MPL-2.0 Source Code Form access and the official PyPI archive digest. Native notice collection includes it only for the matching installed version.

`cpython-core-ci/bindings.json` binds the unchanged official CPython core LICENSE to four exact Mac/Linux CI source-library hashes. It does not provide third-party/static dependency or distribution-wide approval. See [notice progress](../../../docs/byo-notice-progress.md). Unknown profiles, including Windows, are not covered.

`openssl-python-ci` binds official pinned OpenSSL 3.0.16 LICENSE/AUTHORS to exact Mac/Windows source images and requires the build runtime version to agree. `ubuntu-ci` retains fourteen exact installed shared-library distribution copyright/source-access mappings, including every referenced license available in the provenance pass. Windows core mappings retain its original combined license, including Microsoft restrictions; they do not approve Microsoft runtime redistribution. SDK/system image mismatches remain auditable even where Windows 10+ packages use the OS components instead.
