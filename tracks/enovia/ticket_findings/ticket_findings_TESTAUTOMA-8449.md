## TESTAUTOMA-8449

**Failing test:** `TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed` — recorded without the
`.script` extension in the source.
**Suite:** `EngineeringCentral.suite` — UNCERTAIN: the document does not state the suite for this test
in one place. It records the project map as "where handlers live
(`EnoviaCommon.suite/Scripts/...`), where test cases live
(`EngineeringCentral.suite/Scripts/TestCases/...`)" and lists the test's tags as
`EBOM_Loader, EngineeringCentral, Regression Test`. The failing handler `enterBOMLoaderValues` is
placed in `EngineeringCentral.script` by the *TESTAUTOMA-8450* playbook document, not by this one.
**DAI runid:** NOT RECORDED. (Run ids `34649` / `34708` appear in the TESTAUTOMA-8450 document and
belong to that ticket, not this one.)

### Symptom

Verbatim, the two log strings the document says "pinned it precisely":

```
Testcase failed in [enterbomloadervalues -> assertwithscreenshot]
STInvalidBoolean ... '{DPI:250, searchR...}'
```

(The second string is truncated with an ellipsis in the source — the full property list is NOT
RECORDED.)

Which numbered step of the test died: NOT RECORDED for the primary failure. The document localises by
handler chain, not step number.

Three further, distinct failures were part of the same ticket:

- **OCR:** `DPI:250` could not read hyphenated part numbers. Named examples: `B1506AU-OC-PRD`,
  `E7515B-FWS`, `005146-OSP`. "The element WAS on screen."
- **Environment, Step 10 area:** the new BST env (`3dxspacebst.supplychain.keysight.com`) has no
  saved "System Table" view; the old env did. Exact error string: NOT RECORDED.
- **Test data, Step 3:** Step 3 grabs the FIRST "Preliminary EC Part"; on one run it was a Spirent
  part (`INR-MIIM-002`) that the BOM Loader server blocks. Exact error string: NOT RECORDED in this
  document (the trigger text `"Attribute update is not allowed for spirent Part"` and error
  `#1500167` appear in the TESTAUTOMA-8450 document).

### Evidence used

**Mattered:**

- **The log, read to the FIRST error, not the last line.** The document states this as a rule and as
  what was done: "Walk the log to the first LogError/Throw, NOT the last line," because "cascading
  failures hide the trigger."
- **The error *type*, used as the primary narrowing device.** `STInvalidBoolean` = "a non-boolean was
  used where a boolean was required." The document's rule: "the error TYPE narrows the cause faster
  than the message," and it recommends a lookup table `{error_type -> likely_causes +
  where_to_look}`.
- **The literal-value fingerprint.** `'{DPI:250, searchR...}'` — the offending value quoted in the
  error appears on exactly one executable line, which localises the bug without searching.
- **The screenshot** — used to disambiguate failure classes. The document's rule: "Cross-check the
  screenshot with a vision model: is the element actually present? Present-but-not-read => Class B
  [OCR]. Absent => Class C/E/F [environment / timing / real defect]." **Genuinely necessary for the
  OCR sub-issue** (it established the part numbers were on screen and merely misread). For the
  primary `STInvalidBoolean` bug the screenshot was **not** necessary — the error type plus the value
  fingerprint were sufficient, and the document says a lint/parse pass "would have caught the missing
  `ImageFound()` wrapper in ms."
- **`git log` on recent history** — surfaced commit `c47ef962`, the "switch env URLs" commit. The
  document calls this decisive for the environment sub-issue: that commit "EXPLAINED the Class-C root
  cause: the env moved and the 'System Table' view didn't come with it."
- **`git log origin/Testing_Mar10`** during the final merge — revealed **PR #1061 (commit
  `7f3e3be4`)** had *independently fixed the same `STInvalidBoolean`*. That is why there was a merge
  conflict.
- **Branch-topology analysis** — explained why the PR diff showed an extra file (see What was got
  wrong first).
- **All other call sites of the shared handler** — proved every existing caller passes a single
  argument, which is what made an optional second parameter provably safe.

**Source files read, and in what order:** NOT RECORDED as an actual sequence. The document prescribes
a tier order (`context.md`/memory → failing script → the handler it calls → all other callers of that
handler → passing sibling tests → git history) and says "this pipeline maps 1:1 onto how 8449 was
actually solved," but does not record the concrete file list.

**Supplied by Jay from his own head, not in any file:** the document's Q9 records that Jay supplied,
*later than would have been ideal*, two things that were not in any file:

- the constraint **"don't skip critical steps; original path first, fallback later"** — "You gave this
  later — having it at the start would have avoided one iteration";
- delivery preferences (branch name, target branch `Testing_Mar10`, commit-message style, no
  co-author) — "given late; give early".

It also notes that **how to run one test** (which suite to open, how to execute a single script, where
logs land, ~11–17 min run time) "had to be asked for" and was "pure latency."

**Turned out irrelevant / a trap:** the **29 "Exceptions"** present in the *passing* run. They were
"by-design not-found probes, NOT failures." The document warns: "An agent that treats Exceptions as
failures will mis-triage constantly."

### Root cause

**Four distinct root causes under one ticket number, each in a different class.** The document's
taxonomy labels are used below.

1. **Class A — script logic bug (the reported one).** An `else if` had a **bare property list**
   instead of `ImageFound(...)`. In SenseTalk, `{DPI:250, searchRectangle:..., ...}` is a *property
   list* — a data structure, not a truth value. An `if` / `else if` requires a boolean. So SenseTalk
   raised `STInvalidBoolean` at runtime and the test crashed. Stated in one sentence by the document:
   "else-if dropped the `ImageFound()` wrapper, so SenseTalk evaluated a raw property list as a
   boolean -> `STInvalidBoolean`." **File and line: NOT RECORDED in this document** (the *8450*
   document places the same bug in `EngineeringCentral.script`, handler `enterBOMLoaderValues`).
2. **Class B — recognition / OCR failure.** `DPI:250` could not read hyphenated part numbers
   (`B1506AU-OC-PRD`, `E7515B-FWS`, `005146-OSP`). The elements were on screen; the recognition
   settings could not resolve them. Nothing about the test's intent was wrong.
3. **Class C — environment drift.** The BST estate moved to
   `3dxspacebst.supplychain.keysight.com` (old: `3dxspace23xbst.cos.is.keysight.com`, commit
   `c47ef962`). **The saved "System Table" view did not migrate with it.** The test selected that view
   in order to expose the `Source` column — but on the new environment `Source` is visible by default,
   so the view was a means, not the goal.
4. **Class D — test-data dependency.** Step 3 selects the **FIRST** "Preliminary EC Part" in the
   results. That is non-deterministic. On one run it resolved to a Spirent part (`INR-MIIM-002`) whose
   BOM Loader updates the server blocks. Not a code defect.

### The fix

One fix per class. The document records the shapes; only one exact line is quoted.

1. **Class A — restored the `ImageFound()` wrapper** around the property list in the `else if`
   condition. Literal before/after: NOT RECORDED in this document. (The *8450* document records the
   same edit as
   `BEFORE: else if (text: partNumToClick, DPI:250, ... validCharacters:..., waitfor:5)` /
   `AFTER: else if ImageFound(text: partNumToClick, DPI:250, ... validCharacters:..., waitfor:5)`,
   with the source's own ellipses.)
2. **Class B — an OCR fallback ladder**, an ordered cascade tried until one hits:
   ```
   rung 1: DPI:250                          (original, fast, default)
   rung 2: DPI:72  + validWords:<token>     (best for hyphenated tokens)
   rung 3: DPI:250 + validCharacters:<token> (character-level fallback)
   else  : hard error                       (do not silently pass)
   ```
   Note the ordering: the original setting stays first. That ordering was **imposed by a human
   reviewer** — see What was got wrong first.
3. **Class C — an optional parameter with a default that preserves old behaviour.** The one exact line
   the document quotes:
   ```
   if isMandatory is empty then put "yes" into isMandatory
   ```
   With `isMandatory:"no"`, a missing table view is tolerated; the **real** validation
   (`Source = "bomloader"` count check) still runs, because `Source` is default-visible on the new
   env. "Intent preserved, nothing skipped."
4. **Class D — diagnosed, flagged as separate, and deliberately NOT masked.** No code change.

### What was got wrong first

**No wrong root-cause hypothesis is recorded in this document.** The diagnosis is presented as
linear: read the log to the first error → recognise the error type → resolve handler and line →
classify each sub-failure → fix each per class.

**UNCERTAIN whether that reflects the session or the write-up.** This document is structured as a
9-question architecture Q&A rather than a chronological log (unlike the 8278 and 8450 write-ups, which
do record their wrong turns round by round). So I cannot tell whether the diagnosis genuinely was
first-shot correct or whether wrong turns simply were not written down. I am not going to assert
either. **Do not train JARVIS on "8449 was solved cleanly first time" as a fact.**

**What friction *is* recorded — and it is all post-diagnosis, not diagnostic:**

1. **Human review feedback on the OCR ladder ordering.** "the reviewer asked to reorder the OCR
   attempts." The document draws a behavioural rule from it: "the agent must accept and re-apply
   feedback, not re-litigate it." This aligns with Jay's later-stated constraint "original path first,
   fallback later" — i.e. the first version of the ladder did *not* have the original DPI:250 setting
   first, and a human corrected it.
2. **Branch-topology confusion — "why is this file in my diff?"** `fix/Testautoma-8449` had been
   created **on top of `fix/Testautoma-8448`**, which carried an unrelated commit (the PowerShell
   download-detection change touching `TESTAUTOMA_4109` — i.e. 8448's own fix). So the 8449 PR diff
   showed an extra, unrelated file. **The document's key insight here:** "'why is this file in my
   diff?' is answered by ancestry, not by the working tree." Resolved by rebasing onto the real target
   branch. This is a real dead-end class — inspecting the working tree cannot explain it, and an agent
   that tries will find nothing wrong.
3. **A merge conflict from duplicated work.** PR **#1061** (commit `7f3e3be4`) had independently fixed
   the same `STInvalidBoolean`. Found via `git log origin/Testing_Mar10`. The document's rule:
   "someone else may already be fixing 'your' bug; history tells you before you clobber their work."

### Knowledge source

**Multiple — `script_only` (for the primary bug) + `sibling_scripts` + `tribal` + `app_behaviour`.**

- **`script_only` for the Class A bug.** The error type plus the quoted value fingerprint located it,
  and the correct idiom was available locally. The document notes that a **SenseTalk lint/parse pass
  would have caught it in milliseconds**, before any 12-minute run — this bug never needed a run at
  all.
- **`sibling_scripts` for the Class B ladder.** "The DPI/validWords OCR idea was already used
  elsewhere in the suite for hard-to-read text; the fix reused that known-good pattern rather than
  inventing one." Also for Class C: reading the other call sites proved they all pass a single
  argument, which is what licensed the optional-parameter approach. The document's instruction to the
  model: **"Prefer an approach already present in the codebase over a novel one; cite the file you
  copied it from."**
- **`tribal` — several facts existing nowhere in the codebase:**
  - the BST URL migration and, critically, **that saved views did not come with it** (the "System
    Table" view exists on the old env, not the new);
  - that `Source` **is default-visible on the new BST env**, which is what makes the fallback
    legitimate rather than a skipped assertion;
  - that some parts (Spirent / WebINR-owned) are **blocked by server triggers**, and that
    "first Preliminary EC Part" is **non-deterministic**;
  - the *house style* facts: when to use `DPI:72` vs `144` vs `250`, `validWords` vs
    `validCharacters`, contrast — and the ladder idea itself as house style;
  - **log semantics**: Exceptions ≠ Errors ≠ Warnings, and 29 Exceptions in a *passing* run are
    by-design probes.
- **`app_behaviour`** — the BOM Loader server trigger blocking Spirent parts; the domain glossary
  (EBOM, BOM Loader, SDE-COS, `Source=bomloader`, Maturity State).
- **Operational knowledge that had to be asked for:** how to run one test, and where logs and
  screenshots land, and the ~11–17 min run time so the agent can budget verification.

### Fixable component

`script` **and** `test_data` — **`multi_cause: true`**

- Classes A, B, C → `script` (the test and a shared handler in the repo). Note Class C is an
  *environment-caused* problem given a *script-side* remedy: the environment was not changed; the
  script was made tolerant of it while keeping the real assertion. The four-value taxonomy cannot
  express "environment-caused, script-fixed" — flagging rather than forcing.
- Class D → `test_data`, explicitly not code-fixed. "Usually NOT a code fix; fix data selection or
  flag to humans."

### Failure family

`boolean_logic_gap` · `dpi_cascade` · `environment_issue` · `test_data` — **`multi_cause: true`**

- `boolean_logic_gap` — Class A, exact fit: a non-boolean used in a boolean context.
- `dpi_cascade` — Class B, exact fit: element on screen, recognition settings could not read it,
  remedy is a DPI/constraint ladder.
- `environment_issue` — Class C: a saved view that exists on one environment and not another.
- `test_data` — Class D: non-deterministic selection landing on a server-blocked record.

All four are clean fits. This ticket is the best available demonstration that the twelve-family
vocabulary works *when* the ticket is decomposed into sub-failures first — the document's own rule:
"one ticket can hide several root causes; treat each separately."

### Handlers involved

```
test (TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed)
    → enterBOMLoaderValues           (the STInvalidBoolean crash site)
        → assertWithScreenshot       (the log's chain: [enterbomloadervalues -> assertwithscreenshot])
    → selectTableViewDropDownOptions (SHARED — the Class C change)
```

- `selectTableViewDropDownOptions` is shared. Callers enumerated: the **two 2878 call sites** that were
  intentionally edited, and — per the *8450* document — tests **2878, 2879, 4100**, plus **a
  different handler with the same name in `M&AFoundational`**. That name collision is a live hazard:
  resolve handlers by suite/scope, not by name alone.
- The document's blast-radius verdict: every existing caller passes one argument → hits the new
  default → "provably blast-radius zero" outside the two edited lines.

**Surprising / misdescribing:** `selectTableViewDropDownOptions` reads as "select a view," but in this
test its actual *purpose* was to expose the `Source` column. Once you know `Source` is default-visible
on the new env, the handler's call becomes optional without weakening the test — you can only see that
by knowing the *intent*, not the name. This is the concrete case behind the rule "preserve intent, not
steps."

### Outcome

**Validated by a re-run; PR merged. Not recorded as a full end-to-end PASS verdict.**

Precisely what the document says:

- "Verified by re-run and read the fresh log for the exact previously-failing assertion flipping to
  PASS."
- The verification standard it prescribes and claims to have met: "confirm the assertion that
  previously failed now passes AND nothing downstream broke."
- It refers to "the passing run" when discussing the 29 by-design Exceptions, which implies a passing
  run existed.
- The merge happened: the merge-conflict-with-PR-#1061 episode is described as occurring "During the
  final merge."

**No run id, no "0 errors / 0 warnings" statement, and no DAI pipeline confirmation are recorded for
8449** — unlike 8448 and 8450, which both have explicit green confirmations. So: validated by re-run
and merged; a formal PASS verdict on the whole test is NOT RECORDED.

### What would have made this faster

1. **A SenseTalk lint / parse step before any SUT run.** The primary bug is a static type error. "a
   parse/lint pass would have caught the missing `ImageFound()` wrapper in ms" — versus a 12-minute
   run. This is the single highest-leverage item for this ticket class.
2. **An `{error_type -> likely_causes + where_to_look}` lookup table.** `STInvalidBoolean` → "a
   non-boolean used as a condition" → "look for an `if`/`else if` whose condition is a bare property
   list." Deterministic, cheap, and it front-loads the whole diagnosis.
3. **A symbol index (`handler name -> file:line`)** so `enterBOMLoaderValues` resolves instantly
   instead of being searched for.
4. **`context.md` must state log semantics: Exceptions vs Errors vs Warnings**, with the concrete
   calibration "29 Exceptions in the passing run were by-design not-found probes, NOT failures."
   Without this an agent mis-triages constantly.
5. **`context.md` must carry the environment facts:** the BST URL migration *and its consequence*
   ("saved views did not migrate"; "`Source` is default-visible on BST").
6. **`context.md` must carry test-data fragilities:** "first Preliminary EC Part" is
   non-deterministic; Spirent / WebINR-owned parts are blocked by server triggers.
7. **`context.md` must carry OCR conventions as house style:** when to use DPI 72 / 144 / 250,
   `validWords` vs `validCharacters`, contrast, and the ladder pattern itself.
8. **State the constraints and delivery preferences up front, not late.** "don't skip critical steps;
   original path first, fallback later" arrived late and cost an iteration on the ladder ordering.
   Branch/commit/target-branch conventions likewise.
9. **`git log` on recent history, run automatically whenever the failure might be a regression.** It
   is what produced commit `c47ef962` and explained Class C.
10. **Check `git log origin/<target-branch>` before opening a PR**, to catch someone else having
    already fixed the same bug (PR #1061).
11. **Check branch ancestry (`merge-base` / topology), not the working tree**, when the PR diff
    contains an unexpected file.
12. **A ticket-intake template**, so this is never asked for again:
    `ticket_id, dai_run_id, branch, commit, failing_script, expected_behaviour, actual_behaviour,
    acceptance_criteria, scope(this/siblings), constraints, recent_env_changes, related_tickets,
    delivery(branch_name, target_branch, commit_style)`. The document's caveat: a good agent should
    *derive* most of this itself; treat the template as "reduce what must be asked," not "refuse to
    start without it."

### Notes

- **Provenance and its limits.** Derived entirely from `TESTAUTOMA-8449.txt`, written as an
  architecture reference ("REFERENCE NOTES FOR AN AI SCRIPT-FIXING APPLICATION") rather than a
  chronological session log. Its claim: "Every recommendation below is tied to something that really
  happened while fixing `TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed`." Because of that
  structure, the absence of recorded wrong turns is weak evidence that there were none — see What was
  got wrong first.
- **8449 and 8450 are the same bug in the same handler, on sibling tests.** 8449 =
  `TESTAUTOMA_2878_001`; 8450 = `TESTAUTOMA_2879_002`. Both are `STInvalidBoolean` from a bare
  property list in `enterBOMLoaderValues`, and both needed the `isMandatory` fallback in
  `selectTableViewDropDownOptions`. **A future agent that fixes one should immediately check the
  other.** The document flags this directly: "sibling tickets 2879/4100 share the same step — Jira
  links would let the agent fix a whole family at once."
- **`4100` is named as a third caller of `selectTableViewDropDownOptions`** and as a sibling sharing
  the step. Whether it was ever checked or fixed: NOT RECORDED.
- **The single most important prohibition in this document:** "a green test that skipped its assertion
  is worse than a red one — it lies." The Class C fix was deliberately built so the real
  `Source = "bomloader"` count check still runs. Any agent allowed to weaken assertions to reach green
  will produce exactly the failure mode this rule exists to prevent.
- **Safety gates the document proposes, worth carrying into JARVIS verbatim:** the failure class must
  be **named with evidence before any patch**; shared-handler edits must pass impact analysis with
  HIGH risk escalating to a human; "no validation/assertion may be removed to pass"; auto-merge only
  for LOW risk. And: "If your agent cannot confidently name the class, it must STOP and ask /
  escalate rather than patch. A wrong class = a wrong (or masking) fix."
- **Things that looked like the cause but were not:** the 29 Exceptions in a passing run (benign
  probes); and the extra file in the PR diff (branch ancestry, not a stray edit).
