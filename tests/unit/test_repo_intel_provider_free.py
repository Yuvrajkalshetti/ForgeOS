from __future__ import annotations

from pathlib import Path

from forgeos.testing.guards import collect_imported_modules, find_forbidden_imports

REPO_INTEL = Path(__file__).resolve().parents[2] / "src" / "forgeos" / "core" / "repo_intel"


def test_repo_intel_does_not_import_provider_port() -> None:
    # ADR 0005: ingest must remain provider-free.
    forbidden = find_forbidden_imports(REPO_INTEL, ["forgeos.ports.provider"])
    assert forbidden == set()


def test_repo_intel_imports_no_provider_or_network_modules() -> None:
    imported = collect_imported_modules(REPO_INTEL)
    assert "anthropic" not in imported
    assert "httpx" not in imported  # no network client in ingest
    assert not any(m.startswith("forgeos.adapters.providers") for m in imported)
