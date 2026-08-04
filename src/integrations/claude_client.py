from __future__ import annotations

import base64
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self, TypeVar, cast, overload

import anthropic
import structlog
from anthropic import AsyncAnthropic
from anthropic.types import (
	Message,
	MessageParam,
	TextBlockParam,
	ToolChoiceParam,
	ToolUnionParam,
)
from pydantic import BaseModel, ValidationError
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt
from tenacity.wait import wait_random_exponential

from src.orchestrator.track_loader import LlmPriceConfig, TrackConfig
from src.utils.budget import BudgetExceeded, BudgetGuard

if TYPE_CHECKING:
	from collections.abc import Awaitable, Callable

	from src.config import Settings

logger = structlog.get_logger(__name__)

_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class ImageInput:
	data: bytes
	media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


@dataclass(frozen=True)
class ClaudeUsage:
	model: str
	input_tokens: int
	output_tokens: int
	cache_creation_input_tokens: int
	cache_read_input_tokens: int
	total_input_tokens: int
	cost_usd: float
	request_count: int


@dataclass(frozen=True)
class CachedSystemSource:
	diagnosis_system_prompt: str
	vocabulary_digest: str


class StructuredOutputError(RuntimeError):
	pass


class _ToolOutputProblem(ValueError):
	def __init__(self, summary: str, tool_use_id: str | None = None) -> None:
		super().__init__(summary)
		self.summary = summary
		self.tool_use_id = tool_use_id


TModel = TypeVar("TModel", bound=BaseModel)
ClaudeResult = Message | dict[str, Any]


def _nonempty(value: str, name: str) -> str:
	if not value.strip():
		raise ValueError(f"{name} must not be empty")
	return value


def build_cached_system(
	track_cfg: TrackConfig,
	source: CachedSystemSource,
) -> list[TextBlockParam]:
	prompt = _nonempty(source.diagnosis_system_prompt, "diagnosis system prompt")
	vocabulary = _nonempty(source.vocabulary_digest, "vocabulary digest")
	context = _nonempty(
		Path(track_cfg.llm.context_path).read_text(encoding="utf-8"),
		"track context",
	)
	cache_control = {"type": "ephemeral"}
	return [
		{"type": "text", "text": prompt, "cache_control": cache_control},
		{"type": "text", "text": context, "cache_control": cache_control},
		{"type": "text", "text": vocabulary, "cache_control": cache_control},
	]


def _is_retryable(error: BaseException) -> bool:
	if isinstance(error, anthropic.APIConnectionError):
		return True
	return (
		isinstance(error, anthropic.APIStatusError)
		and error.status_code >= 500
	) or isinstance(error, anthropic.RateLimitError)


def _status_code(error: BaseException) -> int | None:
	if isinstance(error, anthropic.APIStatusError):
		return error.status_code
	return None


def _request_id(value: object) -> str | None:
	request_id = getattr(value, "request_id", None)
	if request_id is None:
		request_id = getattr(value, "_request_id", None)
	return request_id if isinstance(request_id, str) else None


def _token_count(value: object, name: str) -> int:
	if not isinstance(value, int) or isinstance(value, bool) or value < 0:
		raise ValueError(f"Anthropic usage {name} must be a non-negative integer")
	return value


def _optional_token_count(value: object, name: str) -> int:
	if value is None:
		return 0
	return _token_count(value, name)


def _cost(
	*,
	input_tokens: int,
	output_tokens: int,
	cache_creation_input_tokens: int,
	cache_read_input_tokens: int,
	price: LlmPriceConfig,
) -> float:
	amount = (
		Decimal(input_tokens) * Decimal(str(price.input_per_million))
		+ Decimal(output_tokens) * Decimal(str(price.output_per_million))
		+ Decimal(cache_creation_input_tokens)
		* Decimal(str(price.cache_write_5m_per_million))
		+ Decimal(cache_read_input_tokens)
		* Decimal(str(price.cache_read_per_million))
	) / _MILLION
	return float(amount)


def _aggregate_usage(first: ClaudeUsage, second: ClaudeUsage) -> ClaudeUsage:
	if first.model != second.model:
		raise ValueError("cannot aggregate usage from different models")
	return ClaudeUsage(
		model=first.model,
		input_tokens=first.input_tokens + second.input_tokens,
		output_tokens=first.output_tokens + second.output_tokens,
		cache_creation_input_tokens=(
			first.cache_creation_input_tokens
			+ second.cache_creation_input_tokens
		),
		cache_read_input_tokens=(
			first.cache_read_input_tokens + second.cache_read_input_tokens
		),
		total_input_tokens=first.total_input_tokens + second.total_input_tokens,
		cost_usd=float(Decimal(str(first.cost_usd)) + Decimal(str(second.cost_usd))),
		request_count=first.request_count + second.request_count,
	)


def _validation_summary(error: ValidationError) -> str:
	parts = []
	for item in error.errors(include_input=False, include_url=False):
		location = ".".join(str(part) for part in item["loc"]) or "root"
		parts.append(f"{location}: {item['type']}")
	return "; ".join(parts)


def _forced_tool_name(tool_choice: ToolChoiceParam | None) -> str | None:
	if tool_choice is None or tool_choice.get("type") != "tool":
		return None
	name = tool_choice.get("name")
	if not isinstance(name, str) or not name:
		raise ValueError("forced tool choice must name a tool")
	return name


def _tool_names(tools: Sequence[ToolUnionParam] | None) -> list[str]:
	if tools is None:
		return []
	names: list[str] = []
	for tool in tools:
		name = tool.get("name")
		if isinstance(name, str):
			names.append(name)
	return names


def _structured_input(
	response: Message,
	tool_name: str,
	output_model: type[TModel],
) -> dict[str, Any]:
	matches = [
		block
		for block in response.content
		if block.type == "tool_use" and block.name == tool_name
	]
	if len(matches) != 1:
		raise _ToolOutputProblem("expected exactly one matching tool-use block")

	block = matches[0]
	tool_use_id = block.id if isinstance(block.id, str) and block.id else None
	if not isinstance(block.input, dict):
		raise _ToolOutputProblem("tool input must be an object", tool_use_id)
	try:
		validated = output_model.model_validate(block.input)
	except ValidationError as error:
		raise _ToolOutputProblem(
			_validation_summary(error),
			tool_use_id,
		) from error
	return validated.model_dump(mode="json")


def _repair_message(problem: _ToolOutputProblem) -> MessageParam:
	if problem.tool_use_id is not None:
		return {
			"role": "user",
			"content": [
				{
					"type": "tool_result",
					"tool_use_id": problem.tool_use_id,
					"is_error": True,
					"content": f"Schema validation failed: {problem.summary}",
				}
			],
		}
	return {
		"role": "user",
		"content": (
			"<<<STRUCTURED_OUTPUT_REPAIR>>>\n"
			f"Return exactly one forced tool call. Error: {problem.summary}\n"
			"<<<END_STRUCTURED_OUTPUT_REPAIR>>>"
		),
	}


def _with_images(
	messages: Sequence[MessageParam],
	images: Sequence[ImageInput] | None,
) -> list[MessageParam]:
	normalized = list(messages)
	if not images:
		return normalized
	if normalized[-1].get("role") != "user":
		raise ValueError("images require a final user message")

	final_message = dict(normalized[-1])
	content = final_message.get("content")
	blocks: list[Any]
	if isinstance(content, str):
		blocks = [{"type": "text", "text": content}]
	else:
		blocks = list(content)
	for image in images:
		if image.media_type not in _MEDIA_TYPES:
			raise ValueError("unsupported image media type")
		if not isinstance(image.data, bytes):
			raise TypeError("image data must be bytes")
		blocks.append(
			{
				"type": "image",
				"source": {
					"type": "base64",
					"media_type": image.media_type,
					"data": base64.b64encode(image.data).decode("ascii"),
				},
			}
		)
	final_message["content"] = blocks
	normalized[-1] = cast(MessageParam, final_message)
	return normalized


class ClaudeClient:
	def __init__(
		self,
		config: Settings | None = None,
		budget_guard: BudgetGuard | None = None,
		client: AsyncAnthropic | None = None,
	) -> None:
		if config is None:
			from src.config import settings

			config = settings

		api_key = config.anthropic_api_key.get_secret_value()
		_nonempty(api_key, "Anthropic API key")
		_nonempty(config.anthropic_base_url, "Anthropic base URL")
		_nonempty(config.model, "Anthropic default model")
		if (
			not math.isfinite(config.budget_usd_per_run)
			or config.budget_usd_per_run <= 0
		):
			raise ValueError("Anthropic budget must be finite and positive")

		self._settings = config
		self._prices = config.track.llm.prices
		if config.model not in self._prices:
			raise ValueError("configured default LLM model has no price entry")
		self._budget_guard = budget_guard or BudgetGuard(config.budget_usd_per_run)
		self._client = client or AsyncAnthropic(
			api_key=api_key,
			base_url=config.anthropic_base_url,
			max_retries=0,
		)
		self._owns_client = client is None
		self._retry_wait = wait_random_exponential(max=30)
		self._clock = time.perf_counter

	async def aclose(self) -> None:
		if self._owns_client:
			await self._client.close()

	async def __aenter__(self) -> Self:
		return self

	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc_value: BaseException | None,
		traceback: object,
	) -> None:
		await self.aclose()

	async def _request(
		self,
		request: Callable[[], Awaitable[Message]],
		model: str,
	) -> tuple[Message, int, float]:
		retrying = AsyncRetrying(
			retry=retry_if_exception(_is_retryable),
			stop=stop_after_attempt(3),
			wait=self._retry_wait,
			reraise=True,
		)
		async for attempt in retrying:
			with attempt:
				attempt_number = attempt.retry_state.attempt_number
				started = self._clock()
				try:
					response = await request()
				except BaseException as error:
					latency_ms = (self._clock() - started) * 1000
					if isinstance(
						error,
						(anthropic.APIConnectionError, anthropic.APIStatusError),
					):
						retrying_error = _is_retryable(error)
						event = (
							"claude.transport_retry"
							if retrying_error and attempt_number < 3
							else "claude.transport_exhausted"
							if retrying_error
							else "claude.transport_failed"
						)
						logger.warning(
							event,
							model=model,
							attempt=attempt_number,
							latency_ms=latency_ms,
							status_code=_status_code(error),
							exception_type=type(error).__name__,
							request_id=_request_id(error),
						)
					raise
				return response, attempt_number, (self._clock() - started) * 1000
		raise RuntimeError("Anthropic retry loop completed without a result")

	def _record_usage(
		self,
		response: Message,
		model: str,
		attempt_number: int,
		latency_ms: float,
	) -> ClaudeUsage:
		try:
			input_tokens = _token_count(response.usage.input_tokens, "input_tokens")
			output_tokens = _token_count(
				response.usage.output_tokens,
				"output_tokens",
			)
			cache_creation_input_tokens = _optional_token_count(
				response.usage.cache_creation_input_tokens,
				"cache_creation_input_tokens",
			)
			cache_read_input_tokens = _optional_token_count(
				response.usage.cache_read_input_tokens,
				"cache_read_input_tokens",
			)
		except ValueError as error:
			logger.warning(
				"claude.response_invalid",
				model=model,
				attempt=attempt_number,
				latency_ms=latency_ms,
				exception_type=type(error).__name__,
				request_id=_request_id(response),
				stop_reason=response.stop_reason,
			)
			raise
		total_input_tokens = (
			input_tokens
			+ cache_creation_input_tokens
			+ cache_read_input_tokens
		)
		cost_usd = _cost(
			input_tokens=input_tokens,
			output_tokens=output_tokens,
			cache_creation_input_tokens=cache_creation_input_tokens,
			cache_read_input_tokens=cache_read_input_tokens,
			price=self._prices[model],
		)
		telemetry = {
			"model": model,
			"attempt": attempt_number,
			"latency_ms": latency_ms,
			"request_id": _request_id(response),
			"input_tokens": input_tokens,
			"output_tokens": output_tokens,
			"cache_creation_input_tokens": cache_creation_input_tokens,
			"cache_read_input_tokens": cache_read_input_tokens,
			"total_input_tokens": total_input_tokens,
			"cache_hit": cache_read_input_tokens > 0,
			"cost_usd": cost_usd,
			"stop_reason": response.stop_reason,
		}
		try:
			cumulative_spend = self._budget_guard.charge(cost_usd)
		except BudgetExceeded:
			logger.info(
				"claude.response",
				cumulative_spend=self._budget_guard.spent,
				**telemetry,
			)
			raise
		logger.info(
			"claude.response",
			cumulative_spend=cumulative_spend,
			**telemetry,
		)
		return ClaudeUsage(
			model=model,
			input_tokens=input_tokens,
			output_tokens=output_tokens,
			cache_creation_input_tokens=cache_creation_input_tokens,
			cache_read_input_tokens=cache_read_input_tokens,
			total_input_tokens=total_input_tokens,
			cost_usd=cost_usd,
			request_count=1,
		)

	@overload
	async def complete(
		self,
		system_blocks: Sequence[TextBlockParam],
		messages: Sequence[MessageParam],
		*,
		model: str | None = None,
		max_tokens: int = 4096,
		tools: Sequence[ToolUnionParam] | None = None,
		tool_choice: ToolChoiceParam | None = None,
		thinking: bool = False,
		images: Sequence[ImageInput] | None = None,
		output_model: type[TModel],
	) -> tuple[dict[str, Any], ClaudeUsage]: ...

	@overload
	async def complete(
		self,
		system_blocks: Sequence[TextBlockParam],
		messages: Sequence[MessageParam],
		*,
		model: str | None = None,
		max_tokens: int = 4096,
		tools: Sequence[ToolUnionParam] | None = None,
		tool_choice: ToolChoiceParam | None = None,
		thinking: bool = False,
		images: Sequence[ImageInput] | None = None,
		output_model: None = None,
	) -> tuple[Message, ClaudeUsage]: ...

	async def complete(
		self,
		system_blocks: Sequence[TextBlockParam],
		messages: Sequence[MessageParam],
		*,
		model: str | None = None,
		max_tokens: int = 4096,
		tools: Sequence[ToolUnionParam] | None = None,
		tool_choice: ToolChoiceParam | None = None,
		thinking: bool = False,
		images: Sequence[ImageInput] | None = None,
		output_model: type[BaseModel] | None = None,
	) -> tuple[ClaudeResult, ClaudeUsage]:
		resolved_model = model or self._settings.model
		if resolved_model not in self._prices:
			raise ValueError("Anthropic model has no configured price entry")
		if max_tokens <= 0:
			raise ValueError("max_tokens must be positive")
		if not messages:
			raise ValueError("messages must not be empty")

		forced_tool = _forced_tool_name(tool_choice)
		if forced_tool is not None:
			if _tool_names(tools).count(forced_tool) != 1:
				raise ValueError("forced tool must exist exactly once")
			if output_model is None:
				raise ValueError("forced structured output requires output_model")
		elif output_model is not None:
			raise ValueError("output_model requires a forced tool choice")
		elif tool_choice is not None and tool_choice.get("type") in {"any", "auto"}:
			if not tools:
				raise ValueError("tool choice requires tools")

		request_messages = _with_images(messages, images)
		request_tools = list(tools) if tools is not None else None
		request_system = list(system_blocks)

		kwargs: dict[str, Any] = {
			"model": resolved_model,
			"max_tokens": max_tokens,
			"system": request_system,
			"messages": request_messages,
		}
		if request_tools is not None:
			kwargs["tools"] = request_tools
		if tool_choice is not None:
			kwargs["tool_choice"] = tool_choice
		if thinking:
			kwargs["thinking"] = {"type": "adaptive"}
			kwargs["output_config"] = {"effort": "high"}

		response, attempt_number, latency_ms = await self._request(
			lambda: self._client.messages.create(**kwargs),
			resolved_model,
		)
		usage = self._record_usage(
			response,
			resolved_model,
			attempt_number,
			latency_ms,
		)
		if forced_tool is None or output_model is None:
			return response, usage

		try:
			structured = _structured_input(response, forced_tool, output_model)
		except _ToolOutputProblem as first_problem:
			repair_messages = [
				*request_messages,
				{"role": "assistant", "content": response.content},
				_repair_message(first_problem),
			]
			repair_kwargs = {**kwargs, "messages": repair_messages}
			repaired, repair_attempt, repair_latency = await self._request(
				lambda: self._client.messages.create(**repair_kwargs),
				resolved_model,
			)
			repair_usage = self._record_usage(
				repaired,
				resolved_model,
				repair_attempt,
				repair_latency,
			)
			usage = _aggregate_usage(usage, repair_usage)
			try:
				structured = _structured_input(
					repaired,
					forced_tool,
					output_model,
				)
			except _ToolOutputProblem as final_problem:
				raise StructuredOutputError(
					"structured output remained invalid after one repair"
				) from final_problem
		return structured, usage
