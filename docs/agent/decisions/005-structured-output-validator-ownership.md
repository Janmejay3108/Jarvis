# Decision 005: Claude Client Owns Structured-Output Validation

## Status

Accepted on 2026-08-04 after review of Plan1 Step 1.2.4.

## Context

Plan1 Step 1.2.4 specifies this abbreviated client API:

```python
complete(
    system_blocks,
    messages,
    model=None,
    max_tokens=4096,
    tools=None,
    tool_choice=None,
    thinking=False,
    images=None,
) -> (response, usage)
```

The same step requires a forced tool call to return the tool input directly and
requires one automatic repair after Pydantic validation fails. The signature
does not provide the Pydantic model class that must perform that validation.
The JSON schema embedded in `tools` is an API request description; it cannot
recover the Python model class or execute its field and model validators.

The Step 1.2.4 brief completed that missing contract with an `output_model`
parameter. Commit `1f8836d` implements the brief and passed independent review:
255 tests passed, 2 pre-existing ripgrep skips remained, and repository Ruff
was clean.

## Decision

- Merge the reviewed Step 1.2.4 implementation unchanged. `output_model` is a
  necessary completion of the plan's stated behavior, not Builder scope creep.
- `tools[].input_schema` remains the schema sent to Anthropic. It does not own
  local runtime validation.
- `output_model: type[BaseModel]` owns local validation and JSON-compatible
  normalization through `model_validate(...)` followed by
  `model_dump(mode="json")`.
- `output_model` is required if and only if `tool_choice.type == "tool"`.
  Incoherent combinations fail before any HTTP request.
- A forced structured call returns the validated dictionary and aggregated
  usage. A non-structured call returns the full Anthropic message and usage.
- The one semantic repair boundary, transport retry boundary, and immediate
  per-response budget charge remain separate and unchanged.

## Required Plan Steward Pass

Update `plan1_diagnosis_and_chat.md` Step 1.2.4 in the next numbered plan pass:

- add `output_model=None` to the abbreviated `complete(...)` signature;
- state the conditional requirement for forced tool choice;
- distinguish the Anthropic request schema from the local Pydantic validator;
- specify the structured and unstructured return variants; and
- preserve the exactly-one semantic repair limit and its separation from
  transport retry and Plan2's three-attempt fix loop.

No implementation follow-up is required for this decision. No other plan file
currently defines a competing Claude client signature.

## Rejected Alternatives

- Remove `output_model` and trust the API's tool schema: this cannot execute
  Pydantic custom validators and contradicts the required repair-on-validation
  behavior.
- Reconstruct a Pydantic model from the JSON schema: this loses Python validator
  behavior, adds unnecessary runtime type generation, and creates a second
  schema authority.
- Move validation into every caller: this duplicates repair and accounting
  policy and prevents the client from returning a consistently validated
  structured result.
- Block or revise commit `1f8836d`: independent review found no build defect;
  changing correct code to match an incomplete signature would weaken the
  reasoning boundary.

## Consequences

- Diagnosis, extraction, and matching callers have one explicit way to bind an
  Anthropic tool schema to the Pydantic model that validates its response.
- Custom validators remain enforceable, including validators whose error text
  must be redacted before a repair prompt is built.
- The plan will describe the API that is already implemented and reviewed,
  without changing runtime behavior.