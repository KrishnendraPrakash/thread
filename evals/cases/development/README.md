# Development cases

[field_lookup.json](field_lookup.json) contains ten synthetic direct-field fixtures with source text, selected pointer, and expected scalar value. The unittest runner copies only source text into an isolated workspace and keeps expected answers outside it.

These cases validate the experimental deterministic path. They do not freeze the full M0 workload, establish model accuracy, or replace repeated M1 trials and the held-out set.
