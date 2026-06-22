"""Static import guards.

Parse a package's source with the ``ast`` module and report imports matching a
forbidden prefix. This statically enforces architectural boundaries — most
importantly that ``forgeos.core.repo_intel`` never imports the provider port
(the deterministic, provider-free ingest directive). No code is executed.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _module_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
            # `from a.b import c` may import submodule a.b.c — record both forms so
            # the guard catches submodule imports, not just the package itself.
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def collect_imported_modules(package_dir: Path) -> set[str]:
    """Return every module imported by any ``.py`` file under ``package_dir``."""
    imported: set[str] = set()
    for path in sorted(package_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported |= _module_names(tree)
    return imported


def find_forbidden_imports(package_dir: Path, forbidden_prefixes: list[str]) -> set[str]:
    """Return imported modules that start with any forbidden prefix."""
    imported = collect_imported_modules(package_dir)
    return {
        module
        for module in imported
        for prefix in forbidden_prefixes
        if module == prefix or module.startswith(f"{prefix}.")
    }
