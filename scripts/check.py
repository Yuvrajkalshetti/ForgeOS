#!/usr/bin/env python3
"""Stdlib-only lint/type substitute.

This is a *fallback* for constrained environments where ruff and mypy cannot be
installed (no network/PyPI). It does not replace them — CI still runs the real
tools. It performs three cheap, deterministic checks over ``src/`` and ``tests/``:

1. Syntax — every file compiles (``py_compile``).
2. Annotations — every function/method in ``src/`` annotates its return type and
   non-self parameters (approximates mypy's ``disallow_untyped_defs``).
3. Import hygiene — no wildcard imports; no unused top-level imports (a subset of
   what ruff's F-rules catch).

Exit code is non-zero if any check fails.
"""

from __future__ import annotations

import ast
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"


def _iter_py(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        if base.exists():
            files.extend(sorted(base.rglob("*.py")))
    return files


def check_syntax(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:  # pragma: no cover - error path
            errors.append(f"{path}: syntax: {exc.msg}")
    return errors


def _is_typed_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    problems: list[str] = []
    if node.returns is None:
        problems.append(f"{node.name}: missing return annotation")
    args = node.args
    positional = args.posonlyargs + args.args
    for arg in positional:
        if arg.arg in {"self", "cls"}:
            continue
        if arg.annotation is None:
            problems.append(f"{node.name}({arg.arg}): missing annotation")
    return problems


def check_annotations(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for problem in _is_typed_function(node):
                    errors.append(f"{path}: {problem}")
    return errors


def _exported_names(tree: ast.AST) -> set[str]:
    """Names listed in a module-level ``__all__`` (treated as used, like ruff)."""
    exported: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
            and isinstance(node.value, ast.List | ast.Tuple)
        ):
            exported.update(
                    elt.value
                    for elt in node.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                )
    return exported


def _collect_unused(tree: ast.AST) -> list[str]:
    """Flag wildcard imports and top-level names imported but never referenced.

    Mirrors ruff's F401: ``__future__`` imports are ignored, and names re-exported
    via ``__all__`` count as used.
    """
    problems: list[str] = []
    bound: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            problems.append("wildcard import")
        if isinstance(node, ast.Import | ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound.add(alias.asname or alias.name.split(".")[0])
    if not bound:
        return problems
    used: set[str] = _exported_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            base: ast.expr = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                used.add(base.id)
    problems.extend(f"unused import: {name}" for name in sorted(bound) if name not in used)
    return problems


def check_imports(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for problem in _collect_unused(tree):
            errors.append(f"{path}: {problem}")
    return errors


def main() -> int:
    src_files = _iter_py([SRC])
    all_files = _iter_py([SRC, TESTS])

    errors: list[str] = []
    errors += check_syntax(all_files)
    errors += check_annotations(src_files)  # strict annotations on src/ only
    errors += check_imports(all_files)

    if errors:
        print(f"check.py: {len(errors)} issue(s):")
        for line in errors:
            print(f"  - {line}")
        return 1
    print(f"check.py: OK ({len(all_files)} files: syntax + annotations + imports)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
