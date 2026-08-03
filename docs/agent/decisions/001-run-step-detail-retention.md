# Decision 001: Preserve Step Detail When Completion Detail Is Omitted

## Status

Accepted on 2026-08-03 during review of Plan1 Step 1.1.1.

## Context

`RunStep.detail` drives the persisted step history and the RunCard timeline. `begin()` may set useful context such as the work being performed. Plan1 specifies `end(detail?, error?)`, but the first brief translated the optional detail into `detail: str = ""`. Calling `end()` then erased the begin-time detail from the model, database, and `step.completed` event.

`StateStore.complete_step` already distinguishes `detail=None` (preserve) from an explicit string (replace), including `""` (clear). The model helper must preserve that distinction.

## Decision

`AgentRun.end` uses `detail: str | None = None`.

- `None` preserves the active step's existing detail in the model, persisted row, and completion event.
- Any explicit string replaces the detail in all three representations.
- An explicit empty string clears the detail.

The completion event always contains the resulting effective detail, so replay and live delivery render the same timeline.

## Rejected Alternatives

- Always replace with `""`: loses useful start context whenever a caller has no completion-specific message.
- Split start and completion detail into new schema fields: adds a migration and frontend contract without a demonstrated need.
- Preserve unconditionally: prevents callers from recording a more useful completion result or deliberately clearing stale detail.

## Consequences

Pipeline callers may call `end()` without repeating begin-time narration. Callers that have a completion result pass it explicitly. Tests must cover omitted detail and explicit empty detail across model, SQLite, and event payloads.