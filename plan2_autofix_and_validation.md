# PLAN 2 — AUTO-FIX + VALIDATION (WEEKS 5–6) — v2 FOR CLAUDE CODE

> **Prereq:** GATE 1 passed. **Objective:** the agent goes from read-only diagnosis to **propose fix → lint → validate → retry**, with an in-chat human approval before anything is published. The **production** Bitbucket repo is still untouched in this plan (push/PR live in plan3) — fixes live on local `wc/<TICKET>` branches and, during validation, on the Practice repo's `/practice` branch.
>
> **Safety invariants (enforced in code):** edits land only on a local working copy; never `Testing_Mar10`; never merge; **the only remote write in this plan is to the Practice repo's `/practice` branch** (production Bitbucket stays untouched until plan3); every SUT run serialized behind the track lock; a fix is discarded unless validation passes; per-run budget cap ($10) active. This plan branches on the **`INNER_LOOP`** flag from PoC 1b (`local-runscript` or `practice-dai`).
>
> Build order: 2.1 fix generator → 2.2 applier → 2.3 lint gate → 2.4 runscript loop → 2.5 Practice gate → 2.6 retry controller → 2.7 approval UX → 2.8 shadow mode.

---

## Phase 2.1 — Fix generation engine [UP-2, UP-4 format] — *Owner: Claude Code*

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

## Phase 2.2 — Apply to the LOCAL working copy — *Owner: Claude Code*

### Step 2.2.1 — `src/orchestrator/fix_applier_local.py`
Git helpers over `settings.working_copy_path`:
- `reset_clean(branch)`: `reset --hard` · `clean -fd` · `checkout Testing_Mar10` · `pull --ff-only`.
- `apply(ticket_key, proposed_fix) -> {branch, applied[], skipped[], diff}`: delete-if-exists then `checkout -b wc/<TICKET>`; for each valid edit do the **single** exact replacement (fallback: normalized match → map back to the literal span); no-op replacements → skipped; `git diff` captured and published as an `artifact {kind: diff}` event. Nothing is pushed here.
- `cleanup(ticket_key)`: drop the wc branch, return to base.
**Verification:** applying the 8055 patch changes exactly one line of the local `CommonEnovia.script`; `git diff` shows the one-clause removal; no-op and ambiguous edits are skipped with reasons; reset between attempts leaves a pristine tree.
**DoD:** atomic local apply; robust matching; clean reset proven; diff event emitted.

---

## Phase 2.3 — Tier-0 lint gate in the loop [UP-3] — *Owner: Claude Code*
Wire `src/static/lint.py` as the first validation tier: after apply, lint every touched file. Any issue → publish `step.failed (linting)` with the issues, record as attempt feedback, **skip the SUT entirely**, continue to the next attempt. Unit test: a seeded unbalanced-`end if` patch consumes an attempt in milliseconds and never calls the runners.
**DoD:** lint gate wired; SUT never invoked on a lint-failing patch.

---

## Phase 2.4 — Local `runscript` inner loop *(if `INNER_LOOP=local-runscript`)* — *Owner: Claude Code ((User): live checks)*

### Step 2.4.1 — `src/integrations/epf_runner.py`
`run(script_repo_path, run_id, timeout=900) -> dict`:
```
cmd = [settings.epf_runscript_path, <abs script under working_copy>,
       "-DefaultDocumentDirectory", settings.epf_default_doc_dir,   # parent of *.suite → cross-suite resolution
       "-GlobalResultsFolder", data/agent_runs/{run_id},
       "-CommandLineOutput","YES","-ReportFailures","YES",
       "-MaxWaitForLicense","600"] (+ ["-LicenserHost", host] if set)
```
Exit **127 → `{"status":"NO_LICENSE"}`**; else PASS/FAIL by exit code; `_parse_results(folder)` reads `LogFile.txt` + collects `*.png`/`*.tiff` (≤8) → `{log, screenshots, results_folder}`. Run via `asyncio.to_thread` (it blocks). If the orchestrator and runner are different VMs, **(User)** decides: co-locate a small worker on `eggptdai10` (a thin FastAPI `POST /run` wrapping this class — Claude Code builds it) or run the orchestrator on the runner VM; record choice in `config/enovia.yaml`.
**Verification ((User), VM):** the known-good original 8055 test → PASS (exit 0); a deliberately broken copy → FAIL with parseable log + screenshots.
**DoD:** PASS/FAIL by exit code; artifacts parsed; license-wait handled. *(If `INNER_LOOP=practice-dai`: skip this phase — Phase 2.5 serves every attempt.)*

---

## Phase 2.5 — The Practice gate (authoritative SUT validation) — *Owner: Claude Code + (User)*

> Mechanism proven end-to-end in PoC 2b: the Practice Test Config's git connection is **pre-wired to the Practice repo's `/practice` branch** and its SUT connection is prebuilt — so validation = *push the candidate code there, trigger, read the results*. No production-DAI repointing, no production-repo writes, nothing to reset afterward.

### Step 2.5.1 — Confirm practice wiring — *(User)*
Confirm in `config/enovia.yaml → practice`: repo URL + PAT, `branch: practice`, Practice DAI base URL + creds, `test_config_id`, the trigger endpoint, and `completion_mode: webhook | eggplant_runner | poll_backoff` (= `PRACTICE_COMPLETION_MODE` from PoC 2b) plus its mode-specific settings (webhook secret + route, or runner binary path, or poll backoff schedule + timeout). If the Practice repo can drift from production, **(User)** decides the sync policy (recommended: the gate force-pushes the full candidate state each time, so drift doesn't matter for validation correctness).

### Step 2.5.2 — `src/integrations/practice_dai.py` + `src/orchestrator/practice_gate.py`
**Invariant (binding): the LLM is never in the wait path.** Claude is called only to generate the fix (before triggering) and to interpret the result (after it resolves). Whichever `completion_mode` is active, waiting is a plain orchestrator coroutine — an `asyncio.Event`, an awaited subprocess, or an `asyncio.sleep` poll loop — never a tool the agentic loop (UP-1) calls repeatedly. A run can legitimately take 20 min–2 hr; nothing in that path may resend a conversation to the model.

`PracticeDAI`: `trigger(test_config_id) -> runid` (the PoC-2b API), plus `log_by_runid`/`error_screenshots` reuse from `dai_client` pointed at the Practice DAI base URL. Completion detection branches on `completion_mode`:
- **`webhook`:** `POST /api/webhooks/dai` (new route, alongside the plan3 Bitbucket webhook) verifies a shared secret, matches the payload to a pending runid, and resolves a per-run `asyncio.Event`; `wait_complete(runid, timeout=<generous, e.g. 3h safety net>)` just awaits that event — the timeout only guards a lost delivery, it is not the normal completion path.
- **`eggplant_runner`:** `await asyncio.create_subprocess_exec(...)` then `await proc.wait()`; exit code 0 = PASS, else FAIL; parse `--result-path` JUnit XML for the run's identifying info.
- **`poll_backoff`:** `wait_complete(runid, timeout=<config, must cover observed 20min–2hr range>, backoff=[15,30,60,120])` — an `asyncio.sleep`-based loop, HTTP-only, no LLM calls.

`PracticeGate.validate(ticket_key, wc_branch) -> {status, runid, log, screenshots, result_url}`: **under the track lock** →
1. `git push practice wc/<TICKET>:refs/heads/practice --force` (the candidate state becomes `/practice`; force is safe — the branch is disposable and the lock serializes writers);
2. `trigger(...)` → capture `runid`; publish `agent.message` ("Practice run <runid> started…") + periodic `step.progress` heartbeats (templated strings, not LLM-generated) while waiting — cheap regardless of `completion_mode`, since with `webhook` there's no polling to hang a heartbeat off of, so heartbeats there are just an elapsed-time timer, not tied to network activity;
3. on completion (event/subprocess/poll resolves), fetch that run's log + error screenshots (failure feedback for the retry controller; evidence on PASS) + `result_url`;
4. release the lock. Timeout → `{status: TIMEOUT}` (degradation path, plan3).
**Verification ((User)):** push a known-good state via the gate → trigger → PASS with evidence retrieved; push a deliberately broken state → FAIL with the failure log captured; confirm no LLM call occurs between trigger and resolution (check trajectory/cost log for the run — cost during the wait window must be $0).
**DoD:** gate returns PASS/FAIL for a candidate branch purely via the practice infrastructure; lock respected; evidence retrieval works on both outcomes; wait mechanism matches `PRACTICE_COMPLETION_MODE` and burns no tokens.

---

## Phase 2.6 — Retry controller [UP-7, UP-13, UP-15] — *Owner: Claude Code*

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
          res = epf.run(...) if INNER_LOOP=="local-runscript" else practice_gate.validate(ticket, wc_branch)
          if res.NO_LICENSE: backoff once, retry same candidate       # runscript path only
          if res.PASS:
              if not callers_pass(fix, run): last_failure="blast-radius regression: <suite>"; continue
              if INNER_LOOP=="local-runscript":
                  g = practice_gate.validate(ticket, wc_branch)       # authoritative, once per fix
                  if not g.PASS: last_failure=g.log_tail; continue
              return {"status":"pass", "attempt":attempt, "fix":fix, "evidence":{**res, **gate_evidence}}
          last_failure = res.log_tail or res.raw
  if all candidates LOW/invalid: return {"status":"low_confidence","attempt":attempt}
return {"status":"exhausted","attempts":max_attempts,"last_logs":last_failure}
```
- `callers_pass(fix, run)`: from blast radius pick the configured smoke set of caller tests (per `enovia.yaml → blast_radius_smoke`), run via the same inner mechanism; all must pass.
- `BudgetGuard` charged on every model call and (optionally, fixed estimate) per SUT run; `BudgetExceeded` → graceful `{"status":"budget_exceeded"}` preserving artifacts.
- Every decision point publishes `agent.message` + step events so the chat narrates the loop ("Attempt 2: re-diagnosing with extended thinking…").
**Design notes:** fresh-diagnosis-on-failure mirrors Self-Debugging/Reflexion — execution feedback drives the next attempt; `runscript` (if available) is the fast inner oracle, the Practice gate the production-fidelity oracle; if `INNER_LOOP=practice-dai`, the Practice gate serves every attempt directly. The callers run is the regression guard.
**Verification (mock-level by Claude Code; live by (User)):** (a) golden 8055 → PASS attempt 1, inner + Practice gate green; (b) a seeded 2-step bug → fails attempt 1, fresh re-diagnosis with extended thinking fixes on attempt 2; (c) a fix breaking a caller → caught by `callers_pass`; (d) a lint-failing patch consumes an attempt without touching the SUT; (e) budget cap aborts cleanly.
**DoD:** loop passes the golden ticket; adds thinking on retries; N-best on retry; never declares success without blast-radius + Practice gate; lock respected; bounded at 3.

---

## Phase 2.7 — In-chat approval gate [UP-9] — *Owner: Claude Code*

### Step 2.7.1 — Backend
On `status=pass`, pipeline enters `awaiting_approval`: persist an `approvals` row; publish `approval.requested` with payload `{diff, evidence: {screenshots, log_excerpt, dai_result_url}, fix_summary, expires_at}`. `POST /api/runs/{id}/approval {decision, comment?}` resolves it (asyncio.Event wakes the pipeline; publish `approval.resolved`). `approval_mode: auto` (config) skips the pause but still records an auto-approval row. Timeout (default 24h) → graceful park: label intent recorded, run marked `awaiting_approval` and resumable.
### Step 2.7.2 — Frontend
`ApprovalCard`: rendered diff (green/red), evidence thumbnails, DAI link, **Approve & Create PR** / **Reject** buttons (+ optional comment). Reject → pipeline records the reason as trajectory feedback and ends the run as `rejected`. In plan2, approval's effect stops at "approved, awaiting publisher" — the actual push/PR arrives in plan3 (the card says so).
**Verification:** end-to-end with a stub publisher: approve → run proceeds; reject → run closes with reason; reload mid-approval → card restored from DB.
**DoD:** HITL pause/resume proven across restarts; auto mode works.

---

## Phase 2.8 — Shadow mode (≥15 fresh tickets) + GATE 2 — *Owner: (User) drives, Claude Code analyzes*

**Actions:** **(User)** select ≥15 fresh Enovia tickets; run the full fix loop in **shadow** (`shadow: true` config → validates fully — including Practice-repo pushes, which are the validation mechanism — produces the `wc/` branch + would-be PR description, but posts nothing to Jira and **pushes nothing to the production repo**). For each, record: first-attempt pass, final pass (≤3) + which attempt, lint-gate saves, and **functional equivalence vs the developer's actual fix** ((User) judges; Claude Code prepares side-by-side diffs). Claude Code computes all rates with Wilson CIs and writes `data/evals/shadow_report.md`.

**GATE 2 (print; (User) confirms):**
| Metric | Target | Measured |
|---|---|---|
| First-attempt fix pass | **≥60%** | ☐ (+CI) |
| Final pass (≤3 attempts) | **≥80%** | ☐ (+CI, + attempt histogram) |
| Functional equivalence to dev fix | **≥75%** | ☐ |
| Regressions (caller-suite breakage) | **0** | ☐ hard zero |
| Avg fix+validation time | < 15 min (local inner) / < 30 min (practice-dai per attempt) | ☐ |
| Cost per ticket | reported honestly ($2–6 expected, Opus 4.6 + caching) | ☐ |

**DoD:** Gate 2 met with CIs; any regression → pause, root-cause, fix. **Plan 3 cannot begin until Gate 2 passes.**

➡ Proceed to **plan3_lifecycle_rollout.md**.
