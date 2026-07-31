# Ticket-learning appendix

Use this appendix when a new signature resembles one of the nine retrospectives or when a fix reveals a second blocker. These are historical run facts, not promises about current code or environment state. Read `context.md` first. `[verified 2026-07-30]`

## How to use history safely

- Match on the executed script, first fatal signature, screenshot state, handler chain, and elapsed time; never match on ticket number or final error text alone. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8814]`
- A historical code shape must be checked against current source. A historical live run remains evidence for that run even when the source later changes. `[verified 2026-07-30]`
- Preserve split verdicts: a ticket-specific fix can be proven while the full run fails later, and a diagnosis can be correct when the environment lacks data needed to pass. `[live-run: TESTAUTOMA-8278]` `[live-run: TESTAUTOMA-8833]` `[live-run: TESTAUTOMA-8943]`

## Quick index

| Ticket -> executed test | Entry signature | Cause class | Historical outcome | Evidence |
|---|---|---|---|---|
| `7947 -> TESTAUTOMA_6170_PartMasterWidgetPassTest` | `Physical Product` not found, then later `Create from Spreadsheet` not found | Blocker chain: rectangle hypothesis/config/environment/topology/intermittent overlay | One complete local pass proved URL/rectangle changes did no harm and environment actions worked; a later popup failure remained. | `[live-run: TESTAUTOMA-7947]` |
| `7949 -> TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget` | `Create from Spreadsheet` not found on a DNS error page | Stale suite-local config | Local end-to-end pass; later run reached the fixed widget and failed downstream in Downloads. | `[live-run: TESTAUTOMA-7949]` |
| `8278 -> TESTAUTOMA_6157_NewPhysicalProductFreezeFlow` | Removed `Set Enterprise Item Number` command not found | Product/change-scope plus unrelated navigation/launch blockers | Ticket flow functionally passed; overall run reported FAILURE because of unrelated launch OCR logging. | `[live-run: TESTAUTOMA-8278]` |
| `8448 -> TESTAUTOMA_4109_RT008_ValidatetheEBOMReportExporttoExcel` | Repeated popup OCR token misses near the same timeout | Missing render wait plus flaky oracle and timeout race | Green locally and independently green in DAI; merged. | `[live-run: TESTAUTOMA-8448]` |
| `8449 -> TESTAUTOMA_2878_001_AgilentPipeDelimitedCollapsed` | `STInvalidBoolean` property-list fingerprint, then OCR/view issues | Code logic, OCR ladder, environment-specific optional view | Previously failing assertions passed on re-run and changes merged; formal run ID/zero-error verdict not recorded. | `[live-run: TESTAUTOMA-8449]` |
| `8450 -> TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded` | `STInvalidBoolean`, missing `System Table`, then Spirent trigger | Code logic, optional environment view, test-data selection | DAI run `34708` passed with 0 errors/warnings and changed branches observed; Spirent data issue was not code-fixed. | `[live-run: TESTAUTOMA-8450]` |
| `8814 -> TESTAUTOMA_2879_002_AgilentPipeDelimitedExpanded` | Generic BOM Loader failure, late permission popup, then blank parent part | Broad selection, popup timing, hardcoded capture coordinate | Final local run passed all steps with 0 errors/warnings; current history contains commit `92bf151d`. | `[live-run: TESTAUTOMA-8814]` `[verified 2026-07-30]` |
| `8833 -> TESTAUTOMA_2793_015_PartNotBeAllowedToBeDeletedIfItsTheFirstRevision` | `Has no revisions` not displayed | Broad object-type search, then no qualifying user-owned data | Target test did not pass and no change was committed; unchanged control test `2868` passed the same assertion. | `[live-run: TESTAUTOMA-8833]` |
| `8943 -> TESTAUTOMA_4336_RT001` | `Create New MEP` did not disappear; native alert visible in screenshot | Modal alert plus elided panel title; later unrelated DMS transaction blocker | One local run passed; run `36469` exercised the fix and failed later because the expected MQL object was absent. | `[live-run: TESTAUTOMA-8943]` |

## TESTAUTOMA-7947: Part Master blocker chain

- **Decisive evidence:** the first failure screenshot showed import success (`Imported Items (1)` and a created Physical Product), while another screenshot showed an old-host DNS error and the final failure showed the late permission popup. `[live-run: TESTAUTOMA-7947]`
- **Cause chain:** caller rectangle difference; stale Part Master dashboard URLs; missing controller template; controller/SUT share topology; intermittent `Access other apps` overlay. Each became visible only after the prior blocker cleared. `[live-run: TESTAUTOMA-7947]`
- **Validated action:** local run 6 passed all five steps after the rectangle/URL changes and environment remediation. The target was found at x=696, inside the old `leftHalf`, so the pass proves no regression but does not prove the rectangle caused run 1. `[live-run: TESTAUTOMA-7947]`
- **Unvalidated action:** the Part Master popup handler had no post-change run in that conversation. Current source contains it, but historical reasoning is not runtime proof. `[live-run: TESTAUTOMA-7947]` `[verified 2026-07-30]`
- **Stop rule:** when the signature changes, retain a demonstrated earlier fix and reclassify the new blocker. Do not spend a code retry on missing files, wrong host topology, or share reachability. `[live-run: TESTAUTOMA-7947]`
- **Latent siblings:** the retrospective reports `6172` and `6179` still used `leftHalf`; re-check current source before acting. `[live-run: TESTAUTOMA-7947]`

## TESTAUTOMA-7949: stale suite-local URL

- **Decisive evidence:** the screenshot showed `DNS_PROBE_FINISHED_NXDOMAIN`; git history showed `fd30b37a` migrated central URLs but omitted `PartMaster.json`. `[live-run: TESTAUTOMA-7949]`
- **Action:** update only `partMasterWidget.BSTURL/TESTURL`; local run typed the new BST URL, found `Create from Spreadsheet`, and completed with 0 errors/warnings. Only BST was runtime-tested. `[live-run: TESTAUTOMA-7949]`
- **Later blocker:** run `36197` reached and used the fixed widget, then failed in `openFromDownloads`; its proposed Excel/Downloads explanation was not validated and is a separate issue. `[live-run: TESTAUTOMA-7949]`
- **Current source:** `PartMaster.json` now contains supplychain dashboard hosts, and `b9a9919e` is reachable from `Testing_Mar10`; do not describe that file as currently stale. `[verified 2026-07-30]`
- **Stop rule:** on a URL symptom, compare every suite-local copy with the migration diff before changing OCR or waits. Do not strict-format the non-strict resource as collateral work. `[live-run: TESTAUTOMA-7949]`

## TESTAUTOMA-8278: product workflow changed

- **Decisive evidence:** the old `Set Enterprise Item Number` command was removed; a domain owner supplied the replacement workflow. KPN is entered as `KEYSIGHT PART NUMBER` on the Physical Product Information page in Edit mode, and the read-only panel does not expose that field. `[live-run: TESTAUTOMA-8278]`
- **Action:** use `PartMaster.enterKPN` with the all-caps field label; a later blocker required scrolling to the moved dashboard app. `[live-run: TESTAUTOMA-8278]`
- **Outcome:** the ticket flow passed end to end, but an unrelated launch-timing OCR error logged an Error and made the run verdict FAILURE. The commit's merge status was not recorded. `[live-run: TESTAUTOMA-8278]`
- **Current source:** test `6157` uses `enterKPN(...,"KEYSIGHT PART NUMBER")`; comments document the removed command. `[verified 2026-07-30]`
- **Stop rule:** when a change-scope ticket depends on a replacement UI fact absent from code/logs/screenshots, ask one targeted domain question. Never commit the local bypass of the Run-dialog `Type the name` check. `[live-run: TESTAUTOMA-8278]`

## TESTAUTOMA-8448: replace the oracle

- **Decisive evidence:** four different OCR token guesses failed at the same step and near the same elapsed time, while screenshots/files showed the download behavior. The invariant was the timeout/mechanism, not the token. `[live-run: TESTAUTOMA-8448]`
- **Cause chain:** toolbar not rendered; transient Edge download popup was a poor OCR surface; the slowest report completed just after the validation window. `[live-run: TESTAUTOMA-8448]`
- **Action:** add a render wait and an opt-in on-disk CSV check while preserving the shared handler's old default for other callers. `[live-run: TESTAUTOMA-8448]`
- **Outcome:** green locally and independently green in DAI on different data/environment, 0 errors/warnings; merged. `[live-run: TESTAUTOMA-8448]`
- **Current source:** `EngineeringCentral.exportBOMreport(...,validateOnDisk:"No")` retains the default and calls `validateDownloadedFileOnDisk` only when opted in; test `4109` opts in for the fragile/slow reports. `[verified 2026-07-30]`
- **Stop rule:** after two same-time failures, propose a mechanism change. Prefer file/API state over OCR of a transient popup, and inspect all uses of the replaced mechanism in the test. `[live-run: TESTAUTOMA-8448]`

## TESTAUTOMA-8449: decompose one ticket

- **Decisive evidence:** `STInvalidBoolean` included a property-list value, pointing to a bare image description in boolean control flow. Separate failures involved hyphenated OCR and a saved view absent on refreshed BST. `[live-run: TESTAUTOMA-8449]`
- **Action:** wrap the condition in `ImageFound`; add the original-first DPI/valid-word fallback ladder; make table-view selection optional without skipping the downstream `Source` assertion. `[live-run: TESTAUTOMA-8449]`
- **Outcome:** fresh logs showed the prior assertions passing and the changes merged, but no run ID or explicit whole-test 0-error verdict was recorded. PR `#1061` / `7f3e3be4` independently fixed the same boolean defect. `[live-run: TESTAUTOMA-8449]` `[verified 2026-07-30]`
- **Current source:** `enterBOMLoaderValues` uses `ImageFound` for each OCR rung, and `CommonEnovia.selectTableViewDropDownOptions(option,isMandatory)` preserves mandatory behavior unless callers opt out. `[verified 2026-07-30]`
- **Stop rule:** `STInvalidBoolean` is a type/control-flow route, not an OCR route. Check sibling tests `2879` and `4100`, then current branch history, before duplicating a fix. `[live-run: TESTAUTOMA-8449]`

## TESTAUTOMA-8450: code fix plus honest non-fix

- **Decisive evidence:** the same boolean fingerprint as 8449; environment evidence that `System Table` was absent while `Source` remained visible; screenshot/run comparison showing a selected Spirent part hit trigger `#1500167`. `[live-run: TESTAUTOMA-8450]`
- **Action:** fix the boolean expression and optional-view flow; retain the required `Source = bomloader` assertion. Do not code-patch the Spirent server refusal; select valid data or escalate. `[live-run: TESTAUTOMA-8450]`
- **Outcome:** fail run `34649`; final DAI run `34708` passed with 0 errors/warnings, emitted `continuing with current view`, exercised the count assertion, and used a non-Spirent part. The data issue was split to `ENOVIA3DX-9162`. `[live-run: TESTAUTOMA-8450]`
- **Stop rule:** decompose code, environment, and test-data blockers. A correct diagnosis-only outcome is preferable to weakening the assertion or masking a product trigger. `[live-run: TESTAUTOMA-8450]`

## TESTAUTOMA-8814: one generic message, three causes

- **Decisive evidence:** screenshots exposed the Spirent trigger and later empty Parent Assembly Name; logs showed the permission popup arrived after the initial check and a hardcoded triple-click captured no part number after search criteria narrowed. `[live-run: TESTAUTOMA-8814]`
- **Action:** constrain Engineering Responsibility to a qualifying non-Spirent value; make `clickHome` dismiss/retry the permission popup; replace fixed-coordinate part capture with text-relative capture. `[live-run: TESTAUTOMA-8814]`
- **Outcome:** final local run passed through cleanup with 0 errors/warnings and logged each changed branch. Commit `92bf151d` and its merge are on current `Testing_Mar10`. `[live-run: TESTAUTOMA-8814]` `[verified 2026-07-30]`
- **Current source:** `clickHome` checks the popup, retries once, and uses `waitFor`; current test data/filtering must still be inspected before assuming every part-mutation test excludes Spirent data. `[verified 2026-07-30]`
- **Stop rule:** `Validating BOM Loader Process ... FAIL` means the success banner was absent. Read the visible error and entered field state; it does not diagnose the loader. `[live-run: TESTAUTOMA-8814]`

## TESTAUTOMA-8833: diagnosis without a pass

- **Decisive evidence:** row-specific refusals split wrong Physical Product type from wrong owner; adding semantic criteria then produced zero results. Unchanged control test `2868` reached and passed `Has no revisions`. `[live-run: TESTAUTOMA-8833]`
- **Cause chain:** `Type = Part` admitted Part Master Physical Products; after filtering for classic EC parts, the execution user owned no qualifying data in refreshed BST. Criterion order also interacted with downward-only scrolling. `[live-run: TESTAUTOMA-8833]`
- **Outcome:** the target test never attempted a successful delete path, did not pass, and no change was committed. Data seeding/user/fixture strategy remained open. `[live-run: TESTAUTOMA-8833]`
- **Current source:** test `2793` still searches by Type, Owner, Maturity State, and Minor Revision without a Collaborative Policy criterion; do not assume the retrospective's diagnostic edits persist. `[verified 2026-07-30]`
- **Stop rule:** run a truly equivalent passing control early. If valid semantic filtering returns zero rows, stop patching and report the exact missing fixture/ownership requirement. `[live-run: TESTAUTOMA-8833]`

## TESTAUTOMA-8943: native alert, false pass, downstream blocker

- **Decisive evidence:** the failure screenshot showed a browser-native `Object Find Limit (1) Reached` alert blocking page JavaScript; long object names elided `Create New MEP` to `Create New M...`. `[live-run: TESTAUTOMA-8943]`
- **Action:** poll for native alerts via the stable `says` heading, dismiss image-first with Return fallback, and use the stable `Part Name` field to observe panel closure. `[live-run: TESTAUTOMA-8943]`
- **Outcome:** a 7/17 local run passed with 0 errors/warnings. In run `36469`, all alert/panel fixes executed and the MEP was visible, but final MQL lookup returned no transaction object; whether timing or product/environment failure remained unresolved. `[live-run: TESTAUTOMA-8943]`
- **Current source:** shared native-alert handlers and `Part Name` panel checks are present. `common.scrollTo` remains direction-specific/down-by-default; the retrospective's reverse-scan idea was never runtime-validated. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8943]`
- **Stop rule:** do not add a retry to a missing durable transaction record until delayed creation is observed; otherwise a wait can mask a genuine integration failure. `[live-run: TESTAUTOMA-8943]`

`[UNVERIFIED — check: on the BST execution path, query the current ticket-specific MEP transaction object immediately after creation and at controlled intervals; record whether the object appears late or never appears before changing the final MQL assertion]`

## Cross-ticket patterns

| Pattern | Tickets | Routing rule | Evidence |
|---|---|---|---|
| Same message, different causes | 7947, 8814 | Error text is low fidelity; compare screenshot, first fatal handler, preceding action, and timeline. | `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8814]` |
| Sequential blocker chain | 7947, 8448, 8814, 8943 | Preserve proven earlier fixes; reset diagnosis and retry budget when the signature changes. | `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8448]` `[live-run: TESTAUTOMA-8814]` `[live-run: TESTAUTOMA-8943]` |
| First-row/data-order sensitivity | 8450, 8814, 8833 | Constrain semantic type/ownership/responsibility and validate the selected row before mutation. | `[live-run: TESTAUTOMA-8450]` `[live-run: TESTAUTOMA-8814]` `[live-run: TESTAUTOMA-8833]` |
| Optional UI step, mandatory assertion | 8449, 8450 | A missing view may be tolerated only when the required column/business assertion still runs. | `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8450]` |
| Runtime verdict differs from ticket verdict | 8278, 8943 | Compare against the original signature and changed-branch markers; classify later failures independently. | `[live-run: TESTAUTOMA-8278]` `[live-run: TESTAUTOMA-8943]` |
| Passing run with many Exceptions | 7949, 8449, 8814 | Optional not-found probes can increment Exceptions; require 0 Errors/Warnings and terminal/ticket assertions. | `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8814]` |
| Passing sibling as control | 7947, 8449, 8450, 8833 | Compare arguments/preconditions or run the sibling unchanged before blaming the shared handler. | `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8450]` `[live-run: TESTAUTOMA-8833]` |

## Runtime ID ledger

| Ticket | Recorded run IDs | Meaning | Evidence |
|---|---|---|---|
| `7947` | `31996`, `35531`; intermediate/local pass had no ID | Original and later popup-chain runs; do not assign IDs to pasted local logs. | `[live-run: TESTAUTOMA-7947]` |
| `7949` | `35255`, later `36197`; validating local pass had no ID | Original stale-URL failure and later unrelated Downloads failure. | `[live-run: TESTAUTOMA-7949]` |
| `8278` | not recorded | Use failure signature and R1-R7 labels, not an invented ID. | `[live-run: TESTAUTOMA-8278]` |
| `8448` | not recorded | Local and DAI validation are described, but no ID is recorded. | `[live-run: TESTAUTOMA-8448]` |
| `8449` | not recorded | Do not borrow `34649/34708` from sibling ticket 8450. | `[live-run: TESTAUTOMA-8449]` |
| `8450` | `34649` fail, `34708` pass | Final pass exercised the intended branches. | `[live-run: TESTAUTOMA-8450]` |
| `8814` | `34649` original; later local runs had no ID | Same numeric run appears in related retrospective context; identify by ticket/script/timestamp too. | `[live-run: TESTAUTOMA-8814]` |
| `8833` | not recorded | Control/target logs had timestamps but no run ID. | `[live-run: TESTAUTOMA-8833]` |
| `8943` | `35365` original, `36469` later downstream failure | The successful 7/17 local run had no recorded DAI ID. | `[live-run: TESTAUTOMA-8943]` |