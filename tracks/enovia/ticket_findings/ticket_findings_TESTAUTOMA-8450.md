## TESTAUTOMA-8450

**Failing test:** `TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded` — recorded without the `.script`
extension in the sources.
**Suite:** UNCERTAIN — NOT RECORDED directly. Neither source names the test's suite folder. Both place
the changed handlers in `EngineeringCentral.script` (`enterBOMLoaderValues`) and
`CommonEnovia.script` (`selectTableViewDropDownOptions`). The sibling test `TESTAUTOMA_2878_001`
(TESTAUTOMA-8449) is placed in `EngineeringCentral.suite/Scripts/TestCases/` by the 8449 document, so
`EngineeringCentral.suite` is the likely answer — but it is inference, not record.
**DAI runid:** **`34649`** (the FAIL run, on the Spirent part) and **`34708`** (the final PASS run —
recorded as "testrunid 34708"). Both are stated verbatim in the sources.

### Symptom

Four distinct failures over the life of the ticket. Verbatim where recorded:

1. **The reported crash.** `STInvalidBoolean`, raised from the handler `enterBOMLoaderValues`. The
   offending value is recorded as the bare property list `{DPI:250,...}` used as an `if`/`else-if`
   condition. Step number: NOT RECORDED. (The sibling 8449 document records the same error's log chain
   as `Testcase failed in [enterbomloadervalues -> assertwithscreenshot]`.)
2. **Step 10 threw** because BST has no "System Table" saved view. Exact error string: NOT RECORDED.
3. **The Spirent block**, surfaced on a different server during verification. The server trigger's
   text, recorded verbatim: `"Attribute update is not allowed for spirent Part"`, error **`#1500167`**.
   Occurred because Step 3 opened the part `INR-MIIM-002`, described in the app as
   `"Testing – Spirent part from WebINR"`.
4. **`"Cannot find Name"`** — a NEW failure that **the fix session caused itself**, via the ordering of
   its own temporary change. Step: NOT RECORDED.

### Evidence used

**Mattered:**

- **The error's literal-value fingerprint.** `{DPI:250, searchR...}` — the sources state the value
  quoted in the error "appears on exactly one executable line," which localised the bug with no
  search. The convergence rule the sources draw from this: use **2–3 independent signals** —
  handler name (`HandlerName1: enterbomloadervalues`), line offset (`"line 68"` = the 68th line *of
  the handler*), and the literal-value fingerprint. "Convergence of 2-3 independent signals = high
  confidence. This is the most important trick: the error's own VALUE often fingerprints one line."
  Note the line-number semantics: **`line 68` is an offset within the handler, not the file.**
- **The line immediately ABOVE the bug.** It was `if ImageFound(...)` — the correct idiom, sitting one
  line above the broken `else if (text:...)`. "the codebase showed the right answer next to the wrong
  one." The sources generalise: "bugs are usually a local deviation from a correct nearby pattern."
- **The log TIMELINE as a control-flow trace.** Reconstructed as: BOM-success found → `ImageFound(if)`
  returned false → fell into the `else-if` → crash. "The timing (`waitfor:15` ~ a 15s gap) matched."
  The rule: "If the timeline contradicts the hypothesis, the hypothesis is wrong."
- **THE ERROR SCREENSHOT — decisive, and it corrected a confidently-stated wrong claim.** See What was
  got wrong first. The sources' verdict: "The screenshot — not the text log — was ground truth."
- **Two same-day runs used as evidence about *time*, not code.** `34649` FAILED on a Spirent part;
  `34708` PASSED on a normal part (`005146-OSP`). Together they proved the failure was
  "data-dependent, refresh-driven, not a code regression." Comparing two runs is a distinct diagnostic
  move from reading one.
- **A pre-existing persisted memory note.** "a persisted note already 'knew' the BST System-Table quirk
  before this run, which is why FIX 2 was anticipated rather than rediscovered." This is the only
  recorded instance across all six tickets of the memory loop actually paying off.
- **Git, used for STATE MANAGEMENT rather than root-causing:** `git diff`,
  `git show origin/<branch>:<file>` to compare working tree vs remote; `git merge-base` (three-dot) to
  "prove what the PR really shows"; `git worktree` to build the fix on a clean base in isolation "so
  unrelated WIP couldn't leak into the commit."

**Explicitly NOT needed:** git history / `git blame` for root-causing. Stated plainly: "Git HISTORY /
blame was NOT needed to find the bug, because the error fingerprint localized it directly. So for 8450
it would have been redundant." This is a useful negative result — history is high-signal for
*regressions*, not for latent type errors that the error message already pinpoints.

**Supplied by humans from their own heads, not in any file — the decisive facts:**

- **Tanay (development team) gave the definitive rule:** a Spirent part = **Engineering Responsibility
  in {SP1, SP2, SP3, SP4}**, and **the parent part must not be one**.
- Tanay also **pushed back and was right**: "step 2 won't give a Spirent part / different type+policy."
- Tanay **disambiguated two independent attributes**: "that is EC Part" → EC-Part (a *policy*) and
  Spirent (an *attribute/trigger*) are independent; the part `INR-MIIM-002` was **both**.
- Tanay **asked the question that reframed the whole issue**: "did it work earlier / before refresh /
  first time?" — which is what led to comparing runs `34649` and `34708`.
- Jay supplied process decisions: "for testing, skip Spirent, pin to the original part, then revert";
  the git worktree / isolate-WIP / exact-commit-message requirements; and bug-raising guidance.

**Turned out irrelevant / a wrong path:** the initial treatment of the Spirent data problem as a code
problem. "we briefly chased a Spirent DATA issue as if it were code."

### Root cause

**Three different things wearing one ticket number.** The sources are explicit about this framing.

**(A) A code bug — the clean, in-scope kind.** In `EngineeringCentral.script`, handler
`enterBOMLoaderValues`, an `else if` condition was a **bare property list**:
`(text: partNumToClick, DPI:250, ... validCharacters:..., waitfor:5)`. In SenseTalk a `{...}` property
list is a data structure, not a truth value; `if`/`else if` requires true/false. So the runtime raised
`STInvalidBoolean` and the test crashed. It reads exactly like a copy of the `if ImageFound(...)` line
directly above it with the wrapper dropped.
Line number: `"line 68"` is recorded as the offset **within the handler**; the file line number is NOT
RECORDED.

**(B) An environment difference — surfaced only when verifying.** The BST environment
(`156.140.21.48`) has **no "System Table" saved view**, so Step 10 threw. The test selected that view
only in order to expose the `Source` column — and on BST **`Source` is already visible by default**.
So the view was a means, not the goal, and its absence did not invalidate the assertion. Described as
"Not a 'bug' in the product; a config/environment gap."

**(C) A test-data / domain issue — raised as a separate ticket, `ENOVIA3DX-9162`.** Step 3 opens the
**FIRST** "Preliminary Part" in the results. After a BST refresh, a freshly-created Spirent test part
(`INR-MIIM-002`, `"Testing – Spirent part from WebINR"`) sorted to row 1. BOM Loader is then blocked by
a **server trigger**: `"Attribute update is not allowed for spirent Part"` (`#1500167`). Root-cause
rule, from Tanay: a Spirent part = Engineering Responsibility in {SP1, SP2, SP3, SP4}; the parent part
must not be one. Fix direction: **exclude SP1–SP4 during part selection** — raised as a change-scope
story for the app team. "This is NOT a product defect and NOT the original code bug — it is
data-selection logic + tribal domain knowledge."

### The fix

Two fixes in the PR (branch `fix/Testautoma-8450`). **This is the only ticket of the six with a
literal before/after recorded.**

**FIX 1 — `EngineeringCentral.script`, handler `enterBOMLoaderValues`:**

```
BEFORE: else if (text: partNumToClick, DPI:250, ... validCharacters:..., waitfor:5)
AFTER : else if ImageFound(text: partNumToClick, DPI:250, ... validCharacters:..., waitfor:5)
```

(The `...` are the source document's own elisions, not mine — the full argument list is NOT RECORDED.)
One line. Wrapping the property list in `ImageFound(...)` makes it return true/false.

**FIX 2 — `CommonEnovia.script`, handler `selectTableViewDropDownOptions`, plus the 2 call sites in
`TESTAUTOMA_2879_002`:** added an optional `isMandatory` parameter with a graceful fallback:

- still tries the requested table view first — **original behaviour keeps priority**;
- if not found AND `isMandatory="no"`: log `"continuing with current view"`, press escape, carry on;
- **default stays `"yes"`, so no other caller changes.**

The real validation (`Source = bomloader`) still runs. "Intent preserved, nothing skipped."

Exact source lines for FIX 2: NOT RECORDED. (The 8449 document records the defaulting idiom as
`if isMandatory is empty then put "yes" into isMandatory`.)

**Temporary changes made for testing and then reverted:** pinning to the original part to skip the
Spirent part. Explicitly reverted after verification.

### What was got wrong first  ← THE MOST IMPORTANT SECTION

**The code bug was first-shot correct. Everything after it was wrong turns.** The sources say so
directly: "Fixed the `STInvalidBoolean` in one pass. (Agent-sweet-spot: DONE fast.)" and "the
resolution took ONE step" for issue (A). Roughly a dozen human input rounds followed, and "Only the
FIRST one was the 'clean code bug.'"

The wrong turns, in order:

**1. Chasing test data as if it were code.** "we briefly chased a Spirent DATA issue as if it were
code." The false signal: it arrived as a test failure in the same test, mid-verification, so it looked
like a continuation of the bug rather than a different class of problem. What it actually needed was
reclassification: "Reclassified: 'this is test-data, not the code bug.'"

**2. Breaking the test with its own temporary fix (round 5).** A NEW failure — `"Cannot find Name"` —
"caused by our own temp change ordering." Fixed by correcting the scroll-order. **A self-inflicted
failure that could easily have been mistaken for a new discovery about the application.** Any agent
that makes temporary test-only changes must attribute subsequent failures to its own edit before
theorising about the app.

**3. Asserting a root cause that had never been traced (round 10).** Tanay pushed back — "step 2 won't
give a Spirent part / different type+policy" — and the position was conceded: **"We had asserted a root
cause we had NOT actually traced. Conceded."** This is the cleanest recorded instance of confident
under-evidenced assertion in the whole set.

**4. Mis-reading the text log and stating the opposite of the truth (round 11).** With the raw DAI log
for runid `34649` in hand: **"I mis-read the TEXT log and wrongly said 'INR-MIIM-002 is not
Spirent.'"** The text log did not carry the information needed to make that call, and the claim was
made anyway.

**5. What corrected it (round 12): the ERROR SCREENSHOT.** It "proved it IS Spirent (description + the
trigger error)." The correction is recorded plainly: "Corrected myself. The screenshot — not the text
log — was ground truth."

**6. Then a conceptual confusion, corrected by Tanay (round 13).** "that is EC Part" → EC-Part
(policy) and Spirent (attribute/trigger) are **independent** properties; `INR-MIIM-002` was **both**.
Treating them as alternatives was the error.

**7. The reframe that finally settled it (round 14).** Tanay asked "did it work earlier / before
refresh / first time?" — answered by comparing the two same-day runs (`34649` FAIL on the Spirent part,
`34708` PASS on the normal part). Conclusion: **data-dependent, refresh-driven, not a code
regression.**

**8. The definitive rule arrived only at round 15** (Tanay: Eng Responsibility must not be SP1–SP4),
and the change-scope story was raised at round 16.

**The through-line:** the dead end lasted from roughly round 2 to round 15 and was not a
mis-localisation — it was **asserting conclusions about a domain the evidence could not settle**. The
sources' proposed guard is a hard requirement on the diagnosis step: "the diagnosis must account for
the log AND the screenshot AND the timeline. If any signal is unexplained or contradicts the
hypothesis, confidence drops and the agent escalates rather than asserts. (This exact rule is what
caught my error.)"

### Knowledge source

**`tribal` (primary) + `script_only` (for the code bug alone) + `app_behaviour`.**

- **`script_only` for FIX 1.** Everything needed was in the file: the error type, the value
  fingerprint, and the correct idiom on the line directly above. No other file was required.
- **`tribal` — the facts that existed nowhere in the codebase, logs, screenshots, or git:**
  - **Spirent = Engineering Responsibility in {SP1, SP2, SP3, SP4}; the parent part must not be one.**
    From Tanay. This is the rule that resolved (C) and it is not derivable from anything in the repo.
  - **EC-Part (policy) and Spirent (attribute/trigger) are independent** — a part can be both.
  - **BST (`156.140.21.48`) has no "System Table" saved view, and `Source` is visible by default
    there.** This one *was* in persisted memory before the run, and that is exactly why FIX 2 was
    anticipated rather than rediscovered.
  - **Tests pick the FIRST "Preliminary" part** and that selection is non-deterministic and
    refresh-sensitive.
- **`app_behaviour`** — the BOM Loader server trigger `#1500167`; what a BOM refresh does to result
  ordering.

The sources' structural conclusion: `context.md` needs an **ENVIRONMENT MATRIX** (server id →
environment → URL → known differences) and a **TEST-DATA-SELECTION / known-bad-data** section, and
"These two sections would have pre-empted most of this session."

### Fixable component

`script` · `environment` · `test_data` — **`multi_cause: true`**

- (A) → `script`.
- (B) → **caused by `environment`, remedied in `script`.** The environment was not changed; the script
  was made tolerant while keeping the real assertion. The four-value taxonomy cannot express this;
  flagging rather than forcing.
- (C) → `test_data`, and deliberately **not fixed here** — raised as a separate ticket
  (`ENOVIA3DX-9162`) for the app team.

### Failure family

`boolean_logic_gap` · `environment_issue` · `test_data` — **`multi_cause: true`**

- `boolean_logic_gap` — (A), exact fit: a non-boolean in a boolean context. Same bug as
  TESTAUTOMA-8449.
- `environment_issue` — (B), exact fit: a saved view present on one environment and absent on another.
- `test_data` — (C), exact fit: non-deterministic selection landing on a server-blocked record.

The self-inflicted `"Cannot find Name"` failure (round 5) has no family and should not get one — it was
an artefact of the session's own temporary edit, not a property of the system under test.

### Handlers involved

```
test (TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded)
    → enterBOMLoaderValues              (EngineeringCentral.script)  — the STInvalidBoolean crash
    → selectTableViewDropDownOptions ×2  (CommonEnovia.script)        — the isMandatory change
```

- `selectTableViewDropDownOptions` callers enumerated: tests **2878, 2879, 4100**, **plus a different
  handler with the same name in `M&AFoundational`**. The sources are explicit: "name collisions matter,
  so resolve by suite/scope, not just by name."
- Blast-radius verdict: only callers passing `isMandatory:"no"` change behaviour. "A caller that does
  not pass the new arg literally cannot behave differently." Everything else provably unaffected.

**Surprising / misdescribing:** `selectTableViewDropDownOptions` names the *action* (select a view) but
in this test the *purpose* was to expose the `Source` column. Knowing that purpose is what made it safe
to skip the view without weakening the test. The name alone would lead you to conclude the step is
essential.

### Outcome

**PASSED — validated by an actual run, with the strongest confirmation in the set.**

- Final DAI run **testrunid `34708`: PASSED, 0 errors, 0 warnings.**
- **"Both fixes confirmed firing in the logs"** — i.e. the run did not merely pass, it demonstrably
  exercised the changed lines. The specific success markers watched for are recorded:
  `"continuing with current view"`, `"2 is equal to 2 ... Matches count"`, and the final `PASSED`.
- Re-run also passed on a **NON-Spirent part (`005146-OSP`)** — "proof the loader works."

The sources make this a named standard: "a green compile is not a fix; a green RUN that exercises the
line is," and "never claim 'fixed' without mapping the fix to the logs and a green run that actually
exercises the changed line."

Issue (C) was **not** fixed and was correctly not fixed — raised as `ENOVIA3DX-9162`.

### What would have made this faster

1. **A TRIAGE hard gate before anything else**, classifying the failure as
   `CODE-LOGIC | ENVIRONMENT | TEST-DATA | INFRASTRUCTURE | PRODUCT BUG`, with low confidence →
   "ask ONE targeted question, don't guess." The sources' central process recommendation, because "the
   single most consequential decision on this ticket was: 'is this a code bug, or a
   data/environment/infra problem?' Get that wrong and everything downstream is wasted or harmful."
2. **An `ENVIRONMENT MATRIX` in `context.md`:** server id → environment → URL → known differences.
   The specific line: `BST 156.140.21.48 has no "System Table" saved view; Source column is default.`
   This "would have pre-explained FIX 2."
3. **A `TEST-DATA RULES & KNOWN-BAD DATA` section in `context.md`:** `Tests pick the FIRST Preliminary
   EC Part`; `Spirent parts (Eng Resp = SP1–SP4) have server triggers that block attribute/BOM
   updates — avoid.` This is the single item that would have saved the most time — most of rounds
   2–15.
4. **A `CONVENTIONS / IDIOMS` section in `context.md`:** `Any image/text check used as an if/while
   condition MUST be wrapped in ImageFound()/ImageLocation() — a bare {..} property list is a type
   error.` "This single rule would have pre-explained FIX 1."
5. **A `FAILURE TAXONOMY -> FIRST CHECK` table:** `STInvalidBoolean -> a non-boolean used as a
   condition`; `"Unable to Find Image (TEXT:..)" then crash -> OCR miss or missing element`;
   `"... not allowed for spirent Part" -> data selection, not code`.
6. **Vision as mandatory, not on-demand, for any UI/text-lookup failure.** The text log routinely
   omits the reason a lookup failed, and here it actively supported a false conclusion. "Elevate vision
   from 'on demand' to 'mandatory when the failure is a UI/text lookup'."
7. **An evidence-completeness requirement on the diagnosis:** it must explain the log AND the
   screenshot AND the timeline. Any unexplained or contradicting signal drops confidence and triggers
   escalation instead of assertion.
8. **`diagnosis_only` as a first-class terminal outcome, not a degradation path** —
   `diagnosis_only:env`, `diagnosis_only:test_data`, `diagnosis_only:infra`, `diagnosis_only:app_bug`,
   each with an evidence bundle and a recommended-action string. "a correct 'don't fix, here's why' is
   a WIN." The correct output for (C) was a crisp diagnosis plus "test-data: Spirent part selected —
   exclude Eng Resp SP1–SP4," not a patch.
9. **A capture loop:** whenever a human supplies a domain rule mid-run, propose a `context.md`
   addition for review. "The back-and-forth then costs ONCE per rule, not once per ticket."
10. **Run info in `context.md`:** how to run one script, where logs and screenshots land, the DAI/ttdb
    log schema, and the exact PASS markers to look for. The sources' honest self-assessment: the
    original inputs were "enough to LOCALIZE and fix the code bug (because the logs were rich), but
    it was UNDER-SPECIFIED for verification and scope, which is what caused the detours."
11. **A `git worktree` off a clean remote base as the default workflow** — used here specifically so
    unrelated WIP could not leak into the commit.
12. **A tree-sitter / SenseTalk grammar boolean-context check.** Named as "Biggest single win for
    static safety" because it would **flag the 8450 bug automatically**, before any run.

### Notes

- **Provenance and its limits.** Derived from **two** source files, both retrospectives, neither a
  session transcript:
  - `TESTAUTOMA-8450 (1).txt` — "PLAYBOOK & ARCHITECTURE NOTES", which carries the literal
    before/after diff, the `{DPI:250,...}` fingerprint, the `156.140.21.48` env id, the run-34708
    confirmation and the success markers;
  - `TESTAUTOMA-8450.txt` — "CASE STUDY + SENIOR-AI-ARCHITECT REVIEW", which carries the
    round-by-round back-and-forth, the Tanay exchanges, the `#1500167` trigger text, runid `34649`,
    and the `ENOVIA3DX-9162` spin-off.
  The second file notes there is "a second TESTAUTOMA-8450.txt in the Enovia repo root — that one is a
  generic 'how to build the agent' Q&A playbook," so the two files are known duplicates-by-name with
  different content. Neither contradicts the other on any fact I relied on.
- **8450 and 8449 are the same bug in the same handler on sibling tests.** 8450 =
  `TESTAUTOMA_2879_002`; 8449 = `TESTAUTOMA_2878_001`. Both `STInvalidBoolean` in
  `enterBOMLoaderValues`; both needed the `isMandatory` fallback in `selectTableViewDropDownOptions`.
  **`4100` is named as a third caller of the same handler and its status is NOT RECORDED.** An agent
  seeing this family should check all three.
- **A separate ticket was correctly spun off rather than fixed:** `ENOVIA3DX-9162` for the Spirent
  part-selection change. Also referenced in the sources: `TESTAUTOMA_4348` (server down) as another
  case that "must NEVER get a code patch."
- **The `"Cannot find Name"` failure was self-inflicted.** It came from the session's own temporary
  change ordering, not from the application. This is a distinct hazard for an autonomous agent that
  makes temporary edits to reach a step: attribute new failures to your own edit first.
- **The one recorded case of memory paying off.** The persisted BST System-Table note pre-empted FIX 2.
  This is the concrete evidence that the memory/`context.md` loop is worth maintaining — and it is the
  only such instance across all six documents.
- **Things that looked like the cause but were not:** the Spirent data problem looked like a code
  regression (it was data + a refresh); the text log looked like it settled whether `INR-MIIM-002` was
  Spirent (it did not); the `"Cannot find Name"` failure looked like a new discovery (it was
  self-inflicted); and EC-Part looked like an alternative to Spirent (they are independent, and the
  part was both).
- **Honest framing from the sources, worth keeping:** the clean code bug was ~10% of the work and was
  solved in one step; the other ~90% was "triage, environment quirks, test-data selection, visual
  ground-truth, and domain knowledge only a human (Tanay) held." The conclusion drawn is not that the
  agent is hopeless but that "the NON-code-bug path is not the exception, it's frequently the main
  event" — so triage and diagnose-only must be first-class, not secondary.
