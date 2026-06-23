from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.core.exec_intel.models import Confidence
from forgeos.core.exec_intel.query import callees, callers, impact, paths_to, resolve
from forgeos.testing.fakes import InMemoryStorage


def _graph(tmp_path: Path) -> ExecGraphStore:
    (tmp_path / "m.py").write_text(
        "def c():\n    pass\n\ndef b():\n    c()\n\ndef a():\n    b()\n", encoding="utf-8"
    )
    store = ExecGraphStore(InMemoryStorage())
    ExecIntelEngine(store).scan(tmp_path)
    return store


def test_resolve_by_label(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    assert resolve(store, "a") == ["func:m.py#a"]


def test_callees_and_callers(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    assert "func:m.py#b" in callees(store, "func:m.py#a", 1, Confidence.RESOLVED)
    assert "func:m.py#a" in callers(store, "func:m.py#b", 1, Confidence.RESOLVED)


def test_impact_is_transitive(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    dependents = set(impact(store, "func:m.py#c", Confidence.RESOLVED))
    assert {"func:m.py#a", "func:m.py#b"} <= dependents


def test_paths_to_target(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    chains = paths_to(store, "func:m.py#c", 6, 20, Confidence.RESOLVED)
    assert ["func:m.py#a", "func:m.py#b", "func:m.py#c"] in chains
