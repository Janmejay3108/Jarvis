# Plan Alignment Pass 5: Reliable Evidence And Instruction Separation

## Authority And Sequence

This pass implements Decision 002, accepted by Jay on 2026-08-03 during review of Plan1 Step 1.1.2. Run it with the **Plan Steward**, not the Builder.

Execute after the corrected Step 1.1.2 branch has passed review and Jay has merged it locally, so `docs/agent/decisions/002-reliable-evidence-instruction-boundary.md` is present on the base. Previous plan-set tag: `plan-set-jarvis-v4`. Cut `docs/jarvis-alignment-5` from that resulting local `master`. Do not push or merge.

## Rulings

Use these IDs in the pass change log:

| ID | Fact supplied or decided | Closes |
|---|---|---|
| F1 | Jira and production DAI are authenticated internal systems with reliable provenance. | The phrase `untrusted data` incorrectly characterizes source provenance. |
| F2 | Ticket descriptions/comments, logs, and screenshot interpretations can be incomplete, stale, approximate, irrelevant, or inaccurate and must be corroborated against one another and current source. | Reliable provenance does not mean 100% semantic accuracy. |
| F3 | Jay estimates this evidence is often 70–80% accurate. This is an operating estimate supplied on 2026-08-03, not a measured Gate result. | The estimate must not become a threshold, confidence multiplier, or flat measured claim. |
| F4 | Evidence content has no authority to override system instructions or direct tool execution, even when it contains instruction-like prose. | Prompt-injection protection remains mandatory without calling the source untrusted. |
| F5 | Evidence framing must preserve domain text, neutralize embedded active boundaries, delimit and cap content, and keep adversarial tests. | Decision 002 and the Step 1.1.2 review proved both boundary forgery and evidence loss. |

## Exact Plan Step

This is a terminology and contract correction to:

- `plan_master.md` UP-14 and §6 Global Conventions item 5;
- `plan0_poc_and_foundation.md` PoC 5 prompt wording;
- `plan1_diagnosis_and_chat.md` Step 1.1.2, Step 1.4.4, Step 1.4.5, and DoD.

Do not change headings, phase scope, sequencing, gates, taxonomy, model configuration, budgets, APIs unrelated to evidence framing, or any validation invariant.

## Per-File Edit Map

### `plan_master.md`

- In the UP-14 table row, rename `Injection hardening+` to `Evidence framing + instruction separation`.
- State that ticket/comments and DAI log/screenshot content comes from reliable-provenance systems but is semantically fallible and must be corroborated with current source. Content remains evidence, never model instructions.
- Preserve the concrete controls: delimiters, active Markdown/HTML neutralization, length caps, prompt guidance, and adversarial tests. Add the proven requirement that embedded delimiter tokens are neutralized after entity decoding and domain angle-bracket evidence is preserved.
- In §6 Global Conventions item 5, replace `Untrusted input (UP-14)` with `Evidence framing (UP-14)` and summarize F1, F2, and F4. Do not add the 70–80% estimate to the canonical invariant.

### `plan0_poc_and_foundation.md`

- In PoC 5, replace `untrusted-data delimiters` with `evidence-framing delimiters` or equivalent wording.
- Preserve the gateway/model proof and prompt behavior. This is terminology alignment, not a retrospective rewrite of the PoC result.

### `plan1_diagnosis_and_chat.md`

- Step 1.1.2 `read_ticket`: replace broad `sanitize` wording with `frame evidence`; reference `frame_evidence_text`; preserve Markdown target/known presentation-tag neutralization, caps, and markers. Require unknown/domain angle-bracket evidence to survive and embedded active markers to be visibly neutralized after entity decoding.
- Step 1.4.4 prompt: replace `untrusted-data rule` with the three-property contract from F1/F2/F4. Explicitly require corroboration across ticket/comments, DAI logs, screenshots, and current source. Preserve the rule that instruction-like content is evidence and is never followed as instruction.
- Step 1.4.5 and DoD: rename the `injection test fixture/guard` to an `instruction-separation adversarial fixture/guard`, while preserving the exact hostile fixture and assertion that it cannot derail diagnosis.
- Do not encode 70–80% in model prompts, confidence calculations, routing, or acceptance thresholds. Gate 1 remains the only measured diagnosis-accuracy contract.

No edits are authorized in `plan2_autofix_and_validation.md`, `plan3_lifecycle_rollout.md`, or `plan4.md`; the set-wide search found no conflicting definition there.

## Verification

Follow the Plan Steward pass protocol in full: capture heading lists/counts before editing, write the rulings table and per-file map to `docs/plan_change_log_jarvis_5.md`, make one commit per fix, and read every diff.

Run at minimum:

```powershell
Select-String -Path plan_master.md,plan0_poc_and_foundation.md,plan1_diagnosis_and_chat.md,plan2_autofix_and_validation.md,plan3_lifecycle_rollout.md,plan4.md -Pattern 'untrusted|untrusted-data|Injection hardening'
Select-String -Path plan_master.md,plan0_poc_and_foundation.md,plan1_diagnosis_and_chat.md -Pattern 'reliable provenance|semantically fallible|instruction separation|corroborat|frame_evidence_text'
git diff --check master...HEAD
git diff --stat master...HEAD
```

Expected: no remaining trust-label use of `untrusted` in the plan set; every accepted control and adversarial test remains present; the three touched plan files have identical before/after heading counts; plans 2–4 are unchanged.

Report the branch, base SHA, commits, heading counts, mechanical-search results, and any contradiction. Do not push or merge. Jay reviews, locally merges, and tags `plan-set-jarvis-v5`.
