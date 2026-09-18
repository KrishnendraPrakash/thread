# Tests

The scaffold has no behavior tests yet. Unit, integration, and acceptance directories are reserved for the implementation. Current CI performs packaging/lint/syntax/CLI smoke checks only.

Use standard-library unittest for the initial suite. When tests exist, run python -m unittest discover -s tests -v. Zero discovered tests does not satisfy any SPEC.md milestone.

Keep model/network integration tests opt-in and keep reference answers outside the agent-visible workspace. Evaluation fixtures and grading live under evals/; teaching traces remain under planning_examples/.
