## TESTAUTOMA-8278

**Failing test:** `TESTAUTOMA_6157_NewPhysicalProductFreezeFlow.script`
**Suite:** `PartMaster.suite` (full path as recorded:
`Enovia/PartMaster.suite/Scripts/TestCases/TESTAUTOMA_6157_NewPhysicalProductFreezeFlow.script`)
**DAI runid:** NOT RECORDED. The document labels runs `R1`–`R7` with no run ids.

### Symptom

Verbatim, as recorded: the log ends with

```
Unable to Find Image (TEXT:"Set Enterprise Item Number")
```

→ `clickElement` throws → testcase FAILED.

It died on **Step 7**. The document states this explicitly and repeatedly ("the failing step
(Step 7)", "Reached Step 7 (the real target)").

Two further, *different* failures surfaced during the fix cycle and matter for the record:

- **R2, Step 3 (`open3DDashboard`)** — a failure "unrelated to the ticket", which appeared only
  because the test was re-run in a drifted environment. Exact error string: NOT RECORDED.
- **R6, launch/login** — an OCR flake on `"3DEXPERIENCE"` splash / `"Type the name"` / `"Run"` text
  "not detected in the wait window". Exact error string: NOT RECORDED.

### Evidence used

**Mattered:**

- The log line above — sufficient to identify the failing script (6157), the failing step (Step 7),
  and the immediate root cause (the menu command no longer exists). The document states R1
  "Correctly identified" all three from ticket + log + screenshot.
- **The error screenshot at R3 — genuinely necessary.** The log at R3 said only that
  `"Enterprise Item Number"` was never found in the Information panel. The screenshot "proved why —
  the read-only Info panel does not list that field; it only shows in the page header." The log alone
  would **not** have distinguished "field is there but unread" from "field is not on this panel at
  all." This is the same discriminator the 7947 document formalises as the visible-text test.
- **The R4 run itself as evidence.** `enterKPN` scrolled the entire edit form for **~13 minutes**,
  found nothing, and OCR aborted. That exhaustive negative is what established the ground truth: the
  edit form has **all-caps** attribute labels (`ICAT`, `MSM FLAG`, `LEGACY PART NUMBER`, ...) and
  **no "Enterprise Item Number" field at all.**
- Source files read: NOT RECORDED as an ordered list. The document names the handler `enterKPN` as
  "the repo's existing enterKPN handler (Info -> Edit -> type -> Save)" and refers to `clickElement`
  and `open3DDashboard`, but never states which files were opened or in what order.

**Supplied from outside every file — the decisive input:**

At **R5** the initiative owner escalated to the **development team**, who supplied the one missing
fact: the value now goes in a **new field named `"KEYSIGHT PART NUMBER"`** (not "Enterprise Item
Number"), and that field feeds the header attribute. The document is emphatic:

> "the decisive input (the field name 'KEYSIGHT PART NUMBER') came from HUMAN TEAM KNOWLEDGE, not
> from code, logs, or screenshots. Once supplied, the fix was a one-line label change and it passed
> immediately."

UNCERTAIN whether Jay personally supplied it or relayed it: the document says "The owner asked the
development team", so the knowledge originated with the dev team.

**Turned out irrelevant / actively misleading:** the label `"Enterprise Item Number"` itself. It was
carried forward from the old removed menu command and was assumed to name the new field. It named
nothing in the new UI. Rounds R1, R3 and R4 were all spent on that assumption.

### Root cause

The application UI was **redesigned**. The menu command `Set Enterprise Item Number` was **removed
from the product**. The Enterprise Item Number (KPN) value is now entered on the *Physical Product
Information* page in **Edit mode**, in a **newly-named field: `KEYSIGHT PART NUMBER`**, which feeds
the header attribute.

The test still tried to click the removed menu command at Step 7, so
`Unable to Find Image (TEXT:"Set Enterprise Item Number")` was literally correct — the element no
longer exists anywhere in the application.

**File and line number of the failing call: NOT RECORDED.** The document never gives a line number
for any part of this fix.

The document's own classification of this root cause is the key point for JARVIS:

> "this is NOT a flaky-selector or a code-logic bug. It is an 'application changed, the test must be
> rewritten to the new workflow' ticket. Fixing it REQUIRES knowing the new intended workflow —
> information that is not present in the failing code, the DAI log, or the error screenshot."

**Secondary root cause (R2, off-ticket).** The BST environment had been "refreshed": the URL changed
`3dxspace23xbst` → `3dxspacebst`, and as a consequence "the 3DDashboard app moved lower in the app
list, off-screen". So Step 3 could not select it — not because the selector was wrong, but because
the target was below the visible region.

### The fix

Two files were committed.

**Fix 1 — the field label, in two places.** Recorded as: "Changed the field label in two `enterKPN`
calls. Nothing else." I.e. the label argument passed to `enterKPN` went from `Enterprise Item Number`
to `KEYSIGHT PART NUMBER`, at two call sites in
`TESTAUTOMA_6157_NewPhysicalProductFreezeFlow.script`.

**Literal before/after source lines: NOT RECORDED.** The document gives the two label strings and
the count of call sites, and nothing more.

**Fix 2 — off-ticket prerequisite.** "add a scroll before selecting it" in the 3DDashboard selection
path (Step 3 / `open3DDashboard`). Exact diff: NOT RECORDED.

**Deliberately NOT committed** (recorded because it was an explicit instruction): an unrelated local
`"Type the name"` **bypass**, plus other working-tree drift (`SuiteInfo`, `PartMaster.json`). The
document states the bypass "must NEVER be committed."

### What was got wrong first

This is the richest wrong-turn record of the six tickets. The path, as recorded:

**R1 — first hypothesis: partly right, wrongly specified.** Correctly diagnosed that the
`Set Enterprise Item Number` command had been removed, and correctly decided to "re-route KPN entry
through Information page Edit". But it **guessed the new field and flow**. The document's own status
line: "plausible but UNVERIFIED — guessed the new field/flow." So the *class* of the fix was right
from round one; every failure after this was about the *field label*.

**R2 — a detour that was not a wrong turn.** The run failed *earlier* than the target, at Step 3, on
an unrelated environment drift. This had to be worked around just to reach Step 7 at all. The
document names this a "prerequisite blocker vs the actual bug" distinction and notes the agent has no
concept of it — the danger being that a retry loop wanders onto the off-ticket failure and starts
"fixing" that instead.

**R3 — second wrong hypothesis.** Expected the text `"Enterprise Item Number"` to appear in the
read-only Information panel. Disproved by the **screenshot**, which showed the read-only panel does
not list that field — it only appears in the page header. Fix adjusted to use the existing `enterKPN`
handler (Info → Edit → type → Save). Status: "still guessing the field label."

**R4 — the dead end, and the most expensive round.** `enterKPN` scrolled the whole edit form for
**~13 minutes** looking for `"Enterprise Item Number"`, never found it, and OCR aborted. This
produced the ground truth that killed the whole line of reasoning: the labels are ALL-CAPS and there
is no such field.

**The false signal that caused the dead end:** the string `"Enterprise Item Number"` appearing in the
original error message. It looked like the name of the thing to search for. It was the name of the
*removed* thing. Three rounds (R1, R3, R4) were spent searching for a label that did not exist
anywhere in the new UI. No amount of further reasoning over code, logs or screenshots could have
produced `KEYSIGHT PART NUMBER`.

**What corrected the course:** **human escalation at R5.** The owner asked the development team; the
team named the field. Nothing in the repo or the evidence chain could have supplied it.

**Attempt count:** three code changes were made and run before the working one (R1, R3, R4), plus the
off-ticket R2 scroll fix. The working fix was the 4th code change and it "passed immediately."

**The document's own summary of the compressibility:** "Of the ~6 rounds, exactly ONE carried the
decisive information (the field name). Rounds R1-R4 were the assistant guessing in the absence of a
knowledge-gap escape hatch."

### Knowledge source

**`tribal`** — and this ticket is the cleanest example of it in the set.

The specific knowledge that was needed and existed nowhere in the codebase, the logs, the
screenshots, or git:

1. **The Enterprise Item Number value is now entered in a field named `KEYSIGHT PART NUMBER`.** This
   is a product-design fact held by the Enovia development team.
2. That this new field **feeds the header attribute** (i.e. it is the correct field, not merely a
   similarly-named one).

Adjacent knowledge that *was* discoverable but only by burning a 13-minute run, and which should
therefore also be written down:

3. **The Physical Product edit form uses ALL-CAPS attribute labels** (`ICAT`, `MSM FLAG`,
   `LEGACY PART NUMBER`, ...). An agent searching for a mixed-case label on that form will always
   fail. This is `app_behaviour`.
4. **The read-only Information panel does not list the Enterprise Item Number field**; that value
   appears only in the page header. Also `app_behaviour`.

The document's structural conclusion: for this ticket class the agent needs a first-class
`ask_human(question, why_needed, options?)` tool that **pauses and resumes** — not a "post a
diagnosis and stop" path. Without it, on every ticket of this class the agent will "either (a) guess
and thrash for 13 minutes like R4, or (b) give up with a diagnosis that still doesn't contain the
fix."

### Fixable component

`script` — the repo change was to the test script only (two label arguments), plus a one-line scroll
addition for the off-ticket blocker.

**But the *driver* was an application redesign, not a script defect.** The script was correct for the
application as it used to be. Recording this as plain `script` loses that; the four-value taxonomy
has no slot for "the app changed under a correct test."

### Failure family

`text_label` · `environment_issue` · **`change_scope`** — **`multi_cause: true`**

- The mechanical fix was `text_label` (a label string was wrong). **But routing on `text_label`
  alone would have re-run exactly the R1–R4 flailing**, because the correct label is not discoverable
  by any label-fixing strategy. `text_label` describes the diff, not the problem.
- `change_scope` — "application changed, the test must be rewritten to the new workflow;
  the new workflow is not present in code, logs or screenshots." None of the twelve names this. The
  source document independently proposes exactly this: "Add 'change_scope' and 'environment_flake' as
  first-class families in the router, and wire change_scope -> ask_human". *(Quoted verbatim. Both were
  ratified on 2026-07-30 — `change_scope` under that name, and `environment_flake` under the name
  **`transient_flake`**, which plan4 already used; see plan_master §3.)* The Jira ticket itself
  **carries the "Change Scope" label**, so this family is detectable *before* any diagnosis begins —
  which is the whole point of proposing it.
- `environment_issue` — the R2 3DDashboard blocker (BST refresh moved the app off-screen).
- **`transient_flake`** — the R6 launch/login OCR flake. Distinct from
  `environment_issue` because nothing is broken and nothing should be fixed; the correct handling is
  to *tolerate* it. Also independently proposed by the source document.

### Handlers involved

```
test (TESTAUTOMA_6157_NewPhysicalProductFreezeFlow) → clickElement            (threw at Step 7)
                                                    → enterKPN  ×2 call sites (Info → Edit → type → Save)
                                                    → open3DDashboard         (Step 3, off-ticket blocker)
```

The document notes the call chain "would have been" trivially recoverable by static call-graph +
handler map — it does not record that the chain was formally traced.

**Surprising behaviour:**

- **`enterKPN` has no fail-fast.** Given a label that does not exist on the form, it scrolled the
  entire edit form for **~13 minutes** before OCR aborted. A wrong label argument therefore costs a
  full run, not a fast error. Any agent generating candidate label values must treat each guess as
  ~13 minutes of SUT time.
- `enterKPN`'s name describes *what* it sets (KPN) but not *how* — the Info → Edit → type → Save
  sequence is invisible from the name.

### Outcome

**Split verdict, and this is the single most important operational fact in the ticket.**

**The fix was validated by an actual run and it worked.** R6 was a "FULL PASS end-to-end: invalid KPN
rejected, valid KPN saved and upper-cased, mandatory attributes filled, product reached FROZEN."

**But the run was reported as FAILURE.** One logged error — the unrelated launch-timing OCR flake
("3DEXPERIENCE" splash / "Type the name" / "Run" text not detected in the wait window) — flipped the
whole run's verdict. "Login actually succeeded; the flake just logged an error, which flips the whole
run to FAILURE."

So: **functionally PASSED, reported FAILED.** Both statements are true and neither may be dropped.

The document spells out what an exit-code oracle would have done with this: rejected a correct fix,
re-diagnosed the flake on the next attempt, and — "most alarming" — "plausibly 'fixed' it by DELETING
the 'Type the name' check (exactly the bypass the human explicitly said must NEVER be committed)."
That is a naive oracle producing an unsafe change, not merely missing a pass.

The fix was then committed (R7) — two files, junk excluded. Whether it was merged: NOT RECORDED.

### What would have made this faster

1. **An `ask_human` tool that pauses and resumes, invoked at R1.** The document's projected collapsed
   path: "diagnose -> detect knowledge gap -> ask ONE question -> apply -> validate (flake-tolerant)
   -> PASS." The trigger condition to encode: *the fix depends on a fact not derivable from code,
   logs or `context.md` — e.g. "what UI element replaced X?"* Guardrail: cap at 1–2 questions per
   run so it does not become a chat crutch.
2. **Route on the Jira "Change Scope" label before diagnosing.** 8278 literally carries it. A
   change-scope ticket should go straight to the knowledge-gap question, not into the code-only fix
   loop.
3. **Two facts that belong in `context.md` today:**
   `Physical Product edit form attribute labels are ALL-CAPS (ICAT, MSM FLAG, LEGACY PART NUMBER…)`
   and
   `KPN / Enterprise Item Number is entered in the field "KEYSIGHT PART NUMBER" on the Information
   page in Edit mode; the read-only Info panel does not show it — it appears only in the page header.`
   The document explicitly wants the R5 answer fed back as a `context.md` suggestion "so the NEXT KPN
   ticket needs no human."
4. **A failure-signature-based validation oracle instead of exit code.** Capture the ticket's failure
   signature at diagnosis time (failing step + the specific lookup that failed, e.g.
   `TEXT:"Set Enterprise Item Number"`); after a candidate run, PASS-for-this-ticket = *that
   signature is gone*, even if other failures exist — provided the others are either known-flaky
   infra steps or were already present on the un-patched baseline.
5. **A known-flaky step allowlist that can never by itself fail a fix:** login, the `3DEXPERIENCE`
   splash, the `Run` window. Plus re-run-N-times flake tolerance.
6. **Anchor every re-diagnosis to the original failure signature**, so an off-ticket blocker (the
   3DDashboard move) is handled as a *prerequisite to route around with a known-safe primitive*
   (scroll / wait) and never silently absorbed into the ticket's fix.

### Notes

- **Provenance and its limits.** Derived entirely from `TESTAUTOMA-8278.txt`, an architecture review
  dated 2026-06-30 written after the fix, not from the session transcript. Rounds are labelled
  R1–R7; the document itself says "~6 rounds", so the round count is approximate in the source.
- **The `"Type the name"` bypass is a named landmine.** It exists as a local change, it makes runs
  go green, and it must never be committed. An agent optimising for a green run will find it
  attractive. This should be an explicit prohibition in `context.md`, not just a reviewer habit.
- **Three independent problems in one run.** The EIN change (the ticket), the 3DDashboard move
  (environment drift), and the launch flake. The document warns that nothing in the planned retry
  loop anchors it to the ticket's own failure, so it can wander onto either of the other two.
- **The ticket relates to TESTAUTOMA-6157**, i.e. as with 7947, the ticket number is not the script
  number. 8278 is a "Change Scope story" that relates to 6157.
- **This ticket is proposed as a golden regression fixture** for two specific behaviours: the
  ask-human path and flake-tolerant validation. "correct fix, flaky launch -> the oracle MUST return
  PASS."
- **Things that looked like the cause but were not:** the label `"Enterprise Item Number"` (it named
  a removed command, not the new field); the Information panel (the field is not on it); and at R2,
  the 3DDashboard selector (nothing was wrong with it — the target had moved off-screen).
