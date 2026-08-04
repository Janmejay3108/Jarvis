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
    assert track.llm.context_path == "tracks/enovia/context.md"
    assert track.budget_usd_per_run == 10.0
    assert track.validation.max_attempts == 3

    price = track.llm.prices[track.llm.model]
    assert price.input_per_million == 5.0
    assert price.output_per_million == 25.0
    assert price.cache_write_5m_per_million == 6.25
    assert price.cache_read_per_million == 0.5


def _write_track_config(tmp_path: Path, raw_config: dict[str, object]) -> Path:
    config_path = tmp_path / "enovia.yaml"
    config_path.write_text(
        yaml.safe_dump(raw_config, sort_keys=False),
        encoding="utf-8",
    )
    return config_path


def test_track_loader_requires_default_model_price(tmp_path: Path) -> None:
    raw_config = yaml.safe_load(
        Path("config/enovia.yaml").read_text(encoding="utf-8")
    )
    raw_config["llm"]["prices"].clear()

    with pytest.raises(ValidationError, match="no price entry"):
        load_track(str(_write_track_config(tmp_path, raw_config)))


@pytest.mark.parametrize("invalid_rate", [-1, float("nan"), float("inf")])
def test_track_loader_rejects_invalid_llm_rates(
    tmp_path: Path,
    invalid_rate: float,
) -> None:
    raw_config = yaml.safe_load(
        Path("config/enovia.yaml").read_text(encoding="utf-8")
    )
    raw_config["llm"]["prices"]["claude-opus-4-7"][
        "input_per_million"
    ] = invalid_rate

    with pytest.raises(ValidationError):
        load_track(str(_write_track_config(tmp_path, raw_config)))


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_track_loader_rejects_invalid_llm_price_shape(
    tmp_path: Path,
    mutation: str,
) -> None:
    raw_config = yaml.safe_load(
        Path("config/enovia.yaml").read_text(encoding="utf-8")
    )
    price = raw_config["llm"]["prices"]["claude-opus-4-7"]
    if mutation == "missing":
        price.pop("cache_read_per_million")
    else:
        price["unexpected_rate"] = 1.0

    with pytest.raises(ValidationError):
        load_track(str(_write_track_config(tmp_path, raw_config)))


def test_registry_loader() -> None:
    registry = load_test_config_registry(
        "tracks/enovia/test_config_registry.yaml"
    )

    assert "PartMaster" in registry
    assert (
        registry["EngineeringCentral"].test_config_id
        == "271b648a-a5e5-43ee-b4d8-24bab75da263"
    )
