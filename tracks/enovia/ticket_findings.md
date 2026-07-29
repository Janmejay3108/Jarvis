# ENOVIA TICKET FINDINGS — the manually executed tickets

**Author: (User) — Jay.** Schema and skeleton by the Agent; **the content is Jay's and only Jay's.**
**Status:** skeleton awaiting Jay's write-up of the 10–12 tickets already run.

---

## Why this file exists

Before JARVIS was built, Jay ran the **full diagnosis → fix → validate flow manually** against
**10–12 real Enovia tickets** — repo connected, real DAI error logs and screenshots supplied, fixes
validated, failures iterated on. That work is the strongest evidence the project has for engine fit,
and it is the reason plan0 A.10's base-rate **decision rule was retired** rather than run.

Right now it exists **only in one person's head.** This file is where it stops being a person-dependency
and becomes an asset. It feeds three things that are already designed to consume it:

| Consumer | What it takes from here | Where |
|---|---|---|
| **`context.md`'s ~20 fix patterns** | The root causes and fixes, grouped by failure family | plan0 **B.4 action 6** |
| **The eval set** | The **first rows** of `validation_tickets.json` | plan1 **§1.7.2** |
| **Few-shot exemplars + the flywheel** | *"What the model got wrong first, and what corrected it"* | plan1 §1.4.4 · plan4 §4.6.5 |

**This file is *evidence for* curation — never a substitute for it.** Megha's team still reviews what
lands in `context.md`.

**Fill in what you remember; leave blanks rather than guessing.** A half-filled real ticket is worth
more than a complete invented one. The single most valuable line is *"what the model got wrong first"* —
that is precisely the signal few-shot exemplar selection needs and the one nobody can reconstruct later.

---

## Schema — one section per ticket

```
## TESTAUTOMA-XXXX
- Failing test / suite:
- Symptom in the DAI log:
- Root cause (file + line + what was actually wrong):
- The fix that worked:
- What the model got wrong first, and what corrected it:   <- the most valuable line
- Failure family:
- Notes / gotchas:
```

**Field notes.**
- **Failing test / suite** — the suite that *owns the failing test*, which is the validation target
  (plan2 §2.5.0 `validation_suite_of`). Note it even when the fix landed in a shared handler; that
  divergence is exactly the case the resolution rule exists for.
- **Failure family** — one of the twelve in `plan_master` §3, or plan4's `flaky_oracle` /
  `change_scope` / `transient_flake`. "None of these" is a genuinely useful answer.
- **Notes / gotchas** — anything that would have saved you an hour.

---

## Tickets

> Replace this block with one section per ticket, using the schema above.

## TESTAUTOMA-XXXX
- Failing test / suite:
- Symptom in the DAI log:
- Root cause (file + line + what was actually wrong):
- The fix that worked:
- What the model got wrong first, and what corrected it:
- Failure family:
- Notes / gotchas:
