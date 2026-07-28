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
already exports `ANTHROPIC_BASE_URL` (IDEs, Claude Code) silently masks your
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

## PoC 2b — The Practice path end-to-end  (Step A.2)  ⬜ TODO  ← do next

**Proves:** the validation mechanism — push candidate code to the **Practice
repo** `/practice` branch → trigger the **Practice Test Config** on the
**Practice DAI** → wait for completion → read the new run's results by runid.
This is the per-attempt validation loop plan2 depends on.

**Where:** [LAPTOP] (can develop) + needs (User)-provided Practice infra.
**Script:** `scripts/poc_practice.py` (to be written).

### (User) must provide FIRST (these are blanks in `.env`)
| `.env` key | What it is | Where to get it |
|---|---|---|
| `PRACTICE_REPO_URL` | the separate Practice Bitbucket repo | repo admin |
| `PRACTICE_PAT` | PAT with push rights to `/practice` | Bitbucket → PAT |
| `PRACTICE_DAI_BASE_URL` | the Practice DAI server base | DAI admin |
| `PRACTICE_DAI_CLIENT_ID` / `_SECRET` | API client on the Practice DAI | Practice DAI UI → System → API Access |
| `PRACTICE_TEST_CONFIG_ID` | the Practice Test Config UUID | **Practice DAI → Controller → Test Config → edit the config → copy the UUID from the browser URL** |

Also confirm with the DAI admin:
- the Practice Test Config's **git connection is pre-wired to `/practice`**, and
- its **SUT connection is prebuilt** (so triggering it actually drives a machine).

### Two ways to trigger (pick one; API is primary)

**Option A — `eggplant-runner` CLI (simplest blocking trigger):**
```powershell
# download the runner exe once from the DAI server's download page
.\eggplant-runner-Windows-<ver>.exe `
  <PRACTICE_DAI_BASE_URL> <PRACTICE_TEST_CONFIG_ID> `
  --client-id=<PRACTICE_DAI_CLIENT_ID> `
  --client-secret=<PRACTICE_DAI_CLIENT_SECRET> `
  --result-path .\practice_result.xml `
  --log-level INFO
echo "exit: $LASTEXITCODE"     # 0 = PASS, non-zero = FAIL
```
- It **blocks until the run finishes** and writes JUnit XML to `--result-path`.
- Add `--ca-cert-path <pem>` if the Practice DAI uses a self-signed cert.

**Option B — REST API (what the agent will use in code):**
1. Token: `POST {PRACTICE_DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token` (same client_credentials shape as PoC 2).
2. Start: `POST {PRACTICE_DAI_BASE_URL}/execution_service/api/v1/executions` (body references the test config) → returns an execution id.
3. Poll: `GET {PRACTICE_DAI_BASE_URL}/ai/runs` until your run shows completed; capture its **runid**.
4. Results: reuse PoC-2 functions against the **Practice** DAI base URL → log + screenshot by runid (on FAIL) or PASS status.

### `scripts/poc_practice.py` should
1. `git clone`/pull the Practice repo to a temp dir; `git checkout -B practice`.
2. Make a trivial change (e.g. add a comment line to one `.script`), `git commit`, `git push practice HEAD:refs/heads/practice --force`.
3. Trigger (Option A or B); capture the new runid.
4. Poll to completion; fetch that run's log + error screenshot (PoC-2 funcs) or confirm PASS.
5. **Print the full timeline with durations:** push → trigger → complete (this is your per-attempt validation latency).

### Verification / DoD
A code push demonstrably reaches the SUT run and its results are fetched by
runid; cycle time recorded in `poc_results.md` A.2. *If the API trigger is
awkward, record `eggplant-runner` as the viable alternative.*

### Gotchas
- Force-push to `/practice` every time so drift never matters for validation correctness.
- DAI tokens expire in ~5 min — re-acquire before long polls.
- Find the TEST_CONFIG_ID from the **URL** when editing the config, not the display name.

---

## PoC 1 — EPF `runscript` runs an Enovia script headless  (Step A.3)  ⬜ TODO

**Proves:** Eggplant Functional can execute an Enovia `.script` from the CLI →
results folder + exit code. Basis of the fast local inner loop.

**Where:** **[RUNNER] `eggptdai10`** (this is a (User) step — needs the VM, EPF, license, SUT). Script written by Claude Code.

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

## PoC 1b — SUT connection OUTSIDE DAI  (Step A.4)  ⬜ TODO  ← decides INNER_LOOP

**Proves (or disproves):** whether `runscript` can establish the RDP SUT
connection without DAI injecting it. Decides whether a fast local inner loop
exists. **Not project-blocking** — PoC 2b's Practice path is the fallback.

**Where:** [RUNNER], guided by Claude Code.

### Step 1 — does the suite contain an explicit `Connect`?
```powershell
rg -n "Connect\b|ConnectionInfo|RemoteWorkInterval|RDP" C:\agent\repo\Enovia
```

### Step 2 — branch on the result
- **(A) explicit `Connect` found** → Claude Code writes a one-line probe:
  ```
  Connect ServerID:"<sut>", … 
  Log "connected: " & ConnectionInfo()
  Disconnect
  ```
  Run it via `runscript`. Connects → **A holds** → `INNER_LOOP=local-runscript`.
- **(B) no `Connect` — DAI injects it** → either
  - **(b1)** Claude Code writes a thin connection-wrapper script the agent prepends for validation (SUT details from DAI's environment) → still `local-runscript`; or
  - **(b2)** fall back to the **Practice path for every attempt** → `INNER_LOOP=practice-dai`.

### DoD — record EXACTLY ONE in `poc_results.md` A.4 and later `.env`
`INNER_LOOP=local-runscript`  **or**  `INNER_LOOP=practice-dai`.
**Plan 2 branches on this flag.**

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
`-param`/globals. **If parity can't be bridged → set `INNER_LOOP=practice-dai`.**

---

## PoC 3 — SenseTalk static call-graph + ripgrep blast radius  (Step A.6)  ⬜ TODO (logic verifiable on [LAPTOP])

**Proves:** deterministic retrieval (the RAG replacement) works on real Enovia
scripts — call chains and "who calls this handler" are correct.

**Where:** Claude Code writes + unit-tests on **[LAPTOP]** with synthetic
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
- Ship `tests/test_poc_static.py` with synthetic SenseTalk fixtures (Claude Code can fully verify the logic locally — no VM needed for unit tests).

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
Body: {"name":"ai-fix/POC-TEST","startPoint":"Testing_Mar10"}
→ 201
```

**Create a pull request:**
```
POST {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/pull-requests
Body:
{
  "title": "POC test PR",
  "description": "delete me",
  "fromRef": {"id":"refs/heads/ai-fix/POC-TEST",
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
| 2 — DAI log + error screenshot by runid | ✅ |
| 2b — Practice path: push → trigger → fetch results | ⬜ |
| 1 — runscript headless + results folder | ⬜ |
| 1b — SUT outside DAI → **INNER_LOOP flag set** | ⬜ |
| 1e — runscript ≡ DAI parity (local-runscript path only) | ⬜ / n.a. |
| 3 — static call-graph + ripgrep | ⬜ |
| 4 — Bitbucket read/branch/PR | ⬜ |
| 5 — Jira read/comment/attach + LLM extraction | 🔶 (read+extract done; write ops pending) |
| 6 — Claude reproduces 8055 from [ORCH] | ⬜ |
| 7 — base rate supports approach | ⬜ |
| dedicated EPF license + RDP SUT secured | ⬜ |

**Pass rule:** PoC **7** must pass; PoC **2 + 5** (the runid evidence chain) must
pass; and **at least one** validation mechanism — PoC **1/1b** (local runscript)
**or** PoC **2b** (Practice path) — must pass. If none of the validation
mechanisms work, or the evidence chain or base rate fails → **STOP and
re-architect that part** before any build.

---

## SUGGESTED EXECUTION ORDER (fastest de-risking first)

1. **2b** (Practice path) — biggest unknown + unblocks the whole validation story. Needs (User) Practice infra.
2. **5 write-ops** (`poc_jira.py`) and **4** (`poc_bitbucket.py`) — pure API, quick on [LAPTOP].
3. **6** (Claude from [ORCH]) — quick once egress is open; run `probe_claude.py` first.
4. **3** (static) — Claude Code can unit-test now; VM real-script check when convenient.
5. **1 → 1b → 1e** (runscript chain) — needs [RUNNER] + license; 1b sets `INNER_LOOP`.
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
