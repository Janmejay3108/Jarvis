# `docs/agent/` — the agent workspace

Working artifacts produced by the custom agents in `.github/agents/`. Nothing here is shipped
code; it is the paper trail of how the code got decided.

```
briefs/     <step>-<slug>.md          Architect → Builder. The specification for one build step.
reviews/    <step>-<slug>-review.md   Reviewer's findings, when a written record is wanted.
decisions/  NNN-<slug>.md             A decision, what it rejected, and why.
```

## The loop

1. **Architect** — Jay discusses the next step, the Architect researches and writes the brief.
2. **Builder** — executes the brief on `build/<step>-<slug>`. One commit. No push, no merge.
3. **Reviewer** — verifies the branch independently. Read-only, so findings surface instead of
   getting quietly patched.
4. **Jay** — decides, merges, pushes.

**Plan Steward** runs out-of-band whenever corrections need folding back into `plan0`–`plan4`.
Collect plan defects as they are found and fold them in as one numbered pass rather than patching
one at a time.

## When to write a decision record

When a choice closes off an alternative someone will later be tempted to reopen. Record what was
decided, what was rejected, and **why** — the reasoning is the part that has to survive, because
the decision alone reads as arbitrary six weeks later and gets relitigated.

Examples worth having written down: why validation force-pushes one permanent branch instead of a
branch per ticket; why retrieval is lexical rather than embeddings; why the validation suite is
the owner of the failing test rather than the owner of the changed file.
