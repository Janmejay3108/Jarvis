from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr, ValidationError

from src.config import Settings
from src.orchestrator.track_loader import load_test_config_registry, load_track


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL", "claude-opus-4-7")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("JIRA_WRITES_ENABLED", "false")

    configured = Settings(_env_file=None)

    assert configured.model == "claude-opus-4-7"
    assert isinstance(configured.anthropic_api_key, SecretStr)
    assert configured.anthropic_api_key.get_secret_value() == "test-api-key"
    assert configured.jira_writes_enabled is False

    monkeypatch.delenv("JIRA_WRITES_ENABLED")
    assert Settings(_env_file=None).jira_writes_enabled is True


def test_track_loader_rejects_unresolved_values(tmp_path: Path) -> None:
    raw_config = yaml.safe_load(
        Path("config/enovia.yaml").read_text(encoding="utf-8")
    )
    raw_config["dai"]["base_url"] = "<TO BE PROVIDED>"
    unresolved_config = tmp_path / "unresolved.yaml"
    unresolved_config.write_text(
        yaml.safe_dump(raw_config, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="TO BE PROVIDED"):
        load_track(str(unresolved_config))


def test_track_loader() -> None:
    track = load_track()

    assert len(track.suites) == 17
    assert track.jarvis.branch == "Enovia"
    assert track.jarvis.run_timeout == 7200
    assert track.dai.base_url == "http://epcorpappsdai12.cos.is.keysight.com:8000"
    assert track.validation.max_attempts == 3


def test_registry_loader() -> None:
    registry = load_test_config_registry(
        "tracks/enovia/test_config_registry.yaml"
    )

    assert "PartMaster" in registry
    assert (
        registry["EngineeringCentral"].test_config_id
        == "271b648a-a5e5-43ee-b4d8-24bab75da263"
    )
