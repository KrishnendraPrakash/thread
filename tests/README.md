# Tests

Run `python -m unittest discover -s tests -v` from an installed development environment. The suite exercises direct-field behavior, source boundaries, saved decisions, provider validation, replay, and CLI subprocesses. Provider responses are mocked; no model server, paid keys, or downloads are required.

Ten development reference cases live in [evals](../evals/cases/development/field_lookup.json). Only their synthetic source content is copied into each allowed workspace; reference answers remain outside. These deterministic cases are not model-quality trials or the complete M0/M1 acceptance suite.

Keep live integrations opt-in. A zero-test discovery run is not a pass. Planned full H01–H13 action/decision gates remain in [SPEC.md](../SPEC.md).
