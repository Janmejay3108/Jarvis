# PLAN CHANGE LOG — JARVIS ALIGNMENT PASS 3

**Branch:** `docs/jarvis-alignment-3` · **Base:** tag `plan-set-jarvis-v2` (`10dd360`) · **Date:** 2026-07-29

Logs 1 and 2 (`plan_change_log_jarvis.md`, `_2.md`) are **not** superseded — the three are read together.
This pass closes residues pass 2 left behind, applies Jay's rulings on PoC scope, and corrects one rule
pass 2 introduced with a blind spot in it.

Rule IDs: **G1–G13** rulings from Jay, 2026-07-28 / 2026-07-29 · **O1–O12** open items ·
**C1–C4** platform constraints · **D2/D3/D4** ratified decisions.

---

## PART 1 — OPEN MARKERS AFTER THIS PASS

**Three.** Two carried from pass 2 — both still need something to *run* — plus the one new marker §8.4
permits.

| # | Question | Where | Status |
|---|---|---|---|
| **1** | **Real per-cycle validation wall-clock timing (O3).** | `plan2` GATE 2 timing row | Carried. Measurable only once the gate runs for real. **Not touched this pass, per §1.4.** |
| **2** | **Model re-import runbook specifics** — export/import menu path; replace vs duplicate; does `TEST_CONFIG_ID` survive. | `docs/maintenance.md` §1 | Carried. Answerable only by walking through one re-import. **Deliberately not answered, per §9.4.** |
| **3** | **Next onboarding target for the golden path (O9).** | `PROGRESS.md` O9 | **New this pass — the only one §8.4 permits.** See the note below. |

> **On marker 3, and why it is not worded as §8.4 words it.** §8.4 asks for a marker on *"which suite
> owns TESTAUTOMA-8055's failing test"*. **That is already recorded**: `plan_master` §3 states the golden
> regression is an **`EngineeringCentral.suite`** test whose bug sits in `CommonEnovia.script:409`.
> Asking an already-answered question is exactly the pattern pass 2 spent effort removing, so the marker
> instead **states the recorded fact and asks the part that is genuinely open** — whether
> EngineeringCentral is therefore the **second onboarding target** for O4, or whether A.10a's frequency
> count should order it differently. **Ruled by Jay before execution.**

---

## PART 2 — CONFLICTS BETWEEN THE PASS-3 BRIEF AND REALITY

| # | Conflict | Resolution |
|---|---|---|
| **Z1** | **§1.1 says to base off tag `plan-set-jarvis-v2` — it did not exist.** Pass 2 (`docs/jarvis-alignment-2`, 5 commits) was still unmerged and `master` sat at pass 1. | **Asked Jay; ruled create the base.** Fast-forwarded `master` to pass-2's head **without squashing** (per-file commits remain the audit trail), tagged `plan-set-jarvis-v2`, branched `docs/jarvis-alignment-3` from it. Tag `plan-set-jarvis-v1` and checkpoint `e0f8be6` untouched. Mirrors exactly what pass 2's §1.1 instructed for pass 1. |
| **Z2** | **§8.4's marker asks a question the plan set already answers** (see Part 1, marker 3). | **Asked Jay; ruled state the fact and confirm the priority.** O9 records EngineeringCentral from `plan_master` §3 and asks only about onboarding order. Keeps §10.7's count at three without inventing a question. |
| **Z3** | **§9.1's permitted-locations list is narrower than reality.** It allows `PartMaster` only in the registry, B.4b's worked example, PROGRESS history and the change logs — but the literal also appears in the **17-suite list** (`plan_master` §3, `docs/context.md`), in A.2b's proven-on line, and in prose about what is onboarded (O4). | **Asked Jay; ruled code-behaviour only.** §9.1 names *modules, config defaults, scripts and unit tests* — things that would make the system single-suite. Factual prose is left intact; stripping "only PartMaster is onboarded (O4)" would hide the project's largest scaling constraint. **Sweep result: no code-behaviour hardcoding exists.** |
| **Z4** | **§0 forbids reordering any Gate; G13 splits Gate 0b.** §10.8 then asks for "every Gate identical". | G13 authorises the split **explicitly** ("this is a structural change, authorised explicitly"), and §10.7b *requires* that no bare "GATE 0b" survive. Resolved as: `GATE 0b` → `GATE 0b-LOCAL` + `GATE 0b-VM`, **no checklist item deleted or reworded**, B.7 not renumbered. This is the **only** structural change in the pass, and the only "removal" §10.8's diff reports. |
| **Z5** | **§6.2 Part 3 says to add fields to `src/models/trajectory.py`** — but `src/` does not exist yet; plan0 B.1 creates it, and pass 2's verification asserts its absence. | Written where the trajectory record is actually **specified**: **plan3 §3.6.1**, naming `src/models/trajectory.py` and the logger as the implementation sites, plus plan0 A.10 Part 3. No code created. |
| **Z6** | **§6.4 says propagate to "plan3 §3.7's rollout prerequisites"**, but §3.7 is *Operational maintenance*; the rollout is §3.9. | Followed the brief literally — the line went into **§3.7**, which is where the VM-bound operational content lives, and it names §3.9 explicitly so the rollout reads it. One line, as instructed. |
| **Z7** | **§6's subsections run 6.1, 6.2, 6.4, 6.3.** | Cosmetic ordering in the brief. All four executed. No action. |

---

## PART 3 — PER-FIX LOG

### FIX 1 — `plan0` B.7 model-ID landmine — commit `0e76a83`

| Change | Why |
|---|---|
| B.7's ping clause `Claude (Opus 4.6 via configured base URL)` → **`settings.model`**, with the reason appended inline | **G2.** Read literally the old clause pinged a model the gateway 401s on, and prescribed *filing a firewall ticket* for a problem that does not exist. B.7 is read first; plan4 §4.0's interpretation rule is read last. |
| Every other `Opus 4.6` literal **left alone** | §3. They sit in cost tables and prose (plan1 §1.6 Gate 1, plan2 §2.4/§2.8, plan3 §3.6 + PROJECT DoD) and are covered by plan4 §4.0 item 1. |

### FIX 2 + 3 — `plan0` B.1–B.4, `plan_master` §4 — commit `a7cff57`

| Change | Why |
|---|---|
| B.2 Goal "both VMs ready" → the JARVIS VM (`eggptdai10`) | **G1** |
| `setup_vm_orchestrator.ps1` + `setup_vm_runner.ps1` **merged into `scripts/setup_vm_jarvis.ps1`**; `plan_master` §4's `scripts/` listing updated | **G1** — two scripts for one machine is how the two-VM confusion returns |
| B.3 ".env on each VM" → the JARVIS VM (+ the local dev machine while development is local); B.4 "respective VMs" → the JARVIS VM; Gate 0b checklist "both VMs provisioned" → "JARVIS VM provisioned" | **G1**. Nothing else in that checklist changed; nothing ticked. |
| `plan_master` §3's `aiagent-testmanager` row **left exactly as pass 2 set it** | §4 — superseded, retained, protected under R1 |
| **B.2a** — VM egress **✅ VERIFIED, nothing to run**, attributed to Jay 2026-07-29; egress loop retained as **deployment-day re-verification** | **G3.** Explicitly *not* claimed as proven by a committed script run. |
| **B.2b** — tooling install + Eggplant component verification **deferred to deployment**; script written now so deployment is a single `(User)` run | **G3, F12** |
| The script **VERIFIES** Eggplant / licenser / agents / `C:\Eggplant_Suites` / `Jay_130` — it does **not** install them | **G3** — all proven by A.2/A.2b's PASSED run |
| New B.2 DoD; **PoC 1 + 1b not reintroduced** | §5 — the old DoD was uncompletable, since both are `n.a. (deferred)` |
| B.1 step 1 — agent repo **local-only**, repo-side actions **deferred not deleted**, validation repo explicitly unaffected | **G11** |
| B.1 — local dev tooling installed **inline by the coding agent** as needed, with `(User)` permission; no dev provisioning step exists or should be invented | §5 |

### FIX 4 — Gate 0a, Gate 0b, PoC 7 — commit `2825be0`

| Change | Why |
|---|---|
| Gate 0a: EPF licence + RDP SUT → **PROVEN** (A.2/A.2b, PROGRESS 2026-07-28) | §6.1 |
| Gate 0a: PoC 3 → **RETIRED, superseded by B.4** — worded *superseded*, not *skipped*; **B.4 untouched** | **G4** |
| Gate 0a: PoC 4 → cheap smoke before plan3 §3.2, with the corrected rationale inline; A.7 records that its **permissions half is already satisfied** | **G5** |
| A.10 Part 1: the `≥60% / 40–60% / <40% STOP` decision rule **deleted and retired** | **G6** — 10–12 manually executed tickets are stronger evidence of engine fit than a label distribution, and settle the vision question. Vision stays deferred. |
| **A.10a** suite-frequency count (scripted, no human labelling) — orders **O4**, answers **O9** as a by-product | **G7** |
| **A.10b** the ≥50 labelled set → deferred to Gate 1 scoring, carried as **O8** | **G7** |
| A.10 Part 3 + **plan3 §3.6.1**: the trajectory record carries `failing_test`, `owning_suite`, `family`, `families_present[]`, `multi_cause`, `knowledge_source`, `fixable_component`, `vision_needed` **from day one**; honest self-selected-sample limitation recorded verbatim | **G7** — the mechanism that replaces the labelling session. A **build** requirement, not a testing one (Z5). |
| **Gate 0b split** into `GATE 0b-LOCAL` (gates plan1) and `GATE 0b-VM` (gates deployment + plan3 rollout); B.7 → B.7a / B.7b | **G13, O12** (Z4) |
| B.7b keeps the do-not-weaken-into-a-local-run warning **verbatim**; B.7a stated as an **additional earlier** checkpoint, never a replacement | §6.4 — so no later pass reads the split as permission to skip the VM run |
| B.7 heading → `GATE 0b-LOCAL / GATE 0b-VM`; plan1 prereq and plan3 §3.7 each gain one line | §6.4, §10.7b |
| Gate 0a Rule paragraph amended; **nothing unproven ticked**; PROGRESS mirrors it | §6.3 |
| **O8, O9, O10, O11, O12** appended to PROGRESS; O1–O7 not renumbered | §6.1, §6.2, §8.4 |

### FIX 5 — `tracks/enovia/ticket_findings.md` — commit `537c405`

| Change | Why |
|---|---|
| **New file** — `(User)`-authored, schema + skeleton by the Agent, one section per ticket | **G8.** The 10–12 manual tickets are the project's strongest engine-fit evidence and currently live only in one person's head. |
| Wired into **plan0 B.4 action 6** — primary input to `context.md`'s ~20 fix patterns, stated as **evidence *for* curation, never a substitute** for Megha's team's review | §7.1 |
| Wired into **plan1 §1.7.2** — the **first rows** of `validation_tickets.json`, carrying O8's columns so nothing is labelled twice | §7.2 |
| Wired into **plan1 §1.4.1 exemplars** (+ plan4 §4.6.5) — the *"what the model got wrong first"* line is what few-shot selection actually needs | §7.3 |
| **No prompt, schema or metric changed** | §7 |

### FIX 6 — `validation_suite_of` — commit `6b71f5a`

| Change | Why |
|---|---|
| `suite_of(file_path)` → **`validation_suite_of(run)`**, resolving (1) the suite owning the **failing test**, (2) else the JIRA number→suite range, (3) else **raise** — never infer from the changed file, never default | **G9.** Pass 2's rule resolved from the changed file. TESTAUTOMA-8055 disproves it: the fix lands in `CommonEnovia.script` ~409, a **shared handler** owned by no suite, so the pre-flight would refuse and **the project's own golden ticket would never validate**. Invisible at one onboarded suite; structural at two. |
| Shared handler directories **explicitly declared not-suites** (`CommonEnovia`, `common`, `configEnovia`, `LaunchApp`, `FileOperations`, `EnoviaSearch`, `exceptionHandling`, `CommonEnoviaContd`, `EnoviaChangeManagement`, `MQLTestData`, `WINSCP`, + anything in `handler_map.yaml`) | §8.2. Wider impact stays covered by `blast_radius` + `callers_pass`. |
| Named `validation_suite_of`, with an explicit cross-reference to plan1 §1.3.2's **`_suite_of`** | §8.2 — different function, different input, different failure mode; they must not be merged |
| Unit tests **added, none replaced**: failing test in `PartMaster` + fix in `CommonEnovia.script` → resolves to `PartMaster`; shared-handler path never yields a registry key; unresolvable run raises | §8.3.2 |
| Written in all five places: plan2 §2.5.0 contract, §2.5.0 tests, §2.5.2 steps 0 **and** 1, `plan_master` §6.13, plan0 B.4b | §8.3 |
| plan0 B.4b: a suite is onboarded so **tickets whose failing tests live in it** can be validated — **a suite is not a location for fixes** | §8.3.5 |

### FIX 7 — N-suite sweep + webhook — commit `c6842df`

| Check | Result |
|---|---|
| 1. `PartMaster` / `Part_Master_Pack_01` / `0310ac5d…` not hardcoded in any module, config default, script or unit test | **PASS**, read-only. Remaining occurrences are the registry, B.4b's worked example, PROGRESS, the change logs, the 17-suite list and onboarding prose (Z3). |
| 2. No `jarvis_test_config_id` scalar | **PASS.** The only hit is B.3 asserting the scalar does **not** exist. |
| 3. `render_all` described as rendering for **every registered suite** | **PASS**, both occurrences. |
| 4. `docs/maintenance.md` as a **per-model** procedure | **REWRITTEN.** It read as a single-model narrative. Now states that there is one model per suite (**D2**), so this is the loop run **once per onboarded suite every month** — one today, **seventeen at full scale**, all UI work that cannot be automated (**C1**). Adds a copy-per-suite checklist and states plainly that this is the **dominant recurring cost, scaling linearly with O4**. Its three open questions **deliberately not answered** (pass 2's marker 2). |
| 5. **O1** — nothing implies the webhook is a prerequisite | **PASS**, line added. `poll_backoff` is the proven day-one mode; the webhook is a **latency upgrade Jay is testing in parallel**. |

---

## PART 4 — §10.8: DID ANYTHING JARVIS BUILDS COME BACK REDUCED?

**No.** Measured against tag `plan-set-jarvis-v2`:

| Build item | v2 | now |
|---|---|---|
| `max_attempts: 3` · `n_best_on_retry` · `BudgetGuard` · `thinking_on_escalation` | 1 / 3 / 3 / 3 | **identical** |
| `callers_pass` | 4 | **5** (added) |
| Tier-0 lint · `run_eval.py` · Wilson CIs | 4 / 7 / 7 | **identical** |
| Unit-test lists | 6 + 8 | **6 + 9** (added) |
| `NOT_ONBOARDED` | 5 | **5**, still exactly its three sections |
| Gate thresholds (≥75%, ≥60%, ≥80%, ≥90%, zeros) | — | **identical in every file** |

**Structural identifiers:** additions only — `Step A.10a`, `A.10b`, `B.2a`, `B.2b`, `B.7a`, `B.7b`, and a
`UP-11` cross-reference. **The single removal is the bare `GATE 0b` token**, replaced by `GATE 0b-LOCAL`
and `GATE 0b-VM` — the authorised G13 change, which §10.7b independently *requires*.

**One threshold-shaped addition:** `≥50 tickets` now appears in plan3 §3.6.1, in the sentence explaining
why the labelling columns are carried from day one. It is a reference to O8's sample size, not a new or
altered target.

**Nothing was softened, deferred or simplified.** The two things this pass defers — B.2b's tooling
installs and A.10b's labelling exercise — are a **provisioning task** and a **PoC measurement**, not
build steps. PoC 3 is **retired only because B.4 builds the same capability as unit-tested modules**,
which is strictly stronger; **B.4 itself is untouched**.
