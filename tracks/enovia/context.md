# Enovia Eggplant context: wrong-turn prevention

Generated and source-verified on 2026-07-30. Re-run each dated check before trusting volatile values. [verified 2026-07-30]

Use this file before diagnosing or changing the Enovia Eggplant suites. It is intentionally a routing guide, not a repository encyclopedia. Load an appendix only when its trigger applies. [verified 2026-07-30]

## Contents

| Need | Go to |
|---|---|
| Start or triage | [If you read nothing else](#if-you-read-nothing-else), [First five minutes](#first-five-minutes), [Triage by symptom](#triage-by-symptom) |
| Machine, suite, or handler ownership | [Runtime and machine boundaries](#runtime-and-machine-boundaries), [Suite and handler resolution](#suite-and-handler-resolution) |
| Environment, data, or oracle | [Environment, config, and data](#environment-config-and-data), [Oracle order](#oracle-order) |
| Repository, execution, or new tests | [Repository map](#repository-map), [Running and writing a test](#running-and-writing-a-test) |
| Detailed lookup | [Appendix triggers](#appendix-triggers), [Self-test quick index](#self-test-quick-index), [Maintenance](#maintenance) |

## If you read nothing else

1. Open the run log first; `Executing Sensetalk snippet TestCases/...` identifies the executed script. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8278]
2. Open the failure screenshot before code for every UI lookup failure; visible SUT state outranks the text log. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450]
3. Open the executed test, then only its directly called handler and one passing sibling before searching wider. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8833]
4. Classify each blocker as code/config, environment/infra, test data, product/change scope, or flaky oracle before proposing a patch. [live-run: TESTAUTOMA-8450]
5. Visible outside the applied rectangle means containment; visible inside means recognition settings; absent means page state, timing, data, environment, or product flow. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8449]
6. One ticket can reveal sequential independent blockers; a later new signature does not disprove an earlier demonstrated fix. [live-run: TESTAUTOMA-7947]
7. The recurring root-cause classes in the nine records are code/config defects, environment drift/overlays, and non-qualifying or missing test data. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8833]
8. Prefer file/API/MQL/stable state over transient OCR; change the oracle mechanism before tuning the token it failed to read. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8943]
9. Never weaken an assertion, widen an unproved rectangle, or patch script code to mask an environment/data/product fault. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8450]
10. Load an appendix only through its trigger below; handler, message, rectangle, lookup, and ticket details are intentionally outside this cached core. [verified 2026-07-30]

## Evidence contract

- `[verified 2026-07-30]` means the current repository was checked on that date. Re-check before acting if the named file, handler, resource key, or suite has changed. [verified 2026-07-30]
- `[live-run: TESTAUTOMA-XXXX]` means the claim was observed in a recorded Eggplant/DAI run or its failure screenshot; it may describe an older code revision or environment state. [verified 2026-07-30]
- `[UNVERIFIED — check: <exact command>]` means the sources did not settle the claim. Run the command from the machine named by the claim; do not silently promote it to fact. [verified 2026-07-30]
- Current source outranks old retrospectives for current code shape. A live run outranks source for what actually happened in that run. A screenshot outranks a text log for what was visible on the SUT. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450]
- Never copy passwords, access keys, tokens, or credential values into prompts, comments, logs, commits, or this document. Refer to the resource key and credential-loading handler only. [verified 2026-07-30]

## First five minutes

1. Identify the executed script from `Executing Sensetalk snippet TestCases/...` in the run log; the change-scope ticket number may differ from the script number. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8278] [live-run: TESTAUTOMA-7949]
2. Record the original failure signature: first fatal step, first `LogError` or `Throw`, handler chain, elapsed time, SUT ID, environment, and the exact missing text/image or exception type. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8449]
3. For every UI or text-lookup failure, obtain the screenshot from the moment of failure before changing code. Answer: is the target visible, and is it inside the rectangle used by the failing call? [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8814] [live-run: TESTAUTOMA-8833] [live-run: TESTAUTOMA-8943]
4. Classify the blocker before localizing it: `CODE-LOGIC`, `CONFIG`, `ENVIRONMENT/INFRA`, `TEST-DATA`, `PRODUCT/CHANGE-SCOPE`, or `FLAKY-ORACLE`. Low confidence is a stop condition, not permission to patch. [live-run: TESTAUTOMA-8450]
5. Read only the failing script, the directly called handler, and a passing sibling or call site. Compare arguments and control flow before inventing a fix. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8833]

## Self-test quick index

| # | Answer or fastest route |
|---:|---|
| 1 | The default login currently resolves `Environment=bst` to `https://3dxspacebst.supplychain.keysight.com/3dspace/nosaml`; Part Master uses its own current BST dashboard URL. The SUT is the active Eggplant connection, not an `EnvUrl.json` value. Re-check both with the commands in [Current launch target and SUT](context_appendix_finding_things.md#current-launch-target-and-sut). [verified 2026-07-30] |
| 2 | `searchEnovia "advancedSearch"` traverses criteria in caller order through downward-default `scrollTo`; pass labels in top-to-bottom panel order. Treat Revision's special branch separately. [verified 2026-07-30] |
| 3 | `Delete is not applicable for object Type 'Part'` identified a selected Part Master Physical Product, a data-selection mismatch. Add/verify `Collaborative Policy = EC Part`, inspect the row, then use control test `TESTAUTOMA_2868`; do not patch the product refusal. [live-run: TESTAUTOMA-8833] |
| 4 | Local captures are under the executing suite's `Results/` via `suiteInfo().resultsFolder`; nonzero Exceptions with zero Errors can be optional failed probes, so read the first fatal error and final assertion. See [Run artifacts and counters](context_appendix_finding_things.md#run-artifacts-and-counters). [verified 2026-07-30] [live-run: TESTAUTOMA-8449] |
| 5 | Put generic shared behavior in a provider suite such as Common and Enovia-specific behavior in EnoviaCommon; there is no undeclared global scope. The caller must list the provider in `SuiteInfo.helperSuitesInfo`; EngineeringCentral currently lists both. [verified 2026-07-30] |
| 6 | Run unchanged `TESTAUTOMA_2868_010_PartsWithOneRevisionCanNotBeDeletedWithPOMRole` as the known control for the part-deletion revision rule. [verified 2026-07-30] [live-run: TESTAUTOMA-8833] |
| 7 | First suspect a missing saved view and missing/non-owned qualifying fixture. If the required column/assertion still works without the view, it is view drift; if semantically correct search returns zero while control `2868` passes, it is a fixture/ownership gap. [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8833] |
| 8 | Load the finding appendix and run [Find every assertion of a message](context_appendix_finding_things.md#find-every-assertion-of-a-message). [verified 2026-07-30] |
| 9 | Recent non-merge ticket fixes have median two files and usually change scripts; use `TESTAUTOMA-XXXX: <imperative summary>` for the recent explicit form. See [Git conventions](context_appendix_finding_things.md#git-conventions). [verified 2026-07-30] |
| 10 | `popUpWarning` can exit before clicking OK when validation fails; `waitForNativeAlert` observes without dismissing; failed `dismissNativeAlert` exits with the alert still modal. Load [Dirty UI on failure](context_appendix_messages.md#dirty-ui-on-failure). [verified 2026-07-30] [live-run: TESTAUTOMA-8833] |
| 11 | The Part Master base template must be pre-provisioned on the controller/serving agent and is not in git; test setup copies/edits it locally, then the SUT reads the generated file through the agent-host UNC share. [verified 2026-07-30] [live-run: TESTAUTOMA-7947] |
| 12 | Search every executable declaration and inspect all bodies. Duplicate-body precedence in the repository's Eggplant version is unverified; do not infer any precedence from source order or log line numbers. [verified 2026-07-30] |
| 13 | Search every resource and consumer. Main URLs live in `EnvUrl.json`; the confirmed shadow is `PartMaster.json.partMasterWidget.BSTURL/TESTURL`, read by `PartMaster.openPartMasterWidget`. [verified 2026-07-30] [live-run: TESTAUTOMA-7949] |
| 14 | Run equivalent control `2868` unchanged. If it reaches the rule while the target's semantically filtered search has zero qualifying rows, diagnose data/ownership, not application change. [live-run: TESTAUTOMA-8833] |
| 15 | Use case-insensitive declaration and usage searches before declaring an identifier undefined; run [Search identifiers safely](context_appendix_finding_things.md#search-identifiers-safely). [verified 2026-07-30] |
| 16 | Measure two possibilities: the target is outside the actual caller rectangle, or it is inside but the DPI/word/character recognition rung cannot read it. Prove containment from the screenshot before changing either. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8449] |
| 17 | Read `Executing Sensetalk snippet` in the DAI log; if unavailable, follow Jira issue links (`7947 -> 6170`, `8278 -> 6157`) and search case-insensitively. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8278] |
| 18 | Replace transient popup OCR with the highest deterministic side effect available: file, API/database/MQL, stable field, or durable row. The tempting wrong fix is changing tokens, DPI, or timeout while retaining the weak oracle. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8943] |
| 19 | The current executable UNC inventory has one host literal: `PartMaster.json.TemplatePath` under `\\EPCORPAPAGENT12\Enovia_PreRequisites\Part Master\`; EPCORPAPAGENT12 serves it and the SUT reads it. Re-run [UNC inventory and ownership](context_appendix_finding_things.md#unc-inventory-and-ownership). [verified 2026-07-30] [live-run: TESTAUTOMA-7947] |

## Hard stops

- Do not patch script code to mask an environment, reachability, missing-prerequisite, test-data, or product-change problem. Produce a diagnosis and the exact remediation owner/action instead. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8833]
- Do not weaken, skip, or replace the business assertion merely to make a run green. A fallback is acceptable only when the original assertion still executes. [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8450]
- Do not tune OCR when the target is absent from the failure screenshot. Route to timing, overlay, workflow change, environment, or test data. [live-run: TESTAUTOMA-8278] [live-run: TESTAUTOMA-8833] [live-run: TESTAUTOMA-8943]
- Do not use a transient popup, short token, hyphenated token, or browser-painted button as the oracle when a file, API, MQL result, clipboard value, stable field label, or dialog heading can prove the state. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8943]
- Do not treat a new failure after a fix as proof that the fix failed. Compare the new signature with the original and reclassify it independently. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8814] [live-run: TESTAUTOMA-8943]
- Do not commit `SuiteInfo` path churn or unrelated workspace changes. Stage an explicit file list; never use `git add -A` in this repository. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-7949] [live-run: TESTAUTOMA-8278] [live-run: TESTAUTOMA-8814]
- Do not commit a bypass of the Run-dialog `Type the name` check. It can hide SUT state failures and was explicitly rejected during TESTAUTOMA-8278. [live-run: TESTAUTOMA-8278]

## Runtime and machine boundaries

- Eggplant Functional runs SenseTalk on the controller and drives a remote Windows SUT through image/OCR operations. All fixed rectangles assume a connected `1920 x 1080` remote screen; `common.checkSUTconnected` enforces that size. [verified 2026-07-30]
- UI actions such as `typeText`, `click`, `ImageFound`, `readText`, Windows-key shortcuts, and commands typed into the Run dialog execute against the SUT. [verified 2026-07-30]
- SenseTalk `file`, `JSONValue(file ...)`, `ResourcePath`, and Excel data-source operations read from the controller-side suite unless the handler explicitly types a filesystem command into the SUT. [verified 2026-07-30]
- `%USERPROFILE%\Downloads` in a command typed through `LaunchApp.launchRunWindow` refers to the SUT user's Downloads directory. [verified 2026-07-30]
- `LaunchApp.launchURL` reads `EnvUrl.json` on the controller, then types the resolved browser command and URL into the SUT Run dialog. The configured browser is launched InPrivate, so browser permission state is not durable across runs. [verified 2026-07-30] [live-run: TESTAUTOMA-8814]
- A path probe is valid only from the machine that will read the path. Controller-side `Test-Path` does not prove SUT reachability, and a laptop/VPN probe does not prove agent-host reachability. [live-run: TESTAUTOMA-7947]

### Known Part Master topology

- Mass-import data is generated or read at `C:\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx` on the Eggplant controller, while the SUT workflow accesses the corresponding UNC path under `\\EPCORPAPAGENT12\Enovia_PreRequisites\...`. [live-run: TESTAUTOMA-7947]
- The historical resolution required the controller to be the serving agent host; a laptop over VPN could not write to that share. Treat this as dated topology, not a universal invariant. [live-run: TESTAUTOMA-7947]
- Current controller identity, share definition, and both access directions are not stored in git. [UNVERIFIED — check: `$env:COMPUTERNAME; Get-SmbShare -Name Enovia_PreRequisites; Test-Path 'C:\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx'`]
- SUT-to-share reachability must be checked on the SUT, for example by typing this through the SUT Run dialog or PowerShell: [UNVERIFIED — check: `Test-Path '\\EPCORPAPAGENT12\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx'`]

## Suite and handler resolution

- A suite can call providers declared in that caller suite's `SuiteInfo.helperSuitesInfo`. For example, EngineeringCentral currently lists Common, EnoviaCommon, and Search as helpers. [verified 2026-07-30]
- `SuiteInfo.helpedSuitesInfo` contains machine-specific absolute paths and is frequently rewritten when suites are opened. It is not the dependency list to edit for a missing provider. [verified 2026-07-30]
- Resolve handlers by provider suite plus script plus handler name. Name-only search is unsafe because collisions exist across suites and duplicate definitions exist within scripts. [verified 2026-07-30]
- Before changing a shared handler, enumerate every call site and compare positional arguments, omitted defaults, expected side effects, and suite dependencies. Prefer an optional, default-preserving addition. [verified 2026-07-30] [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8450]
- Current duplicate definitions and signatures are in [context_appendix_handlers.md](context_appendix_handlers.md). Load it when a log names a handler, a line number looks wrong, or a shared handler is being changed. [verified 2026-07-30]

## Triage by symptom

### Text or image not found

1. Fetch the failure screenshot. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8450]
2. If the target is visible outside the search rectangle, use a proven sibling rectangle or a stable anchor-relative rectangle; do not loosen OCR. [live-run: TESTAUTOMA-7947]
3. If it is visible inside the rectangle, compare the repository's existing OCR ladder and the exact rendering. Preserve the original rung first, then add fallbacks. [live-run: TESTAUTOMA-8449]
4. If it is not visible, inspect overlays, navigation, page state, timing, environment, data selection, and product changes. [live-run: TESTAUTOMA-8278] [live-run: TESTAUTOMA-8833] [live-run: TESTAUTOMA-8943]
5. If the error names content but the handler also navigates, verify the preceding URL and page state. `PartMaster.openPartMasterWidget` reported missing page text when its suite-local URL was stale. [live-run: TESTAUTOMA-7949]

### Boolean or parameter runtime errors

- `STInvalidBoolean` usually means a property list or other non-boolean was used directly in an `if`/`while`; wrap image/text probes in `ImageFound()` or another boolean-producing call. [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8450]
- SenseTalk calls in this codebase are positional. `handler waitToAppear:10` passes a property list in the first position; it does not bind the named handler parameter and can produce `STInvalidNumber`. [live-run: TESTAUTOMA-8943]
- Misspelled command properties can silently lose intended behavior. A historical `watiFor` in `clickHome` was fixed; the current source uses `waitFor`. [live-run: TESTAUTOMA-8814] [verified 2026-07-30]

### Same message, different cause

- Treat generic assertion messages as observations, not diagnoses. `Validating BOM Loader Process ... FAIL` meant both a Spirent server-trigger refusal and an empty Parent Assembly Name in separate runs. [live-run: TESTAUTOMA-8814]
- Read to the first fatal `LogError`/`Throw`; later failures may be cascading effects. Benign `Unable to Find` entries and nonzero exception counts can occur in passing runs because optional probes log misses. [live-run: TESTAUTOMA-7949] [live-run: TESTAUTOMA-8449]
- If two attempts fail at the same step and nearly the same elapsed time, suspect the timeout or oracle mechanism before changing the searched value again. [live-run: TESTAUTOMA-8448]

## Shared contracts that change diagnosis

- `common.scrollTo` defaults to downward scrolling and hard-fails after 10 unsuccessful loops. Advanced Search criteria therefore need to be supplied in top-to-bottom panel order unless the special Revision path deliberately jumps and scrolls up. [verified 2026-07-30] [live-run: TESTAUTOMA-8833]
- `common.waitForTextToDisappear` succeeds when the text is absent from the first probe; it does not prove an observed present-to-absent transition. Use a stable field label and establish presence separately when the transition matters. [verified 2026-07-30] [live-run: TESTAUTOMA-8943]
- `commonEnovia.searchEnovia "advancedSearch"` mutates the `Is Last Revision` label into an image lookup, special-cases Revision, and traverses criteria in caller order. [verified 2026-07-30]
- `commonEnovia.clickHome` currently checks the intermittent `Access other apps` permission popup, attempts Home navigation, checks again on failure, and retries navigation once. [verified 2026-07-30]
- `commonEnovia.dismissNativeAlert`, `waitForNativeAlert`, and `nativeAlertIsOnScreen` use positional arguments. Detection uses the stable `"<host> says"` heading; dismissal prefers the image and falls back to Return because button theme/hover rendering is unstable. [verified 2026-07-30] [live-run: TESTAUTOMA-8943]
- `exceptionHandling.errorCapture` is terminal: it captures/logs the error and exits all. A nested handler calling it does not return control to its caller. [verified 2026-07-30]
- Exact handler signatures, hidden side effects, collisions, and current duplicate bodies are in [context_appendix_handlers.md](context_appendix_handlers.md). [verified 2026-07-30]

## Environment, config, and data

- URL values are not centralized. `EnvUrl.json` is the main environment resource, but suite-local resources can shadow it; the confirmed example is `PartMaster.json.partMasterWidget.BSTURL/TESTURL`. On domain failures, search all resource files for the old and new host. [verified 2026-07-30] [live-run: TESTAUTOMA-7949]
- A migration commit's omissions are evidence: compare every old-host consumer against the files changed by the migration. `fd30b37a` updated central URLs but missed the Part Master copy. [live-run: TESTAUTOMA-7949]
- Do not strict-format or wholesale rewrite resource files merely because a parser rejects them. Some `.json` resources use syntax tolerated by SenseTalk but rejected by strict JSON parsers. Edit the exact key surgically. [live-run: TESTAUTOMA-7949]
- Advanced Search `Type = Part` can include Part Master Physical Products. When the test requires a classic Engineering Central part, constrain `Collaborative Policy = EC Part` and verify the selected row's semantics. [live-run: TESTAUTOMA-8833]
- A part with Engineering Responsibility `SP1` through `SP4` is Spirent and is blocked from BOM/attribute updates by a server trigger; `EC Part` policy and Spirent status are independent. Filter for a proven non-Spirent responsibility such as `02` when the test will mutate the part. [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8814]
- Fresh environments can lack saved table views or user-owned fixtures. Preserve the business assertion while tolerating an optional view only if the required column is still validated; stop with a test-data diagnosis when no qualifying object exists. [live-run: TESTAUTOMA-8450] [live-run: TESTAUTOMA-8833]

## Repository map

| Suite | Decision-relevant ownership | Evidence |
|---|---|---|
| `Common.suite` | Generic UI, OCR, screen geometry, reporting, and terminal exception primitives. | [verified 2026-07-30] |
| `EnoviaCommon.suite` | Shared Enovia login/navigation, search, files/credentials, MQL, browser launch, and environment URL handling. | [verified 2026-07-30] |
| `Search.suite` | Shared search-result geometry, row/column selection, tags, and favorite search behavior. | [verified 2026-07-30] |
| `3DDashboard.suite` | Dashboard creation, search, sharing, and widget flows. | [verified 2026-07-30] |
| `BoundaryApps.suite` | Boundary/integration application and server-facing flows. | [verified 2026-07-30] |
| `EngineeringCentral.suite` | EC Part, BOM, change, route, document, and report workflows. | [verified 2026-07-30] |
| `LibraryCentral.suite` | Library, class, document, and credentials-role workflows. | [verified 2026-07-30] |
| `M&AFoundational.suite` | Foundational company, drawing, part/MEP, material declaration, and compliance flows. | [verified 2026-07-30] |
| `MACS.suite` | Agreement item and MACS report workflows. | [verified 2026-07-30] |
| `MaterialsComplianceCentral.suite` | MEP, MDR, SEM, substance, import, and compliance workflows. | [verified 2026-07-30] |
| `MSFIntegration.suite` | Document/file and MSF integration workflows. | [verified 2026-07-30] |
| `PartMaster.suite` | Physical Product, Part Master widget, Engineering Release, and mass-import workflows. | [verified 2026-07-30] |
| `Performance.suite` | Performance-specific test flows. | [verified 2026-07-30] |
| `PLMBridge.suite` | PLM extract/file-transfer workflows using PuTTY/WinSCP helpers. | [verified 2026-07-30] |
| `SupplierCentral.suite` | Supplier, supplier responsibility, package, and mass-add workflows. | [verified 2026-07-30] |
| `TeamCenter.suite` | TeamCenter integration workflows. | [verified 2026-07-30] |
| `CustomReport.suite` | DAI/custom report APIs, collection, and report generation; it has no test-case inventory. | [verified 2026-07-30] |

Tests live under both `Scripts/TestCases/` and `Scripts/Testcases/`; always search paths case-insensitively. Approximate ID clusters and the authoritative lookup command are in [JIRA ID to suite](context_appendix_finding_things.md#jira-id-to-suite). [verified 2026-07-30]

## Running and writing a test

- No repository `.ps1`, `.bat`, `.cmd`, `.sh`, or CI workflow defines the authoritative single-test launcher. Select the exact suite script in the team's Eggplant Functional/DAI mechanism and record the externally selected SUT; do not infer either from `SuiteInfo.Schedules`. [verified 2026-07-30]
- A recorded SUT run normally costs 12-17 minutes and DAI validation 20 minutes to two hours; static declaration/caller checks belong before either. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8449]
- Start from a nearby passing test in the same suite. Current tests commonly use a metadata header, `#Testdata`, `BeginTestCase`, `try/Catch`, `failedHandlerNavigation(callStack())`, terminal `errorCapture`, and matching `EndTestCase`. [verified 2026-07-30]

```sensetalk
(***
@TestCaseName: TESTAUTOMA_NNNN_Name
@Description: <business behavior>
@Author: <owner>
@JiraID: <ticket URL>
***)
#Testdata
BeginTestCase "TESTAUTOMA_NNNN_Name"
try
	//Step 1 - <business step>
Catch theException
	"exceptionHandling".failedHandlerNavigation(callStack())
	"exceptionHandling".errorCapture theException
end try
EndTestCase "TESTAUTOMA_NNNN_Name"
```

- Header and marker spelling is inconsistent; no current script matches `@modified By: TESTAUTOMA-XXXX`. Preserve the nearest suite convention and put the ticket ID in the test name/Jira field and git subject rather than inventing a universal header. [verified 2026-07-30]
- Existing step comments mostly narrate what the step does. Add a short why-comment only for hidden ordering, machine-boundary, fallback, or cleanup constraints that a future edit could otherwise break. [verified 2026-07-30]

## Oracle order

Prefer the highest available signal: [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8943]

1. Filesystem, API, database, or MQL result. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8943]
2. Stable application state or field label. [live-run: TESTAUTOMA-8943]
3. Clipboard or text value. [live-run: TESTAUTOMA-8814]
4. Stable image template. [live-run: TESTAUTOMA-8943]
5. OCR of live or transient UI. [live-run: TESTAUTOMA-8448]

Before adding OCR tuning, answer: `What deterministic side effect would prove this operation?` [live-run: TESTAUTOMA-8448]

## Retry ledger and validation

For each attempt record: hypothesis, change, original signature, new signature, failure elapsed time, SUT/environment, whether the changed line executed, and whether the previous fix held. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8450]

- Different new signature: retain a demonstrated fix, classify the new blocker from scratch, and reset the per-blocker reasoning. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-8814]
- Same signature and elapsed time: stop substituting values; inspect timing and oracle mechanics. [live-run: TESTAUTOMA-8448]
- Green run without proof the changed branch executed: insufficient. Require a branch-specific log marker or observed side effect plus the final business assertion. [live-run: TESTAUTOMA-8450]
- Original signature gone but an unrelated known environment flake appears: report both facts; do not absorb the flake into the ticket fix. [live-run: TESTAUTOMA-8278]
- A run may pass with many logged Exceptions from optional probes. Final Errors/Warnings, the terminal verdict, and the ticket-specific assertion are the relevant signals. [live-run: TESTAUTOMA-7949] [live-run: TESTAUTOMA-8814]

## Change risk

- Risk 0: one caller/test change. Validate the named test and compare passing sibling arguments. [live-run: TESTAUTOMA-7947]
- Risk 1: suite-local handler. Enumerate suite callers and validate affected flows. [verified 2026-07-30]
- Risk 2: shared handler or shared rectangle. Enumerate all callers, preserve defaults, and run representative callers from different suites or behavior branches. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8449] [live-run: TESTAUTOMA-8814]
- Risk 3: shared resources/environment keys. Enumerate every consumer of the exact key and every duplicate copy before changing it. [live-run: TESTAUTOMA-7947] [live-run: TESTAUTOMA-7949]
- Re-read the target file and remote branch before applying a shared-handler fix; another contributor changed a shared export handler during TESTAUTOMA-8448, and an independent fix already existed during TESTAUTOMA-8449. [live-run: TESTAUTOMA-8448] [live-run: TESTAUTOMA-8449]

## Appendix triggers

- Load [context_appendix_handlers.md](context_appendix_handlers.md) when a handler name, signature, default, duplicate, collision, or call path controls the diagnosis. [verified 2026-07-30]
- Load [context_appendix_messages.md](context_appendix_messages.md) when interpreting a log/error string, exception type, alert text, or generic assertion. [verified 2026-07-30]
- Load [context_appendix_rectangles.md](context_appendix_rectangles.md) only after the failure screenshot shows the target is visible, or when changing a rectangle/offset. [verified 2026-07-30]
- Load [context_appendix_finding_things.md](context_appendix_finding_things.md) when locating a script, provider suite, image, resource consumer, URL copy, UNC path, sibling, or git precedent. [verified 2026-07-30]
- Load [context_appendix_ticket_learnings.md](context_appendix_ticket_learnings.md) when a current signature resembles a solved ticket or a second blocker appears after a fix. [verified 2026-07-30]

## Maintenance

- Keep this core under 600 lines and focused on routing decisions. Move volatile inventories and exhaustive tables to appendices. [verified 2026-07-30]
- Every factual or operational claim must carry one of the evidence markers defined above. [verified 2026-07-30]
- Re-verify current-source facts after changes to Common, EnoviaCommon, Search, SuiteInfo, or Resources. [verified 2026-07-30]
- Preserve uncertainty. Replace an `[UNVERIFIED]` marker only with the command result, date, machine, and direction that were actually checked. [verified 2026-07-30]
- **A change to this file is not complete until `scripts/run_eval.py` has been re-run and the score has not regressed.** This is the review gate for the context set, and it is binding: this document is prompt-cached into *every* diagnosis call, so a wrong claim here degrades every diagnosis silently and without raising an error. A measured check is the only kind that catches that. See plan0 B.4 action 6 and plan1 §1.7.1. [verified 2026-07-30]

Re-check volatile facts without printing credential values: [verified 2026-07-30]

```powershell
git status --short --branch
Select-String -Path 'Enovia/EnoviaCommon.suite/Resources/EnvUrl.json','Enovia/PartMaster.suite/Resources/PartMaster.json' -Pattern '"Environment"|"EnoviaURL"|"BSTURL"|"TESTURL"'
Select-String -Path '<recent-run-log>' -Pattern 'sut_server_id|ServerID|connection|SUT|eggplant_data_sync'
$credentialObject = Get-Content 'Enovia/EnoviaCommon.suite/Resources/Credentials.json' -Raw | ConvertFrom-Json
$credentialObject.PSObject.Properties.Name
Select-String -Path 'Enovia/*.suite/SuiteInfo' -Pattern 'helperSuitesInfo'
```