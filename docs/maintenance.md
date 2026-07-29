# JARVIS — MAINTENANCE PROCEDURES

**Last updated:** 2026-07-28 · **Owner of every procedure below: (User) — Jay**

This file is referenced by plan3 §3.7. It exists because several JARVIS operations are currently
**manual activities that live in one person's head**. Writing them down is the point.

---

## 1. Monthly model re-import from production DAI → JARVIS DAI ⚠ **O7 — person-dependency**

**Status: currently an undocumented manual activity. It MUST become a written procedure.** This
section is the placeholder that procedure goes into — the steps below are the *known shape* of the
task, derived from decision D2 and constraint C4; **they are not a verified runbook** until Jay has
walked through one re-import and filled in the specifics.

**Cadence:** monthly. **Performed by:** Jay. **Cannot be automated today** — the DAI public API v2
exposes no test-config or step create/edit endpoints (**C1**), so the re-authoring steps are UI work.

> ### This is a PER-MODEL procedure, repeated for EVERY onboarded model
>
> There is **one model per suite** (**D2**), so this is not a single narrative you walk once a month —
> it is the loop below **run once per onboarded suite**, every month. Today that is one model
> (`PartMaster`). **At 17 suites it is seventeen**, each with its own export, import, association check,
> re-authoring pass, registry check and smoke run — all of it **UI work that cannot be automated (C1)**.
>
> **That makes this the dominant recurring cost of the whole system, and it scales linearly with O4.**
> Every suite onboarded adds a permanent monthly obligation. Weigh that when ordering O4 (A.10a's
> frequency count exists partly so the highest-value suites are onboarded first), and revisit whether
> the monthly cadence is right per-suite — a rarely-changing suite may not need re-importing as often
> as a volatile one.
>
> **Per-model checklist — copy one block per onboarded model, each month:**
>
> ```
> [ ] <Suite> — exported from production DAI
> [ ] <Suite> — imported into JARVIS DAI
> [ ] <Suite> — suite association re-verified
> [ ] <Suite> — AgentDispatcher action + snippet present (re-created if lost)
> [ ] <Suite> — test case (cleanupSUT + AgentDispatcher) present
> [ ] <Suite> — test config present; SUT by name, reruns OFF, generous timeout
> [ ] <Suite> — test_config_id re-checked against tracks/enovia/test_config_registry.yaml
> [ ] <Suite> — smoke validation PASSED, executed commit SHA visible in the run log
> [ ] <Suite> — O2 name-collision re-check (only if suites were added since last import)
> ```

**Why it is needed.** JARVIS validates against models imported from the production DAI. Production
models drift as the application and the suites evolve. A stale imported model means JARVIS validates
against a world that no longer exists — the failure mode is a **confidently wrong PASS**, which is
exactly what the rest of this system is built to prevent.

**Known shape of the procedure — run this whole sequence once per onboarded model:**

1. Export the suite's model from the **production** DAI (`epcorpappsdai12`, DAI 25.3.1+0).
2. Import it into the **JARVIS** DAI (26.2.2).
3. **Re-verify the suite association** on the imported model.
4. **Re-authoring required after every import (C4):** a model export restores internal structure but
   **not** suite links or test configs. Therefore confirm — and re-create if lost:
   - the `AgentDispatcher` model action and its attached `<Suite>_AgentDispatcher.script` snippet;
   - the test case (`cleanupSUT` + `AgentDispatcher`);
   - the model-based test config (SUT **by name**, **reruns OFF**, generous run timeout).
5. **If the test config was re-created, its ID may have changed.** Re-record it in
   `tracks/enovia/test_config_registry.yaml` (**D3**) — a stale registry entry will trigger the wrong
   config or none at all.
6. Run **one smoke validation** through the gate and confirm the executed commit SHA appears in the
   run log.
7. Re-check **O2** (suite-name collisions) if suites were added since the last import (**C2**: suite
   names must be globally unique across a DAI instance).

> ⚠ **CONFIRM (Jay):** the exact export/import menu path, whether the re-import replaces or duplicates
> an existing model, and whether `TEST_CONFIG_ID` is stable across a re-import — placeholder, not a
> fact. These three answers turn the shape above into an actual runbook.

**Until this is written up, O7 stands: JARVIS validation correctness depends on one person remembering
to do this, and on remembering how.**

---

## 2. Scheduled jobs (automated — verify, don't perform)

Registered in plan0 §B.4 action 1. These need **checking**, not doing:

| Job | Cadence | Host | Purpose |
|---|---|---|---|
| `git pull --ff-only` on the working copy | hourly | orchestrator VM | keeps `Testing_Mar10` current for diagnosis + patching |
| Rebuild `handler_map.yaml` + `handler_vocabulary.json` | nightly | orchestrator VM | derived code knowledge never goes stale without human effort |
| `git pull` on `C:\Eggplant_Suites` | scheduled | **JARVIS VM** | the Design agent's local suites folder tracks the validation repo |

If the nightly rebuild silently stops, the agent's handler knowledge decays invisibly. Confirm all
three are alive at the weekly review.

---

## 3. Test-config registry upkeep

`tracks/enovia/test_config_registry.yaml` maps *suite → `test_config_id`* (**D3**). It replaced the old
single `PRACTICE_TEST_CONFIG_ID` scalar, which could not express one-config-per-suite.

- Every newly onboarded suite adds an entry via the plan0 §B.4b sequence.
- Every re-import (§1 above) may invalidate an entry.
- **O4** tracks the suites not yet onboarded; **O2** is re-checked at each onboarding.

The mapping — *which test config to trigger for a script change in which suite* — **is supplied by
Jay**, not derived by the Agent.

---

## 4. Eval-on-change rule [UP-10]

**Re-run `scripts/run_eval.py` (10-ticket smoke subset) after ANY `context.md` or prompt change.**
Prompt changes regress silently without this. The golden regressions — **TESTAUTOMA-8055** (the Type-A
spine) and, after plan4, **TESTAUTOMA-8278** (ask_human + flake attribution) — must stay green.

---

## 5. Weekly 30-minute cadence (Megha's lead)

Unchanged by the JARVIS alignment. Review chat-app failures, accept/reject `context_suggestions/`
drafts into `context.md`, run `scripts/verify_context.py`, and log the session in
`docs/maintenance_log.md`.

Add to the standing agenda: **the three scheduled jobs are alive**, **the registry matches the DAI**,
and **the monthly re-import is not overdue**.
