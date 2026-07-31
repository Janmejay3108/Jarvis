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
