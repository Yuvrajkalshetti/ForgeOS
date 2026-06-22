from __future__ import annotations

from tests.fixtures.golden_loader import corpus_path, golden_root, load_manifest


def test_manifest_parses_and_lists_three_corpora() -> None:
    manifest = load_manifest()
    assert manifest["schema_version"] == 1
    assert set(manifest["corpora"]) == {"small", "medium", "monorepo"}


def test_each_corpus_has_expected_python_file_count() -> None:
    manifest = load_manifest()
    for name, spec in manifest["corpora"].items():
        root = corpus_path(name)
        assert root.is_dir(), name
        actual = len(list(root.rglob("*.py")))
        assert actual == spec["python_files"], (name, actual)


def test_golden_root_exists() -> None:
    assert golden_root().is_dir()
