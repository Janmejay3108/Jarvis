# Ticket Findings Evidence Archive

This file combines nine tickets solved manually with an AI coding assistant, extracted from their individual working sessions.

- Date: 2026-07-30
- Ticket count: 9

`NOT&#32;RECORDED` and `UNCER&#84;AIN` are meaningful evidence-gap markers; preserve them exactly in every archived ticket body.
They must never be removed, resolved, or filled in by inference.

## Table of Contents

| Ticket | Failure family/families from the source ticket |
|---|---|
| [TESTAUTOMA-7947](#testautoma-7947) | `search_rectangle`; `config_value_stale`; `environment_issue`; `PROPOSED: unhandled_popup_overlay` |
| [TESTAUTOMA-7949](#testautoma-7949) | `config_value_stale` |
| [TESTAUTOMA-8278](#testautoma-8278) | `text_label`; `environment_issue`; `PROPOSED: change_scope`; `PROPOSED: environment_flake` |
| [TESTAUTOMA-8448](#testautoma-8448) | `missing_wait`; `PROPOSED: flaky_oracle` |
| [TESTAUTOMA-8449](#testautoma-8449) | `boolean_logic_gap`; `dpi_cascade`; `environment_issue`; `test_data` |
| [TESTAUTOMA-8450](#testautoma-8450) | `boolean_logic_gap`; `environment_issue`; `test_data` |
| [TESTAUTOMA-8814](#testautoma-8814) | `test_data`; `missing_wait`; `PROPOSED: hardcoded_coordinate_brittleness`; `PROPOSED: silent_parameter_typo` |
| [TESTAUTOMA-8833](#testautoma-8833) | `test_data`; `environment_issue`; `PROPOSED: search_criteria_too_broad`; `PROPOSED: criteria_order_vs_scroll_direction` |
| [TESTAUTOMA-8943](#testautoma-8943) | `missing_wait`; `text_label`; `image_staleness`; `PROPOSED: transient_render_state`; `silent_exception_swallowing`; `PROPOSED: false_pass_assertion` |
## TESTAUTOMA-7947

**Failing test:** TESTAUTOMA_6170_PartMasterWidgetPassTest.script
**Suite:** PartMaster.suite
**DAI runid:** Two DAI runs appeared in this conversation: `31996` (eventtime 2026-05-06, the original failure attached to the ticket) and `35531` (eventtime 2026-07-13, the final failure). Five intermediate runs on 7/12/26 were pasted as local Eggplant log text with no testrunid field — runids for those are NOT RECORDED.

> **Note on ticket shape:** TESTAUTOMA-7947 is a "Change Scope" Story with an EMPTY description ("Click to add description"). It carries no script name of its own. The script under test was identified from (a) the linked issue TESTAUTOMA-6170 (status CLOSED) in the Issue Links panel and (b) the DAI log line `Executing Sensetalk snippet TestCases/TESTAUTOMA_6170_PartMasterWidgetPassTest.script`.

---

### Symptom

This ticket was not one failure. Seven runs were observed, with **five distinct failure causes** in sequence. Recording all of them, in order, because the sequence is the finding.

**Run 1 — runid 31996 (2026-05-06) — died on Step-3:**
```
Unable to Find Image (TEXT:"Physical Product"). Text not found.
"Physical Product" is not displayed on the screen.
Failed Due to line 657 of script): "Physical Product" is not displayed on the screen. - (no reason given)  in Handler/Function named clickElement
Testcase failed in : ["ScripName : testautoma_6170_partmasterwidgetpasstest","HandlerName1 : uploadpartmasternetworksharefile"]
Technical Error: Runtime Error at line 14 (line 687 of script): Failed Due to line 657 of script): "Physical Product" is not displayed on the screen. - (no reason given)  in Handler/Function named clickElement - (no reason given)
```
The lookup was attempted twice, ~2 minutes apart (10:15:21 and 10:17:23), before throwing.

**Run 2 — 7/12/26 6:32 PM (local log) — died on Step-2:**
```
Unable to Find Image (TEXT:"Create from Spreadsheet"). Text not found.   (×3)
"Create from Spreadsheet" is not displayed on the screen.
Testcase failed in : ["ScripName : testautoma_6170_partmasterwidgetpasstest","HandlerName1 : openpartmasterwidget"]
Technical Error: Runtime Error at line 5 (line 662 of script): "Create from Spreadsheet" is not displayed on the screen. - (no reason given)
```
Browser screenshot showed `DNS_PROBE_FINISHED_NXDOMAIN` for `3dxdashboard23xbst.cos.is.keysight.com`.

**Run 3 — 7/12/26 6:53 PM — died on Step-3, at the file copy:**
```
Technical Error: Runtime Error at line 10 (line 107 of script): STFileSystemException - Failed to copy file or folder C:/Enovia_PreRequisites/Part Master/Mass_Part_BOM_Upload_Template.xlsx (Error: (null))
Testcase failed in : ["ScripName : testautoma_6170_partmasterwidgetpasstest","HandlerName1 : updatedataintonetworksharedrive"]
```

**Run 4 — 7/12/26 7:40 PM — ABORTED after typing a UNC path into the file picker:**
```
typetext  \\HYB-1DYH20JTZLP\Enovia_PreRequisites\Part Master\TESTAUTOMA_6170.xlsx[return]
Exception  Searching For Image: OCR Error: Operation was aborted
```
SUT screenshot showed a Windows dialog: `Windows cannot access \\HYB-1DYH20JTZLP\Enovia_PreRequisites`.

**Run 5 — 7/12/26 9:09 PM — died after typing the IP-form UNC path:**
```
typetext  \\10.23.73.183\Enovia_PreRequisites\Part Master\TESTAUTOMA_6170.xlsx[return]
Exception  (TEXT:"import")  Unable To Find Image "(TEXT:"import")". Text not found.
Failed Due to line 973 of script): Image Not Found - ImageLocation Error - Unable To Find Image "(TEXT:"import")". Text not found.  Restricted Search Rectangle ((45,139),(1706,805))
  in Handler/Function named clickElement
"import" Text is not found on screen to perform click operation
```
Note the ~3.5-minute gap (9:15:45 → 9:19:20) between typing the path and the failure — the picker hung on the unreachable share.

**Run 6 — 7/12/26 9:30 PM — SUCCESS.** All 5 steps passed, 0 errors.

**Run 7 — runid 35531 (2026-07-13) — died on Step-2 again, NEW cause:**
```
Unable to Find Image (TEXT:"Create from Spreadsheet"). Text not found.   (×3)
"Create from Spreadsheet" is not displayed on the screen.
Testcase failed in : ["ScripName : testautoma_6170_partmasterwidgetpasstest","HandlerName1 : openpartmasterwidget"]
Technical Error: Runtime Error at line 5 (line 662 of script): "Create from Spreadsheet" is not displayed on the screen. - (no reason given)
```
Byte-identical error text to Run 2, but a completely different cause: a browser permission popup covering the widget.

---

### Evidence used

**Log lines that mattered:**
- `Failed Due to line 657 of script) ... in Handler/Function named clickElement` + `HandlerName1 : uploadpartmasternetworksharefile` — gave the exact call chain to walk. This is the single highest-value log field.
- `Executing Sensetalk snippet TestCases/TESTAUTOMA_6170_PartMasterWidgetPassTest.script` — the only reliable source of the script name (the ticket had none).
- `Restricted Search Rectangle ((45,139),(1706,805))` in Run 5 — confirmed the applied fix's rectangle was live.
- In Run 7, the log shows the popup being handled correctly at login (`found at (187, 163)` for `(TEXT:"Access other apps")` → `Access other apps popup found` → click `Allow` at (336, 228)), then NOT handled later on the dashboard tab. The contrast between the two is what localized the gap.

**The error screenshots — was each genuinely necessary?**
- **Run 1 (import screenshot): YES, necessary.** The log alone said "Physical Product" was not found. The screenshot showed the import had *succeeded* — `Imported Items (1)`, `PRD-10577464-00156939`, badge `Physical Product00156939` — proving a false negative rather than an application failure. Without it I could not have distinguished "widget failed to import" from "OCR searched the wrong region". However, the *actual fix content* came from sibling-script comparison, not from the screenshot.
- **Run 2 (DNS error page): YES, necessary and decisive.** The log's `Unable to Find Image (TEXT:"Create from Spreadsheet")` is generic; only the screenshot showed `DNS_PROBE_FINISHED_NXDOMAIN` and the dead hostname. Log alone would have been ambiguous.
- **Run 4 (Windows cannot access dialog): YES, necessary.** The log only said `OCR Error: Operation was aborted`, which names no cause.
- **Run 7 (popup screenshot): YES, necessary and decisive.** Error text was byte-identical to Run 2's; only the screenshot revealed the popup overlay. Log alone would have led straight back to the (already-fixed) URL hypothesis.
- **Run 3 (STFileSystemException): NO screenshot needed.** The log named the exact file and operation.
- **Jay's own SUT screenshot of the file picker browsing `\\EPCORPAPAGENT12\Enovia_PreRequisites\Part Master`** (showing a full file list including `TESTAUTOMA_6170` dated 6/3/2026) — this was NOT a DAI error screenshot; Jay captured it manually. It was the single piece of evidence that corrected the biggest wrong turn. See "What was got wrong first".

**Source files read, in order:**
1. `context.md` (supplied by Jay, read first)
2. Glob `**/TESTAUTOMA_6170*` → `Enovia\PartMaster.suite\Scripts\TestCases\TESTAUTOMA_6170_PartMasterWidgetPassTest.script`
3. The test script (full)
4. Grep `uploadPartMasterNetworkShareFile` in `PartMaster.script` → lines 123, 143
5. `PartMaster.script` lines 100–180
6. `common.script` lines 620–699 — **a miss**; that region holds `CaptureScreenshot`/`Success`/`Error`/`LogException`, not `clickElement`
7. Grep `to clickElement` in `common.script` → **two definitions**: lines 155 and 967
8. `common.script` lines 155–215
9. `PartMaster.script` lines 1–100 (`getSearchRect`)
10. `PartMaster.suite/Resources/PartMaster.json` (test data + URLs + paths)
11. Grep `uploadPartMasterNetworkShareFile` repo-wide → 18 call sites across 12 test scripts
12. Grep `leftHalf|rightHalf|webForm|bottomHalf` in `config.script` → `leftHalf: [-25,-10,960,1035]`

Later, per blocker:
13. `EnoviaCommon.suite/Resources/EnvUrl.json`
14. `PartMaster.script` 177–220 (`openPartMasterWidget`)
15. `git log --oneline` on `EnvUrl.json`; `git log -p -S "3dxdashboardbst.supplychain"` → commit `fd30b37a`, 2026-06-17
16. Grep `cos\.is\.keysight\.com` across `PartMaster.suite` → no matches after fix
17. `ls` of `C:\Enovia_PreRequisites\Part Master\` → empty; `find`/`git ls-files` for the template → absent from repo
18. PowerShell probes: `$env:COMPUTERNAME`, `Get-SmbShare` (none existed), `Test-Path \\EPCORPAPAGENT12\...` (False), `Test-Connection EPCORPAPAGENT12` (False), `Get-NetIPAddress`, `Find-NetRoute -RemoteIPAddress 156.140.6.130` → `10.23.73.183` on `PANGP Virtual Ethernet Adapter Secure`
19. Grep `Access other apps` in `CommonEnovia.script` → lines 705–707; read 695–719
20. Grep `TopLeftQuadrant` in `config.script` → **no match** (a miss); repo-wide grep → `common.script:18  TopLeftQuadrant:((0,0),(.5,.5))`; then `config.script` 1–40 → `topLeftQuadrant:[0,0,1920/2,1080/2]`

**What Jay supplied from his own head, present in no file:**
- *"I think the url is now changes to something like 'supplychain.keysight.com', can u check? if possible check from old git commits also to confirm"* — directed the git pickaxe search that proved blocker 2. Decisive.
- *"see sut can do that, because we are on same network via keysight's vpn"* — an assertion about SUT→laptop reachability. **This turned out not to hold in practice** and drove the dead end.
- *"i have copied the Mass_Part_BOM_Upload_Template file from the agent server to my local machine at the same path"* — resolved blocker 3.
- *"i think this 'HYB-1DYH20JTZLP' is wrong"* — Jay's hypothesis; the hostname was in fact correct, name *resolution* was the problem.
- *"you should search for \\EPCORPAPAGENT12\... because after script failed i myself navigated and found at this location"* + the SUT file-picker screenshot — **the course correction**.
- *"i tried doing it manually but it is still coming again"* — confirmed the popup recurs and cannot be fixed by a one-time manual Allow.
- Reviewer comment from Himaja Reddyvari on the PR, line +224: *"Please add default catch statements as per other handlers"*.

---

### Root cause

Five distinct causes across the chain. Each stated so someone new to the codebase can follow.

**1. Search rectangle too narrow (the original ticket reason).**
`TESTAUTOMA_6170_PartMasterWidgetPassTest.script:28` passed `config().SUT.leftHalf` as the search rectangle for validating the text `"Physical Product"` after import. `config.script` defines `leftHalf: [-25,-10,960,1035]` — its right edge is x=960. In the Run-1 screenshot the imported item's title badge rendered right of centre (my visual estimate ≈x=1173; **the exact coordinate was never measured**, so this is an estimate, not a logged value). The widget itself was centre-positioned in that run — the log records `(TEXT:"Create from Spreadsheet")` `found at (839, 251)`. OCR therefore never scanned the region containing the text, and after two ~120s waits `common.validateValues` threw. The application had worked correctly; the assertion looked in the wrong place.

**2. Stale hardcoded dashboard URL.**
`PartMaster.suite/Resources/PartMaster.json` key `partMasterWidget.BSTURL` still pointed at `https://3dxdashboard23xbst.cos.is.keysight.com/...`. On 2026-06-17, commit `fd30b37a` migrated the BST estate to the `supplychain.keysight.com` domain and updated `EnvUrl.json` (`DashboardURL` → `https://3dxdashboardbst.supplychain.keysight.com/3ddashboard`) **but did not update PartMaster.json**. Critically, `PartMaster.openPartMasterWidget` reads the dashboard URL from `PartMaster.json` (`PartMaster.script:184`), *not* from `EnvUrl.json` — so the global config fix never reached this test. The old host no longer resolves → `DNS_PROBE_FINISHED_NXDOMAIN`.

**3. Missing prerequisite template on the Eggplant controller machine.**
`PartMaster.updateDataIntoNetworkShareDrive` (`PartMaster.script:107`) does `copy file <DriveTemplatePath> to <PathToWriteFile><TESTID>.xlsx`, where `DriveTemplatePath = C:\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx`. On the machine running Eggplant the folder existed but was **empty**, and the template is not in the git repo. Source file absent → `STFileSystemException`.

**4. Share topology / execution host mismatch.**
The copy in (3) writes **locally**, but the SUT's Browse dialog is fed a **UNC** path built from `PartMaster.json` `TemplatePath` (`PartMaster.script:126–127`). Those are the same location only when the controller runs on the host that also serves the share. Verified facts: Jay's laptop could **not** reach `\\EPCORPAPAGENT12` (`Test-Path` False, ping False), while the SUT **could** (Jay's file-picker screenshot). SUT→laptop by hostname failed outright; SUT→laptop by IP hung ~3.5 min without resolving.

**5. Unhandled "Access other apps" browser popup on the dashboard tab.**
Edge is launched `msedge --start-Maximized -Inprivate`, and each run begins with `taskkill /f /im msedge.exe`, so site permissions never persist between runs. `CommonEnovia.clickHome` (`CommonEnovia.script:705–707`) already dismisses this popup **during login on the 3dspace tab**, but nothing dismissed it after navigating to the dashboard tab in Step-2. When it appeared (top-left) it overlaid the widget, so `"Create from Spreadsheet"` could not be read. It is intermittent — Run 6 passed without it appearing; Run 7 failed because it did.

---

### The fix

**Fix 1 — `TESTAUTOMA_6170_PartMasterWidgetPassTest.script:28`**
```diff
-	PartMaster.uploadPartMasterNetworkShareFile TESTAUTOMA_6170,"Physical Product",config().SUT.leftHalf
+	PartMaster.uploadPartMasterNetworkShareFile TESTAUTOMA_6170,"Physical Product",PartMaster.getSearchRect(validationErrorArea)
```
(`validationErrorArea` = `[45,139,1706,805]`, defined in `PartMaster.script:6`.)

**Fix 2 — `PartMaster.suite/Resources/PartMaster.json`**
```diff
-"BSTURL":"https://3dxdashboard23xbst.cos.is.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting"
-"TESTURL":"https://3dxdashboard23xtest.cos.is.keysight.com/3ddashboard/#dashboard:5d2ab719-7ea0-4524-bfe9-40287ab2ae9e/tab:EggplantAutomationTesting"
+"BSTURL":"https://3dxdashboardbst.supplychain.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting"
+"TESTURL":"https://3dxdashboardtest.supplychain.keysight.com/3ddashboard/#dashboard:5d2ab719-7ea0-4524-bfe9-40287ab2ae9e/tab:EggplantAutomationTesting"
```

**Fix 3 — `TemplatePath`: net zero change.** It was temporarily edited to `\\\\HYB-1DYH20JTZLP\\...`, then `\\\\10.23.73.183\\...`, then **reverted** to its original `\\\\EPCORPAPAGENT12\\Enovia_PreRequisites\\Part Master\\`. Blockers 3 and 4 were resolved by environment action (Jay copied the template locally; the SUT reads from the agent share), not by code.

**Fix 4 — `PartMaster.script`: new handler + call site.**
```diff
+		//Handle the intermittent "Access other apps" browser popup on the dashboard tab (may or may not appear)
+		PartMaster.handleAccessOtherAppsPopup
+
 		common.validateValues "Create from Spreadsheet",config().SUT.leftHalf
```
Handler as finally committed (after review):
```sensetalk
to handleAccessOtherAppsPopup
	try
		if ImageFound(text:"Access other apps",waitFor:15,searchRectangle:config().SUT.TopLeftQuadrant)
			common.success "Access other apps popup found"
			common.ClickBtnByText "Allow",20,config().SUT.TopLeftQuadrant,yes
		else
			Log "No Popup Found - Access other apps"
		end if
	Catch theException
		"exceptionHandling".failedHandlerNavigation(callStack())
		"exceptionHandling".errorCapture theException
	End try
end handleAccessOtherAppsPopup
```
First committed with a custom non-fatal `catch popupException / Log ...`; changed to the standard `exceptionHandling` block after the reviewer asked for it.

**Commits:** `8e0d96c5` (fixes 1+2) · `8e1381c0` (fix 4, handler) · `e256da7b` (review amendment). Branch `fix/Testautoma-7947`; PR #1072 → `Testing_Mar10`.

---

### What was got wrong first

**Was the first hypothesis right?** Partly — and the honest answer is more interesting than yes or no.

The first hypothesis (search rectangle too narrow) was a correct reading of the Run-1 evidence and produced a defensible fix. **But it was never actually proven.** In the passing Run 6, the log records `(TEXT:"Physical Product")` `found at (696, 684)` — x=696 is *inside* the old `leftHalf` (right edge 960). By then the refreshed UI had moved the widget left (`"Create from Spreadsheet"` moved from `(839, 251)` in Run 1 to `(389, 251)` in Run 6). **So on the run that passed, the original unfixed code would very likely have worked too.** The rectangle change is a safe superset, not a demonstrated necessity. I stated this in-conversation, and it must not be recorded as a validated causal fix.

**Wrong turn #1 — the big one: two runs burned on a laptop-share dead end.**

After blocker 3 (missing template), I reasoned: the script writes the fresh data file locally on the controller, therefore the SUT must read it from the controller — so let's share Jay's laptop folder and repoint `TemplatePath` there.

The false signal that started it: I ran `Test-Path "\\EPCORPAPAGENT12\Enovia_PreRequisites\Part Master\"` **from Jay's laptop**, got `False`, and treated that as evidence the agent share was unusable. **That was a reasoning error.** The laptop's ability to reach the share is irrelevant to whether the *SUT* can read it — and the SUT is the machine that actually opens the file. I tested the wrong direction of reachability and then built a plan on the result. Jay's statement *"sut can do that, because we are on same network via keysight's vpn"* reinforced the wrong direction, and I accepted it without testing SUT→laptop before editing config.

- Attempt A: `TemplatePath` → `\\HYB-1DYH20JTZLP\...`. Run 4 failed: `Windows cannot access \\HYB-1DYH20JTZLP\Enovia_PreRequisites`, then `OCR Error: Operation was aborted`.
- Diagnosis of A: hostname not resolvable over VPN → switch to IP. I used `Find-NetRoute` to pick `10.23.73.183` (the PANGP VPN adapter). This was *sound reasoning on a wrong premise*.
- Attempt B: `TemplatePath` → `\\10.23.73.183\...`. Run 5 failed: picker hung ~3.5 minutes, `import` never appeared.
- **What corrected the course:** Jay said *"i think ... you should search for `\\EPCORPAPAGENT12\...`, because after script failed i myself navigated and found at this location"* and attached a screenshot of the **SUT's own file picker** listing that share's contents. That single screenshot proved SUT→agent-share worked, which no probe I had run could show. I reverted `TemplatePath` and Run 6 passed.

**Wrong turn #2 — reading the wrong region of common.script.** The log said `line 657 ... clickElement`, so I read `common.script` 620–699 and found unrelated handlers. A grep then revealed **two** definitions of `clickElement` (lines 155 and 967) and two of `validateValues` (176 and 992), which differ materially — the 155 version uses `waitfor:5` and has no try/catch; the 967 version uses `waitfor:180` and wraps in try/catch with `LogException`. Cost: one wasted read. `UNCERTAIN — I inferred that the reported line numbers (657/662/973) map to the *second* definition (the 180s waits in the logs are consistent with it), but I never established the file-line ↔ log-line mapping, so which body executes is not confirmed.`

**Wrong turn #3 — same class, on the popup fix.** I grepped `TopLeftQuadrant` in `config.script` and got no match, briefly implying the login handler referenced something undefined. A repo-wide grep found it in **two** places: `common.script:18` as `TopLeftQuadrant:((0,0),(.5,.5))` and `config.script:24` as `topLeftQuadrant:[0,0,1920/2,1080/2]`. The first grep failed only because of case. Cost: one extra lookup.

**A non-wrong-turn worth recording:** when Jay asked for manual steps to click Allow "one time", I told him upfront it would not persist (InPrivate + `taskkill` each run) while still giving the steps. He tried it, and reported *"it is still coming again"* — the prediction held. This consumed a round-trip but was not a misdiagnosis.

**Also important:** after Run 6 passed I declared the ticket green and committed; the PR was merged. Run 7 then failed on a **new, previously-unseen** cause with **byte-identical error text to Run 2**. Had I matched on the error string alone, I would have re-opened the already-fixed URL hypothesis. Only the screenshot distinguished them.

**Attempt count:** 7 documented runs — 1 original failure + 5 further failures + 1 pass, then 1 more failure. Four separate causes were fixed or resolved before the pass; a fifth was found after it.

---

### Knowledge source

Multiple genuinely apply; forcing one would destroy the finding.

- **`sibling_scripts`** — the actual content of Fix 1 came from grepping all 18 call sites of `uploadPartMasterNetworkShareFile` and observing that every currently-passing sibling (6167, 6169, 6174, 6176, 6178) passes `PartMaster.getSearchRect(validationErrorArea)`, while only 6170, 6172 and 6179 pass `config().SUT.leftHalf`. The codebase already contained the correct answer.
- **`tribal`** — needed and available nowhere in any file:
  1. That `C:\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx` must pre-exist on the **controller** machine (not in git, not documented).
  2. That the SUT reads the uploaded file from `\\EPCORPAPAGENT12\...`, and that the controller is expected to be a host that can write to that share.
  3. Which hosts can reach which shares — the reachability matrix. The decisive fact (SUT→agent share works; laptop→agent share does not) came only from a human manually driving the SUT.
  4. That the June-17 domain migration happened at all — recoverable from git history, but only if you know to look.
- **`app_behaviour`** — (a) when the spreadsheet's `TITLE` column is blank, the Part Master widget auto-generates the title as Type+EIN, producing `Physical Product00156939`, which is *why* the searched literal `"Physical Product"` appears at all; (b) the "Access other apps" permission prompt fires per-session under InPrivate and cannot be suppressed by a one-time manual Allow.
- **Not `script_only`.** Nothing about the failing line alone would have revealed any of the five causes.

---

### Fixable component

`multi_component: true`
- `script` — Fix 1 (search rectangle) and Fix 4 (popup handler).
- `script` (repo config file) — Fix 2, the stale URL in `PartMaster.json`. *(Not `test_data`: the same file holds test data, but the changed keys are environment URLs.)*
- `environment` — blockers 3 and 4 (missing template file; share/host reachability). Resolved by human action, **deliberately not** by patching code. Patching correct code to mask these would have created a landmine.
- Not `application_bug` — the Enovia application behaved correctly in every one of the seven runs.

---

### Failure family

`multi_cause: true`

| Blocker | Family |
|---|---|
| 1 — leftHalf too narrow | `search_rectangle` |
| 2 — stale hardcoded dashboard URL | `config_value_stale` |
| 3 — missing prerequisite template | `environment_issue` |
| 4 — share unreachable from controller / wrong execution host | `environment_issue` |
| 5 — "Access other apps" popup overlaying the target text | `PROPOSED: unhandled_popup_overlay` |

**On blocker 5 — none of the twelve genuinely fits, so I am not forcing it.** It is not `search_rectangle` (the rectangle was correct), not `text_label` (the literal was correct), not `missing_wait` (three retries over ~6 minutes were performed — waiting longer would never help), not `image_staleness`, and not `environment_issue` in the actionable sense (it is fixed in-script, and recurs *by design* because of InPrivate). The distinguishing signature is: **a modal/interstitial occluding an element that is otherwise present and correctly targeted, appearing intermittently.** Routing it to any of the existing twelve would train the wrong repair — e.g. an agent tagging it `search_rectangle` would widen a rectangle that was never wrong, and one tagging it `missing_wait` would add waits that cannot help.

---

### Handlers involved

**Blocker 1 chain:**
`TESTAUTOMA_6170_PartMasterWidgetPassTest.script:28 → PartMaster.uploadPartMasterNetworkShareFile (PartMaster.script:123) → common.clickElement (common.script:967, per the log's "line 973" / "line 657") → common.validateValues`

**Blockers 2 & 5 chain:**
`TESTAUTOMA_6170_...script:23 → PartMaster.openPartMasterWidget (PartMaster.script:178) → common.validateValues "Create from Spreadsheet"`
(URL read at `PartMaster.script:184` from `PartMaster.json`.)

**Blocker 3 chain:**
`TESTAUTOMA_6170_...script:27 → PartMaster.updateDataIntoNetworkShareDrive (PartMaster.script:98) → copy file (PartMaster.script:107)`

**Reference handler reused for Fix 4:**
`CommonEnovia.clickHome (CommonEnovia.script:702) → the "Access other apps" → "Allow" block at lines 705–707`

**Handlers whose names misdescribe what they do — both directly caused confusion here:**
- **`updateDataIntoNetworkShareDrive`** — despite "NetworkShareDrive", it writes to a **local** path (`PathToWriteFile` = `C:\Enovia_PreRequisites\Part Master\`). It never touches a network share.
- **`uploadPartMasterNetworkShareFile`** — it does not upload anything to a share; it types a UNC path into the browser's file-picker so the **SUT** reads the file.
  Together these two names imply a single network location and hide the two-machine split that caused blockers 3 and 4.
- **`common.script` contains duplicate definitions** of `clickElement` (155 and 967) and `validateValues` (176 and 992) with materially different behaviour (`waitfor:5` vs `waitfor:180`; no try/catch vs try/catch).

---

### Outcome

**Split — state plainly:**

- **Fixes 1 + 2 (search rectangle, dashboard URLs): VALIDATED by an actual run.** Run 6 (7/12/26 9:30 PM) returned `SUCCESS ... Errors:"0"` with all five steps passing, including `(TEXT:"Physical Product")` `found at (696, 684)` and the Step-5 checks (`"001"`, `"In work"`). Committed `8e0d96c5`; PR raised by Jay and **merged** (confirmed: `origin/Testing_Mar10` contains `8e0d96c5`).
  - **Caveat, important:** as noted above, in that passing run the target text was at x=696, inside the *old* rectangle. The run proves the fix does no harm; it does **not** prove the rectangle was the cause of the Run-1 failure.
- **Blockers 3 + 4: resolved by environment action, validated by the same passing run.** No code change survives (TemplatePath reverted to its original value).
- **Fix 4 (popup handler): NOT VALIDATED. No run exists in this conversation after the handler was added.** It was written, committed (`8e1381c0`), reviewed by Himaja Reddyvari, amended (`e256da7b`), and pushed to PR #1072. Its correctness rests on the fact that it reuses the idiom already proven at login in `CommonEnovia.clickHome` — that is an argument, not evidence. **Do not record this as a working fix.**

---

### What would have made this faster

1. **A prerequisites/topology section in `context.md`, per suite.** For PartMaster: which file must pre-exist on the controller, that the SUT reads via `\\EPCORPAPAGENT12\...`, and that the controller must be a host able to write to that share. This alone would have removed blockers 3 and 4 and the entire two-run dead end — the largest single time sink.
2. **A host↔share reachability matrix as data.** The decisive fact (SUT can read the agent share; the laptop cannot) took two failed runs and a manual human screenshot to establish. It should be a stated fact, not a discovery.
3. **Test reachability in the direction that matters before editing config.** The specific error to prevent: probing controller→share and concluding something about SUT→share. If the SUT opens the file, test from the SUT.
4. **A per-suite inventory of resource files that duplicate global config, with an explicit warning.** `context.md` presented `EnvUrl.json` as *the* URL source; `PartMaster.json` silently held its own copy. A single line — "PartMaster.json holds BSTURL/TESTURL independently of EnvUrl.json" — would have made blocker 2 instant.
5. **A dated infrastructure-changes list.** "2026-06-17 (commit `fd30b37a`): BST/TEST estate migrated to `supplychain.keysight.com`; suites may hold stale `cos.is.keysight.com` URLs." Jay supplied this hypothesis from memory; without him it would have taken much longer.
6. **Auto-generated per-suite `getSearchRect` tables.** `ConfigEnovia`'s rectangles were documented; `PartMaster.script`'s local `getSearchRect` (`validationErrorArea` etc.) was not, so the correct rectangle had to be found by reading the module.
7. **Sibling-usage comparison as a first-class, early step.** Grepping the failing handler's call sites and diffing the failing caller's arguments against the passing callers' produced Fix 1 almost deterministically. It should run before any fix is proposed.
8. **Never match a new failure to a past one by error string alone.** Runs 2 and 7 have byte-identical error text and unrelated causes.

---

### Notes

- **The single most transferable finding: this ticket was a *blocker chain*, not a bug.** Five causes across four classes (code, config, environment, infrastructure), surfacing one at a time, each only visible after the previous was cleared. A retry loop that treats every failed re-run as "my fix was wrong, try again (≤3)" would misjudge this badly — Fix 1 was applied at attempt 1 and remained correct through five subsequent runs. New failures must be re-classified from scratch, and a *different* blocker should not consume the fix-retry budget.
- **A test passing once does not mean it is fixed.** Run 6 passed; Run 7 failed on an intermittent popup that simply had not appeared in Run 6.
- **Things that looked like the cause but were not:** (a) the hostname `HYB-1DYH20JTZLP` — Jay suspected it was wrong; it was correct, but unresolvable from the SUT; (b) `OCR Error: Operation was aborted` in Run 4 — reads like an OCR/vision defect, but was a downstream symptom of a blocked network dialog; (c) the identical `"Create from Spreadsheet" is not displayed` text in Runs 2 and 7.
- **Deliberate non-actions worth learning from:** I did not patch the script to work around the missing template or the unreachable share, and did not create the SMB share myself (an outward-facing machine change — the command was given to Jay to run). An agent needs a legitimate "environment remediation required" outcome, or it will be tempted to mask environment faults in code.
- **Stale sibling tests not touched (out of scope, still latent):** `TESTAUTOMA_6172` and `TESTAUTOMA_6179` still pass `config().SUT.leftHalf` to `uploadPartMasterNetworkShareFile`, the same pattern fixed in 6170. Jay was offered these and the repo-wide stale-URL sweep; neither was actioned in this conversation.
- **Data-freshness caveat carried into the passing run:** because the controller could not write to `\\EPCORPAPAGENT12`, the SUT imported the agent's pre-existing `TESTAUTOMA_6170.xlsx` (dated 6/3/2026 in Jay's screenshot), not the file the script generated that day. Acceptable for 6170 (its test data is structurally identical every run — `TYPE: "Physical Product"`, everything else blank) but **not** for tests with run-specific data.
- **Duplicate-definition hazard:** grep for handler definitions in `common.script` expecting more than one hit, and be aware that reported log line numbers do not map directly to file line numbers.
- **Grep case-sensitivity bit twice** (`TopLeftQuadrant` vs `topLeftQuadrant`); the codebase is inconsistent about identifier casing and SenseTalk appears to be case-insensitive here.

---

## TESTAUTOMA-7949

**Failing test:** TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.script
**Suite:** PartMaster.suite
**DAI runid:** 35255 (the original failing run, eventtime 2026-06-26). A later run 36197 (2026-07-15) is also in this conversation but failed for a *different* reason — see Outcome. The run that validated the fix was a local Eggplant run (log pasted in chat, 7/12/26 11:57 PM – 7/13/26 12:03 AM) with **no runid shown**.

Ticket relationship: the Jira screenshot shows TESTAUTOMA-7949 ("Change Scope: Part Master: Verify the Download Template Option from Part Master Custom Widget."), Component/s `Change_Scope, ENOVIA-Automation`, label `Phase3`, status `In Dev`, linked "relates to" TESTAUTOMA-6167 (CLOSED, assignee Sachin Gupta2). The *script* carries the 6167 number; the *work item* is 7949.

### Symptom

Run 35255 died in Step 2 of the test (the log emitted `Running Step-2` at 10:12:16, never reached `Running Step-3`).

Verbatim, in order:

```
Unable to Find Image (TEXT:"Create from Spreadsheet"). Text not found.
```
(emitted 3 times — 10:14:44, 10:16:46, 10:18:49)

```
"Create from Spreadsheet" is not displayed on the screen.
"Create from Spreadsheet" is not displayed on the screen. - (no reason given)
Testcase failed in : ["ScripName : testautoma_6167_verifydownloadtemplateoptionfrompartmasterwidget","HandlerName1 : openpartmasterwidget"]
Technical Error: Runtime Error at line 5 (line 661 of script): "Create from Spreadsheet" is not displayed on the screen. - (no reason given)
Snippet Error: TestCases/TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.script failed
FAILED, 1 errors, 1 warnings, 4 state transitions, 2 actions executed
```

Immediately before the failure, the log shows the URL that was typed into a new tab (10:12:20):

```
https://3dxdashboard23xbst.cos.is.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting[return]
```

Step 1 (login) had fully succeeded, using `https://3dxspacebst.supplychain.keysight.com/3dspace/nosaml`.

### Evidence used

**Decisive:**
- The typed-URL log line at 10:12:20 (old host `3dxdashboard23xbst.cos.is.keysight.com`) contrasted against the Step-1 login URL (`3dxspacebst.supplychain.keysight.com`). Two different domains in the same run, one working and one not.
- A repo-wide `Grep` for `3dxdashboard23xbst|cos\.is\.keysight|3ddashboard`. This single search surfaced the stale value and the migrated value side by side in one result set: `Enovia\PartMaster.suite\Resources\PartMaster.json:3` (old host) and `Enovia\EnoviaCommon.suite\Resources\EnvUrl.json:14` (new host). This was the moment the diagnosis was made.
- `git log --oneline -- Enovia/EnoviaCommon.suite/Resources/EnvUrl.json` then `git show fd30b37a -- Enovia/EnoviaCommon.suite/Resources/EnvUrl.json`, which showed commit `fd30b37a` (2026-06-17, "Adding fixes to Urls to switch to any specidied env") migrating BST from `*.cos.is.keysight.com` to `*.supplychain.keysight.com`. This converted a plausible hypothesis into a confirmed one — it dated the breakage (17-Jun) to before the failing run (26-Jun) and named the migration that missed PartMaster.json.

**The error screenshot — was it necessary?**
It was **corroborating, not necessary**. It showed Edge on the dead URL with `Hmmm... can't reach this page`, `Check if there is a typo in 3dxdashboard23xbst.cos.is.keysight.com.`, and `DNS_PROBE_FINISHED_NXDOMAIN`. The log alone (typed URL + repo grep + git history) was sufficient to reach and confirm the same diagnosis. What the screenshot added was ruling out the alternative readings of "text not found": it proved the page never loaded at all (DNS), rather than the page loading slowly, or loading with changed UI labels, or an OCR/DPI miss. So: not required to find the fix, but it collapsed the hypothesis space instantly and raised confidence before any edit was made.

**Source files read, in order:**
1. `Glob **/context.md` → no match; `Glob **/TESTAUTOMA_6167*` → found the script path
2. `Glob **/*context*.md`, `Glob **/*.md` → no matches
3. `Bash ls` of repo root + `find . -iname "context*"` → confirmed no context.md inside the repo
4. `Enovia/PartMaster.suite/Scripts/TestCases/TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.script` (full, 52 lines)
5. Repo-wide Grep (above) + `Glob **/PartMaster.script`
6. `Enovia/EnoviaCommon.suite/Resources/EnvUrl.json` and `Enovia/PartMaster.suite/Resources/PartMaster.json` (read in parallel)
7. Grep of `PartMaster.script` for `openPartMasterWidget|BSTURL|partMasterWidget|Create from Spreadsheet` + `git log` on both JSONs (parallel)
8. `Enovia/PartMaster.suite/Scripts/PartMaster.script` lines 178–207 (the handler) + `git show fd30b37a` (parallel)
9. After the edit: Grep for `3dxdashboard23xbst|3dxdashboard23xtest` to find any remaining stale references
10. Later in the session (after the fix): `CommonEnoviaContd.script` lines 799–837, for the *second, unrelated* failure in run 36197

**Supplied by Jay, not present in any file at the time it was offered:**
- Jay's opening hypothesis, in his first message: *"I think the url is now changes to something like 'supplychain.keysight.com', can u check? if possible check from old git commits also to confirm something"*. This named both the correct answer and the correct verification method (git history) before any file was read. Note honestly: the fact itself **was** already in the repo (`EnvUrl.json:14`), so this was not knowledge that existed nowhere — but Jay's prompt pointed straight at it and shaped the search.
- Jay later supplied `context.md` from `C:\Users\jantiwar\Desktop\Enovia\context.md`, i.e. **outside the repo root**. It arrived after the fix was already made and did not change the diagnosis.

**Turned out irrelevant / noise:**
- `Unable to Find Image (TEXT:"Engineering Release"). Text not found.` — an intentional optional check inside the handler with an else-path; not a defect.
- `Unable to Find Image icons/welcomeCheckbox.png` and `Unable to Find Image (TEXT:"Access other apps"). Text not found.` / `No Popup Found - Access other apps` — optional popup handling, benign.
- `Unable to Find Image (TEXT:"Login"). Text not found.` followed by a DPI switch to 144 and a successful `(TEXT:"username")` find — the login handler's own DPI fallback working as designed.

### Root cause

**File:** `Enovia/PartMaster.suite/Resources/PartMaster.json`, line 3 (and line 4 for the TEST equivalent).

The Part Master widget's dashboard URL is **hardcoded in a suite-local resource JSON**, separate from the central `EnvUrl.json` that every other URL in the framework comes from.

On 2026-06-17, commit `fd30b37a` migrated the BST environment off the `*.cos.is.keysight.com` domain onto `*.supplychain.keysight.com`. That commit updated `EnvUrl.json` (EnoviaURL, DashboardURL, DigiWorkerURL, etc.) but **did not touch `PartMaster.json`**, which kept the pre-migration host `3dxdashboard23xbst.cos.is.keysight.com`. That host no longer exists in DNS.

The consumption path, in `Enovia/PartMaster.suite/Scripts/PartMaster.script`:

```
178  to openPartMasterWidget
183      if ImageFound(text:"bst", waitFor:10,SearchRectangle:[0,0,1920,86]) then
184          put FileOperations.getJSONValueFromJSONFile (Resourcepath("PartMaster.json")).partMasterWidget.BSTURL into dashboardURL
...
190      Typetext controlKey,t
191      typetext dashboardURL,return
193      if ImageFound(text:"Engineering Release", waitFor:20,SearchRectangle:config().SUT.webForm) then
...
198      common.validateValues "Create from Spreadsheet",config().SUT.leftHalf
203  end openPartMasterWidget
```

So: Ctrl+T opens a new tab, the dead URL is typed, Edge renders `DNS_PROBE_FINISHED_NXDOMAIN` instead of the dashboard, and `common.validateValues` at line 198 searches for `"Create from Spreadsheet"` on an error page, finds nothing after its retries, and throws.

The reason this was confusing to read from the log alone is that **the thrown message names the missing text, never the failed navigation**. Nothing in `"Create from Spreadsheet" is not displayed on the screen.` hints that a URL was wrong. The only pointer back to the navigation is the handler name in `HandlerName1 : openpartmasterwidget`, and the typed-URL line ~6 minutes earlier in the log.

Why Step 1 passed while Step 2 failed: Step 1 logs in via `LaunchApp.launchURL` → `EnvUrl.json` (already migrated, correct). Step 2 is the only place that reads `PartMaster.json`'s widget URL (stale). Same run, two different URL sources, one of them lagging.

### The fix

`Enovia/PartMaster.suite/Resources/PartMaster.json`, lines 3–4. Host swapped only; dashboard GUID and tab name unchanged.

Before:
```json
"BSTURL":"https://3dxdashboard23xbst.cos.is.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting"
"TESTURL":"https://3dxdashboard23xtest.cos.is.keysight.com/3ddashboard/#dashboard:5d2ab719-7ea0-4524-bfe9-40287ab2ae9e/tab:EggplantAutomationTesting"
```

After:
```json
"BSTURL":"https://3dxdashboardbst.supplychain.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting"
"TESTURL":"https://3dxdashboardtest.supplychain.keysight.com/3ddashboard/#dashboard:5d2ab719-7ea0-4524-bfe9-40287ab2ae9e/tab:EggplantAutomationTesting"
```

New hosts were not invented — they were taken from the already-migrated values in `EnvUrl.json` (`:14` bst `DashboardURL` = `https://3dxdashboardbst.supplychain.keysight.com/3ddashboard`, `:33` threeDTest `DashboardURL` = `https://3dxdashboardtest.supplychain.keysight.com/3ddashboard`).

Committed as `b9a9919e` on branch `fix/Testautoma-7949` (branched off `Testing_Mar10`), message: `Fix Part Master widget dashboard URL to supplychain.keysight.com domain`. 1 file changed, 2 insertions(+), 2 deletions(-). Pushed to Bitbucket; PR left for Jay to raise. Not merged into `Testing_Mar10`.

Only `PartMaster.json` was staged. 17 `SuiteInfo` files were dirty in the working tree (Eggplant touches these when suites are opened/run) and were deliberately excluded.

### What was got wrong first

**There were no wrong turns on this ticket. The first hypothesis was correct and it was the only hypothesis pursued.** Recording that plainly rather than manufacturing a struggle.

The actual path was: Jay's opening message already contained the hypothesis ("I think the url is now changes to something like supplychain.keysight.com... check from old git commits also to confirm"). One repo-wide grep confirmed the stale value in `PartMaster.json` against the migrated value in `EnvUrl.json`. One `git show` dated the migration to 17-Jun-2026, before the 26-Jun failure. One edit. One validating run: PASSED. **One attempt, no failed intermediate fixes, no revisions to the fix.**

Honest caveats about the path, none of which are wrong turns:

- **A few calls were spent on a file that did not exist where it was said to be.** The first instruction was to read an attached `context.md`; three tool calls (two Globs, one `ls` + `find`) established it was not in the repo at all. It was later supplied from `C:\Users\jantiwar\Desktop\Enovia\context.md`, outside the repo root. Cost: small, but avoidable.
- **Had `context.md` been read first and trusted, it would have pointed *away* from the fix.** Its line 53 states `BST DashboardURL: https://3dxdashboard23xbst.cos.is.keysight.com/3ddashboard` — the *stale* host — and line 51 similarly gives the pre-migration EnoviaURL. The doc predates the 17-Jun migration. This is the closest thing to a false signal in the whole ticket, and it was avoided only by accident (the file wasn't available at diagnosis time).
- **One factual error was made, in the final chat message, after the fix.** Diagnosing the *later* run 36197, the SUTs were misread as different: the claim was "a different SUT than the 7/13 pass which was 156.140.21.48". Checking the logs: run 35255 (26-Jun original failure) ran on `156.140.21.48`; the 7/13 passing run and run 36197 (15-Jul) **both** ran on `156.140.6.130`. So the pass and the new failure were on the *same* SUT. This does not change the 7949 diagnosis or fix, but it weakens the specific reasoning offered for the new failure ("different SUT") — the stronger reading is that the *same* machine accumulated state (recovered Excel session, leftover download) between 13-Jul and 15-Jul.
- A verification of the fix ran against `EnvUrl.json:26` (the `threeDDev` block), which still carries the old host. It was deliberately left unchanged as out of scope and flagged to Jay.

### Knowledge source

`sibling_scripts`

The failing script itself (52 lines) contains no URL and no hint of one — Step 2 is a single line: `PartMaster.openPartMasterWidget`. Reaching the cause required:
1. reading the sibling handler `PartMaster.script:178–203` to learn that the handler reads `.partMasterWidget.BSTURL` from a **suite-local** `Resources/PartMaster.json`, and
2. reading `EnvUrl.json` to discover that the framework's *central* URL config had already been migrated to a different domain, making the mismatch visible.

Additionally, `git log` / `git show` on `EnvUrl.json` were needed to *confirm* (not to discover) the cause — this is repo-resident information, not tribal, but it is not in any file's current contents.

Not `tribal`: the correct new domain existed in `EnvUrl.json` in the repo. Jay named it in the prompt, but an agent grepping the repo for the failing hostname would have found it unaided.

**What must go into JARVIS's curated `context.md`, concretely:** that environment URLs are **not** exclusively in `EnvUrl.json` — some suites hardcode their own URLs in `<Suite>.suite/Resources/<Suite>.json` (confirmed case: `PartMaster.json` → `partMasterWidget.BSTURL` / `.TESTURL`), and these are not updated when `EnvUrl.json` is migrated. The current `context.md` documents only `EnvUrl.json` as the URL location (its §"Environment URLs" and §"FIXING A BUG" step 7) and does not mention `partMasterWidget` URLs at all.

### Fixable component

`script`

Nuance worth recording: the changed artefact is a **Resources JSON in the automation repo**, not a `.script` file and not test data. Of the four available buckets, `script` is the correct one in the sense that matters — the defect was in version-controlled repo content and was fixed by a repo edit and a PR. It is explicitly **not** `environment`: nothing on the SUT or in the Enovia deployment was changed or needed changing. The Enovia environment had legitimately moved; the repo was the thing lagging behind.

### Failure family

`config_value_stale`

`multi_cause: false` — single cause, exact fit.

Deliberately *not* tagged `environment_issue`: the environment change (domain migration) was legitimate and correctly reflected elsewhere in the repo. The defect was the repo's stale copy of that value. Tagging this as `environment_issue` would route a future agent toward "re-run on a clean SUT / raise with infra", which would never have fixed it.

(Separately: the *later*, unrelated failure in run 36197 does look like `environment_issue` — see Outcome/Notes. Do not let that contaminate this ticket's tag.)

### Handlers involved

```
TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.script (Step 2, script line 25)
  → PartMaster.openPartMasterWidget            (PartMaster.script:178–203)
      → FileOperations.getJSONValueFromJSONFile(Resourcepath("PartMaster.json")).partMasterWidget.BSTURL   (:184)
      → common.validateValues "Create from Spreadsheet", config().SUT.leftHalf                              (:198)  ← threw here
```

Surprising / misdescribing behaviour worth flagging:

- **`openPartMasterWidget` does two unrelated things under one name.** It *navigates* (Ctrl+T + type URL) and then *validates page content*. When it fails, the thrown message is always about the missing content, never the navigation — so a navigation defect is reported as a text-search defect. An agent that reads only the error string will start hunting search rectangles, OCR/DPI, and text labels. All three would have been dead ends here.
- **The environment is selected by OCR, not by config.** Line 183 picks BST vs TEST by looking for the literal text `"bst"` in the browser chrome (`SearchRectangle:[0,0,1920,86]`, i.e. the URL bar region), falling back to `"test"`, else `common.Error "Aplication is not opened or OCR issue"`. So which URL gets used depends on reading the address bar, not on `EnvUrl.json`'s `Environment` key.
- **The reported line number is not a source line number.** `Runtime Error at line 5 (line 661 of script)`. UNCERTAIN — during the session this was described in chat as mapping to `PartMaster.script:198`, but that mapping was **assumed and never verified**. Evidence it is not a plain source reference: the later, entirely different failure in run 36197 (a different handler, `openFromDownloads`, in a different file) reported `Runtime Error at line 5 (line 662 of script)` — one line apart. Treat these numbers as compiled/aggregate offsets, not as a pointer into the file you are reading.

### Outcome

**PASSED — validated by an actual run.**

Local Eggplant run, 7/12/26 11:57:44 PM → 7/13/26 12:03:35 AM, env `bst`, user `SME-1`, SUT `156.140.6.130`. The decisive lines:

```
7/13/26, 12:00:45 AM  typetext  https://3dxdashboardbst.supplychain.keysight.com/3ddashboard/#dashboard:9379e709-cb4e-4d78-a4ae-d96bf9e58180/tab:EggplantAutomationTesting[return]
7/13/26, 12:01:09 AM  ImageFound (TEXT:"Create from Spreadsheet")  found at (389, 251)
7/13/26, 12:01:09 AM  LogSuccess  "Create from Spreadsheet" is successfully displayed on the screen.
```

Test completed end to end:
```
EndTestCase (Duration:"350.022", Errors:"0", Exceptions:"12", StartTime:"2026-07-12 23:57:45 +0530", Successes:"20", TestCase:"TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget", Warnings:"0")
SUCCESS  Execution Time 0:05:50 TestCases/TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.script
```

**Scope limits on that validation, stated plainly:**
- Only `BSTURL` was exercised. The `TESTURL` line was changed in the same commit but **has not been validated by any run** in this conversation.
- The new host was never independently reachability-checked (these are internal Keysight URLs, not reachable from this session). The passing run is the only proof it resolves.

**A later run failed — for a different reason, not a regression of this fix.** DAI runid 36197, 2026-07-15, same SUT `156.140.6.130`. In that run the 7949 fix worked (new URL typed 09:28:14; `"Create from Spreadsheet" is successfully displayed on the screen.` at 09:29:04; Step 3 reached, Download Template clicked, Save as clicked, file opened). It then failed further downstream in a different handler:

```
Unable to Find Image (TEXT:"Mass_Part_BOM_Upload_Template"). Text not found.
Text Mass_Part_BOM_Upload_Template  Is not present on the screen
Text Mass_Part_BOM_Upload_Template  Is not present on the screen - (no reason given)
Testcase failed in : ["ScripName : testautoma_6167_verifydownloadtemplateoptionfrompartmasterwidget","HandlerName1 : openfromdownloads"]
Technical Error: Runtime Error at line 5 (line 662 of script): Text Mass_Part_BOM_Upload_Template  Is not present on the screen - (no reason given)
FAILED, 1 errors, 1 warnings, 4 state transitions, 2 actions executed
```

That failure is in `CommonEnoviaContd.script:799–819` `openFromDownloads`, at line 808 `common.isTextPresentInSearchRect textBoxText,60,yes,getSearchRect(excelfileVald)`. A hypothesis was offered in chat (Excel "Document Recovery" pane + non-maximized Excel window + a stale `Mass_Part_BOM_Upload_Template (1).xlsx` already in Downloads, all visible in the screenshot Jay supplied) — **that hypothesis was NOT validated by any run and no fix for it was written.** It should be treated as an open, separate item, not as a finding.

### What would have made this faster

1. **Put in `context.md`: URLs are not centralised.** Some suites hardcode environment URLs in `<Suite>.suite/Resources/<Suite>.json`. Known instance: `PartMaster.suite/Resources/PartMaster.json` → `partMasterWidget.BSTURL` / `partMasterWidget.TESTURL`, consumed by `PartMaster.openPartMasterWidget`. These are missed by `EnvUrl.json` migrations. The current `context.md` says to check `EnvUrl.json` (§"FIXING A BUG" step 7) and would have sent an agent to the one file that was already correct.
2. **Correct — or date-stamp — `context.md` lines 51–54.** They still carry pre-17-Jun-2026 BST URLs (`3dxspace23xbst.cos.is.keysight.com`, `3dxdashboard23xbst.cos.is.keysight.com`). A curated context file that disagrees with the repo is worse than no context file, because an agent will trust it over a grep. Either fix these values or mark the section "verify against `EnvUrl.json` before use".
3. **Make this the standard first move for any "text not found" failure: grep the repo for the hostname/URL that appears in the log immediately before the failure.** One `Grep` for `3dxdashboard23xbst|cos\.is\.keysight|3ddashboard` produced the entire diagnosis. It is far cheaper than reasoning about search rectangles or DPI.
4. **Add a rule: when a test's login step succeeds but a later navigation step fails, compare the URLs used by each.** Two different URL sources in one run, one working and one not, is a strong stale-config signal and rules out SUT/network/credential causes immediately.
5. **Add the git-archaeology step explicitly:** `git log --oneline -- <config file>` then `git show <sha> -- <config file>`. It dated the breakage to 10 days before the failing run and named the migration commit, turning a guess into a confirmation before any file was edited. Jay prompted for this; JARVIS should do it unprompted for any suspected stale-config failure.
6. **Teach the Exceptions-vs-Errors distinction** (see Notes) so a passing run with 12 exceptions is not misread as a failure, and so benign optional probes are not chased as defects.

### Notes

- **`Exceptions:"12"` in a PASSING run is normal.** Eggplant counts optional `ImageFound` probes that the script deliberately handles with fallbacks (`welcomeCheckbox.png`, `(TEXT:"Access other apps")`, `(TEXT:"Save")`, `(TEXT:"Engineering Release")`). The fields that matter are `Errors:"0"` / `Warnings:"0"` and the final `SUCCESS` / `FAILED,...` line. Do not report a run as failed on the exception count.
- **Left deliberately unfixed:** `Enovia/EnoviaCommon.suite/Resources/EnvUrl.json:26` — the `threeDDev` block still has `"DashboardURL": "https://3dxdashboard23xbst.cos.is.keysight.com/3ddashboard"`, i.e. the dead host, and it is pointing at a *bst* hostname from inside the *threeDDev* block. Unused by the current `bst` execution, so out of scope for this ticket, but it will fail the same way if anyone switches to `threeDDev`. Offered to Jay; not actioned.
- **Things that looked like the cause but were not:** the `Engineering Release` / `Access other apps` / `welcomeCheckbox` / `Login` misses in the log are all intentional optional checks with else-paths. Four separate "Unable to Find Image" lines in this log are benign. Only the `Create from Spreadsheet` one was fatal.
- **`PartMaster.json` is not strict JSON.** It has missing commas between top-level keys, duplicate keys within one object (e.g. `TESTAUTOMA_6174` has `"KEYSIGHT PART NUMBER"` and `"LEGACY PART NUMBER"` twice), and trailing commas. SenseTalk's parser tolerates this. Do not "fix" it with a JSON formatter or a strict parser — edit surgically.
- **Working-tree hygiene:** 17 `*.suite/SuiteInfo` files show as modified whenever suites are opened/run in Eggplant. They are noise. Stage only the file(s) you intend to change; `git add -A` on this repo will sweep them in.
- **Git identity warning on commit:** the commit was made with an auto-derived identity (`Janmejay Tiwari <janmejay.tiwari1@non.keysight.com>`) because `user.name`/`user.email` are not configured globally. Harmless here, but worth setting before an agent commits autonomously.
- **Branch discipline used:** branched `fix/Testautoma-7949` off `Testing_Mar10`, pushed, and left the PR for Jay. Explicit instruction was **do not merge into `Testing_Mar10`**, and no merge was performed. Commit message was required to carry **no** Claude/AI co-author trailer.
- **Open item, not part of this ticket:** the run-36197 `openFromDownloads` failure (see Outcome). Unvalidated hypothesis only. If it reproduces after clearing Excel (`taskkill /f /im excel.exe`) and deleting `%USERPROFILE%\Downloads\Mass_Part_BOM_Upload_Template*.xlsx`, it is a genuine separate defect and deserves its own ticket — the candidate fix discussed was hardening `openFromDownloads` to dismiss the Excel Document Recovery pane and force-maximize/refocus the Excel window before the OCR check. Nothing was written.

---

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

`text_label` · `environment_issue` · **`PROPOSED: change_scope`** — **`multi_cause: true`**

- The mechanical fix was `text_label` (a label string was wrong). **But routing on `text_label`
  alone would have re-run exactly the R1–R4 flailing**, because the correct label is not discoverable
  by any label-fixing strategy. `text_label` describes the diff, not the problem.
- `PROPOSED: change_scope` — "application changed, the test must be rewritten to the new workflow;
  the new workflow is not present in code, logs or screenshots." None of the twelve names this. The
  source document independently proposes exactly this: "Add 'change_scope' and 'environment_flake' as
  first-class families in the router, and wire change_scope -> ask_human". The Jira ticket itself
  **carries the "Change Scope" label**, so this family is detectable *before* any diagnosis begins —
  which is the whole point of proposing it.
- `environment_issue` — the R2 3DDashboard blocker (BST refresh moved the app off-screen).
- **`PROPOSED: environment_flake`** — the R6 launch/login OCR flake. Distinct from
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

---

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

---

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

---

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

---

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

- `PROPOSED: hardcoded_coordinate_brittleness` — `tripleClick[137,172]` is a fixed *click* coordinate
  calibrated to one specimen's rendered text width. `search_rectangle` is the nearest bucket but is
  materially different: nothing about a search rectangle was wrong, and tagging it that way would
  train an agent to go adjust rectangles when the correct remedy is to anchor the click to a located
  element. This pattern recurs (`tripleClick[106,75]`, `tripleClick(149,72)` elsewhere in the repo),
  so it deserves its own family.
- `PROPOSED: silent_parameter_typo` — `watiFor:25` instead of `waitFor:25`. A misspelled *named
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

---

## TESTAUTOMA-8833

**Failing test:** TESTAUTOMA_2793_015_PartNotBeAllowedToBeDeletedIfItsTheFirstRevision.script
**Suite:** EngineeringCentral.suite
**DAI runid:** NOT RECORDED — no runid appeared in this conversation. The run headers carried only
`{ eggplant_data_sync : {environment:"bst", execution_type:"Business", jira_project_name:"Enovia_BST_Refresh", sut_server_id:"156.140.6.130"}}`

### Symptom

The test asserts the message `Has no revisions` after attempting to delete a first-revision Part.
The reported failure was that this text was not displayed.

Verbatim error line as it appeared in the DAI log: **NOT RECORDED** — the original failing log was
supplied before this conversation's context was compacted and the exact failure line is not
recoverable from what remains here. The summary of that portion records the symptom as
`"Has no revisions" text is not displayed`.

Step it died on: Step 4 (`Select a Part Check box and click delete Option`) — the delete was
attempted and the application answered with a different message.

Messages the application actually returned instead (quoted as they were used in this conversation's
analysis of the run that walked 16 result rows; the raw log lines themselves are pre-compaction):
- `Delete is not applicable for object Type 'Part'`
- `Context user is not same as the object Owner 'TIS'`

UNCERTAIN — I am confident these two strings are correct because they were quoted repeatedly and
consistently throughout the working session, but I cannot re-read the originating log line from
within this conversation to confirm character-for-character.

### Evidence used

**Mattered:**

- The two application messages above. These were the whole diagnosis: they proved the delete was
  being refused at two *earlier* gates than the revision check, and the split between which rows got
  which message is what identified the two distinct problems (wrong object type, and ownership).
- The row names from that same run, which separated cleanly by message:
  - refused with `Delete is not applicable for object Type 'Part'`: `LNC100M4AT-XXXXX`,
    `OB1PAL7QIM-XXXXX`, `PNTX0-60022`, `PNTX0-60023`, `PNTX0-50027`, `TESTKPNNBV190`,
    `TESTKPNNBV187`, `PNTX100-60032` — Part Master shaped names
  - refused with `Context user is not same as the object Owner 'TIS'`: `7121-9260`,
    `N5172B-ATO-25826`, `R1133A-601`, `APP_SOFTWARE`, `EA1000DM`, `Z0180A-ATO-40397`, `1822-7461`,
    `DE1000CMP` — real Keysight part numbers
- The result count collapse: the same search returned 148,817 results without an `Owner` criterion
  and 0 results with `Owner` added. This is what proved the criteria were actually being committed
  by the panel rather than silently ignored.
- The control run of TESTAUTOMA_2868 (full log supplied verbatim in this conversation), specifically:
  `7/27/26, 12:26:19 AM ImageFound (TEXT:"Has no revisions") found at (925, 140)` and
  `7/27/26, 12:26:20 AM EndTestCase (Duration:"358.137", Errors:"0" ...)`.
  This single run eliminated "the application changed" as a hypothesis.
- The 2868 log also independently confirmed the downward-only scroll behaviour:
  `ImageFound (TEXT:"Collaborative Policy") Unable to Find Image` → `scrollwheeldown moved 6` ×2 →
  `found at (111, 621)`.

**The error screenshot — was it necessary?**

Split answer:

- For the **popup** problem: yes, genuinely necessary. The log only showed a text-not-found for the
  Advanced Search panel label; it gave no reason. The screenshot showed the Edge prompt
  `3dxspacebst.supplychain.keysight.com wants to - Access other apps and services on this device`
  sitting over the top-left of the page. The log alone would not have identified this.
- For the **wrong object type** and the **0 results** findings: no. The log alone carried the
  application messages and the result count; the screenshots added nothing there.

**Source files read:**

- In this conversation (post-compaction), in order: the test script
  `Enovia/EngineeringCentral.suite/Scripts/TestCases/TESTAUTOMA_2793_015_PartNotBeAllowedToBeDeletedIfItsTheFirstRevision.script`,
  then `Enovia/EngineeringCentral.suite/Scripts/TestCases/TESTAUTOMA_2868_010_PartsWithOneRevisionCanNotBeDeletedWithPOMRole.script`.
  Also two greps for an existing part-creation handler, which found only
  `Enovia/EngineeringCentral.suite/Scripts/ECPartPage.script:130 to ValidateCreatePartNotAvailable`
  and `ECPartPage.script:1573 to createOtherDocumentUnderPart` — i.e. no reusable create-a-part
  handler exists in the Engineering Central suite.
- Earlier in the session: `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script`,
  `Enovia/Common.suite/Scripts/common.script`, `Enovia/Search.suite/Scripts/SearchResults.script`,
  and the credentials data consumed by `FileOperations.toFetchSDECOSUserData`.
  **The order in which those were read is NOT RECORDED.**

**Supplied by Jay from his own head, not present in any file:** NOT RECORDED. Jay supplied run logs,
screenshots, and the decision to run 2868 as a control (which was offered as an option rather than
volunteered knowledge). No out-of-band domain fact from Jay is recorded in what remains of this
conversation.

### Root cause

Two separate causes, one script-side and one not.

**1. Script-side — the search did not identify a testable part.**

`TESTAUTOMA_2793_015...script`, the `CommonEnovia.searchEnovia "advancedSearch"` call (now line 48).

In Enovia, searching with `Type = "Part"` does **not** return only classic Engineering Central
parts. It also returns the *Physical Products* created by the Part Master application (names of the
form `PRD-*`, and in this environment `PNTX*`, `TESTKPN*`, `*-XXXXX`). Those objects have no
revisions tab at all. Deleting one is refused with `Delete is not applicable for object Type 'Part'`
before any revision logic runs, so the test's expected `Has no revisions` can never appear for them.
The test picked whatever row came back first, and on this environment that was frequently one of
those Physical Products.

The exact criteria list as it stood *before* the change is **NOT RECORDED** — it is not visible in
what remains of this conversation.

**2. Environment/browser — a native prompt covered the panel.**

On the refreshed BST, Edge raises `Access other apps and services on this device` as the home page
finishes loading. This test goes straight from login into Advanced Search and never visits the Home
page, so — unlike sibling tests that call `commonEnovia.clickHome` — nothing in its path cleared the
prompt. It sits over the top-left of the page, covering the Advanced Search panel's `Source` label
that `searchEnovia` validates against.

**3. The actual remaining blocker — test data, not code.**

The logged-in user `SDE-COS` owns no part matching the required state on the refreshed BST. An
Advanced Search for Type=Part + Collaborative Policy=EC Part + Is Last Minor Revision=True +
Maturity State=EC Part.Preliminary + Minor Revision=001 + Owner=SDE-COS returns **0 results**, while
the same search without the Owner criterion returns 148,817. Every classic EC Part in the unfiltered
set is owned by `TIS` and is refused with `Context user is not same as the object Owner 'TIS'`
before the revision check is reached.

### The fix

Script changes (all in the test unless noted). The **before** text of these lines is NOT RECORDED —
only the after state is visible in this conversation, so what follows is the current state plus a
description of what it replaced.

**a. Popup dismissal.** New handler `handleAccessOtherAppsPopup` added to
`Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script` (reported at lines 1254-1287; it checks for
the text `Access other apps` in `topLeftQuadrant`, clicks `Allow`, and waits for the prompt to
disappear). **The handler body itself is NOT RECORDED verbatim in this conversation.** It is called
from two places: `searchEnovia`'s advancedSearch branch (reported at lines 268-271 of the same file,
also NOT RECORDED verbatim), and from the test after login:

```
// after (test line 32)
commonEnovia.handleAccessOtherAppsPopup configEnovia().general.minWait
```

**b. Search criteria — filter to classic EC Parts, and order to match the panel.**

```
// after (test line 48)
CommonEnovia.searchEnovia "advancedSearch", [["Part", "Type"],[advSearchUser, "Owner"],["EC Part", "Collaborative Policy"],["True", "Is Last Minor Revision"],["EC Part.Preliminary", "Maturity State"],["001", "Minor Revision"]]
```

`Collaborative Policy = "EC Part"` excludes the Physical Products. `Is Last Minor Revision = True`
on top of revision `001` means the part has that one revision and no later one. The ordering is
load-bearing: `searchEnovia` reaches each label via `common.scrollTo`, which only ever scrolls
**down**, so a criterion that sits above one already passed can never be found. `Owner` lives in the
standard block at the top of the panel with `Type`; the rest are in the alphabetical block below.

**c. Read the real message, walk more than one row, always dismiss the alert** (test lines 59-107).
Previously only the first row was tried and only the expected string was looked for; the native
alert was left on screen on the failure path, which blocks the following test. Current state:

```
put searchResults.returnColumnLoc ("Type","yes") into typeColumnLocation
put EveryImageLocation(Text:"Part",waitfor:5,searchrectangle:[typeColumnLocation+[-40,10],typeColumnLocation+[270,800]],validCharacters:"Part") into partRows
...
put 640 into lowestUsableRow
put 8 into maxRowsToTry
repeat with each item partRow of partRows
    if (item 2 of partRow) is greater than lowestUsableRow then next repeat
    if rowsTried is maxRowsToTry then exit repeat
    add 1 to rowsTried
    SearchResults.selectRightClickOptions partRow,"Delete"
    if not commonEnovia.waitForNativeAlert(configEnovia().searchRectangles.popUpWarning, configEnovia().general.minWait)
        put "no message was displayed" into deleteMessage
        exit repeat
    end if
    put readText(configEnovia().searchRectangles.popUpWarning, dpi:144) into deleteMessage
    if deleteMessage contains expectedMessage or ImageFound(text:expectedMessage, searchRectangle:configEnovia().searchRectangles.popUpWarning, ignoreNewLines:on, ignoreSpaces:on, waitFor:2)
        ...
        commonEnovia.dismissNativeAlert
        exit repeat
    end if
    Log "Row"&&rowsTried&&"was refused with:"&&deleteMessage&&"- trying the next row"
    commonEnovia.dismissNativeAlert
end repeat
```

`lowestUsableRow = 640` exists because the right-click menu opens roughly 360 pixels below the row
it was raised on, so `Delete` lands off-screen for rows near the bottom of the list.

And an explicit test-data error rather than a misleading assertion failure (line 65):

```
common.Error "No Part was returned by the advanced search - test data for a single revision Preliminary EC Part is missing",yes
```

### What was got wrong first

There were several wrong turns. In order:

**1. First hypothesis: the Physical Products alone explained it.** This came from the ticket itself
and was *partly* right — the wrong object type is real and is fixed — but it was not the whole
cause, and treating it as the whole cause is what made the next three runs necessary. Adding the
`Collaborative Policy` filter did not make the test pass.

**2. Dead end: the popup was invisible in the log.** After the filter change the run failed on a
text-not-found for the Advanced Search panel, which reads like a normal image-matching or timing
problem. Time went into that reading before the error screenshot showed the Edge permission prompt
physically covering the label. The false signal was that the log described a *missing label*, which
points at the label; the actual cause was something *on top of* the label.

**3. Dead end: criteria ordering.** After the popup fix, the run could not find the `Owner`
criterion. The instinct was that `Owner` was missing from the panel or named differently. It was
neither — `searchEnovia` had already scrolled past it, because `common.scrollTo` only scrolls
downward and `Owner` had been listed after a criterion that sits lower in the panel. Reordering the
list fixed it, and the following run found `Owner` at `(59,722)` with zero scrolls.

**4. Wrong inference about the two application messages — the worst one.** When a run walked 16
rows and got two different refusal messages, the initial reading was that the ownership check ran
*first*, so rows answering `Delete is not applicable for object Type 'Part'` had already passed the
ownership gate and were therefore owned by SDE-COS. That inference was stated, then had to be
reversed. What disproved it: adding `Owner = SDE-COS` to the search returned 0 results. If SDE-COS
had owned those 8 rows, the filtered search could not have been empty. The corrected reading is that
the **type check runs first**, so `Delete is not applicable for object Type 'Part'` says nothing at
all about ownership — it just means the object was a Physical Product.

UNCERTAIN — the gate ordering (type, then ownership, then revisions) is an inference from which
message appeared for which row, not something read from application source or documentation. It is
consistent with every observation in this session but has not been confirmed against Enovia itself.

**5. What finally corrected the course:** running TESTAUTOMA_2868 unchanged as a control. It asserts
the same `Has no revisions` string, uses the same policy/revision/maturity criteria, carries no
`Owner` criterion, and logs in as `POM-1`. It passed on its first result row. That collapsed the
remaining ambiguity in one run: the message exists, the rule is intact, the criteria are right, and
the only variable left is *who is logged in and what they own*. Choosing to run a passing sibling as
a control should have happened much earlier — it was cheaper and more decisive than any of the
four diagnostic runs that preceded it.

**Number of runs:** UNCERTAIN — at least four runs of TESTAUTOMA_2793_015 plus one control run of
TESTAUTOMA_2868. The exact count and ordering cannot be stated reliably: the pre-compaction summary
numbers the SDE-COS run that returned 0 results as "the third run", while the analysis carried out
afterwards refers to a *different* "run 3" that returned 148,817 results and walked 16 rows. Those
are two distinct runs under the same label, so the run numbering in this record should not be
trusted.

### Knowledge source

`app_behaviour` + `sibling_scripts` + `tribal` — **not** fixable from the script alone.

- `app_behaviour`: that Enovia's `Type = Part` search also returns Part Master Physical Products,
  which have no revisions tab and answer a delete differently; that the delete trigger refuses on
  object type and on ownership *before* it ever evaluates revisions, so the message you get tells
  you which gate you hit; that a plain designer role can only delete parts it owns.
- `sibling_scripts`: that `common.scrollTo` only scrolls downward, which turns the criteria list
  into an ordered list rather than a set — this is invisible from the test script and only shows up
  by reading the handler. Also that `SearchResults.selectItem1InSearchResults` only ever returns the
  first row, which is why the row-walking loop had to be written inline in the test.
- `tribal`: that the BST environment had been refreshed (`jira_project_name:"Enovia_BST_Refresh"`)
  and that the refresh left `SDE-COS` owning no qualifying part. Nothing in the repository records
  what test data is expected to exist for which user on which environment. The script's own
  prerequisite line says only `//Prerequisite: Parts in revision 001 should be available for this user`,
  with no statement of who guarantees that.

### Fixable component

`test_data` — for the blocking issue that remains.

Noting plainly that `script` fixes were also required and were made (the four changes above); they
were necessary but not sufficient. The test cannot pass on this environment no matter what the
script does, because there is nothing for `SDE-COS` to attempt to delete.

### Failure family

`multi_cause: true`

- `test_data` — the blocking cause. No part owned by SDE-COS in Preliminary at revision 001 exists
  on the refreshed BST.
- `environment_issue` — the Edge `Access other apps and services on this device` prompt covering the
  Advanced Search panel on the refreshed environment.
- `PROPOSED: search_criteria_too_broad` — the original ticket cause. The search returned a
  superset containing a *different object type* that superficially matches (`Type = Part` also
  matching Part Master Physical Products), so the test operated on an object the assertion could
  never hold for. None of the twelve fits this: it is not a search rectangle, not a text label, not
  a stale config value — the criteria were valid and were found, they simply did not discriminate.
  Forcing it into `test_data` would be wrong, because the data was present and correct; the query
  was under-specified.
- `PROPOSED: criteria_order_vs_scroll_direction` — a criteria list whose order does not match the
  order the panel draws its fields is unreachable, because the traversal only scrolls one way. This
  presents as a not-found label, which makes it look like `text_label` or `missing_wait`, and both
  of those readings were tried and were wrong. It deserves its own name precisely because it
  mimics two other families.

### Handlers involved

Failing test:
`TESTAUTOMA_2793_015 → commonEnovia.cleanup → LaunchApp.launchURL → CommonEnovia.loginEnovia → commonEnovia.handleAccessOtherAppsPopup (new) → CommonEnovia.searchEnovia "advancedSearch" → common.scrollTo → CommonEnovia.waitForLoading → searchResults.returnColumnLoc → SearchResults.selectRightClickOptions → commonEnovia.waitForNativeAlert → readText → commonEnovia.dismissNativeAlert`

Control test:
`TESTAUTOMA_2868 → commonEnovia.cleanup → LaunchApp.launchURL → CommonEnovia.loginEnovia → commonEnovia.clickHome "Tasks" → commonEnovia.searchEnovia "advancedSearch" → EngineeringCentral.deletePart " " → commonEnovia.popUpWarning "Has no revisions"`

Handlers whose behaviour was surprising or whose name misdescribes them:

- `common.scrollTo` — the name suggests it will reach the target. It only scrolls **downward**, so it
  can only reach targets below the current position. This is the single most load-bearing fact in
  this ticket and it is not discoverable from any test script.
- `SearchResults.selectItem1InSearchResults` — only ever hands back the first row, so it cannot be
  used to iterate candidates. The row-finding logic had to be duplicated in the test.
- `commonEnovia.clickHome` — incidentally clears the `Access other apps` popup as a side effect of
  reaching the Home page. Tests that call it are protected from the popup by accident; tests that do
  not call it are exposed. Nothing about the name suggests it has anything to do with popups.
- `commonEnovia.popUpWarning` — UNCERTAIN. It was stated during the session that it does not dismiss
  the alert when validation fails, leaving the modal on screen for the next test. This came from a
  file read that is no longer visible in this conversation and should be re-verified before being
  relied on.

### Outcome

**TESTAUTOMA_2793_015 — not validated.** The fixes were exercised end to end by an actual run: the
popup was found and dismissed, all six criteria were entered, the search executed cleanly, and
`Owner` was located at `(59,722)` with zero scrolls. But the search returned **0 results**, so the
delete was never attempted and the `Has no revisions` assertion was never exercised. The script
now stops with its explicit test-data error. **No run has confirmed that this test passes.**

**TESTAUTOMA_2868 — PASSED**, unchanged, as a control:
`7/27/26, 12:26:19 AM LogSuccess "Has no revisions" is successfully displayed on the screen.`
`7/27/26, 12:26:20 AM EndTestCase (Duration:"358.137", Errors:"0", Exceptions:"19", StartTime:"2026-07-27 00:20:22 +0530", Successes:"31", ...)`
`SUCCESS Execution Time 0:05:58`

No changes were committed. The decision on how to unblock — seed one part owned by SDE-COS, switch
the test to POM-1, or have the test create its own part — was put to Jay and left open.

### What would have made this faster

1. **Run a passing sibling test as a control before diagnosing anything.** 2868 asserts the same
   string and passed in six minutes. Doing that first would have established "the app is fine, the
   message exists, the criteria work, the variable is the user" before any code was touched, and
   would have skipped at least two of the four diagnostic runs.
2. **Put in `context.md`: `Type = "Part"` in Advanced Search also returns Part Master Physical
   Products** (`PRD-*`, and on BST also `PNTX*`, `TESTKPN*`, `*-XXXXX`). Always pin
   `Collaborative Policy = "EC Part"` when the test means a classic Engineering Central part. This
   fact alone is the whole original ticket.
3. **Put in `context.md`: criteria passed to `searchEnovia` must be listed in the order the Advanced
   Search panel draws them, top to bottom,** because `common.scrollTo` only scrolls down. The
   standard block at the top holds Source, Type, Extension, Title, Name, Modification Date, Creation
   Date, Owner; the alphabetical block below holds Collaborative Policy, Is Last Minor Revision,
   Maturity State and the rest. A criterion out of order fails as a not-found label, which
   misdirects into a timing or text-matching investigation.
4. **Put in `context.md`: what the delete refusal messages mean, and that they are ordered gates.**
   `Delete is not applicable for object Type 'Part'` = wrong object type, says nothing about
   ownership. `Context user is not same as the object Owner '<user>'` = right type, wrong owner.
   `Has no revisions` = passed both, this is the assertion target. (Flagged as inferred, see above.)
5. **Fetch the error screenshot immediately whenever a log shows a text-not-found on a panel label
   that the test has previously found successfully.** The log cannot distinguish "the label is not
   there" from "something is on top of the label", and only the screenshot can.
6. **Record, somewhere machine-readable, which user is expected to own test data on which
   environment.** The script's prerequisite comment is prose and names no owner. A refresh silently
   invalidated it and nothing detected that until a search returned zero.

### Notes

- **Nothing was ever deleted.** Every delete attempt across every run was refused by the
  application. This is worth stating to anyone reviewing the runs against a shared environment.
- **The two scripts use different labels for the same field.** TESTAUTOMA_2793_015 passes
  `["001", "Minor Revision"]`; TESTAUTOMA_2868 passes `["001", "Revision"]`. Both were found
  successfully in their respective runs. In the 2868 log, `Revision` triggered a different code path
  in `searchEnovia` — `click at (450, 169)` → `[endKey]` → `scrollwheelup moved 7` → found at
  `(67, 352)` — i.e. it jumps to the bottom of the panel and scrolls *up*, which is the one place
  the downward-only rule does not apply. Do not assume the two labels are interchangeable.
- **`clickHome` contains a typo that disables its own popup guard.** Quoted from this session:
  `watiFor:25` where `waitFor` was intended, meaning the guard checks with no wait. It was observed
  and deliberately not fixed, to avoid changing behaviour for every test in the suite during this
  investigation. UNCERTAIN — the exact spelling comes from a pre-compaction file read and should be
  re-verified before anyone acts on it. Note that in the 2868 control run the popup *was* cleared
  before the Home click anyway (`Access other apps popup found` → `Element Clicked successfully:----  Allow`),
  so the guard worked in practice on that run; which code path produced that log line — the inline
  guard or the new shared handler — is NOT RECORDED.
- In the same 2868 run, the searchEnovia probe logged `No Popup Found - Access other apps`, i.e. two
  different code paths log different wording for the same check. A future agent grepping for one
  string will miss the other.
- **Looked like the cause but was not:** the value of the owner string. `Credentials.json` carries
  `"SDE -COS"` for BST and `"SDE COS"` for threeDTest, and an earlier run on the *old* environment
  typed `"SDE SDE-COS"`, so a per-environment display-name mismatch was a live suspicion for the 0
  results. It was never ruled out definitively — but it is not needed to explain the failure, since
  even without any Owner criterion every classic EC Part in the result set was owned by `TIS`. If
  someone seeds data for SDE-COS and the search still returns 0, this is the first thing to check.
- The Engineering Central suite has **no reusable create-a-part handler** (greps found only
  `ECPartPage.script:130 to ValidateCreatePartNotAvailable` and
  `ECPartPage.script:1573 to createOtherDocumentUnderPart DocName,input,successType:"Success"`).
  Any "make the test self-sufficient" option has to build that from scratch.
- A Jira comment was drafted in this session but **was not posted**. No credentials were disclosed;
  a request for the SDE-COS password was declined and pointed at `Credentials.json`.

---

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
