## TESTAUTOMA-8943

**Failing test:** TESTAUTOMA_4336_RT001_MEPForPartWithMSMFlagYesDMS.script
**Suite:** BoundaryApps.suite
**DAI runid:** 35365 (initial failing run, 2026-06-29, SUT 156.140.21.48) and 36469 (final run analysed, 2026-07-20, SUT 156.140.6.130). The intermediate runs between these two were run locally by Jay from the Eggplant GUI (results written to `Enovia/BoundaryApps.suite/Results/`) and carried no runid in the logs supplied.

Note on ticket identity: the Jira ticket is TESTAUTOMA-8943; its "Test Case ID" field is TESTAUTOMA_4336, which is the script that fails. Branch in use was `fix/Testautoma-8943`.

### Symptom

Jira ticket title and description (verbatim from the ticket screenshot):
```
(TEXT:"OK") Unable to Find Image (TEXT:"OK"). Text not found
Ok button color has changed which is causing OCR Issue
```
Components: Change_Scope, ENOVIA-Automation. Labels: Non-Regression, Phase3.

The DAI log supplied with the ticket (runid 35365) did **not** show that error. It died with:
```
Text 'Create New MEP' has not disappeared. - (no reason given)  in Handler/Function named waitForTextToDisappear
Failed Due to line 661 of script): Text 'Create New MEP' has not disappeared.
Technical Error: Runtime Error at line 14 (line 691 of script)
Testcase failed in : ["ScripName : testautoma_4336_rt001_mepforpartwithmsmflagyesdms","HandlerName1 : createnewmanufacturerequivalent","HandlerName2 : opencreatedmep"]
```
Step: after filling the Create New MEP panel (Part Name + Manufacturer "Keysight Technologies") and clicking the panel's OK button, while waiting for the panel to close.

Preceding that, the log showed the OK click reported as *successful*:
```
07:39:54  click  okBlue  at (1794, 1020)
```
then 30 s of `found at (1728, 155)` for `(TEXT:"Create New MEP")` with `Waiting for text 'Create New MEP' to disappear...` repeated, then the throw.

### Evidence used

**Decisive:**
- **The error screenshot supplied with the ticket.** This was genuinely necessary and the log alone would *not* have been enough. The log showed a successful click followed by a panel that would not close, with no error explaining why. The screenshot showed the reason: a browser-native modal alert `3dxspacebst.supplychain.keysight.com says / Warning: / Object Find Limit (1) Reached` sitting over the page. Nothing in the log named that alert.
- **Jay's later manual walkthrough screenshots** (taken by hand in Enovia, not from a test run). Two things came only from these:
  1. The Manufacturer Equivalents find icon sits at approximately (1893, 190) — which *disproved* my search-rectangle hypothesis (see "What was got wrong first").
  2. The Equivalents table listed MEPDMS38192, MEPDMS81841, MEPDMS66615 — proving every prior run *had* created its MEP, which disproved my "the OK click is being swallowed" reading and exposed a duplicate-MEP risk in a fix I had already written.
- **The panel title in the screenshots**, rendered as `PNTX100-60029|Create New M...` — elided. This was the actual root cause of the reported failure and was visible only in the screenshots, never in the log.
- **Log timestamps across successive runs**, used to establish that the alert appears several seconds *after* the triggering action (click 12:04:41 → alert visible 12:04:45; click 12:19:25 → alert missed by checks at 12:19:26/27; click 9:32:13 → alert logged 9:32:19).

**From Jay's own head, not in any file or log:**
- "I think the popup came a little late, not sure though." This was correct and was the key that unblocked the run that eventually passed.
- "if script is trying to match with some ok button image, then check by going to the location whether that image is similar to that on screen or not" — prompted an explicit verification of the `icons/okButton` asset rather than an assumption.
- The push-back "why didnt you understood it from the description mentioned in the jira ticket screenshot attached at the beginning" — this was the correction that made me stop using the OK button as a *presence signal*.

**Turned out irrelevant / misleading:**
- The Jira ticket's literal error string `(TEXT:"OK") Unable to Find Image`. The specific line that produced it had already been fixed in the repo before this work started (see Notes). Treating it as "already fixed, move on" was a mistake — the ticket's *underlying* point (this button is unreliable to identify) was the thing that later cost three failed runs.
- The `Object Find Limit (1) Reached` message content. I initially suspected it was truncating the Equivalents table to one row. It was not — the June run showed the same warning with six rows loaded. It is noise from a lookup; only its modality matters.

**Source files read, in order:**
1. `context.md` (supplied)
2. `Enovia/BoundaryApps.suite/Scripts/Testcases/TESTAUTOMA_4336_RT001_MEPForPartWithMSMFlagYesDMS.script`
3. `Enovia/MaterialsComplianceCentral.suite/Scripts/MaterialsComplianceCentral.script` — `openCreatedMEP` (from line 785)
4. `Enovia/MaterialsComplianceCentral.suite/Scripts/MaterialsComplianceCentral.script` — `createNewManufacturerEquivalent` (from line 64)
5. `Enovia/Common.suite/Scripts/common.script` — `waitForTextToDisappear` (line 1489)
6. `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script` — `popUpWarning` (line 1143)
7. `Enovia/EngineeringCentral.suite/Scripts/EngineeringCentral.script` — `findLimitReachedPopup` (line 1231), found by grepping for "find limit"
8. Image assets `Enovia/EnoviaCommon.suite/Images/icons/okButton/okButton.png` and `okButton12.png` (viewed directly)
9. `Enovia/EnoviaCommon.suite/Scripts/ConfigEnovia.script` (grep for rect/wait keys)
10. `Enovia/Common.suite/Scripts/common.script` — `scrollTo` (line 737), after run A failed
11. `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script` — `searchEnovia` (line 165 onward), after run A failed
12. `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script` — `findAnyItemWithFindIcon` (line 1940), after run B failed
13. `Enovia/EnoviaCommon.suite/Images/icon_MagnifyingSearch.png` (viewed directly)

### Root cause

Three independent defects on the same code path. They surfaced one after another, each hidden behind the previous.

**1. Enovia raises a browser-native `alert()` mid-flow, and the framework had no handling for it at all.**
Selecting the Manufacturer in the Create New MEP panel causes Enovia to raise `Object Find Limit (1) Reached` as a browser-native alert. A native alert is modal to the tab and **blocks the page's own JavaScript**, so the create flow is frozen mid-submit until someone clicks OK. Additionally Edge **dims the page** behind the dialog, which makes image matches against page content (specifically `icons/okBlue`) stop matching entirely. `createNewManufacturerEquivalent` had no code path that acknowledged this dialog existed.

**2. `openCreatedMEP` waited on a panel title that Enovia elides.**
`MaterialsComplianceCentral.script:791` (pre-fix):
```sensetalk
common.waitForTextToDisappear "Create New MEP", configEnovia().searchRectangles.rightPane, 30
```
The panel title renders as `<PartName>|Create New MEP` — but for a long part name Enovia truncates it to e.g. `PNTX100-60029|Create New M...`. The literal string "Create New MEP" is then never on screen. Combined with `common.waitForTextToDisappear` (`common.script:1489`), which never verifies the text was present to begin with, this produces a **silent false pass**: it logs `Text 'Create New MEP' has disappeared.` when the panel is still wide open. In the original failing run the part was `1821-5513` (short, title rendered in full) so the wait worked and failed honestly; in later runs the part was `PNTX100-60029` (long, title elided) so the wait passed falsely and the failure moved downstream to `findAnyItemWithFindIcon`, which then timed out for 60 s because the still-open panel was covering the find icon it needed.

**3. `common.scrollTo` only ever scrolls one direction.**
`common.script:737`. `searchEnovia` calls it at `CommonEnovia.script:350` without a `direction` argument, so it always scrolls **down**. If the target label happens to render *above* the viewport, scrolling down walks away from it and it can never be found; after 10 iterations it does `Error "Cannot find"&&toFind,yes` / `Exit all`. The advanced-search criteria panel does not render at a stable scroll position between runs, which makes this intermittent. This caused run A's `Cannot find MSM Item Flag`.
**This fix was never exercised by any run** — see Outcome.

### The fix

**A. New shared handler in `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script`, inserted immediately after `popUpWarning` (final form):**
```sensetalk
to handle dismissNativeAlert waitToAppear, popupRectangle, attempts
	try
		if waitToAppear is empty then put 0 into waitToAppear
		if popupRectangle is empty then put configEnovia().SearchRectangles.PopUpWarning into popupRectangle
		if attempts is empty then put 5 into attempts
		repeat attempts times
			if not commonEnovia.waitForNativeAlert(popupRectangle, waitToAppear)
				exit repeat
			end if
			Log "Dismissing alert:"&&readText(popupRectangle, dpi:144)
			if ImageFound(image:"icons/okButton", searchRectangle:popupRectangle, waitFor:5)
				click FoundImageLocation()
				//Step off the button - a hovered OK repaints and would confuse the next image search
				MoveTo [960,780]
			else
				//The dialog holds keyboard focus with OK as its default button - Enter activates it
				//without having to locate a button whose rendering shifts with theme and hover
				typeText returnKey
			end if
			wait 2
		end repeat
		if commonEnovia.nativeAlertIsOnScreen(popupRectangle)
			common.error "Alert is still on screen after"&&attempts&&"attempts to dismiss it",yes
		end if
	Catch theException
		"exceptionHandling".failedHandlerNavigation(callStack())
		"exceptionHandling".errorCapture theException
	End try
end dismissNativeAlert

to handle waitForNativeAlert popupRectangle, waitToAppear
	try
		put the time into startTime
		repeat
			if commonEnovia.nativeAlertIsOnScreen(popupRectangle)
				return true
			end if
			if (the time - startTime) >= waitToAppear
				return false
			end if
			wait 1
		end repeat
	Catch theException
		return false
	End try
end waitForNativeAlert

to handle nativeAlertIsOnScreen popupRectangle:configEnovia().SearchRectangles.PopUpWarning
	try
		return readText(popupRectangle, dpi:144) contains "says"
	Catch theException
		return false
	End try
end nativeAlertIsOnScreen
```

**B. `MaterialsComplianceCentral.script`, `createNewManufacturerEquivalent` — added before the submit click (new lines 123–125):**
```sensetalk
		//Picking the Manufacturer raises a native "Object Find Limit (n) Reached" alert. It is modal, so it
		//swallows the OK click below if it is left on screen.
		commonEnovia.dismissNativeAlert
		//Click the OK button to submit a part
		click imageName:"icons/okBlue", waitFor:configEnovia().general.MidWait, searchRectangle:common.commonScreenPart(BottomRightQuadrant)
```

**C. `MaterialsComplianceCentral.script`, `createNewManufacturerEquivalent` else-branch — replaced the plain `CommonEnovia.waitForLoading` lead-in with:**
```sensetalk
			commonEnovia.dismissNativeAlert configEnovia().general.minWait
			put the time into panelCloseStart
			repeat while ImageFound(text:"Part Name", searchRectangle:configEnovia().searchRectangles.createNewMEP, DPI:144)
				if (the time - panelCloseStart) > 15
					exit repeat
				end if
				wait 2
				commonEnovia.dismissNativeAlert
			end repeat
			if ImageFound(text:"Part Name", searchRectangle:configEnovia().searchRectangles.createNewMEP, DPI:144)
				click imageName:"icons/okBlue", waitFor:configEnovia().general.MidWait, searchRectangle:common.commonScreenPart(BottomRightQuadrant)
				commonEnovia.dismissNativeAlert configEnovia().general.minWait
			end if
```

**D. `MaterialsComplianceCentral.script`, `openCreatedMEP`:**
```sensetalk
// before
		//wait 5
		common.waitForTextToDisappear "Create New MEP", configEnovia().searchRectangles.rightPane, 30
		set the TextStyle to {DPI:144}

// after
		//wait 5
		set the TextStyle to {DPI:144}
		common.waitForTextToDisappear "Part Name", configEnovia().searchRectangles.createNewMEP, 30
```

**E. `Enovia/Common.suite/Scripts/common.script`, `scrollTo` OCR branch — reverse scan before giving up:**
```sensetalk
// before
			if repeatindex() > 10 then
				Error "Cannot find"&&toFind,yes
				Exit all

// after
			if repeatindex() > 10 then
				if direction is not "horizontal"
					repeat 22 times
						if direction is "up" then
							ScrollWheelDown 6
						else
							ScrollWheelUp 6
						end if
						wait 3
						if imagefound(waitfor:2,text:toFindImage,searchRectangle:SR, ignoreNewlines:on, ignorespaces:on,dpi:144)
							exit repeat
						end if
					end repeat
				end if
				if not imagefound(waitfor:2,text:toFindImage,searchRectangle:SR, ignoreNewlines:on, ignorespaces:on,dpi:144)
					Error "Cannot find"&&toFind,yes
					Exit all
				end if
```

### What was got wrong first

This took **six runs** and the working version was the **fifth** distinct attempt. The path was not clean.

**Attempt 1 — partially right, but I dismissed the ticket.**
First hypothesis: the native alert is modal and swallowed the OK click. That half was correct. But I also concluded the Jira's stated symptom was "already fixed" — because `MaterialsComplianceCentral.script:124` still carries the commented-out `//click text:"OK"` replaced on line 125 by `click imageName:"icons/okBlue"`. That was literally true and strategically wrong. I then wrote my new alert-detection code using `ImageFound(image:"icons/okButton")` as the **presence check** for the dialog — i.e. I used the exact button the ticket warned was unreliable, as my signal. That decision cost runs 3 and 4.

**Run A (7/16 23:12) — my fix never ran.** Failed 4 minutes earlier at `Cannot find MSM Item Flag` in `searchEnovia`. This was a genuine second bug (`scrollTo` one-direction), diagnosed by comparing label Y-positions across two runs (Is Last Revision at y=513 vs y=913; MSM Item Flag at y=235 with zero scrolling in the passing run). Fixed, but note: **this fix has still never been exercised** — in every subsequent run the label happened to be found without needing the reverse scan.

**Run B (7/16 23:33) — first dead end.** Alert dismissed correctly for the first time. But then `Icon Search not found in the screen` — 60 s timeout on `icon_MagnifyingSearch` in `findAnyItemWithFindIcon`. My hypothesis: the search rectangle is wrong, because `openCreatedMEP` passes `rightPane` = `[1400,115,1920,1040]` and I believed the Equivalents toolbar was on the left at x≈230–730. **This was wrong.** Jay's manual screenshot showed the find icon at ≈(1893, 190) — comfortably inside `rightPane`. The rectangle had never been wrong.

**What corrected it:** the elided panel title `PNTX100-60029|Create New M...`, visible in Jay's screenshots. The panel had never closed; it was covering the icon. `waitForTextToDisappear "Create New MEP"` had returned a **false pass** because the literal string was not on screen to begin with. I had spent a message and a half on the wrong rectangle.

**Second dead end, in the same stretch:** I asserted "the MEP has never actually been created on any of these runs" and built a re-click of okBlue on that assumption. Jay's Equivalents screenshot then showed MEPDMS38192, MEPDMS81841 and MEPDMS66615 all present — every run *had* created its MEP from a single click. My re-click was a live duplicate-creation risk. It was subsequently gated behind a 15 s panel-close wait so it only fires if the panel is genuinely still open.

**Run C (7/16 23:58) — the okButton false negative.** Log:
```
12:04:45  ImageFound icons/okButton found at (1148, 227)
12:04:45  click at (1148, 227)
12:04:55  ImageFound icons/okButton  Unable to Find Image
12:05:03  ImageFound (TEXT:"Part Name") found at (1616, 247)
12:06:00  Exception icons/okBlue  No Image Found On Screen: "icons/okBlue"
```
The button read as *gone* while Jay's screenshot showed the alert still up at 12:06:10. Cause: after clicking, the pointer rests on the button, Edge repaints it in its hover state, and the image stops matching. My handler concluded "alert cleared" and moved on. This is exactly the failure mode the Jira ticket describes, arrived at independently — which is what Jay called out.

**Run D (7/17 00:11) — I over-corrected into a race.** I replaced the OK-button presence check with `readText(...) contains "says"` on the dialog heading. Sound in principle, but `readText` is an **instantaneous** read with no `waitFor`, and the alert arrives seconds after the click:
```
12:19:25  click icons/okBlue at (1794, 1020)
12:19:26  readtext (709,6,1212,300)
12:19:27  readtext (709,6,1212,300)
12:19:28  ImageFound (TEXT:"Part Name") found at (1616, 247)
```
Two glances, two seconds, nothing there, gave up. Jay's "I think the popup came a little late, not sure though" was correct and named this before I did.

**Run E (7/17 00:37) — my own syntax bug.**
```
Technical Error: Runtime Error at line 3 (line 1184 of script): STInvalidNumber - Value is not a number: '{waitToAppear:10}'
```
I called `commonEnovia.dismissNativeAlert waitToAppear:configEnovia().general.minWait`. SenseTalk does **not** bind `name:value` call arguments to same-named parameters — it bundles them into a property list and passes it as the **first positional argument**. `{waitToAppear:10}` landed in `attempts`, and `repeat attempts times` threw immediately. The entire wait mechanism from run D's fix never executed. Handler was rewritten to plain positional parameters with defaults assigned in the body.

**Run F (7/17 09:25) — PASSED.** `Errors: 0, Warnings: 0, SUCCESS`. The alert fired **twice**; the first was cleared by the image match on `icons/okButton`, the second missed the image and was cleared by the `typeText returnKey` fallback (`9:32:30  ImageFound icons/okButton Unable to Find Image` → `9:32:30  typetext [returnKey]`) — the first time that fallback was ever exercised. The re-click of okBlue did not fire; the panel closed on its own within the wait window. MQL returned the expected `AgAMLSuccessLogObj` row.

**Summary of the false signals that cost the most time:**
1. The ticket's literal error string had already been patched, so I filed the whole ticket as stale instead of reading its general claim. Cost: two runs.
2. A `waitForTextToDisappear` that logs success for text that was never present. Cost: one run plus a wrong rectangle hypothesis.
3. An image match that silently false-negatives when the cursor rests on the matched element. Cost: one run.
4. Assuming `readText` waits. Cost: one run.

### Knowledge source

Primary: **`app_behaviour`** — the decisive facts existed in no file in this repo:
- Enovia raises `Object Find Limit (n) Reached` as a **browser-native** `alert()`, not an in-page banner.
- It is raised by **selecting the Manufacturer**, and arrives roughly **4–10 seconds after** the triggering action, not synchronously.
- A native alert **blocks the page's own JavaScript**, so the create flow freezes mid-submit and the panel stays open until OK is clicked; afterwards the flow resumes and the panel closes by itself.
- Edge **dims the page** behind a native dialog, so image matches against page content (`icons/okBlue`) fail while it is up.
- Edge repaints a button in its hover state, so an image match on a just-clicked button false-negatives.
- The native dialog holds keyboard focus with **OK as its default button**, so `returnKey` activates it.
- Enovia **elides the create-panel title** for long part names (`PNTX100-60029|Create New M...`).
- Every Edge native dialog carries a `"<host> says"` heading regardless of message or theme.

Also required (secondary, since the "one of" list cannot express this ticket honestly):
- **`sibling_scripts`** — `popUpWarning` (CommonEnovia.script:1143) already used `click imageName:"icons/okButton"` against this same dialog, which is what proved the image asset is sound; and `findLimitReachedPopup` (EngineeringCentral.script:1231) showed a prior, broken attempt at the same problem.
- **`tribal`** — SenseTalk's calling convention: `name:value` at a call site becomes a property list in the first positional parameter, it does **not** bind by name. Nothing in the repo states this and it produced a hard runtime error.

### Fixable component

`script` — for the three defects diagnosed and fixed.

Two unresolved items are **not** script issues and should not be treated as such:
- The `Object Find Limit (1)` setting on the `digi3dx` account raises this alert on every MEP operation. That is `environment` and should be fixed at source rather than worked around indefinitely.
- The final run's failure (see Outcome) is either timing or `application_bug`; undetermined.

### Failure family

`multi_cause: true`

- `missing_wait` — the dominant one, three separate instances: no wait for the late-arriving alert; no wait for the panel to close after the alert clears; `readText` used as if it polled.
- `text_label` — `"Create New MEP"` matched against an elided `Create New M...`.
- `image_staleness` — applies with a caveat. The stored `icons/okButton` asset is **not** stale; it matched correctly twice in the same logs. The failure is that an image match false-negatives under transient render states (hover repaint, page dimming). If the family is meant strictly as "asset no longer resembles the UI", this is a poor fit and the honest tag would be `PROPOSED: transient_render_state` — an image that matches normally but not while hovered, dimmed, or otherwise mid-repaint.

Also present but not the reported failure: `silent_exception_swallowing` in spirit — `common.waitForTextToDisappear` reports success for text that was never present. It swallows no exception, so the tag is imprecise; `PROPOSED: false_pass_assertion` would describe it better.

### Handlers involved

Original reported failure:
```
TESTAUTOMA_4336_RT001_MEPForPartWithMSMFlagYesDMS.script
  → MaterialsComplianceCentral.createNewManufacturerEquivalent   (MaterialsComplianceCentral.script:64)
    → openCreatedMEP                                             (MaterialsComplianceCentral.script:792)
      → common.waitForTextToDisappear                            (common.script:1489)
```
Later failure in the same chain:
```
      → CommonEnovia.findAnyItemWithFindIcon                     (CommonEnovia.script:1940)
```
Run A failure (separate defect):
```
TESTAUTOMA_4336_... → commonEnovia.searchEnovia (CommonEnovia.script:165)
                      → common.scrollTo         (common.script:737, called from CommonEnovia.script:350)
```

**Handlers whose behaviour was surprising or whose name misdescribes them:**
- `common.waitForTextToDisappear` — does not verify the text was ever present. If the string is absent from the start it logs `Text '<x>' has disappeared.` and returns success. The name implies it waits for a transition; it only ever asserts absence.
- `common.scrollTo` — takes a `direction` but has no bidirectional mode. Most callers omit `direction`, silently getting down-only. The image-matching branch (lines 741–753) has the **same** down-only defect and was deliberately left untouched.
- `commonEnovia.popUpWarning` — named for an in-page warning, but is used against the browser-native dialog too, and already matched it by image rather than OCR.
- `findLimitReachedPopup` (EngineeringCentral.script:1231) — handles this exact alert but detects it with `imagefound(text:"OK", ...)`, i.e. the OCR path the ticket says is broken, wrapped in an `if` so an OCR miss **silently no-ops**. Its only caller is `createRevision` (line ~1207). A background task was spawned to migrate it onto `dismissNativeAlert`; **not done in this conversation**.
- `commonEnovia.dismissNativeAlert` (new) — parameters are **positional only**. Calling it with `name:value` arguments throws `STInvalidNumber`.

### Outcome

**Mixed — state precisely:**

- **PASSED, validated by a real run.** Run 7/17 09:25:47 → 09:34:36, `EndTestCase (Duration:"528.423", Errors:"0", ... Successes:"54", Warnings:"0")`, `SUCCESS`. MEP `MEPDMS33826` created, found, and the MQL check returned `AgAMLSuccessLogObj 20260716:220217:760 PNTX100-60029:MEPDMS33826`. Jay confirmed the same row visually in the Run MQL screen. No duplicate MEP.

- **Subsequent run FAILED at a different, later assertion.** Run 7/20 (runid 36469) failed with:
  ```
  MEP is not created or not found  in 3DEXPERIENCE and  transaction should be triggered for the MEP to DMS
  Technical Error: Runtime Error at line 5 (line 662 of script)
  FAILED, 1 errors, 1 warnings
  ```
  Every fixed step worked in that run: alert appeared ~10 s late and was waited out and dismissed (`14:33:57 Dismissing alert: ... Object Find Limit (1) Reached`, cleared via `icons/okButton` at 14:33:58), panel closed (`14:34:43 Text 'Part Name' has disappeared.`), find icon located at (1887, 188), `MEPDMS97157 present in the screen`. The failure is the final DMS verification: `temp query bus AgAMLSuccessLogObj * *:MEPDMS97157` returned **empty**. Jay's own manual screenshot of the Run MQL screen shows the same empty Results box for that MEP, so this is not an OCR or UI-matching problem — the `AgAMLSuccessLogObj` record genuinely did not exist.

- **`scrollTo` reverse-scan fix (E): NOT VALIDATED.** It has never been exercised. In every run after it was written, the target label was found without needing the reverse scan. Its correctness is reasoned, not demonstrated.

- **Unresolved at end of conversation:** whether the 7/20 MQL failure is timing (the `AgAMLSuccessLogObj` is produced by an asynchronous background job and may simply have been slow) or a genuine break in the AML→DMS transaction in BST. A diagnostic was requested from Jay — re-run `temp query bus AgAMLSuccessLogObj * *:MEPDMS97157` a few minutes later — and **no answer was received before the conversation ended**. No retry loop was added, deliberately: adding a wait when the transaction is genuinely broken would convert a true failure into a false pass.

### What would have made this faster

1. **Read a Jira ticket as a claim about a component, not a claim about one line.** The ticket said the OK button's rendering is unreliable. I verified that the one call site producing that literal string was already patched, declared the ticket stale, and then used that same button as my presence signal. Rule for `context.md`: *if a ticket says an element is unreliable to identify, do not use that element as a state signal anywhere, even if the specific reported call site is already fixed.*
2. **`readText` does not wait.** It is an instantaneous single read with no `waitFor` parameter. Any presence check built on it races the UI. Use a polling loop.
3. **SenseTalk has no keyword arguments at the call site.** `handler name:value` passes a property list as the first positional parameter. This belongs in `context.md` — it produced a hard `STInvalidNumber` crash and cost a full run.
4. **Enovia elides panel titles for long object names.** Never key a wait or a presence check on a panel *title*; key it on a field label inside the panel (`Part Name` here). Corollary: a distinctive short-vs-long test object can make this bug appear and disappear between runs.
5. **`common.waitForTextToDisappear` gives a false pass for text that was never present.** Either fix the handler to assert presence first, or treat every use of it as suspect when the following step fails.
6. **Ask "did the object actually get created?" before theorising about swallowed clicks.** One look at the Equivalents tab would have killed the "click swallowed" theory instantly and prevented me writing a duplicate-creation risk into the fix.
7. **Get the *right* error screenshot early.** I asked for `errorScreen ...png` twice and received the pre-submit capture instead; what finally cracked it was Jay manually walking the flow by hand. For a "clicked successfully but nothing happened" symptom, the screenshot from the moment of failure is not optional — the log cannot show a modal dialog.
8. **A native browser dialog is a distinct failure class from an in-page popup.** It blocks page JS, dims the page (so unrelated image matches start failing), and holds keyboard focus. `context.md` should carry this as its own category with the `"<host> says"` heading as the reliable detector and `returnKey` as the reliable dismissal.

### Notes

- **The Jira's reported symptom was already fixed before this work began.** `MaterialsComplianceCentral.script:124` retains the commented-out `//click text:"OK", waitFor:configEnovia().general.MidWait, searchRectangle:configEnovia().searchRectangles.createNewMEP` and line 125 does `click imageName:"icons/okBlue", ...`. Someone had already migrated that one call from OCR to an image match. The test then failed at the *next* obstacle, which is what the supplied log shows.
- **The `icons/okButton` image asset is sound.** Verified by direct inspection and, more usefully, by its own success in the logs: `12:18:43 click icons/okButton at (1148, 173)` dismissing "Validation Method not defined", and `9:32:20` / `14:33:58` at (1148, 227) dismissing the find-limit alert. Do not churn this asset. The OCR fallback path in `dismissNativeAlert` uses `contrast:on` + `LowResolutionMode` but in practice never fired; the `returnKey` fallback is what actually caught the case the image missed.
- **`Object Find Limit (1) Reached` does not truncate the results table.** Initially suspected. Disproved: the June run showed six MEP rows with the same warning present. It is noise from an internal lookup; only its modality matters. Nonetheless, a find limit of **1** on the `digi3dx` account is itself suspicious (the run is tagged `jira_project_name: "Enovia_BST_Refresh"`, so it may be a BST-refresh artefact) and is worth raising with the platform team — fixing it at source removes this alert from every MEP operation across the suite.
- **Test data accumulation:** each passing run leaves a new MEP on part `PNTX100-60029` in BST. Known at end of conversation: MEPDMS38192, MEPDMS81841, MEPDMS66615, MEPDMS33826, MEPDMS97157. Worth periodic cleanup.
- **`(TEXT:"Part Name") Unable to Find Image` lines in a passing log are expected, not errors.** They are the panel-close polling loop confirming the panel has gone; `ImageFound` logs every check including negative ones. Jay flagged these as a possible problem mid-run — they are not. The loop terminates with `Text 'Part Name' has disappeared.`
- **Unrelated noise seen in run 36469, did not cause failure:** `Unable To Find Any Image On Screen "(TEXT:"Host Name")" within 50.00 seconds` (twice, during cleanup), and an `Access other apps` popup that was detected and dismissed via `Allow` by an existing handler.
- Model was switched several times mid-conversation by Jay (`/model` to fable-5, sonnet-5, opus-4-8, opus-5). Recorded only because it may explain tonal shifts across messages; it had no bearing on the diagnosis.
