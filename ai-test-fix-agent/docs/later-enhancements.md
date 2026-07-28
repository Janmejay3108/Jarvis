# JARVIS — LATER ENHANCEMENTS (deliberately deferred)

**Last updated:** 2026-07-28

Everything in this file is **out of scope for this version** and **required by no gate**. Nothing here
is cancelled — each item is retained in the plan set in full, with a `*(DEFERRED …)*` marker at its
original step number, so it can be revived without re-deriving the design.

The distinction that matters: **deferred ≠ deleted ≠ open item.**
- **Deferred** (this file) — designed, documented, consciously not built now.
- **Open item** (`PROGRESS.md`, O1–O7) — needed for the current version, not yet resolved.
- **Out of scope** (plan3 tail, plan4 tail) — decided *against*, do not reintroduce.

---

## 1. Local EPF `runscript` inner loop — the latency optimisation

**Where it lives in the plan set:** plan0 A.3 (PoC 1), A.4 (PoC 1b), A.5 (PoC 1e); plan2 Phase 2.4
(`src/integrations/epf_runner.py`). All four retained in full, all four marked DEFERRED.

**What it is.** A fast, local validation tier: instead of pushing to the validation repo and waiting
20 min–2 hr for a JARVIS DAI run, invoke Eggplant Functional's `runscript.bat` directly on the runner
VM against the local working copy, and read the exit code plus the results folder.

**Why it is deferred.** JARVIS is now the **single mandated validation mechanism** (plan_master §2.1,
§2.3) and it is proven end-to-end. The original plan hedged across two mechanisms behind an
`INNER_LOOP` flag precisely because neither was proven; that hedge is no longer needed. The flag is
retired in favour of `VALIDATION_MECHANISM=jarvis-dai`.

**What it would buy.** Per-attempt latency. The JARVIS gate is production-fidelity but slow; a local
pre-filter could reject obviously-broken candidates in minutes rather than hours, before the SUT lock
is taken.

**What it must never become.** A *substitute* for the JARVIS gate. If revived, it is a **pre-filter in
front of** the authoritative oracle, never in place of it — a fix that passes locally but was never
validated on the real SUT must not reach a PR. The original plan2 §2.6 design already had this shape
(`runscript` fast, gate authoritative); reviving it means restoring that two-tier arrangement, not
re-branching the controller.

**Prerequisites if revived:**
- A.4 must first establish whether `runscript` can bring up the RDP SUT connection without DAI
  injecting it — the open question that stalled it originally.
- A.5 must establish `runscript` ≡ DAI parity, or enumerate the DAI-supplied params to pass through.
- The `validating_local` member of `RunStatus` (plan1 §1.1.1) is **already reserved** for this and was
  deliberately not removed.

---

## 2. Webhook completion mode (open item O1 — the upgrade path)

**Where it lives:** plan0 A.2 option 1; plan2 §2.5.2 `completion_mode: webhook`.

`poll_backoff` is the day-one mode and is sufficient. The webhook path is **available** — the webhooks
admin UI exists on JARVIS and Jay is admin — but the profile is **not yet registered**.

Upgrading means: create the custom-HTTP webhook profile in *System → Webhooks*, point it at
`POST /api/webhooks/dai`, verify the shared secret, and confirm how the payload correlates back to the
triggered run (a run identifier if exposed; otherwise `result-url` or test-config name + last-triggered
record). The orchestrator then awaits an `asyncio.Event` instead of polling — zero HTTP calls and zero
compute while waiting. **No code path is removed by this upgrade**; all three completion modes stay.

---

## 3. Additional SUTs on JARVIS test configs

**Current state — knowledge only, no action required.** The SUT `Jay_130` is registered by hostname +
RDP credentials and is **already bound to the test configs that will be triggered**. There is nothing
for the Agent to set up, and the SUT connection remains a **manual, Jay-maintained** arrangement.

**Later:** more SUTs will be added to some test configs on the JARVIS DAI. This is a (User) task on the
DAI side. When it happens, note that plan_master §6.8's concurrency truth — *one SUT, one test at a
time, `max-parallel: 1`, one dedicated EPF floating license* — is what currently justifies the
single per-track lock. **Adding SUTs is therefore not purely additive**: if genuine parallel execution
becomes possible, the locking model and the license reservation both need revisiting before any
concurrency is enabled. Do not assume more SUTs automatically means more throughput.

---

## 4. Scale-out to the remaining suites (open item O4)

Only `Part_Master_Pack_01` / PartMaster is onboarded. Each remaining suite of the 17+ needs the full
D2 sequence in plan0 §B.4b — export model from production DAI, import to JARVIS, verify suite
association, create the dispatcher script, author the model action and test case, create the
model-based test config, record `TEST_CONFIG_ID` in the registry, smoke run, re-check O2.

This is **(User) work on the DAI side** and is the main gating factor on how much of the ticket flow
JARVIS can actually serve. The "automatable share" trend in plan4 §4.8.1 is the metric that makes the
cost of *not* doing it visible.

---

## 5. Things explicitly decided against — do NOT revive from this file

Listed here only so they are not mistaken for deferrals. See plan3 and plan4 tails for the reasoning.

- **Vector DB / embeddings** — revisit only inside UP-11 retrieval once ≥10 real trajectories exist and
  the lexical scorer measurably misses.
- **Fine-tuning** — only after a measured prompting ceiling and hundreds of verified pairs.
- **tree-sitter SenseTalk grammar** — no public grammar exists; regex + vocabulary + the targeted
  plan4 §4.6.3 rule is the correct 80/20 at this repo size.
- **External tracing stack** — the events table + persisted transcripts already are the trace.
- **@mention / comment-webhook summoning** — manual convention in the rollout contract only.
- **SharePoint / Azure AD / Microsoft Graph** — formally dropped; evidence comes from DAI + Jira.
- **Multi-track expansion** (Oracle GBS, SCC, SF Sales, KCOM, RevPro, ETC) — later playbook.
