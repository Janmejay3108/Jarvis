"""PoC 2 — DAI evidence by runid (Step A.1 of plan0).

End-to-end pipeline:
  1. Take a Jira ticket key (default: TESTAUTOMA-8055).
  2. Fetch the Jira issue via REST v2 (bearer PAT).
  3. Use the LLM to extract the DAI runid + title + description from the
     response (runid may appear anywhere — description, custom field, etc.).
  4. Authenticate to DAI via OAuth2 client_credentials -> access_token.
  5. GET /ai/runlogs/{runid} -> ordered list of log entries.
  6. Use the LLM to identify the SINGLE log entry whose `message` matches the
     failure described in the Jira ticket.
  7. Walk backward from that entry to find the most recent entry whose
     `image_id` is non-null (the user-captured screenshot just before the
     failure — Eggplant captures, then acts).
  8. GET /api/v2/screenshots/{image_id} -> save the PNG to disk.

LLM provider: Anthropic claude-opus-4-7
 via the Keysight AI gateway
(`https://itga-ai-gateway.azure-api.net/anthropic`).

NOTE — plan_master.md §6 mandates `claude-opus-4-6`. The Keysight gateway
whitelists `claude-opus-4-7` (not 4-6) — requests for 4-6 return a
misleading `401 invalid x-api-key` (upstream rejects on the model, not
the key). 4-7 is the same Opus family one minor version newer, so this
is a small, documented deviation: update `plan_master.md` §6 + the
config when convenient.

Run:  python scripts/poc_dai.py [TESTAUTOMA-####]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

ROOT = Path(__file__).resolve().parent.parent
# override=True so the project's .env wins over any parent-shell env vars
# (Claude Code's parent shell sets ANTHROPIC_BASE_URL=https://api.anthropic.com,
# which otherwise silently overrides our Keysight-gateway base URL).
load_dotenv(ROOT / ".env", override=True)

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_PAT = os.environ["JIRA_PAT"]

DAI_AUTH_URL = os.environ["DAI_AUTH_URL"]
DAI_CLIENT_ID = os.environ["DAI_CLIENT_ID"]
DAI_CLIENT_SECRET = os.environ["DAI_CLIENT_SECRET"]
DAI_LOG_BY_RUNID_URL = os.environ["DAI_LOG_BY_RUNID_URL"]
DAI_SCREENSHOT_URL = os.environ["DAI_SCREENSHOT_URL"]

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_BASE_URL = (
    os.environ.get("ANTHROPIC_BASE_URL")
    or "https://itga-ai-gateway.azure-api.net/anthropic"
)
MODEL = os.environ.get("MODEL", "claude-opus-4-5")

EVIDENCE_DIR = ROOT / "data" / "poc2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


def _llm() -> Anthropic:
    """Build the Anthropic client pointed at the Keysight gateway."""
    return Anthropic(
        api_key=ANTHROPIC_API_KEY,
        base_url=ANTHROPIC_BASE_URL,
    )


def _call_tool(
    user_prompt: str, tool_name: str, tool_schema: dict, system: str | None = None
) -> dict:
    """Single forced tool-call round-trip; returns the tool arguments as a dict.

    Uses Claude's forced tool-use (`tool_choice={"type":"tool","name":...}`)
    so the model must respond by calling the named tool with structured JSON.
    """
    kwargs: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": 2048,
        "tools": [
            {
                "name": tool_name,
                "description": tool_schema.get("description", ""),
                "input_schema": tool_schema["parameters"],
            }
        ],
        "tool_choice": {"type": "tool", "name": tool_name},
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if system:
        kwargs["system"] = system

    resp = _llm().messages.create(**kwargs)
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool_name:
            return dict(block.input)  # type: ignore[arg-type]
    raise RuntimeError(f"Model did not return a tool call for {tool_name}")


async def fetch_jira_issue(ticket_key: str) -> dict:
    """Jira DC REST v2: GET /rest/api/2/issue/{key}."""
    url = f"{JIRA_BASE_URL}/rest/api/2/issue/{ticket_key}"
    headers = {"Authorization": f"Bearer {JIRA_PAT}", "Accept": "application/json"}
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()


def extract_ticket_metadata(issue: dict) -> dict[str, Any]:
    """Use the LLM to extract runid + title + description from the Jira issue.

    The runid may live in any field (description, summary, a custom field,
    a comment). The model reads the issue JSON and replies via a forced
    tool call so we get a guaranteed JSON shape.
    """
    issue_json = json.dumps(issue, default=str)
    if len(issue_json) > 120_000:
        issue_json = issue_json[:120_000] + "... [truncated]"

    schema = {
        "description": (
            "Submit the DAI test run id, ticket title, description and "
            "test script name extracted from a Jira issue REST response."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "runid": {
                    "type": "string",
                    "description": (
                        "The DAI test run id as a string of digits. "
                        "Search EVERY field of the response — description, "
                        "summary, custom fields, comments, attachments — "
                        "for a numeric run identifier. If the response "
                        "contains a phrase like 'runid 34156', "
                        "'Run ID: 34156', or 'testrunid=34156', return "
                        "'34156'. If you cannot find one, return an "
                        "empty string."
                    ),
                },
                "title": {
                    "type": "string",
                    "description": "The Jira issue summary (title).",
                },
                "description": {
                    "type": "string",
                    "description": (
                        "The Jira issue description converted to plain "
                        "text (strip wiki markup but keep the meaning)."
                    ),
                },
                "test_script_name": {
                    "type": "string",
                    "description": (
                        "The name of the failing Eggplant/SenseTalk test "
                        "script or test case. Look for tokens like "
                        "'TESTAUTOMA_2941_113_ValidateHeader...', "
                        "'Test Case: <name>', a '*.script' filename, or a "
                        "test-case identifier anywhere in the response "
                        "(description, summary, custom fields, comments). "
                        "Return the most specific test/script name you find, "
                        "verbatim. If none is present, return an empty string."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "One or two short sentences explaining where you "
                        "found the runid and the test_script_name (which "
                        "field/phrase each came from)."
                    ),
                },
            },
            "required": [
                "runid",
                "title",
                "description",
                "test_script_name",
                "reasoning",
            ],
        },
    }

    prompt = (
        "You are reading a Jira REST API v2 issue response for an Eggplant "
        "DAI test failure. Extract four things and submit them via the "
        "submit_ticket_metadata tool:\n"
        "  1) runid — the numeric DAI test run identifier; it can appear "
        "in description text, a custom field, summary, or comments — "
        "search exhaustively;\n"
        "  2) title — the issue summary;\n"
        "  3) description — the issue description as plain text;\n"
        "  4) test_script_name — the failing test/script name (e.g. a "
        "'TESTAUTOMA_<num>_<...>' identifier or a '*.script' filename) "
        "found anywhere in the response.\n\n"
        f"<<<JIRA_ISSUE_JSON>>>\n{issue_json}\n<<<END_JIRA_ISSUE_JSON>>>"
    )

    return _call_tool(prompt, "submit_ticket_metadata", schema)


async def get_dai_token() -> str:
    """OAuth2 client_credentials -> access_token."""
    data = {
        "grant_type": "client_credentials",
        "client_id": DAI_CLIENT_ID,
        "client_secret": DAI_CLIENT_SECRET,
    }
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        r = await client.post(
            DAI_AUTH_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return r.json()["access_token"]


async def fetch_log(runid: str, token: str) -> list[dict]:
    """GET /ai/runlogs/{runid} -> list of log entry objects."""
    url = DAI_LOG_BY_RUNID_URL.format(runid=runid)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        payload = r.json()
    if isinstance(payload, list):
        return payload
    for key in ("logs", "events", "items", "data", "results"):
        if isinstance(payload, dict) and isinstance(payload.get(key), list):
            return payload[key]  # type: ignore[no-any-return]
    raise RuntimeError(
        f"Unexpected DAI runlogs response shape; top-level type={type(payload).__name__}"
    )


def find_error_log_index(
    logs: list[dict], title: str, description: str
) -> tuple[int, str]:
    """Use the LLM to pick the log entry whose message matches the Jira issue.

    Returns (index, reasoning).
    """
    compact = [
        {
            "i": idx,
            "type": e.get("message_type"),
            "sev": e.get("severity"),
            "msg": e.get("message"),
        }
        for idx, e in enumerate(logs)
        if (e.get("message") or "").strip()
    ]
    body = json.dumps(compact, default=str)
    if len(body) > 150_000:
        # keep the tail — failures are almost always near the end
        compact = compact[-1500:]
        body = json.dumps(compact, default=str)

    schema = {
        "description": (
            "Submit the index of the SINGLE log entry whose `message` "
            "best matches the failure described in the Jira ticket."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": (
                        "The `i` field of the matching log entry from "
                        "the LOG_ENTRIES array."
                    ),
                },
                "matched_message": {
                    "type": "string",
                    "description": "The matched entry's `msg` text, verbatim.",
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "One or two sentences explaining the semantic "
                        "link between the Jira issue and this log entry."
                    ),
                },
            },
            "required": ["index", "matched_message", "reasoning"],
        },
    }

    prompt = (
        "A Jira ticket reports an Eggplant DAI test failure. Below is the "
        "JSON description of the ticket followed by a JSON list of log "
        "entries from the failing run. Each entry has fields: i (index in "
        "the full log), type (Eggplant message_type), sev (severity), "
        "msg (the human-readable message).\n\n"
        "Identify the SINGLE log entry whose `msg` best matches the failure "
        "described by the ticket. Look for image / text lookups that failed "
        "(e.g. messages like 'Unable to Find Image (TEXT:\"...\")', "
        "'Text not found', 'Object not found', etc.) and align the keyword "
        "in the message with the keyword the ticket says could not be "
        "found. Pick the FIRST such failure if multiple exist.\n\n"
        f"JIRA_TITLE: {title}\n"
        f"JIRA_DESCRIPTION:\n{description}\n\n"
        f"<<<LOG_ENTRIES>>>\n{body}\n<<<END_LOG_ENTRIES>>>\n\n"
        "Call submit_error_index with the matching entry's `i` value."
    )

    args = _call_tool(prompt, "submit_error_index", schema)
    return int(args["index"]), str(args.get("reasoning", ""))


def _first_failure_index(logs: list[dict]) -> int:
    """Deterministic fallback when Claude is unavailable.

    Eggplant emits a row with `message_type == "imagefound"` for every
    image / text lookup. Successful lookups have a benign message; failed
    lookups carry "Unable to Find" or "not found". We scan in order and
    return the first such failure — which is almost always the proximate
    cause for a single-failure test.
    """
    for i, e in enumerate(logs):
        mtype = (e.get("message_type") or "").lower()
        msg = (e.get("message") or "").lower()
        if mtype == "imagefound" and ("unable to find" in msg or "not found" in msg):
            return i
    for i, e in enumerate(logs):
        msg = (e.get("message") or "").lower()
        if "unable to find image" in msg or "exception" in msg:
            return i
    return len(logs) - 1


def find_last_screenshot_before(logs: list[dict], error_index: int) -> dict | None:
    """Walk back from error_index toward 0; return the first entry whose
    image_id is a non-null, non-empty string. Eggplant captures the screen,
    then acts — so the screenshot just BEFORE the failure is the one we want.
    """
    for i in range(error_index - 1, -1, -1):
        e = logs[i]
        image_id = e.get("image_id")
        if image_id and str(image_id).lower() not in ("null", "none", ""):
            return e
    return None


async def fetch_screenshot(image_id: str, token: str, dest: Path) -> int:
    """GET /api/v2/screenshots/{image_id} -> write bytes to dest."""
    url = DAI_SCREENSHOT_URL.format(image_id=image_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return len(r.content)


async def run(ticket_key: str, runid_override: str | None = None) -> int:
    console.rule(f"[bold cyan]PoC 2 — DAI evidence by runid[/]  ticket={ticket_key}")

    title = ""
    description = ""
    test_script_name = ""
    runid = (runid_override or "").strip()

    if runid:
        console.print(f"[1-2/7] Skipping Jira+LLM — using --runid {runid}", style="yellow")
    else:
        console.print("[1/7] Fetching Jira issue...", style="bold")
        issue = await fetch_jira_issue(ticket_key)
        console.print(f"      OK — key={issue.get('key')}")

        console.print("[2/7] Asking the LLM to extract runid + title + description + test_script_name...", style="bold")
        meta = extract_ticket_metadata(issue)
        runid = (meta.get("runid") or "").strip()
        title = meta.get("title") or ""
        description = meta.get("description") or ""
        test_script_name = meta.get("test_script_name") or ""
        console.print(f"      runid        : {runid or '[red]<not found>[/]'}")
        console.print(f"      title        : {title}")
        console.print(f"      test_script  : {test_script_name or '[yellow]<none>[/]'}")
        short_desc = description if len(description) <= 240 else description[:240] + "..."
        console.print(f"      description  : {short_desc}")
        console.print(f"      reasoning    : {meta.get('reasoning', '')}")
        if not runid:
            console.print("[red]No runid found in the Jira issue. Aborting.[/]")
            return 2

    console.print("[3/7] Authenticating to DAI (OAuth2 client_credentials)...", style="bold")
    token = await get_dai_token()
    console.print(f"      OK — token len={len(token)} chars")

    console.print(f"[4/7] Fetching run logs for runid={runid}...", style="bold")
    logs = await fetch_log(runid, token)
    console.print(f"      OK — {len(logs)} log entries")

    console.print("[5/7] Asking the LLM to identify the matching error entry...", style="bold")
    if runid_override:
        console.print("      Skipped (no Jira context); falling back to first failure marker.", style="yellow")
        error_idx = _first_failure_index(logs)
        reasoning = "deterministic fallback: first entry whose message contains a known failure keyword"
    else:
        error_idx, reasoning = find_error_log_index(logs, title, description)
    error_entry = logs[error_idx]
    error_msg = error_entry.get("message", "")
    console.print(f"      index       : {error_idx}")
    console.print(f"      message     : {error_msg}")
    console.print(f"      reasoning   : {reasoning}")

    console.print("[6/7] Walking back to the last captured screenshot...", style="bold")
    shot = find_last_screenshot_before(logs, error_idx)
    if shot is None:
        console.print("[red]No screenshot found before the error entry.[/]")
        return 3
    image_id = str(shot["image_id"])
    console.print(f"      image_id    : {image_id}")
    console.print(f"      image_name  : {shot.get('image_name')}")

    console.print("[7/7] Downloading screenshot...", style="bold")
    dest = EVIDENCE_DIR / f"{ticket_key}_runid-{runid}_{image_id}.png"
    n = await fetch_screenshot(image_id, token, dest)
    console.print(f"      saved       : {dest} ({n:,} bytes)")

    console.print(
        Panel.fit(
            "\n".join(
                [
                    f"ticket        : {ticket_key}",
                    f"runid         : {runid}",
                    f"test_script   : {test_script_name or '<none>'}",
                    f"log_row_count : {len(logs)}",
                    f"error_index   : {error_idx}",
                    f"error_message : {error_msg}",
                    f"image_id      : {image_id}",
                    f"screenshot    : {dest}",
                ]
            ),
            title="[bold green]SUMMARY[/]",
            border_style="green",
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PoC 2 — DAI evidence by runid")
    parser.add_argument(
        "ticket",
        nargs="?",
        default="TESTAUTOMA-8055",
        help="Jira ticket key (e.g. TESTAUTOMA-8055)",
    )
    parser.add_argument(
        "--runid",
        default=None,
        help=(
            "Skip the Jira+LLM metadata step and feed runid directly. "
            "Useful for validating the DAI half of the flow when LLM "
            "credentials are unavailable."
        ),
    )
    args = parser.parse_args()
    return asyncio.run(run(args.ticket, runid_override=args.runid))


if __name__ == "__main__":
    sys.exit(main())
