from __future__ import annotations

from pathlib import Path

import pytest

from forgeos.testing.guards import collect_imported_modules, find_forbidden_imports

CORE = Path(__file__).resolve().parents[2] / "src" / "forgeos" / "core"
PROVIDER_FREE = ["repo_intel", "compression", "context_assembly"]


@pytest.mark.parametrize("package", PROVIDER_FREE)
def test_engine_does_not_import_provider_port(package: str) -> None:
    # ADR 0005 (RepoIntel) and ADR 0009 (Compression); Context Assembly is graph-only.
    forbidden = find_forbidden_imports(CORE / package, ["forgeos.ports.provider"])
    assert forbidden == set()


@pytest.mark.parametrize("package", PROVIDER_FREE)
def test_engine_imports_no_llm_or_network_clients(package: str) -> None:
    imported = collect_imported_modules(CORE / package)
    assert "anthropic" not in imported
    assert "httpx" not in imported
    assert not any(m.startswith("forgeos.adapters") for m in imported)
