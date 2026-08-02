from functools import cached_property

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.orchestrator.track_loader import (
    SuiteRegistryEntry,
    TrackConfig,
    load_test_config_registry,
    load_track,
)

load_dotenv(override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jira_base_url: str = ""
    jira_pat: SecretStr = SecretStr("")

    bitbucket_base_url: str = ""
    bitbucket_pat: SecretStr = SecretStr("")
    bitbucket_repo_url: str = ""
    bitbucket_branch: str = ""

    dai_base_url: str = ""
    dai_client_id: SecretStr = SecretStr("")
    dai_client_secret: SecretStr = SecretStr("")
    dai_auth_url: str = ""
    dai_log_by_runid_url: str = ""
    dai_screenshot_url: str = ""

    jarvis_repo_url: str = ""
    jarvis_pat: SecretStr = SecretStr("")
    jarvis_dai_base_url: str = ""
    jarvis_dai_client_id: SecretStr = SecretStr("")
    jarvis_dai_client_secret: SecretStr = SecretStr("")
    jarvis_branch: str = "Enovia"
    jarvis_enovia_suites_path_in_vm: str = r"C:\Eggplant_Suites"
    jarvis_completion_mode: str = "poll_backoff"

    validation_mechanism: str = "jarvis-dai"

    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_base_url: str = "https://itga-ai-gateway.azure-api.net/anthropic"
    model: str = "claude-opus-4-7"
    model_light: str = ""

    azure_openai_endpoint: str = "https://itga-ai-gateway.azure-api.net"
    azure_openai_api_version: str = "2024-10-21"
    llm_model: str = "gpt-5.4"

    epf_runscript_path: str = r"C:\Program Files\Eggplant\runscript.bat"
    epf_default_doc_dir: str = r"C:\Eggplant_Suites"
    epf_license_host: str = ""
    working_copy_path: str = "data/working_copy/enovia-plm-test-automation"
    db_path: str = "data/agent.db"
    engine_mode: str = "agentic"
    approval_mode: str = "manual"
    budget_usd_per_run: float = 10.0

    @cached_property
    def track(self) -> TrackConfig:
        return load_track()

    @cached_property
    def test_config_registry(self) -> dict[str, SuiteRegistryEntry]:
        return load_test_config_registry(self.track.jarvis.test_config_registry)


settings = Settings()
