# Message and oracle appendix

Use this appendix when a run reports missing text, an alert, `STInvalid*`, a generic assertion, or many `Unable to Find`/Exception entries. Read `context.md` first. `[verified 2026-07-30]`

## First rule: a message is an observation

- A missing string identifies the failed oracle, not its cause. Inspect the first fatal call, screenshot, rectangle, page URL/state, and preceding action before classifying it. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8814]`
- Optional probes can emit `Unable to Find` and Exceptions during passing runs. Use the first fatal `LogError`/`Throw`, final Errors/Warnings, terminal verdict, and ticket assertion. `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8449]`
- When the screenshot contradicts the text log about what was visible, trust the screenshot for visible SUT state. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8450]`

## High-value current-source oracles

| String or pattern | Qualified consumer | Match and effect | Do not conclude | Better evidence | Evidence |
|---|---|---|---|---|---|
| `Create from Spreadsheet` | `PartMaster.openPartMasterWidget -> common.validateValues` | OCR/text gate after typing the suite-local dashboard URL; failure is fatal through shared error handling. | Do not conclude the widget label changed or OCR is bad. The same miss has occurred on a DNS error page and under an overlay. | Capture the failure screen; inspect the typed URL and host; check for the permission popup; only then inspect rectangle/OCR. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]` |
| `Physical Product` | Part Master import callers of `uploadPartMasterNetworkShareFile` | Post-import text validation in a caller-supplied rectangle. | Do not conclude import failed. One failure screen showed `Imported Items (1)` and the created product outside the failing interpretation. | Use the import result/count and created-item row; verify the actual found coordinates against the supplied rectangle. | `[live-run: TESTAUTOMA-7947]` |
| `Imported Items` | Part Master import-result flow | OCR text in the result panel; current source uses it with `validWords` in import validation. | Presence alone does not prove the expected row or count. | Read and compare the count plus the expected created item. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]` |
| `Log out` | `CommonEnovia.loginEnovia` | Authentication/page gate in a fixed search rectangle with a 30-second wait. | Do not use it to prove the requested app or downstream page loaded. | Validate the next page's stable state after login. | `[verified 2026-07-30]` |
| `Tasks` | Common callers of `CommonEnovia.clickHome` | Caller-selected Home-page expectation; `clickHome` now checks the permission popup and retries navigation once. | Do not conclude Home navigation is broken until checking for overlays. | Inspect the popup and top bar, then use a page-specific expectation rectangle. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]` |
| `No Result found` | `CommonEnovia.searchEnovia` branches | Text probe used to distinguish empty search results. | Do not conclude the query is semantically correct or that matching rows do not exist elsewhere. | Record search criteria/order; inspect result headers/count and selected-row semantics. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8833]` |
| `Loading` | `CommonEnovia.waitForLoading` and related loaders | Polling synchronization text. | Disappearance does not prove the target page or operation succeeded. | Follow with the stable post-load field, row, heading, file, or API result. | `[verified 2026-07-30]` |
| `Part Name` | current MEP create flows | Stable field label used to prove the Create New MEP panel is present or has closed. | Do not restore the full panel title as the oracle; long titles are elided. | Keep the field-label gate and separately validate the created MEP/result state. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8943]` |
| `Your BOM file was processed successfully with no errors` | `EngineeringCentral.enterBOMLoaderValues` and `ECPartPage` BOM loader flow | Business success assertion in `caApprovalPopup`, wrapped by `assertWithScreenshot`. | Its absence does not identify the cause; recorded causes include a blocked Spirent update and an empty required field. | Read the visible alert/error and verify parent selection plus entered Parent Assembly Name. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]` |
| `Has no revisions` | tests `2793`, `2868`, `4078`, and `4086` | Expected delete refusal; validation is via `validateValues`, `popUpWarning`, or a guarded text check. | Do not conclude revision behavior was reached if an earlier type or ownership gate refused deletion. | Verify `Collaborative Policy = EC Part`, last/minor revision criteria, owner, then the final alert. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8833]` |
| `continuing with current view` | `CommonEnovia.selectTableViewDropDownOptions` | Branch marker when an optional table view is absent; the workflow continues. | This marker is not a pass by itself. | Require the downstream required-column/business assertion and final verdict. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8450]` |

## Native alerts and permission popups

| Visible text / invariant | Current handling | Wrong-turn warning | Evidence |
|---|---|---|---|
| `Access other apps ...` and `Allow` | `CommonEnovia.handleAccessOtherAppsPopup(waitTime:5)` and `PartMaster.handleAccessOtherAppsPopup()` look for the stable partial text in the top-left quadrant, then click `Allow`; absence is non-fatal. | Two provider scripts define the handler name. Qualify the intended provider, and allow for delayed appearance. InPrivate launch means a prior run does not establish current popup state. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8814]` `[live-run: TESTAUTOMA-8833]` |
| `<host> says` | `CommonEnovia.nativeAlertIsOnScreen` returns whether `readText(popupRectangle,dpi:144) contains "says"`. | This detects browser-native alert modality, not a particular alert body or root cause. | `[verified 2026-07-30]` |
| `Object Find Limit (n) Reached` | Current MEP paths call `dismissNativeAlert`; the handler waits, detects via `says`, tries `icons/okButton`, then falls back to Return. | Do not infer that only `n` rows loaded. A recorded run had six rows with the warning. The blocking modality matters; the message content did not explain the test result. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8943]` |
| Browser-painted `OK` | `dismissNativeAlert` uses image-first and keyboard fallback, then checks whether an alert remains. | Native modal dimming and theme/hover rendering can make the image disappear while the alert remains. Never use the button image as the sole presence oracle. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8943]` |

Current positional signatures: `[verified 2026-07-30]`

```text
CommonEnovia.dismissNativeAlert waitToAppear, popupRectangle, attempts
CommonEnovia.waitForNativeAlert popupRectangle, waitToAppear
CommonEnovia.nativeAlertIsOnScreen popupRectangle:configEnovia().SearchRectangles.PopUpWarning
CommonEnovia.handleAccessOtherAppsPopup waitTime:5
PartMaster.handleAccessOtherAppsPopup
```

Do not call `dismissNativeAlert waitToAppear:10`; in this codebase that syntax supplies a property list in the first positional argument and can lead to `STInvalidNumber`. `[live-run: TESTAUTOMA-8943]`

## Dirty UI on failure

| Shared handler/path | Dirty-state risk | Required caller behavior | Evidence |
|---|---|---|---|
| `CommonEnovia.popUpWarning` | It validates before clicking `icons/okButton`. If validation throws, its catch routes to terminal `errorCapture`; the alert is not dismissed and can block the next test. | When the exact message is uncertain or rows are being classified, read the alert, dismiss it on every branch, then assert the diagnosis separately. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8833]` |
| `CommonEnovia.waitForNativeAlert` / `nativeAlertIsOnScreen` | These are observation-only and intentionally leave the modal alert open. | Pair a positive result with `dismissNativeAlert` in success, mismatch, and exception paths. | `[verified 2026-07-30]` |
| `CommonEnovia.dismissNativeAlert` | It retries image/Return dismissal, but if the alert survives all attempts it raises a terminal error while the modal remains. | Treat this as environment/UI cleanup failure; do not continue page interaction or reinterpret subsequent image misses. | `[verified 2026-07-30]` |

`exceptionHandling.errorCapture` performs `exit all`; cleanup written after the failing shared call will not execute. Put mandatory alert/popup cleanup before that terminal path or in a structure guaranteed to execute. `[verified 2026-07-30]`

## Runtime-only diagnostic messages

These messages are useful classifiers only in the recorded context. They are not universal mappings. `[verified 2026-07-30]`

| Recorded message | What it proved in that run | Next check | Evidence |
|---|---|---|---|
| `DNS_PROBE_FINISHED_NXDOMAIN` | The SUT displayed a DNS failure for the old Part Master dashboard host. | `Resolve-DnsName <host>` on the SUT, then trace every executable URL consumer; do not generalize to all hosts in the old domain. | `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]` |
| `Attribute update is not allowed for spirent Part` with `#1500167` | A server trigger refused an update to a selected Spirent part. | Inspect Engineering Responsibility; `SP1` through `SP4` identify Spirent data in the recorded environment. Select qualifying data rather than weakening the assertion. | `[live-run: TESTAUTOMA-8450]` `[live-run: TESTAUTOMA-8814]` |
| `Please input the name of the parent assembly that you are loading` | The BOM Loader required field was blank when validation ran. | Verify the field accepted the typed value before waiting for BOM success. | `[live-run: TESTAUTOMA-8814]` |
| `Delete is not applicable for object Type 'Part'` | The selected search row was a Part Master Physical Product, so deletion stopped before revision logic. | Add/verify `Collaborative Policy = EC Part` and inspect the selected row type. | `[live-run: TESTAUTOMA-8833]` |
| `Context user is not same as the object Owner 'TIS'` | A later candidate reached the ownership gate and was not owned by the execution user. | Select an object owned by the execution user or use the intended credential set; do not patch the product refusal. | `[live-run: TESTAUTOMA-8833]` |
| `STInvalidBoolean` | Recorded callers used a non-boolean property list directly in boolean control flow. | Inspect the failing `if`/`while`; wrap image/text descriptions in `ImageFound()` or another boolean-producing operation. | `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8450]` |
| `STInvalidNumber` | A name/value property list occupied a positional numeric parameter in a native-alert call. | Compare the call against the exact positional signature. | `[live-run: TESTAUTOMA-8943]` |

## Shared message-helper semantics

| Qualified signature | Outcome and hidden risk | Evidence |
|---|---|---|
| `common.Success(SuccessMsg)` | Logs success and captures a screenshot. It has two executable declarations; duplicate-body precedence is unverified. | `[verified 2026-07-30]` |
| `common.Error(ErrorMsg,isthrow)` | Logs/captures and conditionally throws according to `isthrow`. It has two executable declarations; inspect both bodies. | `[verified 2026-07-30]` |
| `common.LogException(Exception,HandlerName)` | Logs exception context, captures, and throws. It has two executable declarations. | `[verified 2026-07-30]` |
| `common.validateValues(values,SR:[0,0,1920,1080],pageWait:120)` | Two executable bodies exist, including a richer OCR ladder. Failure routes through shared error behavior; body selection is unverified. | `[verified 2026-07-30]` |
| `common.validateTextAndLogMsg(textBoxText,waitTime,rectSearch,isthrow,validationMsg)` | Tries plain OCR, then `validCharacters`; despite the `isthrow` parameter, the current failure branch calls `common.error ... ,yes`. | `[verified 2026-07-30]` |
| `common.waitForTextToDisappear(textToWaitFor,rectSearch,waitTime)` | Proves absence at the end, not an observed present-to-absent transition; it can pass if text was absent from the first probe. | `[verified 2026-07-30]` |
| `CommonEnovia.popUpWarning(message,clearMessage:"yes",popupRectangle:...)` | Validates through `common.validateValues`; `yes` dismisses, `warningMsg` logs without dismissal, and other values call fatal shared error handling. | `[verified 2026-07-30]` |
| `CommonEnovia.assertWithScreenshot(actualValue,expectedValue,validation)` | Compares values and reports the caller's generic validation label; that label may hide the upstream product/data cause. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]` |
| `exceptionHandling.errorCapture(errorMessage,handlerName)` | Terminal: captures/logs and performs `exit all`; no normal return to nested callers. | `[verified 2026-07-30]` |

For exact declarations, duplicates, and provider collisions, use [context_appendix_handlers.md](context_appendix_handlers.md). `[verified 2026-07-30]`

## Oracle replacement test

Before adding OCR settings or changing expected text, answer all four: `[verified 2026-07-30]`

1. Was the target visible in the failure screenshot? `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8450]`
2. Was it inside the actual rectangle passed by this caller? `[live-run: TESTAUTOMA-7947]`
3. Is the text a business state, or merely a navigation/loading proxy? `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8814]`
4. Can a file, API/MQL result, stable field, clipboard value, or durable row prove the same state? `[live-run: TESTAUTOMA-8448]` `[live-run: TESTAUTOMA-8943]`