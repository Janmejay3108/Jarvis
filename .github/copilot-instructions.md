# JARVIS — repository instructions

These apply to **every** agent and every chat in this repository. Agent-specific files add to
these; they never override them.

JARVIS diagnoses and auto-fixes failing Enovia Eggplant test tickets. It reads a Jira ticket,
pulls the DAI error log and screenshot by `runid`, localises the fault, patches the SenseTalk
script, **validates the patch by actually running it**, and opens a PR for human review.

The plan set at repo root is the design authority, read in order: `plan_master.md` (architecture,
tree, event contract, taxonomy, invariants) → `plan0` → `plan1` → `plan2` → `plan3` → `plan4`.
Plans are **directly editable**, but only in numbered passes with a change log — see the Plan
Steward agent. No other agent edits a plan file.

## Read before you act

This file is short on purpose. The real context lives in the repository, and keyword search will
not find it for you — searching returns a fragment that looks like an answer while the
contradiction sits two files away. **Open and read whole files.**

**`docs/agent/ORIENTATION.md` is the operating brain — read it first, every session.** How we
work, what was decided and why, the eleven mistakes and the rule each produced, the proven DAI API
contract, where the build actually stands, and the traps. It is short enough to read in full and it
is the difference between an agent that has context and one that is guessing.

**`docs/context.md` is the design orientation.** 1,056 lines, twenty sections, a document map at
§19 and a glossary at §20. Read it at the start of any session that will touch design, and reread
the relevant section before any step. §3 (the two-DAI / two-repo topology) and §14 (the complete
safety-invariant list) are the two that get violated most.

| Before you… | Read |
|---|---|
| **anything at all** | `docs/agent/ORIENTATION.md` — in full |
| anything involving design | `docs/context.md` — at minimum §1–3, §14, §19 |
| implementing a plan step | that plan file's section **in full**, plus `plan_master` §2.3, §4, §5 |
| touching validation, the dispatcher, or the fix loop | `docs/context.md` §5, §7, §8; `plan2` §2.5; `plan_master` §2.3 |
| touching diagnosis, retrieval, or prompts | `docs/context.md` §6, §12; `plan1`; `tracks/enovia/context.md` and its five appendices |
| reasoning about a real ticket or a failure mode | `docs/FINDINGS_for_JARVIS.md` — especially §3, the five wrong-turn archetypes |
| claiming a step is done | `PROGRESS.md` — the tick line is the evidence |
| adding or onboarding a suite | `tracks/enovia/test_config_registry.yaml` (D3) and `plan0` B.4b |
| anything Enovia-domain-specific | `tracks/enovia/context.md` + `context_appendix_*.md` |

Plan files contain non-UTF-8 bytes. `export LC_ALL=C` before grepping them.

**Stale sources — do not resurrect.** `Base.md` does not exist and never will. The overlay files
(`plan_practice_env_overlay.md`, `plan_v3_changes.md`, `validation_poc.md`,
`claude_code_kickoff_prompt.md`) are retired; they opened by claiming precedence over the plans,
which meant they overrode *corrected* text. Any `/practice` path literal is superseded by branch
`Enovia`.

## Never do these

- **Never print, log, echo, or commit a secret.** Not PATs, API keys, client secrets, or bearer
  tokens. To debug a credential, print its length or whether it is empty — never its value.
- **Never read, create, or modify `.env`.** If a value is missing, stop and ask Jay.
- **Never merge, and never push without being told to.** Work on a branch, commit, report.
- **Never work around a step marked `(User)`.** Those are Jay's, always. Stop and hand back.
- **Never hardcode a model ID, base URL, host, or credential in runnable code.** Everything comes
  from `settings.*` or `config/enovia.yaml`.

## The three things most likely to be conflated

**Two DAI instances. Never share a client, base URL, or token cache between them.**

| | Production DAI | JARVIS DAI |
|---|---|---|
| Host | `epcorpappsdai12` (**http**) | `eggptdai10` (**https**), port 8000 |
| Version | 25.3.1+0 | 26.2.2 |
| Role | **read-only**, evidence only | executes every validation run |
| Auth | OAuth2 `client_credentials`, form-encoded, Keycloak realm | `POST /api/v2/auth`, **JSON** `client_id`/`client_secret` → `access_token` + `expires_in`, ~10 min |
| Logs | `{DAI_LOG_BY_RUNID_URL}` | `GET /api/v2/test_results/{run_id}/logs?limit=1000` |
| Trigger | n/a | `POST /task_scheduler_service/api/v1/task_instances/{test_config_id}` → 201 + `task_instance_id` |
| Results | n/a | `GET /api/v2/test_config_results?test_config_id=...` (the `/testconfiguration/{id}/results` route 404s) |

**Three repositories.**

- `Jarvis` (GitHub) — the agent's own code. This repo.
- `agentic-eggplant-automation` branch `Enovia` — the validation target, **force-pushed every
  cycle**. Never opens a PR.
- `enovia-plm-test-automation` branch `Testing_Mar10` — production. **PR only**, after PASS and
  human approval, on branch `Jarvis-fix/<TICKET>` (that exact casing).

**Two resolvers that look alike.** plan1's `_suite_of` maps a ticket number to a repo path.
plan2's `validation_suite_of` maps a run to a registry key. Different input, different failure
mode.

## Load-bearing rules, each from a real failure

- **Model.** `claude-opus-4-7` is the only whitelisted Opus on the Keysight gateway.
  `claude-opus-4-6` returns a **misleading `401 invalid x-api-key`** that reads like an egress
  failure. Always `settings.model`, never a literal. Never file a firewall ticket for a 401
  without checking the model ID first.
- **`load_dotenv(override=True)`** in every script. Without `override`, a parent-shell env var
  silently masks the project `.env`.
- **S1 — script paths.** A script under `Scripts/TestCases/` is referenced as `TestCases/<name>`.
  No `.script` extension, no `Scripts/` prefix. EPF does not auto-search subfolders.
- **S2 — dynamic invocation.** Plain `run targetScript`. Never `targetScript.run()`.
- **Invariant 14 — no mutation.** JARVIS never modifies the candidate artifact between validation
  and PR. The bytes validated are the bytes that ship. Auto-rewriting hostnames, paths, or URLs is
  prohibited — it would mask the exact defect class it resembles. The only permitted
  validation-only artifact is the additive generated dispatcher. **An honest "cannot validate
  here" outranks a false PASS.**
- **`validation_suite_of`** resolves from the failing test named in the DAI log, then the JIRA
  number→suite range, then **raises**. Never infers from a changed file path — most real fixes
  land in a shared handler that belongs to no suite. Never defaults to another suite.
- **`NOT_ONBOARDED`.** A run whose suite is absent from `tracks/enovia/test_config_registry.yaml`
  is refused *before* any push or trigger and routed to diagnose-only. Never PASS, never FAIL.
- **The 22-family taxonomy is canonical in `plan_master` §3 only.** Everything else enumerates
  from there. A family earns its place only if it routes to a different repair.
- **Adding a suite is a data change, never a code change.** It is a row in the D3 registry.
- **`max_attempts: 3`, `BudgetGuard` at $10/run, `callers_pass`, the signature-based verdict, the
  lint gate, the eval harness, every unit test.** These may never be softened, deferred, or
  simplified. The reasoning core is the product.

## Evidence discipline

- **No number without a traceable source.** A claim that a step is done cites the line that proves
  it.
- **Label inference as inference.** "This is inferred from X", not a flat assertion.
- `[verified <date>]` is usable as fact. `[live-run: TICKET]` may describe code that has since
  changed — corroborate against current source. `[UNVERIFIED — check: <cmd>]` is **never** actable
  as fact; run the command or drop the claim.
- **Push back.** When something in a brief is wrong or risky, say so plainly with reasoning rather
  than executing it. Flagging a defect is the system working, not a failure to comply.

## Conventions

- Build branches: `build/<step>-<slug>`. Plan-edit branches: `docs/jarvis-alignment-N`.
- One step, one branch, one commit unless told otherwise. Read your own diff before committing.
- Python: `ruff check` clean before every commit. `pytest` green.
- `pip install` needs `--break-system-packages` on some hosts; virtualenvs are fine too.
- Answer in the shape asked for. "In short" means short. Lead with the answer, then the reasoning.
- When wrong, concede in one line and fix the artifact. No extended apology.
