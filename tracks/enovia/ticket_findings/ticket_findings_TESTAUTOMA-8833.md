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
