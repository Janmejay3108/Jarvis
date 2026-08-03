# Decision 004: Jira Publication Failure Does Not Fail the Primary Run

## Status

Accepted on 2026-08-03 after review of Plan1 Step 1.2.1.

This decision narrows Decision 003 where it allowed an uncertain Jira write to
surface as a failed diagnosis run. Decision 003's no-automatic-retry boundary
remains in force.

## Context

Plan1 Step 1.1.2 already publishes a diagnosis comment and the `ai-diagnosed`
label. Plan3 sections 3.3 and 3.4 later require every Jira lifecycle call to be
isolated, require Jira failure to be shown in chat, and state that no Jira call
may fail the run. The binding chat contract in `plan_master.md` section 5
supports replay but defines no Jira reconciliation action.

The current model cannot represent a failed `post_diagnosis` step inside a
successful run: `AgentRun.end(error=...)` marks both the step and run failed.
Using that mechanism would falsely report that diagnosis failed after the
diagnosis artifact had already been produced. Swallowing the error would also
be wrong because a reopened conversation would have no truthful, actionable
record of the publication failure.

The user's requirement is stronger than replay alone: reopening the same
conversation must show the particular Jira operation that failed and provide a
check/retry path. An uncertain non-idempotent write must be checked before it is
retried.

## Decision

### Primary Run Versus Jira Side Effects

- A successful diagnosis remains a successful run even when a Jira publication
  action fails or has an uncertain outcome.
- Jira writes are attempted independently. Failure to post the diagnosis
  comment must not prevent the `ai-diagnosed` label attempt, and vice versa.
- Jira action failure is not represented with `step.failed`, because that event
  currently terminalizes the run. The enclosing `post_diagnosis` step completes
  with a detail stating whether publication succeeded or requires attention.
- The failure remains visible through a separately persisted Jira-action record
  and event. This is degradation, not suppression.

### Persisted Action Contract

- Persist a Jira action before issuing its request. It has a stable `action_id`,
  `run_id`, `ticket_key`, operation, intended-effect metadata, state, check
  result, attempt count, and timestamps.
- States distinguish at least `pending`, `succeeded`, `failed`, `uncertain`, and
  `reconciled`. Check results distinguish `present`, `absent`, and `unknown`.
- Request credentials, authenticated URLs, attachment bytes, and raw transport
  or response text are never persisted. Later attachment actions store an
  artifact reference and safe metadata rather than bytes.
- Publish a persisted `jira.action.updated` event containing the safe action
  summary. SSE replay therefore renders the same state after browser or process
  restart as the live session.

### Check And Retry

- Add authenticated, action-scoped check and retry routes under the existing
  run resource. They operate on an `action_id`; they do not rerun the diagnosis
  or the whole pipeline.
- Checking is read-only. An uncertain action must be checked before retry is
  offered. `present` marks it reconciled without another write; `absent` permits
  an explicit retry; `unknown` remains uncertain and requires manual handling.
- A definite failure may offer explicit retry without an uncertainty check.
  Every check and retry updates the action record and emits an auditable event.
- Retrying is never automatic on page reload, process restart, queue recovery,
  or SSE reconnection.
- Comment writes carry the stable action ID in an inspectable JARVIS footer so a
  comment-list read can reconcile them. Label reconciliation checks the issue's
  exact label set. Plan3 must define attachment and transition reconciliation
  when it extends this mechanism.

### Sequencing And Ownership

- Plan1 owns the diagnosis comment/label action records, independent call
  isolation, backend check/retry routes, replay, and RunCard controls. This must
  land before Gate 1 because Plan1's chat MVP already performs those writes.
- Plan3 sections 3.3 and 3.4 extend the same action contract to evidence
  attachments, `ai-fixed`, workflow transitions, and late lifecycle failures.
  Plan3 must not introduce a second retry mechanism.
- The Step 1.2.1 Jira client remains a transport boundary: reads may retry;
  writes make one attempt and surface definite versus uncertain failure. It
  does not own persistence, reconciliation policy, routes, or UI.
- The reviewed Step 1.2.1 commit is not blocked by this design gap. Its caller
  behavior is corrected in the Plan1 follow-up above.

## Required Plan Steward Pass

Update these sources in one numbered pass before the follow-up is built:

- `plan_master.md` section 5: add the action-scoped check/retry routes and
  `jira.action.updated` event; section 4/data model: add persisted Jira actions.
- `plan1_diagnosis_and_chat.md` Step 1.1.2: isolate comment and label writes and
  preserve diagnosis success; Steps 1.5.3 and 1.6.2: add action routes, replay,
  and RunCard check/retry controls.
- `plan3_lifecycle_rollout.md` sections 3.3 and 3.4: extend, rather than replace,
  the Plan1 reconciliation contract.
- Narrow Step 1.2.1's blanket retry wording as already required by Decision 003.

## Rejected Alternatives

- Fail the diagnosis run when Jira publication fails: confuses a side-effect
  outage with diagnosis failure and contradicts Plan3's degradation contract.
- Mark `post_diagnosis` failed but later overwrite the run as completed: breaks
  the current terminal step/run invariant and makes replay internally
  contradictory.
- Log and continue without persisted action state: a reopened conversation
  cannot explain or recover the failed operation.
- Retry the whole run: repeats expensive reasoning and risks duplicate Jira
  writes unrelated to the failed action.
- Defer all handling to Plan3: Plan1's diagnosis chat already writes to Jira and
  reaches Gate 1 before Plan3 exists.
- Put reconciliation inside `JiraClient`: the client has no run, conversation,
  persistence, SSO, or UI ownership.

## Consequences

- The Plan1 chat can truthfully show “diagnosis completed; Jira publication
  needs attention” and preserve that state across reloads.
- The reliable label attempt survives a comment failure.
- Non-idempotent writes retain Decision 003's check-before-retry safety.
- A small Plan1 follow-up and a Plan Steward pass are required before Gate 1;
  Plan3 reuses the same mechanism instead of designing another one.