# PHASE 0.A — POC EXECUTION GUIDE (super-detailed, step-by-step)

> Companion to `plan0_poc_and_foundation.md`. The plan says *what* each PoC must
> prove and its DoD; **this guide says exactly where to do it, what to click,
> what command to run, what a good result looks like, and the traps to avoid.**
> Research-backed (Eggplant DAI/EPF docs, Bitbucket DC REST, Jira DC REST,
> ripgrep) and grounded in what we already proved on the real Keysight services.
>
> **Golden ticket:** `TESTAUTOMA-8055` · **its DAI runid:** `30832`
> (the `34156` in earlier examples was an illustrative log sample, not 8055's run).

---

## 0. ORIENTATION — machines, accounts, and who runs what

### 0.1 The three machines (know which one you're on for every step)

| Tag | Machine | Address | Spec | Role |
|---|---|---|---|---|
| **[LAPTOP]** | your dev laptop | — | — | Writing code, running the pure-API PoCs (DAI/Jira/Bitbucket/Claude). Must be on Keysight network/VPN to reach `*.it.keysight.com` and `*.cos.is.keysight.com`. |
| **[ORCH]** | Orchestrator VM | `aiagent-testmanager.cos.is.keysight.com` (156.140.21.109) | 4 CPU / 32 GB | Where the agent will eventually run. PoC 6 (Claude-from-VM) and Gate-0b smoke run here. |
| **[RUNNER]** | EPF runner VM | `eggptdai10.cos.is.keysight.com` (156.140.21.30) | 4 CPU / 16 GB | Has Eggplant Functional + `runscript.bat` + the floating license + the RDP SUT. PoC 1 / 1b / 1e run here. |

> Most API PoCs (2, 2b, 4, 5, 6) can be developed and first-run from **[LAPTOP]**
> as long as you're on the corporate network. The plan requires PoC 6 and the
> Gate-0b smoke to also be proven **from [ORCH]** (egress matters there).

### 0.2 Accounts / secrets you'll need (all into `.env`, never committed)

| Secret | Where it comes from | Used by PoC |
|---|---|---|
| `JIRA_PAT` | Jira → profile → Personal Access Tokens | 5, 2 |
| `BITBUCKET_PAT` | Bitbucket → Manage account → Personal access tokens (scopes: Repo R/W, PR R/W, Branch create) | 4, 1 |
| `DAI_CLIENT_ID` / `DAI_CLIENT_SECRET` | DAI UI → **System → API Access → New API Access** → download the `.csv` | 2, 2b |
| `ANTHROPIC_API_KEY` | Keysight AI gateway project key | 6, 2, 5 |
| EPF floating license | License admin reserves **one** seat for the agent | 1, 1b, 1e |

### 0.3 Status legend used below

- ✅ **DONE** — already proven this session.
- 🔶 **PARTIAL** — partly proven; finish noted.
- ⬜ **TODO** — not started; needs (User) infra/credentials.

### 0.4 One-time laptop setup (do before any PoC)

```powershell
# from the project root: C:\Users\janmtiwa\Desktop\Initiative Latest\ai-test-fix-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-poc.txt          # httpx anthropic openai pyyaml python-dotenv rich
Copy-Item .env.example .env                   # then fill secrets in .env (never commit)
```

**Critical gotcha (cost us hours):** every script must call
`load_dotenv(override=True)`. Without `override=True`, a parent shell that
already exports `ANTHROPIC_BASE_URL` (IDEs, Agent sessions) silently masks your
`.env` and your Anthropic calls go to the wrong base URL → misleading
`401 invalid x-api-key`. Already fixed in our scripts; keep it for any new one.

**Model gotcha:** the Keysight gateway whitelists `claude-opus-4-5` and
`claude-opus-4-7` but **not** `claude-opus-4-6` (a 4-6 request returns a
misleading 401). We use `claude-opus-4-7`.

---

## PoC 2 — DAI evidence by `runid`  (Step A.1)  ✅ DONE

**Proves:** from a Jira ticket you can reach the failing run's error log and the
exact error screenshot, using only the runid + the DAI APIs + LLM reasoning.

**Where:** [LAPTOP] · **Script:** `scripts/poc_dai.py`

### The pipeline (already implemented & proven)
1. `GET {JIRA_BASE_URL}/rest/api/2/issue/TESTAUTOMA-8055`  (header `Authorization: Bearer {JIRA_PAT}`)
2. **LLM extract** `{runid, title, description, test_script_name}` from the whole response (any field, any casing).
3. **DAI auth** — `POST {DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token`
   body `grant_type=client_credentials&client_id=…&client_secret=…` → `access_token` (Bearer, ~5 min TTL).
4. `GET {DAI_BASE_URL}/ai/runlogs/{runid}` → `{"items":[LogEntry…],"total_count":N,"date_as_of":…}`.
5. **LLM match** the single `items[i]` whose `message` matches the ticket's failure.
6. **Deterministic walk-back** from `i` to the nearest prior entry with non-null `image_id`.
7. `GET {DAI_BASE_URL}/api/v2/screenshots/{image_id}` → save PNG.

### Run it
```powershell
.\.venv\Scripts\python.exe scripts\poc_dai.py TESTAUTOMA-8055
# DAI-only (skip Jira+LLM, for quick endpoint checks):
.\.venv\Scripts\python.exe scripts\poc_dai.py TESTAUTOMA-8055 --runid 30832
```

### Expected (proven) result
```
runid=30832 · test_script=TESTAUTOMA_2941_113_ValidateHeaderConnection... ·
402 log entries · error_index 384 ("Unable to Find Image (TEXT:\"Released\")…") ·
image_id 465c0ecf-7f18-5a0a-77a1-092d06e18785 · 111,914-byte PNG saved to
data/poc2_evidence/
```

### Gotchas
- **Response is wrapped in `items[]`**, not a bare list — parse `payload["items"]`.
- **Severity is not a failure filter** — the real error is `severity:INFORMATIONAL`, `message_type:imagefound`. Match on `message` semantics, not severity.
- **`--runid` fallback intentionally picks the wrong entry** (first image-find failure = the Login screen) to demonstrate why the LLM step is needed.
- `verify=False` on httpx is used because the DAI host is plain HTTP on :8000; if it were HTTPS-with-internal-CA you'd add `--ca-cert-path`/trust the CA instead.

### DoD ✅
Endpoints + response shape recorded in `poc_results.md` A.1; screenshot on disk.
*Remaining tidy-up:* the old debug images `TESTAUTOMA-8055_manual.png` and
`…runid-34156…png` in `data/poc2_evidence/` are stale — only the
`…runid-30832…` image is the correct 8055 evidence; delete the other two.

---

## PoC 2b — The JARVIS validation path end-to-end  (Step A.2)  ✅ **PROVEN**

**Proves:** the validation mechanism — push the candidate to the **validation
repo** `agentic-eggplant-automation` branch **`Enovia`** → **assert the pushed
SHA** → trigger that suite's **JARVIS test config by ID** on the **JARVIS DAI**
→ wait for completion → read the run's results → **assert the executed commit
SHA**. This is the per-attempt validation loop plan2 depends on.

**Where:** [LAPTOP] (can develop) + the Jay-administered JARVIS VM.
**Script:** `scripts/poc_jarvis_validation.py` (to be written).

### Recorded values (no longer blanks — these are measured facts)
| `.env` key | What it is | Value / source |
|---|---|---|
| `JARVIS_REPO_URL` | the **validation** repo | `bitbucket.it.keysight.com/scm/eggauto/agentic-eggplant-automation.git` |
| `JARVIS_PAT` | PAT with **force-push** rights to `refs/heads/Enovia` | ⚠ CONFIRM (Jay): exact scopes — see plan0 A.7 |
| `JARVIS_BRANCH` | force-push target branch | `Enovia` |
| `JARVIS_DAI_BASE_URL` | the JARVIS DAI (26.2.2) base | ⚠ CONFIRM (Jay): exact URL/scheme/port — observed as `eggptdai10.cos.is.keysight.com:8000` |
| `JARVIS_DAI_CLIENT_ID` / `_SECRET` | API client on the **JARVIS** DAI | JARVIS DAI UI → System → API Access |
| `JARVIS_COMPLETION_MODE` | completion detection | `poll_backoff` (day one); webhook is the upgrade path (**O1**) |
| `JARVIS_ENOVIA_SUITES_PATH_IN_VM` | Design agent suites folder | `C:\Eggplant_Suites` (git clone of the validation repo) |
| *(no scalar test-config ID)* | suite → `test_config_id` | `tracks/enovia/test_config_registry.yaml` (**D3**) — `PRACTICE_TEST_CONFIG_ID` is retired |

**Confirmed with the DAI admin (Jay):**
- the JARVIS test config's **git connection points at the validation repo** and **syncs at run start** (not a cached clone) — this is what makes the executed-SHA assert meaningful;
- its **SUT connection (`Jay_130`) is prebuilt** — triggering really drives a machine;
- the **webhooks admin UI is available and Jay is admin** (so webhooks are enable-able; profile not yet registered — **O1**).

> **Why the test config is never edited per ticket.** DAI public API **v2 exposes no test-config or
> step create/edit endpoints (C1)**. The config therefore stays **permanently static**, and per-ticket
> targeting happens entirely through the **dispatcher** (**D1**) — see PoC 2b-bis below.

### Two ways to trigger (pick one; API is primary)

**Option A — `eggplant-runner` CLI (blocking trigger; documented, NOT selected):**
```powershell
# download the runner exe once from the DAI server's download page
.\eggplant-runner-Windows-<ver>.exe `
  <JARVIS_DAI_BASE_URL> <TEST_CONFIG_ID from the D3 registry> `
  --client-id=<JARVIS_DAI_CLIENT_ID> `
  --client-secret=<JARVIS_DAI_CLIENT_SECRET> `
  --result-path .\jarvis_result.xml `
  --log-level INFO
echo "exit: $LASTEXITCODE"     # 0 = PASS, non-zero = FAIL
```
- It **blocks until the run finishes** and writes JUnit XML to `--result-path`.
- Add `--ca-cert-path <pem>` if the JARVIS DAI uses a self-signed cert.

**Option B — REST API (✅ SELECTED — what the agent uses in code):**
1. **Auth:** `POST {JARVIS_DAI_BASE_URL}/api/v2/auth` with `client_id` / `client_secret` → bearer token, **~10-minute expiry**, cached in-process and refreshed on expiry.
   > **This is NOT the production DAI's scheme.** The production DAI (`epcorpappsdai12`) uses OAuth2 client-credentials against the Keycloak realm (`/auth/realms/eggplant/protocol/openid-connect/token`). Never share a client, base URL or token cache between the two instances.
2. **Trigger:** the existing, already-tested trigger-a-test-config-by-ID API, using the ID from the D3 registry.
3. **Wait:** `poll_backoff` — `asyncio.sleep` loop, backoff `[15, 30, 60, 120]`s, timeout covering the observed 20 min–2 hr range. No LLM in the wait path; cost must be **$0** between trigger and resolution.
4. **Results chain (v2):**
   ```
   GET /api/v2/test_config_results?test_config_id=<ID>   → newest result id
   GET /api/v2/test_results?test_config_result_id=<id>   → step result + status
   GET /api/v2/test_results/{test_result_id}/logs        → entries (message, severity,
                                                             message_type, image_id)
   GET /api/v2/screenshots/{screenshot_id}               → PNG (PoC-2 walk-back reused)
   ```

### `scripts/poc_jarvis_validation.py` should
1. Pull the working copy; render the dispatcher for the target suite; `git commit`.
2. `git push agentic-eggplant-automation wc/<TICKET>:refs/heads/Enovia --force`; record the pushed SHA.
3. **UP-24 pre-check:** assert `git ls-remote agentic-eggplant-automation refs/heads/Enovia` **==** the pushed SHA.
4. Trigger the registry's `test_config_id`; poll to completion via `poll_backoff`.
5. Walk the four-call v2 results chain → status + log + screenshots.
6. **UP-24 post-check:** assert the run log's `Using Git commit SHA: '<sha>'` **==** the pushed SHA.
7. **Print the full timeline with durations:** push → assert → trigger → complete → assert (this is the per-attempt validation latency — still unmeasured across a realistic suite set, **O3**).

### Verification / DoD — ✅ met
A code push demonstrably reached the SUT run (evidenced by the commit SHA in the run log) and its
results were fetched programmatically via the v2 chain. **A full PASSED run with
`Using Git commit SHA` traceable in the run log has been achieved.** `poll_backoff` recorded as
`JARVIS_COMPLETION_MODE`; `eggplant-runner` recorded as the documented, unselected alternative.

### Gotchas
- **Force-push to `Enovia` every time** so drift never matters for validation correctness. Note the
  side effect: the branch contents are wholly replaced, so dispatchers for **other** suites vanish
  unless regenerated (**O5**; policy pending as **O6**).
- **JARVIS DAI tokens expire in ~10 min** — re-acquire before long polls. (The production DAI's
  Keycloak tokens expire in ~5 min; different instance, different lifetime.)
- Find the `TEST_CONFIG_ID` from the **URL** when editing the config, not the display name — then
  record it in `tracks/enovia/test_config_registry.yaml`, not in an env var.
- **Reruns must be OFF** on the test config, or a flaky retry masks a real target failure.

---

## PoC 2b-bis — Dispatcher pattern proof  (Step A.2b)  ✅ **PROVEN**

**Proves:** the script a validation run executes can be switched **purely by a git push**, with the
DAI test config left completely untouched. This is the formal workaround for **C1** and the proof of
**D1**.

**The artifact** (`src/analysis/templates/agent_dispatcher.st.j2`, one per suite, **generated every
cycle**, never hand-edited, **never present in the production repo** — **D4**):
```
-- {{suite}}_AgentDispatcher.script
-- JARVIS — dispatcher for {{suite}}.suite (GENERATED — do not hand-edit)
-- Contract: only the targetScript line is rewritten per validation cycle.
-- No try/catch — a target failure MUST fail this run.

set targetScript to "{{target_rel_path}}"   -- e.g. TestCases/TESTAUTOMA_6167_Verify...

log "start — target=" & targetScript
run targetScript
log "done — target=" & targetScript
```

**Two SenseTalk rules learned the hard way — both were bugs, both are now binding:**
- **S1.** A script in `Scripts/TestCases/` must be referenced as **`TestCases/<name>`** — **no
  `.script` extension**, **no `Scripts/` prefix**. EPF does not auto-search subfolders.
- **S2.** Dynamic invocation is plain **`run targetScript`**. Dot-notation `targetScript.run()` does
  **not** work.

**The missing `try/catch` is deliberate and load-bearing.** A swallowed target failure would produce a
**false PASS** — the worst possible failure mode for this system.

**Verification / DoD — ✅ met:** the **same `test_config_id`** executed a **different script**, with
the only difference being a git push. The negative test (target switched to a deliberately broken
script, nothing touched in DAI) failed **on the target**, as required. Proven on
`Part_Master_Pack_01` / PartMaster.

---

## PoC 1 — EPF `runscript` runs an Enovia script headless  (Step A.3)  ⬜ TODO

**Proves:** Eggplant Functional can execute an Enovia `.script` from the CLI →
results folder + exit code. Basis of the fast local inner loop.

**Where:** **[RUNNER] `eggptdai10`** (this is a (User) step — needs the VM, EPF, license, SUT). Script written by the Agent.

### Prereqs on [RUNNER]
1. RDP into `eggptdai10` (156.140.21.30).
2. Confirm Eggplant Functional installed; note the path to `runscript.bat`
   (typically `C:\Program Files\Eggplant\runscript.bat`).
3. Confirm the floating license server is reachable: EPF → **Preferences → Run**, note `-LicenserHost`.
4. Clone the repo on the VM:
   ```powershell
   git clone https://bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git C:\agent\repo
   cd C:\agent\repo
   git checkout Testing_Mar10
   ```

### The command (`scripts/poc_runscript.ps1`)
```powershell
$RS = "C:\Program Files\Eggplant\runscript.bat"
$SUITES = "C:\agent\repo\Enovia"          # the PARENT of the *.suite folders
& $RS "$SUITES\EngineeringCentral.suite\Scripts\TestCases\<small>.script" `
    -DefaultDocumentDirectory "$SUITES" `       # resolves cross-suite handler calls
    -GlobalResultsFolder "C:\agent_runs\poc1" `
    -CommandLineOutput YES `
    -ReportFailures YES `
    -MaxWaitForLicense 600
echo "exit: $LASTEXITCODE"
```

### Why each flag matters
- **`-DefaultDocumentDirectory` = the parent of the `*.suite` folders** — this is
  what lets `EngineeringCentral` resolve calls into `CommonEnovia`. Get this
  wrong and you get "handler not found" errors that look like code bugs.
- `-GlobalResultsFolder` — must be set **before** the run (log location is fixed once a script starts).
- `-CommandLineOutput YES` — echoes the run log to stdout.
- `-ReportFailures YES` — returns failed-script/suite counts to the CLI.
- `-MaxWaitForLicense 600` — wait up to 10 min for a license seat.
- `-LicenserHost <host>` — add if the license server isn't auto-discovered.

### Exit codes (research-confirmed)
- `0` = pass · non-zero = fail · **`127` = no license available** (the run exits immediately).

### Verification / DoD
`C:\agent_runs\poc1` contains `LogFile.txt` + per-step screenshots; exit code
reflects pass/fail. (User) documents the **results-folder layout** in
`poc_results.md` A.3 (plan2 parses it).

---

## PoC 1b — SUT connection OUTSIDE DAI  (Step A.4)  *(DEFERRED — optional latency optimisation)*

> **Deferred.** The JARVIS validation gate is the **single mandated validation mechanism** and is
> proven, so `VALIDATION_MECHANISM=jarvis-dai` is already recorded and the local inner loop is not on
> the critical path. Retained as a documented option — see `docs/later-enhancements.md` §1.

**Proves (or disproves):** whether `runscript` can establish the RDP SUT
connection without DAI injecting it. Decides whether a fast local inner loop
exists. **Not project-blocking** — the proven JARVIS validation path serves every attempt.

**Where:** [RUNNER], guided by the Agent.

### Step 1 — does the suite contain an explicit `Connect`?
```powershell
rg -n "Connect\b|ConnectionInfo|RemoteWorkInterval|RDP" C:\agent\repo\Enovia
```

### Step 2 — branch on the result
- **(A) explicit `Connect` found** → the Agent writes a one-line probe:
  ```
  Connect ServerID:"<sut>", … 
  Log "connected: " & ConnectionInfo()
  Disconnect
  ```
  Run it via `runscript`. Connects → **A holds** → `VALIDATION_MECHANISM=local-runscript (deferred)`.
- **(B) no `Connect` — DAI injects it** → either
  - **(b1)** the Agent writes a thin connection-wrapper script the agent prepends for validation (SUT details from DAI's environment) → still `local-runscript`; or
  - **(b2)** use the **JARVIS validation gate for every attempt** → `VALIDATION_MECHANISM=jarvis-dai`.

### DoD — record the selected mechanism in `poc_results.md` A.4 and `.env`
**`VALIDATION_MECHANISM=jarvis-dai` — already selected and recorded.** The local-runscript variant
(A / b1) stays **documented but unselected**. **Plan 2 no longer branches on a flag**; the JARVIS gate
serves every attempt.

---

## PoC 1e — `runscript` ≡ DAI run parity  (Step A.5)  ⬜ TODO (only if pursuing local-runscript)

**Proves:** a test that passes under DAI also passes under `runscript` (no hidden
DAI-injected params / `RunValues` / data).

**Where:** [RUNNER].

### Steps
1. Run the PoC-1 test **via DAI** (normal trigger) — note pass/fail + key log lines.
2. Run the **same** test **via `runscript`** (PoC 1 command) — note the same.
3. Compare: pass/fail match? any "missing parameter / undefined RunValues" errors under runscript?

### DoD
Documented parity, OR a documented list of DAI-supplied params to pass via
`-param`/globals. **If parity can't be bridged → set `VALIDATION_MECHANISM=jarvis-dai`.**

---

## PoC 3 — SenseTalk static call-graph + ripgrep blast radius  (Step A.6)  ⬜ TODO (logic verifiable on [LAPTOP])

**Proves:** deterministic retrieval (the RAG replacement) works on real Enovia
scripts — call chains and "who calls this handler" are correct.

**Where:** the Agent writes + unit-tests on **[LAPTOP]** with synthetic
fixtures; (User) runs on the **VM clone** for the real-script check.

### Install ripgrep (both [LAPTOP] and the VMs)
```powershell
winget install BurntSushi.ripgrep.MSVC
rg --version          # confirm; reopen shell if PATH not picked up
```

### `scripts/poc_static.py` should
- Seed a `HANDLER_MAP` of known prefixes → paths (CommonEnovia, common, configEnovia, LaunchApp…).
- Regex calls: `\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b`.
- `call_chain(test_path, depth=3)` — recursive handler resolution.
- `blast_radius(handler)` = `rg -n "\b<handler>\b" <repo>`.
- Ship `tests/test_poc_static.py` with synthetic SenseTalk fixtures (the Agent can fully verify the logic locally — no VM needed for unit tests).

### Verification (on the VM clone)
- The 8055 chain surfaces `EngineeringCentral → CommonEnovia` (incl. `searchEnovia`).
- `blast_radius("searchEnovia")` **equals a manual `rg` grep** — zero missed callers.

### DoD
Chain + blast radius correct on **5 real scripts** spanning bug families; recorded in `poc_results.md` A.6.

---

## PoC 4 — Bitbucket Server read / branch / PR  (Step A.7)  ⬜ TODO (do on [LAPTOP])

**Proves:** the Bitbucket **Server/Data Center** REST shapes (NOT Cloud) for
read, branch-create, and PR-create. Confirms PAT scopes.

**Where:** [LAPTOP]. **Use a SANDBOX repo for the PR write**, then delete the test branch.

### Endpoints (research-confirmed; base `B = https://bitbucket.it.keysight.com`)

**Read a raw file:**
```
GET {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/raw/<path>?at=Testing_Mar10
Header: Authorization: Bearer {BITBUCKET_PAT}
```

**List files in a folder (paginated):**
```
GET {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/browse/<path>?at=Testing_Mar10
→ response has values[] + isLastPage + nextPageStart  (loop on nextPageStart until isLastPage)
```

**Create a branch (note the `branch-utils` API, not `api/1.0`):**
```
POST {B}/rest/branch-utils/latest/projects/EGGAUTO/repos/enovia-plm-test-automation/branches
Body: {"name":"Jarvis-fix/POC-TEST","startPoint":"Testing_Mar10"}
→ 201
```

**Create a pull request:**
```
POST {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/pull-requests
Body:
{
  "title": "POC test PR",
  "description": "delete me",
  "fromRef": {"id":"refs/heads/Jarvis-fix/POC-TEST",
              "repository":{"slug":"enovia-plm-test-automation","project":{"key":"EGGAUTO"}}},
  "toRef":   {"id":"refs/heads/Testing_Mar10",
              "repository":{"slug":"enovia-plm-test-automation","project":{"key":"EGGAUTO"}}}
}
→ 201
```

### PAT scopes the (User) must grant
Repo **Read/Write**, Pull-request **Read/Write**, Branch **create**.

### Verification / DoD
read → content; branch → 201; PR → 201 (sandbox). PAT scopes confirmed and
recorded in `poc_results.md` A.7. Delete the test branch + decline the test PR.

### Gotchas
- It's **Server/DC API `1.0`**, not Cloud `2.0` — different JSON entirely.
- Branch creation lives under `/rest/branch-utils/`, a different base than `/rest/api/1.0/`.
- `fromRef`/`toRef` must be full `refs/heads/...` ids with the repository object.

---

## PoC 5 — Jira DC read / comment / attach + LLM metadata extraction  (Step A.8)  🔶 PARTIAL

**Proves:** Jira **Data Center REST v2** behavior (read/comment/attach/transitions)
AND that the LLM reliably extracts `{runid, title, description, test_script_name}`
from real tickets regardless of where/how the runid appears.

**Where:** [LAPTOP]. **Use a disposable test ticket for the write operations.**
**Status:** the **read + LLM-extraction** half is already proven inside
`scripts/poc_dai.py` (runid 30832 extracted from 8055). What remains is a
dedicated `scripts/poc_jira.py` that also exercises **comment / attach /
transitions** on a throwaway ticket.

### Endpoints (research-confirmed; base `J = https://jira.it.keysight.com`, header `Authorization: Bearer {JIRA_PAT}`)

**Read (request all fields once to discover custom fields):**
```
GET {J}/rest/api/2/issue/TESTAUTOMA-8055?fields=*all
```

**Add a comment (v2 = plain/wiki body, NOT ADF):**
```
POST {J}/rest/api/2/issue/{KEY}/comment
Body: {"body":"AI agent test comment"}
```

**Add an attachment (MUST send the anti-CSRF header):**
```
POST {J}/rest/api/2/issue/{KEY}/attachments
Headers: Authorization: Bearer {PAT} ; X-Atlassian-Token: no-check
Form:    file=@<path>     (multipart/form-data)
```

**List / perform transitions (best-effort — service acct may lack permission):**
```
GET  {J}/rest/api/2/issue/{KEY}/transitions
POST {J}/rest/api/2/issue/{KEY}/transitions   Body: {"transition":{"id":"<id>"}}
```

### LLM extraction (already implemented in poc_dai.py)
Forced tool-call to `claude-opus-4-7` returning `{runid, title, description,
test_script_name, reasoning}` after searching the **entire** response. The
`reasoning` line is human-checked per ticket. Keep an optional deterministic
regex/custom-field cross-check that only **warns** on disagreement.

### Verification / DoD
read/comment/attach succeed on the test ticket; transitions listed; **all four
metadata fields correct on every provided real ticket** (incl. 8055). Record in
`poc_results.md` A.8: the extraction prompt/schema, per-ticket results, and
**whether the service account can transition status** — if not, **label is the
reliable signal** (plan3 relies on this).

### Gotchas
- Attachment fails silently/blocked without `X-Atlassian-Token: no-check`.
- Comment body is plain/wiki text on DC v2 — do **not** send Cloud ADF JSON.
- Provide 2–3 real tickets where the runid sits in *different* places to truly test the LLM extractor.

---

## PoC 6 — Claude reproduces the TESTAUTOMA-8055 diagnosis from the VM  (Step A.9)  ⬜ TODO (must run on [ORCH])

**Proves:** the engine + the VM's network egress to the Anthropic gateway work
on the golden bug.

**Where:** **[ORCH] `aiagent-testmanager`** (egress from the VM is the point).

### Prereqs
1. (User) places into `samples/` on the VM: the 8055 test script,
   `CommonEnovia.script` (incl. ~line 409), and the DAI failure-log excerpt.
2. `.env` on the VM has the gateway key + `MODEL=claude-opus-4-7`.

### `scripts/poc_claude.py` should
- Build a draft diagnosis system prompt (full version lands in plan1).
- Embed ticket/script/handler/logs **inside untrusted-data delimiters**
  (`<<<TICKET_START … TICKET_END>>>`).
- Call `MODEL` via `ANTHROPIC_BASE_URL` (proves the gateway path from the VM).
- Print the diagnosis.

### Verification / DoD
The diagnosis names `CommonEnovia.script` ~409 and the
`and not ImageFound(text:"Name",…)` clause, with the "passed-with-swallowed-
exceptions" observation. Run **from [ORCH]**; paste output into `poc_results.md`
A.9. **If egress fails → (User) files the firewall ticket now.**

### Gotcha
This is the first hard proof that the **VM** (not just your laptop) can reach
the gateway. Run our `scripts/probe_claude.py` there first as a 5-second smoke.

---

## PoC 7 — base-rate study (≥50 historical tickets)  (Step A.10)  ⬜ TODO (do on [LAPTOP])

**Proves:** the real bug-type distribution — decides engine fit and whether the
multimodal/vision path needs to move earlier.

**Where:** [LAPTOP] (JQL + LLM labeling), (User) confirms every label.

### `scripts/categorize_tickets.py` should
- JQL search:
  ```
  project = TESTAUTOMA AND component = "Enovia PLM Automation" AND status = Done ORDER BY resolved DESC
  GET {J}/rest/api/2/search?jql=<encoded>&maxResults=50&fields=summary,description,...
  ```
- For each of ≥50 tickets: record key, summary, the actual fix (file/line/change
  from the linked commit if available), and a **proposed category** from the
  master's failure families (LLM proposes via `MODEL_LIGHT` or small-`max_tokens` Opus).
- Output `tracks/enovia/ticket_base_rate.json` + a summary table.

### Decision rule (record in `poc_results.md` A.10)
- code-reasoning families **≥60%** → proceed, vision deferred.
- **40–60%** → proceed, vision scheduled post-Phase-2.
- **<40%** → **STOP**, pull the multimodal screenshot module into Phase 1.

### DoD
≥50 **human-confirmed** labels; decision recorded. This file later seeds the
≥50 validation tickets in plan1.

---

## GATE 0a — the GO/NO-GO checklist

Print and have the (User) confirm with measured values:

| PoC | Proven? |
|---|---|
| 2 — production-DAI log + error screenshot by runid | ✅ |
| 2b — **JARVIS validation path**: push `Enovia` → SHA assert → trigger → fetch results → executed-SHA assert | ✅ |
| 2b-bis — **Dispatcher pattern** (A.2b): target switched purely by git push | ✅ |
| 1 — runscript headless + results folder | n.a. (deferred) |
| 1b — SUT outside DAI → **`VALIDATION_MECHANISM=jarvis-dai` recorded** | n.a. (deferred) |
| 1e — runscript ≡ DAI parity (local-runscript path only) | n.a. (deferred) |
| 3 — static call-graph + ripgrep | ⬜ |
| 4 — Bitbucket read/branch/PR | ⬜ |
| 5 — Jira read/comment/attach + LLM extraction | 🔶 (read+extract done; write ops pending) |
| 6 — Claude reproduces 8055 from [ORCH] | ⬜ |
| 7 — base rate supports approach | ⬜ |
| dedicated EPF license + RDP SUT secured | ⬜ |

**Pass rule:** PoC **7** must pass; PoC **2 + 5** (the runid evidence chain) must
pass; and **the JARVIS validation path (2b + 2b-bis) must pass** — JARVIS is the
single mandated validation mechanism, so the old either/or with the local
runscript loop no longer applies. **Both are proven.** If the validation path,
the evidence chain, or the base rate fails → **STOP and re-architect that part**
before any build.

---

## SUGGESTED EXECUTION ORDER (fastest de-risking first)

1. ~~**2b** (JARVIS validation path)~~ — ✅ **done.** Was the biggest unknown; it unblocked the whole validation story.
2. **5 write-ops** (`poc_jira.py`) and **4** (`poc_bitbucket.py`) — pure API, quick on [LAPTOP]. For 4, remember the **validation-repo force-push permission is a separate PAT question** from the production-repo PR rights.
3. **6** (Claude from [ORCH]) — quick once egress is open; run `probe_claude.py` first.
4. **3** (static) — the Agent can unit-test now; VM real-script check when convenient.
5. ~~**1 → 1b → 1e** (runscript chain)~~ — **deferred**; see `docs/later-enhancements.md` §1.
6. **B.4b suite onboarding** — the real remaining scale-out work (**O4**): every suite beyond PartMaster needs the D2 sequence before JARVIS can validate tickets against it.
6. **7** (base rate) — parallelizable any time; needs ≥50 Done tickets + human labeling.

---

## Sources (research backing this guide)
- Eggplant DAI — Running Automated Tests: https://docs.eggplantsoftware.com/dai/dai-test-automation/
- Eggplant DAI — REST API / Model Execution Endpoints: https://docs.eggplantsoftware.com/dai/dai-rest-api/
- Eggplant DAI Runner: https://docs.eggplantsoftware.com/dai/dai-runner/
- eggplant-runner (GitHub Action): https://github.com/marketplace/actions/eggplant-runner
- EPF Runscript Command-Line Options: https://docs.eggplantsoftware.com/epf/epf-runscript-command-options/
- Bitbucket DC REST (5.16): https://docs.atlassian.com/bitbucket-server/rest/5.16.0/bitbucket-rest.html
- Bitbucket DC branch-utils: https://developer.atlassian.com/server/bitbucket/rest/v803/api-group-branch-utils/
- Jira DC REST — comments: https://developer.atlassian.com/server/jira/platform/rest/v10007/api-group-comment/
- Jira attachment via REST: https://confluence.atlassian.com/jirakb/how-to-add-an-attachment-to-a-jira-issue-using-rest-api-699957734.html
- ripgrep: https://github.com/BurntSushi/ripgrep
