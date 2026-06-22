"""Layered configuration loader.

Precedence (lowest to highest):

1. Built-in defaults (``ForgeConfig()``)
2. User layer    — ``~/.forgeos/config.yaml``         (L2 user knowledge)
3. Project layer — ``<project>/.forgeos/config.yaml`` (L3 project knowledge)
4. Environment   — ``FORGEOS__SECTION__KEY=value``    (double underscore nests)

Unreadable or missing layers are skipped silently (a sandboxed or fresh machine
has no user config yet), so loading is always safe and deterministic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from forgeos.config.models import ForgeConfig

ENV_PREFIX = "FORGEOS__"
_NESTING_SEPARATOR = "__"


def _read_yaml(path: Path) -> dict[str, Any]:
    """Return a mapping parsed from ``path``; ``{}`` if absent/unreadable/empty."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return {}
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _coerce(value: str) -> Any:
    """Best-effort scalar coercion for environment values."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", ""}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def _env_overrides(environ: dict[str, str]) -> dict[str, Any]:
    """Translate ``FORGEOS__a__b=c`` variables into a nested mapping."""
    result: dict[str, Any] = {}
    for raw_key, raw_value in environ.items():
        if not raw_key.startswith(ENV_PREFIX):
            continue
        path = raw_key[len(ENV_PREFIX) :].lower().split(_NESTING_SEPARATOR)
        cursor = result
        for segment in path[:-1]:
            nxt = cursor.setdefault(segment, {})
            if not isinstance(nxt, dict):
                nxt = {}
                cursor[segment] = nxt
            cursor = nxt
        cursor[path[-1]] = _coerce(raw_value)
    return result


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` onto ``base`` without mutating inputs."""
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def load_config(
    project_dir: Path | None = None,
    user_home: Path | None = None,
    environ: dict[str, str] | None = None,
) -> ForgeConfig:
    """Assemble a :class:`ForgeConfig` from all layers in precedence order."""
    home = user_home if user_home is not None else Path.home()
    environ = environ if environ is not None else dict(os.environ)

    layers: dict[str, Any] = {}
    layers = _deep_merge(layers, _read_yaml(home / ".forgeos" / "config.yaml"))
    if project_dir is not None:
        layers = _deep_merge(layers, _read_yaml(project_dir / ".forgeos" / "config.yaml"))
    layers = _deep_merge(layers, _env_overrides(environ))

    return ForgeConfig.model_validate(layers)
