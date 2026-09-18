# Release readiness

No release or publication is configured. The user has authorized the local scaffold, not deployment or registry publication.

Before publishing a usable release:

- Select the public repository URL, package name, and repository license. No license grant or license classifier is invented by the scaffold.
- Finish the intended runtime milestone and record acceptance outcomes separately from packaging checks.
- Pin a tested model artifact/quantization/runtime and retain relevant model/dependency notices.
- Verify installation from a fresh checkout and a built distribution on declared supported platforms.
- Document local model setup, memory/data locations, action policy, and optional provider credentials.
- Extend the initial uv.lock/update policy to future runtime dependencies and record build tools and measured compatibility for releases.
- Review distribution contents to exclude secrets, private data, model weights, local databases, held-out answers, and development artifacts.
- Define a private security-reporting channel before enabling public reports; there is no maintainer contact or response SLA configured yet.

The scaffold CI does not publish packages, download models, execute paid APIs, or run agent benchmarks.
