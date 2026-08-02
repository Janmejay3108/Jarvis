"""Probe — same Keysight project key, real-workload Claude call.

The Keysight gateway's /anthropic path is FLAKY for real workloads:
trivial "say PONG" calls usually pass, but anything that looks like
production work (tool-use + a non-trivial prompt) intermittently returns
401 "invalid x-api-key" — even back-to-back with passing simple calls.

This script does what scripts/poc_dai.py does: forced tool-use on
claude-opus-4-7 with a small JSON payload as user content. Run it
several times; you will see PASS and FAIL responses with the same key.
"""

import json
import os

from anthropic import Anthropic, AnthropicError
from dotenv import load_dotenv

load_dotenv(override=True)

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    base_url="https://itga-ai-gateway.azure-api.net/anthropic",
)

# A small but realistic structured payload — closer to a real Jira fetch.
SAMPLE_JIRA = {
    "key": "TESTAUTOMA-8055",
    "fields": {
        "summary": "Change Scope: Due to column minimize issue, release was not able to identify",
        "description": "RUN ID: 30832\n\nTest Case: TESTAUTOMA_2941_113_ValidateHeaderConnectionForCALifecycleInAllstatesExcludingObsolete\n\nThe test failed because the Released state could not be located in the lifecycle column after a UI column minimize action. See attached DAI run.",
        "status": {"name": "Open"},
        "labels": ["ai-test", "regression"],
    },
}

TOOLS = [
    {
        "name": "submit_runid",
        "description": "Submit the extracted numeric DAI runid as a string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "runid": {"type": "string", "description": "Digits only."},
            },
            "required": ["runid"],
        },
    }
]

PROMPT = (
    "Extract the numeric DAI runid from the following Jira issue JSON and "
    "submit it via the submit_runid tool. The runid may appear anywhere "
    "in the response.\n\n"
    f"<<<JIRA_ISSUE>>>\n{json.dumps(SAMPLE_JIRA, indent=2)}\n<<<END>>>"
)

try:
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        tools=TOOLS,
        tool_choice={"type": "tool", "name": "submit_runid"},
        messages=[{"role": "user", "content": PROMPT}],
    )
    tool_input = next(
        (b.input for b in resp.content if b.type == "tool_use"),
        None,
    )
    print("RESULT     : PASS")
    print("provider   : Anthropic (Keysight gateway)")
    print("model      : claude-opus-4-7")
    print("tool_input :", tool_input)
    print("usage      :", resp.usage.input_tokens + resp.usage.output_tokens, "tokens")
except AnthropicError as e:
    print("RESULT     : FAIL")
    print("provider   : Anthropic (Keysight gateway)")
    print("model      : claude-opus-4-7")
    print("error      :", type(e).__name__, "-", e)
