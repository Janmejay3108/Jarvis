from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, field_validator


def _reject_placeholder(value: str) -> str:
    if value.strip() == "<TO BE PROVIDED>":
        raise ValueError("configuration value is still <TO BE PROVIDED>")
    return value


ProvidedString = Annotated[str, AfterValidator(_reject_placeholder)]


class RepoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: str
    slug: str
    branch: str
    local_path: str
    remotes: dict[str, str]


class AuthConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    token_path: str
    client_id: str
    client_secret: str


class DaiEndpointsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_by_runid: str
    screenshot: str


class ScreenshotSelectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_entry_strategy: str
    walk_back_to_prior_image: bool
    image_id_field: str


class DaiConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    host: str
    version: str
    base_url: ProvidedString
    auth: AuthConfig
    endpoints: DaiEndpointsConfig
    screenshot_selection: ScreenshotSelectionConfig


class JarvisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo_url: str
    branch: str
    dai_base_url: str
    auth: AuthConfig
    completion_mode: str
    poll_backoff: list[int]
    run_timeout: ProvidedString
    suites_path: str
    test_config_registry: str


class LlmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    anthropic_base_url: str
    api_key: str
    model_light: str | None = None
    engine_mode: str
    thinking_on_escalation: bool


class ValidationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mechanism: str
    max_attempts: int
    n_best_on_retry: int


class NumberToSuiteRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: int | ProvidedString
    end: int | ProvidedString
    suite: ProvidedString


class TrackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: RepoConfig
    suites: list[str]
    number_to_suite_ranges: list[NumberToSuiteRange]
    dai: DaiConfig
    jarvis: JarvisConfig
    llm: LlmConfig
    validation: ValidationConfig
    approval_mode: str
    budget_usd_per_run: float


class SuiteRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suite_dir: str
    model: str
    test_config_id: str
    dispatcher_script: str
    smoke_target: str
    onboarded: str
    status: str

    @field_validator("onboarded", mode="before")
    @classmethod
    def normalize_onboarded(cls, value: object) -> object:
        if isinstance(value, date):
            return value.isoformat()
        return value


class _TestConfigRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    suites: dict[str, SuiteRegistryEntry]


def _read_yaml(path: str) -> object:
    with Path(path).open(encoding="utf-8") as yaml_file:
        return yaml.safe_load(yaml_file)


def load_track(config_path: str = "config/enovia.yaml") -> TrackConfig:
    return TrackConfig.model_validate(_read_yaml(config_path))


def load_test_config_registry(path: str) -> dict[str, SuiteRegistryEntry]:
    registry = _TestConfigRegistry.model_validate(_read_yaml(path))
    return registry.suites
