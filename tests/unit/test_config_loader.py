from __future__ import annotations

from pathlib import Path

from forgeos.config.loader import load_config
from forgeos.config.models import ForgeConfig


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_defaults_when_no_layers(tmp_path: Path) -> None:
    config = load_config(project_dir=tmp_path, user_home=tmp_path / "nohome", environ={})
    assert config == ForgeConfig()
    assert config.providers.default == "claude"
    assert config.concurrency.global_limit == 5


def test_user_layer_overrides_defaults(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write(home / ".forgeos" / "config.yaml", "providers:\n  default: ollama\n")
    config = load_config(project_dir=tmp_path, user_home=home, environ={})
    assert config.providers.default == "ollama"


def test_project_layer_overrides_user(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "proj"
    _write(home / ".forgeos" / "config.yaml", "providers:\n  default: ollama\n")
    _write(project / ".forgeos" / "config.yaml", "providers:\n  default: claude\n")
    config = load_config(project_dir=project, user_home=home, environ={})
    assert config.providers.default == "claude"


def test_env_overrides_everything(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _write(project / ".forgeos" / "config.yaml", "providers:\n  default: claude\n")
    env = {"FORGEOS__PROVIDERS__DEFAULT": "ollama", "FORGEOS__CONCURRENCY__GLOBAL_LIMIT": "9"}
    config = load_config(project_dir=project, user_home=tmp_path / "h", environ=env)
    assert config.providers.default == "ollama"
    assert config.concurrency.global_limit == 9


def test_env_value_coercion(tmp_path: Path) -> None:
    env = {"FORGEOS__LOGGING__JSON": "false", "FORGEOS__TOKENS__PER_REQUEST": "1234"}
    config = load_config(project_dir=tmp_path, user_home=tmp_path / "h", environ=env)
    assert config.logging.as_json is False
    assert config.tokens.per_request == 1234


def test_unreadable_layer_is_skipped(tmp_path: Path) -> None:
    # A home that does not exist must not raise.
    config = load_config(project_dir=tmp_path, user_home=tmp_path / "missing", environ={})
    assert isinstance(config, ForgeConfig)
