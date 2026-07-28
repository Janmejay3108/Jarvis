# PROGRESS

Running checklist. Append `[x] planN/phase/step — <date> — <one-line result>` after each step.

[x] plan0/0.A/A.0 — 2026-06-12 — PoC workspace scaffold created (scripts/, tracks/enovia/, samples/, tests/, .env.example, requirements-poc.txt, poc_results.md, .gitignore).
[x] plan0/0.A/A.1 — 2026-06-12 — scripts/poc_dai.py written; DAI auth + log + screenshot proven end-to-end on TESTAUTOMA-8055/runid 34156 (241 entries, image_id 1fece214... matches User example, screenshot 341,947 bytes saved). Jira REST v2 ticket fetch proven. AI-driven Jira→runid + error-match steps.
[x] plan0/0.A/A.1 — 2026-06-12 — Full pipeline closed: Jira→LLM→DAI→screenshot on TESTAUTOMA-8055. Run: runid=30832 extracted ('RUN ID: 30832' in description), 402 log entries, error index 384 ("Unable to Find Image (TEXT:\"Released\")"), image_id=465c0ecf... walk-back, 111,914-byte PNG saved.
[+] plan0/0.A/A.1 — 2026-06-12 — Added scripts/probe_gpt54.py + scripts/probe_claude.py as availability monitors. Gateway's /anthropic path behavior is flaky: started session 100% failing for all Claude requests; later passed simple probes but still failed inside poc_dai.py despite identical inline reproductions passing. Reverted poc_dai.py to gpt-5.4 (deviation note expanded in poc_results.md A.1).
[x] plan0/0.A/A.1 — 2026-06-12 — Root-caused the "gateway flakiness": (1) gateway whitelists claude-opus-4-5 + claude-opus-4-7 but NOT 4-6 (4-6 -> misleading 401); (2) python-dotenv doesn't override parent-shell env vars, so Claude Code's ANTHROPIC_BASE_URL=https://api.anthropic.com was silently masking the .env gateway URL. Fixed both: model -> claude-opus-4-7 (newer of the two whitelisted Opus IDs); load_dotenv(override=True) in all PoC scripts. poc_dai.py runs end-to-end on Anthropic Claude via Keysight gateway with the same correct result (runid 30832, error idx 384, 111 KB PNG). plan_master §6, plan0 A.0/A.1/A.8/B.1, plan1 §1.1.2/§1.2.3/§1.2.4, .env.example, .env, probe_claude.py all updated to claude-opus-4-7. plan files now ratify the LLM-reasoning approach for runid extraction + error-entry matching (was previously described as deterministic).


Conclusion: to use claude opus 4.7 for the agent.