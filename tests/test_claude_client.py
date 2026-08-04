from __future__ import annotations

import json
import warnings
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest
from pydantic import BaseModel, SecretStr, field_validator
from pytest_httpx import HTTPXMock
from structlog.testing import capture_logs
from tenacity import wait_none

import src.integrations.claude_client as claude_module
from src.integrations.claude_client import (
    CachedSystemSource,
    ClaudeClient,
    ImageInput,
    StructuredOutputError,
    build_cached_system,
)
from src.orchestrator.track_loader import load_track
from src.utils.budget import BudgetExceeded, BudgetGuard

BASE_URL = "https://claude.test/anthropic"
MESSAGES_URL = f"{BASE_URL}/v1/messages"
MODEL = "claude-opus-4-7"
TOOLS = [
    {
        "name": "submit_result",
        "description": "Submit a typed result.",
        "input_schema": {
            "type": "object",
            "properties": {"value": {"type": "integer"}},
            "required": ["value"],
        },
    }
]
TOOL_CHOICE = {"type": "tool", "name": "submit_result"}


class ResultModel(BaseModel):
    value: int


class SecretResultModel(BaseModel):
    value: str


class LeakyValidatorModel(BaseModel):
    value: str

    @field_validator("value")
    @classmethod
    def reject_secret(cls, value: str) -> str:
        if value.startswith("REPAIR_SECRET"):
            raise ValueError(f"rejected payload: {value}")
        return value


def _settings(**overrides: Any) -> SimpleNamespace:
    values = {
        "anthropic_api_key": SecretStr("test-api-key"),
        "anthropic_base_url": BASE_URL,
        "model": MODEL,
        "budget_usd_per_run": 10.0,
        "track": load_track(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _message(
    *,
    content: list[dict[str, Any]] | None = None,
    input_tokens: int = 10,
    output_tokens: int = 5,
    cache_creation_input_tokens: int | None = 0,
    cache_read_input_tokens: int | None = 0,
    model: str = MODEL,
) -> dict[str, Any]:
    usage: dict[str, Any] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    if cache_creation_input_tokens is not None:
        usage["cache_creation_input_tokens"] = cache_creation_input_tokens
    if cache_read_input_tokens is not None:
        usage["cache_read_input_tokens"] = cache_read_input_tokens
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content or [{"type": "text", "text": "done"}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": usage,
    }


def _tool_message(value: Any, *, tool_id: str = "toolu_1") -> dict[str, Any]:
    return _message(
        content=[
            {"type": "thinking", "thinking": "summary", "signature": "sig"},
            {"type": "text", "text": "submitting"},
            {
                "type": "tool_use",
                "id": tool_id,
                "name": "submit_result",
                "input": {"value": value},
            },
        ]
    )


def _add_message(httpx_mock: HTTPXMock, payload: dict[str, Any] | None = None) -> None:
    httpx_mock.add_response(
        method="POST",
        url=MESSAGES_URL,
        json=payload or _message(),
    )


def _add_error(httpx_mock: HTTPXMock, status_code: int, message: str = "failed") -> None:
    error_types = {
        400: "invalid_request_error",
        401: "authentication_error",
        403: "permission_error",
        404: "not_found_error",
        429: "rate_limit_error",
        500: "api_error",
        504: "timeout_error",
        529: "overloaded_error",
    }
    httpx_mock.add_response(
        method="POST",
        url=MESSAGES_URL,
        status_code=status_code,
        json={
            "type": "error",
            "error": {"type": error_types[status_code], "message": message},
            "request_id": "req_test",
        },
    )


def _client(
    *,
    settings: SimpleNamespace | None = None,
    guard: BudgetGuard | None = None,
) -> ClaudeClient:
    client = ClaudeClient(config=settings or _settings(), budget_guard=guard)
    client._retry_wait = wait_none()
    return client


@pytest.mark.asyncio
async def test_owned_sdk_construction_and_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeSdk:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(claude_module, "AsyncAnthropic", FakeSdk)
    client = ClaudeClient(config=_settings())

    async with client as entered:
        assert entered is client

    assert captured == {
        "api_key": "test-api-key",
        "base_url": BASE_URL,
        "max_retries": 0,
    }
    assert client._client.closed is True


@pytest.mark.asyncio
async def test_injected_client_is_not_closed() -> None:
    injected = SimpleNamespace(closed=False)

    async def close() -> None:
        injected.closed = True

    injected.close = close
    client = ClaudeClient(config=_settings(), client=injected)

    await client.aclose()

    assert injected.closed is False


@pytest.mark.asyncio
async def test_plain_completion_uses_config_and_returns_full_message(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock)
    system = [{"type": "text", "text": "system"}]
    messages = [{"role": "user", "content": "hello"}]

    async with _client() as client:
        response, usage = await client.complete(system, messages, max_tokens=123)

    request = httpx_mock.get_request()
    body = json.loads(request.content)
    assert request.headers["x-api-key"] == "test-api-key"
    assert body["model"] == MODEL
    assert body["max_tokens"] == 123
    assert body["system"] == system
    assert body["messages"] == messages
    assert response.id == "msg_test"
    assert response.stop_reason == "end_turn"
    assert usage.request_count == 1
    assert usage.total_input_tokens == 10


@pytest.mark.asyncio
async def test_configured_override_and_unknown_model_preflight(
    httpx_mock: HTTPXMock,
) -> None:
    track = load_track().model_copy(deep=True)
    track.llm.prices["utility-model"] = track.llm.prices[MODEL]
    settings = _settings(track=track)
    _add_message(httpx_mock, _message(model="utility-model"))

    async with _client(settings=settings) as client:
        await client.complete(
            [],
            [{"role": "user", "content": "utility"}],
            model="utility-model",
        )
        with pytest.raises(ValueError, match="no configured price"):
            await client.complete(
                [],
                [{"role": "user", "content": "unknown"}],
                model="unknown-model",
            )

    assert len(httpx_mock.get_requests()) == 1
    assert json.loads(httpx_mock.get_request().content)["model"] == "utility-model"


def test_build_cached_system_reads_only_configured_context(tmp_path: Path) -> None:
    context_path = tmp_path / "track-context.md"
    context_path.write_text("track knowledge", encoding="utf-8")
    track = load_track().model_copy(deep=True)
    track.llm.context_path = str(context_path)

    blocks = build_cached_system(
        track,
        CachedSystemSource("diagnosis prompt", "vocabulary digest"),
    )

    assert [block["text"] for block in blocks] == [
        "diagnosis prompt",
        "track knowledge",
        "vocabulary digest",
    ]
    assert all(
        block["cache_control"] == {"type": "ephemeral"} for block in blocks
    )


@pytest.mark.parametrize("field", ["prompt", "context", "vocabulary"])
def test_build_cached_system_rejects_empty_inputs(tmp_path: Path, field: str) -> None:
    context_path = tmp_path / "track-context.md"
    context_path.write_text("" if field == "context" else "context", encoding="utf-8")
    track = load_track().model_copy(deep=True)
    track.llm.context_path = str(context_path)
    source = CachedSystemSource(
        "" if field == "prompt" else "prompt",
        "" if field == "vocabulary" else "vocabulary",
    )

    with pytest.raises(ValueError, match="must not be empty"):
        build_cached_system(track, source)


def test_build_cached_system_propagates_missing_path(tmp_path: Path) -> None:
    track = load_track().model_copy(deep=True)
    track.llm.context_path = str(tmp_path / "missing.md")

    with pytest.raises(FileNotFoundError):
        build_cached_system(track, CachedSystemSource("prompt", "vocabulary"))


@pytest.mark.asyncio
async def test_usage_costs_all_token_classes_once(httpx_mock: HTTPXMock) -> None:
    _add_message(
        httpx_mock,
        _message(
            input_tokens=1_000,
            output_tokens=200,
            cache_creation_input_tokens=2_000,
            cache_read_input_tokens=3_000,
        ),
    )

    async with _client() as client:
        _, usage = await client.complete([], [{"role": "user", "content": "x"}])

    assert usage.input_tokens == 1_000
    assert usage.output_tokens == 200
    assert usage.cache_creation_input_tokens == 2_000
    assert usage.cache_read_input_tokens == 3_000
    assert usage.total_input_tokens == 6_000
    assert usage.cost_usd == 0.024


@pytest.mark.asyncio
async def test_missing_cache_usage_normalizes_to_zero(httpx_mock: HTTPXMock) -> None:
    _add_message(
        httpx_mock,
        _message(
            cache_creation_input_tokens=None,
            cache_read_input_tokens=None,
        ),
    )

    async with _client() as client:
        _, usage = await client.complete(
            [{"type": "text", "text": "short", "cache_control": {"type": "ephemeral"}}],
            [{"role": "user", "content": "x"}],
        )

    assert usage.cache_creation_input_tokens == 0
    assert usage.cache_read_input_tokens == 0


@pytest.mark.asyncio
async def test_budget_exact_cap_and_overage(httpx_mock: HTTPXMock) -> None:
    _add_message(httpx_mock, _message(input_tokens=1_000, output_tokens=0))
    exact_guard = BudgetGuard(0.005)

    async with _client(guard=exact_guard) as client:
        await client.complete([], [{"role": "user", "content": "exact"}])
    assert exact_guard.spent == 0.005

    _add_message(httpx_mock, _message(input_tokens=1_001, output_tokens=0))
    over_guard = BudgetGuard(0.005)
    with capture_logs() as logs:
        async with _client(guard=over_guard) as client:
            with pytest.raises(BudgetExceeded):
                await client.complete([], [{"role": "user", "content": "over"}])
    assert over_guard.spent == 0.005005
    assert len(logs) == 1
    assert logs[0]["event"] == "claude.response"
    assert logs[0]["cumulative_spend"] == 0.005005


@pytest.mark.asyncio
async def test_forced_tool_returns_matching_validated_dict(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock, _tool_message(7))

    async with _client() as client:
        result, usage = await client.complete(
            [],
            [{"role": "user", "content": "submit"}],
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,
            thinking=True,
            output_model=ResultModel,
        )

    body = json.loads(httpx_mock.get_request().content)
    assert result == {"value": 7}
    assert usage.request_count == 1
    assert body["thinking"] == {"type": "adaptive"}
    assert body["output_config"] == {"effort": "high"}
    assert body["model"] == MODEL
    assert "budget_tokens" not in json.dumps(body)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tools, choice, output_model",
    [
        (None, TOOL_CHOICE, ResultModel),
        (TOOLS, {"type": "tool", "name": "missing"}, ResultModel),
        ([*TOOLS, *TOOLS], TOOL_CHOICE, ResultModel),
        (TOOLS, TOOL_CHOICE, None),
        (None, None, ResultModel),
        (None, {"type": "any"}, None),
    ],
)
async def test_forced_tool_preflight_rejects_incoherent_inputs(
    httpx_mock: HTTPXMock,
    tools: Any,
    choice: Any,
    output_model: Any,
) -> None:
    async with _client() as client:
        with pytest.raises(ValueError):
            await client.complete(
                [],
                [{"role": "user", "content": "x"}],
                tools=tools,
                tool_choice=choice,
                output_model=output_model,
            )

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_invalid_tool_input_repairs_once_and_aggregates_usage(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock, _tool_message("not-an-int"))
    _add_message(httpx_mock, _tool_message(9))
    original_messages = [{"role": "user", "content": "submit"}]

    async with _client() as client:
        result, usage = await client.complete(
            [],
            original_messages,
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,
            output_model=ResultModel,
        )

    requests = httpx_mock.get_requests()
    repair_body = json.loads(requests[1].content)
    repair_messages = repair_body["messages"]
    assert result == {"value": 9}
    assert usage.request_count == 2
    assert usage.input_tokens == 20
    assert usage.output_tokens == 10
    assert original_messages == [{"role": "user", "content": "submit"}]
    assert repair_messages[-2]["role"] == "assistant"
    assert repair_messages[-2]["content"] == _tool_message("not-an-int")["content"]
    assert repair_messages[-1]["content"][0]["type"] == "tool_result"
    assert repair_messages[-1]["content"][0]["is_error"] is True
    assert "not-an-int" not in repair_messages[-1]["content"][0]["content"]


@pytest.mark.asyncio
async def test_repair_summary_excludes_custom_validator_payload(
    httpx_mock: HTTPXMock,
) -> None:
    secret = "REPAIR_SECRET_SENTINEL"
    _add_message(httpx_mock, _tool_message(secret))
    _add_message(httpx_mock, _tool_message("safe"))

    async with _client() as client:
        result, _ = await client.complete(
            [],
            [{"role": "user", "content": "submit"}],
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,
            output_model=LeakyValidatorModel,
        )

    repair = json.loads(httpx_mock.get_requests()[1].content)
    repair_result = repair["messages"][-1]["content"][0]["content"]
    assert result == {"value": "safe"}
    assert "value_error" in repair_result
    assert secret not in repair_result


@pytest.mark.asyncio
async def test_first_response_budget_overage_prevents_repair(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock, _tool_message("invalid"))
    guard = BudgetGuard(0.000001)

    async with _client(guard=guard) as client:
        with pytest.raises(BudgetExceeded):
            await client.complete(
                [],
                [{"role": "user", "content": "submit"}],
                tools=TOOLS,
                tool_choice=TOOL_CHOICE,
                output_model=ResultModel,
            )

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "first_content",
    [
        [{"type": "text", "text": "missing"}],
        [
            {"type": "tool_use", "id": "a", "name": "submit_result", "input": {"value": 1}},
            {"type": "tool_use", "id": "b", "name": "submit_result", "input": {"value": 2}},
        ],
        [{"type": "tool_use", "id": "a", "name": "wrong", "input": {"value": 1}}],
        [{"type": "tool_use", "id": "a", "name": "submit_result", "input": "bad"}],
    ],
)
async def test_invalid_structured_shapes_have_one_repair_ceiling(
    httpx_mock: HTTPXMock,
    first_content: list[dict[str, Any]],
) -> None:
    _add_message(httpx_mock, _message(content=first_content))
    _add_message(httpx_mock, _message(content=first_content))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        async with _client() as client:
            with pytest.raises(StructuredOutputError):
                await client.complete(
                    [],
                    [{"role": "user", "content": "submit"}],
                    tools=TOOLS,
                    tool_choice=TOOL_CHOICE,
                    output_model=ResultModel,
                )

    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
async def test_thinking_false_omits_thinking_fields(httpx_mock: HTTPXMock) -> None:
    _add_message(httpx_mock)

    async with _client() as client:
        await client.complete([], [{"role": "user", "content": "x"}])

    body = json.loads(httpx_mock.get_request().content)
    assert "thinking" not in body
    assert "output_config" not in body


@pytest.mark.asyncio
async def test_images_are_appended_without_mutating_messages(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock)
    messages = [{"role": "user", "content": "inspect"}]
    original = deepcopy(messages)

    async with _client() as client:
        await client.complete(
            [],
            messages,
            images=[ImageInput(b"png-bytes", "image/png")],
        )

    body = json.loads(httpx_mock.get_request().content)
    assert messages == original
    assert body["messages"][0]["content"][0] == {
        "type": "text",
        "text": "inspect",
    }
    assert body["messages"][0]["content"][1] == {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "cG5nLWJ5dGVz",
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["assistant", "media", "data"])
async def test_invalid_images_fail_before_request(
    httpx_mock: HTTPXMock,
    case: str,
) -> None:
    messages = [
        {"role": "assistant" if case == "assistant" else "user", "content": "x"}
    ]
    image = ImageInput(
        b"data" if case != "data" else "not-bytes",  # type: ignore[arg-type]
        "image/png" if case != "media" else "image/tiff",  # type: ignore[arg-type]
    )

    async with _client() as client:
        with pytest.raises((TypeError, ValueError)):
            await client.complete([], messages, images=[image])

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_empty_images_are_noop(httpx_mock: HTTPXMock) -> None:
    _add_message(httpx_mock)
    messages = [{"role": "user", "content": "x"}]

    async with _client() as client:
        await client.complete([], messages, images=[])

    assert json.loads(httpx_mock.get_request().content)["messages"] == messages


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [429, 500, 504, 529])
async def test_retryable_status_recovers_with_one_tenacity_retry(
    httpx_mock: HTTPXMock,
    status_code: int,
) -> None:
    _add_error(httpx_mock, status_code)
    _add_message(httpx_mock)

    async with _client() as client:
        response, _ = await client.complete(
            [],
            [{"role": "user", "content": "retry"}],
        )

    assert response.id == "msg_test"
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "transport_error",
    [httpx.ReadTimeout("slow"), httpx.ConnectError("offline")],
)
async def test_retryable_transport_error_recovers(
    httpx_mock: HTTPXMock,
    transport_error: httpx.HTTPError,
) -> None:
    httpx_mock.add_exception(transport_error, method="POST", url=MESSAGES_URL)
    _add_message(httpx_mock)

    async with _client() as client:
        await client.complete([], [{"role": "user", "content": "retry"}])

    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
async def test_non_retryable_status_is_single_attempt(
    httpx_mock: HTTPXMock,
    status_code: int,
) -> None:
    _add_error(httpx_mock, status_code)

    async with _client() as client:
        with pytest.raises(anthropic.APIStatusError):
            await client.complete([], [{"role": "user", "content": "fail"}])

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_retry_exhaustion_preserves_typed_exception(
    httpx_mock: HTTPXMock,
) -> None:
    for _ in range(3):
        _add_error(httpx_mock, 500)

    async with _client() as client:
        with pytest.raises(anthropic.InternalServerError):
            await client.complete([], [{"role": "user", "content": "fail"}])

    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_malformed_negative_usage_is_not_charged(
    httpx_mock: HTTPXMock,
) -> None:
    _add_message(httpx_mock, _message(input_tokens=-1))
    guard = BudgetGuard(10.0)

    with capture_logs() as logs:
        async with _client(guard=guard) as client:
            with pytest.raises(ValueError, match="non-negative integer"):
                await client.complete([], [{"role": "user", "content": "x"}])

    assert guard.spent == 0.0
    assert len(logs) == 1
    assert logs[0]["event"] == "claude.response_invalid"
    assert logs[0]["exception_type"] == "ValueError"


@pytest.mark.asyncio
async def test_structured_logs_exclude_all_request_secrets(
    httpx_mock: HTTPXMock,
) -> None:
    api_secret = "API_SECRET_SENTINEL"
    prompt_secret = "PROMPT_SECRET_SENTINEL"
    tool_secret = "TOOL_SECRET_SENTINEL"
    image_secret = b"IMAGE_SECRET_SENTINEL"
    base_secret = "BASE_SECRET_SENTINEL"
    exception_secret = "EXCEPTION_SECRET_SENTINEL"
    settings = _settings(
        anthropic_api_key=SecretStr(api_secret),
        anthropic_base_url=f"https://{base_secret.lower()}.test/anthropic",
    )
    message_url = f"https://{base_secret.lower()}.test/anthropic/v1/messages"
    httpx_mock.add_response(
        method="POST",
        url=message_url,
        json=_tool_message(tool_secret),
    )
    for _ in range(3):
        httpx_mock.add_response(
            method="POST",
            url=message_url,
            status_code=500,
            json={
                "type": "error",
                "error": {"type": "api_error", "message": exception_secret},
                "request_id": "req_safe",
            },
        )

    with capture_logs() as logs:
        async with _client(settings=settings) as client:
            result, _ = await client.complete(
                [{"type": "text", "text": prompt_secret}],
                [{"role": "user", "content": prompt_secret}],
                tools=TOOLS,
                tool_choice=TOOL_CHOICE,
                images=[ImageInput(image_secret, "image/png")],
                output_model=SecretResultModel,
            )
            assert result == {"value": tool_secret}
            with pytest.raises(anthropic.InternalServerError):
                await client.complete(
                    [{"type": "text", "text": prompt_secret}],
                    [{"role": "user", "content": prompt_secret}],
                )

    serialized = json.dumps(logs)
    for secret in [
        api_secret,
        prompt_secret,
        tool_secret,
        image_secret.decode(),
        base_secret,
        base_secret.lower(),
        exception_secret,
    ]:
        assert secret not in serialized
    allowed = {
        "event",
        "log_level",
        "model",
        "attempt",
        "latency_ms",
        "status_code",
        "exception_type",
        "request_id",
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "total_input_tokens",
        "cache_hit",
        "cost_usd",
        "cumulative_spend",
        "stop_reason",
    }
    assert all(set(event) <= allowed for event in logs)