# Plan1 post-1.2.3 Jira write follow-up

## 1. Step and authority

This is the separately scheduled reliability follow-up immediately after Plan1 Step 1.2.3 and
before Step 1.2.4. It repairs two reviewed defects in the already-landed Plan1 Step 1.2.1 Jira
client and Step 1.1.2 diagnosis pipeline. It is not a new plan step and does not edit the plan set.

Plan1 Step 1.2.1 is binding:

> Writes (`post_comment`, `add_label`, `add_attachment`, the transition POST): exactly one attempt,
> never auto-retried.
>
> A write timeout/5xx raises a typed, redacted
> `JiraWriteUncertain(operation, ticket_key)` - the write MAY have succeeded. A write 4xx stays an
> ordinary `httpx.HTTPStatusError` (definite failure).
>
> The client is a transport boundary only: it owns no persistence, reconciliation policy, routes,
> or UI.

Decision 003 (`docs/agent/decisions/003-jira-write-retry-boundary.md`) remains binding. In
particular, an uncertain non-idempotent write is never replayed automatically; later explicit
reconciliation checks Jira before any user-authorized retry.

The scheduling contract in `docs/agent/briefs/p1-1.2.3-dai-client.md` section 3 is the direct
specification for this follow-up:

> Formatter/programming defects propagate to the pipeline failure boundary with the pre-created
> action still pending; a successful comment HTTP status counts as a successful write without
> requiring a response body; timeout/5xx uncertainty, one-attempt writes, independent comment/label
> attempts, redaction, and explicit reconciliation remain unchanged.

## 2. Branch and base

- Base: local `master` at `6e06fd00fa39b11cf33820cf8ca56e51b19012e5`.
- Branch: `build/1.2.3-jira-write-followup`.
- Commit once with message `fix: preserve Jira write truthfulness`.

Before editing, run `git status --short --branch` and `git rev-parse HEAD`. Stop and report if the
worktree is dirty or HEAD is not the pinned base. Do not fetch, pull, rebase, push, or merge.

## 3. Per-file specification

### `src/integrations/jira_client.py`

Change only the successful-return contract of:

```python
async def post_comment(self, key: str, body: str) -> None:
```

It must await the existing `_write_request(...)` exactly once with the existing method, path,
operation, ticket key, and `{"body": body}` JSON payload. Once `_write_request` returns, the comment
write succeeded for this transport boundary: return `None` without calling `response.json()` or
otherwise inspecting the response body. Any HTTP 2xx response accepted by httpx, including an empty
body or malformed/non-JSON body, therefore counts as success.

Do not change `_request`, `_write_request`, `_read_request`, `JiraWriteUncertain`, retry predicates,
headers, authentication, URL construction, or any other public Jira method. `add_attachment()` still
parses and validates its documented response array; read methods still parse their documented JSON.

### `src/orchestrator/pipeline.py`

In `DiagnosisPipeline._post_diagnosis`, preserve this order when Jira writes are enabled:

1. Create and persist the `post_comment` Jira action.
2. Derive `diagnosis`, call `self._format_for_jira(...)`, and append the durable action footer.
3. Pass the completed body to `_attempt_jira_write(...)`.
4. If the pipeline is still running, create and independently attempt the label action exactly as it
   does now.

Remove the broad formatter/footer `try/except Exception` and its call that marks the comment action
`failed`. Do not replace it with a narrower recovery catch. A formatter or footer programming defect
must escape `_post_diagnosis` into the existing `_stage` and `execute` failure boundaries. Those
existing boundaries record the safe exception type on the failed `post_diagnosis` step and return a
failed run with reason `pipeline_error`.

Because the comment action is created before formatting but no write attempt began, that action must
remain durable as `state="pending"`, `attempts=0`, and `check_result="unknown"`. Do not create a label
action, call Jira, or emit a false action-completion event after such a defect.

Do not change `_attempt_jira_write`. Once an actual Jira request starts, its current contract remains:

- timeout/5xx or `httpx.RequestError`: comment action `uncertain`, no automatic retry;
- 4xx: comment action `failed`;
- successful request: comment action `succeeded`;
- comment and label attempts remain independent for those handled transport/HTTP outcomes;
- cancellation and unexpected adapter/programming defects leave the begun action pending and abort
  before the label.

Formatting must remain entirely skipped when `jira_writes_enabled` is false.

### `tests/test_jira_client.py`

Replace the obsolete assertion that `post_comment()` returns the Jira comment JSON. Cover successful
comment response bodies as tightly scoped parameterized cases:

- a normal 201 JSON comment object;
- a successful response with an empty body (201 or 204);
- a successful 2xx response whose body is malformed JSON.

For every case assert that `post_comment()` returns `None`, sends exactly one POST to the existing
comment URL, and preserves the exact request body `{"body":"*Diagnosis* body"}`. The malformed and
empty response cases must not raise.

Keep the existing timeout, 5xx, 4xx, redaction, one-attempt, lifecycle, read-retry, attachment,
transition, and label tests unchanged and green except for mechanical type adjustments required by
the intentional `post_comment() -> None` API.

### `tests/test_pipeline.py`

Update `RecordingJira.post_comment` to match the production `-> None` contract; it must still record
the call and raise an injected error before returning when configured.

Replace `test_formatter_failure_precedes_comment_attempt_and_keeps_run_successful`, whose expected
behavior is now known to be wrong, with regression coverage that asserts a formatter
`RuntimeError`:

- makes `execute()` return a run with `RunStatus.failed` and terminal reason `pipeline_error`;
- persists exactly one Jira action: operation `post_comment`, state `pending`, attempts `0`, and
  `check_result == "unknown"`;
- makes no `jira.post_comment` or `jira.add_label` call and creates no label action;
- persists `post_diagnosis` as a failed step whose safe error is `RuntimeError`;
- emits `step.failed` and `run.failed`, never `run.completed`;
- emits only the original pending `jira.action.updated` event for the comment action, and the action
  plus event remain identical after reopening the state store and replaying events.

Add the same state/control-flow regression for a footer programming defect by monkeypatching the
`append_jira_action_footer` symbol imported by `src.orchestrator.pipeline` to raise `TypeError` after
the formatter succeeds. Assert the formatter was called, then the same failed-run, untouched pending
comment action, no Jira request, no label, failed-step safe error, and terminal-event behavior.

Do not weaken or remove these neighboring proofs:

- definite comment 4xx does not block the independent label attempt or fail the diagnosis run;
- uncertain writes make one request and leave comment/label operations independent;
- cancellation leaves a replayable pending attempted action;
- adapter/programming defects after a request begins fail the run with the action pending;
- Jira-disabled runs skip formatter, comment, label, and action creation;
- persisted action events expose only the existing safe payload fields.

## 4. Required tests

The resulting suite must distinctly prove:

1. `post_comment()` accepts valid JSON, empty, and malformed/non-JSON successful bodies, returns
   `None`, preserves the request payload, and makes one request per invocation.
2. A formatter defect reaches the pipeline failure boundary with one durable unattempted pending
   comment action and no label action or Jira call.
3. A footer defect has the same failure semantics after proving the formatter ran.
4. Existing timeout/5xx uncertainty, definite 4xx, single-attempt writes, independent handled
   comment/label outcomes, cancellation, redaction, replay, and write-gate tests remain green.

Do not add live Jira tests. Do not relax an assertion, skip, xfail, retry count, or exception type to
make a test pass.

## 5. Verification commands

Run from repository root in this order:

```powershell
python -m pytest tests/test_jira_client.py tests/test_pipeline.py -q
python -m ruff check src/integrations/jira_client.py src/orchestrator/pipeline.py tests/test_jira_client.py tests/test_pipeline.py
python -m pytest -q
python -m ruff check .
git diff --check
git diff --name-only 6e06fd00fa39b11cf33820cf8ca56e51b19012e5...HEAD
```

Expected results:

- Focused and full tests pass with no new skip or xfail; the two existing environment-dependent
  skips may remain.
- Focused and full Ruff checks report `All checks passed!`.
- `git diff --check` is silent.
- The final name-only diff lists exactly the four files specified in section 3.

## 6. What must not change

- Never retry a Jira write automatically. Never reinterpret timeout/5xx as definite failure.
- Never mark an unattempted formatter/footer action `failed`; it remains pending for truthful audit
  and explicit reconciliation.
- Never expose or persist PATs, request bodies, response bodies, authenticated URLs, exception text,
  or other secrets. Persist only the existing safe exception type/code and safe action/event fields.
- Do not change Jira action schema, event type names or payloads, state-store APIs, run terminal
  semantics, or the explicit reconciliation design.
- Do not change successful/failed/uncertain behavior after an actual Jira request, including the
  independent label attempt for handled comment outcomes.
- Do not edit DAI, Bitbucket, evidence, diagnosis, validation, dispatcher, candidate-script, config,
  plan, progress, decision, or brief files other than this already-present build brief.
- Do not read or modify `.env`. Do not call Jira or any other live service.

## 7. Report back

Commit once, then report:

- branch and commit SHA;
- the four files changed;
- focused and full pytest counts, including skips;
- focused and full Ruff results and `git diff --check` result;
- confirmation that writes remain one attempt and timeout/5xx remain redacted uncertainty;
- confirmation that no plan, progress, decision, config, `.env`, DAI, or validation file changed;
- any deviation or unresolved contract question.

Do not push and do not merge.
