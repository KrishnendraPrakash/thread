# Trace planning examples

All files here are synthetic teaching artifacts. No tools, models, approvals, or writes shown inside these records were actually executed. Scripted timestamps and counters are illustrative; actual latency remains null. The planning trace format is versioned but is not a frozen production schema.

| File | Purpose |
| --- | --- |
| [Direct lookup](../EXAMPLE_TRACE.json) | Explicit deterministic rule/parser/template producers; custom-response interpretation and echo; authorized T2-to-T1 reduction; source integrity and field checks; claim status; render, fidelity, delivery |
| [NEGATIVE_UNSUPPORTED_LOCATOR.json](NEGATIVE_UNSUPPORTED_LOCATOR.json) | Preserves the original flawed trace. Expected failures include an unchecked precise locator, a pre-render fidelity check, and a missing status transition. It must not be treated as a passing example. |
| [AMBIGUOUS_REPLY_TRACE.json](AMBIGUOUS_REPLY_TRACE.json) | A custom reply has unresolved references. Its interpretation remains ambiguous, the original tier/scope stay in force, and the agent asks a focused clarification without granting approval or executing tools. |
| [CONFLICT_TRACE.json](CONFLICT_TRACE.json) | Preserves README and configuration reports; attempts a targeted runtime observation; records insufficient support for runtime truth; delivers an explicitly limited answer |
| [ACTION_REPLAY_TRACE.json](ACTION_REPLAY_TRACE.json) | Revises a concrete proposal after custom input, rejects an obsolete approval, stays waiting for the current approval, and demonstrates an isolated strict-replay mismatch without dispatching a write |
| [MODEL_CALL_SPECIMEN.json](MODEL_CALL_SPECIMEN.json) | Shows exact serialized synthetic model input, raw synthetic output, prompt/schema hashes, and required metadata fields. Actual model artifact/runtime/token counts are unavailable, so it is not a measured model run or a complete baseline for model replay. |

The direct trace deliberately uses an exact known phrase mapping for its custom response. It does not claim a general natural-language parser works without a model. Unknown or ambiguous text requires a separately recorded interpretation process or a follow-up question; SPEC H13 defines the ambiguous-response acceptance case.

The source manifest supplies immutable reference bytes. An integrity check reloads those bytes and compares them to a separately recorded tool excerpt. It detects mismatches in recording or slicing, but does not create a second independent source of factual truth.

Template fidelity uses named template bytes and bindings from previously completed checks. The expected answer must be reconstructed from those inputs, not copied from the render being checked. Complex free prose still needs semantic coverage checks as specified in SPEC.md.

The action example's replay subrun compares two different proposed writes against a synthetic recorded-request fixture. It does not consume the parent run's pending approval, emulate a successful write, or substitute a recorded output for unmatched arguments.
