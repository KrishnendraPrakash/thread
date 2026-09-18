# Optional capabilities

These are documented extension locations, not enabled features or dependency extras.

| Capability | Location | Stage / prerequisite |
| --- | --- | --- |
| Hosted free-tier and paid models | src/thread_agent/providers/hosted/ | M4B; capability tests, user key, data destination, quota/budget policy |
| On-premises model endpoint | src/thread_agent/providers/private/ | M4B; explicit endpoint/auth/TLS and compatibility checks |
| Dashboard or HTTP gateway | src/thread_agent/interfaces/web/ | After local core; reuse runtime and decision service |
| Messaging | src/thread_agent/integrations/messaging/ | Authenticated responder identity and scoped decision resumption |
| Scheduling | src/thread_agent/integrations/scheduling/ | Persisted jobs, policy, cancellation, idempotency |
| Specialist delegation | src/thread_agent/integrations/delegation/ | Bounded tasks, isolated authority, result/status/trace references |
| Containers/deployment | deploy/ | A functional runtime and clear storage/network/secret requirements |

Optional dependencies should be introduced with their implemented feature and tests. No default import, installation, or fallback should require a cloud account. Offline mode must cover every model role and tool. See [SPEC.md](../SPEC.md) for the normative rules.
