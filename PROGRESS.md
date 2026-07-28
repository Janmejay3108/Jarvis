# PROGRESS

Running checklist. Append `[x] planN/phase/step — <date> — <one-line result>` after each step.

[x] plan0/0.A/A.0 — 2026-06-12 — PoC workspace scaffold created (scripts/, tracks/enovia/, samples/, tests/, .env.example, requirements-poc.txt, poc_results.md, .gitignore).
[x] plan0/0.A/A.1 — 2026-06-12 — scripts/poc_dai.py written; DAI auth + log + screenshot proven end-to-end on TESTAUTOMA-8055/runid 34156 (241 entries, image_id 1fece214... matches User example, screenshot 341,947 bytes saved). Jira REST v2 ticket fetch proven. AI-driven Jira→runid + error-match steps.
[x] plan0/0.A/A.1 — 2026-06-12 — Full pipeline closed: Jira→LLM→DAI→screenshot on TESTAUTOMA-8055. Run: runid=30832 extracted ('RUN ID: 30832' in description), 402 log entries, error index 384 ("Unable to Find Image (TEXT:\"Released\")"), image_id=465c0ecf... walk-back, 111,914-byte PNG saved.
[+] plan0/0.A/A.1 — 2026-06-12 — Added scripts/probe_gpt54.py + scripts/probe_claude.py as availability monitors. Gateway's /anthropic path behavior is flaky: started session 100% failing for all Claude requests; later passed simple probes but still failed inside poc_dai.py despite identical inline reproductions passing. Reverted poc_dai.py to gpt-5.4 (deviation note expanded in poc_results.md A.1).
[x] plan0/0.A/A.1 — 2026-06-12 — Root-caused the "gateway flakiness": (1) gateway whitelists claude-opus-4-5 + claude-opus-4-7 but NOT 4-6 (4-6 -> misleading 401); (2) python-dotenv doesn't override parent-shell env vars, so Claude Code's ANTHROPIC_BASE_URL=https://api.anthropic.com was silently masking the .env gateway URL. Fixed both: model -> claude-opus-4-7 (newer of the two whitelisted Opus IDs); load_dotenv(override=True) in all PoC scripts. poc_dai.py runs end-to-end on Anthropic Claude via Keysight gateway with the same correct result (runid 30832, error idx 384, 111 KB PNG). plan_master §6, plan0 A.0/A.1/A.8/B.1, plan1 §1.1.2/§1.2.3/§1.2.4, .env.example, .env, probe_claude.py all updated to claude-opus-4-7. plan files now ratify the LLM-reasoning approach for runid extraction + error-entry matching (was previously described as deterministic).


Conclusion: to use claude opus 4.7 for the agent.

[x] plan0/0.A/A.2 — 2026-07-28 — JARVIS validation path proven end-to-end: Part_Master_Pack_01 imported,
    agentic-eggplant-automation@Enovia connected, Jay_130 bound to a JARVIS execution environment (the SUT
    connection remains manual and is maintained by Jay — nothing for the agent to set up),
    co-located Design+Run agents, full PASSED run with 'Using Git commit SHA' traceable in the run log.
[x] plan0/0.A/A.2b — 2026-07-28 — Dispatcher pattern proven: AgentDispatcher model action authored and
    validated; target switched purely by git push with the DAI test config untouched.
[x] plan0/0.B/B.4b — 2026-07-28 — PartMaster onboarded to JARVIS; TEST_CONFIG_ID recorded in
    tracks/enovia/test_config_registry.yaml. Remaining suites tracked as open item O4.
[x] docs — 2026-07-28 — Plan set aligned to JARVIS: project renamed to JARVIS, executor renamed to Agent,
    practice terminology retired, validation flow integrated. See docs/plan_change_log_jarvis.md.

---

## OPEN ITEMS (O1–O7) — carried forward, none of these are done

| ID | Open item | Where it bites |
|---|---|---|
| **O1** | Webhook profile not yet registered on JARVIS. `poll_backoff` is the day-one completion mode; webhook is the upgrade path, not a prerequisite. | plan0 A.2 · plan2 §2.5.2 · plan4 §4.0 item 3 |
| **O2** | Suite-name collision behaviour as suites accumulate on the JARVIS instance (names must be globally unique per instance, C2). Re-check at every onboarding. | plan0 B.4b · plan3 §3.7 |
| **O3** | Per-cycle validation wall-clock timing across a realistic suite set — not yet measured. | plan2 GATE 2 "avg fix+validation time" row |
| **O4** | Scale-out: only `Part_Master_Pack_01` / PartMaster is onboarded. Every other suite needs the full D2 onboarding sequence. | plan0 B.4b · plan3 §3.7 |
| **O5** | Force-push semantics vs. multi-suite dispatchers: force-pushing the full candidate state onto `Enovia` replaces the branch contents, so dispatchers for non-target suites disappear unless regenerated. | plan2 §2.5.0 |
| **O6** | The policy decision arising from O5. **Recommended invariant (⚠ CONFIRM, not settled):** regenerate dispatchers for every registered suite on every push, so the branch is always complete. | plan2 §2.5.0 |
| **O7** | Monthly model re-import from the production DAI into JARVIS is an **undocumented manual activity** and must become a written procedure in `docs/maintenance.md`, performed by Jay every time. **Person-dependency.** | plan3 §3.7 |

> Full ⚠ CONFIRM (Jay) marker list: `docs/plan_change_log_jarvis.md` Part 1.