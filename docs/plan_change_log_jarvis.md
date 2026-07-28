# PLAN CHANGE LOG — JARVIS ALIGNMENT

**Branch:** `docs/jarvis-plan-alignment` · **Pre-edit checkpoint:** `e0f8be6` · **Date:** 2026-07-28

This file records **every** edit made during the JARVIS plan-set alignment, in the form
`section — what changed — why (rule/finding ID)`. It exists so a human can verify the edits did not
drift from the Prime Directive: **documentation surgery, not redesign.**

Rule IDs: **R1** project name → JARVIS · **R2** "Claude Code" (executor) → "Agent" · **R3** "Practice"
retired · **C1–C4** platform constraints · **D1–D5** ratified decisions · **S1/S2** SenseTalk rules ·
**O1–O7** open items · **UP-n** upgrade tags (never renumbered).

---

## PART 1 — CONSOLIDATED ⚠ CONFIRM (JAY) MARKER LIST

Twelve markers across six files. Each is a **placeholder, not a fact** — nothing below was invented.

| # | Question | File · section |
|---|---|---|
| **M1** | **JARVIS DAI host conflict.** The infra table now has **two rows naming `eggptdai10`** — the pre-existing *"EPF validation runner VM"* (156.140.21.30) and the new *"JARVIS DAI"* (observed `…:8000`). Both left standing deliberately. (a) Same VM or different? (b) Is the runner row obsolete now the local inner loop is deferred? (c) Exact JARVIS DAI base URL / scheme / port? (d) §1 advertises the chat app at `eggptdai10…:8080` while plan1 §1.6.3 says `aiagent-testmanager…:8000` — which host serves it? | `plan_master.md` §3 |
| **M2** | Same host/URL question, restated where an implementer meets it | `docs/context.md` §4 · `docs/poc_execution_guide.md` PoC 2b table |
| **M3** | **Constraint C3 is undefined.** The source brief gives C1, C2 and C4, but references "C1–C4" and cites C3 as the basis of open item O2. Provide C3's statement, or confirm that O2's collision behaviour *is* C3 and the range should read C1–C2, C4. | `plan_master.md` §2.3.1 · `docs/context.md` §5.1 |
| **M4** | **`ai-test-fix-agent` repo slug.** Left literal under R1 because renaming it in docs without renaming it in Bitbucket creates a false record. Is the repo being renamed to `jarvis`? | `plan_master.md` §4 · `plan0` A.0 step 1 · `plan0` B.1 step 1 (**note: 4 occurrences, not 3 — the `pyproject.toml` `name =` field is the fourth**) |
| **M5** | **`Jarvis-fix/` branch prefix + the `ai-*` Jira label set.** The prefix was renamed from `ai-fix/`; the 12 Jira labels were **not** renamed (operational identifiers agreed with the track team). Should either change? | `plan_master.md` §4.1 |
| **M6** | **Validation-repo PAT scopes.** What does a force-push to `refs/heads/Enovia` require (Repo Write plus a branch-permission exemption)? Same PAT as production, or separate? | `plan0` A.7 |
| **M7** | **`PartMaster` `TEST_CONFIG_ID` value** not recorded — needed for `tracks/enovia/test_config_registry.yaml` | `plan0` B.4b |
| **M8** | **O6 — multi-suite dispatcher regeneration policy.** Recommended invariant: *regenerate dispatchers for every registered suite on every push.* Recorded as a recommendation, **not settled fact** | `plan2` §2.5.0 · `PROGRESS.md` O6 |
| **M9** | **O3 — real per-cycle validation wall-clock timing** not yet measured; the Gate 2 timing row carries the marker | `plan2` GATE 2 |
| **M10** | **Model re-import runbook specifics:** exact export/import menu path; does re-import replace or duplicate an existing model; is `TEST_CONFIG_ID` stable across a re-import? These three answers turn the documented *shape* into an actual runbook | `docs/maintenance.md` §1 |

---

## PART 2 — CONFLICTS BETWEEN THE UPDATE BRIEF AND THE EXISTING PLAN TEXT

Flagged prominently rather than buried, per the brief's reporting requirement.

| # | Conflict | Resolution |
|---|---|---|
| **X1** | **Git remote name.** The brief's R3 rename table says remote `practice` → **`agentic-eggplant-automation`**, but §2.1, the §2.5 canonical flow block (`git push jarvis …`), §4.1.10 and §4.2.8 (`git remote add jarvis`) all said **`jarvis`** — 4 occurrences vs 1. | **Asked Jay; ruled `agentic-eggplant-automation`.** Applied everywhere, including inside the canonical flow block, which therefore differs verbatim from the brief's §2.5 listing. Jay's clarification: *"the repo name where the fix will first be uploaded is the `agentic-eggplant-automation` repository; jarvis is not the name of this bitbucket repo."* |
| **X2** | **`Base.md` does not exist.** The brief names it in the file inventory and explicitly rules it out of scope. | Nothing to leave alone and nothing created. Searched the whole `Jarvis/` tree — no such file. Recorded in Part 5. |
| **X3** | **`PROGRESS.md` history vs. verification check 2.** §4.7 says existing entries stay **verbatim**; §6 check 2 demands **zero** "Claude Code" hits across a file list that includes `PROGRESS.md`. Its line 9 records the gateway/model-whitelisting saga using that literal string. | **The specific instruction wins.** History left verbatim; one "Claude Code" hit survives in `PROGRESS.md` by design. It is a historical record of what happened on a date, exactly the rationale the brief uses to protect `Base.md`. |
| **X4** | **Open-item numbering.** §2.8 defines **O1–O5** with O5 = force-push vs multi-suite dispatchers, but §4.2.3 asks for "O1–O7", §4.4.4 and §5 call the multi-suite regeneration policy **O6**, and §4.5.6(a) calls the monthly re-import **O7**. | Reconciled without inventing: **O5** = the *observation* (dispatchers for non-target suites vanish on force-push); **O6** = the *policy decision* pending on it; **O7** = the monthly re-import person-dependency. All seven registered in `PROGRESS.md`. |
| **X5** | **"five new `JARVIS_*` keys".** §4.2.2 says add five; §3-R3 lists only **three** (`JARVIS_BRANCH`, `JARVIS_ENOVIA_SUITES_PATH_IN_VM`, `JARVIS_COMPLETION_MODE`). | Added the three named. Did **not** invent two more. (Five *renames* did occur: `PRACTICE_REPO_URL`/`_PAT`/`_DAI_BASE_URL`/`_DAI_CLIENT_ID`/`_DAI_CLIENT_SECRET` → `JARVIS_*`, plus one deletion — which may be what "five" referred to.) |
| **X6** | **`PRACTICE_STEP_SELECTION` does not exist** anywhere in the plan set, yet R3 instructs "record the resolution". | Recorded as a retired key in `plan0` A.0 and both env files, noting D1 resolved it. No occurrence was edited because none existed. |
| **X7** | **`Jarvis-fix/` vs `jarvis-fix/` casing.** §4.1.10 uses both spellings in the same sentence. | Standardised on **`Jarvis-fix/`** (4 occurrences vs 1 in the brief). Flagged as M5 for a definitive ruling. |
| **X8** | **`docs/` location.** The brief writes `docs/context.md` etc., but the plan set sits at repo root while the scaffold and existing `docs/poc_execution_guide.md` sit under `ai-test-fix-agent/`. plan3 §3.7 and plan4 §4.8.3 already reference `docs/maintenance.md` and `docs/rollout_contract.md` in the *project* repo's frame. | **Asked Jay; ruled `ai-test-fix-agent/docs/`.** This also makes the pre-existing in-plan `docs/…` references resolve correctly, so no marker was needed. |
| **X9** | **`scripts/poc_practice.py`** is not in R3's rename table, but §6 check 1 demands zero non-English "practice" hits. | **Asked Jay; approved for rename** → `scripts/poc_jarvis_validation.py`. Only references were updated; the file does not exist on disk yet. |
| **X10** | **Repo is not a git repository.** §1's safety protocol mandates a branch, a checkpoint commit and `git diff` as deliverables. | **Asked Jay; ruled "git init + full protocol".** `git init` run, `.gitignore` added at root first so `.env` and `.venv/` could never enter history, checkpoint `e0f8be6` committed on `master`, work done on `docs/jarvis-plan-alignment`, one commit per plan file. |

---

## PART 3 — AMBIGUOUS UNDER R2, LEFT UNRENAMED

The judgement rule: *is this about who builds the system, or what the system calls at runtime?*

**Result: no genuinely ambiguous cases required abandonment.** Every occurrence resolved cleanly. Two
worth naming because they look ambiguous at a glance:

| Occurrence | Decision |
|---|---|
| `plan_master` §6.10 — *"a shell that already has `ANTHROPIC_BASE_URL` set (e.g. an IDE / **Claude Code** session)"* | **Renamed → "Agent session".** Although it describes an incident, the referent is the *builder's* tooling environment, which R2 renames. Meaning preserved. |
| `plan0` A.9 — step title *"PoC 6: **Claude** reproduces the TESTAUTOMA-8055 diagnosis from the VM"* | **Kept.** The brief protects this title explicitly; here Claude is the model being called. Its Owner line *was* renamed to `Agent + (User)`. |

All other surviving `Claude` occurrences are the model, the API, `claude_client`, `claude-opus-*`,
`poc_claude.py` or `probe_claude.py` — each read individually and verified.

---

## PART 4 — PER-EDIT LOG

### `plan_master.md` — commit `f02577d`

| Section | Change | Rule |
|---|---|---|
| Title + audience | `AI TEST FIX AGENT (ENOVIA) — … (FOR CLAUDE CODE)` → `JARVIS (ENOVIA) — … (FOR THE AGENT)`; audience/scope reworded | R1, R2 |
| §0 heading | `HOW CLAUDE CODE MUST EXECUTE` → `HOW THE AGENT MUST EXECUTE` | R2 |
| §0 item 3 | Owner vocabulary `Claude Code` → `Agent` | R2 |
| §0 item 7 | Removed "the Practice DAI trigger"; **added**: anything touching the JARVIS DAI, its agents, or a validation-repo push is a **(User)** VM step | R3, brief §4.1.2 |
| §1 END STATE | Approval bullet scoped to *production* writes; Lifecycle bullet rewritten as two repos / one direction | R1, R3 |
| §2.1 Validation bullet | `INNER_LOOP` two-mechanism framing removed; single mandated mechanism = Tier-0 lint then the JARVIS validation gate; deferred-runscript sentence added | R3, D1–D5 |
| §2.1 Evidence flow | Clause added: chain reads the **production** DAI 25.3.1+0, distinct from JARVIS DAI 26.2.2, **different auth schemes** | brief §2.6 |
| §2.2 upgrades table | **Read, no change needed** — no UP row referenced the practice path. Not renumbered | brief §4.1.6 |
| **NEW §2.3** | *"THE VALIDATION FLOW (canonical)"* inserted after §2.2 with six sub-sections: C1–C4 (§2.3.1), D1–D5 (§2.3.2), dispatcher template (§2.3.3), canonical flow (§2.3.4), API + dual-auth (§2.3.5), S1/S2 (§2.3.6). **§3–§8 keep their numbers** | brief §4.1.7 |
| §3 infra table | Four Practice rows → eleven JARVIS rows; ⚠ M1 inserted after the table; every other row untouched | R3, brief §4.1.8 |
| §4 repo layout | `practice_gate.py`→`validation_gate.py`, `practice_dai.py`→`jarvis_dai.py`, `poc_practice.py`→`poc_jarvis_validation.py`; added `dispatcher.py`, `templates/agent_dispatcher.st.j2`, `test_config_registry.yaml`; ⚠ M4 at the root-directory line | R3, D3/D4 |
| §4.1 | Two remotes named explicitly; "exists remotely exactly twice" restated; **D4 rule added**; ⚠ M5 inserted | R3, D4 |
| §6 item 4 | Practice-branch invariant → validation-repo invariant; **two new invariants** (double SHA assert; dispatcher never reaches production) | R3, UP-24, D4 |
| §6 item 10 | `Claude Code session` → `Agent session` | R2 |
| §6 item 11 | R3 terminology; points at plan2 §2.5; `JARVIS_COMPLETION_MODE`; $0-during-wait restated | R3 |
| **NEW §6 item 12** | SenseTalk S1/S2 recorded as a coding convention | S1, S2 |
| §7 Gate 0a row | *"PoC 2b Practice path"* → *"JARVIS validation path"*, marked proven; either/or framing dropped | R3 |
| §8 DoD | R1/R3; two-repo direction made explicit | R1, R3 |

### `plan0_poc_and_foundation.md` — commit `2054fd2`

| Section | Change | Rule |
|---|---|---|
| Title, intro, division-of-labor | R1/R2/R3; added "every one-time DAI setup is done by (User) Jay" | R1–R3, D2 |
| A.0 action 1 | ⚠ M4 added | R1 |
| A.0 action 2 | 5 × `PRACTICE_*` → `JARVIS_*`; **`PRACTICE_TEST_CONFIG_ID` deleted** with a superseded-by-D3 note; `PRACTICE_STEP_SELECTION` recorded as resolved by D1; 3 new `JARVIS_*` keys. `MODEL=claude-opus-4-7` and the dotenv note **untouched** | R3, D1, D3 |
| **A.2 rewritten** | Same number + Owner/Goal/Actions/Verification/DoD skeleton. New goal = the JARVIS cycle. "(User) provide" → a recorded-values table. Auth + v2 results chain documented. **All three completion options kept** as the decision record; `poll_backoff` selected, webhook = O1. Marked **PROVEN**; O1–O7 tabled | R3, brief §4.2.3 |
| **NEW A.2b** | *"Dispatcher pattern proof (dynamic target selection)"*, Owner `Agent + (User)`, incl. the broken-target negative test. Marked **PROVEN** on `Part_Master_Pack_01` | C1, D1, S1, S2 |
| A.3 / A.4 / A.5 | **Not deleted.** Each retitled `*(DEFERRED — optional latency optimisation…)*` + a deferral note. A.4 DoD: `INNER_LOOP` → `VALIDATION_MECHANISM=jarvis-dai`; local variant recorded but unselected | R3, brief §4.2.5 |
| A.6, A.8, A.9, A.10 | Owner lines + action prefixes only. **A.9's title kept** | R2 |
| A.7 | Production-repo scope clarified; validation-repo force-push called out as a separate PAT; ⚠ M6; `ai-fix/POC-TEST` → `Jarvis-fix/POC-TEST` | R1, R3 |
| B.1 action 1 | ⚠ M4 (repo slug + `pyproject.toml` name) | R1 |
| B.1 action 3 | `practice:` block → a fully shaped `jarvis:` YAML block; `validation.inner_loop` → `mechanism: jarvis-dai`; **`max_attempts: 3` and `n_best_on_retry: 2` unchanged** | R3, D3 |
| B.3 action 2 | `practice_*` settings → `jarvis_*`, noting there is no test-config scalar; `inner_loop` → `validation_mechanism` | R3, D3 |
| B.4 action 1 | `git remote add practice` → `git remote add agentic-eggplant-automation`; both repos named; **third scheduled task** for `C:\Eggplant_Suites` | R3, X1 |
| **NEW B.4b** | *"JARVIS suite onboarding + test-config registry"*, Owner `(User), scripts and registry schema by Agent`. D2 sequence verbatim (10 steps). ⚠ M7. DoD: PartMaster **done**, rest = O4 | D2, D3 |
| B.7 + GATE 0b | Practice dry-run → JARVIS line with both SHA asserts; checklist rows added for the registry and the asserts; remotes named | R3, UP-24 |
| GATE 0a | PoC 2b row **proven**; new A.2b row; 1/1b/1e → `n.a. (deferred)`; Rule paragraph either/or → JARVIS path must pass. **PoC 7 requirement preserved exactly** | R3 |

### `plan1_diagnosis_and_chat.md` — commit `8328551`

| Section | Change | Rule |
|---|---|---|
| Title, Owner lines, action prefixes | R2 throughout; project name → JARVIS; DAI qualified as **production** | R1, R2 |
| §1.1.1 `RunStatus` | **Both** `validating_local` and `validating_dai` kept (removing an enum member would be an architecture change); each annotated with its mechanism | brief §4.3.4 |
| §1.2.3 `dai_client.py` | Note added: targets the **production** DAI; the JARVIS client is separate (`jarvis_dai.py`, plan2 §2.5) with a different auth scheme; **do not merge** | brief §4.3.3 |
| Everything else | **Deliberately untouched** — every prompt, tool, schema, gate metric and the 8055 golden regression | brief §4.3.5 |

### `plan2_autofix_and_validation.md` — commit `e53908f`

| Section | Change | Rule |
|---|---|---|
| Header | Only remote write = force-push to `agentic-eggplant-automation@Enovia`; production untouched until plan3; UP-24 invariant added; `INNER_LOOP` sentence replaced; build order includes 2.5.0 | R3, UP-24 |
| 2.1 / 2.2 / 2.3 | **Renames only.** Fix generator, anchor contract, applier, lint gate unchanged | R2 |
| 2.4 | Retitled `*(DEFERRED — optional latency optimisation)*`, content kept, "every attempt is validated by the JARVIS gate" added | R3 |
| **NEW 2.5.0** | Dispatcher generator: `dispatcher.py` + template; `suite_of` / `target_ref` (S1) / `render` (S2) / `write_and_commit`; unit tests incl. **no `try/catch` in output**; D4 rule; ⚠ M8 | C1, D1, D4, S1, S2 |
| 2.5 title | *"The Practice gate"* → *"The JARVIS validation gate"*; phase number kept | R3 |
| 2.5.1 | Confirm JARVIS wiring: registry lookup, v2 creds, `branch: Enovia`, completion mode; drift note reframed | R3, D3 |
| 2.5.2 | `practice_dai.py`+`practice_gate.py` → `jarvis_dai.py`+`validation_gate.py`; **wait-path invariant kept verbatim in substance**; `auth()` / `trigger()` / four-call chain; all three completion modes kept; 8-step flow under the lock with **both mandatory UP-24 asserts**; `STALE_SYNC` never a verdict; cross-ref to plan4 §4.7.2 rather than duplicating; `$0` verification | R3, UP-24 |
| 2.6 pseudocode | Two-branch oracle → single `validation_gate.validate(...)`; dead local-runscript block removed; `STALE_SYNC` handling added. **Attempt cap 3, N-best, extended thinking, `callers_pass`, `BudgetGuard`, fresh re-diagnosis and every event unchanged** | R3 |
| 2.6 design notes | No longer describes two oracles | R3 |
| 2.7 | **Renames only** | R2 |
| 2.8 | *"including Practice-repo pushes"* → force-pushes to `agentic-eggplant-automation@Enovia`; "pushes nothing to the production repo" kept | R3 |
| GATE 2 | Timing row → `< 30 min per attempt (JARVIS gate)` + ⚠ M9. **Every other threshold unchanged** | R3, O3 |

### `plan3_lifecycle_rollout.md` — commit `01aeeb3`

| Section | Change | Rule |
|---|---|---|
| Title, Owner lines, prose | R1/R2/R3 | R1–R3 |
| 3.1 | **Both evidence sources named** (JARVIS run vs original production-DAI evidence) so the packager cannot be misdirected; "zero Graph/SharePoint" kept | brief §4.5.2 |
| 3.2.1 | `origin` stays production; branch → `Jarvis-fix/<TICKET>`; commit prefix → `[JARVIS]`; **hard D4 rule added** (exclude every `*_AgentDispatcher.script`, assert none in the diff) | R1, D4 |
| 3.2.3 | PR Validation line → `lint: PASS · JARVIS gate: PASS (test_config_result <id>, commit <sha>) · attempt n/3`; footer → `_Generated by JARVIS…_` | R1, R3 |
| 3.2 DoD | Dispatcher-exclusion assert added to the DoD | D4 |
| 3.4.2 | Rule 2 `Practice gate TIMEOUT` → `JARVIS gate TIMEOUT`; `NO_LICENSE` kept; **NEW sixth rule** for `STALE_SYNC`. Verification/DoD updated five → six | R3, UP-24 |
| 3.6.1 | `practice_gate_result` → `jarvis_gate_result`; added `dispatcher_target`, `pushed_sha`, `executed_commit_sha`, `test_config_id`; rest unchanged | R3, UP-24 |
| 3.7 | Three JARVIS items added: monthly re-import (**O7**, written up in `docs/maintenance.md`), the `C:\Eggplant_Suites` pull, registry upkeep + O2 re-check. **Weekly cadence and `verify_context.py` unchanged** | brief §4.5.6 |
| GATE 3 | One row added (*"Executed-commit SHA asserted on every validation run"*). **Thresholds unchanged** | UP-24 |
| Project DoD | R1/R3; two-repo direction explicit | R1, R3 |

### `plan4.md` — commit `b0e000b`

| Section | Change | Rule |
|---|---|---|
| Title, Owner lines, hand-off line | R2. **Execution slot `0 → 1 → 2 → 4 → 3` kept exactly** | R2 |
| §0.1 UP-24 row | Retitled *"JARVIS-run integrity check"*; "What changes" → the double assert; "Proved by" notes it is now fully implementable. **UP-16…UP-25 not renumbered** | UP-24 |
| §4.0 item 1 | **Untouched** (the Opus 4.6 interpretation rule) | — |
| §4.0 item 3 | Marked **RESOLVED** with both answers (webhook admin access → O1; run→commit visibility → yes). Cost-of-skipping note kept as historical rationale | brief §4.6.2 |
| §4.2.2 | *"via the active `INNER_LOOP` mechanism"* → *"via the JARVIS validation gate"*. Baseline caching unchanged | R3 |
| §4.7.2 | Retitled *"JARVIS-run integrity check"*; remote/branch renamed; **only the fallback-WARN clause removed** — both asserts now mandatory; `STALE_SYNC` and "no verdict is trusted" kept; note that plan2 §2.5.2 implements it, so this step is enforcement + testing | UP-24, R3 |
| §4.9, Gate 4 | Terminology only; SHA-assert row reworded for both edges. **Thresholds unchanged** | R3 |

### `PROGRESS.md` — commit `4031832`

| Change | Rule |
|---|---|
| **Existing entries left verbatim**, including the gateway/model-whitelisting saga (see conflict X3) | brief §4.7 |
| Four entries appended for A.2, A.2b, B.4b and docs, dated **2026-07-28** (the real current date) | brief §4.7 |
| **O1–O7 register table added** so the open items cannot vanish, with a pointer to Part 1 of this file | brief §4.7 |

### Out-of-brief files (included by Jay's explicit instruction) — commit `4031832`

| File | Change |
|---|---|
| `docs/poc_execution_guide.md` | PoC 2b rewritten to the proven JARVIS path — the old Keycloak + `execution_service/api/v1/executions` + `/ai/runs` sketch replaced by `POST /api/v2/auth` and the four-call v2 results chain, since the former was superseded by what was actually proven. New **PoC 2b-bis** dispatcher section with the template, S1/S2 and the no-`try/catch` rationale. PoC 1b marked deferred. Gate 0a checklist and suggested execution order updated. R1/R2/R3 throughout. |
| `.env.example` | Header → JARVIS; production-DAI block annotated as read-only with its auth scheme; `PRACTICE_*` → `JARVIS_*` with the three new keys; retired keys documented in comments; `VALIDATION_MECHANISM=jarvis-dai` added. |
| `.env` | **Keys renamed only — no values touched** (all six were empty). Same retired-key comments. File is gitignored and remains untracked; a pre-edit backup was taken to the session scratchpad before editing, since git could not have restored it. |
| `scripts/poc_practice.py` | **References only** renamed → `poc_jarvis_validation.py` (in `plan_master` §4, `plan0` A.2 and the guide). The file does not exist on disk yet, so nothing was moved. |
| `.gitignore` (new, repo root) | Added **before** `git init` so `.env`, `.venv/` and `data/` could never enter history at any depth. |

### New documents — commit `4031832`

| File | Purpose |
|---|---|
| `docs/context.md` | The full project explanation required by the brief's standing instruction: architecture, approach, code layout, every part covered in detail rather than summarised. Opens with a prominent warning distinguishing it from `tracks/enovia/context.md`. |
| `docs/later-enhancements.md` | Deferred work: the local `runscript` inner loop, the webhook upgrade path (O1), additional SUTs on JARVIS test configs (with the concurrency caveat), scale-out (O4) — plus an explicit list of things decided *against*, so deferrals are not mistaken for reversals. |
| `docs/maintenance.md` | The monthly production→JARVIS model re-import written up as a procedure with its C4 re-authoring consequences and registry impact, flagged as person-dependency **O7** with three CONFIRM markers where the runbook is genuinely unknown. Plus scheduled-job verification, registry upkeep, and the eval-on-change rule. |

---

## PART 5 — DELIBERATELY NOT TOUCHED

| Item | Why |
|---|---|
| `Base.md` | Declared out of scope: a historical narrative where the old names are literally accurate for what happened on specific dates. **The file does not exist in this repository** (conflict X2) — nothing to leave alone, nothing created. |
| `AI Agent Test Manager` · `Test Automation Scripts Maintenance & Development` · all `TESTAUTOMA-*` keys · `aiagent-testmanager.cos.is.keysight.com` | Real, external identifiers protected by R1. Verified still present and unmodified. |
| The 12 `ai-*` Jira labels | Operational identifiers agreed (or to be agreed) with the track team. Left as-is under one marker (M5). |
| `ai-test-fix-agent` repo slug (4 occurrences) | Real Bitbucket slug; marked (M4), not renamed. |
| `claude_client.py` · `claude-opus-4-7` · `ANTHROPIC_*` · `poc_claude.py` · `probe_claude.py` · every runtime "Claude" | R2 protects the model/API sense. Each occurrence read individually. |
| Literal "Opus 4.6" in passing prose | plan4 §4.0 item 1 already supplies the standing interpretation rule and explicitly says not to edit the files for it. |
| Every gate threshold | ≥75%, ≥60%, ≥80%, ≥90%, 0 regressions, 0 post-merge regressions, hard zeros — all verified unchanged. |
| Every Phase / Step / Gate / UP-n number | Verified against the pre-edit heading baseline. Only additions: A.2b, B.4b, 2.5.0, §2.3, plan_master §6.12, plan3 degradation rule 6. |
| The diagnosis architecture, chat/event contract, SQLite schema, approval/HITL design, and plan4's triage/verdict/`ask_human` design | Explicitly protected by the Prime Directive. Untouched. |
