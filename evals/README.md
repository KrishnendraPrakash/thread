# Evaluation scaffold

No evaluation runner or measured scores exist yet.

- cases/development/: tasks and reference expectations used during development.
- cases/held_out/: reserved tasks excluded from agent context and tuning inputs.
- fixtures/workspaces/: controlled starting environments copied into isolated runs.
- graders/: deterministic references and human-calibrated review specifications.
- reports/: generated outputs, ignored by Git except its README.

Public fixture locations do not by themselves prevent leakage. The future runner must give the agent only the copied workspace and enforce the boundary. Use separate private data when genuine unreleased holdouts are needed. Do not mount this repository wholesale as the workspace during a scored task.
