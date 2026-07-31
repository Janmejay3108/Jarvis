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
| 5 — "Access other apps" popup overlaying the target text | `unhandled_popup_overlay` |

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
