# JARVIS

JARVIS is the Enovia automation testing agent. The repository root is the project root.

## Layout

- `src/` contains the Python application.
- `webapp/` contains the chat web application.
- `config/enovia.yaml` contains track configuration.
- `tracks/enovia/` contains curated Enovia context and the test-config registry.
- `data/` contains ignored runtime state and working copies.

## Install

Requires Python 3.11 or newer.

```text
pip install -e .[dev]
```

## Plans

Read `plan_master.md` first, followed by `plan0_poc_and_foundation.md`,
`plan1_diagnosis_and_chat.md`, `plan2_autofix_and_validation.md`, and
`plan3_lifecycle_rollout.md`. See `docs/context.md` for project orientation.