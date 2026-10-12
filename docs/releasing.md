# Release readiness

The source repository is published at [KrishnendraPrakash/thread](https://github.com/KrishnendraPrakash/thread). The user has now requested public VS Code distribution. Preview packaging and a manual build workflow are configured; the owner selected MIT and next preview 0.2.1; new package publication still requires validated production artifacts and an authorized authenticated upload. See [the publishing guide](publishing.md). This authorization does not mean the M6 general-release gates have passed.

Before publishing a general release (the experimental preview remains explicitly limited):

- The owner selected MIT for Thread-authored code/documentation; the next preview version is 0.2.1. Preserve all independent third-party licenses and complete native notice review.
- Finish the intended runtime milestone and record acceptance outcomes separately from packaging checks.
- Pin a tested model artifact/quantization/runtime and retain relevant model/dependency notices.
- Verify installation from a fresh checkout and a built distribution on declared supported platforms.
- Document local model setup, memory/data locations, action policy, and optional provider credentials.
- Extend the initial uv.lock/update policy to future runtime dependencies and record build tools and measured compatibility for releases.
- Review distribution contents to exclude secrets, private data, model weights, local databases, held-out answers, and development artifacts.
- Define a private security-reporting channel before enabling public reports; there is no maintainer contact or response SLA configured yet.

CI builds/checks packages but does not publish them, download models, execute paid APIs or run agent benchmarks. The preview distribution records actual compatibility and known limits rather than claiming the general-release gates passed.


## Owner-approved BYO scope for 0.2.1 (2026-10-12)

The owner selected user-supplied models, avoiding bundled Llama redistribution and explicitly replacing the ready-to-use offline companion plan. Official artifacts are six native VSIXs for Windows/macOS/Linux ARM64/x64, with no model weights or companion ZIPs. Existing installed-model selection, runtime-only confirmed acquisition and user-provided complete offline import remain. The exact-scope companion gate is not applicable; five gates remain pending: native notices, all-target editor/inference, Windows activation, clean-machine setup and signing. No model license approval or full release certification is inferred from BYO. Conditional Marketplace deployment remains blocked until material gates and exact artifacts pass; the production workflows remain inactive.
