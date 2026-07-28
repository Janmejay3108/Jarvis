# PLAN 4 — HARDENING & TRUST LAYER — v1 FOR THE AGENT

> **Prereq:** GATE 2 passed (plans 0–2 executed as written). **Objective:** promote the lessons of the five Sprint-17 post-mortems (TESTAUTOMA-8278, -8448, -8449, -8450 ×2) from findings into built, tested subsystems: a triage gate that routes before fixing, diagnose-only outcomes scored as wins, a signature-based validation verdict immune to flakes, a human-question channel with permanent memory, and Jira autonomy that is earned rather than assumed.
>
> **Relationship to plans 0–3:** this plan modifies the **codebase** those plans produce — never their documents. Plans 0–3 remain unedited and are executed exactly as written. Where this plan says "the retry controller from plan2 §2.6," it means the code that step produced, not the file.
>
> **Recommended execution slot: 0 → 1 → 2 → 4 → 3.** Plan3 is the production rollout to Megha's team; running it before plan4 means rolling out without the triage gate, the flake-proof verdict, and gated Jira comments — spending team trust exactly when it is scarcest, with no schedule pressure forcing it. Plan4's number reflects creation order, not execution order. If plan3 has already run, plan4 still applies cleanly; the costs of the late slot are listed in §4.9.
>
> Build order: 4.0 carry-alongs → 4.1 triage & routed outcomes → 4.2 verdict engine → 4.3 ask_human → 4.4 gated Jira → 4.5 reasoning hardening → 4.6 knowledge & repo intelligence → 4.7 clustering & integrity → 4.8 metrics, rollout alignment & GATE 4.

**The re-weighting in one line:** triage first; fix only what is safely fixable; a correct "don't fix — here's why, here's the owner" is a first-class SUCCESS; the validation verdict is signature-based, never exit-code-based; unknown facts are asked once and remembered forever; Jira speaks only through a human until precision is proven.

---

## 0.1 New upgrades table (UP-16 … UP-25 — extends the master's §2.2 numbering; master file is NOT edited)

| # | Upgrade | What changes | Proved by |
|---|---|---|---|
| UP-16 | **Triage hard gate** | Classification becomes a routing decision with two exits (fix / diagnose-only), not an advisory family hint | 8449 ("classify before you patch"), 8450 (data issue briefly chased as code) |
| UP-17 | **Diagnose-only terminal outcomes** | `diagnosis_only:{env,test_data,infra,app_bug,change_scope,flake}` are designed, templated, scored-as-SUCCESS exits | 8450 → ENOVIA3DX-9162 was the *correct* output, not a fallback |
| UP-18 | **`ask_human` pause/resume tool** | Agent asks 1–2 sharp questions mid-run; the answer resumes the run and drafts a context.md suggestion | 8278: fix unknowable from inputs; ONE fact ("KEYSIGHT PART NUMBER") solved it |
| UP-19 | **Signature verdict + flake policy + baseline** | PASS = the ticket's failure signature is gone; flake allowlist; baseline/reproduce run for ambiguous families | 8278: a launch flake flipped a correct fix to FAILURE |
| UP-20 | **Attempt ledger** | Structured history of all attempts fed into every retry, with the invariant instruction | 8448: three token swaps all died at the same ~30 s mark |
| UP-21 | **Divergent-mechanism candidate** | At attempt ≥2, one N-best slot proposes an alternative mechanism (prefer non-visual oracle) | 8448: the real fix was OCR→disk-check, not a minimal diff |
| UP-22 | **Failure clustering / dedup** | Signature hash checked against active runs, trajectories, open tickets before spawning work | One app UI change breaks N tests identically (8278 shape) |
| UP-23 | **Graduated Jira autonomy** | All diagnosis comments human-gated through chat; a precision metric unlocks auto mode | One wrong comment in week 1 costs more trust than ten silent tickets |
| UP-24 | **JARVIS-run integrity check** | **Double assert** that the triggered run executed the pushed commit before any PASS/FAIL is trusted: `git ls-remote agentic-eggplant-automation refs/heads/Enovia` == pushed SHA **before** trigger, and the run log's `Using Git commit SHA: '<sha>'` == pushed SHA **after** completion. Both are mandatory; a mismatch yields `STALE_SYNC`, never a verdict | Force-push + pre-wired git sync can silently validate stale code. Now fully implementable: PoC 2b proved the run log records the commit SHA and the git connection syncs at run start |
| UP-25 | **Git history tools + pre-apply freshness** | blame / file-log / diff-since-green tools; re-diff shared targets before apply | 8449 root-caused via commit c47ef962; 8448 mid-flight handler collision |

## 0.2 Global invariants added by plan 4 (enforced in code, extend master §6.4's list)
- **Route conservatism:** the pipeline may automatically *downgrade* a run from `autofix` to `diagnose_only` at any point; it may **never** automatically upgrade `diagnose_only` to `autofix` — that upgrade requires explicit human approval in chat.
- **Never weaken silently:** no candidate may remove or relax an assertion/validation to achieve green; any best-effort / `isMandatory`-style relaxation must set `weakens_assertion: true` and be highlighted in the PR description (§4.5.5).
- **Verdict-based pass:** once Phase 4.2 lands, no attempt is judged by raw exit code; the verdict engine decides. Exit codes feed only `NO_LICENSE` detection.
- **Gated Jira:** in `gated` mode, zero Jira writes occur without an in-chat approval.

---

## Phase 4.0 — Carry-along choices while executing plans 0–2 — *Owner: (User) + Agent*

> These items require **zero edits** to plan files 0–3. They are runtime choices inside artifacts those plans already tell you to create (config values, a labeling sheet, PoC questions). Skipping any of them breaks nothing — it only duplicates work later; the cost of skipping is stated per item so the choice is informed.

1. **Interpretation rule for plans 0–3:** any literal "Opus 4.6" / `claude-opus-4-6` remaining in the v2 plan texts means "the configured Opus model (`settings.model`)." Apply mentally while executing; do not edit the files. *(Cost of skipping: momentary confusion; zero rework.)*
2. **PoC 7 labeling sheet (plan0 A.10):** when writing `scripts/categorize_tickets.py`, include three extra columns per ticket — `families_present[]` + `multi_cause: bool`; `knowledge_source ∈ {self_contained, documentable, external}`; `fixable_component: bool` (ticket contained ≥1 self-contained code-logic sub-failure). Label the ≥50 tickets **once**, with all columns. Phase 4.1's router evaluation consumes them. *(Cost of skipping: a human re-labels ≥50 tickets by hand later.)*
3. **PoC 2b two extra questions (plan0 A.2) — ✅ RESOLVED.** Both answered while proving the JARVIS validation path; recorded in `poc_results.md`:
   - **(a) DAI webhook notifications** — the **webhooks admin UI is available on JARVIS and Jay is admin**, so webhooks are enable-able. The profile is **not yet registered**, so `poll_backoff` is the day-one completion mode and webhook is the upgrade path (**O1**).
   - **(b) Run→commit visibility — yes.** The run log records **`Using Git commit SHA: '<sha>'`**, and the test config's git connection **syncs at run start** (not a cached clone). This makes **UP-24 fully implementable rather than a residual risk**, and is why §4.7.2's fallback-WARN branch has been removed.

   *(The original "cost of skipping: repeating the PoC during Phase 4.7" note is retained as historical rationale — it is why these questions were asked up front.)*
4. **Live-use guard:** until Phase 4.4 delivers gated mode, run any non-eval usage with `jira_writes_enabled: false` (plan1 already supports the boolean; the eval harness already forces false). *(Cost of skipping: unapproved bot comments on real tickets — the exact week-one failure this plan exists to prevent.)*
5. *(Optional, zero cost)* When implementing plan1 §1.1.2, keep the pipeline's step sequence as a data-driven list rather than hard-coded calls, so Phase 4.1 inserts `triage` without surgery.

**DoD:** items 2–4 confirmed done (or consciously skipped, noted in `PROGRESS.md`) before Phase 4.1 begins.

---

## Phase 4.1 — Triage gate + routed outcomes [UP-16, UP-17] — *Owner: Agent*

### Step 4.1.1 — `src/analysis/triage.py`
`TriageGate.classify(ticket_text, log_entries, matched_error_entry, screenshot_path?) -> TriageResult {route: autofix|diagnose_only|ask_human, family, confidence: HIGH|MEDIUM|LOW, signals[], evidence[], reasoning}`.
- **Layer 1 — deterministic rules (zero cost, run first):** `STInvalidBoolean`/syntax/handler-not-found → code family; `"not allowed for spirent Part"` / trigger #1500167 → `test_data`; server/login unreachable, 3DSPACE nodes down, license errors → `environment_issue`/infra; Jira issue type or label "Change Scope" → `change_scope`; failing step ∈ `flake_allowlist` → `transient_flake`.
- **Layer 2 — one forced-tool LLM call** (`settings.model`) with compacted log + delimited ticket text + the screenshot when the failure is a UI/text lookup; same output schema.
- **Routing table:** `family ∈ triage.fixable_families ∧ confidence ≥ min_confidence_for_autofix` → `autofix`; environment / test_data / infra / application_bug → `diagnose_only`; change_scope → `ask_human`; LOW confidence anywhere → `ask_human` (one question) or `diagnose_only` — **never guess-and-patch**. Encode the rationale as a code comment: a false "fix it" burns SUT hours and trust; a false "escalate" costs a human a look they'd have taken anyway.
- Config (add to `config/enovia.yaml`):
```yaml
triage:
  fixable_families: [boolean_logic_gap, silent_exception_swallowing, search_rectangle,
                     dpi_cascade, text_label, missing_wait, handler_name_mismatch,
                     config_value_stale, flaky_oracle]
  min_confidence_for_autofix: MEDIUM
```
- New families registered alongside the existing list: `flaky_oracle` (OCR-of-transient-UI validation; 8448), `change_scope` (app redesign needing new product knowledge; 8278), `transient_flake` (known-flaky infra step).

### Step 4.1.2 — Pipeline insertion + run-model extension
Modify the pipeline built in plan1 §1.1.2: insert `triaging` between `fetch_logs` and `localize`; branch on `TriageResult.route` —
```
read_ticket → fetch_logs → [cluster_check, Phase 4.7] → triage
  ├ transient_flake       → diagnosis_only:flake (evidence: allowlist match) → post → done
  ├ env/data/infra/appbug → localize (evidence-grade) → analyze(diagnose) → post → diagnosis_only ✔
  ├ change_scope          → ask_human [Phase 4.3] → (answered → route per answer) | (unanswered → diagnosis_only:change_scope)
  ├ LOW confidence        → ask_human | diagnosis_only
  └ autofix-eligible      → localize → analyze → FixValidationLoop (plan2 code)
```
Extend `RunStatus` with `triaging`, `running_baseline`, `awaiting_human_input`, and terminal `diagnosis_only`; extend `AgentRun` with `triage: TriageResult`, `diagnosis_route?`, `failure_signature?` (Phase 4.2), `baseline?`, `attempt_ledger: []`, `human_questions: []`. Enforce the route-conservatism invariant in this code path.

### Step 4.1.3 — Per-route Jira output templates
`src/analysis/prompts/jira_templates/` — one consolidated comment per ticket: route + confidence header; evidence bundle (screenshot(s), trimmed log, DAI link); recommended-action string; suggested owner. When confidence < HIGH the template *asks for confirmation* rather than asserting ("signals point to environment — no System Table view on BST; needs app-team confirmation"). Labels per route: `ai-diagnosed` (fix path), `ai-diagnosis-env`, `ai-diagnosis-data`, `ai-diagnosis-infra`, `ai-diagnosis-appbug`, `ai-diagnosis-changescope`, `ai-flake`. (Posting behavior is governed by Phase 4.4; until then these render into the chat only.)

### Step 4.1.4 — Router evaluation
Run `TriageGate` over the PoC-7 three-axis labeled set (Phase 4.0 item 2). Produce a confusion matrix and per-route precision/recall with Wilson CIs.
**Verification:** fix-route precision ≥90% on the labeled set; misroutes reviewed and either rule-patched or accepted with a note.

### Step 4.1.5 — Eval scoring update
Extend plan1 §1.7's `scoring.py`: a diagnose-only run scores `correct` when the route is right AND the recommended action matches what actually resolved the historical ticket — counted as a **win**, not a miss.

**DoD (Phase 4.1):** pipeline branches on route in mocked end-to-end tests; conservatism invariant unit-tested (downgrade free, upgrade requires approval); router ≥90% fix-route precision; templates render for every route.

---

## Phase 4.2 — Verdict engine: signature pass, flake policy, baseline [UP-19] — *Owner: Agent ((User): live checks)*

### Step 4.2.1 — `src/orchestrator/verdict.py`
- `FailureSignature {script, failing_handler, step_ref, message_type, target (normalized lookup text/image), error_type}` — extracted at `fetch_logs` from the matched error entry; stored on the run. Plus `extract_signatures(log_entries) -> [FailureSignature]` for full-run failure sets.
- `verdict(candidate_logs, original_sig, baseline_sigs, allowlist) -> {verdict: PASS_FOR_TICKET|FAIL|FLAKE_SUSPECT, resolved_original, new_failures[], allowlisted[], baseline_matched[], reasoning}`.
- **PASS_FOR_TICKET** := original signature ABSENT ∧ every remaining failure ∈ allowlist ∪ baseline_sigs. **FLAKE_SUSPECT** := the run died at an allowlisted infra step *before reaching* the target step (the fix was never exercised), or residuals are allowlist-shaped but ambiguous.
- Config additions:
```yaml
validation:
  flake_allowlist: ["login", "3DEXPERIENCE splash", "Type the name", "Run window"]
  flake_rerun_max: 1
  baseline_policy:
    deterministic_families: skip        # STInvalidBoolean-class reproduces by construction
    lookup_families: required           # text_label, search_rectangle, image_staleness, missing_wait
    others_required_below: HIGH         # baseline required when triage confidence < HIGH
```

### Step 4.2.2 — Baseline / reproduce run
Where policy requires it, run the **unpatched** test once via the **JARVIS validation gate** before attempt 1. Outcomes: (a) original signature reproduces → store `baseline_sigs`, proceed; (b) does NOT reproduce → **downgrade** the route to `diagnosis_only:{env|test_data}` with evidence "not reproducible on the validation environment" — a finding, not a failure (the 8450 BST lesson cuts both ways: env differences invalidate naive validation in either direction); (c) baseline itself flaky → record, apply allowlist. Cache the baseline per (ticket, base SHA) so retries never repeat it. Cost honesty in code comments: one extra SUT cycle where required, purchased against up to three wasted attempts and a wrong PR.

### Step 4.2.3 — Flake re-run budget
A FLAKE_SUSPECT triggers ≤`flake_rerun_max` re-runs of the *same candidate* without consuming an attempt; a second FLAKE_SUSPECT counts as FAIL with a flake note. `callers_pass` smoke runs also apply the allowlist.

### Step 4.2.4 — Retry-controller swap (the one planned refactor of plan-2 code)
In the controller built by plan2 §2.6: replace `if res.PASS` with `if verdict(...).verdict == PASS_FOR_TICKET`; `last_failure` becomes the *new failure signature(s) + log tail*. Contained change (~1 day); the golden 8055 regression must stay green through it.

**Verification ((User)):** replay the 8278 shape — a correct fix plus a seeded launch-flake failure → PASS_FOR_TICKET. A run missing the original failure but showing a NEW non-allowlisted failure → FAIL naming the new signature.
**DoD (Phase 4.2):** verdict unit-tested on synthetic fixtures incl. the 8278 fixture; "correct fix lost to flake" impossible by construction on the fixture; retry controller consumes verdicts only; baseline caching verified.

---

## Phase 4.3 — `ask_human` channel [UP-18] — *Owner: Agent*

### Step 4.3.1 — Tool + persistence + resume
Register `ask_human(question, why_needed, what_was_tried, options?: [str])` — non-terminal; capped by config `human_input: {max_questions_per_run: 2}`. Mechanics: publish `human_input.requested` (question/why/tried/options/expires); persist to the approvals table with a new `kind` column (`approval|question|jira_post`, default `approval` — a migration, not a new table); pipeline awaits the same asyncio.Event machinery as plan2's approval gate; timeout → park resumable.

### Step 4.3.2 — Surface
`POST /api/runs/{id}/human_input {answer}` resolves the wait; the answer is injected into the loop as a delimited **HUMAN-VERIFIED FACT** block. Frontend: `QuestionCard` (question, why-needed, quick-reply options + free text), survives reload like the approval card.

### Step 4.3.3 — Capture to knowledge
Every answer immediately drafts `tracks/enovia/context_suggestions/<TICKET>-q<n>.md` (fact, provenance run/ticket/date, proposed context.md section) for the weekly human review. The back-and-forth then costs once per fact, not once per ticket.

### Step 4.3.4 — Golden replay #2 (8278)
Scripted end-to-end replay: triage → `change_scope` → ask_human ("what replaced 'Set Enterprise Item Number'?") → canned answer ("the value now goes in the new KEYSIGHT PART NUMBER field") → two-call-site fix → verdict PASS_FOR_TICKET despite the seeded launch flake. Mock-level mandatory; live optional. 8278 joins 8055 as the second permanent golden regression (8055 proves the Type-A spine; 8278 proves ask_human + flake attribution).

**DoD (Phase 4.3):** a scripted loop asks one question, pauses, survives reload, resumes with the injected fact; question budget enforced; suggestion file drafted; 8278 replay green.

---

## Phase 4.4 — Graduated Jira autonomy [UP-23] — *Owner: Agent ((User): policy owner)*

### Step 4.4.1 — Config replaces the boolean
```yaml
jira_writes:
  diagnosis: gated        # gated | auto | off   (eval harness forces off, unchanged)
  lifecycle: auto         # comments documenting an already-approved PR
  labels: follow_parent
graduation:
  min_posts: 30
  min_precision: 0.90
```
`gated` = the drafted comment publishes an `approval.requested {kind: jira_post, editable_body}` card in chat with **editable text** + Post / Discard; on Post → the jira client fires; the drafted-vs-posted edit distance is stored. `lifecycle: auto` is acceptable because the PR approval already covered the substance. Retire the old boolean in behavior (config key may remain for compatibility).

### Step 4.4.2 — Precision metrics
Track per posted comment: approved-as-drafted / edited / rejected, and a weekly-review human verdict correct/incorrect. `graduation` thresholds gate any flip of `diagnosis` to `auto` — a deliberate, documented config change by **(User)**, never a drift.

**DoD (Phase 4.4):** a gated run pauses at the JiraPostCard, posts only on approval, records edits; zero ungated writes possible in gated mode (asserted in tests).

---

## Phase 4.5 — Reasoning hardening [UP-20, UP-21 + evidence completeness + scope/intent] — *Owner: Agent*

### Step 4.5.1 — Attempt ledger [UP-20]
Append `{attempt, hypothesis, change_summary (file + one-liner), failure_signature, failing_step, elapsed_at_failure_s}` after every attempt; inject the full ledger into every re-diagnosis and fix call with the instruction: *"If multiple attempts failed at the same step/elapsed point under different changes, the ROOT CAUSE IS THE INVARIANT across them, not the value you keep changing — switch failure family or propose a MECHANISM change."*

### Step 4.5.2 — Divergent candidate [UP-21]
At attempt ≥2, exactly one N-best slot uses `prompts/fix_divergent.md`: "The current approach may be fundamentally unreliable. Propose an ALTERNATIVE MECHANISM achieving the same validation intent; prefer a non-visual oracle (filesystem/API/clipboard) over OCR; cite the repo precedent you are copying." Candidate carries `divergent: true` into the trajectory; ranked by the same `static_rank`.

### Step 4.5.3 — Evidence completeness (diagnosis schema)
Add required `signals_explained: {log, screenshot, timeline}` and `unexplained_signals: [str]` to the Diagnosis schema; engine rule: `unexplained_signals` non-empty ⇒ confidence capped at MEDIUM. For families in {text_label, search_rectangle, image_staleness, missing_wait, flaky_oracle}: if `submit_diagnosis` arrives without a prior `view_screenshot` call, reject once with "view the screenshot and reconcile before submitting" and force one continuation. (Mechanizes the 8450 lesson: the text log produced a confidently wrong Spirent claim until the screenshot corrected it — the root cause must explain every signal, and the screenshot is ground truth for UI state.)

### Step 4.5.4 — Scope anchoring
Anchor every (re-)diagnosis to the ORIGINAL ticket's `failure_signature`. New unrelated failures must be classified `prerequisite_blocker` (may be routed around only with known-safe primitives — scroll/wait — and listed separately in the diagnosis/PR) or `out_of_scope` (noted for humans, never silently absorbed into the fix).

### Step 4.5.5 — Test intent + assertion-weakening flag
`ProposedFix` gains `test_intent: str` (one line: what this test must validate), injected into `fix_user.md`. `FixEdit` gains `weakens_assertion: bool` — REQUIRED true for any edit that removes/relaxes a validation or adds a best-effort/`isMandatory`-style path. Prompt rules: "never remove or weaken an assertion to achieve green"; "an intent-preserving fallback (original path stays priority, real validation still runs — the 8450 FIX-2 shape) is allowed but MUST set the flag." The PR description renders any such edit under a highlighted "⚠ assertion-relaxing change — review intent" section. (The pattern was the *right* fix in 8450 and the *forbidden* one in 8278 — only a human reviewer can tell which, so it must be named for them.)

**DoD (Phase 4.5):** mock tests — 3 same-step failures produce the ledger + invariant instruction in the prompt; attempt-2 candidate set contains one divergent candidate; a lookup-failure fixture without a screenshot view is rejected once then accepted; a seeded check-deleting candidate carries the flag (or is rejected); the PR template renders the warning block; golden 8055 still green.

---

## Phase 4.6 — Knowledge & repo intelligence [UP-25 + lint + context seeds] — *Owner: Agent + (User for curation)*

### Step 4.6.1 — Git history tools
Add read-only tools `git_blame(path, start, end)`, `git_file_log(path, n=10)` (message + files + date), `diff_since_green(green_ref?)` — budget ≤3 calls/run, suggested in the prompt when triage/diagnosis suspects a regression ("was passing recently", a last-green runid exists). `diff_since_green` returns "unavailable" gracefully when no runid→commit mapping exists.

### Step 4.6.2 — Pre-apply freshness
Before `apply()` (plan2 §2.2 code): `git fetch origin` and diff the target files against the run-start SHA. If changed upstream: config `on_upstream_change: rediagnose` (default) → refresh content, re-run localization + diagnosis once, continue; a second collision in the same run → flag to human. (8448's mid-flight shared-handler collision, prevented for the price of one fetch.)

### Step 4.6.3 — Boolean-context lint rule
In `src/static/lint.py`: flag any `if` / `else if` / `repeat while|until` whose condition begins with a bare property list — `(text:` / `(image:` / `(imageName:` / `{` — not wrapped by a call in config `boolean_wrappers:` (seed `[ImageFound]`, config-extendable). Unit tests: the 8450 BEFORE line is flagged; the AFTER (`ImageFound(...)`) line is clean; document the regex-level limitation on deeply nested parens. Register `flaky_oracle` as a family with the disk-check exemplar and the rule "filesystem/API/clipboard beats pixels." Do **not** attempt a full SenseTalk grammar (see Out of Scope).

### Step 4.6.4 — Seed context.md (curated with Megha's team; facts already paid for)
Mandatory sections written now:
- **ENVIRONMENT MATRIX:** BST (`3dxspacebst.supplychain.keysight.com`, 156.140.21.48) has no "System Table" saved view; the Source column is default-visible there; URL migration `3dxspace23xbst`→`3dxspacebst` (commit c47ef962) moved 3DDashboard lower in the app list (scroll required).
- **TEST-DATA RULES:** "first Preliminary EC Part" selection is nondeterministic after a refresh; Spirent parts = Engineering Responsibility ∈ {SP1–SP4}, server trigger #1500167 blocks BOM/attribute updates — **never** patch a script to mask this; EC-Part (policy) and Spirent (attribute/trigger) are independent properties.
- **ORACLE / OCR CONVENTIONS:** fidelity hierarchy filesystem/API > DOM/app > clipboard > template-match > OCR-of-live-UI; never OCR-validate transient popups or short tokens like ".csv"; the DPI/validWords ladder pattern; `validateDownloadedFileOnDisk` as the disk-oracle precedent.
- **LOG SEMANTICS:** "Exceptions" can be by-design not-found probes, not failures; real failures are often `severity=INFORMATIONAL` + `message_type=imagefound`; read the FIRST failure, not the last line.
- **BOOLEAN IDIOM:** any image/text check used as a condition MUST be wrapped in `ImageFound()` — a bare property list is a type error.
- **KNOWN-FLAKY STEPS:** login, 3DEXPERIENCE splash, "Type the name", Run window (source of the 4.2 allowlist).

### Step 4.6.5 — Capture loop live from the first run
Any human-supplied fact during ANY run (an ask_human answer, a chat correction of a diagnosis) immediately drafts a `context_suggestions/` file — not only post-merge. The weekly human review cadence from plan3 §3.7 is unchanged; only the drafting trigger is earlier.

**DoD (Phase 4.6):** tools budgeted and unit-tested; freshness test with a simulated upstream commit triggers one re-diagnosis then proceeds; lint tests green; context.md contains all six sections; a mid-run human fact produces a suggestion draft.

---

## Phase 4.7 — Clustering & integrity [UP-22, UP-24] — *Owner: Agent ((User): confirms DAI answers)*

### Step 4.7.1 — Failure clustering / dedup
After `fetch_logs`, compute two hashes: **strict** = (failing script, failing handler, message_type, normalized lookup target) and **loose** = (handler, target). Check, in order: (a) active runs — strict match → attach this ticket to the running run (DB link, chat message "TESTAUTOMA-X shares this failure with running TESTAUTOMA-Y; attaching"), do not spawn duplicate work; (b) recent trajectories — strict match on a solved run → surface it first as a chat question ("same signature fixed in PR #N — verify & reuse?"); (c) open tickets via best-effort JQL (component, status != Done, handler/target text) — loose matches → flag "possible cluster (N tickets)" in chat and in the diagnosis draft. Batch handling always requires human confirmation; no auto-batch-patching. Rationale in code comments: one app UI change breaking thirty scripts identically is simultaneously the highest-value event (one diagnosis, one fix, N tickets closed) and the scenario where a naive agent burns N budgets and posts N comments.

### Step 4.7.2 — JARVIS-run integrity check
In `ValidationGate.validate` (plan2 §2.5.2 code): record the pushed SHA; immediately before `trigger()`, assert `git ls-remote agentic-eggplant-automation refs/heads/Enovia` == pushed SHA; after completion, assert the run log's `Using Git commit SHA: '<sha>'` == pushed SHA.

**Both asserts are mandatory.** The earlier conditional hedging is obsolete: PoC 2b (Phase 4.0 item 3) **confirmed** that the run log records the executed commit and that the git connection syncs at run start, so there is no fallback-WARN branch and no residual-risk path — a run that cannot produce its executed SHA is an integrity failure, not a warning.

A mismatch at **either** edge aborts the gate with `{status: STALE_SYNC}` instead of returning a verdict — **no PASS/FAIL is ever trusted from a run whose executed commit cannot be tied to the pushed candidate.**

> **Division of labour with plan2:** plan2 §2.5.2 now *implements* both asserts as part of the gate's normal path. This step's job is **enforcement and testing** — proving the asserts cannot be bypassed, that `STALE_SYNC` never degrades into a verdict, and that the retry controller treats it per plan2 §2.6 (no attempt consumed, retry once, then abort preserving artifacts) — rather than introducing the design.

**DoD (Phase 4.7):** two synthetic tickets with one signature → second attaches, one fix branch would serve both, both Jira drafts reference the one PR; STALE_SYNC test green; **both UP-24 asserts active on every JARVIS validation cycle**.

---

## Phase 4.8 — Metrics, rollout alignment & GATE 4 — *Owner: Agent ((User): the contract meeting)*

### Step 4.8.1 — Metrics additions
Extend the metrics surface (plan3 §3.6's endpoint if already built; otherwise register these for it): routing precision (router decisions later confirmed correct); comment precision (approved-as-drafted / edited / rejected / verdict-correct); flake-saves (candidates rescued by the verdict engine); context.md growth (accepted suggestions over time); and the **automatable-share trend** — the share of incoming tickets whose route was autofix-eligible, the number that should visibly rise as context.md accumulates. That trend is the stakeholder chart.

### Step 4.8.2 — Trajectory field extensions
The per-run trajectory record gains: `triage`, `diagnosis_route`, `verdict` objects, `baseline`, `attempt_ledger`, `divergent` flags, human-question transcripts, and comment-edit distances.

### Step 4.8.3 — Rollout contract — *(User)*
Before any live rollout (plan3 §3.9 Day 1, or immediately if plan3 already ran): meet the scrum master + Megha's lead and agree — the per-route comment templates, the label set, the cadence (≤1 consolidated diagnosis comment per ticket + PR-event comments), the summon convention (@mention handled manually for now; a comment-webhook trigger stays out of scope), and the escalation path for a wrong comment. Record in `docs/rollout_contract.md`. Show the templates *before* the first comment lands — the team shapes them.

### Step 4.8.4 — Full eval re-run
Run `scripts/run_eval.py --label plan4_on` against the same ticket set as the pre-plan4 baseline. Golden 8055 and golden 8278 must be green; overall root-cause accuracy must not regress.

**GATE 4 — HARDENING COMPLETE (print; (User) confirms):**
| Metric | Target | Measured |
|---|---|---|
| Fix-route precision (router, labeled set) | ≥90% (+CI) | ☐ |
| Diagnose-only route + action accuracy | ≥75% | ☐ |
| Correct fixes lost to flakes (8278 fixture) | **0** — hard zero | ☐ |
| 8278 replay green end-to-end via ask_human | yes | ☐ |
| Assertion-weakening edits flagged | 100% | ☐ |
| Ungated Jira posts in gated mode | **0** | ☐ |
| Every attempt judged by verdict engine (no raw exit codes) | yes | ☐ |
| JARVIS-run SHA assert (both edges) active on every cycle | yes | ☐ |
| Clustering demonstrated on a seeded duplicate pair | yes | ☐ |
| context.md seeded (6 sections) + capture loop live | yes | ☐ |
| Eval re-run: goldens green, no accuracy regression | yes | ☐ |
| Rollout contract signed and filed | yes | ☐ |

➡ **After GATE 4: proceed to plan3 (rollout) with the protections in force.** During plan3, `jira_writes.diagnosis` stays `gated`; `auto` is unlocked only after the graduation thresholds are met.

---

## §4.9 — If plan 3 already ran before plan 4 (late-slot costs, stated honestly)
Everything above still applies cleanly; the differences are: the rollout happened without the triage gate, flake-proof verdict, and gated comments (any trust spent is already spent — the contract meeting in 4.8.3 becomes a repair conversation, still worth having); the retry-controller swap (4.2.4) happens against code the team is actively using, so schedule it in a quiet window with the golden regressions as the safety net; and if Phase 4.0 items 2–3 were skipped, the PoC-7 relabeling and the two DAI confirmations must be done now before 4.1.4 and 4.7.2 respectively.

## DELIBERATELY OUT OF SCOPE (unchanged decisions — do not reintroduce)
No vector DB now (revisit only inside UP-11 retrieval once ≥10 real trajectories exist and the lexical scorer measurably misses). No fine-tuning. No tree-sitter SenseTalk grammar (no public grammar exists; English-like syntax is brutal to grammar-ize; regex + vocabulary + the 4.6.3 targeted rule is the correct 80/20 at this repo size). No external tracing stack (the events table + persisted transcripts already are the trace). No @mention/comment-webhook summoning build (manual convention in the rollout contract only). Multi-track expansion unchanged (later playbook).

## EFFORT HONESTY
Roughly 5–8 build days of Agent work, concentrated in Phases 4.1–4.5, plus (User) time for the router-eval review, the DAI confirmations, and the contract meeting. Nothing in plan 4 may be allowed to delay or degrade the already-working read-only diagnosis product — it remains the protected, independently shippable milestone.

➡ **Agent: execute plans 0–2 exactly as written (with the Phase 4.0 carry-alongs), pass GATE 2, then open this file at Phase 4.1. Plans 0–3 are never edited.**
