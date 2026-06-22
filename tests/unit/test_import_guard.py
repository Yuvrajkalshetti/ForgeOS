from __future__ import annotations

from pathlib import Path

from forgeos.testing.guards import collect_imported_modules, find_forbidden_imports

SRC = Path(__file__).resolve().parents[2] / "src" / "forgeos"


def test_guard_detects_forbidden_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text("from forgeos.ports import provider\n", encoding="utf-8")
    found = find_forbidden_imports(pkg, ["forgeos.ports.provider"])
    assert "forgeos.ports.provider" in found


def test_core_does_not_import_adapters() -> None:
    # Hexagonal invariant (ADR 0001): core must never import adapters.
    core = SRC / "core"
    if not core.exists():
        return  # core packages arrive in later phases
    assert find_forbidden_imports(core, ["forgeos.adapters"]) == set()


def test_collect_imports_runs_on_source_tree() -> None:
    modules = collect_imported_modules(SRC)
    assert "pydantic" in modules
