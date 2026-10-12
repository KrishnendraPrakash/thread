# Six-target BYO package proof

[Run 38243563529](https://github.com/KrishnendraPrakash/thread/actions/runs/38243563529) passed all six targets at exact head 50eec6cd8ad18ca69853f14ba48666801480f57e. Standard free runners built native backends, tested source boundaries, packaged temporary BYO VSIXs, probed the extracted actual native protocol, verified model-free identity/license/content, and passed synthetic offline import and blocked-model-pull tests. Each temporary VSIX was removed on its runner. No artifact, model/Ollama acquisition, OIDC, publisher action or signing identity was used. Existing build signatures are not consumer-trust evidence.

| Target | Temporary VSIX bytes | Native file inventory | BINARY/EXTENSION source bindings |
| --- | ---: | ---: | ---: |
| darwin-arm64 | 17190930 | 80 | 50 |
| darwin-x64 | 18416314 | 80 | 50 |
| linux-arm64 | 27501112 | 78 | 54 |
| linux-x64 | 29160445 | 78 | 54 |
| win32-arm64 | 10924050 | 89 | 61 |
| win32-x64 | 10980118 | 89 | 65 |

Exact per-file/package hashes and notice provenance were retained as text in job logs. Local review JSON receipts are in build/local-packaging-review/; they contain metadata only, not candidate images. The first run 38242967443 passed both Mac/Linux architectures but failed Windows on CP1252 decoding of UTF-8 TypeScript. Explicit UTF-8 inputs plus a Unicode regression resolved the retry. No extraction or gate was weakened.

This supplies actual current source/payload inventory metadata across six targets, replacing the prior absence of collected source bindings. Exact distribution/component license mapping, ordinary-user/clean-machine execution, real editor/model workflows, native signing/notarization and Windows activation are still unproven. Notice collectors explicitly retain complete_distribution_review false. All five material release gates remain pending; the exact BYO 0.2.1 companion gate remains not applicable. Production Windows guard and inactive release workflows were preserved.

Concrete notice gaps in this build profile: both Mac targets (CPython 3.12.10) flag Python and libcrypto/libssl notices; both Linux targets (3.12.15) flag libpython, OpenSSL, lzma, bzip2, zlib, uuid, libffi and unmatched distribution-specific static coverage; Windows targets (3.12.10) flag UCRT/API-set DLL source/notice attribution and unmatched static coverage. Those are collector/provenance gaps requiring exact distribution mapping, not proof that redistribution is prohibited or licensed. The portable Mac 3.12.15 profile does not match these other library hashes.
