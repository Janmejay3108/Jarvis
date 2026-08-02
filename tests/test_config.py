from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr, ValidationError

from src.config import Settings
from src.orchestrator.track_loader import load_test_config_registry, load_track


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL", "claude-opus-4-7")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

    configured = Settings(_env_file=None)

    assert configured.model == "claude-opus-4-7"
    assert isinstance(configured.anthropic_api_key, SecretStr)
    assert configured.anthropic_api_key.get_secret_value() == "test-api-key"


def test_track_loader_rejects_unresolved_values() -> None:
    with pytest.raises(ValidationError, match="TO BE PROVIDED"):
        load_track()


def test_track_loader(tmp_path: Path) -> None:
    source = Path("config/enovia.yaml")
    raw_config = yaml.safe_load(source.read_text(encoding="utf-8"))
    raw_config["number_to_suite_ranges"] = [
        item
        for item in raw_config["number_to_suite_ranges"]
        if item["start"] != "<TO BE PROVIDED>"
    ]
    raw_config["dai"]["base_url"] = "https://production-dai.example.test"
    raw_config["jarvis"]["run_timeout"] = "7200"

    resolved_config = tmp_path / "enovia.yaml"
    resolved_config.write_text(
        yaml.safe_dump(raw_config, sort_keys=False),
        encoding="utf-8",
    )

    track = load_track(str(resolved_config))

    assert len(track.suites) == 17
    assert track.jarvis.branch == "Enovia"
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
