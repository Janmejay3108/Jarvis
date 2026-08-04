# Plan change log — JARVIS alignment pass 7

**Branch:** `docs/jarvis-alignment-7` · **Base:** `4d08ded` (`master` @ `5128721` + Decision 005)
· **Previous plan-set tag:** `plan-set-jarvis-v6` (`0758d00`) · **Date:** 2026-08-04

**Authority:** `docs/agent/decisions/005-structured-output-validator-ownership.md`, plus the
plan-defect backlog in `docs/agent/ORIENTATION.md` §6.4.

**Prime directive honoured.** No PoC, gate, threshold, invariant, taxonomy family, event type or
test requirement was removed, softened, deferred or simplified. `max_attempts: 3`, `callers_pass`,
`BudgetGuard`, `NOT_ONBOARDED`, `STALE_SYNC`, the Wilson interval and the signature-based verdict
are all intact — counts verified below. The reasoning core is the product.

> **Numbering correction.** This is pass **7**, not pass 5. Tags `plan-set-jarvis-v5` and `v6` and
> change logs 5 and 6 already exist. `ORIENTATION.md` §5.4 still describes only four passes and is
> **stale**. ORIENTATION is not a plan file, so this pass did not edit it; see §6.

---

## 1. Rulings

| ID | Ruling | Source |
|---|---|---|
| **H1** | A JSON tool schema cannot execute pydantic validators, so it cannot satisfy the step's own repair-on-validation-failure rule. `output_model` is a **necessary completion** of the plan, not scope creep. | D005 |
| **H2** | `tools[].input_schema` is the **wire schema** sent to Anthropic; `output_model` is the **local validator**. Never conflated. | D005 |
| **H3** | `output_model` is required **if and only if** `tool_choice.type == "tool"`; incoherent combinations fail preflight, before HTTP. | D005 |
| **H4** | Structured call → `(validated_dict, usage)`; every other call → `(full_message, usage)`. | D005 |
| **H5** | **Exactly one** semantic repair. It is not a transport retry and not plan2's fix loop. Three separate boundaries. | D005, plan_master §6 |
| **H6** | Every **physical** response is charged immediately, including one that trips the cap; a first-response overage prevents the repair. | D005, `docs/context.md` §8 |
| **H7** | PEP 621 requires `version`; without it `pip install -e .[dev]` fails. Implemented value is `0.1.0`. | M9, `pyproject.toml` L3 |
| **H8** | The `anthropic` floor is `>=0.120.2,<1`; `0.40` lacks the adaptive-thinking and forced-tool shapes Step 1.2.4 needs. | Step 1.2.4 drift ruling |
| **H9** | `settings.working_copy_path` is the **single authority** for the Enovia working copy, resolved as `data/working_copy/enovia-plm-test-automation`. `C:\agent\repo` is superseded. | `config/enovia.yaml` L5 |
| **H10** | The `validation` config block has **no** timeout key; the run timeout is `jarvis.run_timeout` (7200s). | `config/enovia.yaml` L66, L78–81 |
| **H11** | JARVIS DAI trigger/logs/results endpoints proven live 2026-08-02; `/testconfiguration/{id}/results` **404s**; a single transient 500 is not a contract error. The evidence chain is **five** endpoints, not four — `GET /api/v2/test_results/{run_id}/screenshots` must be walked **before** `GET /api/v2/screenshots/{id}`, because on this DAI a PNG cannot be fetched straight from a log entry's `image_id`. | ORIENTATION §3.4 (B.7a) |
| **H12** | Only the **two proven** JIRA→suite ranges may be encoded. The appendix's 14-suite "approximate" table contradicts them and needs a **(User)** ruling. | ORIENTATION §6.4 |
| **H13** | The validation suite is the suite that **owns the failing test**, never the changed file's path. | M2, plan_master §6 invariant 13 |
| **H14** | **One identifier, one name.** The `{run_id}` in `/api/v2/test_results/{run_id}/logs` and `…/screenshots` **is** the test-result id returned by the second results call. There is no separate run identifier. The plans previously wrote `{test_result_id}` for logs and `{run_id}` for screenshots on adjacent lines of the same chain — a Part-7 "pairs that look alike" trap. | ORIENTATION §3.4 L201–L202 |

---

## 2. Per-file edit map

| # | Commit | File → section | Change | Rule |
|---|---|---|---|---|
| 1 | `b2959c6` | `plan_master` §2.3.4, §2.3.5 | Replaced *"derive suite from the affected file path"* with `validation_suite_of(run)` and its resolution order; made the trigger endpoint explicit (201 + `task_instance_id`); added `?limit=1000`; recorded the `/testconfiguration/{id}/results` 404 and the transient-500 note. | H13, H11 |
| 2 | `7e8e913` | `plan1` Step 1.2.4 | Added `output_model` to the signature; separated wire schema from local validator; specified both return types; stated the one-repair ceiling with its redaction limit; added immediate per-response charging; added `max_retries=0`; added the three-boundary table; recorded the adaptive-thinking shape. | H1–H6, H8 |
| 3 | `7fdddcb` | `plan0` B.1 actions 2–3, B.4 action 1, Gate 0b-VM | Added `version = "0.1.0"`; bumped the `anthropic` floor; removed the non-existent `validation` timeout key and pointed at `jarvis.run_timeout`; replaced the `C:\agent\repo` literal with `settings.working_copy_path`. | H7, H8, H9, H10 |
| 4 | `063ff3c` | `plan2` Step 2.5.2 | Enumerated the proven trigger and log endpoints from the canonical §2.3.5 and recorded the 404 route. | H11 |
| 5 | `2ee7548` | `plan1` Step 1.3.2 | Added a blocking constraint: only the two proven ranges may be encoded; the appendix table is contradictory and requires a ruling; an unresolved number must **raise**. | H12, H13 |
| 6 | `15d42d0` | `plan_master` §2.3.4/§2.3.5, `plan2` §2.5.2, `plan0` B.7a | **Correction to fix 1.** Added the missing `GET /api/v2/test_results/{run_id}/screenshots` call and renamed the chain to the **five-endpoint results/evidence chain** in all three places that enumerate it, plus `ValidationGate` step 6 and the `poc_jarvis_validation.py` spec. | H11 |
| 7 | `00bad76` | `plan1` Step 1.2.4, `plan_master` §2.3.4/§2.3.5, `plan2` §2.5.2, `plan0` B.7a | **Corrections from the review of fixes 1–6.** (a) Blank line after the three-boundaries table so **Verification** and **DoD** render as paragraphs rather than being absorbed as table rows by GFM. (b) Standardised `{test_result_id}` → `{run_id}` in all three chain enumerations, stated that the second call yields the `run_id`, and added the explicit *one identifier, one name* note. Code-fence arrow columns repadded (65 in `plan_master`, 54 in `plan0`). | H14 |

**No edit was made without a rule authorising it.** `plan4.md` was searched and needed no change —
it defines no Claude client signature, DAI endpoint, or working-copy path.
`plan3_lifecycle_rollout.md` §1 L13 *references* the chain ("the v2 results chain + screenshots
produced by the gate (plan2 §2.5.2)") but delegates rather than enumerating, and names no count, so
it stays correct without an edit and was deliberately left alone.

**Scope note on fix 6.** The brief named `plan_master` §2.3.4/§2.3.5 and `plan2` §2.5.2. `plan0`
B.7a was found to enumerate the same chain — also four calls, also missing `?limit=1000` — and the
`poc_jarvis_validation.py` spec at B.7a action 2 named the "four-call v2 results chain". Correcting
the canonical definition while leaving two stale copies is the M5 defect class the set-wide
consistency rule exists to prevent, so both were folded into the same commit.

---

## 3. Errors made inside the pass

### 3.1 Caught by the author, before the commit

Fix 3's first attempt **replaced** the *"Deliberately absent: `chromadb`, `sentence-transformers`,
Microsoft Graph SDK"* line with the new `version` note instead of adding alongside it — deleting a
real constraint that keeps the vector-DB dependencies out of the project. Caught immediately by the
post-edit grep, restored before the commit, and both lines are present at plan0 **L294–295**. This is
precisely the failure mode M10 describes: a deletion hiding inside an otherwise reasonable edit.

### 3.2 Missed by the author, caught by review

Three defects survived fixes 1–6 and were found only by the review of this branch. All three are
closed by fix 7 and by this log:

1. **A broken table.** The three-boundaries table added by fix 2 was inserted directly above the
   pre-existing **Verification** and **DoD** lines with no blank line between them. GFM continues a
   table until a blank line, so both lines would have rendered as table rows. A structural check
   that counts *headings* does not see this; nothing in the pass would have caught it.
2. **Two names for one identifier.** Fix 6 added a `{run_id}` line directly beneath a pre-existing
   `{test_result_id}` line in the same chain, in all three enumerations — exactly the Part-7
   "pairs that look alike and are not" trap, introduced while fixing a different defect. See H14.
3. **Wrong evidence in this log.** §5 claimed *"3 residual hits at L111/L114/L131"* for
   `C:\agent\repo`; there are **4**, at L112/L115/L132/L356. The conclusion held, but the cited
   numbers did not — the failure mode *"no number without a traceable source"* exists to prevent.
   The `plan0 L293–294` citation in §3.1 was likewise off by one and is corrected above.

**The lesson for the next pass.** Every one of these is a *line-level* defect in text the pass
itself wrote, and the pass's own verification was blind to all three: heading counts, fence parity,
protected-term counts and UTF-8 validity are all insensitive to them. Line numbers cited in a change
log must be re-derived **after the final commit**, never carried forward from the edit that
introduced them.

---

## 4. Structural check

Heading counts, base `4d08ded` → HEAD. **Zero headings lost.**

| File | Before | After | Δ |
|---|---|---|---|
| `plan_master.md` | 24 | 24 | 0 |
| `plan0_poc_and_foundation.md` | 32 | 32 | 0 |
| `plan1_diagnosis_and_chat.md` | 33 | 33 | 0 |
| `plan2_autofix_and_validation.md` | 21 | 21 | 0 |
| `plan3_lifecycle_rollout.md` | 28 | 28 | 0 |
| `plan4.md` | 46 | 46 | 0 |

Protected-term counts, identical match-counting on both sides:

| Term | Base | Head |
|---|---|---|
| `max_attempts: 3` | 1 | **2** (added to the boundary table) |
| `callers_pass` | 5 | 5 |
| `BudgetGuard` | 3 | 3 |
| `NOT_ONBOARDED` | 7 | 7 |
| `STALE_SYNC` | 11 | 11 |
| `Wilson` | 7 | 7 |

Nothing reduced.

---

## 5. Mechanical verification

| Check | Expected | Result |
|---|---|---|
| `derive suite from the affected` across all plans | 0 | **0** |
| `anthropic>=0.40` across all plans | 0 | **0** (now `>=0.120.2,<1`) |
| `output_model` present in `plan1` | ≥1 | **2** |
| `four-call` / ``four `GET` `` across all plans | 0 | **0** |
| `test_results/{run_id}/screenshots` enumerated | 3 plans | **4 hits** — `plan0` L64, `plan2` L131, `plan_master` L169 + L187 |
| `{test_result_id}` anywhere in the plans | 0 | **0** — unified on `{run_id}` (H14) |
| Blank line terminating the boundary table | yes | **yes** — table rows `plan1` L82–L84, blank L85 |
| `C:\agent\repo` occurrences in `plan0` | 4, none contradictory | **4** — L112 / L115 / L132 are **(User)** records inside *deferred* PoC steps A.3 and A.4; **L356** is the explicit *"the older `C:\agent\repo` literal is **superseded**"* note in B.4. No unresolved contradiction remains |
| Headings vs base, all six plans | Δ 0 | **Δ 0** |
| Markdown fences balanced, all six plans | even | **even** |
| Plan files still valid UTF-8 | 6/6 | **6/6** |
| `git diff --check` | clean | **clean** |

### Diff totals

| Scope | Files | Lines |
|---|---|---|
| **Plan files only** (vs pass base `4d08ded`) | 4 | **+56 / −23** |
| **Plans + Decision 005** (vs `master`, excluding this log) | 5 | **+143 / −23** |

Both figures **exclude this change log**, deliberately. A total that counts the document stating it
changes every time the document is edited and is stale the moment it is written; the two scopes
above are stable and independently reproducible:

```
git diff --shortstat 4d08ded..HEAD -- 'plan*.md'
git diff --shortstat master...HEAD -- 'plan*.md' 'docs/agent/decisions/*'
```

The full branch including this log is 6 files; that count is left unstated for the reason above.
The earlier entry in this table read *"4 files, +41 / −16"*. That was the plan-only total **before**
fix 6 and it did not say so; it is superseded here.

---

## 6. Open items this pass did **not** close

- **H12 — the suite-range ruling is Jay's.** The plan now *blocks* encoding rather than guessing.
  No range was invented. This needs a decision before Step 1.3.2 is built.
- **`ORIENTATION.md` §5.4 and §6.4 are stale** — §5.4 lists four passes when six have merged, and
  §6.4 still lists the five defects this pass closed. ORIENTATION is the Architect's file, not the
  Plan Steward's, so it was not edited here.
- **`PROGRESS.md` has no Step 1.2.4 tick.** That belongs to the build merge, not this pass.
