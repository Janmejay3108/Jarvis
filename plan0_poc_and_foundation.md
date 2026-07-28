# PLAN 0 — PoC DE-RISKING (WEEK 0) + FOUNDATION (WEEKS 1–2) — v2 FOR CLAUDE CODE

> **Prereq:** `plan_master.md` read in full. **Objective:** prove every architectural bet on real Enovia infrastructure, then stand up the project skeleton, static layer, state store and smoke tests so feature work can begin.
>
> **Why PoCs first:** the design rests on empirical bets — the ticket's `runid` reliably fetches the failing run's log + screenshot via the (User)-provided DAI APIs, at least one validation mechanism works (local `runscript` driving the SUT, and/or the **Practice path**: push to the Practice repo `/practice` → trigger the Practice Test Config → read the new run's results), and code-logic bugs dominate the ticket mix. If any is false the design changes. Prove them in days, not after weeks of building.
>
> **Division of labor:** Claude Code writes every script/file. The **(User)** runs anything that needs VMs, credentials, RDP, licenses, or corporate network, and pastes outputs back — and **provides at the marked steps**: the exact Jira base URL, the tested DAI log-by-runid API, the error-screenshot identification logic, and the Practice repo / Practice DAI / Practice Test Config details. Claude Code never invents PoC results.

---

# PHASE 0.A — WEEK 0: PROOF-OF-CONCEPT GATE

### Step A.0 — PoC workspace scaffold — *Owner: Claude Code*
**Goal:** a scratch project where all PoC scripts live, plus the results ledger.
**Actions:**
1. Create folder `ai-test-fix-agent/` with `scripts/`, `tracks/enovia/`, `samples/`, `tests/`.
2. Create `.env.example` with keys: `JIRA_BASE_URL=` *((User) provides the exact base URL where the tickets live)*, `JIRA_PAT=`, `BITBUCKET_BASE_URL=https://bitbucket.it.keysight.com`, `BITBUCKET_PAT=`, `DAI_BASE_URL=`, `DAI_CLIENT_ID=`, `DAI_CLIENT_SECRET=`, `DAI_AUTH_URL=` *(OAuth2 token endpoint, typically `{DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token`)*, `DAI_LOG_BY_RUNID_URL=` *((User) provides the tested endpoint at A.1, typically `{DAI_BASE_URL}/ai/runlogs/{runid}`)*, `DAI_SCREENSHOT_URL=` *((User) provides at A.1, typically `{DAI_BASE_URL}/api/v2/screenshots/{image_id}`)*, `PRACTICE_REPO_URL=`, `PRACTICE_PAT=`, `PRACTICE_DAI_BASE_URL=`, `PRACTICE_DAI_CLIENT_ID=`, `PRACTICE_DAI_CLIENT_SECRET=`, `PRACTICE_TEST_CONFIG_ID=`, `ANTHROPIC_API_KEY=`, `ANTHROPIC_BASE_URL=` *(direct API or the Keysight gateway)*, `MODEL=claude-opus-4-7` *(the ONLY reasoning model — 4-7 because 4-6 isn't whitelisted on the Keysight gateway; the proven whitelisted Opus IDs are 4-5 and 4-7; we use the newer; see plan_master §6)*, `MODEL_LIGHT=` *(optional, non-reasoning utility only; leave empty to disable)*. Every script that reads this file MUST use `load_dotenv(override=True)` so the project `.env` wins over any parent-shell env vars (plan_master §6.10).
3. Create `tracks/enovia/poc_results.md` with a checklist mirroring Gate 0a (every PoC, a Proven? box, and a Notes column).
4. Create `requirements-poc.txt`: `httpx anthropic pyyaml python-dotenv rich`.
5. **(User)** On your laptop: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements-poc.txt`, copy `.env.example` → `.env` (fill as PoCs proceed; never commit).
**Verification:** tree exists; `.env` is gitignored.
**DoD:** workspace ready; results ledger created.

### Step A.1 — PoC 2: DAI evidence by `runid` (cheapest — do first) — *Owner: Claude Code + (User)*
**Goal:** wire the **(User)'s already-tested DAI APIs** PLUS the LLM-reasoning step that picks the right error entry: given a Jira ticket + extracted `runid`, fetch that run's log, **LLM-match** the single error entry that corresponds to the ticket's reported failure, **deterministically walk back** to the most recent screenshot, fetch it.
**Actions:**
1. **(User)** provide: (a) DAI API access (`client_id`/`client_secret` via DAI UI → System → API Access, or whatever auth the tested API uses) + DAI base URL + OAuth2 token endpoint into `.env`; (b) the **log-by-runid endpoint** (method, path, params) — paste a sample response; (c) the **screenshot-fetch endpoint** (method, path, params); (d) confirm Eggplant's capture-then-act ordering so the deterministic walk-back logic is correct (the captured screenshot lives in the most recent prior entry with non-null `image_id`); (e) a real sample `runid`.
2. Claude Code: write `scripts/poc_dai.py` using `load_dotenv(override=True)`:
   - **DAI auth:** OAuth2 `client_credentials` → bearer token (cached in-process).
   - **`fetch_log(runid)`:** `GET {DAI_LOG_BY_RUNID_URL}` → parse `{"items": [LogEntry…], "total_count": N, "date_as_of": ISO}`. `LogEntry` fields: `id, eventtime, testrunid, message, severity, step_id, stage, message_type, image_name, image_id`.
   - **`find_error_log_index(logs, title, description)` [LLM reasoning step]:** forced tool-call to the project's reasoning model (`MODEL`, currently `claude-opus-4-7`); inputs are the ticket `title`+`description` and a compacted list of `{i, message_type, severity, message}`; output is the index of the SINGLE entry whose `message` semantically matches the failure (e.g. ticket says *"release was not able to identify"* → the `"Unable to Find Image (TEXT:\"Released\"). Text not found."` entry; ticket says *"Set Enterprise Item Number"* → that entry, not an earlier `Login` failure). Severity is NOT a reliable filter — real failures are typically `severity=INFORMATIONAL` with `message_type=imagefound`.
   - **`find_last_screenshot_before(logs, error_index)` [deterministic walk-back]:** scan indices `error_index-1, error_index-2, …, 0`; return the first entry whose `image_id` is non-null and non-empty. Returns `None` if no captured frame exists before the failure (should be vanishingly rare in real runs).
   - **`fetch_screenshot(image_id, dest)`:** `GET {DAI_SCREENSHOT_URL}` → write PNG bytes.
   - **Print:** `len(logs)`, the matched error `message`, the matched `image_id`, the saved path.
3. **(User)** run it end-to-end on the sample ticket; paste output into chat and `poc_results.md`.
**Verification:** for TESTAUTOMA-8055 (or the chosen ticket): runid extraction returns the right number, the LLM matches the correct error entry (not the first/any unrelated image-find failure), and the walk-back returns the captured screenshot the test was acting against. (Hard-coded `--runid <N>` mode is allowed as a fallback for credential-free testing, but it uses a deterministic "first imagefound failure" heuristic and is known to pick the WRONG entry when a run has multiple failures — by design, to demonstrate why the LLM step is required.)
**DoD:** log-by-runid + LLM-error-match + deterministic-walk-back + screenshot-fetch all proven on real DAI; the exact JSON shape (`items[]`, `LogEntry` fields above) and the four endpoints (auth, runlogs, screenshots, Jira issue) recorded in `poc_results.md` A.1. *If it fails:* wrong base URL / cert trust (install CA) / API access disabled / model not whitelisted on the gateway (4-6 vs 4-5; see plan_master §6) — **(User)** files the IT ticket or rotates the model now.

### Step A.2 — PoC 2b: the Practice path end-to-end — *Owner: Claude Code + (User)*
**Goal:** prove the full practice validation cycle: push code to the **Practice repo** `/practice` branch → trigger the **Practice Test Config** on the **Practice DAI server** via its (already-tested) API → learn of completion → fetch the new run's log + screenshot by its runid.

**Completion-detection mechanism — decide here, do NOT default to naive polling.** Practice runs take 20 min–2 hr; the wait must cost zero LLM tokens and zero busy-work regardless of which option below is used — Claude is only ever invoked before the gate (generate the fix) and after it resolves (interpret PASS/FAIL). Evaluate in priority order:
1. **DAI Webhooks (preferred).** DAI supports a generic custom-HTTP webhook profile (*System → Webhooks*, requires DAI Administrator) fired on test-config-run completion, with a JSON payload (`test-configurations`, `result-status`, `result-url`, `test-run-completed`, `execution-start-time`, `total-run-duration`) sent to any URL you configure — not restricted to Slack/Teams/PagerDuty. Wire it to a new `POST /api/webhooks/dai` route (same pattern as the already-planned `POST /api/webhooks/bitbucket`); the orchestrator awaits an `asyncio.Event` per runid instead of polling — zero HTTP calls, zero LLM calls, zero compute while waiting; the event fires the instant the webhook lands. **(User)** must confirm: (a) DAI Admin access is available on the Practice DAI server to create the profile, (b) whether `runid`/`testrunid` is an available payload variable for correlating the webhook back to the triggered run (if not, correlate via `result-url` or test-config name + last-triggered record — confirm which during this PoC).
2. **`eggplant-runner` CLI (fallback).** The CLI blocks synchronously until the run completes, exit code 0 = pass / nonzero = fail, `--result-path` for JUnit XML. Run via `asyncio.create_subprocess_exec` + `await proc.wait()` — no polling code to write, no tokens burned either way, but ties up a live process on a specific host for the run's duration and gives coarser live-progress data for the chat UI than a webhook does.
3. **Polling (safety net only, if neither above is available).** A plain `httpx` GET in an `asyncio.sleep`-based orchestrator coroutine — never an LLM tool call, so it costs no tokens regardless of duration, but still costs a live coroutine and repeated HTTP calls. If used: exponential backoff (e.g. 15s → 30s → 60s → 120s cap), not a flat interval, and a timeout that actually covers the observed 20 min–2 hr range (config-driven per test config, not a fixed low number).

**Actions:**
1. **(User)** provide: Practice repo URL + PAT (push rights to `/practice`), Practice DAI base URL + credentials, the `PRACTICE_TEST_CONFIG_ID`, the **trigger API** spec (method/path/body — already tested), and confirm which completion-detection option above is viable (webhook admin access? `eggplant-runner` available on a host we control? neither?). Confirm the config's git connection is pre-wired to `/practice` and the SUT connection is prebuilt.
2. Claude Code: write `scripts/poc_practice.py` — clone/pull the Practice repo; commit a trivial change (e.g. a comment) to `/practice`; push; call the trigger API; capture the new `runid`; detect completion via whichever mechanism (1)/(2)/(3) was confirmed viable; reuse PoC-2 functions to fetch that run's log + error screenshot (if it failed) or confirm PASS status; print the full timeline (push→trigger→complete) with durations.
3. **(User)** run it; paste output. Time the cycle — this is the per-attempt validation latency if the local runscript path (PoC 1b) doesn't pan out.
**Verification:** a code push demonstrably reaches the SUT run (the triggered run executes the pushed `/practice` state) and its results are fetched programmatically by runid, via the chosen completion mechanism (not naive tight polling).
**DoD:** push → trigger → completion-detected-without-busy-polling → results proven; cycle time recorded in `poc_results.md`; chosen mechanism (`webhook` / `eggplant-runner` / `poll-backoff`) recorded as `PRACTICE_COMPLETION_MODE` for plan2 Phase 2.5 to consume.

### Step A.3 — PoC 1: EPF `runscript` runs an Enovia script headless — *Owner: (User), script by Claude Code*
**Goal:** prove Eggplant Functional executes an Enovia `.script` from CLI → results folder + exit code (the fast inner loop's basis).
**Actions:**
1. **(User)** RDP to `eggptdai10` (156.140.21.30); confirm Eggplant Functional installed + floating license reachable (Preferences → Run; note `-LicenserHost`).
2. **(User)** `git clone https://bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git C:\agent\repo && cd C:\agent\repo && git checkout Testing_Mar10`.
3. Claude Code: write `scripts/poc_runscript.ps1`:
```powershell
$RS="C:\Program Files\Eggplant\runscript.bat"; $SUITES="C:\agent\repo\Enovia"
& $RS "$SUITES\EngineeringCentral.suite\Scripts\TestCases\<small>.script" `
  -DefaultDocumentDirectory "$SUITES" -GlobalResultsFolder "C:\agent_runs\poc1" `
  -CommandLineOutput YES -ReportFailures YES -MaxWaitForLicense 600
echo "exit: $LASTEXITCODE"
```

using the dai apis used in the automated JIRA ticket creation initiative to fetch the new dai logs & screenshots after the execution is complete.
   `-DefaultDocumentDirectory` at the **parent of the `*.suite` folders** is what resolves cross-suite handler calls (EngineeringCentral → CommonEnovia). Exit **127 = no license**.
4. **(User)** run on a known-simple test; paste exit code + listing of the results folder.
**Verification:** `C:\agent_runs\poc1` has `LogFile.txt` + per-step screenshots; exit code reflects pass/fail.
**DoD:** headless run proven; **(User)** documents the results-folder layout in `poc_results.md` (parsed in plan2).

### Step A.4 — PoC 1b: SUT connection OUTSIDE DAI (decides the fast inner loop) — *Owner: (User), guided by Claude Code*
**Goal:** decide whether `runscript` can establish the RDP SUT connection without DAI injecting it. This decides whether the **fast local inner loop** exists — it is no longer project-blocking, because PoC 2b's Practice path is a proven fallback for every attempt (just slower per cycle).
**Actions:**
1. **(User)** `rg -n "Connect\b|ConnectionInfo|RemoteWorkInterval|RDP" C:\agent\repo\Enovia` — do the suites contain an explicit `Connect`?
2. **(A) explicit Connect found** → Claude Code writes a one-line probe script (`Connect ServerID:"<sut>", … ; Log "connected: " & ConnectionInfo() ; Disconnect`); **(User)** runs it via runscript. Connects → **A holds**.
3. **(B) no Connect — DAI injects** → either **(b1)** Claude Code writes a thin connection-wrapper script the agent prepends for validation (SUT details from DAI's environment), or **(b2)** fall back to the **Practice path for every attempt** (PoC 2b already proved it; slower per attempt, same architecture).
**DoD — record exactly one of:** `INNER_LOOP=local-runscript` (A/b1) or `INNER_LOOP=practice-dai` (b2) in `poc_results.md` and later `.env`. **Plan 2 branches on this flag.**

### Step A.5 — PoC 1e: `runscript` run ≡ DAI run parity *(only if pursuing `INNER_LOOP=local-runscript`)* — *Owner: (User)*
**Goal:** a test that passes under DAI also passes under `runscript` (no hidden DAI-injected params/`RunValues`/data).
**Actions:** **(User)** run the PoC-1 test (a) via DAI and (b) via runscript (A.3); compare pass/fail, key log lines, and any "missing parameter / undefined RunValues" errors.
**DoD:** documented parity, OR a documented list of DAI-supplied params to pass via `-param`/globals. **If parity can't be bridged → `INNER_LOOP=practice-dai`.**

### Step A.6 — PoC 3: SenseTalk static call-graph + ripgrep blast radius — *Owner: Claude Code + (User)*
**Goal:** deterministic retrieval works on real Enovia scripts (the RAG replacement).
**Actions:**
1. Claude Code: write `scripts/poc_static.py` — seed `HANDLER_MAP` (CommonEnovia, common, configEnovia, LaunchApp → known paths); regex `\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b` for calls; recursive `call_chain(test_path, depth=3)`; `blast_radius(handler)` = `rg -n "\b<handler>\b" <repo>`. Also write `tests/test_poc_static.py` with synthetic SenseTalk fixtures (Claude Code can fully verify this PoC's logic locally).
2. **(User)** run it on the TESTAUTOMA-8055 script + 4 others spanning bug families on the VM clone; paste outputs.
**Verification:** 8055 chain surfaces `EngineeringCentral → CommonEnovia` (incl. `searchEnovia`); `blast_radius("searchEnovia")` equals a manual grep — zero missed callers. (`rg`: `winget install BurntSushi.ripgrep.MSVC`.)
**DoD:** chain + blast radius correct on 5 real scripts.

### Step A.7 — PoC 4: Bitbucket Server read / branch / PR (sandbox) — *Owner: Claude Code + (User)*
**Goal:** confirm Bitbucket **Server/DC** REST shapes (not Cloud).
**Actions:** Claude Code writes `scripts/poc_bitbucket.py`: read `GET {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/raw/<path>?at=Testing_Mar10`; branch create `POST {B}/rest/branch-utils/1.0/projects/…/branches {name:"ai-fix/POC-TEST", startPoint:"Testing_Mar10"}`; PR create `POST …/pull-requests` with `fromRef/toRef` refs objects. **(User)** provides PAT (Repo R/W, PR R/W, Branch create), runs against a **sandbox repo** for the PR write, then deletes the test branch.
**Verification:** read returns content; branch 201; PR 201 (sandbox).
**DoD:** read + branch + PR proven; PAT scopes confirmed.

### Step A.8 — PoC 5: Jira DC read / comment / attach + **LLM-based ticket-metadata extraction** — *Owner: Claude Code + (User)*
**Goal:** confirm **REST v2 (Data Center)** behavior on a disposable test ticket, AND prove the four ticket fields the pipeline needs — `runid`, `title`, `description`, `test_script_name` — are reliably extractable from real tickets by the LLM regardless of where in the response they live or what casing/phrasing they use.
**Actions:** **(User)** provides the exact `JIRA_BASE_URL` + PAT, plus 2–3 real ticket examples incl. TESTAUTOMA-8055 — **without** prescribing where the runid lives (description text, summary, a custom field, a comment, an attachment name, any of `runid`/`run id`/`Run ID`/`RUN ID`/`testrunid=` — all in scope). Claude Code writes `scripts/poc_jira.py`: `GET /rest/api/2/issue/{KEY}` with `Authorization: Bearer <PAT>` (request `fields=*all` once to see custom fields); `extract_ticket_metadata(issue_json) -> {runid, title, description, test_script_name, reasoning}` — a forced tool-call to the project's reasoning model (`MODEL`, currently `claude-opus-4-7`) that searches the ENTIRE response and returns the four fields in structured form, with a short `reasoning` field naming where each value came from; a small deterministic regex/custom-field check may be kept as a sanity-cross-check but is NOT the primary extractor; comment `POST …/comment {body:"…"}` (v2 = plain/wiki body, NOT ADF); attachment `POST …/attachments` with header `X-Atlassian-Token: no-check`; list `GET …/transitions`. **(User)** runs on a test ticket + the 2–3 real examples.
**Verification:** read/comment/attach succeed; transitions listed; **all four metadata fields extracted correctly from every provided real ticket** (the LLM's `reasoning` line for each ticket is human-checked and recorded). The script also runs end-to-end against TESTAUTOMA-8055 producing the same runid that PoC 2 then uses downstream.
**DoD:** v2 confirmed; LLM-extraction prompt + tool schema recorded in `poc_results.md`; per-ticket extraction results recorded; note whether the service account can transition status — if not, **label is the reliable signal** (plan3 relies on this).

### Step A.9 — PoC 6: Claude reproduces the TESTAUTOMA-8055 diagnosis from the VM — *Owner: Claude Code + (User)*
**Goal:** prove engine + VM egress to `api.anthropic.com` on the golden bug.
**Actions:**
1. **(User)** place into `samples/`: the 8055 test script, `CommonEnovia.script` (incl. ~line 409), and the DAI failure-log excerpt.
2. Claude Code: write `scripts/poc_claude.py` — a draft diagnosis system prompt (full version in plan1) + user message embedding ticket/script/handler/logs with untrusted-data delimiters; call **`MODEL` (Opus 4.7)** via `ANTHROPIC_BASE_URL` (proves the gateway path too, if used); print the diagnosis.
3. **(User)** run **from the orchestrator VM**; paste output.
**Verification:** the diagnosis names `CommonEnovia.script` ~409 and the `and not ImageFound(text:"Name",…)` clause, with the "passed-with-swallowed-exceptions" observation.
**DoD:** correct root cause reproduced from the VM. If egress fails, **(User)** files the firewall ticket now.

### Step A.10 — PoC 7: base-rate study (≥50 historical tickets) — *Owner: Claude Code + (User)*
**Goal:** measure the real bug-type distribution; decides engine fit + whether vision moves up.
**Actions:**
1. Claude Code: write `scripts/categorize_tickets.py` — JQL `project = TESTAUTOMA AND component = "Enovia PLM Automation" AND status = Done ORDER BY resolved DESC`, ≥50 tickets; for each record key, summary, actual fix (file/line/change from linked commit if available), and a proposed **category** from the master's failure families (Claude proposes via `MODEL_LIGHT`; output to `tracks/enovia/ticket_base_rate.json` + a summary table).
2. **(User)** confirm/correct every label (semi-automated labeling, human-confirmed).
**Decision rule (record in `poc_results.md`):** code-reasoning families ≥60% → proceed, vision deferred · 40–60% → proceed, vision scheduled post-Phase-2 · <40% → **STOP**, pull the multimodal screenshot module into Phase 1 scope. This file seeds the ≥50 validation tickets in plan1.
**DoD:** ≥50 confirmed labels; decision recorded.

### GATE 0a — PoC GO/NO-GO — *Owner: (User) decision, checklist by Claude Code*
Print and have the user confirm:
| PoC | Proven? |
|---|---|
| 2 DAI log + error screenshot by `runid` (User's APIs) | ☐ |
| 2b Practice path: push `/practice` → trigger config → fetch results | ☐ |
| 1 runscript headless + results folder | ☐ |
| 1b SUT outside DAI → **INNER_LOOP flag set** (`local-runscript` or `practice-dai`) | ☐ |
| 1e runscript ≡ DAI parity *(local-runscript path only)* | ☐ / n.a. |
| 3 static call-graph + ripgrep | ☐ |
| 4 Bitbucket read/branch/PR | ☐ |
| 5 Jira read/comment/attach + **runid extraction rule** | ☐ |
| 6 Claude (Opus 4.6) reproduces 8055 from VM | ☐ |
| 7 base rate supports approach | ☐ |
| dedicated EPF license + RDP SUT secured **(User)** | ☐ |
**Rule:** **PoC 7** must pass, **PoC 2 + 5** (the runid evidence chain) must pass, and **at least one** validation mechanism — **PoC 1/1b** (local runscript) **or PoC 2b** (Practice path) — must pass. If none of the validation mechanisms work, or the evidence chain or base rate fails → STOP and re-architect that part before any build. The rest are cheaper to work around.

---

# PHASE 0.B — FOUNDATION (WEEKS 1–2)

### Step B.1 — Project repo bootstrap — *Owner: Claude Code + (User)*
**Goal:** the agent's own repo, exactly per the master layout (§4).
**Actions:**
1. **(User)** create Bitbucket repo `ai-test-fix-agent` (under `EGGAUTO` or a new `AIAGENT` project); default branch `main`; require ≥1 PR approval; generate a PAT (Repo R/W, PR R/W, Branch create).
2. Claude Code: create the full directory tree from master §4 (empty `__init__.py` everywhere), `README.md`, `PROGRESS.md`, `.gitignore` (`.env`, `data/`, `*.log`, `.venv/`, `node_modules/`, `webapp/dist/`), and `pyproject.toml`:
```toml
[project]
name = "ai-test-fix-agent"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115","uvicorn[standard]>=0.30","sse-starlette>=2.0",
  "pydantic>=2.9","pydantic-settings>=2.5","httpx>=0.27","anthropic>=0.40",
  "jinja2>=3.1","pyyaml>=6.0","tenacity>=9.0","structlog>=24.0",
  "python-multipart>=0.0.9","aiofiles>=24.0","authlib>=1.3","aiosqlite>=0.20"]
[project.optional-dependencies]
dev = ["pytest>=8","pytest-asyncio>=0.24","pytest-httpx>=0.30","ruff>=0.7","mypy>=1.12"]
```
   **Deliberately absent:** `chromadb`, `sentence-transformers`, Microsoft Graph SDK. `ripgrep` is a system binary.
3. Claude Code: create `config/enovia.yaml` skeleton — repo (project/slug/branch/local_path, `origin` + `practice` remotes), suites list, number→suite ranges, `dai` (base_url, log-by-runid endpoint, screenshot logic params), `practice` (repo_url, branch `/practice`, dai_base_url, test_config_id, trigger/status endpoints), `llm` (`model: claude-opus-4-7`, `anthropic_base_url`, optional `model_light`, `engine_mode: agentic`, `thinking_on_escalation: true`), `validation` (`inner_loop` from PoC 1b, timeouts, `max_attempts: 3`, `n_best_on_retry: 2`), `approval_mode: manual`, `budget_usd_per_run: 10.0`.
**Verification:** `pip install -e .[dev] && python -c "import fastapi, anthropic, structlog; print('ok')"`; `ruff check` clean.
**DoD:** repo pushed; deps resolve; tree matches master layout.

### Step B.2 — VM provisioning scripts — *Owner: Claude Code writes, (User) runs*
**Goal:** both VMs ready.
**Actions:**
1. Claude Code: `scripts/setup_vm_orchestrator.ps1` — winget installs (Python 3.11, Git, Node LTS, `BurntSushi.ripgrep.MSVC`), `pip install uv`, and an egress check loop over `https://jira.it.keysight.com`, `https://bitbucket.it.keysight.com`, `$env:DAI_BASE_URL`, `https://api.anthropic.com` printing OK/FAIL per URL.
2. Claude Code: `scripts/setup_vm_runner.ps1` — verify Eggplant Functional + `runscript.bat` path; configure `-LicenserHost`; install Git + ripgrep; verify the dedicated RDP SUT is reachable.
3. **(User)** run both on the respective VMs; reserve **one EPF floating license** for the agent (license admin); paste egress results.
**DoD:** orchestrator egress all-green; runner reruns PoC 1 + 1b successfully; license reserved.

### Step B.3 — Credentials & config module — *Owner: Claude Code + (User)*
**Goal:** every secret loads from env; nothing hardcoded.
**Actions:**
1. **(User)** provision: Jira PAT (R/W on TESTAUTOMA), Bitbucket PAT, DAI API access, Anthropic API key → `.env` on each VM.
2. Claude Code: implement `src/config.py` (pydantic-settings) — all PoC-era keys **plus**: `jira_base_url`, `dai_log_by_runid_url`, `practice_*` (repo url, PAT, DAI url/creds, test config id), `anthropic_base_url`, `model` (Opus 4.7), optional `model_light`, `epf_runscript_path`, `epf_default_doc_dir`, `epf_license_host`, `working_copy_path`, `inner_loop`, `engine_mode`, `approval_mode`, `budget_usd_per_run`, `db_path` (default `data/agent.db`), `sso_*`. Loads `.env` + merges `config/enovia.yaml` via `src/orchestrator/track_loader.py` (returns a typed `TrackConfig`).
**Verification:** `python -c "from src.config import settings; print(settings.model)"` works with `.env`; unit test for track_loader.
**DoD:** config module + track loader tested; secrets only in `.env`.

### Step B.4 — Local clone + static layer + vocabulary [UP-3, UP-12] — *Owner: Claude Code + (User)*
**Goal:** the deterministic retrieval layer that replaces the vector DB — now including the handler vocabulary and the Tier-0 lint.
**Actions:**
1. Claude Code: `scripts/clone_repo.ps1` (clone the **production** repo to `C:\agent\repo` ↔ `settings.working_copy_path`, checkout `Testing_Mar10`, then `git remote add practice <PRACTICE_REPO_URL>` — **one working copy, two remotes**: `origin` = production [pull; later `ai-fix/*` push], `practice` = validation push target) + Task-Scheduler registrations for (a) an hourly `git pull --ff-only` and (b) a **nightly rebuild job** that re-runs `build_handler_map.py` + `build_vocabulary.py` against the fresh clone, so the derived artifacts never go stale. **(User)** run on both VMs; confirm both scheduled tasks.
2. Claude Code: `scripts/build_handler_map.py` — walk every `*.suite/Scripts/*.script`, parse `to handle <name>` / `to <name>` / `function <name>` definitions, map call-prefixes → repo-relative paths; seed/verify against known prefixes (CommonEnovia, common, configEnovia, LaunchApp, FileOperations, EnoviaSearch, exceptionHandling, CommonEnoviaContd, EnoviaChangeManagement, MQLTestData, WINSCP) → `tracks/enovia/handler_map.yaml`.
3. Claude Code: promote PoC-3 logic into real modules with unit tests on synthetic fixtures:
   - `src/static/sensetalk_parser.py` — `handler_defs(text)`, `handler_calls(text)` (ignore strings/comments).
   - `src/static/call_graph.py` — `build_call_chain(test_src, handler_map, depth=3)` + `flatten_paths`.
   - `src/static/ripgrep_search.py` — `find_callers(handler, repo_path)` via `rg -n "\b<h>\b"`.
   - `src/static/handler_map.py` — load YAML; `resolve(prefix) -> path|None`.
4. **[UP-12]** Claude Code: `scripts/build_vocabulary.py` + `src/static/vocabulary.py` — for every handler: `{name, file, line, signature, params[]}`; optional one-time `MODEL_LIGHT` pass adds a 1-line `purpose` (cached; **(User)** approves the spend) → `tracks/enovia/handler_vocabulary.json` with `lookup(name)` / `exists(name)`.
5. **[UP-3]** Claude Code: `src/static/lint.py` — `lint(script_text, vocabulary) -> list[LintIssue]`: balanced blocks (`if/end if`, `repeat/end repeat`, `try/catch/end try`, `to|on|function/end`), unknown-handler calls (vs vocabulary, with a config allowlist for built-ins), and basic paren/quote balance. Unit tests: clean script → 0 issues; seeded errors → each caught.
6. **(User)** with Megha's team: curate `tracks/enovia/context.md` (≤~20K tokens) — handler signatures, search-rectangle definitions, config values, JIRA-number→suite ranges, ~20 known fix patterns grouped **by failure family** (UP-5 exemplar source). Get it dev-reviewed. **Where it lives:** in the AGENT'S OWN repo (not the Enovia repo, not embedded in code) — a versioned data file loaded from disk at runtime and prompt-cached [UP-6]. It is curated tribal knowledge and is **never auto-rewritten**; what IS auto-derived from the Enovia code (handler_map, vocabulary) is rebuilt nightly (action 1), and plan3 adds weekly drift detection + agent-drafted update suggestions for human review.
**Verification:** static modules reproduce PoC-3 results from the **generated** map ((User) reruns on VM); lint unit tests green; vocabulary spot-checked against 5 known handlers.
**DoD:** `handler_map.yaml` + `handler_vocabulary.json` complete; parser/graph/ripgrep/lint tested; `context.md` reviewed; hourly pull + nightly rebuild running; both remotes configured.

### Step B.5 — Evidence retrieval validation — *Owner: (User), scripts by Claude Code*
**Goal:** prove the evidence path with **no** SharePoint/Azure AD.
**Actions:** Claude Code extends `scripts/poc_dai.py` with `--runid <id> --fetch-evidence <dest>` (log + error screenshot via the User's APIs/logic from A.1); **(User)** fetch one evidence set by runid and one screenshot from the PoC-1 results folder; attach both to a test Jira ticket via `scripts/poc_jira.py`. Decide the bundle: error screenshot(s) + trimmed log excerpt + DAI result link.
**DoD:** both retrieval paths + Jira attachment proven; SharePoint/Azure AD formally dropped (noted in `poc_results.md`).

### Step B.6 — Persistent state store + event bus [UP-8] — *Owner: Claude Code*
**Goal:** SQLite persistence for everything the chat product and resumability need.
**Actions:**
1. `src/orchestrator/state_store.py` (aiosqlite) — create-on-start schema:
   - `conversations(id, title, created_at, updated_at)`
   - `messages(id, conversation_id, role, content, run_id NULL, ts)`
   - `runs(run_id, ticket_key, track_id, mode, status, conversation_id, created_at, completed_at, tokens_in, tokens_out, cost_usd, summary_json)`
   - `run_steps(id, run_id, name, status, started_at, completed_at, detail, error)`
   - `events(event_id, run_id, ts, type, payload_json)`  ← SSE replay source
   - `approvals(id, run_id, requested_at, resolved_at, decision, comment, payload_json)`
   CRUD helpers: `create_run`, `update_run`, `append_step`, `append_event`, `list_events(run_id, after?)`, `save_message`, etc.
2. `src/orchestrator/events.py` — `EventBus`: `publish(run_id, type, payload)` persists to `events` AND fans out to in-process async subscriber queues (SSE consumers). Envelope exactly per master §5.2 (includes `cost_usd_so_far`).
3. Unit tests: schema creation, publish→persist→subscribe ordering, replay (`list_events`) equals live sequence.
**DoD:** state store + bus tested; a fake run's events fully replayable from the DB.

### Step B.7 — Integration smoke test + GATE 0b — *Owner: Claude Code + (User)*
**Goal:** one script exercises every integration from `aiagent-testmanager`.
**Actions:** Claude Code writes `scripts/test_integrations.py` printing a ✓/✗ table: Jira read + **runid extraction on a real ticket** · Bitbucket read + sandbox branch · DAI log+screenshot by runid · **Practice path dry-run** (push a no-op commit to `/practice`, trigger, poll) · runscript smoke (1-line script on the runner, if local-runscript) · Claude (Opus 4.6 via configured base URL) ping · static call-graph on the 8055 script · ripgrep blast radius · lint on a sample script · SQLite store round-trip. **(User)** run it on the VM; paste the table.
**GATE 0b checklist** (print; (User) confirms): repo+deps ☐ · both VMs provisioned, egress green ☐ · EPF license reserved, SUT reachable ☐ · Jira (incl. runid)/Bitbucket/DAI-evidence/Claude verified from VM ☐ · Practice path triggers + completes ☐ · runscript runs an Enovia script (if local-runscript) ☐ · two remotes configured on the working copy ☐ · handler_map + vocabulary + static modules + lint correct ☐ · context.md curated & reviewed ☐ · evidence retrieval proven (no SharePoint) ☐ · INNER_LOOP flag set ☐ · hourly pull + nightly rebuild scheduled ☐ · state store + event bus tested ☐.
**DoD:** smoke test all-green. **Plan 1 cannot begin until Gate 0b passes.**

➡ Proceed to **plan1_diagnosis_and_chat.md**.
