from __future__ import annotations

from pathlib import Path

from forgeos.core.repo_intel.scanner import detect_language, iter_source_files


def test_detect_language() -> None:
    assert detect_language(Path("a.py")) == "python"
    assert detect_language(Path("a.ts")) == "typescript"
    assert detect_language(Path("a.jsx")) == "javascript"
    assert detect_language(Path("a.txt")) is None


def test_iter_skips_ignored_dirs_and_unknown_types(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "notes.txt").write_text("ignore me\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "junk.py").write_text("junk\n", encoding="utf-8")

    files = iter_source_files(tmp_path)
    assert [f.path for f in files] == ["pkg/a.py"]
    assert files[0].language == "python"
    assert len(files[0].content_hash) == 64


def test_results_are_sorted_and_hashed(tmp_path: Path) -> None:
    (tmp_path / "b.py").write_text("b\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("a\n", encoding="utf-8")
    files = iter_source_files(tmp_path)
    assert [f.path for f in files] == ["a.py", "b.py"]
    assert files[0].content_hash != files[1].content_hash
