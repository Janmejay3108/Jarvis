# `context.md` seed — tribal facts extracted from five solved tickets

Everything here is a fact that **existed nowhere in the codebase, the logs, or the screenshots** when it
was needed, or that was recoverable only by burning a 12–17 minute run. That is the admission test for
this file. Anything derivable from the repo (handler lists, call graphs, search-rectangle tables) should
be **auto-generated nightly instead** — 7947's rule: "stale hand-written copies of derivable data are
what make docs stupid."

Every line carries its provenance ticket. **Verify before acting**: these were true when written
(source documents dated 2026-06-30 to 2026-07-12) and code moves. If a fact names a file, handler or
flag, re-check it still exists before relying on it.

`⚠ UNVERIFIED` marks facts I could not corroborate across more than one source document.

---

## 1. Environment matrix

| Environment | Identifier | Known differences | Source |
|---|---|---|---|
| BST | `156.140.21.48` | Has **no "System Table" saved view**. The `Source` column is **visible by default**, so selecting that view is a means, not the goal — skipping it does not weaken a `Source = "bomloader"` assertion | 8450 |
| BST (new) | `3dxspacebst.supplychain.keysight.com` | Post-migration host. **Saved views did not migrate with the estate** | 8449 |
| BST (old) | `3dxspace23xbst.cos.is.keysight.com` | Dead. Requests to it return `DNS_PROBE_FINISHED_NXDOMAIN` | 7947, 8449 |

**Dated infrastructure events:**

- **2026-06-17** — the BST/TEST estate migrated to `supplychain.keysight.com`, commit **`fd30b37a`**.
  It updated `EnvUrl.json` and **missed `PartMaster.json`**. Grep all suites for stale
  `cos.is.keysight.com` URLs. *(7947 — one line of this would have made an entire run's diagnosis
  instant.)*
- **Commit `c47ef962`** — the "switch env URLs" commit; this is what explains saved views not
  migrating. *(8449)*
- A **BST "refresh"** changed `3dxspace23xbst` → `3dxspacebst` and, as a side effect, **moved the
  3DDashboard app lower in the app list, off-screen** — so selecting it now requires a scroll first.
  *(8278)*
- After a BST refresh, **result ordering changes**: freshly-created parts sort to row 1. This is what
  put a Spirent part at the top of a "Preliminary Part" search. *(8450)*

**Reachability / host topology:**

- PartMaster mass-import requires
  `C:\Enovia_PreRequisites\Part Master\Mass_Part_BOM_Upload_Template.xlsx` **on the controller machine**
  (the machine running Eggplant).
- The **SUT reads that file via `\\EPCORPAPAGENT12\Enovia_PreRequisites\...`**, and the controller is
  expected to **be** that agent host.
- **A laptop over VPN cannot write to that share.** Reverting to the agent share is the resolution, not
  a code change. *(all 7947)*

## 2. Configuration duplication — a standing trap

**`EnvUrl.json` is not the only source of URLs.** Individual suites keep their own hardcoded copies
(`PartMaster.json` holds `BSTURL` and `TESTURL`) which **silently diverge** when the estate moves. This
is what caused an entire wasted run in 7947.

Standing rules:
- On any URL/domain symptom, grep **every** `Resources/*.json` for the old host, not just the global
  config.
- A migration commit's **omissions are a to-do list of stale files** — diff what the commit touched
  against what it should have touched.
- ⚠ UNVERIFIED whether suites other than PartMaster hold duplicate URL keys. Worth a one-off audit.

## 3. Test-data rules and known-bad data

- **Tests pick the FIRST "Preliminary EC Part" in the results.** This selection is
  **non-deterministic** and **refresh-sensitive**. *(8449, 8450)*
- **Spirent parts block BOM and attribute updates** via a server trigger:
  `"Attribute update is not allowed for spirent Part"`, error `#1500167`. *(8450)*
- **A part is Spirent iff its Engineering Responsibility ∈ {SP1, SP2, SP3, SP4}**, and **the parent part
  must not be one.** This is the definitive rule, from the development team (Tanay). *(8450)*
- **EC-Part (a policy) and Spirent (an attribute/trigger) are independent.** A part can be both. Do not
  treat them as alternatives. *(8450)*
- **WebINR-owned parts** are also named as blocked by server triggers. *(8449)*
- Known part identifiers seen in these tickets: `INR-MIIM-002` (**Spirent, blocked**, described in-app
  as `"Testing – Spirent part from WebINR"`); `005146-OSP`, `B1506AU-OC-PRD`, `E7515B-FWS` (normal parts;
  the latter two are the hyphenated ones that OCR misread at DPI 250).
- **A test-data failure is never a code fix.** Diagnose it, name the data rule, and escalate. 8450 spun
  off `ENOVIA3DX-9162` rather than patching.

## 4. Application behaviour that is not in any file

- The **Part Master widget auto-generates the title `Physical Product<EIN>`** when the `TITLE` field in
  the test data is empty. So the text to expect on screen is e.g. `Physical Product00156939`, not a
  literal from the test data. *(7947)*
- **KPN / Enterprise Item Number** is entered on the **Physical Product Information page in Edit mode**,
  in the field **`KEYSIGHT PART NUMBER`** — which feeds the header attribute. The old menu command
  `Set Enterprise Item Number` **was removed from the product**. *(8278 — this single fact was the
  entire ticket; it came from the dev team after 4 rounds of guessing)*
- The **read-only Information panel does not list the Enterprise Item Number field.** That value appears
  **only in the page header**. *(8278)*
- The **Physical Product edit form uses ALL-CAPS attribute labels** — `ICAT`, `MSM FLAG`,
  `LEGACY PART NUMBER`, … A mixed-case label search on that form will never match. *(8278 — discovered
  by a 13-minute full-form scroll)*
- The **Edge download popup is transient and unreliable to OCR.** The slowest of the four EBOM report
  exports finishes **after** the existing validation window expires. *(8448)*

## 5. Log semantics — read this before triaging anything

- **Exceptions ≠ Errors ≠ Warnings.** **29 "Exceptions" appeared in a *passing* run** — they were
  by-design not-found probes. "An agent that treats Exceptions as failures will mis-triage
  constantly." *(8449)*
- **Real logs contain many benign `Unable to Find` lines.** Picking *the* one that matches the failure
  is essential. *(8448)*
- **Read to the FIRST `LogError`/`Throw`, not the last line** — "cascading failures hide the trigger."
  *(8449)*
- **A single logged error flips the whole run's verdict to FAILURE**, even when the test functionally
  passed end to end. *(8278 — a correct fix reported as FAILURE)*
- **Known-flaky steps that must never by themselves fail a fix:** login, the `3DEXPERIENCE` splash, the
  `Run` window. *(8278)*
- **`"line N"` in a handler-scoped error is an offset within the handler, not the file.** *(8450 —
  `"line 68"` = the 68th line of the handler)*
- **The log can be wrong about the world.** Twice in this set the screenshot contradicted it and the
  screenshot was right. *(7947, 8450)*

## 6. Error type → first check

| Error / symptom | First check | Source |
|---|---|---|
| `STInvalidBoolean` | A non-boolean used where a boolean was required — look for an `if`/`else if` whose condition is a bare `{...}` property list | 8449, 8450 |
| `Unable to Find Image (TEXT:...)` then crash | OCR miss **or** the element is genuinely absent. **Get the screenshot** — do not guess | 8450 |
| `No Image Found: Icons/...` | Element not rendered *yet* → timing, add a render wait | 8448 |
| `DNS_PROBE_FINISHED_NXDOMAIN` | Dead host. Confirm instantly with `nslookup`; then grep suites for the stale domain | 7947 |
| `"... not allowed for spirent Part"` | **Data selection, not code** | 8450 |
| Expected text visible on screen but "not found" | Search-rectangle or DPI problem — never an app bug | 7947 |
| Same step fails at the same elapsed time across ≥2 attempts | The **clock** or the **mechanism**, never the value you keep changing | 8448 |

## 7. SenseTalk / house idioms — the "rules of the language as used here"

- **Any image/text check used as an `if`/`while` condition MUST be wrapped in
  `ImageFound()` / `ImageLocation()`.** A bare `{...}` property list in a boolean position is a runtime
  type error (`STInvalidBoolean`). *(8449, 8450 — this one rule would have pre-explained two tickets)*
- **New parameters on shared handlers are optional and default to the old behaviour.** The house idiom:
  ```
  if isMandatory is empty then put "yes" into isMandatory
  ```
  *(8449, 8450)*
- **Original path first, fallback second.** The original behaviour keeps priority; new behaviour is the
  secondary branch (`if`/`else-if` or `try`/`catch`). A human reviewer enforced this on an OCR ladder
  whose rungs were initially ordered otherwise. *(8449 — Jay's stated constraint)*
- **The OCR fallback ladder** as house style:
  ```
  rung 1: DPI:250                           (original, fast, default)
  rung 2: DPI:72  + validWords:<token>      (best for hyphenated tokens)
  rung 3: DPI:250 + validCharacters:<token> (character-level fallback)
  else  : hard error                        (never silently pass)
  ```
  *(8449)*
- **`common.script:validateValues` already contains its own ladder:** plain OCR → DPI 144 + contrast →
  DPI 72 + contrast → fail. The repo's own conventions are the best style guide for a `dpi_cascade`
  fix. *(7947)*
- **Hyphenated part numbers read badly at DPI 250** and cleanly at DPI 72 with `validWords`. *(8449)*
- The standard `try` / `Catch` + `exceptionHandling.errorCapture` pattern is the house error idiom.
  ⚠ UNVERIFIED — named in 8450's recommendations without a worked example.

## 8. The oracle hierarchy — prefer truth over pixels

To verify a side effect, use the **highest-fidelity signal available**:

```
1. filesystem / API / DB          ← ground truth
2. DOM / app-API
3. clipboard / text
4. template-match
5. OCR of live UI                 ← flaky, last resort
```

- **A download's ground truth is the file on disk, not pixels in a popup.** *(8448)*
- **Never validate a transient popup by OCR when a file/log/API oracle exists.** *(8448)*
- **Never validate short or hyphenated tokens** — `.csv` is the recorded example, and four rounds were
  lost to it. *(8448)*
- Before defaulting to more OCR, the agent must answer: **"is there a deterministic oracle for this
  check?"** *(8450)*
- A precedent handler named **`validateDownloadedFileOnDisk`** (PowerShell + clipboard, no OCR) is
  described as already existing in the codebase. ⚠ UNVERIFIED against the repo, and it is unclear
  whether it predates 8448's fix or was created by it — **resolve this before relying on it, because if
  it predates 8448 then repo search alone would have saved four runs.**
- If you shell out to PowerShell with an interpolated filename, **regex-escape it and harden against
  single-quote injection** — both were flagged by code review on 8448.
- **Best-effort degradation is legitimate only when the real assertion still runs.** 8450's fallback
  logs `"continuing with current view"`, presses escape, continues — and the
  `Source = "bomloader"` count check still executes.

## 9. Handler contracts and hazards

| Handler | File | Note |
|---|---|---|
| `enterBOMLoaderValues` | `EngineeringCentral.script` | Site of the `STInvalidBoolean` bug in **both** 8449 and 8450 |
| `selectTableViewDropDownOptions` | `CommonEnovia.script` | Shared. Callers: **2878, 2879, 4100**. Takes optional `isMandatory` (default `"yes"`). **A different handler of the same name exists in `M&AFoundational`** — resolve by suite/scope, never by name alone. Its *purpose* in these tests is to expose the `Source` column, which the name does not convey |
| `clickElement` | `common.script` | **Two definitions exist** (~line 155 and ~line 967). **Logged line numbers resolve against the second.** Any line-number→source mapping must handle this |
| `validateValues` | `common.script` | Has a built-in OCR fallback ladder (see §7) |
| `uploadPartMasterNetworkShareFile` | `PartMaster.script` | **18 call sites.** Passing callers pass `getSearchRect(validationErrorArea)`; the failing ones pass `leftHalf`. Tests **6172** and **6179** still pass the wrong one |
| `enterKPN` | ⚠ file NOT RECORDED | Info → Edit → type → Save. **No fail-fast**: given a non-existent label it scrolls the entire edit form for ~13 minutes before aborting. Every wrong label guess costs a full run |
| `exportBOMreport` | ⚠ file NOT RECORDED | Shared; other caller is test **4105**. Carries an opt-in on-disk download check added by 8448 |
| `common.IsImagePresentOnScreen` | `common.script` (implied by prefix) | The house render-wait primitive — "add `IsImagePresentOnScreen` before export" |
| `assertWithScreenshot` | ⚠ file NOT RECORDED | Appears in 8449's failure chain |
| `open3DDashboard` | ⚠ file NOT RECORDED | Needs a scroll before selecting the app on refreshed BST |

## 10. Search rectangles

- `PartMaster.script` has its **own local `getSearchRect`** (defining `validationErrorArea` and others),
  **separate** from the documented `ConfigEnovia` rectangles. Do not assume `ConfigEnovia` is the only
  source. *(7947)*
- Known values: `validationErrorArea = [45,139,1706,805]` (the broad, correct one);
  `leftHalf = [-25,-10,960,1035]` (right edge x=960 — too narrow for content rendering at x≈1070).
  *(7947)*
- **Rectangle edits in `ConfigEnovia` are high blast radius** — treat as RISK 2 or above, because a
  single rectangle can have dozens of consumers. *(7947)*
- These tables are **auto-derivable — generate them, do not hand-maintain them.**

## 11. Run and verify

- **A SUT run costs 12–17 minutes.** A DAI Practice run is **20 min – 2 hr**. There is **one serialized
  RDP SUT and one EPF license.** Budget accordingly and never spend a run on something lint can catch.
  *(8448, 8449)*
- **Target branch: `Testing_Mar10`.** Commit-message style: minimal, one line. **No co-author trailer.**
  *(8449, 8450)*
- **Build in an isolated `git worktree` off a clean remote base** so unrelated WIP cannot leak into the
  commit. *(8450)*
- **Never `git add -A`.** Recorded working-tree dirt: **17 unrelated `SuiteInfo` files** (7947);
  `SuiteInfo` + `PartMaster.json` drift plus a forbidden `"Type the name"` bypass (8278). Stage the
  explicit file list. *(7947, 8278)*
- **Before opening a PR, `git log origin/Testing_Mar10`** — someone may already have fixed your bug.
  PR **#1061** (commit `7f3e3be4`) independently fixed the same `STInvalidBoolean`. *(8449)*
- **Before applying to a shared handler, re-pull origin and diff the target file** since your run
  started. A colleague pushed to the same handler mid-flight. *(8448)*
- **"Why is this file in my diff?" is answered by branch ancestry, not the working tree.** *(8449)*
- **Confirm the fix actually fired.** Watch for named success markers, not just a PASS:
  `"continuing with current view"`, `"2 is equal to 2 ... Matches count"`, final `PASSED`. "a green
  compile is not a fix; a green RUN that exercises the line is." *(8450)*

## 12. Naming, ticket structure, and sibling families

- Script naming convention: `TESTAUTOMA_<id>_<seq>_<desc>`. *(8449)*
- **The ticket number is not the script number.** "Change Scope" tickets point at *another* ticket's
  script: 7947 → 6170, 8278 → 6157. Get the script name from the **DAI log** (`Executing Sensetalk
  snippet TestCases/...`) and from the Jira **issue links (relates-to)**. *(7947, 8278)*
- Tests carry tags — e.g. `EBOM_Loader`, `EngineeringCentral`, `Regression Test`. Tags are a free
  "find me siblings" key. *(8449)*
- **Known sibling families — fix one, check the others:**
  - `TESTAUTOMA_2878_001` (8449) and `TESTAUTOMA_2879_002` (8450) are the **same bug in the same
    handler**. **4100** shares the step; its status is unknown.
  - Under `uploadPartMasterNetworkShareFile`: **6167 / 6169 / 6174 / 6176 / 6178** pass the correct
    rectangle; **6170 (fixed) / 6172 / 6179** pass the wrong one.
  - `exportBOMreport` is shared between **4109** (8448) and **4105**.

## 13. Prohibitions

1. **Never trade a real assertion for a green checkmark.** "a green test that skipped its assertion is
   worse than a red one — it lies." *(8449)*
2. **Never commit the `"Type the name"` bypass.** It exists locally, it makes runs green, it is
   forbidden. *(8278)*
3. **Never patch correct code to mask an environment problem** — "creates a landmine." *(7947)*
4. **Never change a shared handler's existing behaviour** — additive, default-preserving only.
   *(8449, 8450, 8448)*
5. **Never patch a `test_data` or `application_bug` finding.** Diagnose and escalate. `TESTAUTOMA_4348`
   (server down) is named as one that must never get a code patch. *(8450)*
6. **Never assert what the evidence cannot settle.** The diagnosis must explain the log **and** the
   screenshot **and** the timeline; any unexplained or contradicting signal drops confidence and
   triggers escalation. *(8450)*
7. **Do not re-litigate human review feedback** — accept and re-apply. *(8449)*

## 14. Maintenance rules for this file

From 7947 and 8449, the conditions under which this file stays useful rather than becoming the doc
nobody reads:

1. **Only non-derivable facts.** Anything computable from the repo is generated nightly instead.
2. **Every entry dated, one paragraph, with provenance** (commit sha, run id, ticket) and a
   **falsifiable** claim someone can re-verify.
3. **Written at resolution time**, when the lesson is fresh, via a human-approved suggestion flow —
   agent drafts, human accepts.
4. **Pruned at review.** Entries older than N months without re-confirmation get challenged. Cap total
   size (~5K tokens) so it can be prompt-cached whole.
5. **Verified on recall.** Before acting on a fact that names a file, handler or flag, re-check it still
   exists.
6. **Cite entries in diagnoses**, so stale ones get noticed and killed.
7. **Capture loop:** whenever a human supplies a domain rule mid-run, propose an addition here. "The
   back-and-forth then costs ONCE per rule, not once per ticket." *(8450)*

**Categories that earn a place here:** environment/infra facts and dated migration events; topology and
reachability; per-suite prerequisite gotchas; test-data rules; app behaviour; log semantics; house
idioms; decisions-with-reasons (e.g. *why* the template path must stay `EPCORPAPAGENT12`).

**Categories that do not:** per-ticket narratives (that is the trajectory log / the per-ticket records
in this directory), code structure, call graphs, handler inventories, search-rectangle tables — all
generated.
