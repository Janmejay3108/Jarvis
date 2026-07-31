# PLAN CHANGE LOG — JARVIS ALIGNMENT PASS 4

**Branch:** `docs/jarvis-alignment-4` · **Base:** `master` @ `69c90fc` (tag `plan-set-jarvis-v3` + 3 context commits) · **Date:** 2026-07-30

Logs 1–3 are **not** superseded — the four are read together. This pass resolves two live inconsistencies
the repository revealed, absorbs the newly-committed `tracks/enovia/` context set into the plans, and
closes six smaller items.

Rule IDs: **H1–H7** rulings · **O1–O12** open items · **C1–C4** constraints · **D2/D3/D4** decisions ·
**UP-n** upgrade tags (never renumbered).

---

## PART 1 — OPEN MARKERS AFTER THIS PASS

**Two**, both carried unchanged from pass 2, both untouched here per §1.4 — each needs something to *run*.

| # | Question | Where |
|---|---|---|
| **1** | **Real per-cycle validation wall-clock timing (O3).** | `plan2` GATE 2 timing row |
| **2** | **Model re-import runbook specifics** — export/import menu path; replace vs duplicate; does `TEST_CONFIG_ID` survive. | `docs/maintenance.md` §1 |

**Closed this pass:** **O9** — EngineeringCentral is onboarded and owns TESTAUTOMA-8055's failing test,
so the end-to-end golden path is demonstrable. Pass 3's third marker is therefore retired.

---

## PART 2 — CONFLICTS BETWEEN THE PASS-4 BRIEF AND THE TREE

| # | Conflict | Resolution |
|---|---|---|
| **W1** | **§4.3 ratifies eight new families; the tree carries TEN distinct `PROPOSED:` tags.** The two unaccounted for — `search_criteria_too_broad` and `criteria_order_vs_scroll_direction`, both from TESTAUTOMA-8833 — pass §4.2's earns-its-place test on their own written reasoning. | **Asked Jay; ruled ratify both → 22 families, not 20.** The miscount came from `FINDINGS_for_JARVIS.md` §9, which lists three, not from deliberate exclusion. The decisive argument is a **routing cost**: `search_criteria_too_broad`'s nearest label is `test_data`, which is **not autofix-eligible**, so folding it would make JARVIS **decline a ticket it can fix with a one-line change**; `criteria_order_vs_scroll_direction`'s nearest label is `search_rectangle`, whose repair — *widen the rectangle* — is **actively harmful**, since a wider rectangle can match the wrong field. All ten tags cleared. |
| **W2** | **§1.1 says base off tag `plan-set-jarvis-v3`; `master` is 3 commits ahead** with the context set that §4 and §5 operate on. | **Asked Jay; ruled branch from `master`.** Branching from the tag would have discarded every file this pass is about. §11.10's heading diff still runs against the tag, which is valid because those three commits touched **no plan file** — verified. |
| **W3** | **§3.3.1 says `tracks/enovia/context.md` is CRLF and asks for renormalisation.** | **It is not, and none was done.** `git ls-files --eol` reports **`i/lf` on all nineteen** files — the index blobs are LF. My own first probe used `git show :file`, which applies smudge filters on output and therefore measured the working tree, not the index. Jay flagged the error before any change was made. Six files show `w/crlf` locally; a fresh checkout produces LF, `git status` is clean, and local is in sync with `origin/master`. **Renormalising would have churned nineteen files for nothing.** |
| **W4** | **§4.4.6 says to retag `context_appendix_ticket_learnings.md`** — that file carries **zero** `PROPOSED:` tags. | Retagged where the tags actually live: `ticket_findings.md` (18) and six of the nine per-ticket sources (13). Combined file kept in sync with its sources; marker counts re-verified at 41/15 after the edit. |
| **W5** | **§11.2 wants zero `environment_flake`**, but two occurrences sit inside a **verbatim quotation** of the source document. | **Annotated, not falsified.** The quote stands; a bracketed note records that it was ratified as `transient_flake`. `docs/FINDINGS_for_JARVIS.md`'s proposal table got the same treatment — a ratified-as column plus a banner — so no reader mistakes it for a live proposal. Deleting words from inside quotation marks to satisfy a grep would have been the wrong trade. |
| **W6** | **§4.4.1 says "extend line 234's list, do not restructure the section".** A twenty-two-family list with a repair-strategy column per family cannot live on one line. | Extended **in place** at that location, as two tables (autofix-eligible 17 / routes-elsewhere 5) under a sub-heading. No section moved, none renumbered, nothing else in §3 touched. |
| **W7** | **§3 describes work already done.** WORK4 says "33 tracked files"; the tree has 43. | Treated as **verified, not re-applied** — see Part 4. Re-writing them would produce a diff with no content change and risk overwriting Jay's commits. |

---

## PART 3 — PER-FIX LOG

### FIX 1 — registry note, B.4 verification, O4/O9, hygiene — commit `d78b6ac`

| Change | Why |
|---|---|
| Registry header records that EngineeringCentral's `smoke_target` **`TESTAUTOMA_2941_…` falls inside the 2864–2950 → EngineeringCentral range** | **First live confirmation the JIRA-number ranges are real** — and they are **branch 2 of `validation_suite_of`**, the fallback when the DAI log does not name the failing test. Specified since plan1 §1.3.2; never before observed to hold. |
| `plan0` B.4 **Verification** — "reproduce PoC-3 results ((User) reruns on VM)" → **B.4's own unit tests on synthetic fixtures with known answers**, against the *generated* map. On-VM rerun → **`GATE 0b-VM`** as one line | **H1.** PoC 3 is retired, so those results will never exist. Fixtures are the **stronger** bar: a PoC comparison proves only *agreement with an earlier script*; a fixture asserts **correctness**. B.4 actions 1–6 and the DoD substance untouched. |
| `PROGRESS`: **O9 ✅ RESOLVED**; **O4 → two of seventeen, fifteen remain**, with A.10a named as the ordering mechanism; two new entries | **H2** |
| `plan_master` §4 tree: `tracks/enovia/` expanded to the real two-tier set; `docs/` gains `FINDINGS_for_JARVIS.md` | §3.3.4 |
| `.claude/settings.local.json` untracked + gitignored | §3.3.3 — local IDE state |

### FIX 2 — the 22-family taxonomy — commit `149b8ac`

**The defect was live, not hypothetical.** `plan4` §4.1.1 routes on `change_scope` and `transient_flake`;
neither was among the twelve; so a pydantic `Diagnosis.category` constrained to "the 12" would have
**rejected plan4's own classifications at runtime, in production, on a valid diagnosis.** Fixed before
`schemas.py` is written.

| Location | Change |
|---|---|
| `plan_master` §3 | The canonical **22** — autofix-eligible **17** + routes-elsewhere **5** — each with a **repair strategy**; the **earns-its-place test** (*a family earns its place iff it routes to a **different repair***); the `flaky_oracle` ↔ `transient_render_state` boundary; the `environment_flake` → **`transient_flake`** naming ruling. Declared the **single source of truth** for `Diagnosis.category` and `triage.fixable_families`. |
| `plan_master` §6 | **NEW invariant 14** (no mutation between validation and PR — §8) and **15** (`false_pass_assertion` is the worst verdict failure available — §4.3). **13 unchanged; nothing renumbered.** |
| `plan1` §1.4.2 | `category: <the 22 families\|unknown>` **+ the runtime-rejection reason stated inline**, so nobody narrows it again. |
| `plan1` §1.4.1 | Router signatures for all ten new families; four read Tier-0 lint rather than re-deriving. **Sparse exemplar coverage stated honestly** — only 8 of 22 instantiated across nine tickets — with why it is acceptable (advisory, behind plan4's hard gate) and why it must be *stated* rather than discovered. |
| `plan4` §4.1.1 | `fixable_families` → the autofix-eligible 17; Layer-1 gains **four deterministic rules**; families declared as *defined in `plan_master` §3*, never maintained twice. **`min_confidence_for_autofix` and every threshold untouched.** |
| `tracks/enovia` | All ten `PROPOSED:` tags cleared (31 occurrences); `environment_flake` → `transient_flake` (3). Quotations annotated, not rewritten (W5). **Markers re-verified 41/15**, nine sources still matching the combined file. |

### FIX 2d — four Tier-0 lint rules — commit `149b8ac`

New `plan2` **Step 2.3.1**. **Added; no existing rule relaxed, narrowed or removed.**

| Rule | Severity |
|---|---|
| `silent_parameter_typo` — named param not matching the callee's declared names (`watiFor` vs `waitFor`) | **block** |
| `false_pass_assertion` — `waitForTextToDisappear` with no preceding presence check | **block** |
| `hardcoded_coordinate_brittleness` — literal coordinate pair into a click-family command | warn |
| `criteria_order_vs_scroll_direction` — criteria ordered against the panel's documented draw order | warn |

**The fourth is Jay's addition**, and it carries a design constraint worth keeping: it **sources the draw
order from `tracks/enovia/context.md` rather than hardcoding it**, so the rule tracks the document as the
panel evolves — with a unit test that edits the fixture's order and proves the verdict follows.
**Economics recorded:** a lint rule costs **milliseconds**; a SUT run **12–17 minutes**; a DAI run
**20 minutes–2 hours**.

### FIX 3–8 — commit `d97c8da`

| Fix | Change |
|---|---|
| **3** (§5) | `search_context` → **multi-file and trigger-aware**, parsing `context.md`'s already machine-readable *Appendix triggers* rather than hardcoding; never all five at once. `context_packer` gains the **two-tier rule with measured sizes** (core ~7.7K always cached; appendices ~3.5–7.2K each, packed on trigger, counted against the cap) and a budget-arithmetic unit test. `diagnosis_system.md` now teaches the **three evidence markers operationally** — the `watiFor` typo is the live proof that a `[live-run]` claim can describe already-fixed code. `[UNVERIFIED]` noted as the natural allowlist source for FINDINGS §5's #1 tool gap; **the tool is not built here**. Gate 0b-LOCAL line updated. |
| **4** (§6) | `plan0` B.4 action 6 rewritten: two-tier structure, **600-line hard ceiling** on the core, detail moves to an appendix rather than being compressed into ambiguity; **how it was actually built** (reasoning agent against the live repo, from nine ticket records + the seed, reviewed by (User)) recorded because the method is repeatable and explains the evidence markers; and **the review gate's new home made binding** — a `context.md` change is not complete until `run_eval.py` has been re-run without regression. Mirrored into `context.md` *Maintenance* and `plan1` §1.7.1. **[UP-5] exemplar-source reference preserved.** |
| **5** (§7) | `plan3` **Step 3.6.5** — weekly context drift detection, closing plan0's dangling forward reference (plan3 had **zero** `drift` hits). Specified by the **mechanical/interpretive split**: checkable claims auto-report and auto-correct *only* when confirmed both wrong **and** newly-right; interpretive claims **never** auto-update, they draft a suggestion. `[UNVERIFIED]` probes run in the same job; `[live-run]` claims get a distinct never-auto-correct check. |
| **6** (§8) | Invariant 14 landed with FIX 2; cross-referenced from `plan2` §2.5.2 and `plan3` §3.2, one line each. |
| **7** (§9) | **Stale-input freshness assert** in `plan2` §2.5.2: where a flow generates then consumes an artifact, confirm the consumed one **is** the generated one (timestamp, hash, or run-unique token) before a PASS is trusted — otherwise **`INCONCLUSIVE`, never PASS**. TESTAUTOMA-7947's *passing* run imported a file dated 6/3/2026 instead of the one generated that day. |
| **8** (§10) | Both scripts **specified, neither built**: `categorize_tickets.py` (two fields per ticket, frequency table, `ticket_base_rate.json`, purpose = ordering O4's remaining fifteen) and `poc4_bitbucket.py` (run against `agentic-eggplant-automation` because **Server API shapes are server-wide, not per-repo**; full create→read→decline→delete cycle; deliverable is the actual request/response JSON). |

---

## PART 4 — §3 ITEMS VERIFIED RATHER THAN APPLIED

Recorded explicitly so a later pass does not mistake "no diff" for "not done".

| Item | State | Evidence |
|---|---|---|
| EngineeringCentral registry row | **already present** | `yaml.safe_load` → `['EngineeringCentral', 'PartMaster']` |
| `.gitattributes` | **already present** | `* text=auto eol=lf`, `*.md text eol=lf`, `*.yaml text eol=lf`, `*.py`, `*.ps1` |
| Nine `ticket_findings_TESTAUTOMA-*.md` committed | **already present** | `git ls-files … \| wc -l` → 9 |
| Marker counts equal between sources and combined | **already true, and still true after retagging** | **41 `NOT RECORDED` / 15 `UNCERTAIN`** in both |
| CRLF normalisation | **not needed — index already LF** | `git ls-files --eol` → `i/lf` on all 19; see W3 |

---

## PART 5 — §11.12: DID ANYTHING JARVIS BUILDS COME BACK REDUCED?

**No. It grew, and shrank nowhere.**

| Measure | v3 | now |
|---|---|---|
| **Tier-0 lint rules** | **4** (balanced blocks · unknown-handler calls · paren/quote balance · boolean-context) | **8** — all four originals **intact**, plus the four family-derived rules |
| Unit-test mentions, `plan1` / `plan2` | 5 / 3 | **6 / 4** |
| Unit-test mentions, `plan_master` / `plan0` / `plan3` / `plan4` | 2 / 8 / 1 / 4 | **identical** |
| Gate thresholds, every file | — | **identical** |
| `max_attempts: 3` · N-best · `callers_pass` · `BudgetGuard` · `thinking_on_escalation` | — | **identical** |
| `NOT_ONBOARDED` | 3 sections | **3 sections** |
| `validation_suite_of` | resolves from the failing test | **unchanged**; zero sentences resolve from a changed file |

**Structural identifiers vs `plan-set-jarvis-v3`: additions only** — `Step 2.3.1`, `Step 3.6.5`, and a
`UP-12` cross-reference. **One regression was caught and repaired during verification:** the B.4 action 6
rewrite initially dropped plan0's `[UP-5]` tag; it was restored, and the heading list now diffs clean.
