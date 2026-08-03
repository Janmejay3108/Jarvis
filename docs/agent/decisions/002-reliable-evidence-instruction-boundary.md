# Decision 002: Reliable Evidence, Separate Instruction Authority

## Status

Accepted on 2026-08-03 during review of Plan1 Step 1.1.2.

## Context

The architecture called Jira ticket text and production DAI logs "untrusted data." That phrase conflated two different questions:

1. Is the source provenance reliable?
2. Is every statement semantically accurate, current, relevant, and authorized to instruct the model?

Jira and production DAI are authenticated internal systems and are reliable evidence sources. Their content is not perfect: ticket descriptions and comments can be approximate or stale, one DAI run contains many irrelevant failures, and screenshots still require interpretation against logs and current source. Jay's operating estimate is that this content is often 70–80% accurate. This is a stakeholder estimate, not a measured Gate result.

The review also demonstrated that the first evidence-framing helper could turn an HTML-escaped end marker into a second active boundary and could erase angle-bracketed domain evidence.

## Decision

Use three independent properties:

- **Reliable provenance:** Jira and production DAI are authenticated internal evidence sources.
- **Semantic fallibility:** their content can be incomplete, stale, approximate, irrelevant, or inaccurate, so diagnosis corroborates ticket, logs, screenshot, and current source rather than trusting one item at 100%.
- **No instruction authority:** text contained in evidence never overrides system instructions, selects tools, or directs model behavior. It remains framed evidence even when it contains instruction-like prose.

Rename the control from "untrusted-data handling" to **evidence framing and instruction separation**. Keep delimiters, length caps, active-markup neutralization, prompt rules, and adversarial boundary tests. Framing must preserve domain evidence and guarantee embedded content cannot forge an active boundary.

Do not encode 70–80% as a confidence multiplier, threshold, or measured project claim. Gate 1 remains the place where diagnosis accuracy is measured with a point estimate and Wilson interval.

## Rejected Alternatives

- Treat reliable provenance as permission to follow embedded instructions: source authentication does not make every content author part of the model's instruction hierarchy.
- Remove framing because the systems are internal: accidental instruction-like text, stale comments, copied prompts, and forged delimiters remain possible without malicious intent.
- Continue calling the evidence "untrusted": technically defensible in security terminology, but misleading for this project's evidence-quality discussion.
- Assign a fixed 70–80% weight: the estimate is not a measured per-source calibration and would create false precision.

## Consequences

- Pipeline and prompt APIs use `frame_evidence_text` terminology.
- Prompts say the sources have reliable provenance but fallible content, and require corroboration.
- Model instructions embedded in evidence are ignored as instructions but retained as evidence.
- Plan Steward must align `plan_master` UP-14/Global Conventions item 5, Plan0's PoC wording, and Plan1's Step 1.1.2/prompt wording and tests in numbered pass 5. Plan2–Plan4 contain no conflicting evidence-trust definition.
- The Step 1.1.2 corrective build aligns `docs/context.md` §6.6 and invariant 11. The operating orientation contains no conflicting trust label. No source should describe the content as either wholly untrusted or 100% accurate.
