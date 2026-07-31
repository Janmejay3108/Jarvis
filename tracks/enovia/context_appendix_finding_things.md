# Finding things appendix

Use this appendix when the blocker is locating the executed test, provider handler, image, rectangle, resource consumer, URL/path copy, sibling, or prior fix. Commands assume PowerShell at the repository root. Read `context.md` first. `[verified 2026-07-30]`

## Find the test that actually ran

The change-scope ticket number can differ from the script number. The DAI line `Executing Sensetalk snippet TestCases/...` is the primary script identity; Jira `relates to` links are a fallback, not a substitute for the run log. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8278]`

```powershell
rg -n -F 'Executing Sensetalk snippet' <downloaded-run-log>
rg --files Enovia | rg -i 'TESTAUTOMA_6170.*\.script$'
```

The repository currently has both `TestCases` and `Testcases` directory spellings, so use case-insensitive path matching. `[verified 2026-07-30]`

If only a ticket document is available, search all retrospectives before assuming the ticket ID names a source file. `[verified 2026-07-30]`

```powershell
rg -n -i 'TESTAUTOMA-7947|TESTAUTOMA_6170|Executing Sensetalk snippet' ticket_findings_TESTAUTOMA-*.md
```

## JIRA ID to suite

Filename clusters overlap and contain holes, so these are routing hints only; a case-insensitive filename search is authoritative. `[verified 2026-07-30]`

| Suite | Current approximate filename clusters | Evidence |
|---|---|---|
| `3DDashboard` | `2942-2949` | `[verified 2026-07-30]` |
| `BoundaryApps` | `4336-4350` | `[verified 2026-07-30]` |
| `EngineeringCentral` | `2785-2951`, `4078-4231`, `5980`, `6404-6792` | `[verified 2026-07-30]` |
| `LibraryCentral` | `2952-2953`, `6136-6149` | `[verified 2026-07-30]` |
| `M&AFoundational` | `5289-5365` | `[verified 2026-07-30]` |
| `MACS` | `2954-2955`, `4352-4359` | `[verified 2026-07-30]` |
| `MaterialsComplianceCentral` | `2800-2805`, `2956-2974`, `4232-4330`, `5972-5981` | `[verified 2026-07-30]` |
| `MSFIntegration` | `5261-5288` | `[verified 2026-07-30]` |
| `PartMaster` | `6154-6157`, `6162-6180` | `[verified 2026-07-30]` |
| `Performance` | `4360-4363` | `[verified 2026-07-30]` |
| `PLMBridge` | `4364-4385` | `[verified 2026-07-30]` |
| `Search` | `2778-2784`, `2975-2996`, `4386-4410`, `6111-6134` | `[verified 2026-07-30]` |
| `SupplierCentral` | `2777`, `2997-3003`, `4411-4417`, `6190-6256` | `[verified 2026-07-30]` |
| `TeamCenter` | `4421-4422` | `[verified 2026-07-30]` |

```powershell
$id = 6170
Get-ChildItem Enovia -Recurse -File -Filter "TESTAUTOMA_$id*.script" | Select-Object -ExpandProperty FullName
```

## Search identifiers safely

Use case-insensitive search before concluding that a handler, key, image, or rectangle is undefined; capitalization is inconsistent across current SenseTalk callers and providers. `[verified 2026-07-30]`

```powershell
$name = 'TopLeftQuadrant'
rg -n -i -F --glob '*.script' -- $name Enovia
```

## Find every assertion of a message

Search the exact message first, then inspect each call to determine whether it is an assertion, an optional probe, or log text. `[verified 2026-07-30]`

```powershell
$message = "Delete is not applicable for object Type 'Part'"
rg -n -i -F --glob '*.script' -- $message Enovia
rg -n -i 'validateValues|popUpWarning|assertWithScreenshot|isTextPresentInSearchRect' --glob '*.script' Enovia
```

## Run artifacts and counters

Shared `common.CaptureScreenshot` writes timestamped captures to `suiteInfo().resultsFolder`; for a local run this is the executing suite's `Results/` directory, for example `Enovia/EngineeringCentral.suite/Results/`. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]`

```powershell
$suite = 'EngineeringCentral'
Get-ChildItem "Enovia/$suite.suite/Results" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,LastWriteTime
```

DAI run IDs and downloaded artifact locations are supplied by DAI rather than fixed by this repository. Do not assign a DAI run ID to a pasted local log. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]`

`Exceptions` can include failed optional `ImageFound`/text probes. Nonzero Exceptions with zero Errors is therefore possible in a passing run; still require zero fatal Errors/Warnings, a terminal verdict, and the ticket-specific assertion. `[live-run: TESTAUTOMA-7949]` `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8814]`

## Find a handler without choosing the wrong provider

Search declarations and calls separately, then inspect the caller suite's `SuiteInfo.helperSuitesInfo`. A name match in an undeclared suite is not a proven provider; `helpedSuitesInfo` is not the caller dependency list. `[verified 2026-07-30]`

```powershell
$name = 'selectTableViewDropDownOptions'
rg -n -i "^\s*(to\s+(handle\s+)?|on\s+|function\s+)$name\b" --glob '*.script' Enovia
rg -n -i "\b$name\b" --glob '*.script' Enovia
Get-Content 'Enovia/EngineeringCentral.suite/SuiteInfo'
```

SenseTalk multiline comments can contain declaration-looking text. Open each candidate and verify it is executable; use [context_appendix_handlers.md](context_appendix_handlers.md) for the checked shared inventory and duplicate list. `[verified 2026-07-30]`

For a shared-handler edit, list usages before touching the declaration and compare positional order, omitted defaults, and side effects. `[verified 2026-07-30]`

```powershell
rg -n -i '\bselectTableViewDropDownOptions\b' --glob '*.script' Enovia
```

## Find an image or Search Object

Image references commonly omit file extensions. Current suites contain paired `.png` and `.imageinfo` assets plus `.searchobject` files; search the reference, asset path, and `SearchObjectName`. `[verified 2026-07-30]`

```powershell
$term = 'okButton'
rg -n -i $term --glob '*.script' Enovia
rg --files Enovia | rg -i "(^|/)(Images|SearchObjects)/.*$term"
rg -n -i "SearchObjectName.*$term" --glob '*.imageinfo' --glob '*.searchobject' Enovia
```

An `.imageinfo` `CaptureHost` records where an image was captured. It is metadata, not an executable URL or proof that the host is currently required/reachable. `[verified 2026-07-30]`

When an image is missing on screen, distinguish three questions: does the asset exist in the provider suite, is the provider declared to the caller, and is the rendered target visible inside the passed rectangle? `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8450]`

## Find a rectangle or offset

Search the fully qualified key first, then bare-key providers. Do not assume `ConfigEnovia` owns a key merely because many callers use it. `[verified 2026-07-30]`

```powershell
$key = 'validationErrorArea'
rg -n -i "\b$key\b" --glob '*.script' Enovia
rg -n -i '^\s*(to|function)\s+(getSearchRect|ScreenPart|commonScreenPart)\b' --glob '*.script' Enovia
```

Use [context_appendix_rectangles.md](context_appendix_rectangles.md) for current central values, local providers, and the coordinate-type checks. `[verified 2026-07-30]`

## Find a resource key and every executable consumer

Search the key across resources and scripts. URL values are not centralized: current Part Master dashboard URLs live in `PartMaster.json`, while primary environment URLs live in `EnvUrl.json`. `[verified 2026-07-30]`

```powershell
$key = 'BSTURL'
rg -n -i "\b$key\b|partMasterWidget" --glob '*.json' --glob '*.script' Enovia
rg -n -i 'Resource[Pp]ath\s*\(\s*"PartMaster\.json"|JSONValue\s*\(\s*file' --glob '*.script' Enovia
```

Trace all of: resource file, property path, reading handler, caller, selected environment, and the machine that consumes the resolved value. A value found in a resource is not proven active until its consumer is identified. `[verified 2026-07-30]`

Some repository `.json` files use syntax accepted by the suite but rejected by strict JSON parsers. Do not reformat or “repair” an entire file during a one-key change; inspect the SenseTalk consumer and edit surgically. `[live-run: TESTAUTOMA-7949]`

Never print credential-bearing resource values. Search keys and call paths only; refer to credential categories or loader handlers. `[verified 2026-07-30]`

## Current launch target and SUT

`EnvUrl.json.Environment` is currently `bst`; the default `LaunchApp.LaunchURL` call resolves that to `Env.bst.EnoviaURL`, currently `https://3dxspacebst.supplychain.keysight.com/3dspace/nosaml`. Part Master navigation instead reads `PartMaster.json.partMasterWidget.BSTURL`, currently the BST dashboard under `3dxdashboardbst.supplychain.keysight.com`. `[verified 2026-07-30]`

```powershell
rg -n -i '"Environment"|"EnoviaURL"|"DashboardURL"' Enovia/EnoviaCommon.suite/Resources/EnvUrl.json
rg -n -i 'BSTURL|TESTURL|openPartMasterWidget' Enovia/PartMaster.suite
```

The target SUT is the active Eggplant connection and is not selected by `EnvUrl.json`; recorded runs used more than one SUT. Confirm the fresh run's connection metadata or `ConnectionInfo().ServerID` rather than copying an old IP from a ticket. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8450]` `[live-run: TESTAUTOMA-8943]`

```powershell
rg -n -i 'sut_server_id|serverid|connection|SUT|eggplant_data_sync' <downloaded-run-log>
```

## Audit URLs without declaring every old-domain match dead

Start with executable-bearing file types and inspect each match in context. Exclude image/search metadata from the first pass. `[verified 2026-07-30]`

```powershell
rg -n -i 'cos\.is\.keysight\.com|supplychain\.keysight\.com' `
  --glob '*.script' --glob '*.json' --glob '*.apitest' Enovia
```

Classify every match before acting: application URL, API endpoint, SMTP host, TeamCenter/server endpoint, SUT command text, comment/test prose, or capture metadata. Only the historical old BST application host has ticket-backed NXDOMAIN evidence; dev/test, DAP, TeamCenter, SMTP, PLMBridge, and reporting hosts need service-specific checks from their actual consumer machine. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-7949]`

Use the right probe on the right machine. Do not put credentials in commands or output. `[verified 2026-07-30]`

```powershell
Resolve-DnsName <host>
Test-NetConnection <host> -Port <port>
Invoke-WebRequest -Method Head -UseBasicParsing -Uri '<non-secret-url>'
```

DNS resolution, TCP reachability, and application authorization are different checks; record which one was run, where, and when. `[verified 2026-07-30]`

## Find a filesystem path and its machine

Controller-side clues include `ResourcePath`, `JSONValue(file ...)`, SenseTalk `file ... exists`, and Excel data-source records. SUT-side clues include `typeText`, Windows shortcuts, Run-dialog handlers, and commands containing `%USERPROFILE%`. `[verified 2026-07-30]`

```powershell
rg -n -i 'ResourcePath|JSONValue\s*\(\s*file|records of \{type:\s*"excel"|file .* exists' --glob '*.script' Enovia
rg -n -i 'typeText|launchRunWindow|%USERPROFILE%|C:\\Enovia_PreRequisites|\\\\[A-Za-z0-9._$-]+\\' --glob '*.script' --glob '*.json' Enovia
```

For a UNC/local pair, trace the writer and reader independently. Run `Test-Path` on each actual reader machine; a laptop/VPN result does not prove controller or SUT access. `[live-run: TESTAUTOMA-7947]`

```powershell
# Run on the machine whose access is being proved.
$env:COMPUTERNAME
Test-Path '<exact-path-read-by-that-machine>'
```

## UNC inventory and ownership

The current executable `.script`, `.json`, and `.apitest` scan has one UNC host literal: `PartMaster.json.partMasterWidget.TemplatePath = \\EPCORPAPAGENT12\Enovia_PreRequisites\Part Master\`. EPCORPAPAGENT12 is the expected share server; the SUT consumes that path through the browser file picker. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]`

```powershell
$files = Get-ChildItem Enovia -Recurse -File | Where-Object { $_.Extension -in '.script','.json','.apitest' }
$files | Select-String -SimpleMatch '\\' | Where-Object { $_.Line -notmatch '[A-Za-z]:\\\\' }
```

`PartMaster.updateDataIntoNetworkShareDrive` is misnamed: controller-side SenseTalk copies the pre-existing local template, writes a ticket-specific workbook under `C:\Enovia_PreRequisites\Part Master\`, and returns that local path. `uploadPartMasterNetworkShareFile` then types the UNC path so the SUT reads it. `[verified 2026-07-30]`

The base `Mass_Part_BOM_Upload_Template.xlsx`, local directory, and SMB share are environment prerequisites, not repository files. The historical working topology made the Eggplant controller the EPCORPAPAGENT12 serving host; confirm current controller identity and share mapping before assigning remediation to the environment owner. `[live-run: TESTAUTOMA-7947]`

## Find passing siblings

Start from the failing handler and argument pattern, not only neighboring ticket numbers. Siblings can reveal a proven rectangle, optional parameter, criterion order, or postcondition. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8449]` `[live-run: TESTAUTOMA-8450]`

```powershell
$handler = 'uploadPartMasterNetworkShareFile'
rg -n -i "\b$handler\b" --glob '*.script' Enovia
rg --files Enovia | rg -i 'TESTAUTOMA_(6167|6169|6170|6172|6174|6176|6178|6179).*\.script$'
```

Compare: caller suite/provider graph, positional arguments, supplied rectangle, data criteria/order, expected message, cleanup, and whether the sibling actually passed in the same environment. Similar code is not runtime proof. `[verified 2026-07-30]`

## Find git precedent

Search commit subjects by ticket, exact string additions/removals with `-S`, and regex diffs with `-G`. Scope to a path when possible. `[verified 2026-07-30]`

```powershell
git log --all --oneline --decorate --grep='TESTAUTOMA-8943'
git log --all -S 'Create from Spreadsheet' -- Enovia
git log --all -G 'BSTURL|TESTURL' -- Enovia/PartMaster.suite
git show --stat --oneline <sha>
git show <sha> -- <target-path>
git branch -a --contains <sha>
```

Current verified anchors: `[verified 2026-07-30]`

| Commit | Date | Exact subject | Reachability | Evidence |
|---|---|---|---|---|
| `fd30b37a` | 2026-06-17 | `Adding fixes to Urls to switch to any specidied env` | `Testing_Mar10`, `origin/Testing_Mar10` | `[verified 2026-07-30]` |
| `c47ef962` | 2026-06-22 | `Adding changes to Url's` | `Testing_Mar10`, `origin/Testing_Mar10` | `[verified 2026-07-30]` |
| `7f3e3be4` | 2026-06-21 | `Pull request #1061: Added missing "imagefound" to the else if condition.` | `Testing_Mar10`, `origin/Testing_Mar10` | `[verified 2026-07-30]` |
| `b9a9919e` | 2026-07-13 | `Fix Part Master widget dashboard URL to supplychain.keysight.com domain` | `Testing_Mar10`, `origin/Testing_Mar10` | `[verified 2026-07-30]` |
| `92bf151d` | 2026-07-21 | `TESTAUTOMA-8814: exclude Spirent parts from parent part search and fix access popup and part number capture` | `Testing_Mar10`, `origin/Testing_Mar10` | `[verified 2026-07-30]` |

A commit subject is an index, not proof of the implemented behavior. Inspect the diff and current source; later commits may supersede it. `[verified 2026-07-30]`

## Git conventions

As of 2026-07-30 the working branch is `Testing_Mar10`, tracking `origin/Testing_Mar10`; `origin` is the Bitbucket Enovia automation repository. Recent explicit subjects use `TESTAUTOMA-XXXX: <imperative summary>`, while Bitbucket merge commits use `Pull request #NNNN: <subject>`. Older history is inconsistent, so copy the recent explicit form rather than an old `Adding fix...` subject. `[verified 2026-07-30]`

Across the latest 300 commits, 42 non-merge commits had a TESTAUTOMA ID: median two changed files, 35 changed one to three files, all 42 changed a `.script`, seven changed a resource, six changed an image/search asset, and none changed `SuiteInfo`. This is a scope baseline, not permission to exclude a necessary resource or asset. `[verified 2026-07-30]`

The historical ticket-branch form `fix/Testautoma-8449` is recorded, but current remote ticket branches are not retained and no branch-name rule can be proved from current refs. `[live-run: TESTAUTOMA-8449]`

```powershell
git status --short --branch
git remote -v
git log --no-merges -300 --format='%H%x09%s' | Select-String -Pattern 'TESTAUTOMA[-_ ]?\d+'
git show --stat <ticket-commit>
```

Make the ticket commit from an explicit path list. Inspect the resulting diff, push the ticket branch, and let Bitbucket create the PR merge commit; never stage `SuiteInfo` churn merely because opening Eggplant rewrote machine paths. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]`

## Protect the working tree

Check both local dirt and branch-relative changes before editing or staging. `SuiteInfo` often acquires machine-specific path churn when suites are opened. `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]`

```powershell
git status --short --branch
git diff -- <target-path>
git diff origin/Testing_Mar10...HEAD -- <target-path>
git diff -- Enovia/*.suite/SuiteInfo
```

Stage explicit paths only; do not use `git add -A` for a ticket fix in this repository. `[live-run: TESTAUTOMA-7947]` `[live-run: TESTAUTOMA-8278]`