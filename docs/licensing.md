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
