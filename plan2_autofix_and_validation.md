# PLAN 2 — AUTO-FIX + VALIDATION (WEEKS 5–6) — v2 FOR THE AGENT

> **Prereq:** GATE 1 passed. **Objective:** JARVIS goes from read-only diagnosis to **propose fix → lint → validate → retry**, with an in-chat human approval before anything is published. The **production** Bitbucket repo is still untouched in this plan (push/PR live in plan3) — fixes live on local `wc/<TICKET>` branches and, during validation, on the **validation repo** `agentic-eggplant-automation` branch **`Enovia`**.
>
> **Safety invariants (enforced in code):** edits land only on a local working copy; never `Testing_Mar10`; never merge; **the only remote write in this plan is the force-push to `agentic-eggplant-automation@Enovia`** — the **production** repo `enovia-plm-test-automation` stays completely untouched until plan3; every SUT run serialized behind the track lock; a fix is discarded unless validation passes; **no verdict is trusted unless the pushed SHA is asserted both before trigger and after completion** (UP-24); per-run budget cap ($10) active. **Validation runs on the JARVIS gate (§2.5); the local `runscript` inner loop is deferred.**
>
> Build order: 2.1 fix generator → 2.2 applier → 2.3 lint gate → 2.4 runscript loop *(deferred)* → **2.5.0 dispatcher generator → 2.5 the JARVIS validation gate** → 2.6 retry controller → 2.7 approval UX → 2.8 shadow mode.

---

## Phase 2.1 — Fix generation engine [UP-2, UP-4 format] — *Owner: Agent*

### Step 2.1.1 — Fix schema (`src/agentic/schemas.py` additions)
`ProposedFix {fixes: [FixEdit], confidence: HIGH|MEDIUM|LOW, blast_radius_assessment, test_recommendation, rationale}`; `FixEdit {file_path, anchor_before?: str, original_code: str, fixed_code: str, explanation}`.
**Patch contract (anchor-based [UP-4]):** `original_code` is an EXACT, contiguous excerpt of the current file, long enough to be **unique in the file** (include surrounding lines if needed); `fixed_code` replaces it verbatim; `anchor_before` (optional nearby unique line) helps disambiguation. No line numbers in the contract — they drift.

### Step 2.1.2 — Prompts (`fix_system.md`, `fix_user.md`)
System: expert SenseTalk developer; produce the EXACT minimal fix; constraints — minimal diff, syntactically valid SenseTalk, match existing indentation/naming/comment style, **blast-radius aware** (caller list provided; do not break other callers of a shared handler); `original_code` must be copied char-for-char from the provided source and be unique; finish by calling `submit_fix`; if a confident minimal patch isn't possible → confidence LOW + why. User template: diagnosis JSON, the affected file(s) source (full or windowed via context_packer), caller list, family exemplar fixes [UP-5], retrieved similar trajectories [UP-11], prior-attempt failure feedback slot (filled by the retry controller).

### Step 2.1.3 — Generator (`src/analysis/fix_generator.py`)
`FixGenerator.generate(diagnosis, run, model=None, temperature=0.2, feedback=None) -> ProposedFix(+usage)`:
1. Build cached system blocks [UP-6]; call via `claude_client` with `tools=[submit_fix]`, `tool_choice` forced [UP-2]; pydantic-validate (one auto-repair retry).
2. **Self-check (pre-apply):** for each edit — target file is among the run's scripts/working copy (else `_invalid="file not in scope"`); `original_code` occurs **exactly once** in the file: 0 → retry once with whitespace-normalized search to recover the true excerpt and rewrite `original_code` to the file's literal text; still 0 → `_invalid="not found (hallucinated)"`; ≥2 → one re-ask to the model for a larger unique anchor; still ambiguous → `_invalid="ambiguous anchor"`.
3. **Tier-0 lint preview [UP-3]:** apply each edit in-memory and `lint()` the result; any new lint issue → attach `_lint=[issues]` (the retry controller treats it as an instant FAIL — no SUT time burned).
**Verification:** on the 8055 diagnosis → the one-line removal of `and not ImageFound(text:"Name",…)`; self-check passes; a deliberately wrong `original_code` flagged; a deliberately unbalanced `fixed_code` flagged by lint preview.
**DoD:** schema-forced output; hallucination/ambiguity/lint checks all proven by unit tests with fixtures.

---

## Phase 2.2 — Apply to the LOCAL working copy — *Owner: Agent*

### Step 2.2.1 — `src/orchestrator/fix_applier_local.py`
Git helpers over `settings.working_copy_path`:
- `reset_clean(branch)`: `reset --hard` · `clean -fd` · `checkout Testing_Mar10` · `pull --ff-only`.
- `apply(ticket_key, proposed_fix) -> {branch, applied[], skipped[], diff}`: delete-if-exists then `checkout -b wc/<TICKET>`; for each valid edit do the **single** exact replacement (fallback: normalized match → map back to the literal span); no-op replacements → skipped; `git diff` captured and published as an `artifact {kind: diff}` event. Nothing is pushed here.
- `cleanup(ticket_key)`: drop the wc branch, return to base.
**Verification:** applying the 8055 patch changes exactly one line of the local `CommonEnovia.script`; `git diff` shows the one-clause removal; no-op and ambiguous edits are skipped with reasons; reset between attempts leaves a pristine tree.
**DoD:** atomic local apply; robust matching; clean reset proven; diff event emitted.

---

## Phase 2.3 — Tier-0 lint gate in the loop [UP-3] — *Owner: Agent*
Wire `src/static/lint.py` as the first validation tier: after apply, lint every touched file. Any issue → publish `step.failed (linting)` with the issues, record as attempt feedback, **skip the SUT entirely**, continue to the next attempt. Unit test: a seeded unbalanced-`end if` patch consumes an attempt in milliseconds and never calls the runners.
**DoD:** lint gate wired; SUT never invoked on a lint-failing patch.

---

## Phase 2.4 — Local `runscript` inner loop *(DEFERRED — optional latency optimisation)* — *Owner: Agent ((User): live checks)*

> **Deferred.** **Every attempt is validated by the JARVIS gate (§2.5) in this version** — that is the single mandated mechanism (plan_master §2.1, §2.3), so the local `runscript` inner loop is not on the critical path and is required by no gate. This phase is retained in full as a documented option; see `docs/later-enhancements.md`.

### Step 2.4.1 — `src/integrations/epf_runner.py`
`run(script_repo_path, run_id, timeout=900) -> dict`:
```
cmd = [settings.epf_runscript_path, <abs script under working_copy>,
       "-DefaultDocumentDirectory", settings.epf_default_doc_dir,   # parent of *.suite → cross-suite resolution
       "-GlobalResultsFolder", data/agent_runs/{run_id},
       "-CommandLineOutput","YES","-ReportFailures","YES",
       "-MaxWaitForLicense","600"] (+ ["-LicenserHost", host] if set)
```
Exit **127 → `{"status":"NO_LICENSE"}`**; else PASS/FAIL by exit code; `_parse_results(folder)` reads `LogFile.txt` + collects `*.png`/`*.tiff` (≤8) → `{log, screenshots, results_folder}`. Run via `asyncio.to_thread` (it blocks). If the orchestrator and runner are different VMs, **(User)** decides: co-locate a small worker on `eggptdai10` (a thin FastAPI `POST /run` wrapping this class — the Agent builds it) or run the orchestrator on the runner VM; record choice in `config/enovia.yaml`.
**Verification ((User), VM):** the known-good original 8055 test → PASS (exit 0); a deliberately broken copy → FAIL with parseable log + screenshots.
**DoD:** PASS/FAIL by exit code; artifacts parsed; license-wait handled. *(Deferred in this version: §2.5 serves every attempt.)*

---

## Phase 2.5 — The JARVIS validation gate (authoritative SUT validation) — *Owner: Agent + (User)*

> Mechanism **proven end-to-end** in PoC 2b (plan0 A.2) and A.2b: the JARVIS test config's git connection is **pre-wired to the validation repo `agentic-eggplant-automation` branch `Enovia`** and **syncs at run start** (not a cached clone); its SUT connection (`Jay_130`) is prebuilt. So validation = *push the candidate there, assert the SHA, trigger, read the results, assert the executed SHA*. No production-DAI repointing, no production-repo writes, nothing to reset afterward.
>
> **Because DAI API v2 exposes no test-config or step create/edit endpoints (C1), the test config cannot be rewritten per ticket.** The dispatcher pattern (D1) is what makes per-ticket targeting possible: the config stays permanently static and only the dispatcher script's target line changes, via git. Build the generator first.

### Step 2.5.0 — Dispatcher generator — *Owner: Agent*
`src/orchestrator/dispatcher.py` + `src/analysis/templates/agent_dispatcher.st.j2` (template contract: plan_master §2.3.3).

**The registry is the input.** `tracks/enovia/test_config_registry.yaml` (**D3**) is **read at runtime**, never compiled in. Adding a suite is a **data** change, never a code change.

Functions:
- `load_registry() -> {suite_key: entry}` — read the D3 registry at runtime.
- **`validation_suite_of(run) -> suite_key`** — resolve **which suite's test config to trigger**, in this order:
  1. the suite that **owns the failing test** named in the DAI log;
  2. failing that, the **JIRA number→suite range** from `config/enovia.yaml` (plan1 §1.3.2);
  3. if neither resolves — **raise. Never infer from the changed file's path, and never default.**

  **Resolve from the failing test, NOT the changed file.** TESTAUTOMA-8055 is the proof: its fix lands in `CommonEnovia.script` ~line 409, a **shared handler**. Shared handlers belong to no suite and have no test config, so resolving from the changed file would find nothing in the registry, the pre-flight would refuse, and **the project's own golden ticket would route to diagnose-only and never validate.** Invisible with one suite onboarded; structural with two, because most real fixes touch shared code.

  **Shared handler directories are explicitly not suites.** `CommonEnovia`, `common`, `configEnovia`, `LaunchApp`, `FileOperations`, `EnoviaSearch`, `exceptionHandling`, `CommonEnoviaContd`, `EnoviaChangeManagement`, `MQLTestData`, `WINSCP` — and anything else in `handler_map.yaml` — must **never** resolve to a registry key. A shared-handler fix is validated by **running the failing test's suite**; wider impact is already covered by `blast_radius` and `callers_pass`.

  This reuses plan1's **existing** primary localization signal (§1.1.2 `localize`, §1.3.2) rather than inventing one. **Naming — do not merge these:** plan1 §1.3.2 already defines **`_suite_of`** (ticket number → repo path), a *different* function with different input and a different failure mode. This one is **`validation_suite_of`**.
  **An unresolved key is an error, never a fallback.** The gate's pre-flight check (§2.5.2) turns that error into a refusal to validate.
- `target_ref(script_path) -> "TestCases/<name>"` — implements **S1**: strip the `Scripts/` prefix, strip the `.script` extension. EPF does not auto-search subfolders, so any other form silently fails to resolve.
- `render(suite, target) -> str` — render the template. Emits plain `run targetScript` per **S2** (dot-notation `targetScript.run()` does not work).
- `render_all(registry, target_suite, target) -> {suite: text}` — render a dispatcher for **every** registered suite (see the regeneration rule below): the target suite gets the ticket's target, every other suite gets its own `smoke_target`.
- `write_and_commit(working_copy, rendered) -> sha` — write **all** generated dispatchers into their suites and commit them onto `wc/<TICKET>`.

**Regeneration rule (settled — F8/O6, a rule, not a recommendation).** Every registered suite has its **own** `<Suite>_AgentDispatcher.script` **and its own test config**, which executes that suite's dispatcher. On **every** validation push, JARVIS regenerates the dispatcher for **every suite in the registry**, so the `Enovia` branch is **always complete**. This is what makes the force-push safe: the push replaces branch contents wholesale, so any dispatcher not regenerated would simply vanish (**O5**). Consequence: **a registered suite with no `smoke_target` is a hard error at onboarding time**, never a silent failure at validation time — the non-target suites still need a valid target line.

**Unit tests (all mandatory):** the template renders exactly the §2.3.3 contract; a `Scripts/TestCases/Foo.script` path yields `TestCases/Foo`; **`.script` and `Scripts/` are never emitted**; **no `try/catch` appears in the output** — its absence is load-bearing, since a swallowed target failure would produce a false PASS, the worst possible failure mode for this system; **`render_all` emits one dispatcher per registered suite**; a registry entry missing `smoke_target` **raises at load time**.
**Plus, for `validation_suite_of` (added, not replacing any of the above):** a ticket whose **failing test is in `PartMaster`** but whose **fix edits `CommonEnovia.script`** resolves to **`PartMaster`** — the shared-handler case that motivated the rule; a **shared-handler path never yields a registry key**; a run where **neither the failing test nor the JIRA range resolves raises**, rather than defaulting to any suite.

**Assertion rule:** anything that keys off the dispatcher's log output must match the **`AgentDispatcher:` prefix only**, never the full line — the em dash in `— target=` is non-ASCII, and log encoding must not be able to break a verdict.

**D4 (binding):** the generated `<Suite>_AgentDispatcher.script` is a validation artifact. It **never exists in the production repo** and must **never** appear in a `Jarvis-fix/<TICKET>` branch or PR — the publisher asserts this before pushing (plan3 §3.2).

### Step 2.5.1 — Confirm JARVIS wiring — *(User)*
Confirm in `config/enovia.yaml → jarvis`: repo URL + PAT (**force-push rights to `Enovia`**), `branch: Enovia`, **JARVIS DAI** base URL + **v2 client credentials** (`POST /api/v2/auth` — *not* the production DAI's Keycloak OAuth2 scheme), that the **test-config registry resolves for the target suite** (`tracks/enovia/test_config_registry.yaml`, D3), the trigger endpoint, and `completion_mode: webhook | eggplant_runner | poll_backoff` (= `JARVIS_COMPLETION_MODE`, **`poll_backoff` day one**) plus its mode-specific settings (webhook secret + route, or runner binary path, or poll backoff schedule + timeout).

**Drift note:** the gate **force-pushes the full candidate state** on every cycle, so any drift between the validation repo and production is **irrelevant to validation correctness** — the branch contents are wholly replaced each time. (This is also what creates O5/O6; see 2.5.0.)

### Step 2.5.2 — `src/integrations/jarvis_dai.py` + `src/orchestrator/validation_gate.py`
**Invariant (binding): the LLM is never in the wait path.** Claude is called only to generate the fix (before triggering) and to interpret the result (after it resolves). Whichever `completion_mode` is active, waiting is a plain orchestrator coroutine — an `asyncio.Event`, an awaited subprocess, or an `asyncio.sleep` poll loop — never a tool the agentic loop (UP-1) calls repeatedly. A run can legitimately take 20 min–2 hr; nothing in that path may resend a conversation to the model.

`JarvisDAI`:
- `auth()` — `POST /api/v2/auth` with `client_id`/`client_secret` → bearer token, **~10-minute expiry**, cached in-process and **refreshed on expiry**. This instance is **not** the production DAI; do not share a client, base URL or token cache with `dai_client.py` (plan1 §1.2.3).
- `trigger(test_config_id)` — the existing, already-tested trigger-by-ID API.
- The **four-call results chain** (plan_master §2.3.4): `GET /api/v2/test_config_results?test_config_id=<ID>` → newest result id; `GET /api/v2/test_results?test_config_result_id=<id>` → step result + status; `GET /api/v2/test_results/{test_result_id}/logs` → entries (`message`, `severity`, `message_type`, `image_id`); `GET /api/v2/screenshots/{screenshot_id}` → PNG (PoC-2 walk-back logic reused).

All three completion modes are kept; **`poll_backoff` is the day-one mode and webhook is the upgrade path (O1)**:
- **`webhook`:** `POST /api/webhooks/dai` (new route, alongside the plan3 Bitbucket webhook) verifies a shared secret, matches the payload to a pending run, and resolves a per-run `asyncio.Event`; `wait_complete(timeout=<generous, e.g. 3h safety net>)` just awaits that event — the timeout only guards a lost delivery, it is not the normal completion path.
- **`eggplant_runner`:** `await asyncio.create_subprocess_exec(...)` then `await proc.wait()`; exit code 0 = PASS, else FAIL; parse `--result-path` JUnit XML for the run's identifying info.
- **`poll_backoff`:** `wait_complete(timeout=<config, must cover observed 20min–2hr range>, backoff=[15,30,60,120])` — an `asyncio.sleep`-based loop, HTTP-only, no LLM calls.

`ValidationGate.validate(ticket_key, wc_branch, affected_files) -> {status, result_id, log, screenshots, result_url, executed_sha}`: **under the track lock**, in this order →
0. **Pre-flight — suite onboarded?** **`validation_suite_of(run)`** — the suite that **owns the failing test**, never the changed file's path (§2.5.0). If the resolved suite is **not present in the D3 registry**, return **`{status: NOT_ONBOARDED}` immediately — before any push, before any trigger.** The gate **never** falls back to another suite's `test_config_id`, and `NOT_ONBOARDED` is **never** reported as PASS or FAIL. The run is routed to the existing **diagnose-only** outcome with reason `suite_not_onboarded`, using the existing `ai-diagnosis-only` label. This is a routing decision taken before a run starts, not a run-time failure — so it adds no plan3 §3.4.2 degradation rule. Only one suite is onboarded today (**O4**), so this path is live from day one (plan_master §6.13);
1. take the suite resolved in step 0 by `validation_suite_of(run)` — **the owner of the failing test**, not of `affected_files` — and look up its `test_config_id` in the D3 registry;
2. render and commit a dispatcher for **every registered suite** (2.5.0 regeneration rule) — target suite gets the ticket's target, the rest get their `smoke_target`;
3. `git push agentic-eggplant-automation wc/<TICKET>:refs/heads/Enovia --force` (force is safe — the branch is disposable and the lock serialises writers); record the pushed SHA;
4. **UP-24 pre-check (mandatory):** assert `git ls-remote agentic-eggplant-automation refs/heads/Enovia` **==** the pushed SHA;
5. `trigger(test_config_id)`; publish `agent.message` ("JARVIS validation run started…") + periodic `step.progress` heartbeats (templated strings, **not** LLM-generated) while waiting — with `webhook` there is no polling to hang a heartbeat off of, so heartbeats there are just an elapsed-time timer;
6. on completion, walk the four-call results chain for status + logs + screenshots + `result_url`;
7. **UP-24 post-check (mandatory):** assert the run log's `Using Git commit SHA: '<sha>'` **==** the pushed SHA;
8. map to `PASSED | FAILED | ERROR | CANCELLED`; return verdict + evidence; release the lock. Timeout → `{status: TIMEOUT}` (degradation path, plan3 §3.4.2).

**Both asserts are mandatory.** A pre-trigger mismatch or a post-completion SHA mismatch returns **`{status: STALE_SYNC}`** and **never** a PASS/FAIL verdict — no verdict is trusted from a run whose executed commit cannot be tied to the pushed candidate. This is plan4 §4.7.2 landing early; see that section for the enforcement and test design rather than duplicating it here.

**Verification ((User)):** a known-good candidate → **PASSED** with evidence retrieved; a deliberately broken candidate → **FAILED** with the failure log captured; a **seeded SHA mismatch → `STALE_SYNC`** (and no verdict); **a candidate touching a suite absent from the registry → `NOT_ONBOARDED`, with nothing pushed and nothing triggered**; confirm no LLM call occurs between trigger and resolution — **the cost log must show $0 spent between trigger and resolution**.
**DoD:** the gate returns a verdict for a candidate branch purely via the JARVIS infrastructure; lock respected; both UP-24 asserts active on every cycle; evidence retrieval works on both outcomes; the wait mechanism matches `JARVIS_COMPLETION_MODE` and burns no tokens.

---

## Phase 2.6 — Retry controller [UP-7, UP-13, UP-15] — *Owner: Agent*

### Step 2.6.1 — `src/orchestrator/validation_loop.py`
`FixValidationLoop.execute(run, diagnosis, max_attempts=3) -> {status, attempt, fix?, evidence?, last_logs?}`:
```
for attempt in 1..max_attempts:
  model    = settings.model                                           # Opus 4.6, always
  thinking = settings.thinking_on_escalation and attempt>=2           # UP-15: same model + extended thinking
  if last_logs: diagnosis = DiagnosisEngine.diagnose(run, override_logs=last_logs,
                                                     thinking=thinking)   # FRESH re-diagnosis
  candidates = [generate(diagnosis, run, feedback=last_failure, thinking=thinking)]
  if attempt>=2 and cfg.n_best_on_retry>1:                            # UP-7
      candidates += [generate(..., temperature=0.7) for _ in range(cfg.n_best_on_retry-1)]
      candidates = dedupe_by_normalized_diff(candidates)
      candidates.sort(key=static_rank)        # lint-clean first, fewest files, smallest diff
  for fix in candidates:
      if fix.confidence=="LOW" or no valid edits: continue
      applied = applier.apply(ticket, fix)
      if lint fails: last_failure=lint issues; continue               # Tier 0, no SUT
      async with track_lock:                                          # SUT serialization
          res = validation_gate.validate(ticket, wc_branch, affected_files)   # the JARVIS gate, §2.5
          if res.NOT_ONBOARDED:                                       # pre-flight, nothing pushed
              # does NOT consume an attempt; NOT retried — end the run as diagnose-only
              return {"status":"diagnosis_only","reason":"suite_not_onboarded",
                      "artifacts":preserved}
          if res.STALE_SYNC:                                          # UP-24: never a verdict
              # does NOT consume an attempt; retry once, then abort preserving artifacts
              if not stale_retry_used: stale_retry_used=True; retry same candidate
              else: return {"status":"stale_sync","attempt":attempt,"artifacts":preserved}
          if res.PASS:
              if not callers_pass(fix, run): last_failure="blast-radius regression: <suite>"; continue
              return {"status":"pass", "attempt":attempt, "fix":fix, "evidence":res}
          last_failure = res.log_tail or res.raw
  if all candidates LOW/invalid: return {"status":"low_confidence","attempt":attempt}
return {"status":"exhausted","attempts":max_attempts,"last_logs":last_failure}
```
- `callers_pass(fix, run)`: from blast radius pick the configured smoke set of caller tests (per `enovia.yaml → blast_radius_smoke`), run via the **same JARVIS gate**; all must pass.
- **`NOT_ONBOARDED` handling:** the changed file belongs to a suite that has never been onboarded (plan0 B.4b), so there is no `test_config_id` to trigger and **nothing was pushed**. This says nothing about the candidate's quality, so it **does not consume an attempt** and is **not retried** — retrying cannot change the registry. The run **ends as diagnose-only** with reason `suite_not_onboarded`, artifacts preserved, using the existing `ai-diagnosis-only` label. Never a PASS, never a FAIL.
- **`STALE_SYNC` handling:** a SHA mismatch at either UP-24 edge is an **integrity failure, not a fix failure** — it says nothing about the candidate's quality. It therefore **does not consume an attempt**; retry once, and if it recurs, **abort the run preserving all artifacts** (branch, diagnosis, evidence, transcript) and surface it via the plan3 §3.4.2 degradation path. Never convert it into a PASS or a FAIL.
- `BudgetGuard` charged on every model call and (optionally, fixed estimate) per SUT run; `BudgetExceeded` → graceful `{"status":"budget_exceeded"}` preserving artifacts.
- Every decision point publishes `agent.message` + step events so the chat narrates the loop ("Attempt 2: re-diagnosing with extended thinking…").
**Design notes:** fresh-diagnosis-on-failure mirrors Self-Debugging/Reflexion — execution feedback drives the next attempt. **There is one oracle, not two:** the JARVIS validation gate (§2.5) is the single production-fidelity oracle and serves every attempt directly. (The deferred local `runscript` loop of §2.4 would, if ever revived, be a fast pre-filter in front of it — never a substitute for it.) The callers run is the regression guard.
**Verification (mock-level by Agent; live by (User)):** (a) golden 8055 → PASS attempt 1, JARVIS gate green; (b) a seeded 2-step bug → fails attempt 1, fresh re-diagnosis with extended thinking fixes on attempt 2; (c) a fix breaking a caller → caught by `callers_pass`; (d) a lint-failing patch consumes an attempt without touching the SUT; (e) budget cap aborts cleanly.
**DoD:** loop passes the golden ticket; adds thinking on retries; N-best on retry; never declares success without blast-radius + the JARVIS gate; `STALE_SYNC` never consumes an attempt and never yields a verdict; lock respected; bounded at 3.

---

## Phase 2.7 — In-chat approval gate [UP-9] — *Owner: Agent*

### Step 2.7.1 — Backend
On `status=pass`, pipeline enters `awaiting_approval`: persist an `approvals` row; publish `approval.requested` with payload `{diff, evidence: {screenshots, log_excerpt, dai_result_url}, fix_summary, expires_at}`. `POST /api/runs/{id}/approval {decision, comment?}` resolves it (asyncio.Event wakes the pipeline; publish `approval.resolved`). `approval_mode: auto` (config) skips the pause but still records an auto-approval row. Timeout (default 24h) → graceful park: label intent recorded, run marked `awaiting_approval` and resumable.
### Step 2.7.2 — Frontend
`ApprovalCard`: rendered diff (green/red), evidence thumbnails, DAI link, **Approve & Create PR** / **Reject** buttons (+ optional comment). Reject → pipeline records the reason as trajectory feedback and ends the run as `rejected`. In plan2, approval's effect stops at "approved, awaiting publisher" — the actual push/PR arrives in plan3 (the card says so).
**Verification:** end-to-end with a stub publisher: approve → run proceeds; reject → run closes with reason; reload mid-approval → card restored from DB.
**DoD:** HITL pause/resume proven across restarts; auto mode works.

---

## Phase 2.8 — Shadow mode (≥15 fresh tickets) + GATE 2 — *Owner: (User) drives, Agent analyzes*

**Actions:** **(User)** select ≥15 fresh Enovia tickets; run the full fix loop in **shadow** (`shadow: true` config → validates fully — including force-pushes to `agentic-eggplant-automation@Enovia`, which are the validation mechanism — produces the `wc/` branch + would-be PR description, but posts nothing to Jira and **pushes nothing to the production repo**). For each, record: first-attempt pass, final pass (≤3) + which attempt, lint-gate saves, and **functional equivalence vs the developer's actual fix** ((User) judges; the Agent prepares side-by-side diffs). the Agent computes all rates with Wilson CIs and writes `data/evals/shadow_report.md`.

**GATE 2 (print; (User) confirms):**
| Metric | Target | Measured |
|---|---|---|
| First-attempt fix pass | **≥60%** | ☐ (+CI) |
| Final pass (≤3 attempts) | **≥80%** | ☐ (+CI, + attempt histogram) |
| Functional equivalence to dev fix | **≥75%** | ☐ |
| Regressions (caller-suite breakage) | **0** | ☐ hard zero |
| Avg fix+validation time | **< 30 min per attempt (JARVIS gate)** · ⚠ **CONFIRM (Jay):** real per-cycle wall-clock timing is not yet measured (**O3**) — obtainable only once the gate runs for real | ☐ |
| Cost per ticket | reported honestly ($2–6 expected, Opus 4.6 + caching) | ☐ |

**DoD:** Gate 2 met with CIs; any regression → pause, root-cause, fix. **Plan 3 cannot begin until Gate 2 passes.**

➡ Proceed to **plan3_lifecycle_rollout.md**.
