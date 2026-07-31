## TESTAUTOMA-8814

**Failing test:** TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded.script
**Suite:** EngineeringCentral.suite
**DAI runid:** `34649` (the original failing run supplied by Jay, eventtime 2026-06-22). The three
subsequent runs on 7/21/26 were supplied as Eggplant-format text logs with no runid field —
`NOT RECORDED` for those.

### Symptom

**Run 1 (runid 34649) — the ticket as filed.** Died in "Running Steps 5 to 9" (the
`enterBOMLoaderValues` step). Verbatim:

```
Unable to Find Image (TEXT:"Your BOM file was processed successfully with no errors"). Text not found.
Validating BOM Loader Process - Actual Value (False) is NOT equal to Expected Value (True) - FAIL
Testcase failed in : ["ScripName : testautoma_2879_002_agilentpipedelimitedexpanded","HandlerName1 : enterbomloadervalues","HandlerName2 : assertwithscreenshot"]
Technical Error: Runtime Error at line 5 (line 661 of script): Validating BOM Loader Process - Actual Value (False) is NOT equal to Expected Value (True) - FAIL - (no reason given)
FAILED, 1 errors, 1 warnings, 4 state transitions, 2 actions executed
```

The part typed into Parent Assembly Name was `INR-MIIM-002`.

The error screenshot showed the BOM Loader dialog with Enovia's own error text:

```
Attribute update is not allowed for spirent Part.
Error: #1900068: connect business object failed Warning: #1500167: Check trigger blocked event
```

**Two further, different failures surfaced afterwards** (see "What was got wrong first"):

Run 2 (7/21 8:32:38–8:39:30) died in Step 2 at `clickHome`:
```
8:38:09 AM  ImageFound (TEXT:"Access other apps")  Unable to Find Image (TEXT:"Access other apps"). Text not found.
8:38:09 AM  Log  No Popup Found - Access other apps
8:39:26 AM  LogError  Text Tasks  Is not present on the screen
8:39:26 AM  Throw  Assertion Warning - Unable to click Home. Check if the top bar is disabled and consider escaping overlaying windows or panes.
8:39:26 AM  LogWarning  Testcase failed in : ["ScripName : testautoma_2879_002_agilentpipedelimitedexpanded","HandlerName1 : clickhome"]
Technical Error: Runtime Error at line 15 (line 716 of script): Assertion Warning - Unable to click Home...
EndTestCase (Errors:"2", Exceptions:"5", Successes:"14", Warnings:"1")
```

Run 3 (7/21 9:00:54–9:10:13) died at the *same* BOM Loader assertion as run 1, but for an unrelated
reason — the Parent Assembly Name typed was empty:
```
9:09:16 AM  typetext  [controlKey]a
9:09:16 AM  typetext                      <- empty; nothing typed
9:09:19 AM  typetext  [returnKey]
9:10:09 AM  ImageFound (TEXT:"Your BOM file was processed successfully with no errors")  Unable to Find Image ...
EndTestCase (Errors:"2", Exceptions:"22", Successes:"40", Warnings:"1")
```
Its screenshot showed Enovia's JS alert: `Please input the name of the parent assembly that you are
loading`, with the field blank.

### Evidence used

- **Run 1 log line(s):** necessary but *not sufficient*. The log said only
  `Validating BOM Loader Process - ... FAIL - (no reason given)`. It names no cause. On its own it
  would not have led to Spirent.
- **Run 1 error screenshot: genuinely necessary — the log alone was NOT enough.** The string
  `Attribute update is not allowed for spirent Part` and the trigger warning `#1500167` appear
  *only* in the screenshot, never in the log. However, see caveat below: the Jira description was an
  independent path to the same answer.
- **Jira ticket screenshot (supplied by Jay):** title *"Automation selects a Spirent part as the
  Preliminary part; Spirent server trigger blocks the BOM/attribute update and fails the test"*;
  description *"Parent part shouldn't have Engineering Responsibility as SP1 or SP2 or SP3 or SP4.
  Kindly put filter while searching the parent part."* This supplied the SP1–SP4 fact and prescribed
  the fix. Arguably the single highest-value piece of evidence — with it, the screenshot was
  corroboration rather than discovery.
- **Screenshots read from disk during run-3 diagnosis — decisive, and they overturned a hypothesis:**
  `Enovia/EngineeringCentral.suite/Results/21_07_2026_09_08_18.png` (state 1s before the
  triple-click) and `.../21_07_2026_09_08_24.png` (5s later). See "What was got wrong first".

**Source files read, in order:**
1. `context.md` (supplied by Jay)
2. Glob `**/TESTAUTOMA_2879*` → located the test
3. `TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded.script` (full)
4. Grep `to (handle )?searchEnovia`; Grep `Engineering Responsibility` repo-wide
5. `CommonEnovia.script:165-324` then `325-464` (the `searchEnovia` handler)
6. Grep `MQLQueries.json` → found `attribute[Engineering Responsibility]==02 || attribute[Engineering Responsibility]==00`
7. `git log` (checked for prior 8814 work — none)
8. `EngineeringCentral.script:3107` (`enterBOMLoaderValues`)
9. `EnoviaSearch.script` (full)
10. Grep `searchEnovia "advancedSearch"` repo-wide → the established sibling-test pattern
11. Later rounds: Grep `handleAccessOtherAppsPopup|Access other apps`; `PartMaster.script:190-231`;
    `CommonEnovia.script:680-739`; `config.script` (full); Grep `tripleClick|RemoteClipboard\(\)`;
    `CommonEnovia.script:1274-1293` and `:1575-1612`

**Supplied by Jay from his own head, not in any file:**
- That the probable cause was a Spirent part being blocked, and a pointer to read the Jira
  description (round 1).
- **That a handler already existed for the access popup** — *"There was this handler created. Look
  for it in some of the folders. That handler was specifically for clicking out on this type of
  access popup ... it was an optional thing."* This directly produced the round-2 fix. He described
  it as "the black popup on the top right"; it is actually rendered top-left, and the config
  rectangle used is `topLeftQuadrant`.

### Root cause

Three distinct defects, found one at a time. Only the first is the ticket as filed.

**1. `TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded.script:38` — unfiltered parent-part search.**
The advanced search constrained only Type and Maturity State:
```sensetalk
commonEnovia.searchEnovia "advancedSearch", [["Part", "Type"],["EC Part.Preliminary", "Maturity State"]]
```
The test then opens *the first result* and reuses it as the BOM Loader parent assembly. In this
Enovia deployment a part's `Engineering Responsibility` attribute identifies its owning org: `00`
and `02` are standard non-Spirent orgs, `SP1`–`SP4` are Spirent. Spirent parts carry a server-side
check trigger that rejects BOM/attribute updates. With no ER constraint, a Spirent part
(`INR-MIIM-002`) sorted to the top, was selected as parent, and the trigger blocked the load.

**2. `CommonEnovia.script:705` (pre-fix) — one-shot popup check inside `clickHome`.**
```sensetalk
if ImageFound(text:"Access other apps",watiFor:25,searchRectangle:config().SUT.TopLeftQuadrant)
```
Two problems: `watiFor` is a misspelling of `waitFor` (confirmed present in the original via
`git diff`); and the check ran exactly once, before `common.navigate`. Edge is launched
`-Inprivate`, so the permission grant is never remembered and the popup is intermittent. In run 2 it
rendered *after* the check had already logged `No Popup Found`, then sat over the page so `Tasks` was
never found.
> `UNCERTAIN — which of the two problems actually caused run 2.` The retry-absence clearly explains
> it (the popup was on screen at failure time per the screenshot, having appeared post-check). The
> typo is a real defect but I cannot prove from the logs that it changed run-2 behaviour — I asserted
> in chat that "the intended 25-second wait was never applied as written", which is an inference
> about how Eggplant treats an unknown named property, not something observed. Both were fixed
> together, so the runs do not separate them.

**3. `TESTAUTOMA_2879_002_...script:49` (pre-fix) — `commonEnovia.tripleClick[137,172]`.**
A hardcoded screen coordinate used to select-and-copy the part number, with two faults:
- (a) **No wait for the part page.** The script did `wait 3` → close 6W panel → triple-click
  immediately. `21_07_2026_09_08_18.png` proves the part page had not rendered: the screen still
  showed **"Collaboration and Approvals"** (the Tasks list) with the 6W Tags panel open over the
  left side.
- (b) **x=137 assumes a long part name.** In `21_07_2026_09_08_24.png` the opened part `E1827B`
  spans roughly x≈38–98, so x=137 falls past the end of the text and selects nothing. The
  previously-selected `INR-MIIM-002` spans roughly x≈38–148, so x=137 landed inside it. *(These x
  ranges are my visual estimates off the screenshots, not values printed in any log.)*

Result: `PartNum` was empty, a blank Parent Assembly Name was submitted, and the failure resurfaced
as the *same misleading* `Validating BOM Loader Process ... FAIL` message as the original Spirent bug.

### The fix

**1 — parent-part search (`TESTAUTOMA_2879_002_...script:38`, plus explanatory comment):**
```diff
-	commonEnovia.searchEnovia "advancedSearch", [["Part", "Type"],["EC Part.Preliminary", "Maturity State"]]
+	commonEnovia.searchEnovia "advancedSearch", [["Part", "Type"],["02","Engineering Responsibility"],["EC Part.Preliminary", "Maturity State"]]
```

**2 — `CommonEnovia.script`: extract a shared handler, and retry once inside `clickHome`:**
```diff
+to handleAccessOtherAppsPopup waitTime:5
+	try
+		if ImageFound(text:"Access other apps",waitFor:waitTime,searchRectangle:config().SUT.TopLeftQuadrant)
+			common.success "Access other apps popup found"
+			common.ClickBtnByText "Allow",20,config().SUT.TopLeftQuadrant,yes
+		else
+			Log "No Popup Found - Access other apps"
+		end if
+	Catch theException
+		"exceptionHandling".failedHandlerNavigation(callStack())
+		"exceptionHandling".errorCapture theException
+	End try
+end handleAccessOtherAppsPopup
```
```diff
 	try
-			if ImageFound(text:"Access other apps",watiFor:25,searchRectangle:config().SUT.TopLeftQuadrant)
-				common.success "Access other apps popup found"
-				common.ClickBtnByText "Allow",20,config().SUT.TopLeftQuadrant,yes
-			else
-				Log "No Popup Found - Access other apps"
-			end if
+			commonEnovia.handleAccessOtherAppsPopup 25
 			// click Home button
 			common.navigate "icons/homeButton", configEnovia().searchRectangles.topBar, expectationSR, expectation
 		catch theException
-			put "clickHome"&&formattedTime("%d%m%y-%H%M") into screenshotName
-			captureScreen {name:screenshotName}
-			throw "Assertion Warning","Unable to click Home. ..."
+			commonEnovia.handleAccessOtherAppsPopup 5
+			try
+				common.navigate "icons/homeButton", configEnovia().searchRectangles.topBar, expectationSR, expectation
+			catch theRetryException
+				put "clickHome"&&formattedTime("%d%m%y-%H%M") into screenshotName
+				captureScreen {name:screenshotName}
+				throw "Assertion Warning","Unable to click Home. ..."
+			end try
 		end try
```

**3 — part-number capture (`TESTAUTOMA_2879_002_...script`, comments omitted here for brevity):**
```diff
-	commonEnovia.tripleClick[137,172]
+	put [0,150,1000,240] into partHeaderSR
+	if not ImageFound(text:"Maturity State", waitFor:configEnovia().general.midWait, searchRectangle:partHeaderSR)
+		common.error "Part page header did not load - unable to read the parent part number", yes
+	end if
+	commonEnovia.tripleClick [55, item 2 of FoundImageLocation()]
 	typeText controlKey, "c"
 	put trimAll(RemoteClipboard()) into PartNum
+	log "Parent part selected for BOM Loader:" && PartNum
+	if PartNum is empty
+		common.error "Failed to read the parent part number from the part page header", yes
+	end if
```
`Maturity State` sits on the same header line as the part number, so it doubles as the page-loaded
gate and the y-anchor; x=55 sits inside both a short and a long part name.

### What was got wrong first

**On the ticket's actual issue (Spirent / ER filter): no wrong turn. First hypothesis was correct
and landed in one attempt.** Jay named the likely cause, the Jira description prescribed the filter,
and the codebase corroborated it independently (`MQLQueries.json` ER `02||00` convention; six-plus
sibling tests already using `["02","Engineering Responsibility"]` for Preliminary-part searches). No
re-run was needed to diagnose it. That is a real finding and I am not going to manufacture a struggle
around it.

**But the ticket took four runs to go green, because two further defects sat behind it.** That is the
substance of what went wrong:

- **Attempt 1 → run 2 FAILED at `clickHome`, unrelated to my change.** An intermittent Edge
  permission popup. This was *not* caused by the ER filter — it is pre-existing flakiness that
  happened to fire. **The correcting input was Jay**, who remembered a handler had already been
  written for exactly this popup. A grep for `handleAccessOtherAppsPopup|Access other apps` found it
  in `PartMaster.script:216` (added under TESTAUTOMA-7947) *plus* a broken inline copy in
  `clickHome`. Without Jay's prompt I would likely have written a new one rather than found the
  existing pattern.

- **Attempt 2 → run 3 FAILED with an empty PartNum, and this one *was* caused by my fix.** The ER
  filter selected a different part (`E1827B` instead of `INR-MIIM-002`), which was shorter-named and
  slower to render — exposing latent fragility that had been getting away with it for as long as the
  selected part happened to be long-named.

- **The dead end / false signal.** The failure message in run 3 was
  `Validating BOM Loader Process - Actual Value (False) is NOT equal to Expected Value (True) - FAIL`
  — **byte-identical to the original Spirent failure**. That message strongly implies "the BOM load
  was rejected", which is what it meant in run 1 and *not* what it meant in run 3. Jay's question
  ("Is this something new... completely out of context?") shows the same message misdirected him too.
  The line that actually broke it open was `9:09:16 AM typetext` with an empty payload — the script
  typed nothing into Parent Assembly Name.

- **A hypothesis I formed and then discarded on evidence.** After grepping `tripleClick`, I found the
  coordinate `[137,172]` was shared with sibling test `TESTAUTOMA_2878_001`, and I began reasoning
  about the coordinate in isolation. I stated in chat *"my first hypothesis was wrong, so I opened
  the actual captures rather than guessing"* and *"That changes the diagnosis completely."* Reading
  `21_07_2026_09_08_18.png` showed something I had not anticipated at all: the part page **was not on
  screen** — the Approvals list with 6W panel was still displayed. That converted a one-cause theory
  (bad x coordinate) into a two-cause one (missing wait **and** bad x coordinate).
  > `UNCERTAIN — the exact content of that first hypothesis.` I never wrote it out in chat before
  > checking the screenshots, so I can only report that I characterised it as wrong, and what the
  > screenshots corrected it to.

- **A smaller error, self-corrected, no impact on the fix.** I ran a case-sensitive Grep for
  `TopLeftQuadrant|TopLeft` against `config.script`, got no matches, and told Jay *"`TopLeftQuadrant`
  doesn't exist in config."* That was wrong — reading the file showed `topLeftQuadrant:[0,0,1920/2,1080/2]`
  at `config.script:24` (lowercase leading `t`). SenseTalk property access is case-insensitive here,
  so the existing code was fine. Lesson: do not conclude "missing" from a case-sensitive grep.

### Knowledge source

`tribal` + `sibling_scripts` + `app_behaviour` (all three genuinely required; different ones per defect).

- **`tribal` — the decisive fact, present nowhere in the codebase:** that `Engineering Responsibility`
  `SP1`–`SP4` denotes **Spirent**, and that Spirent parts carry a server-side check trigger that
  blocks BOM/attribute updates. This came from the Jira description and the error screenshot. No file
  in the repo states it. The codebase only ever encodes the *converse* (use `02`/`00`), never why.
- **`sibling_scripts` — how to express the filter:** the exact criterion form
  `["02","Engineering Responsibility"]` and the fact that `02`/`00` are the accepted non-Spirent
  codes was recovered from `MQLQueries.json` (`attribute[Engineering Responsibility]==02 || ==00`)
  and from sibling tests (`TESTAUTOMA_2936_031`, `TESTAUTOMA_6413_006`, `TESTAUTOMA_2931_009`,
  `TESTAUTOMA_6214_021`, `TESTAUTOMA_4086_RT001`, `TESTAUTOMA_4081_RT002`).
- **`sibling_scripts` — for defect 2:** the pre-existing `handleAccessOtherAppsPopup` in
  `PartMaster.script`, which is suite-local and therefore *not callable* from EngineeringCentral.
- **`app_behaviour` — for defect 3:** that Enovia part names vary in rendered width, that the part
  page header lags the 6W-panel close, and that a blank Parent Assembly Name raises a JS alert rather
  than a distinct log error. Only obtainable from screenshots of a real run.

### Fixable component

`script` (all three defects were script-side; no test data, environment or Enovia change was needed).

### Failure family

`multi_cause: true`

- **Defect 1 — `test_data`.** The script selects its own fixture via search; the criteria were too
  loose and admitted an unusable part. Closest genuine fit of the twelve.
- **Defect 2 — `missing_wait`.** A single pre-flight check with no re-check/retry around an
  intermittent overlay.
- **Defect 3 — `missing_wait`** (no wait for the part page to render) **+ see proposed below.**

Two things did not fit any of the twelve, and I am not forcing them:

- `hardcoded_coordinate_brittleness` — `tripleClick[137,172]` is a fixed *click* coordinate
  calibrated to one specimen's rendered text width. `search_rectangle` is the nearest bucket but is
  materially different: nothing about a search rectangle was wrong, and tagging it that way would
  train an agent to go adjust rectangles when the correct remedy is to anchor the click to a located
  element. This pattern recurs (`tripleClick[106,75]`, `tripleClick(149,72)` elsewhere in the repo),
  so it deserves its own family.
- `silent_parameter_typo` — `watiFor:25` instead of `waitFor:25`. A misspelled *named
  parameter* that neither errors nor warns; the call silently runs without the intended option.
  `handler_name_mismatch` is about handler names, not parameter names, and would mis-route the fix.

### Handlers involved

```
test → commonEnovia.searchEnovia            (CommonEnovia.script:165)
test → commonEnovia.clickHome               (CommonEnovia.script:702 pre-fix / :723 post-fix) → common.navigate
test → commonEnovia.tripleClick             (CommonEnovia.script:1278)
test → EngineeringCentral.enterBOMLoaderValues (EngineeringCentral.script:3107)
           → commonEnovia.assertWithScreenshot   (assertion at EngineeringCentral.script:3167)
```
Also relevant but **not reachable from this suite**: `PartMaster.handleAccessOtherAppsPopup`
(`PartMaster.script:216`).

**Handlers whose behaviour was surprising or misdescribing:**
- **`enterBOMLoaderValues` — the big one.** Its assertion message is a fixed string,
  `"Validating BOM Loader Process"`, emitted whenever the success banner is absent. It reported
  *identically* for two completely unrelated root causes (server-side Spirent trigger rejection; and
  a blank Parent Assembly Name never submitted). The message actively implies the load was attempted
  and rejected. Treat it as "the success banner was not found", nothing more.
- **`clickHome`** silently contained popup-handling logic that its name does not advertise — a caller
  reading the test would not know the popup was already (badly) handled inside it.
- **`openFirstPartInSameWindow`** (`CommonEnovia.script:1581`) exists and reads the first part number
  robustly via `readtext` + `validCharacters`, and is sitting **commented out** at line 39 of the
  test in favour of the brittle `tripleClick`. Not used in the fix; noted as a possible better path.

### Outcome

**PASSED — validated by an actual run.** Run 7/21/26 09:19:50–09:30:52 on SUT `156.140.6.130`,
env `bst`:
```
9:27:15 AM  Log  Parent part selected for BOM Loader: E1827B
9:28:19 AM  Validating BOM Loader Process - Actual Value (True) is equal to Expected Value (True) - PASS
9:29:48 AM  Validating BOM Loader Process - Actual Value (True) is equal to Expected Value (True) - PASS
9:30:52 AM  Validating the BOM Loaders are removed - Actual Value (False) is equal to Expected Value (False) - PASS
9:30:52 AM  SUCCESS  Execution Time 0:11:02
EndTestCase (Duration:"662.304", Errors:"0", Exceptions:"31", Successes:"70", Warnings:"0")
```
Full run through Step 12 including `removeAllBOMLoadedParts` cleanup. The Spirent trigger error did
not recur; the part selected was `E1827B`, not a Spirent part.

All three fixes were confirmed exercised at runtime (not silently skipped):
`9:25:50 typetext 02` (filter actually entered), `9:24:23 Access other apps popup found` →
`9:24:24 click Allow`, `9:27:12 ImageFound (TEXT:"Maturity State") found at (398, 178)` →
`9:27:13 click at (55, 178)`.

### What would have made this faster

1. **Put the Spirent/ER mapping in `context.md`.** One line would have removed the entire round-1
   investigation: *"Engineering Responsibility `00`/`02` = standard non-Spirent orgs; `SP1`–`SP4` =
   Spirent. Spirent parts have a server-side check trigger that blocks BOM/attribute updates. Any
   test that searches for a part and then modifies it must filter `["02","Engineering Responsibility"]`."*
2. **Record that `Validating BOM Loader Process ... FAIL` is a non-specific message.** It means only
   "success banner not found". An agent seeing it must check the Parent Assembly Name was actually
   populated *before* concluding the load was rejected. This single fact would have collapsed the
   run-3 dead end.
3. **Fetch the `Results/*.png` captures immediately when a coordinate-based step misbehaves.** The
   run's own screenshots are on local disk and are ground truth for what was on screen. Reading
   `21_07_2026_09_08_18.png` overturned my hypothesis in one step; reasoning about the coordinate
   without it was heading somewhere wrong.
4. **After changing a data-selection filter, expect downstream coordinate/timing assumptions to
   break.** Narrowing a search changes *which* specimen is selected, and hardcoded geometry is often
   calibrated to the old one. A pre-emptive scan for hardcoded coordinates in the same test would
   have caught defect 3 before the run.
5. **When an intermittent browser popup is suspected, grep the whole repo for an existing handler
   first** — suite-local helpers (e.g. in `PartMaster.script`) will not be callable but show the
   established pattern and rectangle to reuse.
6. **Do not conclude "identifier missing" from a case-sensitive grep** in this codebase; read the
   file.

### Notes

- **The three failures were sequential, not simultaneous.** Each run revealed exactly one. An agent
  should expect that fixing the filed defect can *unmask* others, and should not treat a second
  failure as evidence the first fix was wrong. Here fix 1 was verified correct even though the run
  it produced still failed.
- **Failure 2 was not caused by the fix; failure 3 was.** Worth distinguishing: run 2's popup was
  pre-existing flakiness coinciding; run 3's empty PartNum was a genuine consequence of selecting a
  different part.
- **The SUT changed mid-investigation**, from `156.140.21.48` (run 1) to `156.140.6.130` (runs 2–4).
  This did not appear to matter but was not controlled for.
- **`CommonEnovia.script` is shared by every test that logs in.** The `clickHome` change has repo-wide
  blast radius. It is strictly more permissive (identical failure message and screenshot name on
  genuine failures, one extra retry) but reviewers were flagged.
- **Known-latent, deliberately not fixed:** `TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed.script`
  is the sibling BOM-Loader test and carries **all three** defects — same unfiltered Preliminary
  search, same `tripleClick[137,172]` at line 47. It passes only by luck of which part it selects.
  Jay was offered the port and had not answered as of the end of this conversation.
- **Committed** as `92bf151d` on branch `fix/Testautoma-8814`, pushed to Bitbucket; PR to be raised
  by Jay. Only the two fix files were staged; 18 pre-existing modified `SuiteInfo` files and
  `EnoviaCommon.suite/SearchObjects/icons/okButton/okButton11.searchobject` were deliberately left
  unstaged as unrelated. Not merged to `Testing_Mar10`.
- **`config().SUT.topLeftQuadrant` = `[0,0,1920/2,1080/2]`** (`config.script:24`) is the rectangle the
  popup handler searches. The popup renders top-**left** despite being described as top-right in
  conversation.
