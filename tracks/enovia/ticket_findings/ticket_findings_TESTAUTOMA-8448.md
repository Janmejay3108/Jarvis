## TESTAUTOMA-8448

**Failing test:** `TESTAUTOMA_4109_RT008_ValidatetheEBOMReportExporttoExcel` — the ticket title is
recorded as `Scriptfix: TESTAUTOMA_4109_RT008_ValidatetheEBOMReportExporttoExcel` (line-wrapped in the
source between `...EBOMReport` and `ExporttoExcel`). The `.script` extension is not shown in the
source; the filename is assembled from the ticket title.
**Suite:** `EngineeringCentral.suite`
**DAI runid:** NOT RECORDED. Runs are labelled `R1`–`R7` plus a final `DAI` run; no run ids appear.

### Symptom

The test opens a Part's Engineering BOM and exports four report types to CSV (the EBOM tab itself,
AVL Report, Multi-Level Report, AVL Multi-Level BOM), confirming each download.

Verbatim failures, in the order they occurred:

- **R1, Step 6:** `No Image Found: Icons/tools` — recorded interpretation: "toolbar not rendered /
  timing".
- **R2, Step 6:** validation failed on token `.csv` — recorded as "truncated/unreadable in popup".
- **R3, Step 5:** validation failed on token `Multi-` — recorded as `(OCR)`.
- **R4, Step 5:** validation failed on token `AVL_Multi` — recorded as `(OCR)`.
- **R5, Step 5:** validation failed on token `Level_Report`.

The full error line for R2–R5 (i.e. whatever wrapper text surrounded the failing token) is **NOT
RECORDED** — the source names only the token that failed at each round.

### Evidence used

**Mattered:**

- The per-round logs, principally for the **step number and the failing token**.
- **The cross-round timing invariant — the single most valuable piece of evidence.** Three different
  tokens had failed at the **same ~30s mark**. That invariant is what identified the real cause: "the
  cause is the CLOCK (a timeout + a fragile popup), not the token."
- **The captured screenshot at R5.** Reading it showed "the file was ALREADY on disk." This is what
  proved the export itself was working and the *validation* was the problem.
- **Whether the log alone would have been enough: UNCERTAIN.** My reading is that the ~30s invariant
  was present in the logs across R2–R5 and would by itself have been sufficient to abandon
  token-swapping — the tokens were changing, the failure time was not. The screenshot then supplied
  the positive confirmation (file present) that justified switching to a disk oracle. I am unsure
  because the source records both signals arriving together at R5 as one "PIVOT" and does not say
  which was load-bearing.
- **Sibling script 4105** — found via deterministic retrieval (call-graph + ripgrep + `context.md`,
  no vector DB). It was the other caller of the shared handler, and defined what must not break.
- **AI code review** on the PR, which found two real defects in the new fix (see The fix).

**Source files read, and in what order:** NOT RECORDED. The document names the shared handler
`exportBOMreport` and the wait primitive `common.IsImagePresentOnScreen`, but never records a file
read order or any line numbers.

**Supplied by Jay from his own head, not in any file:** NOT RECORDED as domain knowledge. What Jay
supplied was **hands and decisions**, not facts: he triggered each of the ~7 SUT runs (12–17 min
each), pasted back the logs and screenshots, made the approach decisions, drove all git/PR/merge/
force-push, and answered review comments. The document is explicit that this round-tripping existed
"ONLY because the tool loop was a human."

**Turned out irrelevant:** the token values themselves. Four separate token choices
(`.csv` → `Engineering_Bill_of_Materials`, `Multi-` → `AVL_Multi`, `AVL_Multi` → `Level_Report`) were
all beside the point.

### Root cause

**Three stacked causes, not one.** The document is emphatic: "Root cause was NOT one bug — it was
three".

1. **Timing / toolbar not rendered.** The export was clicked before the toolbar had rendered, so the
   `Icons/tools` image was genuinely not on screen yet. (R1.)
2. **A fragile visual oracle.** The download validation worked by **OCR-reading the Edge download
   popup** — a transient, low-fidelity UI surface. Whether a given filename token could be read out
   of that popup was effectively a coin flip, which is why every token substitution appeared to "work
   differently" without ever fixing anything.
3. **A timeout race.** The **slowest** of the four reports finished downloading *just after* the
   validation's timeout expired. So even a perfectly-read token would have failed for the slowest
   report. This is why all three token attempts died at the same ~30s point.

Because of (2) and (3) together, the thing the code was *asserting on* (pixels in a popup, within a
fixed window) was the wrong source of truth. The actual ground truth — the file on disk — was
available all along and was never consulted.

**File paths and line numbers: NOT RECORDED.** The document names `exportBOMreport` as the shared
handler and `common.IsImagePresentOnScreen` as the wait primitive, and gives no file paths or lines
for either.

### The fix

Two changes, both to the export/validation path:

1. **Add a render wait before the export click** — `common.IsImagePresentOnScreen`, plus "change
   token" (R1's fix as recorded: "add common.IsImagePresentOnScreen wait before export; change
   token").
2. **Replace the popup-OCR validation with an on-disk check.** A PowerShell check of the actual file
   on disk, whose **result returns via the clipboard**. Implemented as an **opt-in,
   backward-compatible addition** to the shared handler `exportBOMreport` — so its other caller
   (test 4105) is unaffected.

Applied first to Step 5 (green at R6), then — after discovering Step 6's OCR path was "ALSO flaky (no
report-page backstop)" — to Step 6 as well (green at R7).

**Literal before/after lines: NOT RECORDED.** The document describes the mechanism change and the
backward-compatibility property, and gives no diff.

**Two hardening changes applied in response to AI code review on the PR:** `regex-escape` and
`single-quote injection` hardening. (These are real defects that a naive "shell out to PowerShell
with an interpolated filename" fix introduces. Exact code: NOT RECORDED.)

### What was got wrong first  ← THE MOST IMPORTANT SECTION

**This ticket is a textbook case of changing the wrong variable four times in a row.**

**First hypothesis (R1): timing.** This one was *correct* — the toolbar genuinely had not rendered.
The wait fix held. But R1 also "changed the token", which planted the idea that the token was a knob
worth turning.

**The dead end: R2 → R3 → R4 → R5, four rounds of token-swapping.**

| Round | Change made | Result |
|---|---|---|
| R2 | token `.csv` → `Engineering_Bill_of_Materials` | Fail, Step 5, token `Multi-` |
| R3 | token → `AVL_Multi` | Fail, Step 5, token `AVL_Multi` |
| R4 | token → `Level_Report` | Fail, Step 5, token `Level_Report` |
| R5 | — | Fail again; **pivot** |

At 12–17 minutes per run, that is roughly **an hour of SUT time spent substituting one string for
another**.

**The false signal that caused it:** the failure message *names the token that was not found*. That
makes the token look like the independent variable. Each substitution produced a *different* failure
message, which felt like progress — a new token, a new error — when in fact nothing had changed. The
document's phrasing of the insight that broke it: "the thing I keep changing is not the cause; the
invariant is."

**What finally corrected the course (R5), two things at once:**

1. Reading the **captured screenshot** — the file was already on disk, so the export was fine and the
   *validation* was the defect.
2. Noticing that **three different tokens had failed at the same ~30s mark** — so the controlling
   variable was the clock, not the string.

That reframed the fix from "find a readable token" to "stop reading pixels; check the file."

**Second, smaller wrong turn:** the R6 fix was applied only to Step 5. Step 6's OCR path was *also*
flaky and had "no report-page backstop", so it needed the same treatment. Found only after opening the
PR, fixed at R7. The lesson: when you replace a fragile mechanism, sweep every place that mechanism
is used in the same test, not just the one that happened to fail.

**Total: ~7 SUT runs, of which 4 (R2–R5) were spent on a variable that was not the cause.**

### Knowledge source

**Multiple — `tribal` + `sibling_scripts` + `app_behaviour`.**

- **`tribal` — the decisive gap.** The knowledge needed was an *engineering principle* that existed
  nowhere in the codebase: **an oracle hierarchy.** The document states it as a ranked list:
  `(1) filesystem/API/DB > (2) DOM/app-API > (3) clipboard/text > (4) template-match > (5) OCR of
  live UI (flaky)`, with the rule "A download's ground truth is the file on disk, not pixels in a
  popup." Plus the concrete sub-rule "never validate short/hyphenated tokens like `.csv`". The
  document calls this "the single most reusable lesson from 8448" and estimates that having it
  written down "would have collapsed R2-R6 into one attempt."
- **`sibling_scripts`** — needed to read the *other* caller of `exportBOMreport` (test **4105**) to
  establish the contract the change must not break, which is what forced the opt-in/default-
  preserving shape of the fix.
- **`app_behaviour`** — that the Edge download popup is transient and unreliable to read, and that
  the slowest of the four reports takes longer than the existing validation window.
- **Not `script_only`.** Everything mechanically needed was in the file, but the *insight* was not:
  the file contains a plausible-looking OCR validation, and nothing in it says "this approach is
  fundamentally unsound."

The structural point the document draws: a minimal-diff-first bias actively obstructs this class of
fix, because "Some correct fixes are NOT minimal diffs." It recommends generating one **divergent
candidate** at attempt ≥2 with an explicit prompt: "The current approach may be fundamentally
unreliable. Propose a more robust ALTERNATIVE MECHANISM to achieve the same validation (prefer a
non-visual oracle)."

### Fixable component

`script` — all changes were in the repo (the test's validation path and the shared handler
`exportBOMreport`). No environment or test-data action was needed.

### Failure family

`missing_wait` · **`PROPOSED: flaky_oracle`** — **`multi_cause: true`**

- `missing_wait` — R1, the unrendered toolbar. Clean fit.
- **`PROPOSED: flaky_oracle`** (the source document's own proposed name; it also calls it
  `ocr_fragility`) — "the check is reading a low-fidelity, transient surface when a deterministic
  source of truth exists; the fix is to change the *mechanism* of verification, not its parameters."
  **None of the twelve fits, and forcing it would mis-route badly:**
  - `text_label` would send the agent to fix the token — **that is precisely the hour-long dead
    end.**
  - `dpi_cascade` would send it to tune OCR parameters — same trap, one level down.
  - `missing_wait` covers R1 but not causes (2)+(3); lengthening the timeout would have papered over
    (3) while leaving the popup-OCR fragility intact.
  This family is worth adding *because* the three nearest existing labels each name a plausible
  wrong fix.
- The timeout race (cause 3) is arguably a fourth thing. It is subsumed by `flaky_oracle` here
  because replacing the oracle removed it, but note that a pure timeout-extension fix would have been
  a partial, fragile fix rather than a wrong one.

### Handlers involved

```
test (TESTAUTOMA_4109_RT008_ValidatetheEBOMReportExporttoExcel)
    → exportBOMreport                  (SHARED — also called by test 4105)
    → common.IsImagePresentOnScreen    (added as the render wait)
```

- `exportBOMreport` is the shared handler; the blast radius was **test 4105**, handled by making the
  disk-check **opt-in with the old behaviour as the default**.
- A pre-existing on-disk validation handler named `validateDownloadedFileOnDisk` is described in the
  *TESTAUTOMA-8450* playbook document as already existing in the codebase, and the *TESTAUTOMA-8449*
  document refers to this same disk-check pattern as "recorded in memory from a sibling task."
  **UNCERTAIN whether 8448's fix used, extended or duplicated `validateDownloadedFileOnDisk`** — the
  8448 document never names it, so I cannot tell whether the precedent already existed at the time of
  8448 or was *created by* 8448 and then referenced by the other two write-ups. This matters: if the
  precedent already existed, R2–R5 were avoidable by repo search alone.

**Surprising:** nothing recorded about a handler's name misdescribing it. The surprise here was
mechanical, not nominal — the validation *looked* like a normal check and was structurally unsound.

### Outcome

**PASSED — validated twice, by two independent runs, and merged.**

- **R7: green locally** (Steps 5 and 6 both via the disk check).
- **Then independently green in the DAI production pipeline, on a different environment and a
  different part: 0 errors, 0 warnings.** The document leads with this and repeats it: "green locally
  and then INDEPENDENTLY green in the DAI pipeline on a different environment and a different part".
- Merged. The document's header states the ticket was resolved "end-to-end (merged + green in DAI)".

The different-environment / different-part second confirmation is the strongest validation in any of
the six tickets — it rules out the fix having been tuned to one machine's rendering.

### What would have made this faster

1. **An attempt ledger fed into every retry.** The document's concrete proposal:
   `[{attempt, hypothesis, change_made, failure_signature, failure_timestamp}]`, with the standing
   instruction: *"If multiple attempts failed at the same step/location/elapsed-time, the ROOT CAUSE
   IS THE INVARIANT across them, not the value you keep changing. Switch failure family or propose a
   MECHANISM change."* Note the required field: **`failure_timestamp`**. Without elapsed time in the
   ledger, the ~30s invariant is invisible and this ticket repeats.
2. **The oracle-hierarchy rule in `context.md`**, as a named failure family with the disk-check +
   clipboard exemplar. Estimated in-document to collapse R2–R6 into one attempt.
3. **The specific gotcha `never validate '.csv'`** — and more generally, never validate short or
   hyphenated tokens. This is knowledge, not reasoning; no amount of thinking recovers it.
4. **A mechanism-change escalation at attempt ≥2**, generating one divergent non-minimal candidate
   alongside the minimal patches and ranking them together.
5. **Pass the test's intent into the fix prompt** (one line, sourced from the ticket or test
   docstring), so a candidate can never "pass" by removing a real check.
6. **Re-pull origin and diff the target file before applying to a shared handler.** A colleague
   pushed a change to the *same* shared handler mid-flight, causing a merge conflict.
7. **Sweep every use of a mechanism you are replacing** within the test, not just the failing one —
   Step 6 needed the same fix and was found only after the PR was open.
8. **Tier-0 lint before any SUT run.** At 12–17 min per run, "never burn a 12-17 min run on a typo"
   is the direct answer to run expense.

### Notes

- **Provenance and its limits.** Derived entirely from `TESTAUTOMA-8448.txt`, a session retrospective
  written after the ticket was merged and green, not from the session transcript. Its own framing of
  the friction is worth carrying forward verbatim: "the volume of inputs you saw is largely a property
  of ME being tool-less on a hard ticket" — i.e. most round-trips were the human acting as the tool
  loop (trigger run, paste log, paste screenshot, drive git), not the model failing to reason.
- **This ticket is explicitly nominated as the canonical hard exemplar** — "multi-cause +
  oracle-swap" — on the grounds that "One good hard exemplar teaches more than ten easy ones." If
  JARVIS gets seeded with exemplars, this is the one to include for the non-minimal-fix case.
- **The document positions this ticket in the hard ~20% tail**, not the median. Stated Gate targets
  it references: ~60% first-attempt and ~80% final (≤3 attempts) fix pass, ~75% equivalence, zero
  regressions — which explicitly means ~20% of tickets will not be auto-fixed, and that is designed
  for, not a failure.
- **SUT throughput is named as the real bottleneck, not model quality.** One serialized RDP SUT and
  one EPF license; a Practice DAI run is 20 min – 2 hr. A single hard ticket can consume up to
  3 attempts × 1 run, plus N-best extra candidates, plus caller smoke runs — hours of exclusive SUT
  time, capping throughput at a handful of hard tickets per day. Mitigations named: make the local
  inner loop work, lean on free Tier-0 lint, keep smoke sets small.
- **Things that looked like the cause but were not:** the filename token (four times over); and, at
  R2, the idea that `.csv` was merely "truncated" — the real problem was that the surface being read
  was unreliable *and* the clock was too short.
- **Parallel-edit hazard is real, not theoretical.** A colleague's OCR improvement landed on the same
  shared handler mid-flight; the resolution was to rebase and merge their change into the untouched
  branch.
