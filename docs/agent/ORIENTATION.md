# JARVIS — ORIENTATION

**What this file is:** the operating brain. The plan files carry the *design*; this file carries
*how we work, what was decided and why, what went wrong and what rule came out of it, and what
happens next.*

**Read this, then `docs/context.md`, then `PROGRESS.md`.**

**Last updated:** 2026-08-02, after `GATE 0b-LOCAL`. Sections marked ⏱ go stale fastest — update
them in the same sitting as any merge. A fresh session reading a stale table is how confusion
restarts.

---

# PART 1 — HOW WE WORK

## 1.1 The project

**JARVIS** diagnoses and auto-fixes failing Enovia Eggplant test tickets. It reads a Jira ticket,
pulls the DAI error log and screenshot by `runid`, localises the fault, patches the SenseTalk
script, **validates the patch by actually running it**, and opens a PR for human review.

Jira Epic **TESTAUTOMA-8422**. Sponsor: **Mahavir Rathi**. Approver: **Jatin Sibal**. Jay is an IT
intern at Keysight; this is his primary initiative and his path to a full-time conversion.

Repo: **`github.com/Janmejay3108/Jarvis`** (public). Local clone at
`C:\Users\jantiwar\Desktop\Jarvis\Codebase`.

## 1.2 Division of labour

Through 2026-08-02 this ran as a Claude chat (planning + review) plus Copilot (build) plus Claude
Code (multi-file passes). It now runs entirely inside Copilot as four custom agents in
`.github/agents/`.

| Who | Does what |
|---|---|
| **Architect** | Planning, research, design decisions. Writes **briefs** to `docs/agent/briefs/`. **Writes no JARVIS code, ever.** Edits nothing outside `docs/agent/`. |
| **Builder** | The build executor. Writes `src/`, `scripts/`, `tests/` from a brief. One branch, one commit, no push, no merge. |
| **Reviewer** | Independent verification. **Read-only by design** — no edit tool, so findings surface as findings instead of being quietly patched. |
| **Plan Steward** | The only agent that edits `plan_master.md` and `plan0`–`plan4`, in numbered passes with a change log. |
| **Jay** | All decisions. All DAI / VM / Bitbucket / Jira actions. Every step marked `(User)`. Merges, pushes, tags. |

The separation is not ceremony. The Reviewer's value comes from arriving cold with only the diff
and the invariants — the Architect wrote the brief, so it would be reviewing its own instructions.

## 1.3 The loop

1. **Discuss with the Architect.** It researches, reads the tree, proposes.
2. **The Architect writes a brief** to `docs/agent/briefs/<step>-<slug>.md`.
3. **Handoff to the Builder.** It works on `build/<step>-<slug>` and **does not merge**.
4. **Handoff to the Reviewer.** It verifies the branch against the brief and the invariants.
5. **Jay decides**, merges to `master`, pushes.
6. Repeat. Plan defects accumulate and get folded in by the **Plan Steward** as one numbered pass,
   then Jay tags `plan-set-jarvis-vN` **and pushes the tag** (see M4).

**Never trust a self-report alone.** The Builder's report says what it believes it did. Four
separate times, reading the actual tree revealed something no report mentioned.

## 1.4 Non-negotiable habits

These emerged from real failures. They are not style preferences.

- **Verify before asserting.** Read whole files. Chunk search returns a fragment that looks like an
  answer while the contradiction sits two files away. That is exactly how M5 hid.
- **No number without a traceable source.** A gate tick cites the `PROGRESS.md` line that proves it.
- **Label inference as inference.** "This is inferred from X", not a flat assertion.
- **Push back.** Every pass improved because something was flagged rather than executed. Concede
  quickly to facts; when the disagreement is about real risk, say so plainly, with reasoning.
- **Answer in the shape asked for.** "In short" means short.
- **`(User)` means stop.** Never work around a `(User)` step.
- **`export LC_ALL=C`** before grepping plan files — they contain non-UTF-8 bytes.

## 1.5 The brief shape — proven over seven build steps

1. **Which plan step**, with the spec quoted rather than paraphrased. The Builder will not read the
   whole plan.
2. **Branch name and base.**
3. **Per-file specification** — path, API surface (signatures, dataclasses, return types),
   behaviour. Concrete enough that two competent builders produce substantially the same thing.
4. **The tests, enumerated**, each naming what it asserts. Never deferred.
5. **Exact verification commands** with expected results.
6. **What must not change** — the invariants this step could erode.
7. **Report back in chat. No push, no merge.**

A brief that says "implement the config module" is a failed brief.

---

# PART 2 — CONVENTIONS

## 2.1 The plan set

Six documents at repo root, read in order: `plan_master.md` (architecture, tree, event contract,
taxonomy, invariants) → `plan0` (PoCs + foundation) → `plan1` (diagnosis + chat) → `plan2` (autofix
+ validation gate) → `plan3` (lifecycle, PR, rollout) → `plan4` (hardening, triage, edge cases).

**The plans are NOT immutable.** This changed on 2026-07-28. Plans are edited **directly**, in
numbered passes, each with its own change log (`docs/plan_change_log_jarvis{,_2,_3,_4}.md`).

**Do not resurrect the overlays** (`plan_practice_env_overlay.md`, `plan_v3_changes.md`,
`validation_poc.md`, `claude_code_kickoff_prompt.md`). They open with *"where this file conflicts
with the plans, this file wins"*, which would override *corrected* text. `Base.md` does not exist
and never will (retired as fact F10). Any `/practice` path literal is superseded by branch `Enovia`.

## 2.2 The plan-pass shape

1. **Prime directive** — what must not change. Always includes:
   > **PoCs may be retired when the risk they existed to retire is retired by other evidence. Build
   > steps — the static layer, the lint gate, the diagnosis prompts, `callers_pass`, the
   > signature-based verdict, the attempt cap, `BudgetGuard`, the eval harness, every unit test —
   > may never be softened, deferred or simplified. The reasoning core is the product.**
2. **Safety protocol** — base tag, new branch, new change log, one commit per fix, read your own diff.
3. **A rulings table** (`F1–F13`, `G1–G13`, `H1–H7`) — every value Jay supplied, each closing a
   named marker. Facts, not placeholders. Rule IDs make the reasoning travel with the file.
4. **A per-file edit map** — file → section → what changes → which rule authorises it.
5. **Mechanical verification** — `rg` one-liners with expected counts.
6. **A structural check** — diff the heading list against the last tag, confirm nothing came back
   *reduced*. **This is the check that catches quiet erosion of the reasoning core.**
7. **Report back in chat, not as a file. Do not merge.**

## 2.3 Naming and tagging

- Plan-edit branches: `docs/jarvis-alignment-N`. Build branches: `build/<step>-<slug>`.
- Tags after each merged plan pass: `plan-set-jarvis-vN`. **Push tags** — see M4.
- JARVIS's own fix branches on the production repo: **`Jarvis-fix/<TICKET>`** (that casing).
- Build steps do **not** get a tag. That convention is for plan passes only.
- The 12 `ai-*` Jira labels are unchanged.

---

# PART 3 — DECISIONS ALREADY MADE (do not reopen)

## 3.1 Infrastructure

1. **One VM.** JARVIS deploys on **`eggptdai10.cos.is.keysight.com`** (156.140.21.30), port **8080**,
   co-located with the JARVIS DAI (port **8000**), the Design + Run agents, EPF 26.2.x,
   `C:\Eggplant_Suites`, and the Enovia working copy. The old `[ORCH]`/`[RUNNER]` split is retired.
   `aiagent-testmanager` is **retained in the docs as superseded** — that hostname belongs to a real
   separate org initiative (protected under rule R1).
2. **Two DAIs, never conflate.** See the contract table in §3.4 — it is now proven, not inferred.
3. **Three repos, never conflate.** `Jarvis` (the agent's own code, GitHub) ·
   `agentic-eggplant-automation` branch `Enovia` (validation target, force-pushed every cycle) ·
   `enovia-plm-test-automation` branch `Testing_Mar10` (production, PR only, after PASS + human
   approval).
4. **Development is local; deployment comes later** (F12). VM-bound steps (B.2b, B.4's clone, B.4b's
   DAI authoring, B.7b) stay `(User)`-on-VM. Missing local packages are installed inline as needed —
   there is no dev-machine provisioning step and none should be invented.
5. **The agent repo is on GitHub, not Bitbucket** (G11, as amended). B.1's repo-side actions —
   Bitbucket remote, default branch, ≥1-approval rule, repo PAT — are **deferred, not deleted**.
6. **Model: `claude-opus-4-7` only.** `claude-opus-4-6` is **not whitelisted** and returns a
   **misleading 401**. See M1.
7. **JARVIS uses Jay's credentials initially** (G12); someone else approves PRs. A service account
   is a later migration, tracked as **O11**.

## 3.2 Architecture

8. **Constraint C3:** a DAI git connection binds one repo to exactly one branch. *This is why*
   validation force-pushes one permanent `Enovia` branch rather than a branch per ticket.
9. **D3 registry + D4 regeneration.** Every registered suite has its own dispatcher **and its own
   test config**. Every push regenerates **every** registered suite's dispatcher. A suite with no
   `smoke_target` is a hard error at onboarding. **Adding a suite is a data change, never code.**
10. **`NOT_ONBOARDED`.** A run whose suite is absent from the registry is refused *before* any push
    or trigger and routed to diagnose-only. Never falls back to another suite's config; never PASS
    or FAIL.
11. **The validation suite is the suite that owns the FAILING TEST**, not the one containing the
    changed file. See M2 — the most important architectural correction made.
12. **Invariant 14 — no mutation.** JARVIS never modifies the candidate artifact between validation
    and PR. Auto-rewriting hostnames/paths/URLs is **prohibited**. The only permitted
    validation-only artifact is the **additive** generated dispatcher (D4). See M3.
13. **Two-tier context.** `tracks/enovia/context.md` (~7.7K tokens) is always in the cached prefix;
    five `context_appendix_*.md` load **on trigger only**. Triggers are parsed from the core, not
    hardcoded.
14. **22-family taxonomy**, canonical in **`plan_master` §3 only**; everything else enumerates from
    there. 17 autofix-eligible. See M5.
15. **Learning is retrieval, not fine-tuning.** Trajectories (JSONL, append-only, from day one) +
    lexical retrieval by category + handler overlap + keyword. **No embeddings, no vector DB** —
    deliberate: inspectable, no extra dependency, and handler overlap beats semantic similarity
    here. Embeddings are a later upgrade path, not a rewrite (plan3 §3.6.1).

## 3.3 Process

16. **PoC rulings.** PoC 3 **retired** (superseded by B.4, which builds the same capability with
    unit tests — strictly stronger). PoC 4 **reduced** to an API-shape smoke test. PoC 7's decision
    rule **retired**; see M6.
17. **Gate 0b splits** into `GATE 0b-LOCAL` (gates plan1, provable on the dev machine) and
    `GATE 0b-VM` (gates deployment and rollout). **B.7b's on-VM run is preserved, not weakened.**
18. **`context.md`'s review gate moved and was replaced, not dropped.** The replacement gate is
    binding: **a `context.md` change is not complete until `run_eval.py` has been re-run without
    regression** (plan1 §1.7.1).

## 3.4 The DAI API contract — proven live, 2026-08-02

Discovered the hard way during B.7a; six fix commits. **These are facts now, not guesses.**

| | Production DAI | JARVIS DAI |
|---|---|---|
| Host | `epcorpappsdai12.cos.is.keysight.com:8000` (**http**) | `eggptdai10.cos.is.keysight.com:8000` (**https**) |
| Version | 25.3.1+0 | 26.2.2 |
| Role | **read-only**, evidence only | executes every validation run |
| Auth | OAuth2 `client_credentials`, **form-encoded**, Keycloak realm | `POST /api/v2/auth`, **JSON** `{client_id, client_secret}` → `{access_token, expires_in}`, ~10 min, no refresh |
| Logs | `{DAI_LOG_BY_RUNID_URL}` — may return a bare list *or* `{items: […]}`; IDs may be numeric | `GET /api/v2/test_results/{run_id}/logs?limit=1000` → `{items, total_count}` |
| Screenshots | `{DAI_SCREENSHOT_URL}` | `GET /api/v2/test_results/{run_id}/screenshots`, then `GET /api/v2/screenshots/{id}` |
| Trigger | n/a | `POST /task_scheduler_service/api/v1/task_instances/{test_config_id}` → **201** + `task_instance_id` |
| Results | n/a | `GET /api/v2/test_config_results?test_config_id=…` — **`/testconfiguration/{id}/results` 404s on this DAI** |

Log entries carry `timestamp`, `message`, `severity` (`CRITICAL`/`ERROR`/`WARNING`/`INFO`/`DEBUG`),
`stage`, `message_type`, `image_name`, `image_id`. A non-null `image_id` is a screenshot bound to
that exact log line. **Eggplant captures then acts, so the screenshot that matters is the one
*before* the failure** — walk backward from the error index.

The scheduler returned one transient **500**; the identical retry returned 201. Do not treat a
single 500 as a contract error.

Git push to the validation repo uses PAT user-info URL form: `https://{pat}@{host}/{path}`.
**Redact it from every error message.**

---

# PART 4 — MISTAKES WORTH KEEPING

Each produced a rule. They are here because the rule is only legible alongside the failure.

**M1 — the misleading 401.** A day lost to what looked like gateway flakiness. Two causes:
`claude-opus-4-6` is not whitelisted (returns 401, not a clear "unknown model"), and `python-dotenv`
does not override parent-shell env vars, so a shell `ANTHROPIC_BASE_URL` silently masked the `.env`
gateway URL. **Rules:** `claude-opus-4-7` everywhere; `load_dotenv(override=True)` in every script;
**never a literal model ID in runnable code — always `settings.model`.** A residue survived into
`plan0` B.7 and was caught in pass 3: B.7's stated response to that 401 was *"file the firewall
ticket now"*, which would have chased a non-existent network problem.

**M2 — the shared-handler blind spot.** Pass 2 wrote the `NOT_ONBOARDED` rule as *"resolve the
**changed file** to a suite."* TESTAUTOMA-8055's fix lands in `CommonEnovia.script` — a **shared
handler**, which belongs to no suite and has no test config. The project's own golden ticket would
have been routed to diagnose-only and never validated. Invisible with one suite onboarded;
structural at two, because most real fixes touch shared code. **Rule:** `validation_suite_of(run)`
resolves from the failing test named in the DAI log, then the JIRA number→suite range, then
**raises** — never infers from a file path, never defaults.

**M3 — the tempting shortcut that was rejected.** Jay proposed auto-substituting hardcoded agent-VM
hostnames during validation and reverting before the PR. Rejected: it breaks the invariant that
*the bytes validated are the bytes that ship*, and it would have **masked** the exact defect class
it resembles (7947's blocker 2 was a stale hardcoded URL). **Rule:** invariant 14. Correct
alternatives, in order — satisfy the path in the environment; promote the literal to config as a
*proposed fix*; or route to diagnose-only. **An honest "cannot validate here" outranks a false
PASS.**

**M4 — four passes of an unverifiable check.** Every brief's most important check is *"diff the
heading list against the last tag."* The tags existed only on Jay's laptop and were never pushed,
so the check was un-runnable from outside for four passes. **Rule:** tag **and push** after every
merged pass.

**M5 — a live schema contradiction found only by reading the tree.** `plan_master` defined 12
families; `plan1` constrained `Diagnosis.category` to "the 12"; but `plan4` already routed on
`change_scope` and `transient_flake`, which were not among them. A pydantic schema written to plan1
would have **rejected plan4's own output at runtime.** Resolved by ratifying all 10 proposed
families → 22 total. **Rule:** a family earns its place **iff it routes to a different repair**;
the damning signal is that the nearest existing label prescribes a *wrong* fix.

**M6 — an over-argued gate.** The planning chat pushed hard for a ≥50-ticket labelling exercise
before development. Jay ruled it out: too slow, and he had already run the full flow manually on
10–12 real tickets. He was right about the trade. The salvage was better than the original: the
trajectory schema carries the labelling columns **from day one**, so the dataset accumulates as a
by-product, and the formal ≥50 set is assembled only at Gate 1 (**O8**). **Rule:** when proposing
measurement work, first ask whether the data can accrue as a by-product of work already happening.

**M7 — a wrong risk assessment, corrected by facts.** The planning chat argued PoC 4 was urgent
because PR permissions might need a policy exemption with weeks of lead time. Jay held approvals
from Megha, Mahavir and Gaurav, and a working PAT. **Rule:** ask about organisational facts rather
than inferring risk from org structure.

**M8 — findings that describe superseded code.** The `watiFor:25` typo in `clickHome` was real in a
ticket record and is **already fixed** in current source. **Rule:** `[live-run: TESTAUTOMA-XXXX]`
claims may describe code that has since changed; corroborate against current source before citing
them as current state.

**M9 — Copilot found a genuine plan defect.** `plan0` B.1 action 2's `pyproject.toml` snippet omits
`version`, which PEP 621 requires, so `pip install -e .[dev]` fails. Answer: `version = "0.1.0"`.
**This is the system working** — the agent asked instead of inventing.

**M10 — nine defaults deleted inside a whitespace diff.** B.1's `.env.example` change showed 83
lines touched, all of which looked like a CRLF→LF normalisation from `.gitattributes`. Inside that
churn, nine non-secret default values had been blanked — including `MODEL=claude-opus-4-7`, the
exact M1 landmine — with the rationale "keep values out of tracked files." That rationale is right
for credentials and wrong for defaults, which is what a template is *for*. Caught only by reading
the diff's semantic content. **Rule:** for any modification to an existing file, ask what
*behaviour* changed, never how many lines moved. Size is not scope.

**M11 — empty placeholders that fail silently.** B.1 created 104 empty files. For `.py` that is
harmless — they fail loudly. But empty `handler_map.yaml` loads as `None` rather than erroring, an
empty `agent_dispatcher.st.j2` renders an empty string (a content-free dispatcher, force-pushed),
and an empty prompt `.md` is a prompt with no instructions. Seven were deleted before merge.
**Rule:** stub `__init__.py` only. Never stub data, config, or template artifacts.

---

# PART 5 — WHERE THINGS STAND ⏱

## 5.1 Proven and working

- **The full validation loop**, ~6-minute cycle: git commit → dispatcher generated → force-push to
  `agentic-eggplant-automation@Enovia` → `git ls-remote` SHA assert → trigger a static DAI test
  config by ID → poll → fetch results → assert `Using Git commit SHA` in the run log → verdict.
  (plan0 A.2/A.2b)
- **The evidence chain**: Jira ticket → LLM extracts `runid` → production DAI log + error
  screenshot. (PoC 2 + PoC 5; runid 30832, 402 log entries, error idx 384, 111 KB PNG)
- **Claude reachable** through the Keysight gateway, and **VM egress verified by Jay** (2026-07-29).
- **The JARVIS VM** has EPF, licenser, Design + Run agents, `C:\Eggplant_Suites` and the `Jay_130`
  SUT connection, all proven by a full PASSED run.
- **Two suites onboarded**: `PartMaster` / `Part_Master_Pack_01`, and `EngineeringCentral` /
  `Engineering_Central_Pack_01` (config `271b648a-a5e5-43ee-b4d8-24bab75da263`). EngineeringCentral
  owns TESTAUTOMA-8055's failing test, so **the golden path is onboarded end to end**.
- **`TESTAUTOMA_2941_…` confirmed the 2864–2950 → EngineeringCentral range** — first live proof the
  JIRA number→suite ranges are real. They are branch 2 of `validation_suite_of`.
- **The Enovia knowledge set**: `context.md` (249 lines) + five appendices + `context_seed.md` +
  `ticket_findings.md` (nine tickets). Marker integrity verified: **41 `NOT RECORDED` / 15
  `UNCERTAIN`, combined == sum of sources.**
- **Phase 0.B complete.** See §5.3.

## 5.2 Repo state ⏱

154 tracked files. Repo root **is** project root. `.gitattributes` present, `.md` LF-normalised,
`.env` untracked. Tags `plan-set-jarvis-v1` … `v4` pushed and resolving.

```
Jarvis/
├── plan_master.md  plan0…plan4.md  PROGRESS.md  README.md
│   pyproject.toml  .env.example  .gitignore  .gitattributes
├── .github/    copilot-instructions.md  agents/*.agent.md
├── config/     enovia.yaml                    ← fully resolved, no placeholders
├── docs/       context.md (project explainer — NOT the Enovia one)
│               ORIENTATION.md (this file)  FINDINGS_for_JARVIS.md
│               maintenance.md  later-enhancements.md  poc_execution_guide.md
│               gate_0b_local_validation_report.md  plan_change_log_jarvis{,_2,_3,_4}.md
│               agent/  README.md  briefs/  reviews/  decisions/
├── src/        config.py · orchestrator/{state_store,events,track_loader}.py
│               integrations/{dai_client,jira_client}.py · evidence/packager.py
│               static/{sensetalk_parser,handler_map,call_graph,ripgrep_search,vocabulary,lint}.py
│               (agentic/ analysis/ api/ chat/ evals/ flywheel/ models/ static/ utils/ — empty stubs)
├── scripts/    poc_dai.py  probe_claude.py  test_integrations.py
│               build_handler_map.py  build_vocabulary.py
│               setup_vm_jarvis.ps1  clone_repo.ps1
├── tests/      test_config  test_evidence  test_state_store  test_sensetalk_parser
│               test_handler_map  test_call_graph  test_ripgrep_search  test_vocabulary
│               test_lint  test_build_handler_map
├── data/       trajectories/  working_copy/  agent_runs/   (.gitkeep only)
└── tracks/enovia/  context.md + 5 appendices  context_seed.md
                    ticket_findings.md  ticket_findings/ (9)  test_config_registry.yaml
```

## 5.3 Phase 0.B — complete, 2026-08-02 ⏱

| Step | What landed |
|---|---|
| **B.1** | Repo bootstrap. 107 files. Two pre-merge fixes: restored nine `.env.example` defaults (M10), deleted seven silent-failure stubs (M11). |
| **B.2b** | `setup_vm_jarvis.ps1`, 245 lines. Written; **runs at deployment**, not yet executed. |
| **B.3** | `src/config.py` (36 fields, `SecretStr` on eight credentials) + `track_loader.py` (typed, `extra="forbid"`). No `jarvis_test_config_id` field — the map lives in D3. |
| **B.4** | The static layer: parser, handler_map, call_graph, ripgrep_search, vocabulary, lint (4 Tier-0 rules) + two builder CLIs + `clone_repo.ps1`. `config/enovia.yaml` fully resolved. 28 tests. |
| **B.5** | `dai_client.py`, `jira_client.py`, `evidence/packager.py`. 6 tests. |
| **B.6** | `state_store.py` (6 tables, aiosqlite) + `events.py` (EventBus, persist + fan-out + replay). 10 tests. |
| **B.7a** | `test_integrations.py`, 648 lines, 10 checks. Six fix commits against live APIs → §3.4. |

**`GATE 0b-LOCAL`:** checks 1–9 passed live. Check 10 proved auth → force-push → remote SHA assert
→ HTTP 201 trigger → `task_instance_id` parsed → backoff polling entered. Jay cancelled the
execution deliberately at that point rather than wait 20 minutes for plumbing already proven in
A.2/A.2b. The post-completion SHA assertion is therefore the one leg not exercised end to end in
this script. Recorded in `docs/gate_0b_local_validation_report.md`. **Plan1 is unblocked.**

## 5.4 The four alignment passes

| Pass | What it did | Tag |
|---|---|---|
| **1** | Renamed to JARVIS, retired "Practice" terminology, integrated the validation flow | `v1` (d461650) |
| **2** | Flattened the repo to one root, retired the `ai-test-fix-agent` slug, created the D3 registry, closed 10 markers | `v2` (10dd360) |
| **3** | Opus-4.6 landmine, two-VM residue, B.2 split, Gate 0a reconciliation, **validation-suite resolution fix**, Gate 0b split | `v3` (ad528dd) |
| **4** | **22-family taxonomy**, four Tier-0 lint rules, appendix-aware context layer, B.4 action 6 rewrite, **drift detection**, **invariant 14**, freshness assert, two script specs | `v4` (bb7b606) |

Pass 4's structural check ran clean: headings 23→24, 32→32, 33→33, 20→21, 27→28, 46→46. **Zero
headings lost.** Every threshold, `max_attempts: 3`, `callers_pass`, `BudgetGuard`,
`NOT_ONBOARDED` intact.

---

# PART 6 — WHAT COMES NEXT ⏱

## 6.1 Immediate

**Plan1 — the diagnosis engine and chat MVP.** No code changes to Enovia; pure analysis. Roughly:
pipeline skeleton and queue → the four integration clients wired → retrieval and the two-tier
context layer → the diagnosis prompt and `Diagnosis` schema → chat API and SSE → the eval harness.
Read `plan1` in full, plus `docs/context.md` §6 and §12, before shaping the first brief.

## 6.2 Jay's parallel tasks (none block the build)

- **Onboard more suites** (O4) — 15 of 17 remain, each needing the manual D2 sequence. **The single
  largest constraint** on how much of the ticket flow JARVIS can serve.
- **Run A.10a** once `categorize_tickets.py` exists → frequency-ranked onboarding order for O4.
- **PoC 4's API-shape smoke** (~1 hour, before plan3) — run against `agentic-eggplant-automation`,
  Jay's own repo, since Bitbucket Server API shapes are **server-wide, not per-repo**. The call that
  matters is PR-create with `fromRef`/`toRef` as objects.
- **B.7b** — the same smoke script on the VM at deployment → `GATE 0b-VM`.

## 6.3 Open items (full table in `PROGRESS.md`)

| ID | Status | What |
|---|---|---|
| **O1** | open | Webhook not registered; `poll_backoff` is the proven day-one mode. Upgrade, not prerequisite |
| **O2** | open | Suite-name collisions as suites accumulate (constraint **C2**) |
| **O3** | marker | Real per-cycle wall-clock timing — needs the gate to run for real |
| **O4** | **open — biggest** | 15 of 17 suites still to onboard |
| **O5** | mitigated | Force-push wipes non-target dispatchers — neutralised by O6, kept visible |
| **O6** | resolved | Regenerate every registered suite's dispatcher on every push |
| **O7** | open | Monthly model re-import is a person-dependency; scales with O4 |
| **O8** | open | The ≥50-ticket labelled set, assembled at Gate 1 scoring |
| **O9** | resolved | EngineeringCentral onboarded |
| **O10** | open | EPF licence contention — **must classify as infrastructure, never as a failed fix** |
| **O11** | open | Agent identity — Jay's creds today; service account later |
| **O12** | resolved | Gate 0b split |
| **marker** | open | Model re-import runbook: menu path · replace-vs-duplicate · does `TEST_CONFIG_ID` survive |

## 6.4 Plan defects to fold into the next Plan Steward pass ⏱

- **`plan0` B.1 action 2** omits `version` from the `pyproject.toml` snippet (M9). Add `0.1.0`.
- **`repo.local_path` contradiction.** `plan_master` §4's tree shows `data/working_copy/`; `plan0`
  B.4 action 1 and the Gate 0b-VM checklist say `C:\agent\repo`. B.4 encoded the former silently.
- **`plan0` B.1 action 3** lists "timeouts" in the `validation` config block; no timeout key was
  implemented there (`jarvis.run_timeout` covers it). Reconcile or drop.
- **The DAI v2 API contract (§3.4)** should be written into `plan2` §2.5 — the endpoints in the
  plans predate the B.7a discovery and are wrong in three places.
- **`number_to_suite_ranges`** carries only the two proven ranges. `context_appendix_finding_things`
  has a 14-suite table marked "approximate filename clusters" that **contradicts** the exact range
  for EngineeringCentral (2785–2951 vs 2864–2950). Needs a ruling before those rows are encoded —
  a wrong range routes validation at the wrong suite.

---

# PART 7 — TRAPS: PAIRS THAT LOOK ALIKE AND ARE NOT

Every one of these has already caused a conflict or a correction.

| These | Are different |
|---|---|
| `docs/context.md` | Human-readable JARVIS project explainer. **Never** fed to a model. Its disambiguation header is correct — leave it |
| `tracks/enovia/context.md` | Curated Enovia knowledge, **prompt-cached into every call** |
| The **agent repo**'s remote → GitHub `Jarvis` | The **Enovia working copy**'s `origin` → `enovia-plm-test-automation`, second remote → `agentic-eggplant-automation` |
| plan1 `_suite_of` — ticket number → repo path | plan2 `validation_suite_of` — run → registry key. Different input, different failure mode |
| **JARVIS DAI** `eggptdai10:8000` v26.2.2 — **https**, writable | **Production DAI** `epcorpappsdai12:8000` v25.3.1 — **http**, read-only, evidence only |
| JARVIS DAI auth — JSON `client_id`/`client_secret` → `access_token` | Production DAI auth — OAuth2 form-encoded, Keycloak realm |
| `agentic-eggplant-automation` — force-pushed every cycle | `enovia-plm-test-automation` — PR only, after PASS + approval |
| `flaky_oracle` — the verification *mechanism* is wrong; change the mechanism | `transient_render_state` — the mechanism is fine; re-probe after settling |
| `[verified <date>]` — usable as fact, ages | `[live-run: …]` — may describe superseded code (M8) · `[UNVERIFIED — check: <cmd>]` — **never act on as fact**; run the command |

---

# PART 8 — TONE

Jay is direct, technically strong, and moving fast toward a deadline that matters to his career. He
does not need encouragement; he needs accurate analysis and things caught before they cost him time.

- **Match the requested shape.** "In short" means short.
- **Lead with the answer**, then the reasoning.
- **When wrong, concede in one line and fix the artifact.** No extended apology.
- **When it matters, hold the position** — with facts, not repetition. The shared-handler correction
  (M2) and invariant 14 (M3) were both worth the friction.
- **Flag what he cannot see.** He is reading agent self-reports, not diffs. Reading the tree has
  caught something material five times now. That is the highest-value thing an agent does here.
