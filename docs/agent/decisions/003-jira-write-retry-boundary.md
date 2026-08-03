# Decision 003: Retry Jira Reads, Surface Uncertain Writes

## Status

Accepted on 2026-08-03 while preparing Plan1 Step 1.2.1.

## Context

Plan1 Step 1.2.1 says to retry Jira requests three times on server errors and
timeouts. That is safe for reads, but it is unsafe as a blanket rule for Jira
writes. A comment, attachment, label update, or workflow transition may reach
Jira successfully and then lose its response. Automatically repeating that
request can duplicate evidence or advance workflow twice.

Chat history must still explain the failure after a browser or process restart.
The existing run model, state store, and EventBus already persist `step.failed`
and `run.failed`; later chat routes replay those events before subscribing to
live events. The missing distinction is whether an operation is safe to retry.

## Decision

- Retry read-only Jira operations up to three attempts with exponential backoff
  on `httpx.TimeoutException` and HTTP 5xx responses.
- Do not automatically retry `post_comment`, `add_label`, `add_attachment`, or
  the POST that performs a workflow transition.
- When a Jira write times out or returns 5xx, raise a typed, redacted
  `JiraWriteUncertain` carrying only the operation name and ticket key. Its
  public message states that Jira may have completed the write and that callers
  must check Jira before retrying.
- Definite 4xx failures remain ordinary `httpx.HTTPStatusError` failures and are
  never retried.
- A requested transition that is not available remains a best-effort no-op with
  a structured warning. This is different from an attempted transition whose
  outcome is unknown.
- The diagnosis pipeline may persist and replay the resulting failed step/run;
  it must not silently retry or hide an uncertain write.
- A later chat/lifecycle step owns the explicit check-and-retry interaction. It
  must inspect Jira first and create an auditable retry action rather than
  replaying a non-idempotent request automatically when a chat is reopened.

## Rejected Alternatives

- Retry every request literally as Plan1 currently says: can create duplicate
  comments or attachments and can advance workflow more than intended.
- Swallow every write failure because Jira lifecycle is best-effort: hides an
  operational failure and gives the reopened chat no truthful state to show.
- Build the retry button and reconciliation workflow in Step 1.2.1: the HTTP
  client does not own persisted runs, chat controls, or lifecycle policy.
- Treat every write failure as definitely failed: a timeout or 5xx does not
  prove that Jira rejected or rolled back the request.

## Consequences

- The Jira client has separate internal read and write request paths even though
  they share authentication, URL construction, and response validation.
- Tests assert three-attempt retries for reads and exactly one request for every
  uncertain write.
- Persisted run/chat failure replay remains the source of truth after reload.
- Plan Steward must narrow Plan1 Step 1.2.1's blanket retry wording in a later
  numbered pass.
- The future chat/lifecycle brief must specify the user-visible reconciliation
  action for `JiraWriteUncertain`: show the failed operation, check Jira state,
  then retry only with explicit user intent when the write is absent.