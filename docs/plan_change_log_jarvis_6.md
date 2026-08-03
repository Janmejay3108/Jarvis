# Plan change log — JARVIS alignment pass 6

**Branch:** `docs/jarvis-alignment-6` · **Base:** `master` @ `03fc07c` (previous tag
`plan-set-jarvis-v5` @ `cc5a49c`) · **Date:** 2026-08-03

**Purpose.** Fold Decisions 003 and 004 into the design authority. The plan set said to retry every
Jira request three times and said nothing about what a reopened chat shows when a Jira write fails.
Both are corrected here.

**Prime directive honoured.** No PoC, gate, threshold, invariant, test requirement, or event type
was removed, softened, deferred, or simplified. `max_attempts: 3`, `callers_pass`, `BudgetGuard`,
`NOT_ONBOARDED`, `STALE_SYNC` and the signature-based verdict are untouched. The reasoning core is
the product.

---

## 1. Why this pass exists

Two defects, both found by review of the built Step 1.2.1 rather than by reading the plans:

1. **The blanket retry was unsafe.** `plan1` Step 1.2.1 said *"`tenacity` retry (3x, expo backoff)
   on 5xx/timeouts"* for the whole client. Jira DC REST v2 has **no idempotency key**, so retrying
   a write can post a duplicate comment, duplicate an attachment, or advance a workflow twice.
   Reads are safe to retry; writes are not.

2. **A sequencing gap between plan1 and plan3.** `plan1` Step 1.1.2 already posts the diagnosis
   comment and the `ai-diagnosed` label, but the rule that *"nothing here may fail the run: each
   call individually try/except-ed"* lived only in `plan3` §3.3 and `docs/context.md` §9.3 — a
   phase that does not exist yet. Meanwhile the built pipeline wraps both writes in one stage, so a
   transient Jira 5xx failed the whole run and skipped the label, **after** the diagnosis had
   already succeeded. Removing the write retries (defect 1) makes this bite more often, so the
   compensating control has to land in the same plan that performs the writes.

Neither defect is theoretical: the second one turns a Jira outage into a reported diagnosis
failure, which is the wrong answer to give a developer.

---

## 2. Rulings applied

| ID | Ruling | Source |
|---|---|---|
| **J1** | Reads (`get_ticket`, `transitions`) retry 3× with backoff on timeout/5xx | D003 |
| **J2** | Writes make **exactly one** attempt; timeout/5xx → typed redacted `JiraWriteUncertain`; 4xx stays a definite `httpx.HTTPStatusError` | D003 |
| **J3** | Jira publication is a side effect — a successful diagnosis stays a **successful run** | D004 |
| **J4** | Comment and label attempts are **independent**; a failed comment must not suppress the label | D004 |
| **J5** | Persisted `jira_actions` row + `jira.action.updated` event, safe fields only | D004 |
| **J6** | Authenticated, **action-scoped** check/retry; check-before-retry for uncertain; **never automatic** | D004 |
| **J7** | RunCard renders replayed action state, so a reopened chat shows which operation failed | D004 |
| **J8** | All reconciliation complete **before Gate 1** | D004 |
| **J9** | plan3 **extends** this mechanism; a second retry path is a defect | D004 |

---

## 3. Per-file edit map

| # | Commit | File → section | Change | Authorised by |
|---|---|---|---|---|
| 1 | `f0b9816` | `plan_master` §5.1, §5.2 | Added `GET /api/runs/{run_id}/jira_actions`, `…/check`, `…/retry`; added the `jira.action.updated` event type and its safe payload; stated action-scoped, check-before-retry, never-automatic | J5, J6 |
| 2 | `aa0a06f` | `plan1` Step 1.2.1 | Split the retry boundary: reads retry 3×, writes single-attempt; uncertain vs definite failure; client is a transport boundary only; added a DoD | J1, J2 |
| 3 | `ff0f794` | `plan1` Step 1.1.2 | `post_diagnosis` isolates each write, keeps the run `completed`, declares the `jira_actions` schema addition, forbids persisting secrets/bytes, emits the event, forbids automatic retry; extended the DoD | J3, J4, J5 |
| 4 | `76655bf` | `plan1` Steps 1.5.3, 1.6.2 | Added the three SSO-gated recovery routes with read-only `check` and explicit `retry`; added `JiraActionCard` rebuilt from replayed events; extended Verification and DoD | J6, J7 |
| 5 | `3535ed0` | `plan1` GATE 1 | New gate row requiring Jira action recovery to be complete | J8 |
| 6 | `226336e` | `plan3` §3.3, Step 3.4.2 | Lifecycle writes reuse the plan1 mechanism; per-operation reconciliation reads defined for comment/label/**attachment**/**transition**; degradation rule 4 now names the persisted action and its recovery path | J9 |

**No edit was made without a ruling authorising it.**

---

## 4. Deviation from Decision 004, and why

Decision 004 asked for the persisted-action schema to be added to *"`plan_master.md` section
4/data model"*. **It was placed in `plan1` Step 1.1.2 instead.** Two reasons:

- `plan_master` §4 is the **repo layout tree**, not a data model. The canonical SQLite schema lives
  in `plan0` §B.6.
- `plan0` §B.6 is **already built** (`state_store.py`, six tables, merged). Editing a completed
  step to describe work that a later plan performs would misrepresent what B.6 delivered. The
  established convention is the plan4 precedent recorded in `docs/context.md` §11 — *"Plan4 adds a
  `kind` column to `approvals` … a migration, not a new table"* — where the **owning plan declares
  its own schema delta**.

So `jira_actions` is declared in `plan1` Step 1.1.2 and explicitly labelled *"a migration on plan0
§B.6's store, not a new store"*. `plan_master` §5 carries the binding **contract** (routes, event,
policy) as Decision 004 requires. `plan0` was not edited.

---

## 5. Mechanical verification

```
jira_actions              8 occurrences
jira.action.updated       6 occurrences
decision refs (003/004)   7 occurrences
never-automatic wording   3 occurrences
```

Additive-change proof:

```
git diff --stat master...HEAD
 plan1_diagnosis_and_chat.md | 29 +++++++++++++++++++++++++----
 plan3_lifecycle_rollout.md  |  7 +++++--
 plan_master.md              | 13 +++++++++++++
 3 files changed, 43 insertions(+), 6 deletions(-)
```

All **6** removed lines were audited individually. Each is a line replaced by an expanded version
that **retains the original text verbatim**: the Step 1.1.2 DoD, the Step 1.2.1 client one-liner,
the Step 1.5.3 Verification and DoD, the §3.3 DoD, and the §3.4.2 degradation-rule line. **No
requirement was dropped.**

Core guards re-counted after the pass, all intact:
`max_attempts` 3 · `callers_pass` 4 · `BudgetGuard` 3 · `NOT_ONBOARDED` 6 · `STALE_SYNC` 12.

---

## 6. Structural check

| File | Headings before | Headings after |
|---|---|---|
| `plan_master.md` | 24 | **24** |
| `plan1_diagnosis_and_chat.md` | 33 | **33** |
| `plan3_lifecycle_rollout.md` | 28 | **28** |

**Zero headings lost. Zero gained.** Every change is prose, table-row, or route-block content
inside an existing section.

---

## 7. Consequences for the build

- The next buildable slice is **`plan1` Step 1.1.2's** isolation + `jira_actions` persistence. It
  is buildable now; it does not depend on Phase 1.5 or 1.6.
- The recovery **routes** (Step 1.5.3) and **RunCard controls** (Step 1.6.2) land with their own
  phases. They are now explicit requirements rather than implied work, and **Gate 1 cannot pass
  without them**.
- `plan3` §3.3 must reuse this mechanism. Attachment and transition reconciliation reads are now
  specified, closing the open question Decision 004 left for the lifecycle owner.
- `docs/context.md` §9.3 is consistent with the plans again: the "nothing here may fail the run"
  rule is now stated in the plan that actually performs the diagnosis-phase writes.

## 8. Not done in this pass

- No code, config, test, or `PROGRESS.md` change — Plan Steward edits plans only.
- `plan0` §B.6 deliberately untouched (see §4).
- No push, no merge, no tag. Jay merges, then tags **`plan-set-jarvis-v6`** and **pushes the tag**
  (M4 — for four passes the tags existed only locally, which made this structural check
  un-runnable from outside).
