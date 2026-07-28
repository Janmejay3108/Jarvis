# PLAN CHANGE LOG — JARVIS ALIGNMENT PASS 2

**Branch:** `docs/jarvis-alignment-2` · **Base:** tag `plan-set-jarvis-v1` (`d461650`) · **Date:** 2026-07-28

Pass 1's log is `plan_change_log_jarvis.md` and is **not** superseded by this file — the two are read
together. This one records the repo restructure, the slug retirement, the fact closures, and the two
markers that survive.

Rule IDs: **F1–F13** facts supplied by Jay on 2026-07-28 · **R1** project name · **R3** "Practice" retired ·
**C1–C4** platform constraints · **D1–D5** ratified decisions · **S1/S2** SenseTalk rules · **O1–O7** open items.

---

## PART 1 — MARKERS STILL OPEN AFTER THIS PASS

**Two, and only two.** Every other pass-1 marker is closed by the facts in §2 of the pass-2 brief.
Both survivors share a property: neither can be answered by discussion — each needs something to run.

| # | Question | Where | Why it cannot be closed yet |
|---|---|---|---|
| **1** | **Real per-cycle validation wall-clock timing (O3).** | `plan2` GATE 2, "avg fix+validation time" row | Measurable only once the JARVIS gate runs for real across a realistic suite set. The row carries `< 30 min per attempt` as the target with the marker attached. |
| **2** | **Model re-import runbook specifics.** The exact export/import menu path; whether a re-import **replaces** or **duplicates** an existing model; whether `TEST_CONFIG_ID` **survives** a re-import. | `docs/maintenance.md` §1 | Answerable only by walking through one re-import. Until then O7 stands: JARVIS validation correctness depends on one person remembering both to do this and how. |

**Closed by this pass:** JARVIS DAI base URL · the `eggptdai10` two-row conflict · which host serves the
chat app · the PartMaster `TEST_CONFIG_ID` · validation-repo PAT scopes · the `Jarvis-fix/` prefix and the
`ai-*` label set · the repo slug · the O6 regeneration policy · the statement of constraint C3.

---

## PART 2 — CONFLICTS BETWEEN THE PASS-2 BRIEF AND REALITY

Flagged rather than buried, same contract as pass 1.

| # | Conflict | Resolution |
|---|---|---|
| **Y1** | **The flatten had already been done, manually, outside git.** §3.1 describes the nested directory as `jarvis/`; it actually carried the project’s former slug (the literal is preserved in pass 1’s log), and Jay had already moved every entry to the root with the OS rather than `git mv`. Git therefore saw 13 deletions + 13 untracked additions. | Staged with rename detection rather than reconstructing the move. Git recorded **13 renames with zero content churn**, so history follows the files exactly as `git mv` would have produced. Verified in the commit's `--stat -M`. |
| **Y2** | **`ARCHITECTURE.md` does not exist.** §3.1 lists it as currently at the repo root, §3.2 lists it in the target tree, and §3.3(4) asks for its relative link to `plan_master.md` to be verified. It is absent from the whole tree, and no plan step creates it. | **Asked Jay; ruled skip.** Nothing verified, nothing created, and it is not listed in `plan_master` §4's tree. (`README.md` is also absent but legitimately so — plan0 B.1 creates it.) |
| **Y3** | **§10.12 references "§3.3(6)", which does not exist** — §3.3 has four items, and "the two-`origin` distinction" is never defined. | **Asked Jay; confirmed** it means: the **JARVIS project repo's** `origin` (→ Bitbucket `jarvis`) versus the **Enovia working copy's** `origin` (→ `enovia-plm-test-automation`). Two unrelated clones, same remote name. Written into `plan_master` §4.1 and cross-referenced from `plan0` B.1. |
| **Y4** | **The root `.gitignore` had been replaced** by the old project-level copy during the manual flatten, losing pass 1's defensive `**/` patterns. | Restored with `**/` coverage for `.env`, `.venv/`, `data/` and `__pycache__` at any depth, and the now-redundant nested `.gitignore` deleted. `.env` verified untracked. |
| **Y5** | **§3.4's occurrence list is incomplete.** It names `plan_master` §4, `plan0` A.0 step 1, `plan0` B.1 step 1 (+ `pyproject.toml`) and `docs/context.md`. It omits `docs/poc_execution_guide.md:47`, which carried the retired slug inside a stale local dev path (under a different Windows username). §10.1 requires zero hits outside pass 1's log. | Fixed the guide line too, replacing the machine-specific path with a neutral "from the project root" comment. Logged here rather than silently. |
| **Y6** | **F10 asks for an edit to pass 1's log**, which §3.4 otherwise protects as historical record. | Treated F10 as the more specific instruction and applied it narrowly: the Base.md rows in pass-1's Part 2 (X2) and Part 5 are struck through with a pointer here, rather than deleted outright — the audit trail stays legible while the carry stops. **Flagged prominently, because it is the one place this pass writes into a file pass 1 declared protected.** |
| **Y7** | **§10 numbers two different checks "8"** (mechanical 8 and semantic 8). | Cosmetic; both were run. No action. |

---

## PART 3 — PER-EDIT LOG

### Repo restructure — commit `d8a4a8b`

| Change | Why |
|---|---|
| 13 entries moved from the nested project directory to the repo root, staged as **git renames** | §3.2/§3.3 — repo root becomes project root, so a clone of `jarvis` does not produce `jarvis/jarvis/src/…` |
| Nested `.gitignore` removed; root `.gitignore` restored with `**/` depth patterns | §3.3(3) + Y4 |
| `config/`, `src/`, `webapp/` deliberately **not** created | §3.2 — plan0 B.1 creates them, at this root |
| `.env` verified untracked; no secret entered history | §3.3(3), §10.4 |

### `tracks/enovia/test_config_registry.yaml` — **NEW** (commit `d8a4a8b` onward)

| Change | Why |
|---|---|
| Created with the header comments and the PartMaster row: `suite_dir`, `model`, `test_config_id`, `dispatcher_script`, `smoke_target`, `onboarded`, `status` | §4 + **F1** + **F13** |
| Header records that a suite absent from the file is **not validatable**, and that adding a suite is a **data** change, never a code change | §4 + §5 |
| Header records the F8 consequence: a suite with no `smoke_target` is a **hard error at onboarding time** | §4 tail |
| Verified by parsing: `yaml.safe_load(...)['suites']['PartMaster']['test_config_id']` returns the F1 ID | §10.5 |

### `plan_master.md` — commit `3248858`

| Section | Change | Rule |
|---|---|---|
| §1 | Chat app at `eggptdai10:8080` confirmed **correct and kept**; co-location rationale added; note that 8080 must be **confirmed free at deploy time** since the DAI holds 8000 | F11 |
| §2.3.1 | **C3 stated**: a DAI git connection binds one repo to exactly one branch — *this is why validation force-pushes one permanent branch rather than a branch per ticket*. The `C1–C4` range now reads correctly | F4 |
| §2.3.2 D4 | Every-suite regeneration stated as a **rule**, not a recommendation, with the `smoke_target` hard-error consequence | F8 |
| §2.3.3 | Dispatcher template corrected to the **proven** script: `AgentDispatcher:`-prefixed log lines, the retained `Value = path relative to Scripts/` comment (states S1 at point of use), JARVIS header. Assertion guidance: **key off the prefix only, never the full line** — the em dash is non-ASCII and encoding must not break a verdict | §4.1 |
| §3 | Two `eggptdai10` rows **collapsed into one JARVIS VM row** carrying every role; EPF-runner **role** marked deferred while the **machine** stays; `aiagent-testmanager` row **kept** and re-labelled superseded-but-retained; CONFIRM block replaced by a two-line port map | F2, F3, F11 |
| §4 | Tree root is `jarvis`; `docs/` and `samples/` added; slug note replaced the CONFIRM | F5 |
| §4.1 | Branch-prefix CONFIRM replaced by settled naming; the 12 `ai-*` labels explicitly unchanged; **NEW** two-`origin` distinction | F7, Y3 |
| §6 | **NEW invariant 13** (`NOT_ONBOARDED`), appended after item 12 — nothing renumbered | §5 |

### `plan0_poc_and_foundation.md` — commit `c746b4b`

| Section | Change | Rule |
|---|---|---|
| A.0 step 1 | Repo root *is* project root; CONFIRM deleted | F5 |
| A.0 step 2 | `JARVIS_DAI_BASE_URL` documented as the real value shape. **Key names only — no client secret in any tracked file** | F2, §6.2.1 |
| A.2 | JARVIS DAI row carries the real HTTPS base URL and the co-location note | F2 |
| A.2 open items | O2's **C3→C2 citation corrected**; O5 marked **mitigated** but kept; O6 marked **resolved** with rule + date | F4, F8 |
| A.7 | PAT-scope CONFIRM replaced by the settled fact — Jay holds admin, force-push works, no exemption outstanding | F6 |
| A.9 | **Reworded to what was actually proven**: connectivity + credentials, from the development machine. The two claims it does *not* make are named, each with where it **is** discharged | F9 |
| B.1 step 1 | The `jarvis` repo **already exists and is empty**; what remains is default branch, ≥1-approval rule, PAT. `pyproject` name → `jarvis`. Two-`origin` cross-reference | F5, Y3 |
| B.1 `jarvis:` block | `dai_base_url` filled | F2 |
| B.4b | Action 8 points at the now-existing registry, states the `smoke_target` hard-error rule, carries the worked PartMaster row; DoD cites the real config ID and names the remaining **16** suites | F1, F8, F13 |
| B.7 | Host → `eggptdai10`; **F12 note** on where development actually happens, without weakening the VM-bound steps; Claude ping labelled as the VM-egress check folded in from A.9 | F11, F12, F9 |
| GATE 0a | PoC **2**, **5**, **6** ticked with PROGRESS evidence + dates; **3, 4, 7** left unticked with consequences named; Rule paragraph untouched; PoC 7 stays required | §7, F9 |

### `plan2_autofix_and_validation.md` — commit `c7a4d5c`

| Section | Change | Rule |
|---|---|---|
| §2.5.0 | Registry named as the **runtime** input; `load_registry()` and `render_all()` added; `suite_of()` — **an unresolved key is an error, never a fallback**; F8 regeneration stated as a rule; CONFIRM deleted; unit tests extended (render_all, missing `smoke_target` raises, `suite_of` raises); assertion rule on the `AgentDispatcher:` prefix | §4, §4.1, F8 |
| §2.5.2 | **NEW step 0 pre-flight**: unregistered suite → `NOT_ONBOARDED` **before any push or trigger**, routed to diagnose-only with the existing `ai-diagnosis-only` label; never a fallback to another suite's config; never PASS or FAIL. Step 2 regenerates all registered suites. Verification gains the unregistered-suite case | §5 |
| §2.6 | `NOT_ONBOARDED` **does not consume an attempt** and is **not retried** — retrying cannot change the registry; run ends diagnose-only with artifacts preserved | §5 |
| Everything else | **Untouched** — attempt cap 3, N-best, `callers_pass`, `BudgetGuard`, every published event | §6.4 |

### `plan1` · `plan3` · `plan4`

| File | Change | Rule |
|---|---|---|
| `plan1` §1.6.3 | `http://aiagent-testmanager…:8000/` → `http://eggptdai10.cos.is.keysight.com:8080/`. **This is the one file that changes on that point** — plan_master §1 was already correct | F11, §6.3 |
| `plan3` | **No change.** §3.2's D4 dispatcher-exclusion assert **verified intact** from pass 1; `Jarvis-fix/` casing already consistent; **no degradation rule added** for `NOT_ONBOARDED`, per §5 | §6.3, §5 |
| `plan4` | **No change.** Casing already consistent; nothing in F1–F13 touches the triage/verdict/`ask_human` design | §6.3 |

### `PROGRESS.md`

| Change | Rule |
|---|---|
| B.4b entry **verified, not assumed**, and extended with the config ID, suite dir, model and smoke target so the claim is self-evidencing | §8.1 |
| One new entry appended for this pass (flatten, slug, registry, markers closed), dated 2026-07-28 | §8.2 |
| Open items: O1/O3/O7 unchanged; **O2** C3→C2 citation corrected; **O4** flagged as the biggest scaling item with the 16-suite count; **O5 mitigated but kept visible**; **O6 resolved** with date | §8.3 |
| Existing history left **verbatim**, including the one surviving "Claude Code" reference (pass-1 conflict X3) | §8.4 |

### `docs/`

| File | Change |
|---|---|
| `context.md` | Machine table collapsed to the JARVIS VM + superseded ORCH row, with the port map, the co-location rationale, the deferred-role note and the F12 development-location note. C3 stated. Protected-identifiers row for the slug struck and replaced. Dispatcher template corrected + regeneration rule. O4/O5/O6 rows updated. The "awaiting an answer" list cut from nine items to **two**, with the closed ones listed as answered. Document map gains `plan_change_log_jarvis_2.md` and the registry. |
| `poc_execution_guide.md` | Machine table cut from three to two, with the superseded-host and deferred-role notes. PoC 6 retitled and rewritten to connectivity-only from the development machine, with the two claims it does not make. Gate 0a row and execution order updated. Dispatcher template corrected. Stale local dev path replaced (Y5). PAT and base-URL markers closed. |
| `plan_change_log_jarvis.md` | **Only** the two Base.md entries struck through with a pointer here (Y6). Nothing else touched — pass 1's record stands. |
| `maintenance.md` | Unchanged. Its three CONFIRM questions are the surviving marker 2. |
| `later-enhancements.md` | Unchanged — the deferral set is unaffected by F1–F13. |

---

## PART 4 — RETIRED CARRIES

| Item | Why retired |
|---|---|
| **`Base.md`** | It does not exist and never will in this repo. Pass 1 recorded it as conflict X2 and listed it under "deliberately not touched", which meant every reader had to re-discover that there was nothing there. Carrying a placeholder for a file that will never exist is noise, so both entries are struck through and this line is the record (**F10**). |
| **The project’s former slug** | Retired as a repo name, a directory name and a package name. The Bitbucket repo is `jarvis` and it exists. The literal survives **only** in `plan_change_log_jarvis.md`, where it is a record of a decision made on a date — the same protection pass 1 gave `PROGRESS.md`'s history (**F5**). |
| **The `[ORCH]` / `[RUNNER]` two-VM split** | One machine, `eggptdai10`, now holds every role. The EPF-runner *role* is deferred with the local inner loop; the *machine* is not obsolete. `aiagent-testmanager` is retained as a hostname because it belongs to a real, separate org-level initiative (**F3**, **F11**, R1). |
