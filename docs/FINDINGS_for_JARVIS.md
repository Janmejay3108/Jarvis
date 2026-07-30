# Cross-ticket findings for JARVIS

Derived from six retrospective documents covering five tickets. **Every claim here is traceable to a
named ticket record.** Where the sources do not settle something, it says so.

**Standing caveat that applies to this whole directory:** none of the six source documents is a
session transcript. All are post-hoc retrospectives written by the assistant that did the work. They
are strong on *what was learned* and weak on *exact strings, file paths and line numbers* — almost
every `NOT RECORDED` in the per-ticket records is a missing verbatim artefact. Two of the six (8449,
8448) are structured as Q&A rather than chronology, so the **absence** of recorded wrong turns in
8449 is not evidence there were none.

## Index

| Record | Test | Families | Outcome |
|---|---|---|---|
| [TESTAUTOMA-7947](ticket_findings_TESTAUTOMA-7947.md) | `TESTAUTOMA_6170_*` | `search_rectangle` + `config_value_stale` + `environment_issue` | PASSED (run 5) |
| [TESTAUTOMA-8278](ticket_findings_TESTAUTOMA-8278.md) | `TESTAUTOMA_6157_NewPhysicalProductFreezeFlow` | `text_label` + `environment_issue` + PROPOSED `change_scope` / `environment_flake` | Functionally PASSED, **reported FAILED** |
| [TESTAUTOMA-8448](ticket_findings_TESTAUTOMA-8448.md) | `TESTAUTOMA_4109_RT008_ValidatetheEBOMReportExporttoExcel` | `missing_wait` + PROPOSED `flaky_oracle` | PASSED locally **and** independently in DAI; merged |
| [TESTAUTOMA-8449](ticket_findings_TESTAUTOMA-8449.md) | `TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed` | `boolean_logic_gap` + `dpi_cascade` + `environment_issue` + `test_data` | Validated by re-run; merged. Formal PASS verdict NOT RECORDED |
| [TESTAUTOMA-8450](ticket_findings_TESTAUTOMA-8450.md) | `TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded` | `boolean_logic_gap` + `environment_issue` + `test_data` | PASSED, runid `34708`, 0 errors 0 warnings |

Plus: [`context_seed.md`](context_seed.md) — the tribal facts, ready to paste into `context.md`.

---

## 1. The single biggest finding: one ticket ≠ one bug

**All five tickets were multi-cause. Not one was a single defect.**

| Ticket | Distinct root causes | Of how many classes |
|---|---|---|
| 7947 | 4 | 3 (code, config, environment/infra) |
| 8278 | 3 | 3 (app redesign, environment drift, flake) |
| 8448 | 3 | 2 (timing, oracle fragility × 2 manifestations) |
| 8449 | 4 | 4 (logic, OCR, environment, test data) |
| 8450 | 3 | 3 (logic, environment, test data) |

This is a 5-for-5 pattern, and it has one hard consequence for the retry controller:

> **A failed validation run does not mean the previous fix was wrong.**

7947 is the proof case: "attempt 1's fix was CORRECT and stayed correct through 4 more runs." A
controller that reads "run 2 failed → retry (≤3 attempts)" will burn its whole budget on tickets where
it is actually succeeding. Required behaviour:

1. Re-classify the **new** failure from scratch on the **new** log after every run.
2. If it is a different blocker, record the previous fix as **HELD** and **reset the attempt budget**
   for the new blocker. Cap total blockers per ticket instead (7947 suggests 4).
3. Report time and cost **per ticket class** — chain tickets are not agent failures and must not look
   like them.

And its mirror image, from 8448: when *repeated* attempts fail **the same way**, the invariant is the
cause. Both rules are needed; they are not in tension because they are keyed on different things —
*different* new signature → new blocker, *same* signature/step/elapsed-time → you are changing the
wrong variable.

## 2. Ticket types, and where the agent's ceiling actually is

The sources converge on a typology. Restated with the tickets that instantiate it:

| Type | Description | Tickets | Autonomous prospects |
|---|---|---|---|
| **A — code-logic bug** | Everything needed is in the file + log | 8449 (A), 8450 (A) | **Strong.** Both solved in one pass. 8450: "the resolution took ONE step" |
| **B — change scope** | The app changed; the new workflow exists in nobody's file | 8278 | **Zero without a question channel.** 4 rounds of guessing produced nothing |
| **C — environment / infra** | Config, hosts, shares, saved views, drifted URLs | 7947 (×3), 8449 (C), 8450 (B), 8278 (R2) | **Diagnose, do not patch** |
| **D — test data** | Non-deterministic or blocked records | 8449 (D), 8450 (C) | **Diagnose and escalate.** 8450 correctly spun off `ENOVIA3DX-9162` |
| **E — flaky oracle / flake** | The check is unsound, or the verdict is polluted | 8448, 8278 (R6) | **Needs a mechanism change, and a flake-tolerant verdict** |

Two independent sources make the same estimate about proportion, and it is uncomfortable: 8450 states
that ticket's "true" work was **"~90% NOT"** the clean-code-bug problem, and 8278 that of ~6 rounds
"exactly ONE carried the decisive information." The clean code bugs were solved fast and cheap; they
were a small fraction of the elapsed work.

**What follows for JARVIS:** the value is not only "auto-fix". Correct triage plus a crisp
diagnose-only output is a *win state*, not a degradation path. 8450 asks for explicit terminal
outcomes — `diagnosis_only:env`, `diagnosis_only:test_data`, `diagnosis_only:infra`,
`diagnosis_only:app_bug` — each carrying an evidence bundle and a recommended action, and each scored
as a success in the eval harness.

## 3. The five wrong-turn archetypes — what actually cost the time

These are the recorded dead ends, generalised. Each is a check JARVIS can run *before* spending a run.

### 3.1 Changing the variable the error message names (8448 — worst single cost)
The failure message names the token that was not found, so the token looks like the knob. Four rounds
and ~1 hour of SUT time went into token substitution while the real cause was a 30-second timeout on a
transient popup. **Check:** if ≥2 attempts failed at the same step *and* the same elapsed time, stop
changing values and change the *mechanism*. Requires `failure_timestamp` in the attempt ledger — without
elapsed time this invariant is invisible.

### 3.2 Trusting the log's account of the world over the screenshot (7947, 8450 — twice)
- 7947: log said `Physical Product not displayed`. It was displayed, at x≈1070, outside a search
  rectangle ending at x=960.
- 8450: "I mis-read the TEXT log and wrongly said 'INR-MIIM-002 is not Spirent'" — the screenshot
  proved the opposite. "The screenshot — not the text log — was ground truth."

**Check:** for any UI/text-lookup failure, fetch the screenshot **before** reading code, and answer two
questions: is the expected text present, and at what coordinates? Then compare against the search
rectangle the code used. This is 7947's **visible-text test** and it classifies the family almost for
free:

| Screenshot says | Family | Fix direction |
|---|---|---|
| Visible, **outside** the rectangle | `search_rectangle` | Adopt an existing named rect that contains the coordinates |
| Visible, **inside** the rectangle | `dpi_cascade` | Climb the repo's own DPI/contrast ladder |
| **Not visible** | *not an OCR bug* | App change, environment, or test data. **Do not touch OCR params** |

The third row is what prevents "solving" a rectangle bug by loosening DPI, and vice versa.

### 3.3 Assuming a label survived a redesign (8278)
`"Enterprise Item Number"` named a *removed* command. Three rounds hunted for it, including a 13-minute
full-form scroll. The real name was `KEYSIGHT PART NUMBER`, obtainable only from the dev team.
**Check:** if the failing lookup is a label and the ticket carries the **"Change Scope"** Jira label,
route to a question, not to a code loop. 8278 carries that label literally — the routing signal is free.

### 3.4 Asserting a root cause that was never traced (8450)
"We had asserted a root cause we had NOT actually traced. Conceded." Corrected by a human pushing back.
**Check — make it a hard requirement of the diagnosis step:** the hypothesis must explain the log **and**
the screenshot **and** the timeline. Any signal left unexplained or contradicted drops confidence and
triggers escalation rather than assertion. The sources note this exact rule is what caught the error.

### 3.5 Mistaking self-inflicted damage for a discovery (8450)
The `"Cannot find Name"` failure came from the session's own temporary change ordering, not the app.
**Check:** after any temporary or scaffolding edit, attribute the next failure to your own edit before
theorising about the system under test.

**Sixth, adjacent:** 8449's "why is this file in my diff?" — answered by **branch ancestry, not the
working tree**. `fix/Testautoma-8449` sat on top of `fix/Testautoma-8448`. An agent inspecting the
working tree will find nothing wrong and can look indefinitely.

## 4. What evidence actually decided things

Ranked by how often it was load-bearing, with the negative results included — those matter as much.

| Evidence | Verdict |
|---|---|
| **Error screenshot** | **Decisive in 3 of 5** (7947, 8278 R3, 8450 R12) and the pivot in a 4th (8448 R5). Twice it *contradicted* the log. Promote from on-demand to **mandatory for UI/text-lookup failures** |
| **The log, read to the FIRST error** | Always needed. 8449: "cascading failures hide the trigger" |
| **Error *type* over error message** | 8449: `STInvalidBoolean` → "a non-boolean used where a boolean was required" narrowed faster than the message. Build an `{error_type → likely_causes + where_to_look}` table |
| **Literal-value fingerprint** | 8450: `{DPI:250, searchR...}` "appears on exactly one executable line." Free, exact localisation |
| **Sibling call-site mining** | **Produced the actual fix in 7947.** 18 call sites; every passing sibling used `validationErrorArea`, only the failing ones used `leftHalf`. Distinct from blast-radius: "blast-radius asks 'who might I break', sibling mining asks 'how do the survivors do it'" |
| **Cross-attempt invariant (same step + same elapsed time)** | The pivot in 8448. Needs an attempt ledger to be visible at all |
| **Comparing two runs** | 8450: `34649` FAIL on a Spirent part vs `34708` PASS on a normal part proved "data-dependent, not a code regression" |
| **`git log -S` (pickaxe)** | **Decisive in 7947** — found the migration commit `fd30b37a`, dated it, and revealed by omission that `PartMaster.json` was missed. "a migration commit's omissions are a to-do list of stale files" |
| **`git log` recent history** | Decisive in 8449 — commit `c47ef962` explained the environment class |
| **`git log origin/<target>`** | 8449: revealed PR #1061 (`7f3e3be4`) had already fixed the same bug. Check before opening a PR |
| **Environment probes** (`Test-Path`, `Get-SmbShare`, `ping`, `nslookup`, `Find-NetRoute`) | 7947 runs 3–5 "were diagnosed entirely with these, not with code reading" |
| **`git blame` / history for root cause** | **Negative result.** 8450: "NOT needed... the error fingerprint localized it directly." History is for *regressions*, not for latent type errors |
| **Nothing recorded as fetched-and-useless** | No source records wasted evidence. The waste was always wasted *runs*, not wasted reads |

## 5. Tool gaps the sources name explicitly

Ranked by the value they would have had on these five tickets:

1. **Environment probe toolkit** (read-only, allowlisted): `Test-Path`/`dir` on local + UNC paths,
   `Get-SmbShare`, `ping`/`Test-Connection`, `nslookup`, `Find-NetRoute`. 7947 estimates **~2 saved
   runs**; 3 of its 4 blockers were diagnosed this way. Named as a total absence in the plan.
2. **Git history tools**: `git_log_file(path, n)`, `git_pickaxe(string)`, `git_show(sha, path?)`,
   `git_blame(path, line_range)`. All read-only, all cheap. Decisive in 7947 and 8449.
3. **`compare_sibling_usages(handler_name) → [{file, line, args_passed, last_known_status?}]`** — one
   ripgrep plus light parsing. In 7947 "that rule alone produces the correct one-line fix
   deterministically." Pair it with the instruction: *if passing callers use a different
   parameterization than the failing caller, adopt the passing pattern rather than inventing one.*
4. **Coordinate-aware vision on error screenshots** — not "describe the image" but "is the expected
   text present, and at what (x,y)?", then a deterministic containment check against the rectangle from
   the code. Turns the screenshot "from 'context' into a measuring instrument."
5. **SenseTalk lint / parse before any SUT run.** 8449: the `ImageFound()` wrapper bug is a static type
   error a parser catches "in ms" versus a 12-minute run. 8450 goes further and wants a tree-sitter
   grammar with a **boolean-context check**, which would have flagged its bug automatically — "Biggest
   single win for static safety."
6. **`ask_human(question, why_needed, options?)` that pauses and resumes** — not "post a diagnosis and
   stop". This is the only thing that could have solved 8278. Cap at 1–2 questions per run so it does
   not become a chat crutch, and feed the answer back as a `context.md` suggestion.
7. **An operator-assist / environment-remediation outcome** that pauses the run with a precise request
   ("copy file X to host Y", "create share Z") and resumes on confirmation. 7947 needed a human to copy
   a file and create/remove an SMB share. Without this, "every environment blocker is a dead run
   instead of a 5-minute pause."
8. **An attempt ledger** passed into every retry:
   `[{attempt, hypothesis, change_made, failure_signature, failure_timestamp}]`.
9. **A reachability matrix as data** — which host can reach which share/URL. The `EPCORPAPAGENT12`
   lesson generalises.
10. **An xlsx reader** (openpyxl). PartMaster tests generate `.xlsx` test data and there is currently no
    way to verify what the script actually wrote. "Small, occasionally decisive."

**Explicitly judged unnecessary** by 7947: a vector DB, SharePoint, and live RDP control of the SUT
mid-run (post-mortem screenshots sufficed). Note the sources disagree here — 8449 and the 8450 playbook
both recommend an embeddings index for "find precedent" while 7947, 8448 and 8450's review all endorse
deterministic retrieval with no vector DB. **The disagreement is real and unresolved; do not present
either as settled.** The majority position, and the one credited with working, is
ripgrep + call-graph + `context.md`.

## 6. Validation is the top technical risk, not diagnosis

**8278 is the fixture that proves it.** The fix was correct — the product reached FROZEN — and the run
was reported **FAILURE** because one unrelated launch OCR flake logged an error. A naive exit-code
oracle would have:

- rejected a correct fix,
- re-diagnosed the flake on the next attempt, and
- "plausibly 'fixed' it by DELETING the 'Type the name' check" — **exactly the bypass the human said
  must never be committed.**

That is an oracle producing an unsafe change, not merely missing a pass. Required design:

1. **Capture the ticket's failure signature at diagnosis time** — failing step + the specific
   image/text lookup, e.g. `TEXT:"Set Enterprise Item Number"`.
2. **PASS-for-this-ticket = that signature is gone**, even if other failures remain — provided the
   others are either (i) known-flaky infra steps or (ii) present on the un-patched baseline too.
3. **A known-flaky step allowlist** that can never by itself fail a fix: login, the `3DEXPERIENCE`
   splash, the `Run` window.
4. **Flake tolerance**: re-run a failing candidate N times, or diff against a baseline run of the
   un-patched test.
5. **Anchor every re-diagnosis to the original signature**, so an off-ticket blocker is either routed
   around with a known-safe primitive (scroll/wait) or flagged — never silently absorbed into the
   ticket's fix.

And the counterweight from 8450: a green run is not enough either. **"a green compile is not a fix; a
green RUN that exercises the line is."** 8450 confirmed "Both fixes confirmed firing in the logs" and
watched for named markers (`"continuing with current view"`, `"2 is equal to 2 ... Matches count"`,
final `PASSED`). Require evidence that the changed line actually executed.

## 7. The prohibitions — the things that must never happen

Each is recorded because it was a live temptation in a real session.

1. **Never trade a real assertion for a green checkmark.** 8449: "a green test that skipped its
   assertion is worse than a red one — it lies." Both 8449's and 8450's environment fallbacks were
   built so the real `Source = "bomloader"` check still runs.
2. **Never commit the `"Type the name"` bypass** (8278). It exists locally, it makes runs green, and it
   is explicitly forbidden. An agent optimising for green will find it attractive.
3. **Never patch correct code to mask an environment problem** (7947). "patching correct code to mask
   an env problem creates a landmine." 3 of 7947's 4 blockers needed *zero* code change.
4. **Never `git add -A`.** 7947's working tree held **17 unrelated dirty `SuiteInfo` files**; 8278 had
   drift in `SuiteInfo` and `PartMaster.json` plus the forbidden bypass. Stage the explicit file list
   from the applied edits. 8450's stronger version: build in an isolated **`git worktree` off a clean
   remote base** so WIP cannot leak in at all.
5. **Never patch a `test_data` or `application_bug` finding.** 8450 correctly raised
   `ENOVIA3DX-9162` instead of patching; `TESTAUTOMA_4348` (server down) is named as another that
   "must NEVER get a code patch."
6. **Never assert what the evidence cannot settle** (8450, twice). Escalate instead.
7. **Never change a shared handler's existing behaviour.** New parameters are optional and default to
   the old path — 8449's `if isMandatory is empty then put "yes" into isMandatory`, 8450's
   `isMandatory` default `"yes"`, 8448's opt-in disk check. "A caller that does not pass the new arg
   literally cannot behave differently."
8. **Do not re-litigate human review feedback.** 8449: a reviewer required the OCR ladder be reordered
   so the original setting is tried first. "the agent must accept and re-apply feedback, not
   re-litigate it."

## 8. Blast radius without running everything

The sources agree on a risk ladder, spending validation effort in proportion to reach:

| Risk | Change | Checks | Runs | Instance |
|---|---|---|---|---|
| **0** | Caller-side, one test script | Lint only | Just that test | 7947 (18 call sites existed; only 6170's line changed) |
| **1** | Suite-local handler | Ripgrep callers in suite; per-site signature compatibility | Affected tests | — |
| **2** | Shared handler | (a) enumerate every call site (b) per-site arg/signature compatibility (c) **LLM semantic review**: "given this diff and these N call sites, which callers' *behaviour* changes?" (d) small smoke subset, 2–5 representative callers (e) **prefer additive changes** | Smoke subset | 8449, 8450 (`selectTableViewDropDownOptions`), 8448 (`exportBOMreport`, caller 4105) |
| **3** | Shared config / resources | Grep every consumer of the exact key. **Rectangle edits in `ConfigEnovia` are RISK 2+** | Per consumer count | 7947 (`PartMaster.json` `BSTURL` had one consumer) |

Two hard hazards recorded:

- **Handler name collisions are real.** `selectTableViewDropDownOptions` exists **twice** — once in
  `CommonEnovia.script` and again, as a *different handler*, in `M&AFoundational`. "resolve by
  suite/scope, not just by name."
- **Duplicate definitions within one file are real.** `common.script` has **two `clickElement`
  bodies** (~line 155 and ~line 967); logged line numbers resolve against the **second**. Any
  line-number-to-source mapping must handle this or it reads the wrong body.

Plus, from 8448: **re-pull origin and diff the target file before applying to a shared handler** — a
colleague pushed to the same handler mid-flight. And from 8449: **check `git log origin/<target>` before
opening a PR** — PR #1061 had independently fixed the same bug.

## 9. Failure-family taxonomy: what the twelve get right and wrong

**Clean fits, no changes needed:** `boolean_logic_gap` (8449 A, 8450 A), `dpi_cascade` (8449 B),
`search_rectangle` (7947 B1), `config_value_stale` (7947 B2), `missing_wait` (8448 R1),
`environment_issue` (7947, 8449 C, 8450 B, 8278 R2), `test_data` (8449 D, 8450 C).

**Never instantiated in these five tickets:** `silent_exception_swallowing`, `image_staleness`,
`handler_name_mismatch`, `application_bug`. Their absence is not evidence they are wrong — five tickets
is a small sample.

**Three families the sources propose adding, each because the nearest existing label names a *wrong
fix*:**

| Proposed | From | Why the nearest existing label mis-routes |
|---|---|---|
| **`flaky_oracle`** (a.k.a. `ocr_fragility`) | 8448 | `text_label` → fix the token = **the hour-long dead end**. `dpi_cascade` → tune OCR = same trap one level down. `missing_wait` → extend the timeout = papers over it |
| **`change_scope`** | 8278 | `text_label` describes the diff, not the problem. Routing there re-runs R1–R4 flailing. Detectable *free* from the Jira "Change Scope" label, before any diagnosis |
| **`environment_flake`** | 8278, 8448 | Distinct from `environment_issue` because **nothing should be fixed** — the correct handling is to tolerate it in the verdict |

**A structural gap in the `Fixable component` axis (`script`/`test_data`/`environment`/
`application_bug`):** it cannot express **"environment-caused, script-remedied"**, which is what 8449's
and 8450's `isMandatory` fallbacks are — the environment was not changed; the script was made tolerant
of it while keeping the real assertion. It also cannot express "stale repo config data" (7947's
`PartMaster.json`), which is mechanically `script` but is not logic. Both were flagged rather than
forced in the per-ticket records.

**The meta-rule that makes the taxonomy work at all**, from 8449: *decompose the ticket into
sub-failures first, then classify each.* Every one of the five tickets fits the twelve cleanly once
decomposed and fits none of them cleanly as a whole.

## 10. Ordering that the tickets prove correct

1. **Fetch logs BEFORE localizing.** 7947 is concrete proof: the ticket had **no script of its own** —
   the script number came from the linked closed issue (6170) and from the log itself. "the log is the
   most reliable script-name source; the ticket number is not." Also make the Jira extractor read
   **issue links (relates-to)**: 7947→6170, 8278→6157.
2. **Fetch the screenshot before reading code**, for any UI/text-lookup failure (§3.2).
3. **Triage before localizing.** 8450's hard gate:
   `CODE-LOGIC | ENVIRONMENT | TEST-DATA | INFRASTRUCTURE | PRODUCT BUG`, low confidence → ask one
   targeted question. "Get that wrong and everything downstream is wasted or harmful." 8449's version:
   "If your agent cannot confidently name the class, it must STOP and ask / escalate rather than patch.
   A wrong class = a wrong (or masking) fix."
4. **Then tiered retrieval**, cheapest first — all four sources independently describe the same ladder:
   `context.md`/memory → the failing script → the named handler → all other callers → passing siblings
   → repo-wide → git history.
5. **Lint before any run.** Runs cost 12–17 minutes (8448, 8449); a DAI Practice run is 20 min – 2 hr.
6. **Then validate, then re-classify from scratch on the new log** (§1).

## 11. Known follow-ups these tickets left open

Real, actionable, and recorded — a future agent should check these rather than rediscover them.

- **7947:** tests **6172** and **6179** also pass the too-narrow `leftHalf` to
  `uploadPartMasterNetworkShareFile` and were **not fixed**. Same latent bug.
- **8449/8450:** test **4100** is a third caller of `selectTableViewDropDownOptions` and shares the
  step. Status **NOT RECORDED**. 8449 notes "sibling tickets 2879/4100 share the same step — Jira links
  would let the agent fix a whole family at once."
- **8450:** `ENOVIA3DX-9162` (exclude Eng Resp SP1–SP4 during part selection) was raised, not fixed.
- **8448:** UNCERTAIN whether its disk-check fix used, extended or duplicated the pre-existing
  `validateDownloadedFileOnDisk` handler that the 8450 playbook says already existed. **If the precedent
  already existed, rounds R2–R5 were avoidable by repo search alone** — worth resolving, because it
  changes whether the lesson is "write down the oracle hierarchy" or "search for precedent first".
- **7947:** whether the final passing run was a DAI pipeline run or a SUT run is UNCERTAIN.
- **8449:** no formal PASS verdict, run id, or DAI confirmation is recorded — only "the assertion that
  previously failed now passes" plus a merge.

## 12. Throughput, because it bounds everything

Not a correctness issue, but it caps the whole initiative: **one serialized RDP SUT, one EPF license.**
A SUT run is 12–17 min; a DAI Practice run is 20 min – 2 hr. A single hard ticket can consume
3 attempts × 1 run + N-best extra candidates + caller smoke runs = **hours of exclusive SUT time**,
capping throughput at a handful of hard tickets per day.

The costs in this set are concrete: 8448 burned ~4 runs (~1 hour) on token substitution; 8278 burned a
13-minute run on a single wrong label guess; 7947 spent 3 of 5 runs on environment blockers that no code
change could fix. **Every item in §3 and §5 is, in effect, a throughput optimisation** — the free checks
(lint, sibling mining, screenshot-vs-rectangle containment, environment probes, the attempt ledger) all
exist to avoid spending a run.

Mitigations the sources name: make the local `runscript` inner loop work so DAI Practice is only the
final authoritative check; lean hard on free Tier-0 lint; keep smoke sets small; and treat a graceful
handoff with a diagnosis as a **success mode** — "The agent saving 10-15 min of triage on a ticket it
can't fully fix is still a win."
