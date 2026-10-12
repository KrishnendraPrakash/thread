# Thread licensing and third-party notices

The owner approved the MIT license for Thread-authored code and documentation on 2026-10-11. The [OSI MIT template](https://opensource.org/license/mit) is the basis for the root [LICENSE](../LICENSE), which contains the grant and copyright attribution. Python and extension metadata record MIT; the prepared next preview is 0.2.1. This decision does not relicense third-party code, models or runtime distributions, and does not authorize publication.

Repository history records contributions under `Krishnendra Prakash` and `KrishnendraPrakash`, the owner's two author spellings. No separate external contributor was identified in that history; commit attribution alone is not proof of ownership of every included component. Generated dependency/runtime files remain governed by their original copyright and license notices.

## Inspected local notice identities

| Component | Inspected terms | Where retained |
| --- | --- | --- |
| pathspec 0.12.1 | Mozilla Public License 2.0 | Installed distribution's LICENSE; copied dependency metadata in Python/native packages |
| pypdf 6.19.0 | BSD-3-Clause | Installed distribution's licenses/LICENSE; copied dependency metadata |
| zstandard Python wrapper 0.25.0 | BSD-3-Clause | Installed distribution's licenses/LICENSE; native dependency metadata |
| Native Zstandard 1.5.7 | BSD-3-Clause, separate from wrapper | extensions/vscode/notices/zstd-1.5.7-LICENSE and native notices |
| PyInstaller 6.22.3 | GPL with bootloader distribution exception | Installed COPYING.txt; native notice collection |
| CPython / portable Python | PSF and distribution-specific third-party terms | Portable archive LICENSE.txt and native notice provenance; complete binary dependency inventory remains open |
| Ollama 0.34.4 | MIT plus dependencies' separate notices | Existing private companion's Ollama and runtime dependency notices |
| Qwen2.5-Coder 0.5B trial model | Apache-2.0 | Exact acquired model license layer and existing private companion notice |

These identities were read from installed dependency metadata/license files and previously approved trial assets, not inferred from Thread's MIT grant. The table is not a complete distribution license inventory. The macOS runtime additionally retains GO, llama.cpp/vendor, MLX, MLX_C, cpp-httplib, DLPack, fmt, picojson and XGrammar notices. Existing files are preserved byte-for-byte.

The install-only portable Python archive does not supply the full binary dependency license inventory; native OpenSSL 3.5.9 terms and complete static dependency notices remain unverified. Do not substitute an unrelated Homebrew OpenSSL notice or mark complete_third_party_notices passed. Signing, platform/editor/inference/clean-machine and offline companion distribution review remain independent pending gates.

The root MIT license must travel with Thread-authored distribution files; separate third-party license/copyright notices must remain in their corresponding packages. Existing package builders copy the selected root license and retain dependency notices. A passing project_license gate means the owner's project decision is recorded, not that every redistributable binary/model is certified.

## Draft follow-up: source-bound static notice retention

The next draft adds exact upstream notice/attribution texts and a SHA-bound profile for the existing portable darwin-arm64 CPython 3.12.15 library. Its verified archive SHA is 233f8e15255b3e1d1fd47ea5dd5230dfed803f371138e896e54d98c60ae19f6f; source library SHA is f684eb35620b1af1202566e43f2bc94db61f315858fff02b711faa0ea7d2b974. Portable dependency metadata is pinned to python-build-standalone commit ccc07c40c2731bfb459c119f2388f65a5a470de6, OpenSSL 3.5.9 to commit 45e844fa2a14ec92d146bd8f5778ac130b6625fb, and CPython's unchanged license to release commit e848e4b09ca4bc67c0041c9ce7526dae471d4c36.

The native collector now retains nine matching texts, records their sources/digests, explicitly maps CPython, and clears only its proven libpython mapping gap. Other builds are flagged for distribution-specific static review. Notice regeneration clears only the generated notice directory to prevent stale attribution on repeated builds. Source notices are never silently modified or relicensed. Full release review is still false: source-specific exceptions, distribution modifications, other targets and signing need separate evidence.
