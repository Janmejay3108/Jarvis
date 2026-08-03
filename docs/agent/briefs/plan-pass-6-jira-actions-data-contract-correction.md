# Plan Alignment Pass 6: Jira Actions Data-Contract Correction

## Decision

No new architecture decision is required. Decision 004 already requires persisted Jira actions in
the master data contract. Alignment pass 6 implemented the schema in Plan1 and the routes/event in
`plan_master.md`, but omitted `jira_actions` from `plan_master.md` UP-8's persistent-store
enumeration. Its explanation also identified, but did not align, the forward-migration note in
`docs/context.md` §11.

This is a Plan Steward correction to the still-unmerged pass, not a Builder defect.

## Branch And Base

Continue on `docs/jarvis-alignment-6`, based on `master` at `03fc07c`. Do not create a second plan
pass or branch. Preserve the seven existing pass-6 commits.

## Plan Steward Correction

### `plan_master.md`

In UP-8, extend the `data/agent.db` table list from:

> conversations, messages, runs, steps, events, approvals

to:

> conversations, messages, runs, steps, events, approvals, Jira actions

Use prose naming consistent with the existing row; the physical table name remains `jira_actions`
as specified by Plan1 Step 1.1.2. Do not change the UP-8 rationale, resumability contract, metrics
contract, heading structure, or any other row.

### `docs/plan_change_log_jarvis_6.md`

Correct §4 so it no longer claims that master §5 alone carries the full binding contract. Record
that Decision 004's locator (`section 4/data model`) was wrong because master §4 is the repo tree,
but its requirement was fulfilled at UP-8, the actual master persistent-state enumeration.

Update the per-file edit map, mechanical counts, additive diff totals, removed-line audit if its
count changes, and structural table from commands actually run after the correction. Do not hand
edit verification numbers from expectation.

Commit these two changes as one corrective fix, after reading the full diff:

```text
fix7(plan_master): add Jira actions to UP-8 persistent-state contract (D004)
```

## Context Alignment

`docs/context.md` §11 is also a canonical data-model surface and currently enumerates the original
six tables. After the Plan Steward correction, the design-document owner must add a forward note
beside the existing Plan4 `approvals.kind` precedent stating that Plan1 adds `jira_actions` as a
migration on the same store, with the schema and safe-persistence constraints from Plan1 Step
1.1.2. This is not an edit to plan0 §B.6 and must not imply that the already-built foundation step
created the table.

Because the Plan Steward may edit only plans and its own change log, it must report this context
alignment as the sole follow-up rather than silently editing `docs/context.md`.

## Verification

Run all of these after the Plan Steward correction:

```powershell
$env:LC_ALL='C'
Select-String -Path plan_master.md -Pattern '^\| UP-8 .*Jira actions'
Select-String -Path plan1_diagnosis_and_chat.md -Pattern 'jira_actions\(action_id, run_id, ticket_key, operation, intent_json, state, check_result, attempts, created_at, updated_at\)'
Select-String -Path plan_master.md,plan1_diagnosis_and_chat.md,plan3_lifecycle_rollout.md -Pattern 'jira\.action\.updated|No automatic retry|never automatic|Nothing retries automatically|No control ever fires automatically'
foreach ($file in 'plan_master.md','plan1_diagnosis_and_chat.md','plan3_lifecycle_rollout.md') {
  $before = (git show master:$file | Select-String -Pattern '^#{1,4} ').Count
  $after = (Select-String -Path $file -Pattern '^#{1,4} ').Count
  '{0}: before={1} after={2}' -f $file,$before,$after
}
git diff --check master...HEAD
python -m pytest -q
python -m ruff check .
git status --short --branch
```

Expected: exactly one UP-8 match naming Jira actions; the complete Plan1 schema match remains;
retry/replay language remains; heading counts remain 24/33/28; 119 tests pass with 2 skipped;
ruff passes; the worktree is clean after the corrective commit.

## Must Not Change

- Decision 003's read-only retry boundary and single-attempt writes.
- Decision 004's independent Jira writes, successful primary run, persisted/replayed action state,
  check-before-explicit-retry, and prohibition on automatic retry.
- Plan1 Gate 1 ownership and Steps 1.5.3/1.6.2.
- Plan3's reuse of the Plan1 mechanism.
- Any test, gate, heading, threshold, taxonomy item, `max_attempts: 3`, `BudgetGuard`,
  `callers_pass`, verdict logic, `NOT_ONBOARDED`, `STALE_SYNC`, or safety invariant.
- `plan0_poc_and_foundation.md` §B.6; it describes the already-built foundation schema.

## Report Back

Report the corrective commit SHA, exact UP-8 line, corrected change-log counts, heading counts,
pytest/ruff results, and the outstanding `docs/context.md` §11 alignment. No push, merge, or tag in
Plan Steward mode.