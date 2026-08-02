# PLAN 0 — PoC DE-RISKING (WEEK 0) + FOUNDATION (WEEKS 1–2) — v2 FOR THE AGENT

> **Prereq:** `plan_master.md` read in full. **Objective:** prove every architectural bet for **JARVIS (Automation Testing Agent)** on real Enovia infrastructure, then stand up the project skeleton, static layer, state store and smoke tests so feature work can begin.
>
> **Why PoCs first:** the design rests on empirical bets — the ticket's `runid` reliably fetches the failing run's log + screenshot via the (User)-provided **production** DAI APIs, the **JARVIS validation flow** works (push to the validation repo `agentic-eggplant-automation@Enovia` → assert the SHA → trigger the suite's JARVIS test config → read the run's results → assert the executed commit SHA), and code-logic bugs dominate the ticket mix. If any is false the design changes. Prove them in days, not after weeks of building. **The validation bet is now proven end-to-end — see A.2 and A.2b.**
>
> **Division of labor:** the Agent writes every script/file. The **(User)** runs anything that needs VMs, credentials, RDP, licenses, or corporate network, and pastes outputs back — and **provides at the marked steps**: the exact Jira base URL, the tested production-DAI log-by-runid API, the error-screenshot identification logic, and the JARVIS DAI / validation repo / test-config-registry details. **Every one-time DAI setup — model import, dispatcher authoring, test-config creation, SUT binding — is done by the (User), Jay.** The Agent never invents PoC results.

---

# PHASE 0.A — WEEK 0: PROOF-OF-CONCEPT GATE

### Step A.0 — PoC workspace scaffold — *Owner: Agent*
**Goal:** a scratch project where all PoC scripts live, plus the results ledger.
**Actions:**
1. At the **repo root** (which **is** the project root — the Bitbucket repo is `jarvis`, so there is no nested project directory), create `scripts/`, `tracks/enovia/`, `samples/`, `tests/`.
2. Create `.env.example` with keys: `JIRA_BASE_URL=` *((User) provides the exact base URL where the tickets live)*, `JIRA_PAT=`, `BITBUCKET_BASE_URL=https://bitbucket.it.keysight.com`, `BITBUCKET_PAT=`, `DAI_BASE_URL=`, `DAI_CLIENT_ID=`, `DAI_CLIENT_SECRET=`, `DAI_AUTH_URL=` *(OAuth2 token endpoint, typically `{DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token`)*, `DAI_LOG_BY_RUNID_URL=` *((User) provides the tested endpoint at A.1, typically `{DAI_BASE_URL}/ai/runlogs/{runid}`)*, `DAI_SCREENSHOT_URL=` *((User) provides at A.1, typically `{DAI_BASE_URL}/api/v2/screenshots/{image_id}`)*, `JARVIS_REPO_URL=` *(the validation repo `agentic-eggplant-automation`)*, `JARVIS_PAT=`, `JARVIS_DAI_BASE_URL=https://eggptdai10.cos.is.keysight.com:8000/`, `JARVIS_DAI_CLIENT_ID=`, `JARVIS_DAI_CLIENT_SECRET=`, `JARVIS_BRANCH=Enovia`, `JARVIS_ENOVIA_SUITES_PATH_IN_VM=C:\Eggplant_Suites`, `JARVIS_COMPLETION_MODE=poll_backoff`, `ANTHROPIC_API_KEY=`, `ANTHROPIC_BASE_URL=` *(direct API or the Keysight gateway)*, `MODEL=claude-opus-4-7` *(the ONLY reasoning model — 4-7 because 4-6 isn't whitelisted on the Keysight gateway; the proven whitelisted Opus IDs are 4-5 and 4-7; we use the newer; see plan_master §6)*, `MODEL_LIGHT=` *(optional, non-reasoning utility only; leave empty to disable)*. Every script that reads this file MUST use `load_dotenv(override=True)` so the project `.env` wins over any parent-shell env vars (plan_master §6.10).
   **Retired keys — do not reintroduce:** the old scalar `PRACTICE_TEST_CONFIG_ID` is **deleted**, superseded by the per-suite registry file `tracks/enovia/test_config_registry.yaml` (decision **D3**, plan_master §2.3.2) — one test config per suite, looked up at runtime, so a single global config ID no longer expresses the mapping. `PRACTICE_STEP_SELECTION` is likewise **resolved and removed**: decision **D1** (the dispatcher pattern) makes per-ticket step selection unnecessary, because the test config stays permanently static and only the dispatcher script's target line changes, via git.
3. Create `tracks/enovia/poc_results.md` with a checklist mirroring Gate 0a (every PoC, a Proven? box, and a Notes column).
4. Create `requirements-poc.txt`: `httpx anthropic pyyaml python-dotenv rich`.
5. **(User)** On your laptop: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements-poc.txt`, copy `.env.example` → `.env` (fill as PoCs proceed; never commit).
**Verification:** tree exists; `.env` is gitignored.
**DoD:** workspace ready; results ledger created.

### Step A.1 — PoC 2: DAI evidence by `runid` (cheapest — do first) — *Owner: Agent + (User)*
**Goal:** wire the **(User)'s already-tested DAI APIs** PLUS the LLM-reasoning step that picks the right error entry: given a Jira ticket + extracted `runid`, fetch that run's log, **LLM-match** the single error entry that corresponds to the ticket's reported failure, **deterministically walk back** to the most recent screenshot, fetch it.
**Actions:**
1. **(User)** provide: (a) DAI API access (`client_id`/`client_secret` via DAI UI → System → API Access, or whatever auth the tested API uses) + DAI base URL + OAuth2 token endpoint into `.env`; (b) the **log-by-runid endpoint** (method, path, params) — paste a sample response; (c) the **screenshot-fetch endpoint** (method, path, params); (d) confirm Eggplant's capture-then-act ordering so the deterministic walk-back logic is correct (the captured screenshot lives in the most recent prior entry with non-null `image_id`); (e) a real sample `runid`.
2. Agent: write `scripts/poc_dai.py` using `load_dotenv(override=True)`:
   - **DAI auth:** OAuth2 `client_credentials` → bearer token (cached in-process).
   - **`fetch_log(runid)`:** `GET {DAI_LOG_BY_RUNID_URL}` → parse `{"items": [LogEntry…], "total_count": N, "date_as_of": ISO}`. `LogEntry` fields: `id, eventtime, testrunid, message, severity, step_id, stage, message_type, image_name, image_id`.
   - **`find_error_log_index(logs, title, description)` [LLM reasoning step]:** forced tool-call to the project's reasoning model (`MODEL`, currently `claude-opus-4-7`); inputs are the ticket `title`+`description` and a compacted list of `{i, message_type, severity, message}`; output is the index of the SINGLE entry whose `message` semantically matches the failure (e.g. ticket says *"release was not able to identify"* → the `"Unable to Find Image (TEXT:\"Released\"). Text not found."` entry; ticket says *"Set Enterprise Item Number"* → that entry, not an earlier `Login` failure). Severity is NOT a reliable filter — real failures are typically `severity=INFORMATIONAL` with `message_type=imagefound`.
   - **`find_last_screenshot_before(logs, error_index)` [deterministic walk-back]:** scan indices `error_index-1, error_index-2, …, 0`; return the first entry whose `image_id` is non-null and non-empty. Returns `None` if no captured frame exists before the failure (should be vanishingly rare in real runs).
   - **`fetch_screenshot(image_id, dest)`:** `GET {DAI_SCREENSHOT_URL}` → write PNG bytes.
   - **Print:** `len(logs)`, the matched error `message`, the matched `image_id`, the saved path.
3. **(User)** run it end-to-end on the sample ticket; paste output into chat and `poc_results.md`.
**Verification:** for TESTAUTOMA-8055 (or the chosen ticket): runid extraction returns the right number, the LLM matches the correct error entry (not the first/any unrelated image-find failure), and the walk-back returns the captured screenshot the test was acting against. (Hard-coded `--runid <N>` mode is allowed as a fallback for credential-free testing, but it uses a deterministic "first imagefound failure" heuristic and is known to pick the WRONG entry when a run has multiple failures — by design, to demonstrate why the LLM step is required.)
**DoD:** log-by-runid + LLM-error-match + deterministic-walk-back + screenshot-fetch all proven on real DAI; the exact JSON shape (`items[]`, `LogEntry` fields above) and the four endpoints (auth, runlogs, screenshots, Jira issue) recorded in `poc_results.md` A.1. *If it fails:* wrong base URL / cert trust (install CA) / API access disabled / model not whitelisted on the gateway (4-6 vs 4-5; see plan_master §6) — **(User)** files the IT ticket or rotates the model now.

### Step A.2 — PoC 2b: the JARVIS validation path end-to-end — *Owner: Agent + (User)* — **✅ PROVEN**
**Goal:** prove the full JARVIS validation cycle: push the candidate to the **validation repo** `agentic-eggplant-automation` branch **`Enovia`** → **assert the pushed SHA** (`git ls-remote`) → trigger that suite's **JARVIS test config by ID** on the **JARVIS DAI** via the (already-tested) trigger API → detect completion → fetch the run's results / log / screenshots via the v2 chain → **assert the executed commit SHA** recorded in the run log.

**Recorded infrastructure values (no longer "(User) provides" — these are measured facts, plan_master §3):**

| Role | Value |
|---|---|
| Production DAI (evidence, READ-ONLY) | `epcorpappsdai12`, DAI **25.3.1+0** |
| JARVIS DAI (execution) | DAI **26.2.2**, Jay-administered. **Base URL `https://eggptdai10.cos.is.keysight.com:8000/` — HTTPS, port 8000.** Same VM as the Design + Run agents, `C:\Eggplant_Suites` and (at `:8080`) the JARVIS orchestrator itself (plan_master §3) |
| Validation repo / branch | `bitbucket.it.keysight.com/scm/eggauto/agentic-eggplant-automation.git` / **`Enovia`**; git remote name `agentic-eggplant-automation` |
| Production repo / branch | `enovia-plm-test-automation.git` / `Testing_Mar10`; git remote name `origin` |
| Agents | `Test26_2_Design` + a Run environment, **co-located on the JARVIS VM**, licensed **EPF 26.2.x** |
| Version policy | DAI / agents / EPF **lockstep at 26.2.x**; `.ini` access keys are instance-specific (HTTPS, 26.2.1+); production agents/certs **not reusable** |
| SUT | `Jay_130`, registered by hostname + RDP credentials — **already bound; no Agent setup required** |
| Suites folder on the JARVIS VM | `C:\Eggplant_Suites` (a git clone of the validation repo) |
| Onboarded suite | `Part_Master_Pack_01` / PartMaster |

**Auth (JARVIS DAI):** `POST /api/v2/auth` with `client_id` / `client_secret` from JARVIS **API Access** → bearer token, **~10-minute expiry**, cached in-process and refreshed on expiry. This is **not** the production DAI's scheme (OAuth2 client-credentials against the Keycloak realm) — the two instances must never share a client, token cache or base URL.

**Results chain (v2):**
```
GET /api/v2/test_config_results?test_config_id=<ID>   → newest result id
GET /api/v2/test_results?test_config_result_id=<id>   → step result + status
GET /api/v2/test_results/{test_result_id}/logs        → entries (message, severity, message_type, image_id)
GET /api/v2/screenshots/{screenshot_id}               → PNG (PoC-2 walk-back logic reused)
```

**Completion-detection mechanism — the decision record.** JARVIS validation runs take 20 min–2 hr; the wait must cost zero LLM tokens and zero busy-work regardless of which option below is used — Claude is only ever invoked before the gate (generate the fix) and after it resolves (interpret PASS/FAIL). The three options were evaluated in priority order and are **kept here as the permanent decision record**:
1. **DAI Webhooks (the upgrade path — available, not yet registered).** DAI supports a generic custom-HTTP webhook profile (*System → Webhooks*, requires DAI Administrator) fired on test-config-run completion, with a JSON payload (`test-configurations`, `result-status`, `result-url`, `test-run-completed`, `execution-start-time`, `total-run-duration`) sent to any URL you configure — not restricted to Slack/Teams/PagerDuty. Wire it to a new `POST /api/webhooks/dai` route (same pattern as the already-planned `POST /api/webhooks/bitbucket`); the orchestrator awaits an `asyncio.Event` per run instead of polling — zero HTTP calls, zero LLM calls, zero compute while waiting; the event fires the instant the webhook lands. **RESOLVED:** the webhooks admin UI **is available on JARVIS and Jay is admin**, so webhooks are enable-able. The profile is **not yet registered** — carried as open item **O1**. Still to confirm at registration time: whether the run identifier is an available payload variable for correlating the webhook back to the triggered run (if not, correlate via `result-url` or test-config name + last-triggered record).
2. **`eggplant-runner` CLI (fallback).** The CLI blocks synchronously until the run completes, exit code 0 = pass / nonzero = fail, `--result-path` for JUnit XML. Run via `asyncio.create_subprocess_exec` + `await proc.wait()` — no polling code to write, no tokens burned either way, but ties up a live process on a specific host for the run's duration and gives coarser live-progress data for the chat UI than a webhook does.
3. **Polling with exponential backoff — ✅ SELECTED as the day-one mode.** A plain `httpx` GET in an `asyncio.sleep`-based orchestrator coroutine — never an LLM tool call, so it costs no tokens regardless of duration, but still costs a live coroutine and repeated HTTP calls. As used: exponential backoff (15s → 30s → 60s → 120s cap), not a flat interval, and a timeout that actually covers the observed 20 min–2 hr range (config-driven per test config, not a fixed low number).

**Decision recorded:** `JARVIS_COMPLETION_MODE=poll_backoff` from day one; **webhook is the upgrade path, not a prerequisite** (O1). Option 2 (`eggplant-runner` CLI) remains documented but unselected.

**Actions:**
1. **(User)** — **done.** Provided and recorded in the table above: validation repo URL + PAT (push rights to `Enovia`), JARVIS DAI base URL + v2 client credentials, the per-suite `TEST_CONFIG_ID` (recorded in `tracks/enovia/test_config_registry.yaml`, D3), and the **trigger API** spec (trigger a test config by ID — the existing, already-tested API). Confirmed: the test config's git connection points at the validation repo and **syncs at run start** (not a cached clone), and the SUT connection is prebuilt.
2. Agent: write `scripts/poc_jarvis_validation.py` — pull the working copy; commit a trivial change; **force-push** `wc/<TICKET>:refs/heads/Enovia` to the `agentic-eggplant-automation` remote; **assert `git ls-remote agentic-eggplant-automation refs/heads/Enovia` equals the pushed SHA**; call the trigger API with the registry's `test_config_id`; detect completion via `poll_backoff`; walk the four-call v2 results chain to fetch status + logs + screenshots; **assert the run log's `Using Git commit SHA: '<sha>'` equals the pushed SHA**; print the full timeline (push→assert→trigger→complete→assert) with durations.
3. **(User)** run it; paste output. Time the cycle — this is the per-attempt validation latency.
**Verification:** a code push demonstrably reaches the SUT run (the triggered run executes the pushed `Enovia` state, evidenced by the commit SHA in the run log) and its results are fetched programmatically via the v2 chain, using backoff polling (not naive tight polling).
**DoD:** push → SHA assert → trigger → completion-detected-without-busy-polling → results → executed-SHA assert, all proven; cycle time recorded in `poc_results.md`; mechanism recorded as `JARVIS_COMPLETION_MODE=poll_backoff` for plan2 Phase 2.5 to consume.

**✅ STATUS: PROVEN END-TO-END.** Model import; validation repo connected via git; SUT configured with a JARVIS execution environment; co-located Design + Run agents; repo cloned to `C:\Eggplant_Suites` with scripts surfacing in the Modeler's Snippets panel; `AgentDispatcher` model action authored and validated; **a full PASSED run with the git commit SHA traceable in the run log.** Because run→commit integrity is solved, plan4's **UP-24 is fully implementable rather than a residual risk**.

**⚠ OPEN — residual items, carried forward, NOT marked done:**

| ID | Open item |
|---|---|
| **O1** | Webhook profile not yet registered on JARVIS (`poll_backoff` is the day-one mode). |
| **O2** | Suite-name collision behaviour as suites accumulate on the JARVIS instance (**constraint C2** — suite names must be globally unique per DAI instance; plan_master §2.3.1). |
| **O3** | Per-cycle wall-clock timing across a realistic suite set — needed for the plan2 Gate 2 "avg fix+validation time" row. |
| **O4** | Scale-out: only `Part_Master_Pack_01` is onboarded. Every other suite needs the D2 onboarding sequence (Step B.4b). |
| **O5** | ⚠️ **MITIGATED by the O6 decision** (not closed — the underlying mechanic stands). Force-pushing the full candidate state onto `Enovia` replaces the branch contents, so dispatchers for suites *other than* the target suite disappear unless regenerated. Regenerating **every** registered suite's dispatcher on every push is what removes the risk. |
| **O6** | ✅ **RESOLVED 2026-07-28.** Every registered suite has its **own** dispatcher script **and its own test config** executing that dispatcher; on **every** push JARVIS regenerates the dispatcher for **every suite in the registry**, so the `Enovia` branch is always complete. This is a **rule**, not a recommendation (plan_master §2.3.2 D4, plan2 §2.5.0). |
| **O7** | Monthly model re-import from the production DAI into JARVIS is currently an **undocumented manual activity** and must become a written maintenance procedure performed by Jay every time (`docs/maintenance.md`, plan3 §3.7). Person-dependency. |

### Step A.2b — Dispatcher pattern proof (dynamic target selection) — *Owner: Agent + (User)* — **✅ PROVEN**
**Goal:** prove that the script a JARVIS validation run executes can be switched **purely by a git push**, with the DAI test config left completely untouched. This is the workaround for **constraint C1** (DAI public API v2 has no test-config or step create/edit endpoints, so a config's steps cannot be rewritten per ticket) and the proof of **decision D1** (the dispatcher pattern).

**Actions:**
1. Agent: generate `<Suite>_AgentDispatcher.script` from `src/analysis/templates/agent_dispatcher.st.j2` (plan_master §2.3.3) with the target set to a known-good test case, written per **S1** (`TestCases/<name>` — no `.script` extension, no `Scripts/` prefix) and invoked per **S2** (plain `run targetScript`, never `targetScript.run()`).
2. Commit and **force-push** the candidate state to `agentic-eggplant-automation@Enovia`; trigger the suite's test config by ID.
3. Confirm the run log contains **both dispatcher marker lines** (`start — target=…` and `done — target=…`) **and** the target script's own execution entries — i.e. the dispatcher really delegated.
4. **Negative test:** switch the dispatcher's target to a deliberately broken script. Push again. **Touch nothing in DAI.** Re-trigger. Confirm the run **fails on the target** — proving the absence of `try/catch` in the template is load-bearing, since a swallowed target failure would produce a false PASS.
**Verification:** the **same `test_config_id`** executed a **different script**, and the only difference introduced between the two runs was a git push. No DAI UI interaction, no API config edit.
**DoD:** the dispatcher claim is proven; **C1 is formally worked around**; **S1 and S2 are recorded** as binding constraints on the template and on the target-path derivation logic (plan_master §6.12, plan2 §2.5.0). Proven on **`Part_Master_Pack_01` / the PartMaster suite**.

### Step A.3 — PoC 1: EPF `runscript` runs an Enovia script headless *(DEFERRED — optional latency optimisation; not required for any gate in this version)* — *Owner: (User), script by Agent*
**Goal:** prove Eggplant Functional executes an Enovia `.script` from CLI → results folder + exit code (the fast inner loop's basis).
> **Deferred.** JARVIS is the single mandated validation mechanism (plan_master §2.1, §2.3), so the local `runscript` inner loop is no longer on the critical path and is required by no gate in this version. This step is retained in full as a documented option; see `docs/later-enhancements.md`.
**Actions:**
1. **(User)** RDP to `eggptdai10` (156.140.21.30); confirm Eggplant Functional installed + floating license reachable (Preferences → Run; note `-LicenserHost`).
2. **(User)** `git clone https://bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git C:\agent\repo && cd C:\agent\repo && git checkout Testing_Mar10`.
3. Agent: write `scripts/poc_runscript.ps1`:
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

### Step A.4 — PoC 1b: SUT connection OUTSIDE DAI (decides the fast inner loop) *(DEFERRED — optional latency optimisation; not required for any gate in this version)* — *Owner: (User), guided by Agent*
**Goal:** decide whether `runscript` can establish the RDP SUT connection without DAI injecting it. This decides whether the **fast local inner loop** exists — it is no longer project-blocking, because the JARVIS validation gate (A.2) is proven and serves every attempt.
> **Deferred.** JARVIS is the single mandated validation mechanism (plan_master §2.1, §2.3), so the local `runscript` inner loop is no longer on the critical path and is required by no gate in this version. Retained in full as a documented option; see `docs/later-enhancements.md`.
**Actions:**
1. **(User)** `rg -n "Connect\b|ConnectionInfo|RemoteWorkInterval|RDP" C:\agent\repo\Enovia` — do the suites contain an explicit `Connect`?
2. **(A) explicit Connect found** → the Agent writes a one-line probe script (`Connect ServerID:"<sut>", … ; Log "connected: " & ConnectionInfo() ; Disconnect`); **(User)** runs it via runscript. Connects → **A holds**.
3. **(B) no Connect — DAI injects** → either **(b1)** the Agent writes a thin connection-wrapper script prepended for validation (SUT details from DAI's environment), or **(b2)** use the **JARVIS validation gate for every attempt** (A.2 already proved it; slower per attempt, same architecture).
**DoD — record the selected mechanism:** `VALIDATION_MECHANISM=jarvis-dai` in `poc_results.md` and `.env`. **This is the selected mechanism for this version and plan2 does not branch.** The local-runscript variant (A/b1) stays **recorded but unselected** as the deferred latency optimisation (`docs/later-enhancements.md`).

### Step A.5 — PoC 1e: `runscript` run ≡ DAI run parity *(DEFERRED — optional latency optimisation; not required for any gate in this version; relevant only if the local-runscript variant is later revived)* — *Owner: (User)*
**Goal:** a test that passes under DAI also passes under `runscript` (no hidden DAI-injected params/`RunValues`/data).
> **Deferred.** JARVIS is the single mandated validation mechanism (plan_master §2.1, §2.3), so the local `runscript` inner loop is no longer on the critical path and is required by no gate in this version. Retained in full as a documented option; see `docs/later-enhancements.md`.

**Actions:** **(User)** run the PoC-1 test (a) via DAI and (b) via runscript (A.3); compare pass/fail, key log lines, and any "missing parameter / undefined RunValues" errors.
**DoD:** documented parity, OR a documented list of DAI-supplied params to pass via `-param`/globals. **If parity can't be bridged, the local-runscript variant stays permanently unselected** and `VALIDATION_MECHANISM=jarvis-dai` remains the mechanism.

### Step A.6 — PoC 3: SenseTalk static call-graph + ripgrep blast radius — *Owner: Agent + (User)*
**Goal:** deterministic retrieval works on real Enovia scripts (the RAG replacement).
**Actions:**
1. Agent: write `scripts/poc_static.py` — seed `HANDLER_MAP` (CommonEnovia, common, configEnovia, LaunchApp → known paths); regex `\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b` for calls; recursive `call_chain(test_path, depth=3)`; `blast_radius(handler)` = `rg -n "\b<handler>\b" <repo>`. Also write `tests/test_poc_static.py` with synthetic SenseTalk fixtures (the Agent can fully verify this PoC's logic locally).
2. **(User)** run it on the TESTAUTOMA-8055 script + 4 others spanning bug families on the VM clone; paste outputs.
**Verification:** 8055 chain surfaces `EngineeringCentral → CommonEnovia` (incl. `searchEnovia`); `blast_radius("searchEnovia")` equals a manual grep — zero missed callers. (`rg`: `winget install BurntSushi.ripgrep.MSVC`.)
**DoD:** chain + blast radius correct on 5 real scripts.

### Step A.7 — PoC 4: Bitbucket Server read / branch / PR (sandbox) — *Owner: Agent + (User)*
**Goal:** confirm Bitbucket **Server/DC** REST shapes (not Cloud).
**Actions:** the Agent writes `scripts/poc_bitbucket.py`: read `GET {B}/rest/api/1.0/projects/EGGAUTO/repos/enovia-plm-test-automation/raw/<path>?at=Testing_Mar10`; branch create `POST {B}/rest/branch-utils/1.0/projects/…/branches {name:"Jarvis-fix/POC-TEST", startPoint:"Testing_Mar10"}`; PR create `POST …/pull-requests` with `fromRef/toRef` refs objects. **(User)** provides PAT (Repo R/W, PR R/W, Branch create), runs against a **sandbox repo** for the PR write, then deletes the test branch.
**Two repos, two permission sets — do not conflate:**
- **This step proves read / branch / PR against the *production* repo path** (`enovia-plm-test-automation`, project `EGGAUTO`). That is the plan3 PR target, written only as `Jarvis-fix/<TICKET>` after PASS + approval.
- **Push access to the *validation* repo** (`agentic-eggplant-automation`, branch `Enovia`) is a **separate PAT / permission** and must be confirmed independently — the validation gate force-pushes there on every cycle, which is a different right from opening a PR.
**Validation-repo permission — settled.** Jay holds **admin** on the validation repo, and force-push to `refs/heads/Enovia` with the configured PAT (`JARVIS_PAT`) **works**. No branch-permission exemption is outstanding.

> **The permissions half of this step's DoD is ALREADY SATISFIED — do not re-litigate it.** Jay holds
> organisational approval (Megha, Mahavir, Gaurav) for these operations on `enovia-plm-test-automation`,
> and his Bitbucket PAT carries the required access. **What this step still proves is purely the
> Bitbucket *Server/DC* REST API shape** — the branch-create endpoint
> (`/rest/branch-utils/1.0/…` with `{name, startPoint}`) and especially **PR create with
> `fromRef`/`toRef` refs objects**, which differs from Cloud. That makes this a **cheap smoke test**
> rather than a risk gate: run it any time **before plan3 §3.2**, which is the first step that depends
> on it. Note that **B.7's smoke covers read + sandbox branch only — PR create is the one shape it does
> not exercise.**

**Specification — `scripts/poc4_bitbucket.py`, enough to hand to an implementer:**
- **Run it against `agentic-eggplant-automation`** — Jay's own repo — **not** the production repo. This is safe *and* sufficient because **Bitbucket Server API shapes are server-wide, not per-repo**: the endpoint contract is identical, so the production repo is never touched to learn it.
- **Sequence, cleaning up after itself:** read repo metadata → read a file at a ref → create a branch → **create a PR** → read it back → **decline** it → delete the branch.
- **The call that matters is PR create with `fromRef`/`toRef` as objects** (`{id: refs/heads/<b>, repository: {slug, project: {key}}}`). That is where **Server differs from Cloud**, and it is the one shape **B.7's smoke does not exercise** — B.7 covers read + sandbox branch only.
- **Deliverable:** the **actual request/response JSON** pasted into `poc_results.md`. Not "it worked" — the shapes, so the client is written against observed reality.

**Verification:** read returns content; branch 201; **PR 201 (sandbox) — the shape that matters**; a force-push to the validation repo's `Enovia` branch succeeds with the credential recorded as `JARVIS_PAT`.
**DoD:** the **API shapes** proven on the production repo path (read + branch + **PR create**); validation-repo force-push permission separately confirmed; both PAT scopes recorded. *(Permissions: already satisfied — see above.)*

### Step A.8 — PoC 5: Jira DC read / comment / attach + **LLM-based ticket-metadata extraction** — *Owner: Agent + (User)*
**Goal:** confirm **REST v2 (Data Center)** behavior on a disposable test ticket, AND prove the four ticket fields the pipeline needs — `runid`, `title`, `description`, `test_script_name` — are reliably extractable from real tickets by the LLM regardless of where in the response they live or what casing/phrasing they use.
**Actions:** **(User)** provides the exact `JIRA_BASE_URL` + PAT, plus 2–3 real ticket examples incl. TESTAUTOMA-8055 — **without** prescribing where the runid lives (description text, summary, a custom field, a comment, an attachment name, any of `runid`/`run id`/`Run ID`/`RUN ID`/`testrunid=` — all in scope). the Agent writes `scripts/poc_jira.py`: `GET /rest/api/2/issue/{KEY}` with `Authorization: Bearer <PAT>` (request `fields=*all` once to see custom fields); `extract_ticket_metadata(issue_json) -> {runid, title, description, test_script_name, reasoning}` — a forced tool-call to the project's reasoning model (`MODEL`, currently `claude-opus-4-7`) that searches the ENTIRE response and returns the four fields in structured form, with a short `reasoning` field naming where each value came from; a small deterministic regex/custom-field check may be kept as a sanity-cross-check but is NOT the primary extractor; comment `POST …/comment {body:"…"}` (v2 = plain/wiki body, NOT ADF); attachment `POST …/attachments` with header `X-Atlassian-Token: no-check`; list `GET …/transitions`. **(User)** runs on a test ticket + the 2–3 real examples.
**Verification:** read/comment/attach succeed; transitions listed; **all four metadata fields extracted correctly from every provided real ticket** (the LLM's `reasoning` line for each ticket is human-checked and recorded). The script also runs end-to-end against TESTAUTOMA-8055 producing the same runid that PoC 2 then uses downstream.
**DoD:** v2 confirmed; LLM-extraction prompt + tool schema recorded in `poc_results.md`; per-ticket extraction results recorded; note whether the service account can transition status — if not, **label is the reliable signal** (plan3 relies on this).

### Step A.9 — PoC 6: Claude reachable with working credentials — *Owner: Agent* — **✅ PROVEN (connectivity, from the development machine)**
**Goal:** prove the engine is reachable and the credentials work — `MODEL` (Opus 4.7) answers through `ANTHROPIC_BASE_URL` (the Keysight gateway).
**Actions:**
1. **(User)** place into `samples/`: the 8055 test script, `CommonEnovia.script` (incl. ~line 409), and the DAI failure-log excerpt.
2. Agent: write `scripts/poc_claude.py` — a draft diagnosis system prompt (full version in plan1) + user message embedding ticket/script/handler/logs with untrusted-data delimiters; call **`MODEL` (Opus 4.7)** via `ANTHROPIC_BASE_URL` (proves the gateway path too); print the response.
3. Run it from the **development machine**; paste output.
**Verification:** a successful authenticated call returns a response — engine reachable, credentials valid, gateway path working.
**DoD:** ✅ **met.** Opus 4.7 answered through the Keysight gateway, after root-causing the `claude-opus-4-6` whitelist gap and the `load_dotenv(override=True)` masking (PROGRESS 2026-06-12).

> **Two claims this step deliberately does NOT make, and where each is actually discharged:**
> - **It was not run on a VM.** VM egress to the gateway is verified in **Step B.7**, where the full
>   integration set runs on `eggptdai10` for the first time. If egress fails there, **(User)** files
>   the firewall ticket at that point.
> - **It did not re-derive the 8055 diagnosis.** Reproducing the root cause — naming
>   `CommonEnovia.script` ~409 and the `and not ImageFound(text:"Name",…)` clause with the
>   "passed-with-swallowed-exceptions" observation — is **plan1's golden regression** (plan1 §1.4.5
>   Verification, scored at Gate 1). It is not weakened, only verified where it belongs.

### Step A.10 — PoC 7: base-rate study — *Owner: Agent + (User)*
**Goal:** order the suite-onboarding queue now, and assemble the ≥50-ticket labelled set by the time Gate 1 is scored.

#### Part 1 — the decision rule is **RETIRED**
The former rule — *code-reasoning families ≥60% → proceed · 40–60% → vision post-Phase-2 · <40% → **STOP*** — is **deleted**.

**Why (ruled by Jay, 2026-07-29):** Jay ran the **full diagnosis→fix→validate flow manually across 10–12 real Enovia tickets** — repo connected, real DAI error logs and screenshots supplied, fixes validated, failures iterated on. **That is direct evidence of engine fit, and it is stronger than a category-label distribution**, which only ever proxied for it. It also settles the vision question empirically: **vision stays deferred** (and `view_screenshot` is already an on-demand tool, so nothing is blocked either way). Those tickets are captured in `tracks/enovia/ticket_findings.md` (B.4 action 6).

#### Step A.10a — suite-frequency count — small, scripted, **no human labelling**
Agent: `scripts/categorize_tickets.py` runs the JQL `project = TESTAUTOMA AND component = "Enovia PLM Automation" AND status = Done ORDER BY resolved DESC` and, for each resolved ticket, records **only the failing test and the suite that owns it**, then prints a frequency table.

**Specification — enough to hand to an implementer:**
- **In:** the JQL above. **Out:** `tracks/enovia/ticket_base_rate.json` plus a frequency table on stdout, ranked descending by ticket count per suite.
- **Per ticket, record exactly two things:** the **failing test** and the **suite that owns it** (resolve via the same rule as `validation_suite_of` — owner of the failing test, then the JIRA number→suite range; plan2 §2.5.0).
- **Explicitly NOT in scope here:** no family labels, no root-cause analysis, no human review pass. **That is A.10b**, and conflating them is what turns a twenty-minute script into a four-hour session.
- **Purpose, stated plainly:** it produces the **frequency-ranked onboarding order for O4's remaining fifteen suites**, which are otherwise onboarded in arbitrary order. Two of seventeen are done; the ranking decides which of the fifteen is worth the next D2 sequence.

**Why this half is worth doing early:** it produces a **frequency-ranked onboarding order for O4**. Jay is otherwise onboarding 16 suites in arbitrary order, and **O4 is the largest constraint on how much of the ticket flow JARVIS can serve** — onboarding the highest-frequency suites first is the difference between covering most tickets early and covering them last. It also answers **O9**'s scheduling question as a by-product.
**No family labels, no root-cause analysis, no human review pass.**

#### Step A.10b — the ≥50 labelled set — **deferred to Gate 1 scoring**
Same script, `--label` mode: drafts categories from the master's failure families via `MODEL_LIGHT` for **(User)** confirmation → `tracks/enovia/ticket_base_rate.json`. **Not a Phase 0.B activity and not a plan1 blocker.** Carried as open item **O8** against **Gate 1**.

#### Part 3 — the dataset accumulates as a **by-product**, so nothing is re-labelled later
This is the mechanism that replaces the labelling session, and it is a **build requirement, not a testing one**. UP-11 already states the flywheel is *"wired from day one"*, so this adds fields to a schema being built anyway.

The **trajectory record must carry the labelling columns from day one** — `src/models/trajectory.py`, and whatever `flywheel/trajectory_logger.py` writes into `data/trajectories/enovia.jsonl` (specified at plan3 §3.6.1):

```
failing_test · owning_suite · family · families_present[] · multi_cause
knowledge_source · fixable_component · vision_needed
```

These are exactly A.10's columns plus plan4 §4.0 item 2's three additions. **Reason, recorded inline:** every ticket JARVIS processes during development yields these fields **for free**; plan4 §4.0 item 2 warns that omitting them means **a human re-labels ≥50 tickets by hand later**. This is how that is avoided without ever holding a labelling session.

> **Honest limitation — do not drop this line:** tickets processed during development are a
> **self-selected sample**, so they support *tracking improvement* but **not a headline base-rate
> claim**. When Gate 1 is scored, draw the ≥50 sample by JQL (**A.10b**); by then most of its labels
> already exist.

**DoD:** **A.10a** — suite-frequency table produced and used to order O4. **A.10b** — carried as **O8**, due at Gate 1 scoring, not before.

### GATE 0a — PoC GO/NO-GO — *Owner: (User) decision, checklist by Agent*
Print and have the user confirm:
| PoC | Proven? |
|---|---|
| 2 production-DAI log + error screenshot by `runid` (User's APIs) | ✅ **PROVEN** — PROGRESS 2026-06-12 (runid 30832, 402 log entries, error idx 384, 111 KB PNG) |
| 2b **JARVIS validation path**: push `agentic-eggplant-automation@Enovia` → SHA assert → trigger the suite's test config → fetch results → executed-SHA assert | ✅ **PROVEN** |
| 2b-bis **Dispatcher pattern (A.2b)**: target switched purely by git push, DAI test config untouched | ✅ **PROVEN** |
| 1 runscript headless + results folder | n.a. (deferred) |
| 1b SUT outside DAI → **`VALIDATION_MECHANISM=jarvis-dai` recorded** | n.a. (deferred) |
| 1e runscript ≡ DAI parity *(local-runscript path only)* | n.a. (deferred) |
| 3 static call-graph + ripgrep | **RETIRED — superseded by B.4**, which builds the parser, call-graph, ripgrep search and lint as **real modules with unit tests**. A separate PoC adds nothing. *Superseded, not skipped* — the risk it existed to retire is retired by a stronger mechanism. **B.4 itself is untouched.** |
| 4 Bitbucket read/branch/PR | ☐ **not done — cheap smoke test, any time before plan3 §3.2.** *Permissions are settled*: Jay holds organisational approval (Megha, Mahavir, Gaurav) for these operations on `enovia-plm-test-automation`, and his Bitbucket PAT carries the required access. **What remains unproven is purely the Bitbucket *Server/DC* API shape** — specifically **PR create with `fromRef`/`toRef` refs objects**, which differs from Cloud. B.7's smoke covers **read + sandbox branch only**, so **PR create is the one shape it does not exercise.** |
| 5 Jira read/comment/attach + **runid extraction rule** | ✅ **PROVEN** — PROGRESS 2026-06-12 (Jira REST v2 fetch + LLM runid extraction) |
| 6 **Claude reachable with working credentials** | ✅ **PROVEN (connectivity, from the development machine)** — Opus 4.7 through the Keysight gateway, after the `claude-opus-4-6` whitelist and `load_dotenv(override=True)` root-cause (PROGRESS 2026-06-12). **Not** run on a VM (that folds into B.7) and did **not** re-derive the 8055 diagnosis (that is plan1's golden regression) |
| 7 base rate supports approach | ☐ **not done** — Gate 1 cannot be *scored* without it |
| dedicated EPF license + RDP SUT secured **(User)** | ✅ **PROVEN** — EPF, the licenser, the co-located Design + Run agents and the `Jay_130` SUT connection are installed and configured, evidenced by A.2/A.2b's full **PASSED** run (PROGRESS 2026-07-28) |
**Rule:** **Gate 0a passes on PoC 2 + PoC 5 + the JARVIS validation path (2b + A.2b) — all proven.**

- **PoC 3** is **superseded** by B.4, which builds the same capability as unit-tested modules.
- **PoC 4**'s permissions half is **already satisfied**; its **API-shape** half is a **cheap smoke test that must pass before plan3 §3.2**.
- **PoC 7**'s decision rule is **retired** on the evidence of **10–12 manually executed tickets**. Its labelling **exercise** is deferred: **A.10a** (suite-frequency count) is small and scheduled; **A.10b** (the ≥50 labelled set) is carried as **O8** against **Gate 1**, fed by trajectory records accumulated during development.

**Phase 0.B may begin.** *(2026-07-28 / 2026-07-29, ruled by Jay.)*

JARVIS is the single mandated validation mechanism, so the old either/or with the local `runscript` loop no longer applies. If the validation path or the evidence chain were to fail → STOP and re-architect that part before any build.

---

# PHASE 0.B — FOUNDATION (WEEKS 1–2)

### Step B.1 — Project repo bootstrap — *Owner: Agent + (User)*
**Goal:** the agent's own repo, exactly per the master layout (§4).
**Actions:**
1. **The agent repo is local-only for now — its repo-side actions are DEFERRED, not deleted.** Git tracks the project on the **(User)'s** machine and **no Bitbucket remote is configured yet**. The Bitbucket repo `jarvis` exists and is empty. Still required for the **(User)**, before any team member reads the code — unchanged in substance, only in timing: configure the `origin` remote, confirm the default branch, set the **≥1 PR approval** rule, and issue a repo PAT (Repo R/W, PR R/W, Branch create).
   *(This is the **agent** repo's `origin` → `jarvis`. It is a different clone from the **Enovia working copy**, whose own `origin` → `enovia-plm-test-automation`; see plan_master §4.1. **The validation repo is unaffected** — `agentic-eggplant-automation` is still force-pushed every validation cycle and `JARVIS_PAT` is still required today.)*
2. Agent: create the full directory tree from master §4 (empty `__init__.py` everywhere), `README.md`, `PROGRESS.md`, `.gitignore` (`.env`, `data/`, `*.log`, `.venv/`, `node_modules/`, `webapp/dist/`), and `pyproject.toml`:
```toml
[project]
name = "jarvis"
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
3. Agent: create `config/enovia.yaml` skeleton — `repo` (project/slug/branch/local_path, **`origin` + `agentic-eggplant-automation` remotes**), suites list, number→suite ranges, `dai` (**production** base_url, log-by-runid endpoint, screenshot logic params, OAuth2/Keycloak auth), and the **`jarvis`** block replacing the old `practice` block:
```yaml
jarvis:                                     # the JARVIS validation gate — plan_master §2.3
  repo_url: <JARVIS_REPO_URL>               # agentic-eggplant-automation
  branch: Enovia                            # force-push target for every validation cycle
  dai_base_url: https://eggptdai10.cos.is.keysight.com:8000/   # JARVIS DAI 26.2.2 — NOT the production DAI
  auth:                                     # v2 client-credentials; ~10-min bearer, cached + refreshed
    mode: v2_client_credentials
    token_path: /api/v2/auth
    client_id: <JARVIS_DAI_CLIENT_ID>
    client_secret: <JARVIS_DAI_CLIENT_SECRET>
  completion_mode: poll_backoff             # day one; webhook is the upgrade path (O1)
  poll_backoff: [15, 30, 60, 120]           # seconds; exponential, capped — never a flat interval
  run_timeout: <must cover the observed 20min-2hr range>
  suites_path: C:\Eggplant_Suites           # JARVIS VM clone of the validation repo
  test_config_registry: tracks/enovia/test_config_registry.yaml   # D3 — suite -> test_config_id
```
   …plus `llm` (`model: claude-opus-4-7`, `anthropic_base_url`, optional `model_light`, `engine_mode: agentic`, `thinking_on_escalation: true`), `validation` (**`mechanism: jarvis-dai`** — replacing the old `inner_loop` flag; timeouts, `max_attempts: 3`, `n_best_on_retry: 2` **unchanged**), `approval_mode: manual`, `budget_usd_per_run: 10.0`.
> **Local development environment — no provisioning step, by design.** Any package or tool the local
> machine is missing is installed **inline by the coding agent as the need arises**, with **(User)**
> granting permission at that moment. There is no separate provisioning step for the development
> machine and none should be invented. B.2 provisions the **VM**, and only at deployment.

**Verification:** `pip install -e .[dev] && python -c "import fastapi, anthropic, structlog; print('ok')"`; `ruff check` clean.
**DoD:** repo tracked locally; deps resolve; tree matches master layout. *(The repo-side actions in step 1 — remote, default branch, approval rule, repo PAT — are **deferred**, not part of this DoD.)*

### Step B.2 — JARVIS VM provisioning script — *Owner: Agent writes, (User) runs*
**Goal:** the JARVIS VM (`eggptdai10`) ready. **One machine, one script.**

> **What is already done, and proven.** Eggplant Functional + `runscript.bat`, the licenser, the
> co-located Design and Run agents, `C:\Eggplant_Suites`, and the SUT connection to `Jay_130` are all
> **installed and configured**, evidenced by A.2/A.2b's full **PASSED** run with the commit SHA traceable
> in the run log. **The script therefore VERIFIES these components; it does not install them.**

**Actions:**
1. Agent: `scripts/setup_vm_jarvis.ps1` — **one script for the one machine.** *(It replaces the earlier pair of per-VM scripts; two scripts for one host is how the two-VM confusion returns.)* It contains:
   - **winget installs:** Python 3.11, Git, Node LTS, `BurntSushi.ripgrep.MSVC`; `pip install uv`.
   - **an egress check loop** over `https://jira.it.keysight.com`, `https://bitbucket.it.keysight.com`, `$env:DAI_BASE_URL`, `$env:JARVIS_DAI_BASE_URL` and the configured Anthropic base URL, printing OK/FAIL per URL.
   - **an Eggplant component verification table (✓/✗, verify only):** Eggplant Functional + `runscript.bat` path present · `-LicenserHost` reachable · Design and Run agents registered · `C:\Eggplant_Suites` present and a clone of the validation repo · the `Jay_130` SUT connection reachable.
2. **(User)** run it on the JARVIS VM; reserve **one EPF floating license** for the agent (license admin); paste the results.

#### Step B.2a — VM egress — ✅ **VERIFIED, nothing to run**
**(User)** Jay has confirmed (**2026-07-29**) that `eggptdai10` reaches the Claude gateway and **every API used in the PoCs**. Recorded as **proven on Jay's verification**, not on a committed script run — no script output is claimed here. The egress loop stays in `setup_vm_jarvis.ps1` as a **deployment-day re-verification**, not as an open action.

#### Step B.2b — Tooling install + Eggplant component verification — **deferred to deployment day**
The winget installs, `uv`, the ✓/✗ component table and the reserved EPF licence are **not needed while development is local** (G3; and see B.7a/B.7b). The script is **written now** so deployment day is a single `(User)` run — but it is not run now.

**DoD:** `setup_vm_jarvis.ps1` **written and reviewed**; **VM egress verified (Jay, 2026-07-29)**; installs and licence reservation **deferred to deployment day**. *(PoC 1 and 1b are `n.a. (deferred)` and are deliberately **not** reintroduced as a completion condition — the previous DoD could not be met as written.)*

### Step B.3 — Credentials & config module — *Owner: Agent + (User)*
**Goal:** every secret loads from env; nothing hardcoded.
**Actions:**
1. **(User)** provision: Jira PAT (R/W on TESTAUTOMA), Bitbucket PAT, DAI API access, Anthropic API key → `.env` on the JARVIS VM (and on the local development machine while development is local).
2. Agent: implement `src/config.py` (pydantic-settings) — all PoC-era keys **plus**: `jira_base_url`, `dai_log_by_runid_url`, `jarvis_*` (validation repo url, PAT, JARVIS DAI url/v2 creds, branch, suites path, completion mode — **note there is no `jarvis_test_config_id` scalar**; the suite→config mapping lives in `tracks/enovia/test_config_registry.yaml` per D3), `anthropic_base_url`, `model` (Opus 4.7), optional `model_light`, `epf_runscript_path`, `epf_default_doc_dir`, `epf_license_host`, `working_copy_path`, `validation_mechanism` (= `jarvis-dai`), `engine_mode`, `approval_mode`, `budget_usd_per_run`, `db_path` (default `data/agent.db`), `sso_*`. Loads `.env` + merges `config/enovia.yaml` via `src/orchestrator/track_loader.py` (returns a typed `TrackConfig`).
**Verification:** `python -c "from src.config import settings; print(settings.model)"` works with `.env`; unit test for track_loader.
**DoD:** config module + track loader tested; secrets only in `.env`.

### Step B.4 — Local clone + static layer + vocabulary [UP-3, UP-12] — *Owner: Agent + (User)*
**Goal:** the deterministic retrieval layer that replaces the vector DB — now including the handler vocabulary and the Tier-0 lint.
**Actions:**
1. Agent: `scripts/clone_repo.ps1` (clone the **production** repo `enovia-plm-test-automation` to `C:\agent\repo` ↔ `settings.working_copy_path`, checkout `Testing_Mar10`, then `git remote add agentic-eggplant-automation <JARVIS_REPO_URL>` — **one working copy, two remotes pointing at two different Bitbucket repositories**: `origin` = the **production** repo `enovia-plm-test-automation` [pull `Testing_Mar10`; later `Jarvis-fix/*` push at plan3 PR time], `agentic-eggplant-automation` = the **validation** repo `agentic-eggplant-automation` [force-push the candidate to branch `Enovia` on every validation cycle]) + Task-Scheduler registrations for (a) an hourly `git pull --ff-only` on the working copy, (b) a **nightly rebuild job** that re-runs `build_handler_map.py` + `build_vocabulary.py` against the fresh clone, so the derived artifacts never go stale, and (c) a **scheduled `git pull` for `C:\Eggplant_Suites` on the JARVIS VM**, so the Design agent's local suites folder tracks the validation repo. **(User)** run on the JARVIS VM; confirm all three scheduled tasks.
2. Agent: `scripts/build_handler_map.py` — walk every `*.suite/Scripts/*.script`, parse `to handle <name>` / `to <name>` / `function <name>` definitions, map call-prefixes → repo-relative paths; seed/verify against known prefixes (CommonEnovia, common, configEnovia, LaunchApp, FileOperations, EnoviaSearch, exceptionHandling, CommonEnoviaContd, EnoviaChangeManagement, MQLTestData, WINSCP) → `tracks/enovia/handler_map.yaml`.
3. Agent: promote PoC-3 logic into real modules with unit tests on synthetic fixtures:
   - `src/static/sensetalk_parser.py` — `handler_defs(text)`, `handler_calls(text)` (ignore strings/comments).
   - `src/static/call_graph.py` — `build_call_chain(test_src, handler_map, depth=3)` + `flatten_paths`.
   - `src/static/ripgrep_search.py` — `find_callers(handler, repo_path)` via `rg -n "\b<h>\b"`.
   - `src/static/handler_map.py` — load YAML; `resolve(prefix) -> path|None`.
4. **[UP-12]** Agent: `scripts/build_vocabulary.py` + `src/static/vocabulary.py` — for every handler: `{name, file, line, signature, params[]}`; optional one-time `MODEL_LIGHT` pass adds a 1-line `purpose` (cached; **(User)** approves the spend) → `tracks/enovia/handler_vocabulary.json` with `lookup(name)` / `exists(name)`.
5. **[UP-3]** Agent: `src/static/lint.py` — `lint(script_text, vocabulary) -> list[LintIssue]`: balanced blocks (`if/end if`, `repeat/end repeat`, `try/catch/end try`, `to|on|function/end`), unknown-handler calls (vs vocabulary, with a config allowlist for built-ins), and basic paren/quote balance. Unit tests: clean script → 0 issues; seeded errors → each caught.
6. **Curate the `tracks/enovia/` context set — ✅ BUILT 2026-07-30; the (User) owns the decision, the eval owns the gate.**

   **Structure — two tiers, not one file.** This was originally specified as a single `context.md` at ≤~20K tokens. What exists is better:
   - **`context.md` — the CORE.** 249 lines, **~7.7K tokens**, **always in the cached prefix** [UP-6]. It carries what is needed on *every* diagnosis: hard stops, runtime boundaries, suite/handler resolution, triage by symptom, shared contracts, oracle order, the retry ledger.
   - **Five appendices** — `handlers`, `messages`, `rectangles`, `finding_things`, `ticket_learnings` — **~3.5–7.2K tokens each, ~23K total**, loaded **only on trigger** (plan1 §1.3.3, §1.4.2). The trigger conditions live in the core's *Appendix triggers* section and are **parsed, not hardcoded**.
   - Plus `context_seed.md` (the cross-ticket seed the core was generated from) and `ticket_findings.md` with its nine per-ticket sources.

   **Two rules that keep it that way:** the core has a **600-line hard ceiling**; and when it grows past that, **detail moves to an appendix — it is never compressed into ambiguity.** A shorter core that says something vague is worse than a longer one that says something precise, because the core is what every call pays for.

   **How it was built, recorded because the method is repeatable.** Not hand-written. **Generated by a reasoning agent against the live Enovia repo**, from the **nine solved-ticket records** plus the cross-ticket seed, then **reviewed by (User)**. This is why the document carries **evidence markers** (`[verified <date>]`, `[live-run: TICKET]`, `[UNVERIFIED — check: <cmd>]`) at all — a hand-written document would not have distinguished what was checked from what was recalled, and that distinction is what makes the set safe to cache into every call.

   **The review gate moved — here is where it went.** The original design put a second human reviewer at this step for a specific reason: `context.md` is prompt-cached into **every** call, so a wrong claim there degrades **every** diagnosis, silently and without error. That reviewer is now the author, so the gate cannot stay here. **The replacement already exists and is already named:** plan1 §1.7.1 states `scripts/run_eval.py` is *"the one command rerun after any prompt/`context.md` change."* **Make it binding: a `context.md` change is not complete until the eval has been re-run and the score has not regressed.** That converts an unfalsifiable human review into a **measured** one — which is stronger, not weaker, and it is the same standard every other change to the reasoning path is held to. The same line goes into the *Maintenance* section of `tracks/enovia/context.md`.

   **Unchanged:** it is **curated knowledge and never auto-rewritten**; what IS auto-derived from the Enovia code (`handler_map`, `vocabulary`) is rebuilt nightly (action 1); and **it lives in the AGENT'S OWN repo** — not the Enovia repo, not embedded in code — as a versioned data file loaded from disk at runtime and prompt-cached [UP-6]. **plan3 §3.6.5 adds weekly drift detection + agent-drafted update suggestions for human review.**

   **What the set must still carry** (unchanged from the original specification, now spread across core and appendices): handler signatures, search-rectangle definitions, config values, JIRA-number→suite ranges, and the **known fix patterns grouped by failure family — the [UP-5] exemplar source** that `prompts/family_exemplars/` draws on (plan1 §1.4.1).

   **Primary input — `tracks/enovia/ticket_findings.md`** (nine tickets, sources in `ticket_findings/`): root cause, the fix that worked, and *what the model got wrong first*. It is **evidence *for* curation, never a substitute for review** — and with the human gate now at the eval, that distinction is what the eval is measuring.
**Verification:** the static modules pass **their own unit tests on synthetic fixtures with known answers** (action 3 builds exactly these), running against the **generated** `handler_map.yaml` rather than a seeded one; lint unit tests green; vocabulary spot-checked against 5 known handlers. *(This replaces "reproduce PoC-3 results" — PoC 3 is **superseded by this step** and its results will never exist. Fixtures with known answers are the **stronger** bar: a PoC comparison could only prove the modules agreed with an earlier script, whereas a fixture asserts they are **right**. The on-VM rerun moves to **`GATE 0b-VM`**, where every machine-bound check now lives.)*
**DoD:** `handler_map.yaml` + `handler_vocabulary.json` complete; parser/graph/ripgrep/lint tested; `context.md` reviewed; hourly pull + nightly rebuild + the `C:\Eggplant_Suites` pull all running; both remotes configured (`origin` → `enovia-plm-test-automation`, `agentic-eggplant-automation` → `agentic-eggplant-automation`).

### Step B.4b — JARVIS suite onboarding + test-config registry — *Owner: (User), scripts and registry schema by Agent*
**Goal:** bring a suite onto the JARVIS DAI so the validation gate can target it.
> **What onboarding a suite buys you:** tickets whose **failing tests live in that suite** become validatable. **A suite is not a location for fixes** — a fix frequently lands in a shared handler (`CommonEnovia.script` and friends) that belongs to no suite at all. The validation target is always the **owner of the failing test** (`validation_suite_of`, plan2 §2.5.0). This is the **D2 sequence** (plan_master §2.3.2) — a one-time, per-suite authoring job. **Every DAI-side action below is performed by the (User), Jay**; the Agent supplies the registry schema, the dispatcher template and the validation scripts.

**Actions (the D2 sequence, in order):**
1. **Export** the suite's model from the **production** DAI.
2. **Import** it into the **JARVIS** DAI. *(Recall **C4**: model exports restore internal structure but **not** suite links or test configs — those are re-authored in the steps below.)*
3. **Verify the suite association** on the imported model. *(Recall **C2**: suite names must be globally unique across a DAI instance — see **O2** as suites accumulate.)*
4. **Create `<Suite>_AgentDispatcher.script`** in the suite, in the Design agent's local suites folder `C:\Eggplant_Suites`. Generated from `src/analysis/templates/agent_dispatcher.st.j2`; obeys **S1** (`TestCases/<name>`, no `.script`, no `Scripts/` prefix) and **S2** (plain `run targetScript`). **No `try/catch`** — a swallowed target failure would be a false PASS.
5. **Author the dispatcher model action** `AgentDispatcher` and attach the snippet.
6. **Create the test case**: `cleanupSUT` + `AgentDispatcher`.
7. **Create the model-based test config**: SUT **by name**, **reruns OFF**, **generous run timeout**. Reruns must be off or a flaky retry would mask a real target failure.
8. **Add the suite's row to `tracks/enovia/test_config_registry.yaml`** (**D3** — the file exists; adding a suite is a **data** change, never a code change). This mapping — *which test config to trigger for a script change in which suite* — **is provided by the (User), Jay**. Every field is required; in particular a suite with **no `smoke_target` is a hard error at onboarding time**, because every push regenerates *every* registered suite's dispatcher (F8) and the non-target ones still need a valid target line.
9. **One smoke run** through the gate to confirm the registry entry resolves and the suite executes.
10. **Re-check O2** (suite-name collisions, **constraint C2** — names must be globally unique per DAI instance) as suites accumulate on the JARVIS instance.

**The onboarded PartMaster row (the worked example, already in the registry):**

```yaml
  PartMaster:
    suite_dir: PartMaster.suite                              # exact directory name in the validation repo
    model: Part_Master_Pack_01                               # JARVIS DAI model the config is built on
    test_config_id: 0310ac5d-c0c5-49dc-8b04-44c42a33d84e     # triggered by ID via the DAI API
    dispatcher_script: PartMaster_AgentDispatcher.script     # generated every push — never in the production repo
    smoke_target: TestCases/TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget
    onboarded: 2026-07-28
    status: proven                                           # A.2 + A.2b, full PASSED run with SHA traceable
```

**Verification:** the registry entry resolves for the target suite, and a smoke run **PASSES** with the executed commit SHA traceable in the run log.
**DoD:** at least **`PartMaster` onboarded — ✅ done** (`Part_Master_Pack_01`, test config `0310ac5d-c0c5-49dc-8b04-44c42a33d84e`, proven in A.2/A.2b). Remaining **16** suites tracked as open item **O4**; each needs this full sequence.

### Step B.5 — Evidence retrieval validation — *Owner: (User), scripts by Agent*
**Goal:** prove the evidence path with **no** SharePoint/Azure AD.
**Actions:** the Agent extends `scripts/poc_dai.py` with `--runid <id> --fetch-evidence <dest>` (log + error screenshot via the User's APIs/logic from A.1); **(User)** fetch one evidence set by runid and one screenshot from the PoC-1 results folder; attach both to a test Jira ticket via `scripts/poc_jira.py`. Decide the bundle: error screenshot(s) + trimmed log excerpt + DAI result link.
**DoD:** both retrieval paths + Jira attachment proven; SharePoint/Azure AD formally dropped (noted in `poc_results.md`).

### Step B.6 — Persistent state store + event bus [UP-8] — *Owner: Agent*
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

### Step B.7 — Integration smoke test + GATE 0b-LOCAL / GATE 0b-VM — *Owner: Agent + (User)*
**Goal:** one script exercises every integration — run **locally first (B.7a)**, then **on `eggptdai10` at deployment (B.7b)**. `eggptdai10` is the JARVIS VM that hosts the DAI, the agents, `C:\Eggplant_Suites`, the working copy and the orchestrator itself.

> **Why this step and Gate 0b split (ruled by Jay, 2026-07-29 — open item O12).** As previously written,
> Gate 0b required a provisioned VM and an on-VM smoke, so it could not pass until deployment — while
> gating **plan1**, which is built locally. That is a deadlock, not a standard. The gate now splits by
> **what machine can prove each item**: **`GATE 0b-LOCAL` gates plan1**; **`GATE 0b-VM` gates deployment
> and plan3's rollout.** **No checklist item is deleted and no item's substance is reworded** — each is
> simply filed under the machine that can prove it. **B.7 is not renumbered.**

> **Where development actually happens.** Day-to-day development and unit testing run on the **(User)'s local machine**; VM deployment comes later. The inherently VM-bound steps — **B.2** provisioning, **B.4**'s clone + scheduled tasks, **B.4b**'s DAI authoring, and **B.7b** — stay **(User)-on-VM**.
**Actions:** the Agent writes `scripts/test_integrations.py` printing a ✓/✗ table: Jira read + **runid extraction on a real ticket** · Bitbucket read + sandbox branch · **production**-DAI log+screenshot by runid · **JARVIS validation dry-run** (push a no-op commit to `agentic-eggplant-automation@Enovia`, **assert `git ls-remote` equals the pushed SHA**, trigger the registry's test config for the suite, poll to completion via `poll_backoff`, fetch the results chain, **assert the run log's `Using Git commit SHA` equals the pushed SHA**) · runscript smoke (1-line script on the runner — *deferred; skip unless the local-runscript variant is revived*) · **Claude ping via `settings.model` and the configured base URL — this is the VM-egress verification folded in from A.9; if it fails, (User) files the firewall ticket now.** *Use `settings.model` — **never** a literal model ID. `claude-opus-4-6` is **not** whitelisted on the gateway and returns a misleading `401 invalid x-api-key` that is easily mistaken for an egress failure (root-caused, PROGRESS 2026-06-12); filing a firewall ticket for it would chase a problem that does not exist.* · static call-graph on the 8055 script · ripgrep blast radius · lint on a sample script · SQLite store round-trip. **(User)** run it on the VM; paste the table.
#### Step B.7a — run the smoke **locally** — satisfies `GATE 0b-LOCAL`
The Agent writes `scripts/test_integrations.py` (above); **(User)** runs it **on the development machine**; all-green satisfies `GATE 0b-LOCAL`. **B.7a is an *additional, earlier* checkpoint — never a replacement for B.7b.**

#### Step B.7b — run **the same script, unchanged, on `eggptdai10`** — satisfies `GATE 0b-VM`
**(User)** runs it on the JARVIS VM at deployment. **B.7b is the first time the full integration set runs on the target host, and that is precisely its value. Do not weaken it into a local run.** Passing B.7a does **not** discharge B.7b; no later pass may read this split as permission to skip the VM run.

**GATE 0b-LOCAL checklist** (print; (User) confirms) — *provable from the development machine; **gates plan1***:
repo+deps ☐ · Jira (incl. runid)/Bitbucket/production-DAI-evidence/Claude verified ☐ · **JARVIS validation path triggers + completes** ☐ · **`tracks/enovia/test_config_registry.yaml` populated and resolving for the target suite** ☐ · **pushed-SHA assert working at both edges (`git ls-remote` pre-trigger, `Using Git commit SHA` post-completion)** ☐ · handler_map + vocabulary + static modules + lint correct ☐ · **`tracks/enovia/` context set curated & reviewed — core + five appendices + cross-references resolving** ☐ · evidence retrieval proven (no SharePoint) ☐ · **`VALIDATION_MECHANISM=jarvis-dai` recorded** ☐ · state store + event bus tested ☐ · **the local working copy carrying both remotes: `origin` → `enovia-plm-test-automation`, `agentic-eggplant-automation` → `agentic-eggplant-automation`** ☐.

**GATE 0b-VM checklist** (print; (User) confirms) — *machine-bound; **gates deployment and plan3's rollout***:
VM tooling installed (B.2b) ☐ · egress re-verified on deployment day ☐ · **dedicated EPF licence reserved, SUT reachable** ☐ · **every integration verified *from the VM* (B.7b)** ☐ · **the VM working copy at `C:\agent\repo` carrying both remotes** ☐ · hourly pull + nightly rebuild + `C:\Eggplant_Suites` pull scheduled ☐ · **B.4's static modules re-run against the VM's generated `handler_map.yaml`** ☐ · runscript runs an Enovia script *(deferred — n.a. this version)* ☐.

**DoD:** smoke test all-green on the machine in question. **Plan 1 cannot begin until `GATE 0b-LOCAL` passes. `GATE 0b-VM` gates deployment and plan3's rollout, not plan1.**

➡ Proceed to **plan1_diagnosis_and_chat.md**.
