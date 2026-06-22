"""``forge doctor`` / ``forgeos doctor`` — environment & readiness diagnostics.

Read-only. Checks local state and configuration so a first-time user learns exactly
what is missing (and how to fix it) *before* running a provider-backed command. It
never makes a live provider call — that is the smoke test's job, not a diagnostic's.
Exit code is 0 when healthy, 1 when any check FAILs.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.config.loader import load_config

_FORGEOS_DIR = ".forgeos"


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def doctor_cmd(project: Path = Path()) -> None:
    """Diagnose ForgeOS setup for this project; report each check + remediation."""
    checks: list[dict[str, str]] = []
    initialized = (project / _FORGEOS_DIR).exists()
    if initialized:
        checks.append(_check("initialized", "OK", f"{project / _FORGEOS_DIR} present"))
        try:
            open_store(project)
            checks.append(_check("store", "OK", "snapshot store opens; index rebuildable"))
        except Exception as exc:  # diagnostic must not raise
            checks.append(_check("store", "FAIL", f"cannot open store: {exc}"))
    else:
        checks.append(
            _check("initialized", "FAIL", "project not initialized — run `forgeos init`")
        )

    config = load_config(project_dir=project)
    default = config.providers.default
    checks.append(_check("provider", "OK", f"default provider: {default}"))

    if default == "claude":
        env = config.providers.claude.api_key_env
        if os.environ.get(env):
            checks.append(_check("credentials", "OK", f"${env} is set"))
        else:
            checks.append(
                _check("credentials", "FAIL", f"${env} not set — `export {env}=...` to use Claude")
            )
    elif default == "ollama":
        host = config.providers.ollama.host
        checks.append(_check("credentials", "INFO", f"ollama needs no key; host {host}"))
    else:
        checks.append(_check("credentials", "INFO", f"provider '{default}' — verify its setup"))

    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 12)
    checks.append(_check("python", "OK" if py_ok else "FAIL", f"Python {py} (need >=3.12)"))

    ok = not any(c["status"] == "FAIL" for c in checks)
    typer.echo(json.dumps({"ok": ok, "checks": checks}, indent=2))
    if not ok:
        raise typer.Exit(code=1)
