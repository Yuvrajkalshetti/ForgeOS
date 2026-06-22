from __future__ import annotations

import datetime
import shutil
from pathlib import Path

import pytest
from tests.fixtures.golden_loader import corpus_path, load_manifest

from forgeos.catalog import Collections
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.core.repo_intel import RepoIntelEngine
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _engine() -> tuple[RepoIntelEngine, GraphStore, InMemoryStorage]:
    store = InMemoryStorage()
    graph = GraphStore(store, clock=lambda: T0)
    return RepoIntelEngine(graph, store, clock=lambda: T0), graph, store


def _copy(name: str, dest: Path) -> Path:
    target = dest / name
    shutil.copytree(corpus_path(name), target)
    return target


@pytest.mark.parametrize("name", ["small", "medium", "monorepo"])
def test_golden_corpus_counts_match_manifest(name: str, tmp_path: Path) -> None:
    expected = load_manifest()["corpora"][name]["expected"]
    files_expected = load_manifest()["corpora"][name]["python_files"]
    engine, graph, _ = _engine()

    result = engine.scan(_copy(name, tmp_path))

    assert result.files == files_expected
    assert result.modules == expected["modules"]
    assert result.internal_edges == expected["internal_edges"]
    assert result.external_deps == expected["external_deps"]

    assert len(graph.nodes(NodeType.FILE)) == files_expected
    assert len(graph.nodes(NodeType.MODULE)) == expected["modules"]
    assert len(graph.nodes(NodeType.DEPENDENCY)) == expected["external_deps"]
    depends = [e for e in graph.edges() if e.type == EdgeType.DEPENDS_ON]
    assert len(depends) == expected["internal_edges"] + expected["external_deps"]


def test_medium_internal_and_external_edges_are_correct(tmp_path: Path) -> None:
    engine, graph, _ = _engine()
    engine.scan(_copy("medium", tmp_path))
    # pkg_a/mod.py -> pkg_b module (internal); pkg_b/helper.py -> httpx (external)
    assert graph.find_by_label("pkg_b") is not None
    assert graph.find_by_label("httpx") is not None
    assert graph.find_by_label("json") is None  # stdlib excluded


def test_repo_profile_is_written(tmp_path: Path) -> None:
    engine, _, store = _engine()
    engine.scan(_copy("small", tmp_path))
    profile = store.get(Collections.REPO_PROFILE, "profile")
    assert profile is not None
    assert profile["languages"] == ["python"]
    assert profile["module_count"] == 1
    assert profile["index_hash"]


def test_incremental_rescan_reuses_unchanged(tmp_path: Path) -> None:
    engine, _, _ = _engine()
    root = _copy("medium", tmp_path)
    first = engine.scan(root)
    assert first.parsed == first.files and first.reused == 0

    second = engine.scan(root)
    assert second.parsed == 0
    assert second.reused == first.files


def test_modified_file_is_reparsed(tmp_path: Path) -> None:
    engine, _, _ = _engine()
    root = _copy("medium", tmp_path)
    engine.scan(root)
    (root / "src" / "pkg_b" / "helper.py").write_text(
        "import httpx\n\n\ndef normalize(v: dict) -> dict:\n    return v\n", encoding="utf-8"
    )
    result = engine.scan(root)
    assert result.parsed == 1
    assert result.reused == result.files - 1


def test_removed_file_is_pruned(tmp_path: Path) -> None:
    engine, graph, _ = _engine()
    root = _copy("medium", tmp_path)
    engine.scan(root)
    (root / "src" / "pkg_a" / "mod.py").unlink()

    result = engine.scan(root)
    assert result.removed == 1
    assert graph.get_node("file:src/pkg_a/mod.py") is None


def test_engine_constructed_without_provider(tmp_path: Path) -> None:
    # Provider-free by construction: no provider argument exists or is needed.
    engine, _, _ = _engine()
    result = engine.scan(_copy("small", tmp_path))
    assert result.files == 3
