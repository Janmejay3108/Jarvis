# AI TEST FIX AGENT (ENOVIA) — MASTER PLAN v2 (FOR CLAUDE CODE)

**Audience:** Claude Code (the AI IDE) executing this build, and the User (Jay) performing infrastructure/credential/review tasks.
**Scope:** Build the Enovia-only AI Test Fix Agent end to end — from zero code to a production **chat web application** where a user types a Jira ticket ID (or a natural-language command) into a chat interface and watches the agent diagnose, fix, validate and open a Bitbucket PR, live. Multi-track expansion is out of scope (later playbook).

---

## 0. HOW CLAUDE CODE MUST EXECUTE THIS PLAN SET

1. **Read this master file completely before any plan file.** It is the single source of truth for architecture, repo layout, infra facts, the event contract, and conventions.
2. **Execute plans strictly in order:** `plan0_poc_and_foundation.md` → `plan1_diagnosis_and_chat.md` → `plan2_autofix_and_validation.md` → `plan3_lifecycle_rollout.md`. Within a plan, execute Phases in order; within a Phase, execute Steps in order.
3. **Step protocol.** Every step has: *Owner* (`Claude Code` or `(User)` or `Claude Code + (User)`), *Goal*, *Actions*, *Verification*, *DoD*. Do not begin a step until the previous step's DoD is met. Maintain a running checklist file `PROGRESS.md` at repo root: append `[x] planN/phase/step — <date> — <one-line result>` after each step.
4. **(User) steps:** when a step (or sub-action) is marked **(User)**, STOP and print a clear, numbered request to the user (what to do, where, what output/credential to paste back). Resume only after the user provides the result. Never fabricate credentials, API responses, or PoC results.
5. **Gate discipline:** Gates (0a, 0b, 1, 2, 3) are forced pauses. Print the gate checklist, ask the user to confirm each line with measured values. If a metric misses, do not proceed — diagnose and fix the cause. Every accuracy metric is reported as **point estimate + 95% Wilson confidence interval**.
6. **Testing discipline:** every Python module gets pytest unit tests in `tests/` (mock external services with `pytest-httpx`). Run `ruff check`, `mypy` (lenient), and `pytest` after each phase. The golden regression — TESTAUTOMA-8055 — must keep passing at every later phase.
7. **Environment reality:** the production runtime is Windows VMs. Claude Code may develop and unit-test anywhere, but anything touching `runscript`, the Practice DAI trigger, RDP SUTs, or corporate intranet endpoints is a **(User)** execution step on the VMs. Write code OS-aware (use `pathlib`, config-driven paths, no hardcoded `C:\`).
8. **Never** commit secrets; never write to `Testing_Mar10`; never merge a PR; never bypass a gate.

---

## 1. END STATE (DEFINITION OF THE PRODUCT)

A web app at `http://eggptdai10.cos.is.keysight.com:8080/` (SSO-gated):

- **Chat interface.** The user types `fix TESTAUTOMA-8055`, `diagnose TESTAUTOMA-9123`, or just pastes a ticket ID , uses may or may not provide some additional inputs which may be helpful for solving the tickets . An intent parser maps the message to a pipeline mode.
- **Live progress.** The agent streams its work into the chat as messages and collapsible cards (steps, tool calls, diffs, screenshots, logs) over SSE.
-  The life progress is shown on the screen in a timeline-type UI. Each step comes one after another. After one pointer finishes, another pops out of it as a timeline form UI form, and that starts etc.
- **Human-in-the-loop approval.** Before any Bitbucket write, the agent posts the diff + validation evidence in chat with **Approve & Create PR / Reject** buttons (configurable auto mode later).
- **Lifecycle automation.** On approval: branch `ai-fix/<TICKET>` pushed, PR opened into `Testing_Mar10`, Jira comment + label + screenshot attachments posted, trajectory logged.
- **History & metrics.** Conversation/run history sidebar; a metrics page (pass rates with CIs, PR acceptance, cost, time saved).
- **Safety.** Revert button per merged fix; SUT lock; budget caps; graceful degradation (a failed run always leaves a diagnosis/branch/label behind).

---

## 2. ARCHITECTURE v2 — BASE DESIGN + UPGRADES

### 2.1 Base design (proven; updated per Roadmap)
- **Engine:** **Claude Opus 4.7 for ALL diagnosis and fix-generation calls, from day one** — no Sonnet default, no model escalation ladder. Model ID (`claude-opus-4-7`) and the Anthropic base URL (the Keysight gateway) come from config. "Escalation" on retries = **adding extended thinking**, not switching models. (Originally targeted `claude-opus-4-6`; switched to `4-7` after PoC 2 — `4-6` is not whitelisted on the Keysight gateway while `4-5` and `4-7` are. `4-7` is the newer of the two.)
- **Evidence flow (runid-first, LLM-reasoned at two points):** the Jira ticket **carries the DAI `runid` of the failing execution**, but the runid can live anywhere in the response (description, summary, custom field, comment, attachment name) and appear in any form (`runid`, `run id`, `Run ID`, `RUN ID`, `testrunid=`, …). The agent therefore **uses the LLM to extract** four fields from the Jira response — `runid`, `title`, `description`, comments (for any addtional inputs if present) , `test_script_name` — via a forced-tool-call (structured output). It then calls the **(User)-provided, already-tested DAI APIs** to fetch that run's log. The log typically contains MANY image/text-lookup failures; only one corresponds to the user-reported ticket. The agent therefore **uses the LLM a second time** to pick the single log entry whose `message` is something like error and also semantically matches the ticket's `title`+`description`. From that entry's index, a **deterministic walk-back** finds the most recent prior entry whose `image_id` is non-null (Eggplant captures the screen, *then* attempts the action — so the last captured frame before the failure IS the frame the lookup ran against). That `image_id` feeds the screenshot fetch endpoint. Failing script name from the log corroborates the test-script name extracted from Jira and seeds localization.
- **Grounding:** deterministic — SenseTalk static call-graph + ripgrep blast radius + curated `tracks/enovia/context.md`. **No vector DB.**
- **Validation:** Tier-0 lint, then one of two SUT mechanisms (flag `INNER_LOOP`): **(a) local EPF `runscript` inner loop** on the runner VM (fast, if PoC 1b proves it), and/or **(b) the Practice path** — push the fix to the **Practice Bitbucket repo** `/practice` branch → trigger the **Practice Test Config** on the **Practice DAI server** via its (already-tested) API → wait for completion → fetch the new run's log/screenshot by runid → PASS/FAIL. The **production** Bitbucket repo is touched **only after** PASS + approval (plan3 PR).
- **Evidence:** DAI/runscript screenshots + Jira attachments. No SharePoint/Azure AD.
- **Method:** base-rate study first; Wilson CIs at every gate. **No fine-tuning** — log trajectories.

### 2.2 Upgrades in v2 (integrate everywhere; tagged **[UP-n]** in plan files)

| # | Upgrade | What changes | Why |
|---|---|---|---|
| UP-1 | **Agentic tool-loop diagnosis** | Diagnosis runs as a multi-turn Claude tool-use loop (`read_script`, `get_call_chain`, `find_callers`, `get_dai_log`, `view_screenshot`, `search_context`) with an iteration cap, instead of one stuffed prompt. Single-shot kept as `engine_mode: single_shot` fallback. | Deeper chains, less token waste, vision only when needed; matches how SWE-agents win. |
| UP-2 | **Structured outputs via forced tool call** | Diagnosis/fix JSON is produced through a `submit_diagnosis` / `submit_fix` tool with a JSON schema (`tool_choice` forced), validated by pydantic, one auto-repair retry. | Kills JSON-parsing fragility. |
| UP-3 | **Tier-0 SenseTalk lint** | `src/static/lint.py`: balanced-block check (if/end if, repeat/end repeat, try/catch/end try, to/end), called-handler-exists check vs vocabulary, before any runscript. | A 5–15 min SUT cycle never burned on a syntax error. |
| UP-4 | **Anchor-based patching with disambiguation** | `original_code` must match **exactly once**; if 0 matches, retry with whitespace-normalized matching; if >1, reject and ask the model for a larger anchor. | Patch-apply success is the #1 silent killer in fix agents. |
| UP-5 | **Failure-family router** | Cheap classifier (log-signature rules + small model fallback) tags the family early; per-family few-shot exemplars from `context.md` injected into prompts. | Precision: rectangle bugs and DPI bugs need different exemplars. |
| UP-6 | **Prompt caching** | System prompt + `context.md` + handler vocabulary sent as cached blocks (`cache_control: ephemeral`). | ~90% cost cut on the stable prefix; faster runs. |
| UP-7 | **N-best on retries** | At attempt ≥2: sample 2–3 candidate fixes (temperature varied), dedupe, rank by lint + heuristics, validate best-first. | Big lift on hard tickets at bounded cost. |
| UP-8 | **Persistent state (SQLite)** | `data/agent.db`: conversations, messages, runs, steps, events, approvals. Runs are resumable; chat history survives restarts; metrics read one store. | In-memory runs lose work on crash; the chat product needs history. |
| UP-9 | **Chat-first UI + HITL approval** | The dashboard becomes a chat app; `approval.requested` event pauses the pipeline until POST approve/reject. `approval_mode: manual|auto`. | The product requirement; safer rollout; builds trust. |
| UP-10 | **Repeatable eval harness** | `src/evals/` + `scripts/run_eval.py`: frozen labeled ticket set re-runnable after any prompt/`context.md` change; per-category report + Wilson CIs. | Prompt changes regress silently without this. |
| UP-11 | **Trajectory few-shot retrieval (lexical)** | `src/flywheel/retrieval.py`: top-k similar solved trajectories by category + handler overlap + keyword score (no embeddings), injected as exemplars. Empty-corpus tolerant; wired from day one. | The flywheel pays immediately; bridge to NL-generation. |
| UP-12 | **Handler vocabulary + gold scripts** | `scripts/build_vocabulary.py` → `tracks/enovia/handler_vocabulary.json` (every handler: name, file, signature, params, 1-line purpose); `tracks/enovia/gold_scripts/` exemplar registry. | Powers lint (UP-3), grounds diagnosis, and is the vocabulary for future NL-to-script generation. |
| UP-13 | **Budget guard + cost telemetry** | Per-run hard cap (`budget_usd_per_run`, default **10.0** — Opus-only economics), per-step token/cost on every event; surfaced in chat + metrics. | Cost honesty, runaway protection. |
| UP-14 | **Injection hardening+** | Beyond delimiters: strip markdown images/links from ticket text, length-cap ticket/log inserts, treat DAI log text as data too. | Logs can contain attacker-ish strings as easily as tickets. |
| UP-15 | **Extended thinking on retry** | Attempt ≥2 diagnosis/fix calls enable extended thinking on the **same Opus 4.7 model** (config `thinking_on_escalation: true`). No model switch — Opus is already the only reasoning model. | Hard multi-handler bugs benefit from longer reasoning. |

---

## 3. CONFIRMED ENOVIA INFRASTRUCTURE (single source of truth)

| Thing | Value |
|---|---|
| Bitbucket repo | `bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git` |
| Project key / slug | `EGGAUTO` / `enovia-plm-test-automation` |
| Default/working branch | `Testing_Mar10` |
| DAI git connection name | `Enovia PLM` |
| Orchestrator VM | `aiagent-testmanager.cos.is.keysight.com` (156.140.21.109) — 4 CPU / 32 GB |
| EPF validation runner VM | `eggptdai10.cos.is.keysight.com` (156.140.21.30) — 4 CPU / 16 GB |
| Agent-VM suite cache | `C:\ProgramData\Eggplant\Agent\suites\{Env}\.run\enovia-plm-test-automation\Enovia\` |
| DAI Environments | `EnoviaExecEnv_92_1/2/3` |
| SUT connection type | **RDP** (one test at a time; one dedicated EPF floating license) |
| Jira project | `TESTAUTOMA` (Data Center → REST v2; confirm in PoC 5) |
| Jira base URL | **(User) provides the exact base URL** where tickets live → `.env JIRA_BASE_URL` |
| DAI runid source | The Jira ticket carries the failing run's `runid` somewhere in the response, in any form/casing. **The agent uses the LLM (forced tool-call) to extract `runid` + `title` + `description` + `test_script_name`** from the issue JSON — see PoC 5 (A.8). A deterministic regex/custom-field rule may be kept as a sanity check but is not the primary path. |
| DAI log-by-runid API | **(User)-provided, PoC-2-proven.** `GET {DAI_BASE_URL}/ai/runlogs/{runid}` with `Authorization: Bearer <token>` (token via OAuth2 `client_credentials` against `{DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token`). Response shape: `{"items": [LogEntry…], "total_count": N, "date_as_of": "ISO8601"}`. `LogEntry` keys: `id, eventtime, testrunid, message, severity, step_id, stage, message_type, image_name, image_id`. |
| Error-entry identification | **LLM step (`claude-opus-4-7`).** Given the ordered `items[]` and the ticket's `title`+`description`, the LLM picks the SINGLE entry whose `message` matches the user-reported failure (e.g. ticket says *"release was not able to identify"* → log entry `"Unable to Find Image (TEXT:\"Released\"). Text not found."`). Severity alone is not a reliable filter — real failures often have `severity: INFORMATIONAL` and `message_type: imagefound`. |
| Error-screenshot fetch | **Deterministic walk-back** from the matched-entry index toward 0; return the first entry whose `image_id` is non-null/non-empty. Then `GET {DAI_BASE_URL}/api/v2/screenshots/{image_id}` with the same bearer token → PNG bytes. |
| Practice Bitbucket repo | **(User) provides URL** — separate repo whose `/practice` branch feeds validation runs |
| Practice branch | `/practice` (the Practice Test Config's git connection is pre-wired to it) |
| Practice DAI server | **(User) provides URL + API access** — hosts the Practice Test Config, pre-connected to a SUT |
| Practice Test Config | **(User) provides config ID + the already-tested trigger API** (+ status/poll API) |
| Suites (17+) | 3DDashboard, BoundaryApps, Common, CustomReport, EngineeringCentral, EnoviaCommon, LibraryCentral, M&AFoundational, MACS, MaterialsComplianceCentral, MSFIntegration, PartMaster, Performance, PLMBridge, Search, SupplierCentral, TeamCenter |
| Golden regression | **TESTAUTOMA-8055** — `EngineeringCentral.suite` test; bug at `CommonEnovia.script:409`, the `and not ImageFound(text:"Name",…)` clause |

**Handler-chain reality:** `test → suite handler (e.g. addHeaderOnly) → searchEnovia (CommonEnovia.script) → sub-handlers`. Failure families: `boolean_logic_gap, silent_exception_swallowing, search_rectangle, dpi_cascade, text_label, missing_wait, image_staleness (rare), handler_name_mismatch, config_value_stale, environment_issue, application_bug, test_data`.

---

## 4. CANONICAL REPO LAYOUT v2 (built in plan0 §B.1)

```
ai-test-fix-agent/
├── pyproject.toml  .env.example  README.md  PROGRESS.md
├── config/enovia.yaml                  # track config (repo, suites, DAI ids, models, modes, budgets)
├── src/
│   ├── main.py  config.py
│   ├── api/        routes_chat.py routes_runs.py routes_sse.py routes_metrics.py
│   │               routes_webhooks.py auth_sso.py
│   ├── chat/       intent.py conversation_store.py
│   ├── orchestrator/ pipeline.py validation_loop.py practice_gate.py lifecycle.py publisher.py
│   │               revert.py state_store.py queue.py locks.py track_loader.py events.py
│   ├── agentic/    tool_loop.py tools.py schemas.py            # UP-1, UP-2
│   ├── integrations/ jira_client.py bitbucket_client.py dai_client.py
│   │               practice_dai.py epf_runner.py claude_client.py
│   ├── analysis/   diagnosis.py fix_generator.py family_router.py context_packer.py
│   │               prompts/ (diagnosis_system.md diagnosis_user.md fix_system.md fix_user.md
│   │                         family_exemplars/*.md)
│   ├── static/     sensetalk_parser.py call_graph.py ripgrep_search.py handler_map.py
│   │               vocabulary.py lint.py                        # UP-3, UP-12
│   ├── evidence/   packager.py
│   ├── flywheel/   trajectory_logger.py retrieval.py            # UP-11
│   ├── evals/      runner.py scoring.py wilson.py               # UP-10
│   ├── models/     run.py ticket.py diagnosis.py fix.py events.py trajectory.py
│   └── utils/      logging_config.py budget.py textguard.py     # UP-13, UP-14
├── webapp/                              # React + Vite + Tailwind chat app
│   └── src/ (App.tsx components/ hooks/ api/)
├── scripts/
│   ├── poc_dai.py poc_practice.py poc_bitbucket.py poc_jira.py poc_claude.py poc_static.py poc_runscript.ps1
│   ├── categorize_tickets.py setup_vm_orchestrator.ps1 setup_vm_runner.ps1 clone_repo.ps1
│   ├── build_handler_map.py build_vocabulary.py run_validation.py run_eval.py
│   ├── test_integrations.py verify_context.py
├── tracks/enovia/
│   ├── context.md handler_map.yaml handler_vocabulary.json prompt_overrides.md
│   ├── validation_tickets.json ticket_base_rate.json poc_results.md
│   └── gold_scripts/                    # UP-12 exemplar tests
├── data/                                # gitignored
│   ├── working_copy/ agent_runs/{run_id}/ trajectories/enovia.jsonl agent.db
└── tests/
```

### 4.1 Where the fix physically happens (no online IDE / sandbox service needed)
The orchestrator VM **is** the workspace. A **local git clone of the Enovia test repo** lives at `settings.working_copy_path` with **two remotes**: `origin` = the production repo (pull `Testing_Mar10` hourly; push only `ai-fix/<TICKET>` at plan3 PR time) and `practice` = the Practice repo (push target for validation). All reading/analysis (parser, ripgrep, Claude's `read_script`/`grep_repo` tools) and all writing (the fix applier's exact text replacement) happen on this clone's files, isolated on a local branch `wc/<TICKET>`. Git is the sandbox: the branch isolates the change, `git diff` is the reviewable patch (streamed to the chat as a diff artifact, so the user sees exactly what changed and where), `git reset --hard` restores a pristine tree between attempts. The fix exists remotely only twice: on `practice/practice` during validation, and on `origin ai-fix/<TICKET>` after approval. The trajectory log + transcript keep the permanent record after `wc/` cleanup.

---

## 5. CHAT & EVENT CONTRACT (binding for backend AND frontend)

### 5.1 HTTP API (all SSO-gated)
```
POST /api/chat/messages        {conversation_id?, text}
                               → {conversation_id, message_id, run_id?|reply}
GET  /api/conversations        → list (id, title, updated_at)
GET  /api/conversations/{id}   → full message + run-card history
GET  /api/runs/{run_id}/stream → SSE event stream (live or replay-from-db then live)
POST /api/runs/{run_id}/approval {decision: "approve"|"reject", comment?}
POST /api/runs/{run_id}/cancel
GET  /api/metrics              → metrics JSON
POST /api/webhooks/bitbucket   → PR-merge webhook (plan3)
```

### 5.2 SSE event envelope (every event; persisted to `events` table)
```json
{"event_id": "...", "run_id": "...", "ts": "ISO8601", "type": "<type>",
 "payload": { ... }, "cost_usd_so_far": 0.42}
```
**Types:** `run.queued` · `step.started` · `step.progress` · `step.completed` · `step.failed`
· `agent.message` (NL narration for a chat bubble) · `tool.called` / `tool.result` (collapsible card)
· `artifact` (payload.kind: `diagnosis|diff|screenshot|log_excerpt|evidence|pr`)
· `approval.requested` (payload: diff, evidence, expires) · `approval.resolved`
· `run.completed` / `run.failed` (summary, totals).

### 5.3 Intent grammar (chat → pipeline)
Regex first: `(?i)\b(TESTAUTOMA-\d+)\b` + mode keywords (`diagnose`, `fix`, `status`, `revert`, `metrics`, `help`) + optional `runid[=: ]?(\d+)` override token. Bare ticket ID → ask "diagnose or fix?" with quick-reply buttons. Anything else → one light model call (or Opus with small `max_tokens`, per the single-model policy) maps to `{action, ticket?, runid?}` or a plain conversational reply. Unknown → helpful usage message.

---

## 6. GLOBAL CONVENTIONS (apply to every step)

1. **Step template:** Owner → Goal → Actions → Verification → DoD. DoD gates the next step.
2. **Secrets:** never in repo. `.env` per VM via `pydantic-settings`. `.gitignore` covers `.env`, `data/`, `*.log`, `node_modules/`, `webapp/dist/`.
3. **Logging:** `structlog` JSON from line one; every external call logs latency + status; every log line carries `run_id`.
4. **Safety invariants (enforced in code):** never merge; never write `Testing_Mar10`; **validation pushes go ONLY to the Practice repo's `/practice` branch**; the production repo is written only as `ai-fix/<TICKET>` after PASS + approval; production writes require SSO session; SUT serialized via per-track lock; budget cap aborts gracefully (UP-13).
5. **Untrusted input (UP-14):** ticket text AND DAI logs are data, not instructions — delimit, strip active markdown, length-cap; instruct the model accordingly.
6. **Cost honesty:** track tokens/cost per call; with Opus 4.7 + prompt caching expect **$2–6/ticket**; report it.
7. **One reasoning model:** `llm.model = claude-opus-4-7` for every diagnosis/fix/agentic call — no quality compromise, no escalation ladder. (The originally planned `claude-opus-4-6` is not whitelisted on the Keysight AI gateway; a request for 4-6 returns a misleading `401 invalid x-api-key` because the gateway forwards the model name and Anthropic upstream rejects it. The whitelisted Opus IDs proven in PoC 2 are `claude-opus-4-5` and `claude-opus-4-7`; we use 4-7 as the newer of the two. If/when Keysight whitelists 4-8 or later, bump this convention.) `llm.model_light` is **optional** and used ONLY for non-reasoning utility calls (chat-intent fallback, one-time vocabulary purpose lines); if the user prefers strict single-model, set it to the same Opus ID or rely on the regex layer alone. `llm.anthropic_base_url` supports the direct API **or** the Keysight gateway (e.g. the Azure APIM Anthropic endpoint) — both model ID and base URL live in `.env`.
10. **`.env` overrides parent shell:** every script (PoC and prod) loads dotenv with `load_dotenv(override=True)` so the project's `.env` wins over any parent-process env vars. Without this, a developer running scripts from a shell that already has `ANTHROPIC_BASE_URL` set (e.g. an IDE / Claude Code session) will silently hit the wrong API base. Discovered the hard way during PoC 2.
8. **Concurrency truth:** one SUT, one test at a time (`max-parallel: 1`); one dedicated EPF license; one dedicated RDP SUT.
9. **Prompt caching (UP-6):** stable prefix (system + context.md + vocabulary) marked cacheable on every Claude call.
11. **No LLM in wait paths:** any long-running external wait (Practice DAI run: 20 min–2 hr; local runscript license wait; any future SUT job) is waited on by plain orchestrator code — an `asyncio.Event` resolved by a webhook, an awaited subprocess, or an `asyncio.sleep` poll loop — never by the LLM/agentic tool-loop (UP-1) calling a "check status" tool repeatedly. Claude touches a validation gate only at its two edges: generating the candidate before triggering, and interpreting PASS/FAIL/logs after it resolves. See plan2 Phase 2.5 for the concrete `PRACTICE_COMPLETION_MODE` design (webhook preferred, `eggplant-runner` CLI or backoff-polling as fallbacks).

---

## 7. GATE SUMMARY

| Gate | After | Bar |
|---|---|---|
| **0a** | Week-0 PoCs | PoC 7 (base rate) must pass, **and at least one validation mechanism** (PoC 1/1b local runscript **or** PoC 2b Practice path) must be proven, or STOP & re-architect that part |
| **0b** | Foundation | Integration smoke test all-green from the orchestrator VM |
| **1** | Diagnosis | Root-cause match ≥75% on ≥50 tickets (+95% CI); 0 crashes; chat MVP usable |
| **2** | Auto-fix | First-attempt ≥60%, final(≤3) ≥80%, equivalence ≥75%, 0 regressions (+CIs) |
| **3** | Rollout | ≥50% triggered tickets → merged PR ≤24h; PR-accept ≥75%; 0 post-merge regressions |

## 8. DEFINITION OF DONE (WHOLE PROJECT)
A developer opens the SSO chat app, types `fix TESTAUTOMA-XXXX`, watches the agent extract the runid → fetch the DAI error log + screenshot → localize → diagnose → patch → lint → validate (local runscript inner loop and/or the Practice-DAI gate) → request approval → push `ai-fix/<TICKET>` + open PR + update Jira with evidence — all live in chat — with one-click revert available, every trajectory logged, and Gate 3 metrics met with CIs and zero post-merge regressions.

➡ **Claude Code: open `plan0_poc_and_foundation.md` and begin at Phase 0.A, Step A.0.**
