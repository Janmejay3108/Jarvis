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
[x] plan0/0.B/B.4b — 2026-07-28 — PartMaster onboarded to JARVIS. Registry row VERIFIED present in
    tracks/enovia/test_config_registry.yaml: suite_dir PartMaster.suite, model Part_Master_Pack_01,
    test_config_id 0310ac5d-c0c5-49dc-8b04-44c42a33d84e, dispatcher PartMaster_AgentDispatcher.script,
    smoke_target TestCases/TESTAUTOMA_6167_VerifyDownloadTemplateOptionFromPartMasterWidget.
    Remaining 16 suites tracked as open item O4.
[x] docs — 2026-07-28 — Plan set aligned to JARVIS: project renamed to JARVIS, executor renamed to Agent,
    practice terminology retired, validation flow integrated. See docs/plan_change_log_jarvis.md.
[x] repo — 2026-07-28 — Alignment pass 2. Repo FLATTENED to a single root (repo root == project root ==
    Bitbucket repo `jarvis`); the nested project directory is gone and all 13 entries moved as git renames,
    so history follows. Slug retired -> `jarvis` (repo, directory, pyproject name).
    tracks/enovia/test_config_registry.yaml CREATED with the proven PartMaster row (D3).
    Dispatcher template corrected to the script that actually ran (AgentDispatcher:-prefixed log lines).
    NEW safety rule: a changed file resolving to a suite absent from the registry is refused before any
    push or trigger and routed to diagnose-only. Markers closed: JARVIS DAI base URL, the eggptdai10
    two-row conflict, chat-app host, PartMaster TEST_CONFIG_ID, validation-repo PAT, branch prefix,
    repo slug, O6 policy, constraint C3. See docs/plan_change_log_jarvis_2.md.
[x] plan0/0.B/B.4b — 2026-07-30 — EngineeringCentral onboarded to JARVIS — the SECOND suite, and the one
    that owns TESTAUTOMA-8055's failing test, so the end-to-end golden path is now demonstrable (closes O9).
    Registry row: suite_dir EngineeringCentral.suite, model Engineering_Central_Pack_01,
    test_config_id 271b648a-a5e5-43ee-b4d8-24bab75da263,
    smoke_target TestCases/TESTAUTOMA_2941_113_ValidateHeaderConnectionForCALifecycleInAllstatesExcludingObsolete.
    NOTE: TESTAUTOMA_2941_... falls inside the 2864-2950 -> EngineeringCentral range in config/enovia.yaml.
    This is the FIRST live confirmation that the JIRA-number->suite ranges are real, which matters because
    they are BRANCH 2 of validation_suite_of (plan2 §2.5.0) — the fallback when the DAI log does not name
    the failing test. Two of seventeen suites onboarded; fifteen remain (O4).
[x] docs — 2026-07-30 — tracks/enovia/ context set committed: context.md core (249 lines / ~7.7K tokens)
    plus five triggered appendices, context_seed.md, and nine per-ticket findings files with the combined
    ticket_findings.md. Generated by a reasoning agent against the live Enovia repo, reviewed by Jay.
    Also docs/FINDINGS_for_JARVIS.md. See docs/plan_change_log_jarvis_4.md.

---

## OPEN ITEMS (O1–O12)

| ID | Status | Open item | Where it bites |
|---|---|---|---|
| **O1** | **open** | Webhook profile not yet registered on JARVIS. `poll_backoff` is the day-one completion mode; webhook is the upgrade path, not a prerequisite. **Nothing anywhere treats a webhook as a prerequisite:** `poll_backoff` is the *proven* day-one mode, and the webhook is a **latency upgrade Jay is testing in parallel** — it blocks nothing. | plan0 A.2 · plan2 §2.5.2 · plan4 §4.0 item 3 |
| **O2** | **open** | Suite-name collision behaviour as suites accumulate on the JARVIS instance — **constraint C2** (names must be globally unique per DAI instance). *Corrected 2026-07-28: this was previously mis-cited as C3; C3 is the one-repo-one-branch git-connection constraint.* Re-check at every onboarding. | plan0 B.4b · plan3 §3.7 |
| **O3** | **open** | Per-cycle validation wall-clock timing across a realistic suite set — not yet measured. Measurable only once the gate runs for real. | plan2 GATE 2 "avg fix+validation time" row |
| **O4** | **open — biggest scaling item** | Scale-out: **two of seventeen suites onboarded** (PartMaster 2026-07-28, EngineeringCentral 2026-07-30). **Fifteen remain**, each needing the full D2 onboarding sequence. This is still the single largest constraint on how much of the ticket flow JARVIS can serve. **A.10a's suite-frequency count exists to order the remaining fifteen** rather than onboarding them arbitrarily. | plan0 B.4b · plan0 A.10a · plan3 §3.7 |
| **O5** | ⚠️ **MITIGATED** (2026-07-28) | Force-push semantics vs. multi-suite dispatchers: force-pushing the full candidate state onto `Enovia` replaces the branch contents, so dispatchers for non-target suites disappear unless regenerated. **The mechanic still stands — it is neutralised, not removed, by the O6 rule.** Kept visible so nobody re-introduces a partial regeneration. | plan2 §2.5.0 |
| **O6** | ✅ **RESOLVED** (2026-07-28) | Every registered suite has its **own** `<Suite>_AgentDispatcher.script` **and its own test config**, which executes that suite's dispatcher. On **every** validation push, JARVIS regenerates the dispatcher for **every suite in the registry**, so the `Enovia` branch is always complete. **A rule, not a recommendation.** Consequence: a registered suite with no `smoke_target` is a hard error at onboarding time. | plan_master §2.3.2 D4 · plan2 §2.5.0 |
| **O7** | **open** | Monthly model re-import from the production DAI into JARVIS is an **undocumented manual activity** and must become a written procedure in `docs/maintenance.md`, performed by Jay every time. **Person-dependency.** | plan3 §3.7 |
| **O8** | **open** | The **≥50-ticket labelled set** is assembled at **Gate 1 scoring**, drawing on trajectory records accumulated during development — not as a separate pre-development labelling session. *Why 50 and not 12:* at n=12, 9 correct = 75% with a 95% Wilson CI of **[46.8, 91.1]** — an interval containing a coin flip, which cannot support a ≥75% claim to any reviewer. At n=50, 38 correct = 76% with CI **[62.6, 85.7]**. Gate 1 reports a point estimate **and** a CI; the dataset is what makes that number defensible. | plan0 A.10b · plan1 §1.7 GATE 1 |
| **O9** | ✅ **RESOLVED** (2026-07-30) | The **end-to-end golden path** needed the suite **owning TESTAUTOMA-8055's failing test** to be onboarded. That suite is **`EngineeringCentral`** (the fix lands in the shared handler `CommonEnovia.script:409`, which belongs to no suite — which is exactly why `validation_suite_of` resolves from the failing test, not the changed file). **EngineeringCentral is now onboarded and proven**: model `Engineering_Central_Pack_01`, test config `271b648a-a5e5-43ee-b4d8-24bab75da263`. The golden path is demonstrable. | plan0 B.4b · registry · O4 |
| **O10** | **open** | **EPF licence contention.** If the agent shares a floating pool with human testers, a validation run started when the pool is exhausted fails for reasons unrelated to the candidate fix. Such a failure **must be classified as infrastructure, never as a failed fix** — otherwise licence scarcity is indistinguishable from JARVIS producing bad patches, which is the worst possible misreading of a verdict. | plan2 §2.6 verdict classification · plan4 §4.2 |
| **O11** | **open** | **Agent identity.** JARVIS acts as **Jay**: PRs are authored as Jay and approved by someone else on the reviewing team, which satisfies the ≥1-approval rule. PR authorship, the audit trail and continuity across **token rotation or personnel change** therefore all depend on one person's credentials. Migration to a **Bitbucket/Jira service account** is a later migration, not a redesign, and should happen **before wider rollout**. Same person-dependency theme as **O7**. **Build nothing for it now.** | plan3 §3.7 · plan3 §3.9 |
| **O12** | ✅ **RESOLVED** (2026-07-29) | **Gate 0b's local/VM split.** Ruled by Jay: as written, Gate 0b required a provisioned VM and an on-VM smoke, so it could not pass until deployment — while gating plan1, which is built locally. **`GATE 0b-LOCAL` gates plan1; `GATE 0b-VM` gates deployment and plan3's rollout.** No checklist item was deleted or reworded; B.7 was not renumbered. | plan0 B.7a/B.7b · plan1 prereq · plan3 §3.7 |

> **Three questions remain open across the whole plan set** — O3 (real per-cycle timing), the model
> re-import runbook specifics, and O9's next-onboarding-target confirmation. The first two need something
> to actually run before they can be answered. Full list: `docs/plan_change_log_jarvis_3.md` Part 1.

---

## GATE 0a — PASSED (2026-07-29)

Gate 0a passes on **PoC 2 + PoC 5 + the JARVIS validation path (2b + A.2b)** — all proven.
**PoC 3** is **superseded** by B.4 (unit-tested modules, a stronger mechanism than a PoC).
**PoC 4**'s permissions half is already satisfied; its **API-shape** half is a cheap smoke test due
before plan3 §3.2. **PoC 7**'s decision rule is **retired** on the evidence of 10–12 manually executed
tickets; **A.10a** (suite-frequency count) is scheduled and **A.10b** (the ≥50 labelled set) is carried
as **O8** against Gate 1. **Phase 0.B may begin.** *(Ruled by Jay, 2026-07-28 / 2026-07-29.)*

[x] plan0/0.B/B.1 — 2026-08-02 — repo bootstrap: tree per master §4, pyproject (name=jarvis),
    config/enovia.yaml skeleton, .env.example. Repo-side actions (remote, default branch,
    approval rule, PAT) deferred per B.1 action 1.
[x] plan1/1.1/1.1.1 — 2026-08-03 — Run and step lifecycle models landed with persisted EventBus
    transitions and durable step-detail semantics; 51 tests passed, 2 skipped, and Ruff clean.
[x] plan1/1.1/1.1.2 — 2026-08-03 — Diagnosis pipeline landed with reliable-provenance evidence framing and instruction separation; Decision 004 follow-up added persisted/replayable Jira actions, independent single-attempt comment/label publication, safe action events, and non-terminal Jira degradation; 128 tests passed, 2 skipped, and Ruff clean.
[x] plan1/1.1/1.1.3 — 2026-08-03 — Per-track FIFO diagnosis queues and native cross-process validation locks landed; 95 tests passed, 2 skipped, and Ruff clean.
[x] plan1/1.2/1.2.1 — 2026-08-03 — Jira DC REST v2 client hardened with retry-safe reads, single-attempt uncertain writes, complete REST surface validation, and persisted reconciliation design; 119 tests passed, 2 skipped, and Ruff clean.
[x] plan1/1.2/1.2.2 — 2026-08-04 — Read-only Bitbucket Server/DC client landed with encoded raw-file reads, server-driven pagination, retry-safe reads, lifecycle ownership, and malformed-response validation; 147 tests passed, 2 skipped, and Ruff clean.