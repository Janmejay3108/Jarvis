# JARVIS (ENOVIA) — MASTER PLAN v2 (FOR THE AGENT)

**Audience:** the Agent (the AI IDE) executing this build, and the User (Jay) performing infrastructure/credential/review tasks.
**Scope:** Build the Enovia-only **JARVIS (Automation Testing Agent)** end to end — from zero code to a production **chat web application** where a user types a Jira ticket ID (or a natural-language command) into a chat interface and watches JARVIS diagnose, fix, validate and open a Bitbucket PR, live. Multi-track expansion is out of scope (later playbook).

---

## 0. HOW THE AGENT MUST EXECUTE THIS PLAN SET

1. **Read this master file completely before any plan file.** It is the single source of truth for architecture, repo layout, infra facts, the event contract, and conventions.
2. **Execute plans strictly in order:** `plan0_poc_and_foundation.md` → `plan1_diagnosis_and_chat.md` → `plan2_autofix_and_validation.md` → `plan3_lifecycle_rollout.md`. Within a plan, execute Phases in order; within a Phase, execute Steps in order.
3. **Step protocol.** Every step has: *Owner* (`Agent` or `(User)` or `Agent + (User)`), *Goal*, *Actions*, *Verification*, *DoD*. Do not begin a step until the previous step's DoD is met. Maintain a running checklist file `PROGRESS.md` at repo root: append `[x] planN/phase/step — <date> — <one-line result>` after each step.
4. **(User) steps:** when a step (or sub-action) is marked **(User)**, STOP and print a clear, numbered request to the user (what to do, where, what output/credential to paste back). Resume only after the user provides the result. Never fabricate credentials, API responses, or PoC results.
5. **Gate discipline:** Gates (0a, 0b, 1, 2, 3) are forced pauses. Print the gate checklist, ask the user to confirm each line with measured values. If a metric misses, do not proceed — diagnose and fix the cause. Every accuracy metric is reported as **point estimate + 95% Wilson confidence interval**.
6. **Testing discipline:** every Python module gets pytest unit tests in `tests/` (mock external services with `pytest-httpx`). Run `ruff check`, `mypy` (lenient), and `pytest` after each phase. The golden regression — TESTAUTOMA-8055 — must keep passing at every later phase.
7. **Environment reality:** the production runtime is Windows VMs. The Agent may develop and unit-test anywhere, but anything touching `runscript`, RDP SUTs, or corporate intranet endpoints is a **(User)** execution step on the VMs. **Additionally: anything touching the JARVIS DAI, its Design/Run agents, or a push to the validation repo is a (User) execution step on the VMs** — those live on the Jay-administered JARVIS VM, not on a developer laptop. Write code OS-aware (use `pathlib`, config-driven paths, no hardcoded `C:\`).
8. **Never** commit secrets; never write to `Testing_Mar10`; never merge a PR; never bypass a gate.

---

## 1. END STATE (DEFINITION OF THE PRODUCT)

A web app at `http://eggptdai10.cos.is.keysight.com:8080/` (SSO-gated) — **JARVIS is deployed on `eggptdai10`, co-located with the JARVIS DAI** (§3). Co-location is deliberate: the DAI, the Design and Run agents, EPF, `C:\Eggplant_Suites` and the Enovia working copy all live on that VM, so co-locating the orchestrator shortens every hop that matters. **Port 8080 is the target and must be confirmed free at deploy time** — the JARVIS DAI holds **8000** on the same host.

- **Chat interface.** The user types `fix TESTAUTOMA-8055`, `diagnose TESTAUTOMA-9123`, or just pastes a ticket ID , uses may or may not provide some additional inputs which may be helpful for solving the tickets . An intent parser maps the message to a pipeline mode.
- **Live progress.** The agent streams its work into the chat as messages and collapsible cards (steps, tool calls, diffs, screenshots, logs) over SSE.
-  The life progress is shown on the screen in a timeline-type UI. Each step comes one after another. After one pointer finishes, another pops out of it as a timeline form UI form, and that starts etc.
- **Human-in-the-loop approval.** Before any **production** Bitbucket write, JARVIS posts the diff + validation evidence in chat with **Approve & Create PR / Reject** buttons (configurable auto mode later).
- **Lifecycle automation — two repos, one direction.** Validation runs on the **JARVIS DAI** against the **validation repo** (`agentic-eggplant-automation`, branch `Enovia`), which is force-pushed with the candidate state on every validation cycle. Only on **PASS + approval** does the fix reach the **production** Enovia repo (`enovia-plm-test-automation`): branch `Jarvis-fix/<TICKET>` is pushed to `origin` and a PR is opened into `Testing_Mar10`, with Jira comment + label + screenshot attachments posted and the trajectory logged. The production repo is never written during validation; the validation repo is never the PR target.
- **History & metrics.** Conversation/run history sidebar; a metrics page (pass rates with CIs, PR acceptance, cost, time saved).
- **Safety.** Revert button per merged fix; SUT lock; budget caps; graceful degradation (a failed run always leaves a diagnosis/branch/label behind).

---

## 2. ARCHITECTURE v2 — BASE DESIGN + UPGRADES

### 2.1 Base design (proven; updated per Roadmap)
- **Engine:** **Claude Opus 4.7 for ALL diagnosis and fix-generation calls, from day one** — no Sonnet default, no model escalation ladder. Model ID (`claude-opus-4-7`) and the Anthropic base URL (the Keysight gateway) come from config. "Escalation" on retries = **adding extended thinking**, not switching models. (Originally targeted `claude-opus-4-6`; switched to `4-7` after PoC 2 — `4-6` is not whitelisted on the Keysight gateway while `4-5` and `4-7` are. `4-7` is the newer of the two.)
- **Evidence flow (runid-first, LLM-reasoned at two points):** the Jira ticket **carries the DAI `runid` of the failing execution**, but the runid can live anywhere in the response (description, summary, custom field, comment, attachment name) and appear in any form (`runid`, `run id`, `Run ID`, `RUN ID`, `testrunid=`, …). The agent therefore **uses the LLM to extract** four fields from the Jira response — `runid`, `title`, `description`, comments (for any addtional inputs if present) , `test_script_name` — via a forced-tool-call (structured output). It then calls the **(User)-provided, already-tested DAI APIs** to fetch that run's log. The log typically contains MANY image/text-lookup failures; only one corresponds to the user-reported ticket. The agent therefore **uses the LLM a second time** to pick the single log entry whose `message` is something like error and also semantically matches the ticket's `title`+`description`. From that entry's index, a **deterministic walk-back** finds the most recent prior entry whose `image_id` is non-null (Eggplant captures the screen, *then* attempts the action — so the last captured frame before the failure IS the frame the lookup ran against). That `image_id` feeds the screenshot fetch endpoint. Failing script name from the log corroborates the test-script name extracted from Jira and seeds localization. **This entire runid-first evidence chain reads the *production* DAI (`epcorpappsdai12`, DAI 25.3.1+0) — the evidence source. It is a different instance from the *JARVIS* DAI (26.2.2) that executes validation runs (§2.3), and the two use different auth schemes: production is OAuth2 client-credentials against the Keycloak realm, JARVIS is `POST /api/v2/auth` → a ~10-minute bearer token. Never conflate the two.**
- **Grounding:** deterministic — SenseTalk static call-graph + ripgrep blast radius + curated `tracks/enovia/context.md`. **No vector DB.**
- **Validation:** Tier-0 lint, then **the JARVIS validation gate** — the single mandated SUT mechanism, proven end-to-end on real infrastructure. Push the candidate to the **validation repo** `agentic-eggplant-automation` branch `Enovia` → assert the pushed SHA → trigger that suite's **JARVIS test config** by ID on the **JARVIS DAI** → wait for completion → fetch the run's results/log/screenshots → assert the executed commit SHA → PASS/FAIL. The full canonical flow, including the dispatcher pattern that makes it possible, is **§2.3**. The **production** Bitbucket repo is touched **only after** PASS + approval (plan3 PR). *A local EPF `runscript` inner loop remains a possible future latency optimisation; it is out of scope for this version and is not required by any gate. It will be checked or added later in JARVIS as an update or enhancement (see `docs/later-enhancements.md`).*
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
| UP-8 | **Persistent state (SQLite)** | `data/agent.db`: conversations, messages, runs, steps, events, approvals, `jira_actions` (a plan1 Step 1.1.2 migration on the plan0 §B.6 store, not a new store). Runs are resumable; chat history survives restarts; metrics read one store. | In-memory runs lose work on crash; the chat product needs history. |
| UP-9 | **Chat-first UI + HITL approval** | The dashboard becomes a chat app; `approval.requested` event pauses the pipeline until POST approve/reject. `approval_mode: manual|auto`. | The product requirement; safer rollout; builds trust. |
| UP-10 | **Repeatable eval harness** | `src/evals/` + `scripts/run_eval.py`: frozen labeled ticket set re-runnable after any prompt/`context.md` change; per-category report + Wilson CIs. | Prompt changes regress silently without this. |
| UP-11 | **Trajectory few-shot retrieval (lexical)** | `src/flywheel/retrieval.py`: top-k similar solved trajectories by category + handler overlap + keyword score (no embeddings), injected as exemplars. Empty-corpus tolerant; wired from day one. | The flywheel pays immediately; bridge to NL-generation. |
| UP-12 | **Handler vocabulary + gold scripts** | `scripts/build_vocabulary.py` → `tracks/enovia/handler_vocabulary.json` (every handler: name, file, signature, params, 1-line purpose); `tracks/enovia/gold_scripts/` exemplar registry. | Powers lint (UP-3), grounds diagnosis, and is the vocabulary for future NL-to-script generation. |
| UP-13 | **Budget guard + cost telemetry** | Per-run hard cap (`budget_usd_per_run`, default **10.0** — Opus-only economics), per-step token/cost on every event; surfaced in chat + metrics. | Cost honesty, runaway protection. |
| UP-14 | **Evidence framing + instruction separation** | Jira and production DAI have **reliable provenance**, but their content is **semantically fallible** — corroborate ticket/comments, DAI logs, screenshots and current source rather than trusting any one item. Content is **evidence, never model instructions**. Controls: delimit ticket AND DAI log inserts, neutralize active markdown/known HTML, length-cap, instruct the model accordingly, and keep the adversarial fixture. Embedded delimiter tokens are neutralized **after entity decoding**; unknown/domain angle-bracket evidence (e.g. `<Suite>`) is preserved. | Logs carry instruction-like strings as easily as tickets, and the Step 1.1.2 review proved both boundary forgery and evidence loss. |
| UP-15 | **Extended thinking on retry** | Attempt ≥2 diagnosis/fix calls enable extended thinking on the **same Opus 4.7 model** (config `thinking_on_escalation: true`). No model switch — Opus is already the only reasoning model. | Hard multi-handler bugs benefit from longer reasoning. |

---

### 2.3 THE VALIDATION FLOW (canonical)

> This section is the authoritative description of how a candidate fix is validated. Plan0 A.2/A.2b
> prove it, plan2 §2.5 builds it, plan4 §4.7.2 hardens it. Everything here is **proven on real
> infrastructure** unless carried as an open item (O1–O7).

#### 2.3.1 Platform constraints discovered (these are *why* the design is what it is)

- **C1.** DAI public API **v2 has no test-config or step create/edit endpoints.** A test config's steps
  cannot be rewritten per ticket via API. **This is the constraint that forced the dispatcher (D1).**
- **C2.** Suite names must be **globally unique across a DAI instance.**
- **C3.** A DAI **git connection binds one repository to exactly one branch**; the same repository
  **cannot be connected on two branches within one DAI instance.** *This is why validation force-pushes
  a single permanent branch (`Enovia`) rather than a branch per ticket* — a per-ticket branch would need
  a per-ticket git connection, which the instance cannot hold. Together with **C1**, C3 is the reason
  the whole design is "static config + dispatcher + one disposable branch".
- **C4.** Model exports restore internal structure but **not** suite links or test configs — those are
  re-authored after import.

#### 2.3.2 Ratified architecture decisions (D1–D5)

- **D1 — Dispatcher pattern.** Because of C1, the test config stays **permanently static**; only *file
  content* changes, and it changes **via git**. Each suite gets one permanent test config whose single
  test case wraps a dispatcher action. Per validation cycle, only the dispatcher script's target line
  changes.
- **D2 — Model-per-suite topology.** Each suite's model is exported from the production DAI and
  imported into the JARVIS DAI. One-time authoring per suite (**done by the User: Jay**): create model
  action `AgentDispatcher` → attach snippet `<Suite>_AgentDispatcher.script` → create test case
  (`cleanupSUT` + `AgentDispatcher`) → create a **model-based** test config (SUT **by name**, **reruns
  OFF**, generous run timeout). Authoring is done against the Design agent's local suites folder
  (`C:\Eggplant_Suites`). **Every one-time DAI setup of this kind is a (User) task, never an Agent task.**
- **D3 — Test-config registry.** The mapping *suite → `test_config_id`* is recorded once per suite in a
  versioned registry file (`tracks/enovia/test_config_registry.yaml`) and looked up at runtime. There is
  **no single `PRACTICE_TEST_CONFIG_ID` env var any more** — that scalar is replaced by this registry.
  The per-suite mapping (*which test config to trigger for a script change in which suite*) is
  **provided by the User (Jay)** and stored in this registry.
- **D4 — Dispatcher as generated artifact.** `<Suite>_AgentDispatcher.script` is **generated by JARVIS
  from a template on every validation cycle**. It **never exists in the production repo** and must
  **never** appear in a `Jarvis-fix/<TICKET>` branch or PR. Every validation push carries freshly
  generated dispatchers.
  **Regeneration rule (settled — this is a rule, not a recommendation).** Every registered suite has
  its **own** `<Suite>_AgentDispatcher.script` **and its own test config**, which executes that suite's
  dispatcher. On **every** validation push, JARVIS regenerates the dispatcher for **every suite in the
  D3 registry**, so the `Enovia` branch is **always complete**. This is what makes the force-push safe:
  the push replaces the branch contents wholesale, so any dispatcher not regenerated would simply
  vanish. Consequence: a registered suite with no `smoke_target` is a **hard error at onboarding time**,
  never a silent failure at validation time — the non-target suites still need a valid target line.
- **D5 — Target reference form.** The dispatcher's target is written using the proven SenseTalk path
  rules in §2.3.6 (S1/S2).

#### 2.3.3 The dispatcher artifact

Template location: `src/analysis/templates/agent_dispatcher.st.j2`.

This is the **proven** form — the script whose log lines exist in a real JARVIS run log. It is
authoritative over any earlier draft:

```
-- {{suite}}_AgentDispatcher.script
-- JARVIS — dispatcher for {{suite}}.suite (GENERATED — do not hand-edit)
-- Contract: only the targetScript line below is rewritten per validation cycle.
-- Value = path relative to Scripts/, forward slashes, no .script extension.
-- No try/catch — a target failure MUST fail this run.
set targetScript to "{{target_rel_path}}"
log "AgentDispatcher: start — target=" & targetScript
run targetScript
log "AgentDispatcher: done — target=" & targetScript
```

Three details are load-bearing:

1. **The log lines carry the `AgentDispatcher:` prefix.** A.2b's verification and the gate's log parsing
   both key off these markers. **Assert on the `AgentDispatcher:` prefix only, never on the full line** —
   the em dash is non-ASCII, and log encoding must not be able to break a verdict.
2. **The `Value = path relative to Scripts/…` comment stays.** It states rule **S1** at the point of use,
   where an implementer will actually read it.
3. **The header says JARVIS.** Any live copy predating the rename shows the old project name; the
   generator emits the corrected header from now on.

The absence of `try/catch` is **deliberate and load-bearing**: a swallowed target failure would produce
a false PASS, which is the worst possible failure mode for this system.

#### 2.3.4 The canonical flow

```
FixValidationLoop produces a candidate on local branch wc/<TICKET>
  → validation_suite_of(run) → the suite that OWNS THE FAILING TEST
        (failing test named in the DAI log → JIRA number→suite range → raise)
        NEVER inferred from the affected file path — most fixes land in a shared handler
  → look up test_config_id for that suite (D3 registry)
  → render <Suite>_AgentDispatcher.script from the template with the target (D4/D5) → commit
  → git push agentic-eggplant-automation wc/<TICKET>:refs/heads/Enovia --force   (UNDER THE TRACK LOCK)
  → ASSERT  git ls-remote agentic-eggplant-automation refs/heads/Enovia == pushed SHA
                                                                  (UP-24 pre-check, mandatory)
  → POST /task_scheduler_service/api/v1/task_instances/{test_config_id}  → 201 + task_instance_id
  → wait per JARVIS_COMPLETION_MODE (poll_backoff day 1 → webhook once registered)
        NO LLM IN THE WAIT PATH — plain orchestrator coroutine only
  → fetch results:
        GET /api/v2/test_config_results?test_config_id=<ID>      → newest result id
        GET /api/v2/test_results?test_config_result_id=<id>      → step result + status
        GET /api/v2/test_results/{test_result_id}/logs?limit=1000 → entries (message, severity,
                                                                    message_type, image_id)
        GET /api/v2/test_results/{run_id}/screenshots            → screenshot list for the run
        GET /api/v2/screenshots/{screenshot_id}                  → PNG (walk-back logic reused)
  → ASSERT  run log "Using Git commit SHA: '<sha>'" == pushed SHA (UP-24 post-check)
  → status PASSED | FAILED | ERROR | CANCELLED
  → verdict + evidence returned to the retry controller
  → release the track lock
```

Force-push is safe **because** the branch is disposable and the lock serialises writers.

#### 2.3.5 API surface and auth (JARVIS DAI)

- **Auth:** `POST /api/v2/auth` with `client_id` / `client_secret` from JARVIS **API Access** → bearer
  token, **~10-minute expiry** → cache in-process and refresh on expiry.
- **Results/evidence chain:** the **five** `GET` calls listed in §2.3.4 — config results → step
  status → logs → **screenshot list for the run** → PNG. Fetching a PNG requires the
  `/test_results/{run_id}/screenshots` listing first; `image_id` from a log entry is the
  **production** DAI's path, not this one. **`GET /testconfiguration/{id}/results`
  404s on this DAI** — use `/api/v2/test_config_results?test_config_id=…` instead.
- **Trigger:** `POST /task_scheduler_service/api/v1/task_instances/{test_config_id}` → **201** with a
  `task_instance_id`. A single transient **500** was observed and the identical retry returned 201;
  do not treat one 500 as a contract error.
- All JARVIS DAI endpoints in §2.3.4/§2.3.5 were **proven live 2026-08-02** during plan0 B.7a.
- **Dual-auth warning.** The **production** DAI evidence endpoints in §3 (`/ai/runlogs/{runid}`,
  `/api/v2/screenshots/{image_id}`, OAuth2 client-credentials against the Keycloak realm) are
  **unchanged** and belong to the **production** DAI, not the JARVIS DAI. The two instances use
  **different auth schemes**. Do not share a client, a token cache, or a base URL between them.

#### 2.3.6 Proven SenseTalk rules (two bugs, both resolved)

- **S1.** Scripts living in `Scripts/TestCases/` must be referenced as `TestCases/<name>` — **no
  `.script` extension** and **no `Scripts/` prefix**. EPF does not auto-search subfolders.
- **S2.** Dynamic invocation is plain `run targetScript`. Dot-notation `targetScript.run()` does
  **not** work.

Both rules constrain the dispatcher template and the target-path derivation logic (see §6.12).

---

## 3. CONFIRMED ENOVIA INFRASTRUCTURE (single source of truth)

| Thing | Value |
|---|---|
| Bitbucket repo | `bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git` |
| Project key / slug | `EGGAUTO` / `enovia-plm-test-automation` |
| Default/working branch | `Testing_Mar10` |
| DAI git connection name | `Enovia PLM` |
| **The JARVIS VM (one machine, all roles)** | **`eggptdai10.cos.is.keysight.com` (156.140.21.30)** — 4 CPU / 16 GB. Hosts, together: **JARVIS DAI 26.2.2** at `https://eggptdai10.cos.is.keysight.com:8000/` · the **co-located Design + Run agents** (`Test26_2_Design` + a Run environment) · **EPF 26.2.x** · **`C:\Eggplant_Suites`** (git clone of the validation repo) · the **Enovia working copy** · and the **JARVIS orchestrator + chat app at `:8080`**. The former *"EPF validation runner"* role is **deferred with the local `runscript` inner loop** (§2.1) — the role is deferred, the **machine is not obsolete**. SUTs stay on their own VMs and are connected at execution time. |
| Orchestrator VM (superseded) | `aiagent-testmanager.cos.is.keysight.com` (156.140.21.109) — 4 CPU / 32 GB. **Previously designated orchestrator host; superseded by the `eggptdai10` co-location decision above. Retained** — the hostname belongs to a real, separate org-level initiative and is protected under R1. |
| Agent-VM suite cache | `C:\ProgramData\Eggplant\Agent\suites\{Env}\.run\enovia-plm-test-automation\Enovia\` |
| DAI Environments | `EnoviaExecEnv_92_1/2/3` |
| SUT connection type | **RDP** (one test at a time; one dedicated EPF floating license) |
| Jira project | `TESTAUTOMA` (Data Center → REST v2; confirm in PoC 5) |
| Jira base URL | **(User) provides the exact base URL** where tickets live → `.env JIRA_BASE_URL` |
| DAI runid source | The Jira ticket carries the failing run's `runid` somewhere in the response, in any form/casing. **The agent uses the LLM (forced tool-call) to extract `runid` + `title` + `description` + `test_script_name`** from the issue JSON — see PoC 5 (A.8). A deterministic regex/custom-field rule may be kept as a sanity check but is not the primary path. |
| DAI log-by-runid API | **(User)-provided, PoC-2-proven.** `GET {DAI_BASE_URL}/ai/runlogs/{runid}` with `Authorization: Bearer <token>` (token via OAuth2 `client_credentials` against `{DAI_BASE_URL}/auth/realms/eggplant/protocol/openid-connect/token`). Response shape: `{"items": [LogEntry…], "total_count": N, "date_as_of": "ISO8601"}`. `LogEntry` keys: `id, eventtime, testrunid, message, severity, step_id, stage, message_type, image_name, image_id`. |
| Error-entry identification | **LLM step (`claude-opus-4-7`).** Given the ordered `items[]` and the ticket's `title`+`description`, the LLM picks the SINGLE entry whose `message` matches the user-reported failure (e.g. ticket says *"release was not able to identify"* → log entry `"Unable to Find Image (TEXT:\"Released\"). Text not found."`). Severity alone is not a reliable filter — real failures often have `severity: INFORMATIONAL` and `message_type: imagefound`. |
| Error-screenshot fetch | **Deterministic walk-back** from the matched-entry index toward 0; return the first entry whose `image_id` is non-null/non-empty. Then `GET {DAI_BASE_URL}/api/v2/screenshots/{image_id}` with the same bearer token → PNG bytes. |
| **Production DAI** (evidence source) | `epcorpappsdai12`, DAI **25.3.1+0**. **READ-ONLY.** Ticket runid → run log → error screenshot. Validation never touches it. |
| **JARVIS DAI** (execution) | DAI **26.2.2**, Jay-administered, on the JARVIS VM above. **Base URL: `https://eggptdai10.cos.is.keysight.com:8000/` — HTTPS, port 8000.** Executes every validation run. |
| **Production repo** (PR target) | `bitbucket.it.keysight.com/scm/eggauto/enovia-plm-test-automation.git`, project `EGGAUTO`, branch `Testing_Mar10`. Working-copy source. Written **only** as `Jarvis-fix/<TICKET>` + PR, after PASS + human approval. Git remote name: **`origin`**. |
| **Validation repo** (execution target) | `bitbucket.it.keysight.com/scm/eggauto/agentic-eggplant-automation.git`, branch **`Enovia`**. Force-pushed with the full candidate state on every validation cycle. Git remote name: **`agentic-eggplant-automation`**. |
| JARVIS agents | `Test26_2_Design` plus a Run environment, **co-located on the JARVIS VM**, with licensed **EPF 26.2.x** |
| Version policy | DAI / agents / EPF are **lockstep at 26.2.x**. Agent `.ini` access keys are instance-specific (HTTPS, 26.2.1+). Production agents and certificates are **not reusable** on JARVIS. |
| JARVIS suites folder | `C:\Eggplant_Suites` on the JARVIS VM — a git clone of the validation repo (`JARVIS_ENOVIA_SUITES_PATH_IN_VM`) |
| Completion signal | Webhooks admin UI is available on JARVIS and Jay is admin. **`poll_backoff` works from day one; webhook is the upgrade path, not a prerequisite** (O1). |
| Run→commit integrity | **Solved.** The run log records `Using Git commit SHA: '<sha>'`, and the git connection **syncs at run start** (not a cached clone). This makes plan4's UP-24 fully implementable rather than a residual risk. |
| Imported model | Per-suite model exported from the production DAI and imported into the JARVIS DAI (D2). `Part_Master_Pack_01` / **PartMaster onboarded and proven**; all other suites remain open item **O4**. |
| JARVIS SUT | `Jay_130`, registered by hostname + RDP credentials. **Already bound to the test configs that will be triggered — no setup required by the Agent.** Additional SUTs are added to test configs by Jay later; see `docs/later-enhancements.md` and `docs/context.md`. |
| Suites (17+) | 3DDashboard, BoundaryApps, Common, CustomReport, EngineeringCentral, EnoviaCommon, LibraryCentral, M&AFoundational, MACS, MaterialsComplianceCentral, MSFIntegration, PartMaster, Performance, PLMBridge, Search, SupplierCentral, TeamCenter |
| Golden regression | **TESTAUTOMA-8055** — `EngineeringCentral.suite` test; bug at `CommonEnovia.script:409`, the `and not ImageFound(text:"Name",…)` clause |

> **Port map on the JARVIS VM:** `:8000` = JARVIS DAI (HTTPS) · `:8080` = the JARVIS orchestrator +
> chat app (target port — **confirm free at deploy time**). Two services, one host, distinct ports.

**Handler-chain reality:** `test → suite handler (e.g. addHeaderOnly) → searchEnovia (CommonEnovia.script) → sub-handlers`.

#### Failure families — the canonical taxonomy (22)

> **The test a family must pass.** *A family earns its place if and only if it **routes to a different
> repair**.* Not if it describes a different symptom — if the **fix strategy** differs. This is the rule
> that keeps the list from growing without limit, and it is the rule to apply to any future proposal.
>
> Each of the ten families added on 2026-07-30 passes it for the same damning reason: **the nearest
> existing label names a wrong fix.** That is why they were added rather than folded in. Two worked
> examples, because the cost is concrete rather than aesthetic — `search_criteria_too_broad`'s nearest
> label is `test_data`, which is **not autofix-eligible**, so folding it would make JARVIS *decline a
> ticket it can fix with a one-line change*; `criteria_order_vs_scroll_direction`'s nearest label is
> `search_rectangle`, whose repair is *widen the rectangle* — not merely useless but **actively harmful**,
> since a wider rectangle can match the wrong field.

**Code / script defects — autofix-eligible (17):**

| Family | Repair strategy |
|---|---|
| `boolean_logic_gap` | Make the boolean context receive a boolean (`ImageFound(...)`) |
| `silent_exception_swallowing` | Remove or narrow the swallowing catch |
| `search_rectangle` | Adopt a proven sibling rectangle or an anchor-relative rectangle |
| `dpi_cascade` | Fix the DPI ladder / reset after use |
| `text_label` | Correct the expected string |
| `missing_wait` | Add or extend a wait on a **real condition** |
| `image_staleness` (rare) | Update the stored image asset |
| `handler_name_mismatch` | Correct the handler name or provider qualification |
| `config_value_stale` | Update the value — **and every shadowing copy** |
| `flaky_oracle` | **Change the verification mechanism, not its parameters** — move up the oracle order |
| `unhandled_popup_overlay` | **Call the popup handler before the assertion** — the rectangle and the string were never wrong |
| `hardcoded_coordinate_brittleness` | **Anchor the click to a located element** instead of a fixed coordinate |
| `silent_parameter_typo` | **Correct the misspelled named parameter** — the call silently ran without the option |
| `transient_render_state` | **Re-probe after settling**; never use a hover/dim-sensitive image as the sole presence oracle |
| `false_pass_assertion` | **Establish presence before asserting absence** — see the warning in §6 |
| `search_criteria_too_broad` | **Add or narrow a discriminating criterion** so the result set contains only the intended type (`Collaborative Policy = "EC Part"` is the live example) |
| `criteria_order_vs_scroll_direction` | **Reorder the criteria to match the panel's top-to-bottom draw order** — `scrollTo` travels one way, so a criterion above one already passed is unreachable |

**Not autofix-eligible — the routing differs (5):**

| Family | Route |
|---|---|
| `environment_issue` | `diagnose_only` + remediation request |
| `test_data` | `diagnose_only` |
| `application_bug` | `diagnose_only` |
| `change_scope` | **`ask_human`** — detectable free from the Jira label, before any diagnosis |
| `transient_flake` | **Tolerate — re-run, fix nothing** |

**Two boundaries to state explicitly, because they will otherwise be confused:**
- `flaky_oracle` = the verification **mechanism** is wrong → change the mechanism.
  `transient_render_state` = the mechanism is fine but a **transient render state** breaks it → re-probe.
- **Naming:** the ticket records propose `environment_flake`; plan4 §4.1.1 already codes **`transient_flake`**, which wins — it is the existing usage, and the name is more accurate since not every flake is environmental.

**This list is the single source of truth for `Diagnosis.category` (plan1 §1.4.2) and for plan4's
`triage.fixable_families` (§4.1.1).** Those two must never drift from it: a schema constrained to a
narrower list would **reject plan4's own classifications at runtime**.

---

## 4. CANONICAL REPO LAYOUT v2 (built in plan0 §B.1)

> **The repo root IS the project root.** The Bitbucket repo is named **`jarvis`**, so cloning it
> produces exactly this tree — there is no nested project directory. (The project's former slug is
> retired: as a repo name, as a directory name, and as the `pyproject.toml` package name.)
> `agentic-eggplant-automation` is a **different** repo — the validation repo — and is **not** renamed.

```
jarvis/                                  # git repo root == project root == Bitbucket repo `jarvis`
├── plan_master.md  plan0…plan4.md       # the plan set lives at root; it is the entry point
├── pyproject.toml  .env.example  README.md  PROGRESS.md  .gitignore  requirements-poc.txt
├── docs/                                # context.md maintenance.md later-enhancements.md
│                                        # plan_change_log_jarvis{,_2,_3,_4}.md
│                                        # poc_execution_guide.md
│                                        # FINDINGS_for_JARVIS.md  — cross-ticket findings + tool gaps
├── config/enovia.yaml                  # track config (repo, suites, DAI ids, models, modes, budgets)
├── src/
│   ├── main.py  config.py
│   ├── api/        routes_chat.py routes_runs.py routes_sse.py routes_metrics.py
│   │               routes_webhooks.py auth_sso.py
│   ├── chat/       intent.py conversation_store.py
│   ├── orchestrator/ pipeline.py validation_loop.py validation_gate.py dispatcher.py
│   │               lifecycle.py publisher.py
│   │               revert.py state_store.py queue.py locks.py track_loader.py events.py
│   ├── agentic/    tool_loop.py tools.py schemas.py            # UP-1, UP-2
│   ├── integrations/ jira_client.py bitbucket_client.py dai_client.py
│   │               jarvis_dai.py epf_runner.py claude_client.py
│   ├── analysis/   diagnosis.py fix_generator.py family_router.py context_packer.py
│   │               templates/ (agent_dispatcher.st.j2)         # D4 — generated dispatcher
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
│   ├── poc_dai.py poc_jarvis_validation.py poc_bitbucket.py poc_jira.py poc_claude.py poc_static.py poc_runscript.ps1
│   ├── categorize_tickets.py setup_vm_jarvis.ps1 clone_repo.ps1
│   ├── build_handler_map.py build_vocabulary.py run_validation.py run_eval.py
│   ├── test_integrations.py verify_context.py
├── tracks/enovia/                       # the curated track knowledge set (see §2.4)
│   ├── context.md                       # CORE, ~7.7K tokens, always in the cached prefix (UP-6)
│   ├── context_appendix_handlers.md     # loaded ON TRIGGER only — see context.md "Appendix triggers"
│   ├── context_appendix_messages.md
│   ├── context_appendix_rectangles.md
│   ├── context_appendix_finding_things.md
│   ├── context_appendix_ticket_learnings.md
│   ├── context_seed.md                  # cross-ticket seed the core was generated from
│   ├── ticket_findings.md               # combined; sources in ticket_findings/
│   ├── ticket_findings/                 # one file per solved ticket (nine today)
│   ├── handler_map.yaml handler_vocabulary.json prompt_overrides.md
│   ├── test_config_registry.yaml        # D3 — suite → test_config_id (replaces the old scalar env var)
│   ├── validation_tickets.json ticket_base_rate.json poc_results.md
│   └── gold_scripts/                    # UP-12 exemplar tests
├── data/                                # gitignored
│   ├── working_copy/ agent_runs/{run_id}/ trajectories/enovia.jsonl agent.db
├── samples/
└── tests/
```

### 4.1 Where the fix physically happens (no online IDE / sandbox service needed)
The orchestrator VM **is** the workspace. A **local git clone of the Enovia test repo** lives at `settings.working_copy_path` with **two remotes pointing at two different Bitbucket repositories**:

- **`origin`** = the **production** Enovia repo `enovia-plm-test-automation` — pull `Testing_Mar10` hourly; push **only** `Jarvis-fix/<TICKET>` at plan3 PR time, after PASS + approval.
- **`agentic-eggplant-automation`** = the **validation** repo `agentic-eggplant-automation` — force-push the full candidate state to branch `Enovia` on every validation cycle (§2.3).

All reading/analysis (parser, ripgrep, Claude's `read_script`/`grep_repo` tools) and all writing (the fix applier's exact text replacement) happen on this clone's files, isolated on a local branch `wc/<TICKET>`. Git is the sandbox: the branch isolates the change, `git diff` is the reviewable patch (streamed to the chat as a diff artifact, so the user sees exactly what changed and where), `git reset --hard` restores a pristine tree between attempts. **The fix exists remotely exactly twice: on `agentic-eggplant-automation/Enovia` during validation, and on `origin Jarvis-fix/<TICKET>` after approval.** The trajectory log + transcript keep the permanent record after `wc/` cleanup.

**D4 rule (binding).** The generated `<Suite>_AgentDispatcher.script` files exist **only** on `agentic-eggplant-automation/Enovia`. They are validation scaffolding, not product code, and must be **excluded from the `Jarvis-fix/<TICKET>` branch** — the publisher asserts none is present in the diff before pushing (plan3 §3.2). A dispatcher reaching the production repo is a defect.

**Settled naming:** the fix branch prefix is **`Jarvis-fix/<TICKET>`**, that exact casing. The 12 `ai-*`
Jira labels (`ai-fixed`, `ai-diagnosed`, `ai-diagnosis-only`, `ai-needs-manual`, `ai-budget-stop`,
`ai-flake`, `ai-diagnosis-env`, `ai-diagnosis-data`, `ai-diagnosis-infra`, `ai-diagnosis-appbug`,
`ai-diagnosis-changescope`, `ai-needs-manual-validation`) are **unchanged and stay exactly as they are** —
they are operational identifiers agreed with the track team.

> **Two clones, two remotes both called `origin` — do not confuse them.**
> - The **JARVIS project repo** (this repo, the agent's own code): its `origin` is Bitbucket **`jarvis`**.
> - The **Enovia working copy** (`settings.working_copy_path`, the test scripts being fixed): its
>   `origin` is **`enovia-plm-test-automation`**, and its second remote is
>   **`agentic-eggplant-automation`** (the validation repo).
>
> Every `origin` mentioned in a *validation* or *publishing* context means the **Enovia working copy's**
> origin — the production test repo. Agent code is never pushed to the test repo, and test fixes are
> never pushed to the JARVIS repo.

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
GET  /api/runs/{run_id}/jira_actions          → persisted Jira action records for this run
POST /api/runs/{run_id}/jira_actions/{action_id}/check  → READ-ONLY reconciliation probe
POST /api/runs/{run_id}/jira_actions/{action_id}/retry {confirm: true} → ONE explicit re-attempt
GET  /api/metrics              → metrics JSON
POST /api/webhooks/bitbucket   → PR-merge webhook (plan3)
```
**Jira action recovery is action-scoped, never run-scoped** — `check`/`retry` act on one
`action_id`; they never re-run diagnosis or the pipeline. **A retry is never automatic**: not on
reload, reconnect, restart, or queue recovery. An `uncertain` action MUST be checked before a retry
is offered (check `present` → reconciled without a second write; `absent` → retry permitted;
`unknown` → stays uncertain, manual handling). Rationale:
`docs/agent/decisions/003-jira-write-retry-boundary.md` +
`docs/agent/decisions/004-jira-action-reconciliation.md`.

### 5.2 SSE event envelope (every event; persisted to `events` table)
```json
{"event_id": "...", "run_id": "...", "ts": "ISO8601", "type": "<type>",
 "payload": { ... }, "cost_usd_so_far": 0.42}
```
**Types:** `run.queued` · `step.started` · `step.progress` · `step.completed` · `step.failed`
· `agent.message` (NL narration for a chat bubble) · `tool.called` / `tool.result` (collapsible card)
· `artifact` (payload.kind: `diagnosis|diff|screenshot|log_excerpt|evidence|pr`)
· `approval.requested` (payload: diff, evidence, expires) · `approval.resolved`
· `jira.action.updated` (payload: the SAFE action summary — `action_id`, operation, state,
  check result, attempt count, timestamps; **never** PAT, authenticated URL, attachment bytes,
  or raw transport/response text)
· `run.completed` / `run.failed` (summary, totals).

### 5.3 Intent grammar (chat → pipeline)
Regex first: `(?i)\b(TESTAUTOMA-\d+)\b` + mode keywords (`diagnose`, `fix`, `status`, `revert`, `metrics`, `help`) + optional `runid[=: ]?(\d+)` override token. Bare ticket ID → ask "diagnose or fix?" with quick-reply buttons. Anything else → one light model call (or Opus with small `max_tokens`, per the single-model policy) maps to `{action, ticket?, runid?}` or a plain conversational reply. Unknown → helpful usage message.

---

## 6. GLOBAL CONVENTIONS (apply to every step)

1. **Step template:** Owner → Goal → Actions → Verification → DoD. DoD gates the next step.
2. **Secrets:** never in repo. `.env` per VM via `pydantic-settings`. `.gitignore` covers `.env`, `data/`, `*.log`, `node_modules/`, `webapp/dist/`.
3. **Logging:** `structlog` JSON from line one; every external call logs latency + status; every log line carries `run_id`.
4. **Safety invariants (enforced in code):** never merge; never write `Testing_Mar10`; **validation pushes go ONLY to the validation repo `agentic-eggplant-automation` on branch `Enovia`**; the production repo is written only as `Jarvis-fix/<TICKET>` after PASS + approval; production writes require SSO session; SUT serialized via per-track lock; budget cap aborts gracefully (UP-13). **Plus:** (a) **no PASS/FAIL is trusted unless the pushed SHA is asserted both before trigger (`git ls-remote`) and after completion (the run log's `Using Git commit SHA`)** — a mismatch yields `STALE_SYNC`, never a verdict (UP-24, §2.3.4, plan2 §2.5.2, plan4 §4.7.2); (b) **the generated dispatcher never reaches the production repo** (D4, §4.1, plan3 §3.2).
5. **Evidence framing (UP-14):** Jira and DAI have reliable provenance, but their content is semantically fallible and must be corroborated across ticket/comments, logs, screenshots and current source; evidence content never acquires model-instruction authority — delimit ticket AND DAI log text, neutralize active markdown, length-cap; instruct the model accordingly.
6. **Cost honesty:** track tokens/cost per call; with Opus 4.7 + prompt caching expect **$2–6/ticket**; report it.
7. **One reasoning model:** `llm.model = claude-opus-4-7` for every diagnosis/fix/agentic call — no quality compromise, no escalation ladder. (The originally planned `claude-opus-4-6` is not whitelisted on the Keysight AI gateway; a request for 4-6 returns a misleading `401 invalid x-api-key` because the gateway forwards the model name and Anthropic upstream rejects it. The whitelisted Opus IDs proven in PoC 2 are `claude-opus-4-5` and `claude-opus-4-7`; we use 4-7 as the newer of the two. If/when Keysight whitelists 4-8 or later, bump this convention.) `llm.model_light` is **optional** and used ONLY for non-reasoning utility calls (chat-intent fallback, one-time vocabulary purpose lines); if the user prefers strict single-model, set it to the same Opus ID or rely on the regex layer alone. `llm.anthropic_base_url` supports the direct API **or** the Keysight gateway (e.g. the Azure APIM Anthropic endpoint) — both model ID and base URL live in `.env`.
10. **`.env` overrides parent shell:** every script (PoC and prod) loads dotenv with `load_dotenv(override=True)` so the project's `.env` wins over any parent-process env vars. Without this, a developer running scripts from a shell that already has `ANTHROPIC_BASE_URL` set (e.g. an IDE / Agent session) will silently hit the wrong API base. Discovered the hard way during PoC 2.
8. **Concurrency truth:** one SUT, one test at a time (`max-parallel: 1`); one dedicated EPF license; one dedicated RDP SUT.
9. **Prompt caching (UP-6):** stable prefix (system + context.md + vocabulary) marked cacheable on every Claude call.
11. **No LLM in wait paths:** any long-running external wait (JARVIS DAI validation run: 20 min–2 hr; any future SUT job) is waited on by plain orchestrator code — an `asyncio.Event` resolved by a webhook, an awaited subprocess, or an `asyncio.sleep` poll loop — never by the LLM/agentic tool-loop (UP-1) calling a "check status" tool repeatedly. Claude touches a validation gate only at its two edges: generating the candidate before triggering, and interpreting PASS/FAIL/logs after it resolves. See **plan2 Phase 2.5** for the concrete `JARVIS_COMPLETION_MODE` design (`poll_backoff` is the day-one mode; webhook is the registered upgrade path, O1). Cost during the wait window must be **$0**.
12. **SenseTalk path + invocation rules (S1/S2, §2.3.6):** a script under `Scripts/TestCases/` is referenced as `TestCases/<name>` — **never** with a `.script` extension, **never** with a `Scripts/` prefix (EPF does not auto-search subfolders); dynamic invocation is plain `run targetScript`, **never** dot-notation `targetScript.run()`. Both rules are load-bearing for the dispatcher template and the target-path derivation logic — violating either produces a run that fails for the wrong reason.
13. **Suite not onboarded → never validate.** The validation suite is **the suite that owns the FAILING TEST**, resolved by `validation_suite_of(run)` (plan2 §2.5.0) — **never** the suite containing the changed file, because most real fixes land in **shared handlers** that belong to no suite and have no test config. If that resolution yields a suite **not** present in `tracks/enovia/test_config_registry.yaml` (D3), the validation gate returns **`{status: NOT_ONBOARDED}` *before* any push or trigger**. The run is routed to the existing **diagnose-only** outcome with reason `suite_not_onboarded`, using the existing `ai-diagnosis-only` label. The gate **never** falls back to another suite's `test_config_id`, and `NOT_ONBOARDED` is **never** reported as PASS or FAIL. This is a routing decision taken *before* a run starts, not a run-time failure. Only one suite is onboarded today (**O4** tracks the rest), so this rule is load-bearing from day one. See plan2 §2.5.2 and §2.6.
14. **JARVIS never modifies the candidate artifact between validation and PR.** The bytes validated are the bytes proposed. **Automatic rewriting of environment literals — hostnames, UNC paths, URLs, SUT addresses — before or after a validation run is prohibited**, however convenient. A PASS on rewritten code says nothing about the code that ships, and the SHA assertion at both edges (`git ls-remote` pre-trigger, `Using Git commit SHA` post-completion) exists precisely to make such a substitution detectable. It would also **mask the defect class it resembles**: TESTAUTOMA-7947's blocker 2 was a stale hardcoded URL, and auto-substituting environment literals would have hidden it.
    **The permitted exception is additive only, and already defined:** the generated `<Suite>_AgentDispatcher.script` (**D4**) exists on the validation branch and never reaches the PR. It **adds** a scaffold entry point; it does **not** alter the code under test. *Additive validation-only scaffolding is permitted; mutating the artifact under validation is not.*
    When a literal genuinely must differ per environment, the correct outcomes are, in order: **satisfy the path in the environment** (alias/share on the machine that reads it); **promote the literal into environment config as a proposed fix**, subject to normal review; or **route to `diagnose_only`** with a precise remediation request. **An honest "cannot validate here" outranks a false PASS.**
15. **`false_pass_assertion` is the worst verdict failure available — treat it as such.** A check that reports success for a state **never observed** produces a **false PASS**, and a verdict built on one is worse than no verdict: it consumes the approval budget, ships an unvalidated change, and burns the trust the whole HITL design exists to protect. The live example is `common.waitForTextToDisappear` succeeding when the text was **never present** (`tracks/enovia/context.md`, *Shared contracts*). Wherever absence is asserted, **presence must be established first** — and Tier-0 lint flags the pattern statically (plan2 §2.3).

---

## 7. GATE SUMMARY

| Gate | After | Bar |
|---|---|---|
| **0a** | Week-0 PoCs | PoC 7 (base rate) must pass, **and the JARVIS validation path** (PoC 2b JARVIS validation path + A.2b dispatcher proof) must be proven — **both are proven** — or STOP & re-architect that part. JARVIS is now the single mandated validation mechanism; the old either/or with the local `runscript` loop no longer applies (that loop is deferred, §2.1). |
| **0b** | Foundation | Integration smoke test all-green from the orchestrator VM |
| **1** | Diagnosis | Root-cause match ≥75% on ≥50 tickets (+95% CI); 0 crashes; chat MVP usable |
| **2** | Auto-fix | First-attempt ≥60%, final(≤3) ≥80%, equivalence ≥75%, 0 regressions (+CIs) |
| **3** | Rollout | ≥50% triggered tickets → merged PR ≤24h; PR-accept ≥75%; 0 post-merge regressions |

## 8. DEFINITION OF DONE (WHOLE PROJECT)
A developer opens the SSO chat app, types `fix TESTAUTOMA-XXXX`, watches JARVIS extract the runid → fetch the **production** DAI error log + screenshot → localize → diagnose → patch → lint → **validate on JARVIS** (force-push the candidate to `agentic-eggplant-automation@Enovia`, assert the SHA, trigger that suite's test config on the JARVIS DAI, assert the executed commit SHA) → request approval → push `Jarvis-fix/<TICKET>` to the **production** repo `enovia-plm-test-automation` + open PR into `Testing_Mar10` + update Jira with evidence — all live in chat — with one-click revert available, every trajectory logged, and Gate 3 metrics met with CIs and zero post-merge regressions. **Two repos, one direction: candidate → validation repo → (PASS + approval) → production repo.**

➡ **Agent: open `plan0_poc_and_foundation.md` and begin at Phase 0.A, Step A.0.**
