# Runtime integration diagnosis, 2026-10-12

Draft PR #7 preserves the production Windows guard and starter models. Nothing in this diagnosis executes Ollama or acquires model blobs.

## Exact archive evidence

[Metadata-only run 38215230670](https://github.com/KrishnendraPrakash/thread/actions/runs/38215230670) passed both standard temporary runners at commit 72786df. It verified the approved v0.34.4 archive sizes/hashes, read manifests and bounded license text without extracting/executing payloads, and deleted its owned archives. No artifacts were exported. It inspected 87 Windows ZIP entries and 65 Linux tar entries. CLI-rendered combined logs omitted the long JSON records; direct textual job logs retained them.

The main Windows archive contains CUDNN_LICENSE.txt, MLX_LICENSE and MLX_C_LICENSE, but no cuDNN DLL or MLX backend directory. The initial filename-only audit therefore stopped on notices rather than an additional proprietary runtime. These notices remain intact. Only exact path/hash matches for the inspected permissive notices are accepted by the revised diagnostic audit; changed notices and actual cuDNN/MLX binaries still stop.

- Windows CUDNN_LICENSE.txt is a 1,169-byte MIT-style NVIDIA 2020 notice, SHA-256 b6fe452605fe29245f0cbafa724b42df94a5e170bedb9d45bc9cfaa4883ad907. Its text grants permission subject to retention of copyright/permission notices and contains no SDK acceptance mechanism. It is not the proprietary SDK EULA and does not establish an installed cuDNN version.
- [MLX revision 59d600b5e64c238427d0f8d897ab7c682ef4d3d2](https://github.com/ml-explore/mlx/blob/59d600b5e64c238427d0f8d897ab7c682ef4d3d2/LICENSE) and [MLX-C revision ebc88f10caa1b625e6b581437a8dea6df8a70085](https://github.com/ml-explore/mlx-c/blob/ebc88f10caa1b625e6b581437a8dea6df8a70085/LICENSE) are exact [Ollama source pins](https://github.com/ollama/ollama/tree/v0.34.4). Their MIT texts match Linux bytes and Windows CRLF variants. Neither introduces a separate SDK agreement or explicit acceptance prompt; notice retention remains required.
- The optional MLX Windows build uses cuDNN 9.18.1.3 for CUDA 13 in [official release configuration](https://github.com/ollama/ollama/blob/v0.34.4/.github/workflows/release.yaml). [Official packaging](https://github.com/ollama/ollama/blob/v0.34.4/scripts/build_windows.ps1) moves MLX backend directories into a separate optional ZIP. That optional ZIP was not requested/downloaded. If a future payload includes that SDK, obtain a separate bounded approval to download/install/use it under the [cuDNN 9.18.1 SDK agreement](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.18.1/reference/eula.html), which requires acceptance before download/install/use. Do not infer approval from existing CUDA approval or permissive notices.
- The Linux Dockerfile selects CUDA 12.8 and 13.0 toolkit packages. Its cuBLAS library filename versions are component versions, not evidence of a different toolkit agreement. Existing CUDA approvals remain the scope; this diagnosis does not grant redistribution approval or complete legal review.

## Linux extraction failure and narrow fix

The first unresolved member in the verified archive is a symbolic link, type 2: lib/ollama/libggml-base.so -> libggml-base.so.0. Its target is another declared symbolic link -> libggml-base.so.0.24.0, which is a regular archive file. Similar two-step internal chains exist for ggml, llama-common, llama and mtmd. The previous single-pass materialization reached the first link before its target copy existed.

The fix revisits deferred internal file links for at most 64 passes and materializes only regular independent copies. It never creates filesystem symlinks/hardlinks. Every resolved target must remain inside the extraction root; absolute/backslash/escaping targets, cycles, missing files, directory targets, unsupported entry types and duplicates still reject. Original archive counts, decompression/extraction bounds and cumulative copied-byte limits remain. No archive bypass or direct execution path was added.

Synthetic regression tests cover the observed forward chain, independent copies, cycles, missing/directory/absolute/escaping targets, cumulative copy bytes and bounded depth. 120 Python tests passed with seven platform skips; Ruff and diff checks passed. Real installation/inference has not been rerun after these changes. The earlier integration run installed/extracted Windows but executed neither platform; Linux extraction failed. Full legal, clean-machine, model-quality and release gates remain open.


Real integration retries exposed a Windows CI cleanup defect: the PowerShell ownership query returned system-process paths, so prior Windows cleanup attempts cannot establish owned-only termination. Affected temporary runs were requested force-stopped. Cleanup now treats process-query output solely as metadata and independently filters exact dedicated-directory paths in Node, rejects ambiguous identities, and rechecks executable/PID ownership before direct termination. Portable regressions exclude system paths, sibling prefixes, traversal, empty roots and duplicate IDs. Linux integration passed in multiple runs; one intervening zero-VRAM assertion failed and remains an unresolved inconsistency. No zero-VRAM check was weakened. Model outputs on both platforms were rejected separately from CPU completion.


The real CPU integration harness now explicitly selects Ollama’s documented `OLLAMA_LLM_LIBRARY=cpu`, disables Vulkan/integrated GPU discovery and masks accelerator visibility only for the owned test runtime child. This addresses a runner residency discrepancy without changing production settings or the captured structured request. Zero-VRAM assertions remain mandatory before/after the production call. Windows owned-process classification regressions remain enabled before acquisition.


## Final real integration result

[Run 38218047751](https://github.com/KrishnendraPrakash/thread/actions/runs/38218047751) completed successfully on standard windows-2025 and ubuntu-22.04 at exact tested head d003dbfd403e079c6f9ea196f74d9ebd406c1836. Each job retained the 45-minute bound, disk preflight, exact approved main-archive/runtime/model identities, no optional MLX/cuDNN payloads, and vendor audit before execution.

| Evidence | Windows x64 | Linux x64 |
| --- | --- | --- |
| Actual native installer / runtime version | Passed / Ollama 0.34.4 | Passed / Ollama 0.34.4 |
| Real model / quantization | Qwen2.5-Coder 0.5B / Q4_K_M | Qwen2.5-Coder 0.5B / Q4_K_M |
| Bounded CPU completion | READY; 10 generated tokens; stop | READY; 10 generated tokens; stop |
| Reported VRAM before/after production call | 0 / 0 bytes | 0 / 0 bytes |
| Unchanged production structured request | Captured; 119 tokens; stop | Captured; 103 tokens; stop |
| Backend acceptance | Rejected: invalid source reference or text | Rejected: edits prohibited in ask mode |
| Synthetic source preservation | Passed | Passed |
| Independently verified owned-process cleanup | Zero remaining | Zero remaining |

The real runtime path passed its integration checks; the production task did not produce an accepted answer on either platform. Both responses included proposed edits and contradictory statements about the add function, and Windows also invented source IDs. This is retained model-failure evidence, not a model-quality pass. The production schema, prompt and options (context 16384, output cap 3072) were forwarded unchanged; test-only CPU-library environment controls do not change shipped settings.

Earlier Windows cleanup attempts returned system paths from an overbroad query and are invalid owned-only evidence. The affected four runs (38216011621, 38216413084, 38216778581, 38217103078) reached terminal cancelled state. The independent Node path classifier, pre-termination identity recheck and negative ownership regressions correct that defect; the final run required no post-stop termination because its owned-process inventory was empty. One earlier Linux attempt reported nonzero VRAM and correctly stopped; explicit documented CPU-library selection plus disabled accelerator discovery resolved the final integration check without weakening assertions.

Zero artifacts were exported. Large assets ran only on temporary GitHub runners. No Mac runtime/model acquisition, driver installation, paid capacity, access change, Windows guard removal, starter-model change, merge, publication or release activation occurred. This is synthetic-input real runtime/backend evidence on development runners, not ordinary-user/clean-machine editor certification, Windows ARM validation, external-network-denial certification, complete redistribution review or a benchmark. Full release/model-quality gates remain open.


Cleanup incident clarification: in cancelled run 38217103078 (head d5885b0), the pre-termination record listed unowned lsass.exe PID 1008 first, followed by svchost.exe PID 716. The exact sequential cleanup code reached PID 716 and logged its failed taskkill, with no failure logged for PID 1008. This establishes by control flow that the unowned PID 1008 termination command returned success; it was not merely a query. Successful stdout and an independent post-kill probe were not retained, so the actual process exit and full OS impact cannot be independently reconstructed. It would be incorrect to claim no unowned processes were terminated. The impact was confined to disposable Windows CI runners, whose teardown stalled; affected runs reached terminal cancelled state. Final corrected runs independently enforce ownership and report zero remaining owned processes. No user Mac process was involved.
